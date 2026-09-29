import { HttpErrorResponse } from '@angular/common/http';

export type FieldErrors = Record<string, string[]>;

// Messages for failures that are not about a specific form field.
export function describeHttpError(error: HttpErrorResponse): string {
  const detail = (error.error as { detail?: unknown } | null)?.detail;
  if (typeof detail === 'string' && error.status >= 400 && error.status < 500) {
    return detail;
  }
  switch (true) {
    case error.status === 0:
      return 'Server is not available. Check your connection and try again.';
    case error.status === 429:
      return 'Too many attempts. Wait a minute and try again.';
    case error.status >= 500:
      return 'Server error. Please try again later.';
    default:
      return 'Something went wrong. Try again.';
  }
}

// DRF returns 400 as {"field": ["message", ...], "non_field_errors": [...]}.
export function toFieldErrors(error: HttpErrorResponse): FieldErrors | null {
  if (error.status !== 400 || typeof error.error !== 'object' || error.error === null) {
    return null;
  }
  return Object.fromEntries(
    Object.entries(error.error as Record<string, unknown>).map(([field, messages]) => [
      field,
      Array.isArray(messages) ? messages.map(String) : [String(messages)],
    ]),
  );
}
