from sqlalchemy import select, insert, update
from app.database.models import email_verifications, users
from app.database.db import engine
from datetime import datetime


async def get_verification_by_email(email: str):
    async with engine.connect() as conn:
        result = await conn.execute(
            select(email_verifications).where(email_verifications.c.email == email)
        )
        return result.fetchone()


async def check_email_exists(email: str) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(
            select(email_verifications.c.email).where(email_verifications.c.email == email)
        )
        return result.scalar_one_or_none() is not None


async def update_verification_code(email: str, code: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            select(email_verifications)
            .where(email_verifications.c.email == email)
            .with_for_update()
        )

        await conn.execute(
            update(email_verifications)
            .where(email_verifications.c.email == email)
            .values(
                verification_code=code,
                code_created_at=now,
                updated_at=now
            )
        )


async def insert_verification_code(email: str, code: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            insert(email_verifications).values(
                email=email,
                verification_code=code,
                code_created_at=now,
                created_at=now,
                updated_at=now,
                user_id=None
            )
        )


async def get_user_by_email(email: str):
    async with engine.connect() as conn:
        result = await conn.execute(select(users).where(users.c.login == email))
        return result.fetchone()


async def insert_user(email: str, hashed_password: str) -> int:
    now = datetime.utcnow()
    async with engine.begin() as conn:
        result = await conn.execute(
            insert(users).values(
                first_name="Default",
                last_name="Default",
                login=email,
                password=hashed_password,
                birth_date=datetime(1970, 1, 1),
                is_admin=False,
                is_blocked=False,
                created_at=now,
                updated_at=now
            )
        )
        return result.inserted_primary_key[0]


async def update_verification_user_id(email: str, user_id: int, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            update(email_verifications)
            .where(email_verifications.c.email == email)
            .values(user_id=user_id, updated_at=now)
        )


async def update_user_password(email: str, hashed: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            update(users)
            .where(users.c.login == email)
            .values(password=hashed, updated_at=now)
        )


async def touch_email_verification(email: str, now: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            update(email_verifications)
            .where(email_verifications.c.email == email)
            .values(updated_at=now)
        )

