import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';

import { ALERT_TYPES, GymAlert, GymEvent, GymOverview } from '../dto/gym.dto';
import { OverviewService } from './overview.service';
import { SocketConnection, SocketService } from '../../shared/socket/socket.service';
import { describeHttpError } from '../../shared/http-errors';

@Component({
  selector: 'app-overview',
  imports: [DatePipe],
  templateUrl: './overview.component.html',
  styleUrl: './overview.component.scss',
})
export class OverviewComponent implements OnInit, OnDestroy {
  private readonly overview = inject(OverviewService);
  private readonly sockets = inject(SocketService);

  protected readonly alertTypes = ALERT_TYPES;
  protected readonly data = signal<GymOverview | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly ackingId = signal<number | null>(null);

  private connection?: SocketConnection<GymEvent>;

  ngOnInit(): void {
    this.load();
    this.connection = this.sockets.connect<GymEvent>('/ws/gym/');
    this.connection.messages.subscribe((event) => {
      if (event.type === 'alert') {
        this.data.update((current) => current && { ...current, alerts: [event.alert, ...current.alerts] });
      } else {
        this.load();
      }
    });
  }

  ngOnDestroy(): void {
    this.connection?.close();
  }

  protected ack(alert: GymAlert): void {
    this.ackingId.set(alert.id);
    this.overview.ack(alert.id).subscribe({
      next: () => {
        this.data.update(
          (current) => current && { ...current, alerts: current.alerts.filter((a) => a.id !== alert.id) },
        );
        this.ackingId.set(null);
      },
      error: () => this.ackingId.set(null),
    });
  }

  private load(): void {
    this.overview.get().subscribe({
      next: (data) => {
        this.data.set(data);
        this.error.set(null);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(describeHttpError(error));
        this.loading.set(false);
      },
    });
  }
}
