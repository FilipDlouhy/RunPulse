from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd

from apps.pipelines.services.pipeline_runner import PipelineAbort
from apps.runners.calculations import heart_rate_limits, karvonen_zones, zone_of
from apps.runs.models import RECORD_METERS

DEFAULT_WEIGHT_KG = 70.0
HR_MIN = 40
HR_MAX = 230
MAX_GAP_S = 5
MIN_LAST_SPLIT_M = 100
COLUMNS = ["seq", "hr", "speed", "incline"]


def to_int(value):
    if value is None:
        return None
    value = float(value)
    if np.isnan(value):
        return None
    return int(round(value))


def tenths(value):
    return Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def short_gaps(missing, max_gap):
    short = [False] * len(missing)
    gap_start = None
    for index, is_missing in enumerate(missing):
        if is_missing and gap_start is None:
            gap_start = index
        if not is_missing and gap_start is not None:
            if index - gap_start <= max_gap:
                for gap_index in range(gap_start, index):
                    short[gap_index] = True
            gap_start = None
    return pd.Series(short, index=missing.index)


def fill_short_gaps(series, max_gap):
    interpolated = series.interpolate(limit_area="inside")
    is_short_gap = short_gaps(series.isna(), max_gap)
    can_fill = is_short_gap & interpolated.notna()
    filled_series = series.mask(can_fill, interpolated)
    return filled_series, can_fill


def second_when_reached(cumulative, meters):
    after = int(np.searchsorted(cumulative, meters))
    before = after - 1
    meters_in_that_second = cumulative[after] - cumulative[before]
    part_of_second = (meters - cumulative[before]) / meters_in_that_second
    return before + part_of_second


def mean_hr(hr, start, end):
    first = int(start)
    last = max(int(np.ceil(end)), first + 1)
    window = hr[first:last]
    if np.isnan(window).all():
        return None
    return to_int(np.nanmean(window))


