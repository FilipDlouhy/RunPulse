.PHONY: up infra down ps logs psql migrate seed seed-load web consume worker ui gym run backfill load lint

up:
	docker compose up -d --build

infra:
	docker compose up -d db rabbitmq redis

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

psql:
	docker compose exec db psql -U runpulse runpulse

migrate:
	cd api && uv run python manage.py migrate

seed:
	cd api && uv run python manage.py seed_demo

seed-load:
	cd api && uv run python manage.py seed_load

web:
	cd api && uv run python manage.py runserver 8000

consume:
	cd api && uv run python manage.py consume

worker:
	cd api && uv run celery -A config worker -P threads -c 4 -l info

ui:
	cd ui && npm start

gym:
	cd simulator && uv run python simulator.py gym --speedup 60

run:
	cd simulator && uv run python simulator.py run --user runner --type intervals

backfill:
	cd simulator && uv run python simulator.py backfill --weeks 8

load:
	cd simulator && uv run python simulator.py load --devices 500 --rate 10 --duration 60

lint:
	cd api && uv run ruff check . && uv run mypy apps common config
	cd simulator && uv run ruff check .
