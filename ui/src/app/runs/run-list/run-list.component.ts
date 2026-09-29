import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { RUN_TYPES, RunListItem, RunType } from '../dto/run.dto';
import { RunService } from '../run.service';
import { formatDistance, formatDuration, formatPace, plural } from '../../shared/format';
import { describeHttpError } from '../../shared/http-errors';

@Component({
  selector: 'app-run-list',
  imports: [DatePipe, ReactiveFormsModule, RouterLink],
  templateUrl: './run-list.component.html',
  styleUrl: './run-list.component.scss',
})
export class RunListComponent implements OnInit {
  private readonly runs = inject(RunService);
  private readonly fb = inject(FormBuilder);

  protected readonly types = RUN_TYPES;
  protected readonly typeOptions = Object.entries(RUN_TYPES).map(([value, label]) => ({ value, label }));
  protected readonly formatDistance = formatDistance;
  protected readonly formatDuration = formatDuration;
  protected readonly plural = plural;

  protected readonly filter = this.fb.nonNullable.control<RunType | ''>('');
  protected readonly items = signal<RunListItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
    this.filter.valueChanges.subscribe(() => this.load());
  }

  protected paceLabel(run: RunListItem): string {
    const pace = run.summary?.avg_pace_s;
    if (!pace) {
      return '–';
    }
    return formatPace(pace);
  }

  private load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.runs.list(this.filter.value).subscribe({
      next: (items) => {
        this.items.set(items);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(describeHttpError(error));
        this.loading.set(false);
      },
    });
  }
}
