import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ChartConfiguration } from 'chart.js';
import { forkJoin } from 'rxjs';

import { PersonalRecord, RECORD_LABELS, RUN_STATUSES, RUN_TYPES, RunListItem, WeeklyStat } from '../runs/dto/run.dto';
import { RunService } from '../runs/run.service';
import { ChartComponent } from '../shared/chart/chart.component';
import { formatDistance, formatDuration, formatPace } from '../shared/format';
import { describeHttpError } from '../shared/http-errors';
import { DashboardService } from './dashboard.service';

const RECENT_RUNS_COUNT = 5;

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, DatePipe, ChartComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly runs = inject(RunService);
  private readonly dashboard = inject(DashboardService);

  protected readonly types = RUN_TYPES;
  protected readonly statuses = RUN_STATUSES;
  protected readonly recordLabels = RECORD_LABELS;
  protected readonly formatDistance = formatDistance;
  protected readonly formatDuration = formatDuration;

  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly recentRuns = signal<RunListItem[]>([]);
  protected readonly records = signal<PersonalRecord[]>([]);
  protected readonly weekly = signal<WeeklyStat[]>([]);

  protected readonly chartConfig = computed<ChartConfiguration>(() => {
    const weeks = this.weekly();
    return {
      type: 'bar',
      data: {
        labels: weeks.map((week) => formatWeekLabel(week.week)),
        datasets: [
          {
            label: 'Km',
            data: weeks.map((week) => week.km),
            backgroundColor: '#4f46e5',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    };
  });

  ngOnInit(): void {
    forkJoin({
      runs: this.runs.list(''),
      records: this.dashboard.records(),
      weekly: this.dashboard.weeklyStats(12),
    }).subscribe({
      next: ({ runs, records, weekly }) => {
        this.recentRuns.set(runs.slice(0, RECENT_RUNS_COUNT));
        this.records.set(records);
        this.weekly.set(weekly);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(describeHttpError(error));
        this.loading.set(false);
      },
    });
  }

  protected paceLabel(run: RunListItem): string {
    return run.summary && run.summary.avg_pace_s ? formatPace(run.summary.avg_pace_s) : '–';
  }
}

function formatWeekLabel(week: string): string {
  const date = new Date(week);
  return `${date.getDate()}.${date.getMonth() + 1}.`;
}
