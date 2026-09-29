import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { HeatmapResponse } from './dto/usage.dto';

@Injectable({ providedIn: 'root' })
export class UsageService {
  private readonly http = inject(HttpClient);

  heatmap(weeks: number): Observable<HeatmapResponse> {
    const params = new HttpParams().set('weeks', weeks);
    return this.http.get<HeatmapResponse>('/api/gym/usage/heatmap/', { params });
  }
}
