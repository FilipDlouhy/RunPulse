"""
Gym simulator: member arrivals, run sessions, heartbeats, and device status
management.
"""
import random
import uuid
from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

import yaml

from plans import RUN_TYPES, plan_for
from runner_model import RunnerModel
from telemetry import FIRMWARE, HEARTBEAT_EVERY_S, SURGE_S, chaos, heartbeat, parse_ts, run_messages, surge

GYM_TZ = ZoneInfo("Europe/Prague")
MEMBER_TRAITS_SEED = 42                 # deterministic member generation
FITNESS_GAIN_PER_WEEK = 0.012           # fitness improves by 1.2% per week for improving members
CHAOS_FRACTION = 0.12                   # 12% of runs get random errors
SURGE_FRACTION = 0.1                    # 10% of runs may get a heart rate surge
OUT_OF_ORDER = "OUT_OF_ORDER"           # status value indicating a broken treadmill


def member_traits(index):
    """Generate deterministic traits for a member based on their index."""
    rng = random.Random(MEMBER_TRAITS_SEED + index)
    age = rng.randint(20, 55)
    hr_rest = rng.randint(48, 68)
    hr_max = 208 - round(0.7 * age)
    weekly_runs = rng.randint(1, 4)
    improving = rng.random() < 0.5
    return age, hr_rest, hr_max, weekly_runs, improving


class Member:
    """Gym member with fitness characteristics affecting their run behavior."""
    def __init__(self, username, age, hr_rest, hr_max, weekly_runs, improving):
        self.username = username
        self.age = age
        self.hr_rest = hr_rest
        self.hr_max = hr_max
        self.weekly_runs = weekly_runs
        self.improving = improving

    @classmethod
    def from_index(cls, index):
        age, hr_rest, hr_max, weekly_runs, improving = member_traits(index)
        return cls(f"member{index:03d}", age, hr_rest, hr_max, weekly_runs, improving)

    def pick_plan(self, rng):
        return rng.choice(RUN_TYPES)

    def fitness(self, weeks_elapsed):
        if not self.improving:
            return 1.0
        return 1 + weeks_elapsed * FITNESS_GAIN_PER_WEEK


def gym_members(count):
    """Create gym members with deterministic traits plus a known test runner."""
    members = [Member.from_index(index) for index in range(1, count + 1)]
    members.append(Member("runner", None, 52, 188, 4, True))
    return members


@dataclass
class Peaks:
    """Hourly traffic intensity multipliers: 0.0 when closed, 0.2-1.0 when open."""
    open_hour: int
    close_hour: int
    values: dict
    default: float = 0.2

    def at(self, hour):
        if not (self.open_hour <= hour < self.close_hour):
            return 0.0
        return self.values.get(hour, self.default)


def hour_of(time_text):
    """Extract hour from HH:MM time string."""
    return int(time_text.split(":")[0])


def parse_open(text):
    """Parse "HH:MM-HH:MM" to (open_hour, close_hour)."""
    start, end = text.split("-")
    return hour_of(start), hour_of(end)


@dataclass
class GymConfig:
    seed: int
    name: str
    treadmills: int
    out_of_order: list
    open: str
    peaks: dict
    members: int


def load_config(path):
    with open(path, encoding="utf-8") as file:
        data = yaml.safe_load(file)
    gym = data["gym"]
    return GymConfig(
        seed=data["seed"],
        name=gym["name"],
        treadmills=gym["treadmills"],
        out_of_order=gym["out_of_order"],
        open=gym["open"],
        peaks={int(hour): value for hour, value in gym["peaks"].items()},
        members=gym["members"],
    )


def sample_gaps(messages):
    """Find time periods where samples are missing (> 1s apart)."""
    gaps = []
    last_ts = None
    for message in messages:
        if message["type"] != "sample":
            continue
        ts = parse_ts(message["ts"])
        if last_ts is not None and (ts - last_ts).total_seconds() > 1:
            gaps.append((last_ts, ts))
        last_ts = ts
    return gaps


