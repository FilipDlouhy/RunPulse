import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { TechStatus } from './dto/tech.dto';

@Injectable({ providedIn: 'root' })
export class TechService {
  private readonly http = inject(HttpClient);

  get(): Observable<TechStatus> {
    return this.http.get<TechStatus>('/api/tech/');
  }

  retryDlq(id: number): Observable<void> {
    return this.http.post<void>(`/api/dlq/${id}/retry/`, null);
  }
}
