import argparse
import os
import random
import time
import uuid
from datetime import UTC, datetime, timedelta

from gym import GYM_TZ, GymSimulator, Peaks, gym_members, load_config, parse_open
from plans import RUN_TYPES, duration_s, plan_for
from publisher import Publisher
from runner_model import RunnerModel
from telemetry import chaos, load_messages, parse_ts, run_end, run_messages

DEFAULT_URL = os.environ.get("RABBITMQ_URL", "amqp://runpulse:runpulse@localhost:5672/%2F")
DEFAULT_CONFIG = "config.yaml"
PROGRESS_EVERY_S = 5
STATUS_EVERY_S = 1


def publish_realtime(publisher, messages, start, speedup=1.0, show_minutes=False):
    began = time.monotonic()
    report_at = began + PROGRESS_EVERY_S
    for message in messages:
        ts = parse_ts(message.get("ts"))
        if ts is not None:
            delay = began + (ts - start).total_seconds() / speedup - time.monotonic()
            if delay > 0:
                publisher.sleep(delay)
        publisher.publish(message)
        if show_minutes and message["type"] == "sample" and message.get("seq", 1) % 60 == 0:
            print(f"  {message['seq'] // 60:>3} min  hr {message.get('hr')}  {message.get('speed_kmh')} km/h")
        if time.monotonic() >= report_at:
            elapsed = time.monotonic() - began
            print(f"  sent {publisher.sent} messages ({publisher.sent / elapsed:.0f}/s)")
            report_at += PROGRESS_EVERY_S


def simulate_run(args, publisher, rng, config):
    start = datetime.now(UTC)
    run_uuid = str(uuid.uuid4())
    model = RunnerModel.for_user(args.user, rng=rng)
    plan = plan_for(args.type, rng)
    messages = run_messages(plan, model, device=args.device, user=args.user, run_type=args.type, start=start, run_uuid=run_uuid)
    if args.chaos:
        messages = chaos(messages, rng)

    print(f"{args.type} run of {args.user} on {args.device}: {duration_s(plan) // 60} min at {args.speedup}x, run {run_uuid}")
    try:
        publish_realtime(publisher, messages, start, args.speedup, show_minutes=True)
    except KeyboardInterrupt:
        publisher.publish(run_end(args.device, run_uuid, datetime.now(UTC)))
        print("Stopped, run ended early.")
    print(f"Sent {publisher.sent} messages.")


def build_gym(publisher, config, rng, heartbeats, start):
    devices = [f"TREAD-{i:02d}" for i in range(1, config.treadmills + 1)]
    members = gym_members(config.members)
    open_hour, close_hour = parse_open(config.open)
    peaks = Peaks(open_hour, close_hour, config.peaks)
    return GymSimulator(publisher, devices, members, peaks, start, rng, heartbeats, config.out_of_order)


def gym_start(start_arg):
    now = datetime.now(GYM_TZ)
    if start_arg:
        hour, minute = start_arg.split(":")
        now = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    return now.astimezone(UTC)


def run_gym(args, publisher, rng, config):
    start = gym_start(args.start)
    sim = build_gym(publisher, config, rng, heartbeats=True, start=start)
    print(f"Gym '{config.name}': {len(sim.devices)} treadmills, {len(sim.members)} members, speedup {args.speedup}x")

    began = time.monotonic()
    checked_at = time.monotonic()
    try:
        while True:
            sim.tick()
            if time.monotonic() - checked_at >= STATUS_EVERY_S:
                for message in publisher.device_statuses():
                    sim.set_device_status(message["device"], message["status"])
                checked_at = time.monotonic()
            publisher.sleep(1.0 / args.speedup)
    except KeyboardInterrupt:
        elapsed = time.monotonic() - began
        print(f"Stopped after {elapsed:.0f}s, sent {publisher.sent} messages.")


def run_backfill(args, publisher, rng, config):
    now = datetime.now(UTC)
    start = (now.astimezone(GYM_TZ) - timedelta(weeks=args.weeks)).replace(hour=0, minute=0, second=0, microsecond=0)
    start = start.astimezone(UTC)
    sim = build_gym(publisher, config, rng, heartbeats=False, start=start)

    began = time.monotonic()
    while sim.clock < now:
        sim.tick()
    elapsed = time.monotonic() - began
    print(f"Backfilled {args.weeks} weeks, {publisher.sent} messages in {elapsed:.1f}s.")


def run_load(args, publisher, rng, config):
    devices = [f"LOAD-{i:03d}" for i in range(1, args.devices + 1)]
    start = datetime.now(UTC)
    messages = load_messages(devices, user="loadbot", rate=args.rate, duration_s=args.duration, start=start, rng=rng)
    print(f"Load test: {args.devices} devices x {args.rate} msg/s = {args.devices * args.rate} msg/s for {args.duration}s")
    publish_realtime(publisher, messages, start)
    print(f"Sent {publisher.sent} messages.")


def parse_args(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--url", default=DEFAULT_URL, help="RabbitMQ URL")
    common.add_argument("--seed", type=int, default=None, help="random seed for repeatable data")
    common.add_argument("--config", default=DEFAULT_CONFIG, help="gym config yaml")

    parser = argparse.ArgumentParser(description="RunPulse treadmill simulator")
    modes = parser.add_subparsers(dest="mode", required=True)

    gym = modes.add_parser("gym", parents=[common], help="live gym: arrivals, runs and heartbeats")
    gym.add_argument("--speedup", type=float, default=60.0)
    gym.add_argument("--start", default=None, help="HH:MM local time, default now")

    run = modes.add_parser("run", parents=[common], help="one run in real time")
    run.add_argument("--type", choices=RUN_TYPES, default="intervals")
    run.add_argument("--device", default="TREAD-01")
    run.add_argument("--user", default="runner")
    run.add_argument("--speedup", type=float, default=1.0)
    run.add_argument("--chaos", action="store_true", help="drop HR, send nonsense and duplicates")

    backfill = modes.add_parser("backfill", parents=[common], help="weeks of past gym history, as fast as possible")
    backfill.add_argument("--weeks", type=int, default=8)

    load = modes.add_parser("load", parents=[common], help="many devices with random data")
    load.add_argument("--devices", type=int, default=500)
    load.add_argument("--rate", type=float, default=10, help="messages per second per device")
    load.add_argument("--duration", type=float, default=60, help="seconds")

    return parser.parse_args(argv)


MODES = {"gym": run_gym, "run": simulate_run, "backfill": run_backfill, "load": run_load}


def main(argv=None):
    args = parse_args(argv)
    config = load_config(args.config)
    seed = config.seed
    if args.seed is not None:
        seed = args.seed
    rng = random.Random(seed)
    publisher = Publisher(args.url)
    try:
        MODES[args.mode](args, publisher, rng, config)
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
