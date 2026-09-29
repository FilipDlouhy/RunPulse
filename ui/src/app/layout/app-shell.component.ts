import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../auth/auth.service';
import { LogoComponent } from '../shared/logo.component';

interface NavLink {
  path: string;
  label: string;
  exact: boolean;
}

const RUNNER_LINKS: NavLink[] = [
  { path: '/', label: 'Dashboard', exact: true },
  { path: '/runs/live', label: 'Live run', exact: true },
  { path: '/runs', label: 'Runs', exact: true },
  { path: '/profile', label: 'Profile', exact: false },
];

const ADMIN_LINKS: NavLink[] = [
  { path: '/gym', label: 'Overview', exact: true },
  { path: '/gym/devices', label: 'Machines', exact: false },
  { path: '/gym/usage', label: 'Usage', exact: false },
  { path: '/gym/tech', label: 'Technical status', exact: false },
];

@Component({
  selector: 'app-shell',
  imports: [LogoComponent, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app-shell.component.html',
  styleUrl: './app-shell.component.scss',
})
export class AppShellComponent {
  protected readonly auth = inject(AuthService);

  protected readonly links = computed(() =>
    this.auth.currentUser()?.role === 'GYM_ADMIN' ? ADMIN_LINKS : RUNNER_LINKS,
  );

  protected readonly initials = computed(() => {
    const user = this.auth.currentUser();
    if (!user) {
      return '';
    }
    const fromName = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
    return (fromName || user.username.slice(0, 2)).toUpperCase();
  });

  protected signOut(): void {
    this.auth.logout().subscribe();
  }
}
