export type DeviceStatus = 'FREE' | 'IN_USE' | 'OFFLINE' | 'OUT_OF_ORDER';
export type AlertType = 'HR_HIGH' | 'NO_HR' | 'DEVICE_FAULT';

export const DEVICE_STATUSES: Record<DeviceStatus, string> = {
  FREE: 'Free',
  IN_USE: 'In use',
  OFFLINE: 'Offline',
  OUT_OF_ORDER: 'Out of order',
};

export const ALERT_TYPES: Record<AlertType, string> = {
  HR_HIGH: 'High heart rate',
  NO_HR: 'No heart rate',
  DEVICE_FAULT: 'Treadmill fault',
};

export interface Device {
  id: number;
  serial: string;
  status: DeviceStatus;
  firmware: string;
  last_seen: string | null;
  total_hours: number;
  hours_since_service: number;
  needs_service: boolean;
}

export interface GymAlert {
  id: number;
  type: AlertType;
  message: string;
  device: string;
  run_id: number | null;
  created_at: string;
  acknowledged_at: string | null;
}

export interface GymOverview {
  treadmills_total: number;
  treadmills_in_use: number;
  treadmills_free: number;
  treadmills_out_of_order: number;
  treadmills_offline: number;
  runs_today: number;
  alerts: GymAlert[];
}

export type GymEvent = { type: 'alert'; alert: GymAlert } | { type: 'devices' };
