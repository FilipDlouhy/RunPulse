import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { EMPTY, catchError } from 'rxjs';

import { DeadLetter, PipelineRun, TechStatus } from './dto/tech.dto';
import { TechService } from './tech.service';
import { describeHttpError } from '../../shared/http-errors';
import { poll } from '../../shared/polling';

const POLL_INTERVAL_MS = 5000;

@Component({
  selector: 'app-tech',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './tech.component.html',
  styleUrl: './tech.component.scss',
})
export class TechComponent implements OnInit {
  private readonly tech = inject(TechService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly data = signal<TechStatus | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly expandedId = signal<number | null>(null);
  protected readonly retryingId = signal<number | null>(null);

  ngOnInit(): void {
    poll(
      this.destroyRef,
      () =>
        this.tech.get().pipe(
          catchError((error: HttpErrorResponse) => {
            this.error.set(describeHttpError(error));
            return EMPTY;
          }),
        ),
      POLL_INTERVAL_MS,
    ).subscribe((data) => {
      this.error.set(null);
      this.data.set(data);
    });
  }

  protected toggle(run: PipelineRun): void {
    this.expandedId.update((id) => (id === run.id ? null : run.id));
  }

  protected retry(item: DeadLetter): void {
    this.retryingId.set(item.id);
    this.tech.retryDlq(item.id).subscribe({
      next: () => {
        this.data.update(
          (current) =>
            current && {
              ...current,
              dead_letters: current.dead_letters.filter((letter) => letter.id !== item.id),
              dead_letter_count: current.dead_letter_count - 1,
            },
        );
        this.retryingId.set(null);
      },
      error: () => this.retryingId.set(null),
    });
  }
}
