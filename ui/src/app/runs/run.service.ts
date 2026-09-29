import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { LiveRunState, RunDetail, RunListItem, RunType, SamplePoint } from './dto/run.dto';

const RUNS_URL = '/api/runs/';

@Injectable({ providedIn: 'root' })
export class RunService {
  private readonly http = inject(HttpClient);

  list(type: RunType | ''): Observable<RunListItem[]> {
    const params = type ? new HttpParams().set('type', type) : new HttpParams();
    return this.http.get<RunListItem[]>(RUNS_URL, { params });
  }

  get(id: number): Observable<RunDetail> {
    return this.http.get<RunDetail>(`${RUNS_URL}${id}/`);
  }

  updateRpe(id: number, rpe: number | null): Observable<RunDetail> {
    return this.http.patch<RunDetail>(`${RUNS_URL}${id}/`, { rpe });
  }

  samples(id: number, stepSeconds = 10): Observable<SamplePoint[]> {
    const params = new HttpParams().set('step', stepSeconds);
    return this.http.get<SamplePoint[]>(`${RUNS_URL}${id}/samples/`, { params });
  }

  stop(id: number): Observable<RunDetail> {
    return this.http.post<RunDetail>(`${RUNS_URL}${id}/stop/`, null);
  }

  live(): Observable<LiveRunState | null> {
    return this.http
      .get<LiveRunState>(`${RUNS_URL}live/`, { observe: 'response' })
      .pipe(map((response) => (response.status === 204 ? null : response.body)));
  }
}