def splits_of(cumulative, hr):
    total = cumulative[-1]
    full_km = int(total // 1000)
    rest = total - full_km * 1000

    marks = [0.0]
    for km in range(1, full_km + 1):
        marks.append(second_when_reached(cumulative, km * 1000))
    if rest >= MIN_LAST_SPLIT_M:
        marks.append(float(len(cumulative) - 1))

    splits = []
    for number in range(1, len(marks)):
        start = marks[number - 1]
        end = marks[number]
        if number <= full_km:
            meters = 1000
        else:
            meters = rest
        seconds = end - start
        splits.append({
            "km": number,
            "distance_m": round(meters),
            "time_s": round(seconds),
            "pace_s": round(seconds / (meters / 1000)),
            "avg_hr": mean_hr(hr, start, end),
        })
    return splits


def fastest(cumulative, meters):
    best = None
    for start in range(len(cumulative)):
        target = cumulative[start] + meters
        if target > cumulative[-1]:
            break
        seconds = second_when_reached(cumulative, target) - start
        if best is None or seconds < best:
            best = seconds
    if best is None:
        return None
    return round(float(best))


def clean(ctx):
    samples = ctx["samples"].drop_duplicates("seq")
    last_second = int(samples["seq"].max())
    frame = samples.set_index("seq").reindex(range(last_second + 1))
    frame.index.name = "t"

    too_low = frame["hr"] < HR_MIN
    too_high = frame["hr"] > HR_MAX
    invalid = too_low | too_high
    frame.loc[invalid, "hr"] = np.nan

    repaired = invalid
    for column in ["hr", "speed", "incline"]:
        filled_series, filled = fill_short_gaps(frame[column], MAX_GAP_S)
        frame[column] = filled_series
        repaired = repaired | filled
    frame["speed"] = frame["speed"].fillna(0.0)
    frame["incline"] = frame["incline"].ffill().bfill().fillna(0.0)

    ctx["frame"] = frame
    ctx["cleaned_points"] = int(repaired.sum())
    return ctx


def distance(ctx):
    frame = ctx["frame"]
    meters_per_second = frame["speed"].to_numpy() / 3.6
    cumulative = np.concatenate([[0.0], np.cumsum(meters_per_second)])
    total = float(cumulative[-1])
    duration = len(frame)

    if total >= MIN_LAST_SPLIT_M:
        avg_pace_s = round(duration / (total / 1000))
    else:
        avg_pace_s = None

    ctx["cumulative"] = cumulative
    ctx["distance_m"] = total
    ctx["duration_s"] = duration
    ctx["avg_pace_s"] = avg_pace_s
    ctx["splits"] = splits_of(cumulative, frame["hr"].to_numpy())
    return ctx


def zones(ctx):
    hr = ctx["frame"]["hr"].dropna().to_numpy()
    bounds = karvonen_zones(ctx["hr_rest"], ctx["hr_max"])

    zone_seconds = [0, 0, 0, 0, 0]
    for value in hr:
        zone = zone_of(value, bounds)
        zone_seconds[zone - 1] += 1
    ctx["zone_seconds"] = zone_seconds

    if len(hr) > 0:
        ctx["avg_hr"] = to_int(hr.mean())
        ctx["max_hr"] = to_int(hr.max())
    else:
        ctx["avg_hr"] = None
        ctx["max_hr"] = None
    return ctx


def load_metrics(ctx):
    trimp = 0
    for zone, seconds in enumerate(ctx["zone_seconds"], start=1):
        trimp += seconds / 60 * zone
    ctx["trimp"] = round(trimp)
    ctx["kcal"] = round(ctx["weight_kg"] * ctx["distance_m"] / 1000)
    return ctx


def records(ctx):
    found = {}
    for record_distance, meters in RECORD_METERS.items():
        time_s = fastest(ctx["cumulative"], meters)
        if time_s is not None:
            found[record_distance] = time_s
    ctx["records"] = found
    return ctx


def machine_usage(ctx):
    ctx["device_hours"] = tenths(ctx["duration_s"] / 3600)
    return ctx


class RunAnalysisPipeline:
    name = "run_analysis"

    def __init__(
        self,
        *,
        pipeline_runner,
        run_repository,
        sample_repository,
        runner_profile_repository,
        analysis_service,
    ):
        self.pipeline_runner = pipeline_runner
        self.run_repository = run_repository
        self.sample_repository = sample_repository
        self.runner_profile_repository = runner_profile_repository
        self.analysis_service = analysis_service

    def run(self, run_id):
        steps = [self.load, clean, distance, zones, load_metrics, records, machine_usage, self.save]
        return self.pipeline_runner.run(self.name, steps, {"run_id": run_id}, run_id=run_id)

    def load(self, ctx):
        run = self.run_repository.get_with_device_and_user(ctx["run_id"])
        if run is None or run.is_live:
            raise PipelineAbort("The run does not exist or is still live.")
        rows = self.sample_repository.rows_of_run(run)
        if not rows:
            raise PipelineAbort("The run has no data.")

        profile = self.runner_profile_repository.get_by_user(run.user)
        hr_rest, hr_max = heart_rate_limits(profile, run.started_at.date())

        weight_kg = DEFAULT_WEIGHT_KG
        if profile is not None and profile.weight_kg:
            weight_kg = float(profile.weight_kg)

        samples = pd.DataFrame(rows, columns=COLUMNS, dtype="float64")
        samples = samples.astype({"seq": "int64"})

        ctx["run"] = run
        ctx["samples"] = samples
        ctx["hr_rest"] = hr_rest
        ctx["hr_max"] = hr_max
        ctx["weight_kg"] = weight_kg
        return ctx

    def save(self, ctx):
        self.analysis_service.save_result(
            run_id=ctx["run_id"],
            summary={
                "distance_m": round(ctx["distance_m"]),
                "duration_s": ctx["duration_s"],
                "avg_pace_s": ctx["avg_pace_s"],
                "avg_hr": ctx["avg_hr"],
                "max_hr": ctx["max_hr"],
                "zones": ctx["zone_seconds"],
                "splits": ctx["splits"],
                "trimp": ctx["trimp"],
                "kcal": ctx["kcal"],
                "cleaned_points": ctx["cleaned_points"],
            },
            records=ctx["records"],
            device_hours=ctx["device_hours"],
        )
        return ctx
