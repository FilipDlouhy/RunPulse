# RunPulse

RunPulse monitors the treadmills in a gym. The treadmills send telemetry through RabbitMQ, the backend stores it and shows it live. A runner watches their run live and gets an analysis when it ends. The gym admin watches the machines, alerts and utilization.

**Stack:** Django 5.2 + DRF + Channels, TimescaleDB, RabbitMQ, Celery, Redis, Angular, Docker. A Python simulator plays the treadmills.

- **Telemetry:** a treadmill publishes `run_start`, `sample` (every second), `heartbeat` and `run_end` to RabbitMQ. The `consumer` writes them in batches (500 messages or 1 s) and acks after the DB commit.
- **Live data:** the consumer pushes the metrics through Redis to WebSockets (Django Channels).
- **Analysis:** after `run_end` a Celery worker computes splits, heart rate zones and personal records.
- **Monitoring:** heart rate alerts, a watchdog for runs without data and offline treadmills, and a dead letter table for invalid messages.

## Demo accounts

| Username | Password | Role |
| --- | --- | --- |
| `admin` | `admin` | gym admin, also superuser in the Django admin |
| `manager` | `demo1234` | gym admin |
| `filip` | `filip123` | runner |
| `runner` | `demo1234` | runner |
| `member001` … `member120` | `demo1234` | gym members (runners) |
| `loadbot` | `demo1234` | load test runner, created by `seed_load` |

## How to run

Everything runs in Docker:

```bash
make up
```

Without `make` it is `docker compose up -d --build`. The first start takes about a minute: `web` runs the migrations and seeds the demo data, the other containers wait until it is healthy. `docker compose ps` should show every container as `healthy` or `running`.

| Service | Address |
| --- | --- |
| UI | http://localhost:8080 |
| API | http://localhost:8000 |
| Django admin | http://localhost:8000/admin/ |
| Health | http://localhost:8000/health/ |
| RabbitMQ admin | http://localhost:15672 (`runpulse` / `runpulse`) |

The `simulator` container runs a live gym at 60× speed on its own.

More simulator data:

```bash
docker compose run --rm simulator python simulator.py backfill --weeks 8
docker compose run --rm simulator python simulator.py run --user filip --speedup 10
```

Load test:

```bash
docker compose exec web python manage.py seed_load
docker compose run --rm simulator python simulator.py load --devices 500 --rate 10 --duration 60
```

Stop with `make down`. `docker compose down -v` also deletes the data.

### If you don't want Docker

Only the infrastructure runs in Docker, the rest runs locally:

```bash
make infra
make migrate
make seed
```

Then in separate terminals `make web`, `make consume`, `make worker`, `make ui` and `make gym`. The UI then runs at http://localhost:4200.

## How to test

### 1. Runner (`filip`) at http://localhost:8080

- **Profile:** fill in the resting and max heart rate and check that the heart rate zones appear.
- **Live run:** start one run for `filip`. The "Live run" page shows heart rate, pace and distance changing.

  ```bash
  docker compose run --rm simulator python simulator.py run --user filip --speedup 10
  ```

- **Analysis:** after the run ends it goes from `ANALYZING` to `DONE` and the run detail shows the summary, splits, zones and records.

### 2. Gym admin (`admin`) at http://localhost:8080

- **Overview and Machines:** occupancy from the simulator and alerts. Acknowledge an alert.
- **Machines:** mark a treadmill out of order, then confirm the service is done. The simulator stops using the treadmill and picks it up again after the service.
- **Usage:** utilization heatmap. More data:

  ```bash
  docker compose run --rm simulator python simulator.py backfill --weeks 8
  ```

- **Technical status:** telemetry queue, pipelines and dead letters. A run with broken messages fills the dead letters:

  ```bash
  docker compose run --rm simulator python simulator.py run --user filip --speedup 10 --chaos
  ```

### 3. Django admin

http://localhost:8000/admin/ as `admin` shows users, treadmills and runs.

### 4. Health

http://localhost:8000/health/ returns 200 when the DB, RabbitMQ and Redis are reachable.

## Architecture

