app-build:
	docker compose build

app-stop:
	docker compose down

app-start:
	docker compose up -d

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
