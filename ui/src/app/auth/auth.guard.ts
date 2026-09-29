import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs';

import { AuthService } from './auth.service';
import { Role } from './dto/auth.dto';

export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.restoreSession().pipe(
    map((loggedIn) => {
      if (loggedIn) {
        return true;
      }
      return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
    }),
  );
};

export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.currentUser()) {
    return router.createUrlTree(['/']);
  }
  return true;
};

export function roleGuard(role: Role): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);
    if (auth.currentUser()?.role === role) {
      return true;
    }
    return router.createUrlTree(['/']);
  };
}

export const homeGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.currentUser()?.role === 'GYM_ADMIN') {
    return router.createUrlTree(['/gym']);
  }
  return true;
};
