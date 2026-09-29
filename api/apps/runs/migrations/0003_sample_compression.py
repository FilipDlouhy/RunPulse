from django.db import migrations

ENABLE_COMPRESSION = """
ALTER TABLE runs_sample SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'run_id',
    timescaledb.compress_orderby = 'seq, time, id'
);
"""
DISABLE_COMPRESSION = """
SELECT decompress_chunk(chunk, if_compressed => TRUE) FROM show_chunks('runs_sample') AS chunk;
ALTER TABLE runs_sample SET (timescaledb.compress = false);
"""

ADD_COMPRESSION_POLICY = "SELECT add_compression_policy('runs_sample', INTERVAL '7 days', if_not_exists => TRUE);"
REMOVE_COMPRESSION_POLICY = "SELECT remove_compression_policy('runs_sample', if_exists => TRUE);"


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('runs', '0002_timescale'),
    ]

    operations = [
        migrations.RunSQL(ENABLE_COMPRESSION, reverse_sql=DISABLE_COMPRESSION),
        migrations.RunSQL(ADD_COMPRESSION_POLICY, reverse_sql=REMOVE_COMPRESSION_POLICY),
    ]
