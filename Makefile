app-build:
	docker compose build

app-up:
	docker compose up -d

app-down:
	docker compose down

code-beauty:
	black . && isort .

app-log:
	docker-compose logs -f app

app-test:
	docker-compose exec app "pytest"

db-migrate:
	docker-compose exec app alembic revision --autogenerate -m "${MSG}"

db-upgrade:
	docker-compose exec app alembic upgrade head

pip-list:
	docker-compose exec app sh -c "pip list"