| Container | What runs in it |
| --- | --- |
| `db` | PostgreSQL 16 + TimescaleDB |
| `rabbitmq` | RabbitMQ with the admin UI, telemetry queue and Celery broker |
| `redis` | channel layer for Django Channels |
| `web` | Django + Channels (Daphne), REST API and WebSocket |
| `consumer` | processes telemetry from RabbitMQ |
| `worker` | Celery worker, run analysis |
| `simulator` | gym simulator |
| `ui` | Angular build served by nginx |

### How it works

```mermaid
flowchart LR
    SIM["Treadmills / simulator"]
    UI["Angular UI<br/>nginx :8080 in Docker"]

    TQ[["RabbitMQ<br/>telemetry exchange + queue"]]
    CQ[["RabbitMQ<br/>Celery queue"]]
    SQ[["RabbitMQ<br/>device_status queue"]]

    CON["consumer<br/>manage.py consume"]
    WRK["worker<br/>Celery: analyze_run"]
    WEB["web<br/>daphne: REST /api/, WS /ws/live/, /ws/gym/"]

    DB[("TimescaleDB<br/>runs_sample hypertable<br/>usage_hourly aggregate")]
    RD[("Redis<br/>channel layer")]

    SIM -->|"heartbeat, run_start, sample, run_end"| TQ
    TQ -->|"batches of 500 msgs / 1 s"| CON
    UI <-->|"REST + WebSocket"| WEB
    CON -->|"analyze_run after run_end"| CQ
    CQ --> WRK
    CON -->|"samples, runs, devices, alerts, dead letters"| DB
    WRK -->|"summaries, records"| DB
    WEB --> DB
    CON -->|"notify"| RD
    WRK -->|"notify"| RD
    WEB -->|"notify"| RD
    RD -.->|"groups live.user.{id}, gym"| WEB
    WEB -->|"out of order, service done"| SQ
    SQ --> SIM
```

### Live run

```mermaid
sequenceDiagram
    autonumber
    participant T as Treadmill
    participant MQ as RabbitMQ
    participant C as consumer
    participant DB as TimescaleDB
    participant W as worker
    participant R as Redis
    participant UI as Angular UI

    T->>MQ: run_start
    MQ->>C: run_start
    C->>DB: create Run (LIVE), device IN_USE
    C-->>R: device status to group gym

    loop every second
        T->>MQ: sample (hr, speed, incline)
        MQ->>C: sample
        Note over C: buffer, flush every 1 s or 500 messages
        C->>DB: bulk insert into runs_sample
        C->>MQ: ack after the DB commit
        C->>C: AlarmMonitor checks heart rate
        opt heart rate too high or missing
            C->>DB: create Alert
            C-->>R: alert to groups gym and live.user.{id}
        end
        C-->>R: live metrics to group live.user.{id}
        R-->>UI: WebSocket /ws/live/
    end

    T->>MQ: run_end
    MQ->>C: run_end
    C->>DB: Run ANALYZING, device FREE
    C->>MQ: analyze_run(run_id) after commit
    MQ->>W: analyze_run
    W->>DB: 8 steps, save RunSummary and PersonalRecord, Run DONE
    W-->>R: run DONE to group live.user.{id}
    R-->>UI: WebSocket event, UI reloads the run

    Note over C,DB: invalid message goes to runs_deadletter
    Note over C,DB: watchdog every 10 s: no data means alert, then the run is closed
```

### Database

`runs_sample` is a TimescaleDB hypertable partitioned by `time`. `usage_hourly` is a continuous aggregate over `runs_sample` (seconds of running per hour and run) that feeds the utilization heatmap. Django's built-in tables (`auth_*`, `django_*`) are left out.

