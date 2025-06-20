from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

DATABASE_URL = settings.DB_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=True,            # Логгирование SQL-запросов
    pool_size=10,         # Основной пул: 10 соединений
    max_overflow=20,      # Временные соединения, если пул заполнен
    pool_timeout=30,      # Ожидание свободного соединения (сек)
    pool_recycle=1800,    # Перезапуск соединения каждые 30 минут
    pool_pre_ping=True    # Проверка соединения перед выдачей из пула
)
