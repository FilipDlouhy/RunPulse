import asyncio
import logging
import threading

from channels.layers import get_channel_layer
from django.db import transaction

from apps.gym_admin.dtos import AlertResponseSerializer
from apps.runs.dtos import RunAlertResponseSerializer

logger = logging.getLogger(__name__)

SEND_TIMEOUT_S = 5

GYM_GROUP = "gym"

DEVICES_EVENT = {"type": "devices"}


def notify_user(user_id, payload):
    _send_many([(f"live.user.{user_id}", payload)])


def notify_users(payloads):
    messages = []
    for user_id, payload in payloads:
        messages.append((f"live.user.{user_id}", payload))
    _send_many(messages)


def notify_gym(payload):
    _send_many([(GYM_GROUP, payload)])


def notify_user_on_commit(user_id, payload):
    transaction.on_commit(lambda: notify_user(user_id, payload))


def notify_gym_on_commit(payload):
    transaction.on_commit(lambda: notify_gym(payload))


def notify_devices_changed():
    notify_gym_on_commit(DEVICES_EVENT)


def notify_run_status(user_id, run_id, status, new_records=0):
    notify_user_on_commit(user_id, {"type": "run", "run_id": run_id, "status": status, "new_records": new_records})


def notify_alert(alert):
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
