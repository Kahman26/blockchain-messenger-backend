from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

DATABASE_URL = settings.DB_URL

engine = create_async_engine(DATABASE_URL, echo=True)