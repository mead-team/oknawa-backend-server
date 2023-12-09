app-build:
	docker-compose build

app-up:
	docker-compose up -d

app-down:
	docker-compose down

api-up:
	docker start oknawa_api

api-down:
	docker stop oknawa_api

api-restart:
	docker restart oknawa_api

code-beauty:
	black . && isort .

app-log:
	docker-compose logs -f app

app-test:
	docker-compose exec app pytest --cov-report term-missing --cov --ignore temp

db-migrate:
	docker-compose exec app alembic revision --autogenerate -m "${MSG}"

db-upgrade:
	docker-compose exec app alembic upgrade head

pip-list:
	docker-compose exec app pip list
