import uuid
from datetime import datetime, timedelta

HEARTBEAT_EVERY_S = 30
FIRMWARE = "3.2.1"
SURGE_S = 90
SURGE_PCT = 0.99

HR_OUTAGE_CHANCE = 1 / 900
DEVICE_OUTAGE_CHANCE = 1 / 1800
NONSENSE_CHANCE = 0.002
DUPLICATE_CHANCE = 0.01


def iso(ts):
    return ts.isoformat().replace("+00:00", "Z")


def parse_ts(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def heartbeat(device, status, firmware, ts):
    return {"type": "heartbeat", "device": device, "status": status, "firmware": firmware, "ts": iso(ts)}


def run_start(device, user, run_uuid, run_type, ts):
    return {"type": "run_start", "device": device, "user": user, "run_uuid": run_uuid, "run_type": run_type, "ts": iso(ts)}


def run_end(device, run_uuid, ts):
    return {"type": "run_end", "device": device, "run_uuid": run_uuid, "ts": iso(ts)}


def sample(device, run_uuid, seq, ts, hr, speed_kmh, incline):
    return {
        "type": "sample",
        "device": device,
        "run_uuid": run_uuid,
        "seq": seq,
        "ts": iso(ts),
        "hr": hr,
        "speed_kmh": speed_kmh,
        "incline": incline,
    }


def run_messages(plan, model, *, device, user, run_type, start, run_uuid=None):
    run_uuid = str(run_uuid or uuid.uuid4())
    yield run_start(device, user, run_uuid, run_type, start)

    elapsed = 0
    for segment in plan:
        for _ in range(segment.duration_s):
            ts = start + timedelta(seconds=elapsed)
            hr = model.step(segment.speed_kmh, segment.incline, elapsed)
            yield sample(device, run_uuid, elapsed, ts, hr, segment.speed_kmh, segment.incline)
            elapsed += 1

    yield run_end(device, run_uuid, start + timedelta(seconds=elapsed))


def load_messages(devices, *, user, rate, duration_s, start, rng):
    runs = {device: str(uuid.uuid4()) for device in devices}
    for device, run_uuid in runs.items():
        yield run_start(device, user, run_uuid, "easy", start)

    ticks = int(duration_s * rate)
    for tick in range(ticks):
        ts = start + timedelta(seconds=tick / rate)
        for device, run_uuid in runs.items():
            speed = round(rng.uniform(6, 16), 1)
            yield sample(device, run_uuid, tick, ts, rng.randint(90, 185), speed, rng.choice([0, 1, 2]))

    end = start + timedelta(seconds=ticks / rate)
    for device, run_uuid in runs.items():
        yield run_end(device, run_uuid, end)


def with_value(message, key, value):
    changed = dict(message)
    changed[key] = value
    return changed


def without(message, key):
    changed = dict(message)
    del changed[key]
    return changed


def broken(message, rng):
    kind = rng.choice(["hr", "speed", "missing"])
    if kind == "hr":
        return with_value(message, "hr", 999)
    if kind == "speed":
        return with_value(message, "speed_kmh", -3)
    return without(message, "incline")


def chaos(
    messages,
    rng,
    *,
    hr_outage_chance=HR_OUTAGE_CHANCE,
    device_outage_chance=DEVICE_OUTAGE_CHANCE,
    nonsense_chance=NONSENSE_CHANCE,
    duplicate_chance=DUPLICATE_CHANCE,
):
    hr_outage_left = 0
    device_outage_left = 0
    for message in messages:
        if message["type"] != "sample":
            yield message
            continue

        if not hr_outage_left and not device_outage_left:
            if rng.random() < device_outage_chance:
                device_outage_left = rng.randint(15, 30)
            elif rng.random() < hr_outage_chance:
                hr_outage_left = rng.randint(10, 40)

        if device_outage_left:
            device_outage_left -= 1
            continue

        if hr_outage_left:
            message = with_value(message, "hr", None)
            hr_outage_left -= 1

        if rng.random() < nonsense_chance:
            yield broken(message, rng)
            continue
        yield message
        if rng.random() < duplicate_chance:
            yield dict(message)


def surge(messages, *, hr_max, at_s, duration_s=SURGE_S):
    hr = round(hr_max * SURGE_PCT)
    for message in messages:
        if message["type"] == "sample" and at_s <= message["seq"] < at_s + duration_s:
            message = with_value(message, "hr", hr)
        yield message
