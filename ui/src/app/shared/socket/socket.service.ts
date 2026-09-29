import { Injectable, inject } from '@angular/core';
import { Observable, Subject } from 'rxjs';

import { AuthService } from '../../auth/auth.service';

export interface SocketConnection<T> {
  readonly messages: Observable<T>;
  close(): void;
}

const MAX_BACKOFF_MS = 15000;
const AUTH_EXPIRED_CODE = 4401;

@Injectable({ providedIn: 'root' })
export class SocketService {
  private readonly auth = inject(AuthService);

  connect<T>(path: string): SocketConnection<T> {
    const messages = new Subject<T>();
    let socket: WebSocket | null = null;
    let attempt = 0;
    let closed = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    const open = (): void => {
      if (closed) {
        return;
      }
      socket = new WebSocket(buildUrl(path));
      socket.onopen = () => {
        attempt = 0;
      };
      socket.onmessage = (event: MessageEvent<string>) => {
        messages.next(JSON.parse(event.data) as T);
      };
      socket.onclose = (event: CloseEvent) => {
        if (closed) {
          return;
        }
        if (event.code === AUTH_EXPIRED_CODE) {
          this.auth.refresh().subscribe({ next: open, error: open });
          return;
        }
        const delay = Math.min(1000 * 2 ** attempt, MAX_BACKOFF_MS);
        attempt++;
        retryTimer = setTimeout(open, delay);
      };
    };
    open();

    return {
      messages: messages.asObservable(),
      close: () => {
        closed = true;
        clearTimeout(retryTimer);
        socket?.close();
      },
    };
  }
}

function buildUrl(path: string): string {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${location.host}${path}`;
}
