import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';

import { HeatmapResponse } from './dto/usage.dto';
import { UsageService } from './usage.service';
import { describeHttpError } from '../../shared/http-errors';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const WEEK_OPTIONS = [
  { weeks: 1, label: '1 week' },
  { weeks: 4, label: '4 weeks' },
  { weeks: 8, label: '8 weeks' },
  { weeks: 12, label: '12 weeks' },
];
const HOURS = Array.from({ length: 24 }, (_, hour) => hour);

@Component({
  selector: 'app-usage',
  templateUrl: './usage.component.html',
  styleUrl: './usage.component.scss',
})
export class UsageComponent implements OnInit {
  private readonly usage = inject(UsageService);

  protected readonly days = DAY_LABELS;
  protected readonly hours = HOURS;
  protected readonly weekOptions = WEEK_OPTIONS;

  protected readonly weeks = signal(4);
  protected readonly data = signal<HeatmapResponse | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);

  protected readonly max = computed(() => Math.max(1, ...(this.data()?.heatmap.flat() ?? [0])));

  ngOnInit(): void {
    this.load();
  }

  protected selectWeeks(weeks: number): void {
    this.weeks.set(weeks);
    this.load();
  }

  protected row(dayIndex: number): number[] {
    return this.data()?.heatmap[dayIndex] ?? this.hours.map(() => 0);
  }

  protected intensity(value: number): number {
    return Math.max(0.06, Math.min(1, value / this.max()));
  }

  private load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.usage.heatmap(this.weeks()).subscribe({
      next: (data) => {
        this.data.set(data);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(describeHttpError(error));
        this.loading.set(false);
      },
    });
  }
}
