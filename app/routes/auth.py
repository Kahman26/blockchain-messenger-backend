from aiohttp import web
from sqlalchemy import select, insert, update
from app.models import users, email_verifications
from app.db import engine
from app.utils.email import send_verification_email
from app.utils.auth import create_access_token
from app.utils.password import hash_password, verify_password
import random
from datetime import datetime

from aiohttp_swagger3 import docs, request_schema, response_schema
from pydantic import BaseModel, EmailStr, Field
from app.schemas.auth import *

routes = web.RouteTableDef()

@routes.post('/auth/request-verification')
@docs(
    tags=["Auth"],
    summary="Запросить код подтверждения на email",
    description="Отправляет 6-значный код подтверждения на почту пользователя"
)
@request_schema(EmailSchema)
async def request_verification(request: web.Request):
    data = await request.json()
    email = data.get("email")
    if not email:
        return web.json_response({"error": "Email required"}, status=400)

    code = f"{random.randint(100000, 999999)}"
    now = datetime.utcnow()

    async with engine.begin() as conn:
        result = await conn.execute(select(email_verifications).where(email_verifications.c.email == email))
        existing = result.fetchone()

        if existing:
            await conn.execute(update(email_verifications).where(
                email_verifications.c.email == email
            ).values(
                verification_code=code,
                code_created_at=now,
                updated_at=now
            ))
        else:
            await conn.execute(insert(email_verifications).values(
                email=email,
                verification_code=code,
                code_created_at=now,
                created_at=now,
                updated_at=now,
                user_id=None
            ))

    try:
        send_verification_email(email_to=email, code=code)
    except Exception as e:
        return web.json_response({"error": f"Failed to send email: {str(e)}"}, status=500)

    return web.json_response({"message": "Verification code sent"})


@routes.post("/auth/register")
@docs(
    tags=["Auth"],
    summary="Регистрация пользователя",
    description="Создаёт нового пользователя по email, паролю и коду подтверждения, отправленному на почту"
)
@request_schema(RegisterSchema)
async def register(request: web.Request):
    from sqlalchemy import and_

    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    code = data.get("code")

    if not email or not password or not code:
        return web.json_response({"error": "email, password and code required"}, status=400)

    async with engine.begin() as conn:
        result = await conn.execute(
            select(email_verifications).where(email_verifications.c.email == email)
        )
        verification = result.fetchone()

        if not verification or verification.verification_code != code:
            return web.json_response({"error": "Invalid verification code"}, status=400)

        # Проверим, не истёк ли код (например, 10 мин)
        if verification.code_created_at and (datetime.utcnow() - verification.code_created_at).total_seconds() > 600:
            return web.json_response({"error": "Verification code expired"}, status=400)

        # Проверим, нет ли уже пользователя
        result = await conn.execute(select(users).where(users.c.login == email))
        if result.fetchone():
            return web.json_response({"error": "User already exists"}, status=400)

        # Создаём пользователя
        hashed_password = hash_password(password)
        now = datetime.utcnow()
        user_insert = await conn.execute(insert(users).values(
            first_name="Default",
            last_name="Default",
            login=email,
            password=hashed_password,
            birth_date=datetime(1970, 1, 1),
            is_admin=False,
            is_blocked=False,
            created_at=now,
            updated_at=now
        ))

        user_id = user_insert.inserted_primary_key[0]

        # Обновляем user_id в email_verifications
        await conn.execute(update(email_verifications).where(
            email_verifications.c.email == email
        ).values(user_id=user_id, updated_at=now))

    return web.json_response({"message": "User registered successfully"})


@routes.post("/auth/login")
@docs(
    tags=["Auth"],
    summary="Вход в систему",
    description="Авторизация по email и паролю. Возвращает JWT токен."
)
@request_schema(LoginSchema)
@response_schema(TokenResponse, 200)
async def login(request: web.Request):
    from app.utils.password import verify_password

    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return web.json_response({"error": "Missing email or password"}, status=400)

    async with engine.begin() as conn:
        result = await conn.execute(select(users).where(users.c.login == email))
        user = result.fetchone()

        if not user or not verify_password(password, user.password):
            return web.json_response({"error": "Invalid credentials"}, status=401)

        if user.is_blocked:
            return web.json_response({"error": "User is blocked"}, status=403)

        token = create_access_token({
            "sub": str(user.id),
            "email": user.login,
            "is_admin": user.is_admin
        })

        return web.json_response({"access_token": token})


@routes.post("/auth/reset-password")
@docs(
    tags=["Auth"],
    summary="Сброс пароля",
    description="Позволяет сбросить пароль с помощью кода подтверждения, отправленного на почту"
)
@request_schema(ResetPasswordSchema)
async def reset_password(request: web.Request):
    from app.utils.password import hash_password

    data = await request.json()
    email = data.get("email")
    code = data.get("code")
    new_password = data.get("new_password")

    if not email or not code or not new_password:
        return web.json_response({"error": "email, code, and new_password are required"}, status=400)

    async with engine.begin() as conn:
        # Найдём верификацию
        result = await conn.execute(
            select(email_verifications).where(email_verifications.c.email == email)
        )
        verification = result.fetchone()

        if not verification or verification.verification_code != code:
            return web.json_response({"error": "Invalid verification code"}, status=400)

        # Проверим срок действия
        if verification.code_created_at and (datetime.utcnow() - verification.code_created_at).total_seconds() > 600:
            return web.json_response({"error": "Verification code expired"}, status=400)

        # Найдём пользователя
        result = await conn.execute(select(users).where(users.c.login == email))
        user = result.fetchone()

        if not user:
            return web.json_response({"error": "User not found"}, status=404)

        # Обновим пароль и updated_at
        now = datetime.utcnow()
        hashed = hash_password(new_password)

        await conn.execute(
            update(users).where(users.c.id == user.id).values(
                password=hashed,
                updated_at=now
            )
        )

        # Очистим код верификации
        await conn.execute(
            update(email_verifications)
            .where(email_verifications.c.email == email)
            .values(
                updated_at=now
            )
        )

    return web.json_response({"message": "Password successfully reset"})




