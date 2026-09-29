import { Component } from '@angular/core';

let nextId = 0;

@Component({
  selector: 'app-logo',
  template: `
    <svg class="mark" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="9" [attr.fill]="'url(#' + gradientId + ')'" />
      <polyline
        points="5,17 11,17 13.5,11 17,23 19.5,14 21.5,17 27,17"
        fill="none"
        stroke="#fff"
        stroke-width="2.4"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <defs>
        <linearGradient [attr.id]="gradientId" x1="0" y1="0" x2="32" y2="32">
          <stop stop-color="#6366f1" />
          <stop offset="1" stop-color="#f43f5e" />
        </linearGradient>
      </defs>
    </svg>
    <span class="wordmark">Run<strong>Pulse</strong></span>
  `,
  styles: `
    :host {
      display: inline-flex;
      align-items: center;
      gap: 10px;
    }

    .mark {
      width: 32px;
      height: 32px;
      flex-shrink: 0;
    }

    .wordmark {
      font-size: 1.125rem;
      font-weight: 500;
      letter-spacing: -0.01em;

      strong {
        font-weight: 700;
      }
    }
  `,
})
export class LogoComponent {
  // Unique per instance so two logos on one page never share a gradient.
  protected readonly gradientId = `logo-gradient-${nextId++}`;
}
