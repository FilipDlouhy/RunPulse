import { DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, timer } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

export function poll<T>(
  destroyRef: DestroyRef,
  source: () => Observable<T>,
  intervalMs: number,
  stopWhen: (value: T) => boolean = () => false,
): Observable<T> {
  return timer(0, intervalMs).pipe(
    switchMap(() => source()),
    takeWhile((value) => !stopWhen(value), true),
    takeUntilDestroyed(destroyRef),
  );
}
