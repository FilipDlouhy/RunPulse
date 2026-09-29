import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, finalize, map, of, shareReplay, tap } from 'rxjs';

import { LoginRequest, RegisterRequest, User } from './dto/auth.dto';

export const AUTH_ENDPOINTS = {
  login: '/api/auth/login/',
  register: '/api/auth/register/',
  refresh: '/api/auth/refresh/',
  logout: '/api/auth/logout/',
  me: '/api/auth/me/',
};

// Tokens live in httpOnly cookies managed by the API, so this service never touches them.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private refreshInFlight: Observable<void> | null = null;

  readonly currentUser = signal<User | null>(null);

  login(body: LoginRequest): Observable<User> {
    return this.http
      .post<User>(AUTH_ENDPOINTS.login, body)
      .pipe(tap((user) => this.currentUser.set(user)));
  }

  register(body: RegisterRequest): Observable<User> {
    return this.http
      .post<User>(AUTH_ENDPOINTS.register, body)
      .pipe(tap((user) => this.currentUser.set(user)));
  }

  // After a page reload only the browser knows the cookies, so ask the API who we are.
  restoreSession(): Observable<boolean> {
    if (this.currentUser()) {
      return of(true);
    }
    return this.http.get<User>(AUTH_ENDPOINTS.me).pipe(
      tap((user) => this.currentUser.set(user)),
      map(() => true),
      catchError(() => of(false)),
    );
  }

  // Concurrent 401s share one refresh request instead of each firing their own.
  refresh(): Observable<void> {
    this.refreshInFlight ??= this.http.post<void>(AUTH_ENDPOINTS.refresh, null).pipe(
      finalize(() => (this.refreshInFlight = null)),
      shareReplay(1),
    );
    return this.refreshInFlight;
  }

  logout(): Observable<void> {
    return this.http.post<void>(AUTH_ENDPOINTS.logout, null).pipe(
      // Sign out locally even if the API is unreachable.
      catchError(() => of(undefined)),
      tap(() => {
        this.currentUser.set(null);
        this.router.navigate(['/login']);
      }),
    );
  }

  // The session can't be refreshed any more. During navigation the guard redirects instead.
  endSession(): void {
    this.currentUser.set(null);
    if (!this.router.currentNavigation()) {
      this.router.navigate(['/login'], { queryParams: { returnUrl: this.router.url } });
    }
  }
}
