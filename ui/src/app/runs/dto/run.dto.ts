export type RunType = 'easy' | 'intervals' | 'tempo' | 'long';
export type RunStatus = 'LIVE' | 'ANALYZING' | 'DONE' | 'FAILED';
export type LiveRunStatus = RunStatus | 'DISCARDED';
export type RecordDistance = '1K' | '5K' | '10K';
export type AlertType = 'HR_HIGH' | 'NO_HR' | 'DEVICE_FAULT';

export const RUN_TYPES: Record<RunType, string> = {
  easy: 'Easy',
  intervals: 'Intervals',
  tempo: 'Tempo',
  long: 'Long',
};

export const RUN_STATUSES: Record<RunStatus, string> = {
  LIVE: 'Live',
  ANALYZING: 'Analyzing',
  DONE: 'Done',
  FAILED: 'Failed',
};

export const RECORD_LABELS: Record<RecordDistance, string> = {
  '1K': '1 km',
  '5K': '5 km',
  '10K': '10 km',
};

export const ALERT_LABELS: Record<AlertType, string> = {
  HR_HIGH: 'High heart rate',
  NO_HR: 'No heart rate',
  DEVICE_FAULT: 'Treadmill fault',
};

export interface RunSummaryBrief {
  distance_m: number;
  duration_s: number;
  avg_pace_s: number | null;
  avg_hr: number | null;
  trimp: number;
}

export interface Split {
  km: number;
  distance_m: number;
  time_s: number;
  pace_s: number;
  avg_hr: number | null;
}

export interface RunSummary extends RunSummaryBrief {
  max_hr: number | null;
  zones: number[];
  splits: Split[];
  kcal: number;
  cleaned_points: number;
  analyzed_at: string;
}

export interface RunListItem {
  id: number;
  type: RunType;
  status: RunStatus;
  device: string;
  started_at: string;
  ended_at: string | null;
  rpe: number | null;
  summary: RunSummaryBrief | null;
}

export interface PersonalRecord {
  distance: RecordDistance;
  time_s: number;
  pace_s: number;
  achieved_at: string;
  run_id: number;
}

export interface RunDetail extends RunListItem {
  summary: RunSummary | null;
  new_records: PersonalRecord[];
}

export interface SamplePoint {
  t: number;
  hr: number | null;
  speed_kmh: number;
}

export interface LiveMetrics {
  elapsed_s: number;
  hr: number | null;
  zone: number | null;
  speed_kmh: number;
  pace_s: number | null;
  distance_m: number;
}

export interface LiveSample {
  seq: number;
  t: number;
  hr: number | null;
  speed_kmh: number;
}

export interface RunAlert {
  id: number;
  type: AlertType;
  message: string;
  created_at: string;
}

export interface LiveRunState {
  run: RunListItem;
  metrics: LiveMetrics | null;
  samples: LiveSample[];
  alerts: RunAlert[];
}

export type LiveEvent =
  | { type: 'samples'; run_id: number; metrics: LiveMetrics; samples: LiveSample[] }
  | { type: 'alert'; alert: RunAlert }
  | { type: 'run'; run_id: number; status: LiveRunStatus; new_records: number };

export interface WeeklyStat {
  week: string;
  runs: number;
  km: number;
  duration_s: number;
  trimp: number;
}
