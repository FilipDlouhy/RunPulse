import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';

import { statusBadge } from '../device-status';
import { DeviceService } from '../device.service';
import { DEVICE_STATUSES, Device, GymEvent } from '../../dto/gym.dto';
import { SocketConnection, SocketService } from '../../../shared/socket/socket.service';
import { plural } from '../../../shared/format';
import { describeHttpError } from '../../../shared/http-errors';

@Component({
  selector: 'app-device-list',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './device-list.component.html',
  styleUrl: './device-list.component.scss',
})
export class DeviceListComponent implements OnInit, OnDestroy {
  private readonly devices = inject(DeviceService);
  private readonly sockets = inject(SocketService);

  protected readonly statuses = DEVICE_STATUSES;
  protected readonly statusBadge = statusBadge;
  protected readonly plural = plural;

  protected readonly items = signal<Device[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly busyId = signal<number | null>(null);

  protected readonly needsServiceCount = computed(
    () => this.items().filter((device) => device.needs_service).length,
  );

  private connection?: SocketConnection<GymEvent>;

  ngOnInit(): void {
    this.load();
    this.connection = this.sockets.connect<GymEvent>('/ws/gym/');
    this.connection.messages.subscribe((event) => {
      if (event.type === 'devices') {
        this.load();
      }
    });
  }

  ngOnDestroy(): void {
    this.connection?.close();
  }

  protected serviceDone(device: Device): void {
    this.act(device.id, this.devices.serviceDone(device.id));
  }

  protected outOfOrder(device: Device): void {
    this.act(device.id, this.devices.outOfOrder(device.id));
  }

  private act(id: number, action: Observable<Device>): void {
    this.busyId.set(id);
    action.subscribe({
      next: (device) => {
        this.items.update((items) => items.map((item) => (item.id === device.id ? device : item)));
        this.busyId.set(null);
      },
      error: () => this.busyId.set(null),
    });
  }

  private load(): void {
    this.devices.list().subscribe({
      next: (items) => {
        this.items.set(items);
        this.error.set(null);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(describeHttpError(error));
        this.loading.set(false);
      },
    });
  }
}
