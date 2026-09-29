import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { FieldErrors, describeHttpError, toFieldErrors } from '../../shared/http-errors';
import { AuthLayoutComponent } from '../auth-layout.component';
import { AuthService } from '../auth.service';

type Field = 'username' | 'email' | 'password';

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  // Mirrors Django's username rules and MinimumLengthValidator.
  readonly form = inject(FormBuilder).nonNullable.group({
    username: [
      '',
      [Validators.required, Validators.maxLength(150), Validators.pattern(/^[\w.@+-]+$/)],
    ],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  readonly serverErrors = signal<FieldErrors>({});
  readonly error = signal<string | null>(null);
  readonly loading = signal(false);
  readonly showPassword = signal(false);

  hasError(field: Field): boolean {
    const control = this.form.controls[field];
    return (control.invalid && control.touched) || !!this.serverErrors()[field];
  }

  serverError(field: Field): string | null {
    return this.serverErrors()[field]?.join(' ') ?? null;
  }

  clearServerError(field: Field): void {
    if (this.serverErrors()[field]) {
      const { [field]: _, ...rest } = this.serverErrors();
      this.serverErrors.set(rest);
    }
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.serverErrors.set({});

    // The API signs the new user in straight away, so there is no separate login call.
    this.auth.register(this.form.getRawValue()).subscribe({
      next: () => this.router.navigateByUrl('/'),
      error: (error: HttpErrorResponse) => {
        this.showError(error);
        this.loading.set(false);
      },
    });
  }

  private showError(error: HttpErrorResponse): void {
    const fieldErrors = toFieldErrors(error);
    if (!fieldErrors) {
      this.error.set(describeHttpError(error));
      return;
    }
    const { non_field_errors, detail, ...perField } = fieldErrors;
    this.serverErrors.set(perField);
    const general = [...(non_field_errors ?? []), ...(detail ?? [])];
    if (general.length) {
      this.error.set(general.join(' '));
    }
  }
}
