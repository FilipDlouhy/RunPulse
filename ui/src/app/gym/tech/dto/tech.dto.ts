export interface QueueStats {
  messages: number;
  ready: number;
  unacked: number;
  consumers: number;
  publish_rate: number;
  deliver_rate: number;
}

export interface PipelineStep {
  order: number;
  name: string;
  status: string;
  duration_ms: number | null;
  error: string | null;
}

export interface PipelineRun {
  id: number;
  name: 'run_analysis';
  status: string;
  run_id: number | null;
  device: string | null;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  failed_step: string | null;
  steps: PipelineStep[];
}

export interface SlowestStep {
  name: string;
  avg_ms: number;
  max_ms: number;
  count: number;
}

export interface DeadLetter {
  id: number;
  routing_key: string;
  device_serial: string;
  body: string;
  error: string;
  created_at: string;
}

export interface TechStatus {
  queue: QueueStats | null;
  queue_error: string | null;
  dead_letter_count: number;
  dead_letters: DeadLetter[];
  pipeline_count: number;
  pipeline_failed: number;
  pipeline_avg_ms: number | null;
  slowest_steps: SlowestStep[];
  pipelines: PipelineRun[];
}