```mermaid
erDiagram
    user_user ||--o| runners_runnerprofile : "has"
    user_user ||--o{ runs_run : "runs"
    gym_device ||--o{ runs_run : "used in"
    runs_run ||--o{ runs_sample : "has"
    runs_run ||--o| runs_runsummary : "has"
    runs_run ||--o{ runs_personalrecord : "sets"
    user_user ||--o{ runs_personalrecord : "holds"
    gym_device ||--o{ gym_alert : "raises"
    runs_run |o--o{ gym_alert : "during"
    runs_run ||--o{ usage_hourly : "aggregated into"
    runs_run |o--o{ pipelines_pipelinerun : "analyzed by"
    pipelines_pipelinerun ||--o{ pipelines_pipelinestep : "has"
    user_user |o--o{ token_blacklist_outstandingtoken : "owns"
    token_blacklist_outstandingtoken ||--o| token_blacklist_blacklistedtoken : "blacklisted as"

    user_user {
        bigint id PK
        varchar username UK
        varchar email
        varchar password
        varchar first_name
        varchar last_name
        varchar role "RUNNER or GYM_ADMIN"
        bool is_active
        bool is_staff
        bool is_superuser
        timestamptz last_login
        timestamptz date_joined
    }

    runners_runnerprofile {
        bigint id PK
        bigint user_id FK, UK
        decimal weight_kg
        date birth_date
        smallint hr_rest
        smallint hr_max
        int goal_distance "5000, 10000 or 21097 m"
        int goal_time_s
    }

    gym_device {
        bigint id PK
        varchar serial UK
        varchar status "FREE, IN_USE, OFFLINE, OUT_OF_ORDER"
        varchar firmware
        timestamptz last_seen
        decimal total_hours
        decimal hours_since_service
        bool needs_service
    }

    gym_alert {
        bigint id PK
        varchar type "HR_HIGH, NO_HR, DEVICE_FAULT"
        varchar message
        bigint device_id FK
        bigint run_id FK "nullable"
        timestamptz created_at
        timestamptz acknowledged_at
    }

    runs_run {
        bigint id PK
        uuid uuid UK
        bigint user_id FK
        bigint device_id FK
        varchar type "easy, intervals, tempo, long"
        timestamptz started_at
        timestamptz ended_at
        varchar status "LIVE, ANALYZING, DONE, FAILED"
        timestamptz last_data_at
        smallint rpe "1 to 10"
    }

    runs_sample {
        bigint id PK
        timestamptz time PK "hypertable partition key"
        bigint run_id FK
        int seq
        smallint hr
        float speed_kmh
        float incline
    }

    runs_runsummary {
        bigint id PK
        bigint run_id FK, UK
        int distance_m
        int duration_s
        int avg_pace_s
        smallint avg_hr
        smallint max_hr
        jsonb zones
        jsonb splits
        int trimp
        int kcal
        int cleaned_points
        timestamptz analyzed_at
    }

    runs_personalrecord {
        bigint id PK
        bigint user_id FK
        bigint run_id FK
        varchar distance "1K, 5K, 10K"
        int time_s
        timestamptz achieved_at
    }

    runs_deadletter {
        bigint id PK
        varchar routing_key
        text body
        text error
        varchar device_serial
        timestamptz created_at
    }

    usage_hourly {
        timestamptz bucket PK "1 hour bucket"
        bigint run_id PK, FK
        int seconds "number of samples"
    }

    pipelines_pipelinerun {
        bigint id PK
        varchar name "run_analysis"
        varchar status "RUNNING, DONE, FAILED"
        bigint run_id FK "nullable"
        timestamptz started_at
        timestamptz finished_at
        varchar failed_step
    }

    pipelines_pipelinestep {
        bigint id PK
        bigint pipeline_run_id FK
        smallint order
        varchar name
        varchar status "RUNNING, DONE, FAILED"
        int duration_ms
        text error
    }

    token_blacklist_outstandingtoken {
        bigint id PK
        bigint user_id FK "nullable"
        varchar jti UK
        text token
        timestamptz created_at
        timestamptz expires_at
    }

    token_blacklist_blacklistedtoken {
        bigint id PK
        bigint token_id FK, UK
        timestamptz blacklisted_at
    }
```

## Run analysis pipeline (8 steps)

Starts automatically after `run_end` (or when the runner stops the run manually) as the Celery task `analyze_run(run_id)`.

| # | Step | What it does |
| --- | --- | --- |
| 1 | `load` | Loads the run's samples from the DB ordered by time |
| 2 | `clean` | Drops nonsense values, fills gaps up to 5 s linearly |
| 3 | `distance` | Computes distance and per-kilometer splits |
| 4 | `zones` | Time in heart rate zones Z1–Z5 (Karvonen) |
| 5 | `load_metrics` | TRIMP and calories |
| 6 | `records` | Finds new personal records (1K/5K/10K) |
| 7 | `machine_usage` | Adds treadmill hours, sets "needs service" after 500 h |
| 8 | `save` | Saves `RunSummary` and records, sends the runner the WebSocket message `run DONE` |

## Lint

```bash
make lint   # ruff + mypy in api/, ruff in simulator/
```
