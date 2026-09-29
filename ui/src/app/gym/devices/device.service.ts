import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Device } from '../dto/gym.dto';

@Injectable({ providedIn: 'root' })
export class DeviceService {
  private readonly http = inject(HttpClient);

  list(): Observable<Device[]> {
    return this.http.get<Device[]>('/api/gym/devices/');
  }

  serviceDone(id: number): Observable<Device> {
    return this.http.post<Device>(`/api/devices/${id}/service-done/`, null);
  }

  outOfOrder(id: number): Observable<Device> {
    return this.http.post<Device>(`/api/devices/${id}/out-of-order/`, null);
  }
}
