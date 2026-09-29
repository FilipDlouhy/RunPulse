import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';

import { formatDuration, parseDuration } from '../../shared/format';
import { FieldErrors, describeHttpError, toFieldErrors } from '../../shared/http-errors';
import { Profile, RACE_DISTANCES, RaceDistance } from '../dto/profile.dto';
import { ProfileService } from '../profile.service';

type Field = 'weight_kg' | 'birth_date' | 'hr_rest' | 'hr_max' | 'goal_distance' | 'goal_time';

function durationValidator(control: AbstractControl<string>): ValidationErrors | null {
  if (!control.value) {
    return null;
  }
  if (parseDuration(control.value) === null) {
    return { duration: true };
  }
  return null;
}

@Component({
  selector: 'app-runner-profile',
  imports: [ReactiveFormsModule],
  templateUrl: './runner-profile.component.html',
  styleUrl: './runner-profile.component.scss',
})
export class RunnerProfileComponent implements OnInit {
  private readonly profiles = inject(ProfileService);
  private readonly fb = inject(FormBuilder);

  protected readonly distances = RACE_DISTANCES;
  protected readonly today = new Date().toISOString().slice(0, 10);

  protected readonly form = this.fb.group({
    weight_kg: this.fb.control<number | null>(null, [Validators.min(30), Validators.max(250)]),
    birth_date: this.fb.control<string | null>(null),
    hr_rest: this.fb.control<number | null>(null, [Validators.min(30), Validators.max(100)]),
    hr_max: this.fb.control<number | null>(null, [Validators.min(120), Validators.max(230)]),
    goal_distance: this.fb.control<RaceDistance | null>(null),
    goal_time: this.fb.nonNullable.control('', durationValidator),
  });

  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly saved = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly serverErrors = signal<FieldErrors>({});

  ngOnInit(): void {
    this.profiles.get().subscribe({
      next: (profile) => {
        this.show(profile);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(describeHttpError(error));
        this.loading.set(false);
      },
    });
  }

  protected hasError(field: Field): boolean {
    const control = this.form.controls[field];
    return (control.invalid && control.touched) || !!this.serverError(field);
  }

  protected serverError(field: Field): string | null {
    const key = field === 'goal_time' ? 'goal_time_s' : field;
    return this.serverErrors()[key]?.join(' ') ?? null;
  }

  protected save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    this.saved.set(false);
    this.error.set(null);
    this.serverErrors.set({});

    this.profiles.save(this.toInput()).subscribe({
      next: (profile) => {
        this.show(profile);
        this.saved.set(true);
        this.saving.set(false);
      },
      error: (error: HttpErrorResponse) => {
        const fieldErrors = toFieldErrors(error);
        if (fieldErrors) {
          this.serverErrors.set(fieldErrors);
        } else {
          this.error.set(describeHttpError(error));
        }
        this.saving.set(false);
      },
    });
  }

  private show(profile: Profile): void {
    this.form.reset({
      weight_kg: profile.weight_kg,
      birth_date: profile.birth_date,
      hr_rest: profile.hr_rest,
      hr_max: profile.hr_max,
      goal_distance: profile.goal_distance,
      goal_time: profile.goal_time_s ? formatDuration(profile.goal_time_s) : '',
    });
  }

  private toInput(): Profile {
    const value = this.form.getRawValue();
    return {
      weight_kg: value.weight_kg,
      birth_date: value.birth_date || null,
      hr_rest: value.hr_rest,
      hr_max: value.hr_max,
      goal_distance: value.goal_distance,
      goal_time_s: value.goal_time ? parseDuration(value.goal_time) : null,
    };
  }
}
