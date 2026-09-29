from apps.runners.calculations import zone_of


def elapsed_s(started_at, ts):
    return round((ts - started_at).total_seconds())


def pace_s(speed_kmh):
    if speed_kmh < 1:
        return None
    return round(3600 / speed_kmh)


def live_metrics(*, started_at, ts, hr, speed_kmh, incline, zones, distance_m):
    return {
        "elapsed_s": elapsed_s(started_at, ts),
        "hr": hr,
        "zone": zone_of(hr, zones),
        "speed_kmh": speed_kmh,
        "pace_s": pace_s(speed_kmh),
        "incline": incline,
        "distance_m": round(distance_m),
    }


def live_sample(*, started_at, seq, ts, hr, speed_kmh):
    return {"seq": seq, "t": elapsed_s(started_at, ts), "hr": hr, "speed_kmh": speed_kmh}
