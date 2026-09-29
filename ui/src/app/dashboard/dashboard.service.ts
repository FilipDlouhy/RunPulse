import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { PersonalRecord, WeeklyStat } from '../runs/dto/run.dto';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);

  weeklyStats(weeks = 12): Observable<WeeklyStat[]> {
    const params = new HttpParams().set('weeks', weeks);
    return this.http.get<WeeklyStat[]>('/api/stats/weekly/', { params });
  }

  records(): Observable<PersonalRecord[]> {
    return this.http.get<PersonalRecord[]>('/api/records/');
  }
}
