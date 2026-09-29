import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';

import { AUTH_ENDPOINTS, AuthService } from '../auth/auth.service';

const PUBLIC_ENDPOINTS = [
  AUTH_ENDPOINTS.login,
  AUTH_ENDPOINTS.register,
  AUTH_ENDPOINTS.refresh,
  AUTH_ENDPOINTS.logout,
];

// The browser attaches the auth cookies itself; this only recovers from an expired access token.
export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  if (PUBLIC_ENDPOINTS.includes(req.url)) {
    return next(req);
  }

  const auth = inject(AuthService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401) {
        return throwError(() => error);
      }
      // Access cookie expired: refresh once and replay the original request.
      return auth.refresh().pipe(
        catchError((refreshError) => {
          auth.endSession();
          return throwError(() => refreshError);
        }),
        switchMap(() => next(req)),
      );
    }),
  );
};
