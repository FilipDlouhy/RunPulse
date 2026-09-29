import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { RECORD_LABELS, RUN_STATUSES, RUN_TYPES, RunDetail, SamplePoint } from '../dto/run.dto';
import { RunService } from '../run.service';
import { ChartComponent } from '../../shared/chart/chart.component';
import { hrSpeedChart } from '../../shared/chart/hr-speed-chart';
import { formatDistance, formatDuration, formatPace } from '../../shared/format';
import { describeHttpError } from '../../shared/http-errors';

const ZONE_LABELS = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5'];
const RPE_OPTIONS = Array.from({ length: 10 }, (_, i) => i + 1);

@Component({
  selector: 'app-run-detail',
  imports: [DatePipe, FormsModule, RouterLink, ChartComponent],
  templateUrl: './run-detail.component.html',
  styleUrl: './run-detail.component.scss',
})
export class RunDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly runs = inject(RunService);

  protected readonly types = RUN_TYPES;
  protected readonly statuses = RUN_STATUSES;
  protected readonly recordLabels = RECORD_LABELS;
  protected readonly zoneLabels = ZONE_LABELS;
  protected readonly rpeOptions = RPE_OPTIONS;
  protected readonly formatDistance = formatDistance;
  protected readonly formatDuration = formatDuration;
  protected readonly formatPace = formatPace;

  protected readonly run = signal<RunDetail | null>(null);
  protected readonly samples = signal<SamplePoint[]>([]);
  protected readonly loading = signal(true);
  protected readonly notFound = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly savingRpe = signal(false);

  protected readonly maxZoneSeconds = computed(() => Math.max(1, ...(this.run()?.summary?.zones ?? [0])));

  protected readonly chartConfig = computed(() => hrSpeedChart(this.samples()));

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    forkJoin({
      run: this.runs.get(id),
      samples: this.runs.samples(id, 10),
    }).subscribe({
      next: ({ run, samples }) => {
        this.run.set(run);
        this.samples.set(samples);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.notFound.set(error.status === 404);
        this.error.set(error.status === 404 ? null : describeHttpError(error));
        this.loading.set(false);
      },
    });
  }

  protected saveRpe(rpe: number | null): void {
    const run = this.run();
    if (!run) {
      return;
    }
    this.savingRpe.set(true);
    this.runs.updateRpe(run.id, rpe).subscribe({
      next: (updated) => {
        this.run.set(updated);
        this.savingRpe.set(false);
      },
      error: () => this.savingRpe.set(false),
    });
  }
}
