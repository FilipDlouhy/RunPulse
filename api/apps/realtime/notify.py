"""
Push WebSocket events to runners and gym admins through the Channels layer (Redis).
"""
import asyncio
import logging
import threading

from channels.layers import get_channel_layer
from django.db import transaction

from apps.gym_admin.dtos import AlertResponseSerializer
from apps.runs.dtos import RunAlertResponseSerializer

logger = logging.getLogger(__name__)

SEND_TIMEOUT_S = 5            # timeout for group_send calls

GYM_GROUP = "gym"             # gym admin broadcast group

DEVICES_EVENT = {"type": "devices"}


def notify_user(user_id, payload):
    _send_many([(f"live.user.{user_id}", payload)])


def notify_users(payloads):
    """Send events to multiple users (list of (user_id, payload) tuples)."""
    messages = []
    for user_id, payload in payloads:
        messages.append((f"live.user.{user_id}", payload))
    _send_many(messages)


def notify_gym(payload):
    _send_many([(GYM_GROUP, payload)])


def notify_user_on_commit(user_id, payload):
    # after commit only, a rolled-back change sends nothing
    transaction.on_commit(lambda: notify_user(user_id, payload))


def notify_gym_on_commit(payload):
    # after commit only, a rolled-back change sends nothing
    transaction.on_commit(lambda: notify_gym(payload))


def notify_devices_changed():
    """Tell the gym page to reload the treadmill list."""
    notify_gym_on_commit(DEVICES_EVENT)


def notify_run_status(user_id, run_id, status, new_records=0):
    """Notify user when run analysis completes or fails (includes new record count)."""
    notify_user_on_commit(user_id, {"type": "run", "run_id": run_id, "status": status, "new_records": new_records})


def notify_alert(alert):
    """Broadcast alert to gym; also notify user if alert is tied to a run."""
    notify_gym_on_commit({"type": "alert", "alert": AlertResponseSerializer(alert).data})
    if alert.run_id:
        notify_user_on_commit(alert.run.user_id, {"type": "alert", "alert": RunAlertResponseSerializer(alert).data})


def _send_many(messages):
    if not messages:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        # one shared event loop, async_to_sync per call was too slow for the consumer
        future = asyncio.run_coroutine_threadsafe(_group_send_all(layer, messages), _background_loop())
        future.result(SEND_TIMEOUT_S)
    except Exception as error:
        logger.warning("Realtime notify to %s groups failed: %s", len(messages), error)


_loop = None


def _background_loop():
    global _loop
    if _loop is None:
        _loop = asyncio.new_event_loop()
        thread = threading.Thread(target=_loop.run_forever, name="realtime-notify", daemon=True)
        thread.start()
    return _loop


async def _group_send_all(layer, messages):
    for group, payload in messages:
        await layer.group_send(group, {"type": "send_event", "payload": payload})
