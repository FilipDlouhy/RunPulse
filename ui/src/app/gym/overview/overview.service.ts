import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { GymAlert, GymOverview } from '../dto/gym.dto';

@Injectable({ providedIn: 'root' })
export class OverviewService {
  private readonly http = inject(HttpClient);

  get(): Observable<GymOverview> {
    return this.http.get<GymOverview>('/api/gym/overview/');
  }

  ack(alertId: number): Observable<GymAlert> {
    return this.http.post<GymAlert>(`/api/alerts/${alertId}/ack/`, null);
  }
}
