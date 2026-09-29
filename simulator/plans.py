from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    duration_s: int
    speed_kmh: float
    incline: float = 0.0


def minutes(count, speed_kmh, incline=0.0):
    return Segment(round(count * 60), speed_kmh, incline)


WARM_UP = minutes(10, 8)
COOL_DOWN = minutes(5, 7)
INTERVAL_REPEATS = 6


def interval_plan():
    plan = [WARM_UP]
    for _ in range(INTERVAL_REPEATS):
        plan.append(minutes(3, 14))
        plan.append(minutes(2, 8))
    plan.append(COOL_DOWN)
    return plan


PLANS = {
    "easy": [minutes(5, 8), minutes(35, 10), minutes(5, 7)],
    "intervals": interval_plan(),
    "tempo": [WARM_UP, minutes(20, 12.5), COOL_DOWN],
    "long": [minutes(90, 9.5)],
}

RUN_TYPES = tuple(PLANS)


def plan_for(run_type, rng=None):
    if run_type == "long" and rng is not None:
        return [minutes(rng.randint(60, 90), 9.5)]
    return PLANS[run_type]


def duration_s(plan):
    return sum(segment.duration_s for segment in plan)
