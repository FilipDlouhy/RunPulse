import { provideHttpClient, withInterceptors, withXsrfConfiguration } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { apiInterceptor } from './shared/api.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([apiInterceptor]),
      // Django's CSRF cookie/header names, so POSTs carry the token the API checks.
      withXsrfConfiguration({ cookieName: 'csrftoken', headerName: 'X-CSRFToken' }),
    ),
  ],
};