class RunSession:
    """A single member's run on a treadmill: yields messages as clock advances."""
    def __init__(self, member, device, messages, gaps):
        self.member = member
        self.device = device
        self.messages = messages
        self.gaps = gaps
        self.pos = 0

    @classmethod
    def start(cls, member, device, run_type, plan, model, clock, rng):
        run_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"runpulse/{device}/{member.username}/{clock.isoformat()}"))
        stream = run_messages(plan, model, device=device, user=member.username, run_type=run_type, start=clock, run_uuid=run_uuid)
        if rng.random() < CHAOS_FRACTION:
            stream = chaos(stream, rng)
        messages = list(stream)

        if rng.random() < SURGE_FRACTION:
            sample_count = sum(1 for message in messages if message["type"] == "sample")
            if sample_count > SURGE_S + 60:
                at_s = rng.randint(30, sample_count - SURGE_S - 30)
                messages = list(surge(iter(messages), hr_max=member.hr_max, at_s=at_s))

        return cls(member, device, messages, sample_gaps(messages))

    def pending(self, clock):
        while self.pos < len(self.messages) and parse_ts(self.messages[self.pos]["ts"]) <= clock:
            yield self.messages[self.pos]
            self.pos += 1

    @property
    def finished(self):
        return self.pos >= len(self.messages)

    def is_faulty(self, clock):
        for start, end in self.gaps:
            if start <= clock < end:
                return True
        return False


class GymSimulator:
    """Simulates a gym: member arrivals weighted by time-of-day, active runs, device status."""
    def __init__(self, publisher, devices, members, peaks, start, rng, heartbeats=True, out_of_order=()):
        self.publisher = publisher
        self.devices = list(devices)
        self.members = list(members)
        self.peaks = peaks
        self.clock = start
        self.rng = rng
        self.heartbeats = heartbeats

        self.out_of_order = set(out_of_order)
        self.free = []
        for device in self.devices:
            if device not in self.out_of_order:
                self.free.append(device)
        self.active = {}
        self.running = set()
        self.sim_start = start
        self.next_heartbeat = start
        self.daily_target = sum(member.weekly_runs for member in self.members) / 7
        self.weight_total = sum(self.peaks.at(hour) for hour in range(24)) or 1.0

    def _local_hour(self):
        return self.clock.astimezone(GYM_TZ).hour

    def _try_arrival(self, dt):
        # ---- check if anyone can arrive
        if not self.free:
            return
        weight = self.peaks.at(self._local_hour())
        if weight <= 0:
            return
        rate_per_s = self.daily_target * weight / self.weight_total / 3600
        if self.rng.random() >= rate_per_s * dt:
            return

        # ---- pick a free member and device
        pool = [member for member in self.members if member.username not in self.running]
        if not pool:
            return
        member = self.rng.choices(pool, weights=[member.weekly_runs for member in pool])[0]
        device = self.rng.choice(self.free)
        self.free.remove(device)

        # ---- create and start a run session
        weeks_elapsed = (self.clock - self.sim_start).days // 7
        run_type = member.pick_plan(self.rng)
        plan = plan_for(run_type, self.rng)
        model = RunnerModel(member.hr_rest, member.hr_max, fitness=member.fitness(weeks_elapsed), rng=self.rng)
        session = RunSession.start(member, device, run_type, plan, model, self.clock, self.rng)

        self.active[device] = session
        self.running.add(member.username)

    def set_device_status(self, device, status):
        """Apply a status from the backend: OUT_OF_ORDER removes treadmill and running session."""
        if device not in self.devices:
            return
        if status == OUT_OF_ORDER:
            self.out_of_order.add(device)
            if device in self.free:
                self.free.remove(device)
            if device in self.active:
                session = self.active[device]
                del self.active[device]
                self.running.discard(session.member.username)
            return
        if device in self.out_of_order:
            self.out_of_order.remove(device)
            self.free.append(device)

    def _send_heartbeats(self):
        if not self.heartbeats or self.clock < self.next_heartbeat:
            return
        for device in self.devices:
            session = self.active.get(device)
            status = "ok"
            if session is not None and session.is_faulty(self.clock):
                status = "fault"
            self.publisher.publish(heartbeat(device, status, FIRMWARE, self.clock))
        self.next_heartbeat = self.clock + timedelta(seconds=HEARTBEAT_EVERY_S)

    def tick(self, dt=1.0):
        """Advance the clock by dt seconds: process arrivals, active runs, and heartbeats."""
        self._try_arrival(dt)

        for device, session in list(self.active.items()):
            for message in session.pending(self.clock):
                self.publisher.publish(message)
            if session.finished:
                del self.active[device]
                self.free.append(device)
                self.running.discard(session.member.username)

        self._send_heartbeats()
        self.clock += timedelta(seconds=dt)
