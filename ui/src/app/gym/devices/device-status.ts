import { DeviceStatus } from '../dto/gym.dto';

const STATUS_BADGES: Record<DeviceStatus, string> = {
  FREE: 'badge-success',
  IN_USE: 'badge-primary',
  OFFLINE: '',
  OUT_OF_ORDER: 'badge-danger',
};

export function statusBadge(status: DeviceStatus): string {
  return `badge badge-dot ${STATUS_BADGES[status]}`;
}
