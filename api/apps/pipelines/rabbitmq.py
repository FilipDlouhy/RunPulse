from urllib.parse import quote

import httpx
import pika
from django.conf import settings

TIMEOUT_S = 2


def fetch_queue_stats():
    params = pika.URLParameters(settings.RABBITMQ_URL)
    url = f"{settings.RABBITMQ_MANAGEMENT_URL}/queues/{quote(params.virtual_host, safe='')}/{settings.TELEMETRY_QUEUE}"
    response = httpx.get(
        url,
        auth=(params.credentials.username, params.credentials.password),
        timeout=TIMEOUT_S,
    )
    response.raise_for_status()
    data = response.json()
    stats = data.get("message_stats", {})
    return {
        "messages": data.get("messages", 0),
        "ready": data.get("messages_ready", 0),
        "unacked": data.get("messages_unacknowledged", 0),
        "consumers": data.get("consumers", 0),
        "publish_rate": stats.get("publish_details", {}).get("rate", 0.0),
        "deliver_rate": stats.get("deliver_get_details", {}).get("rate", 0.0),
    }
