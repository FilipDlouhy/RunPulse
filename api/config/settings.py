import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True
SECRET_KEY = "dev-insecure-key-only-for-local-development"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.user",
    "apps.gym_admin",
    "apps.runners",
    "apps.runs",
    "apps.pipelines",
    "apps.realtime",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "postgres://runpulse:runpulse@localhost:5432/runpulse")
    )
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Prague"
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "user.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.user.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "COERCE_DECIMAL_TO_STRING": False,
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "auth": "20/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

AUTH_COOKIE_ACCESS = "access_token"
AUTH_COOKIE_REFRESH = "refresh_token"
AUTH_COOKIE_SECURE = False
AUTH_COOKIE_SAMESITE = "Lax"

GYM_NAME = os.environ.get("GYM_NAME", "FitPoint Zlín")

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://runpulse:runpulse@localhost:5672/%2F")
TELEMETRY_EXCHANGE = "telemetry"
TELEMETRY_QUEUE = "telemetry"
DEVICE_STATUS_QUEUE = "device_status"
RABBITMQ_MANAGEMENT_URL = os.environ.get("RABBITMQ_MANAGEMENT_URL", "http://localhost:15672/api")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [{"address": REDIS_URL, "socket_timeout": 20}]},
    },
}

CELERY_BROKER_URL = RABBITMQ_URL
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

PIPELINE_RETRY_DELAYS = [2, 10]
STUCK_TASK_MINUTES = 5

STALE_RUN_MINUTES = 5
HR_ALARM_PCT = 95
HR_ALARM_SECONDS = 60
NO_DATA_SECONDS = 10
SERVICE_INTERVAL_HOURS = 500
DEVICE_OFFLINE_SECONDS = 90

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "apps": {"handlers": ["console"], "level": "INFO"},
        "pika": {"level": "WARNING"},
    },
}
