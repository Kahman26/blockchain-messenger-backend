from sqlalchemy import select, insert, update, delete
from app.database.models import Users, Admins, UserKeys
from app.database.db import engine
from datetime import datetime


async def get_user_by_id(user_id: int):
    async with engine.connect() as conn:
        result = await conn.execute(select(Users).where(Users.c.user_id == user_id))
        return result.fetchone()


async def get_all_users():
    async with engine.connect() as conn:
        result = await conn.execute(select(Users))
        return result.fetchall()


async def insert_user(data: dict, hashed_password: str, birth_date: datetime):
    async with engine.begin() as conn:
        result = await conn.execute(insert(Users).values(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=data["phone_number"],
            email=data["email"],
            password_hash=hashed_password,
            birth_date=birth_date,
        ))
        return result.inserted_primary_key[0]

async def update_user(user_id: int, data: dict):
    async with engine.begin() as conn:
        await conn.execute(update(Users).where(Users.c.user_id == user_id).values(**data))


async def delete_user(user_id: int):
    async with engine.begin() as conn:
        await conn.execute(delete(Users).where(Users.c.user_id == user_id))
        await conn.execute(delete(Admins).where(Admins.c.user_id == user_id))


async def is_admin(user_id: int) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(select(Admins).where(Admins.c.user_id == user_id))
        return result.fetchone() is not None


async def add_admin(user_id: int):
    async with engine.begin() as conn:
        await conn.execute(insert(Admins).values(user_id=user_id, assigned_at=datetime.utcnow(), active=True))


async def remove_admin(user_id: int):
    async with engine.begin() as conn:
        await conn.execute(delete(Admins).where(Admins.c.user_id == user_id))


async def get_user_key(user_id: int):
    async with engine.connect() as conn:
        result = await conn.execute(
            select(UserKeys).where(UserKeys.c.user_id == user_id)
        )
        return result.fetchone()
