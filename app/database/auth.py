from sqlalchemy import select, insert, update
from app.database.models import Email_verifications, Users, UserKeys
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


async def insert_user(username: str, phone_number: str, email: str, password_hash: str) -> int:
    async with engine.begin() as conn:
        result = await conn.execute(
            insert(Users).values(
                username=username,
                first_name=None,
                last_name=None,
                phone_number=phone_number,
                email=email,
                password_hash=password_hash,
                birth_date=datetime(1970, 1, 1),
                is_activated_acc=False,
            )
        )
        return result.inserted_primary_key[0]


async def activate_user_account(user_id: int):
    async with engine.begin() as conn:
        await conn.execute(
            update(Users)
            .where(Users.c.user_id == user_id)
            .values(is_activated_acc=True)
        )


async def save_public_key(user_id: int, public_key: str):
    async with engine.begin() as conn:
        await conn.execute(
            insert(UserKeys).values(
                user_id=user_id,
                public_key=public_key
            )
        )


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


async def user_exists_by_email(email: str) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(select(Users).where(Users.c.email == email))
        return result.scalar_one_or_none() is not None


async def user_exists_by_username(username: str) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(
            select(Users).where(
                Users.c.username == username,
                Users.c.is_activated_acc == True
            )
        )
        return result.scalar_one_or_none() is not None


async def create_user_with_key_and_verification(
    *,
    email: str,
    password_hash: str,
    username: str,
    phone_number: str,
    public_key: str,
    birth_date: datetime,
    verification_code: str,
    now: datetime,
) -> int:
    async with engine.begin() as conn:
        # 1. Создание пользователя
        result = await conn.execute(
            insert(Users).values(
                email=email,
                password_hash=password_hash,
                username=username,
                phone_number=phone_number,
                birth_date=birth_date,
                is_activated_acc=False,
            ).returning(Users.c.user_id)
        )
        user_id = result.scalar()

        # 2. Сохраняем публичный ключ
        await conn.execute(
            insert(UserKeys).values(
                user_id=user_id,
                public_key=public_key,
                created_at=now,
            )
        )

        # 3. Код подтверждения
        await conn.execute(
            insert(Email_verifications).values(
                user_id=user_id,
                verification_code=verification_code,
                created_at=now,
                updated_at=now,
            )
        )

        return user_id

