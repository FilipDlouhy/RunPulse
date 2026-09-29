import math
import random

HR_RISE_TAU_S = 15
HR_FALL_TAU_S = 30
FATIGUE_START_S = 20 * 60
FATIGUE_BPM_PER_MIN = 0.15
INCLINE_KMH_PER_PCT = 0.5
HR_NOISE_BPM = 2
START_HR_ABOVE_REST = 25
BASE_INTENSITY = 0.15
INTENSITY_PER_KMH = 0.05
MIN_INTENSITY = 0.2
MAX_INTENSITY = 1.0

KNOWN_RUNNERS = {
    "runner": (52, 188),
}


def heart_rate_of(username):
    if username in KNOWN_RUNNERS:
        return KNOWN_RUNNERS[username]
    same_for_this_user = random.Random(username)
    hr_rest = same_for_this_user.randint(48, 62)
    hr_max = same_for_this_user.randint(172, 193)
    return hr_rest, hr_max


class RunnerModel:
    def __init__(self, hr_rest, hr_max, fitness=1.0, rng=None):
        self.hr_rest = hr_rest
        self.hr_max = hr_max
        self.fitness = fitness
        self.rng = rng or random.Random()
        self.hr = float(hr_rest + START_HR_ABOVE_REST)

    @classmethod
    def for_user(cls, username, fitness=1.0, rng=None):
        hr_rest, hr_max = heart_rate_of(username)
        return cls(hr_rest, hr_max, fitness, rng)

    def intensity(self, speed_kmh, incline):
        effective_kmh = speed_kmh + incline * INCLINE_KMH_PER_PCT
        intensity = (BASE_INTENSITY + INTENSITY_PER_KMH * effective_kmh) / self.fitness
        return min(MAX_INTENSITY, max(MIN_INTENSITY, intensity))

    def target_hr(self, speed_kmh, incline, elapsed_s):
        target = self.hr_rest + (self.hr_max - self.hr_rest) * self.intensity(speed_kmh, incline)
        if elapsed_s > FATIGUE_START_S:
            target += (elapsed_s - FATIGUE_START_S) / 60 * FATIGUE_BPM_PER_MIN
        return target

    def step(self, speed_kmh, incline, elapsed_s):
        target = self.target_hr(speed_kmh, incline, elapsed_s)
        tau = HR_RISE_TAU_S if target > self.hr else HR_FALL_TAU_S
        self.hr += (target - self.hr) * (1 - math.exp(-1 / tau))
        return round(self.hr + self.rng.uniform(-HR_NOISE_BPM, HR_NOISE_BPM))
