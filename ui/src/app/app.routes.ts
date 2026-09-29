import { Routes } from '@angular/router';

import { authGuard, guestGuard, homeGuard, roleGuard } from './auth/auth.guard';
import { LoginComponent } from './auth/login/login.component';
import { RegisterComponent } from './auth/register/register.component';
import { AppShellComponent } from './layout/app-shell.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent, canActivate: [guestGuard], title: 'Log in · RunPulse' },
  {
    path: 'register',
    component: RegisterComponent,
    canActivate: [guestGuard],
    title: 'Sign up · RunPulse',
  },
  {
    path: '',
    component: AppShellComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./dashboard/dashboard.component').then((m) => m.DashboardComponent),
        canActivate: [homeGuard],
        title: 'Dashboard · RunPulse',
      },
      {
        path: 'profile',
        loadComponent: () =>
          import('./profile/runner-profile/runner-profile.component').then((m) => m.RunnerProfileComponent),
        canActivate: [roleGuard('RUNNER')],
        title: 'Profile · RunPulse',
      },
      {
        path: 'runs',
        canActivate: [roleGuard('RUNNER')],
        children: [
          {
            path: '',
            loadComponent: () => import('./runs/run-list/run-list.component').then((m) => m.RunListComponent),
            title: 'Runs · RunPulse',
          },
          {
            path: 'live',
            loadComponent: () => import('./runs/run-live/run-live.component').then((m) => m.RunLiveComponent),
            title: 'Live run · RunPulse',
          },
          {
            path: ':id',
            loadComponent: () =>
              import('./runs/run-detail/run-detail.component').then((m) => m.RunDetailComponent),
            title: 'Run detail · RunPulse',
          },
        ],
      },
      {
        path: 'gym',
        canActivate: [roleGuard('GYM_ADMIN')],
        children: [
          {
            path: '',
            loadComponent: () => import('./gym/overview/overview.component').then((m) => m.OverviewComponent),
            title: 'Gym overview · RunPulse',
          },
          {
            path: 'devices',
            loadComponent: () =>
              import('./gym/devices/device-list/device-list.component').then((m) => m.DeviceListComponent),
            title: 'Machines · RunPulse',
          },
          {
            path: 'usage',
            loadComponent: () => import('./gym/usage/usage.component').then((m) => m.UsageComponent),
            title: 'Usage · RunPulse',
          },
          {
            path: 'tech',
            loadComponent: () => import('./gym/tech/tech.component').then((m) => m.TechComponent),
            title: 'Technical status · RunPulse',
          },
        ],
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
