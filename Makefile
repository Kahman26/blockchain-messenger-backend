.PHONY: update pull build up down restart migrate install_deps check_env

# Полное обновление проекта: код, зависимости, миграции и запуск
update: pull check_env build up migrate

# Загружает последнюю версию из Git
pull:
	git pull origin main

# Проверка наличия .env (если нужно)
check_env:
	@if [ ! -f .env ]; then \
		echo "⚠️  Файл .env не найден. Создаю пустой .env..."; \
		touch .env; \
	fi

# Собирает контейнеры с обновлением базового образа
build:
	docker pull python:3.11
	docker compose build

# Поднимает контейнеры
up:
	docker compose up -d

# Останавливает контейнеры
down:
	docker compose down

# Перезапускает контейнеры с пересборкой
restart:
	docker compose down
	docker compose pull
	docker compose up -d --build

# Применяет миграции alembic
migrate:
	docker compose exec backend alembic upgrade head

# Устанавливает зависимости внутри контейнера (если нужно)
install_deps:
	docker compose exec backend pip install -r requirements.txt
