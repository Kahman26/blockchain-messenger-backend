from sqlalchemy import select, insert, update
from app.database.models import Email_verifications, Users
from app.database.db import engine
from datetime import datetime


async def get_verification_by_email(email: str):
    async with engine.connect() as conn:
        result = await conn.execute(
            select(Email_verifications).join(Users).where(Users.c.email == email)
        )
        return result.fetchone()


async def check_email_exists(email: str) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(
            select(Users).where(Users.c.email == email)
        )
        return result.scalar_one_or_none() is not None


async def create_verification_code(user_id: int, code: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            insert(Email_verifications).values(
                user_id=user_id,
                verification_code=code,
                created_at=now,
                updated_at=now,
            )
        )

async def get_verification_by_user_id(user_id: int):
    async with engine.connect() as conn:
        result = await conn.execute(
            select(Email_verifications).where(Email_verifications.c.user_id == user_id)
        )
        return result.fetchone()


async def update_verification_code(email: str, code: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            select(Email_verifications)
            .where(Users.c.email == email)
            .with_for_update()
        )

        await conn.execute(
            update(Email_verifications)
            .where(Email_verifications.c.user_id == Users.c.user_id)
            .where(Users.c.email == email)
            .values(
                verification_code=code,
                updated_at=now
            )
        )


async def insert_verification_code(code: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            insert(Email_verifications).values(
                verification_code=code,
                created_at=now,
                updated_at=now,
                user_id=None
            )
        )


async def get_user_by_email(email: str):
    async with engine.connect() as conn:
        result = await conn.execute(select(Users).where(Users.c.email == email))
        return result.fetchone()


async def insert_user(email: str, hashed_password: str) -> int:
    async with engine.begin() as conn:
        result = await conn.execute(
            insert(Users).values(
                username="NoneUsername",
                first_name=None,
                last_name=None,
                phone_number=None,
                email=email,
                password_hash=hashed_password,
                birth_date=datetime(1970, 1, 1)
            )
        )
        return result.inserted_primary_key[0]


async def update_verification_user_id(email: str, user_id: int, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            update(Email_verifications)
            .where(Email_verifications.c.user_id == user_id)
            .values(updated_at=now)
        )


async def update_user_password(email: str, hashed: str):
    async with engine.begin() as conn:
        await conn.execute(
            update(Users)
            .where(Users.c.email == email)
            .values(password_hash=hashed)
        )


async def touch_email_verification(email: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            update(Email_verifications)
            .where(Email_verifications.c.user_id == Users.c.user_id)
            .where(Users.c.email == email)
            .values(updated_at=now)
        )

