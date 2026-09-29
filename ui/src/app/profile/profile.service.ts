import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Profile } from './dto/profile.dto';

const PROFILE_URL = '/api/profile/';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);

  get(): Observable<Profile> {
    return this.http.get<Profile>(PROFILE_URL);
  }

  save(profile: Profile): Observable<Profile> {
    return this.http.put<Profile>(PROFILE_URL, profile);
  }
}
