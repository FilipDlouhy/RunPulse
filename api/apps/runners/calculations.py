"""
Running performance calculations: heart rate zones, predictions based on personal records.
"""
from .models import RaceDistance

ZONE_BOUNDS = [(1, 0.5, 0.6), (2, 0.6, 0.7), (3, 0.7, 0.8), (4, 0.8, 0.9), (5, 0.9, 1.0)]  # Karvonen zones
RIEGEL_EXPONENT = 1.06                # race time scaling exponent
DEFAULT_HR_REST = 60                  # default resting heart rate
DEFAULT_HR_MAX = 190                  # default max heart rate when profile not available


def age(birth_date, today):
    years = today.year - birth_date.year
    before_birthday = today.month < birth_date.month
    if today.month == birth_date.month:
        before_birthday = today.day < birth_date.day
    if before_birthday:
        years -= 1
    return years


def effective_hr_max(profile, today):
    """Return (max_bpm, is_estimated). Use measured value if available, else calculate from age."""
    if profile.hr_max:
        return profile.hr_max, False
    if profile.birth_date:
        return 220 - age(profile.birth_date, today), True
    return None, False


def heart_rate_limits(profile, today):
    if profile is None:
        return DEFAULT_HR_REST, DEFAULT_HR_MAX

    hr_rest = profile.hr_rest
    if not hr_rest:
        hr_rest = DEFAULT_HR_REST

    hr_max, _estimated = effective_hr_max(profile, today)
    if not hr_max:
        hr_max = DEFAULT_HR_MAX

    return hr_rest, hr_max


def karvonen_zones(hr_rest, hr_max):
    """Calculate 5 training zones using Karvonen formula (percentage of heart rate reserve)."""
    reserve = hr_max - hr_rest
    zones = []
    for zone, low, high in ZONE_BOUNDS:
        zones.append(
            {
                "zone": zone,
                "min_bpm": round(hr_rest + reserve * low),
                "max_bpm": round(hr_rest + reserve * high),
            }
        )
    return zones


def zone_of(hr, zones):
    """Return the highest training zone matching the given heart rate."""
    if hr is None:
        return None
    current = 1
    for zone in zones:
        if hr >= zone["min_bpm"]:
            current = zone["zone"]
    return current


def riegel(time_s, from_m, to_m):
    """Predict race time for distance to_m based on known time_s at distance from_m."""
    return time_s * (to_m / from_m) ** RIEGEL_EXPONENT


def goal_summary(profile):
    if not profile.goal_distance or not profile.goal_time_s:
        return None

    predictions = []
    for distance in RaceDistance:
        predictions.append(
            {
                "distance": distance.value,
                "label": distance.label,
                "time_s": round(riegel(profile.goal_time_s, profile.goal_distance, distance.value)),
            }
        )

    return {
        "pace_s_per_km": round(profile.goal_time_s / (profile.goal_distance / 1000)),
        "predictions": predictions,
    }
