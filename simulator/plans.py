"""
Run plans: segments with speed, incline, and duration for different workout types.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    """A uniform run segment: speed and incline held constant for duration_s seconds."""
    duration_s: int
    speed_kmh: float
    incline: float = 0.0


def minutes(count, speed_kmh, incline=0.0):
    """Create a segment from duration in minutes."""
    return Segment(round(count * 60), speed_kmh, incline)


WARM_UP = minutes(10, 8)               # shared warm-up segment
COOL_DOWN = minutes(5, 7)              # shared cool-down segment
INTERVAL_REPEATS = 6                   # number of fast/slow intervals


def interval_plan():
    """Build interval workout: warm-up, fast/slow repeats, cool-down."""
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
    """Total duration of a plan in seconds."""
    return sum(segment.duration_s for segment in plan)
