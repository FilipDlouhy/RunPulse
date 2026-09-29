import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { describeHttpError } from '../../shared/http-errors';
import { AuthLayoutComponent } from '../auth-layout.component';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent],
  templateUrl: './login.component.html',
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly form = inject(FormBuilder).nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required],
  });

  readonly error = signal<string | null>(null);
  readonly loading = signal(false);
  readonly showPassword = signal(false);

  hasError(field: 'username' | 'password'): boolean {
    const control = this.form.controls[field];
    return control.invalid && control.touched;
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set(null);

    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigateByUrl(this.returnUrl()),
      error: (error: HttpErrorResponse) => {
        this.error.set(
          error.status === 401 ? 'Incorrect username or password.' : describeHttpError(error),
        );
        this.form.controls.password.reset();
        this.loading.set(false);
      },
    });
  }

  private returnUrl(): string {
    const url = this.route.snapshot.queryParamMap.get('returnUrl');
    return url?.startsWith('/') && !url.startsWith('//') ? url : '/';
  }
}
