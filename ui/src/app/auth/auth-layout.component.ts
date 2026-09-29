import { Component, input } from '@angular/core';

import { LogoComponent } from '../shared/logo.component';

@Component({
  selector: 'app-auth-layout',
  imports: [LogoComponent],
  templateUrl: './auth-layout.component.html',
  styleUrl: './auth-layout.component.scss',
})
export class AuthLayoutComponent {
  readonly heading = input.required<string>();
  readonly subheading = input<string>('');
}
