import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ALERT_LABELS, LiveEvent, LiveMetrics, LiveRunStatus, LiveSample, RunAlert, RunListItem } from '../dto/run.dto';
import { RunService } from '../run.service';
import { ChartComponent } from '../../shared/chart/chart.component';
import { hrSpeedChart } from '../../shared/chart/hr-speed-chart';
import { SocketConnection, SocketService } from '../../shared/socket/socket.service';
import { formatDistance, formatDuration, formatPace, plural } from '../../shared/format';
import { describeHttpError } from '../../shared/http-errors';

const LIVE_WINDOW_SECONDS = 600;

@Component({
  selector: 'app-run-live',
  imports: [RouterLink, ChartComponent],
  templateUrl: './run-live.component.html',
  styleUrl: './run-live.component.scss',
})
export class RunLiveComponent implements OnInit, OnDestroy {
  private readonly runs = inject(RunService);
  private readonly sockets = inject(SocketService);

  protected readonly alertLabels = ALERT_LABELS;
  protected readonly formatDistance = formatDistance;
  protected readonly formatDuration = formatDuration;
  protected readonly formatPace = formatPace;
  protected readonly plural = plural;

  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly run = signal<RunListItem | null>(null);
  protected readonly metrics = signal<LiveMetrics | null>(null);
  protected readonly alerts = signal<RunAlert[]>([]);
  protected readonly samples = signal<LiveSample[]>([]);
  protected readonly status = signal<LiveRunStatus | null>(null);
  protected readonly newRecords = signal(0);
  protected readonly stopping = signal(false);
  protected readonly stopError = signal<string | null>(null);

  protected readonly chartConfig = computed(() => hrSpeedChart(this.samples()));

  private connection?: SocketConnection<LiveEvent>;

  ngOnInit(): void {
    this.runs.live().subscribe({
      next: (state) => {
        this.loading.set(false);
        if (!state) {
          return;
        }
        this.run.set(state.run);
        this.metrics.set(state.metrics);
        this.alerts.set(state.alerts);
        this.samples.set(state.samples);
        this.status.set(state.run.status);
        this.connect();
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(describeHttpError(error));
        this.loading.set(false);
      },
    });
  }

  ngOnDestroy(): void {
    this.connection?.close();
  }

  protected stop(): void {
    const run = this.run();
    if (!run) {
      return;
    }
    this.stopping.set(true);
    this.stopError.set(null);
    this.runs.stop(run.id).subscribe({
      next: () => this.stopping.set(false),
      error: (error: HttpErrorResponse) => {
        this.stopError.set(describeHttpError(error));
        this.stopping.set(false);
      },
    });
  }

  private connect(): void {
    this.connection = this.sockets.connect<LiveEvent>('/ws/live/');
    this.connection.messages.subscribe((event) => {
      switch (event.type) {
        case 'samples':
          if (event.run_id !== this.run()?.id) {
            break;
          }
          this.metrics.set(event.metrics);
          this.samples.update((current) => trimToWindow([...current, ...event.samples]));
          break;
        case 'alert':
          this.alerts.update((current) => [event.alert, ...current]);
          break;
        case 'run':
          if (event.run_id !== this.run()?.id) {
            break;
          }
          this.status.set(event.status);
          this.newRecords.set(event.new_records);
          break;
      }
    });
  }
}

function trimToWindow(samples: LiveSample[]): LiveSample[] {
  if (!samples.length) {
    return samples;
  }
  const latest = samples[samples.length - 1].t;
  return samples.filter((sample) => sample.t >= latest - LIVE_WINDOW_SECONDS);
}
