from django.db import migrations

ENABLE_EXTENSION = "CREATE EXTENSION IF NOT EXISTS timescaledb;"

WIDEN_PRIMARY_KEY = """
ALTER TABLE runs_sample DROP CONSTRAINT IF EXISTS runs_sample_pkey;
ALTER TABLE runs_sample ADD CONSTRAINT runs_sample_pkey PRIMARY KEY (id, time);
"""
NARROW_PRIMARY_KEY = """
ALTER TABLE runs_sample DROP CONSTRAINT IF EXISTS runs_sample_pkey;
ALTER TABLE runs_sample ADD CONSTRAINT runs_sample_pkey PRIMARY KEY (id);
"""

CREATE_HYPERTABLE = "SELECT create_hypertable('runs_sample', 'time', if_not_exists => TRUE, migrate_data => TRUE);"

CREATE_CONTINUOUS_AGGREGATE = """
CREATE MATERIALIZED VIEW usage_hourly
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    run_id,
    count(*) AS seconds
FROM runs_sample
GROUP BY bucket, run_id
WITH NO DATA;
"""
DROP_CONTINUOUS_AGGREGATE = "DROP MATERIALIZED VIEW IF EXISTS usage_hourly CASCADE;"

ADD_REFRESH_POLICY = """
SELECT add_continuous_aggregate_policy('usage_hourly',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '15 minutes');
"""
REMOVE_REFRESH_POLICY = "SELECT remove_continuous_aggregate_policy('usage_hourly', if_exists => TRUE);"


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('runs', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(ENABLE_EXTENSION, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(WIDEN_PRIMARY_KEY, reverse_sql=NARROW_PRIMARY_KEY),
        migrations.RunSQL(CREATE_HYPERTABLE, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(CREATE_CONTINUOUS_AGGREGATE, reverse_sql=DROP_CONTINUOUS_AGGREGATE),
        migrations.RunSQL(ADD_REFRESH_POLICY, reverse_sql=REMOVE_REFRESH_POLICY),
    ]
