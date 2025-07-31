from aiohttp import web
from app.utils.email import send_verification_email
from app.utils.auth import create_access_token, verify_refresh_token, create_refresh_token
from app.utils.password import hash_password, verify_password
from app.schemas.auth import *
from app.database import auth as db_auth
import random

from aiohttp_apispec import docs, request_schema, response_schema

from app.database.models import RefreshTokens
from sqlalchemy import select, insert, update
from app.database.db import engine
from datetime import datetime, timedelta
from app.config import settings


routes = web.RouteTableDef()


@routes.post("/auth/register")
@docs(tags=["Auth"], summary="Регистрация", description="Создание нового пользователя и отправка кода подтверждения")
@request_schema(RegisterSchema)
async def register(request: web.Request):
    data = await request.json()
    email = data["email"]
    password = data["password"]
    username = data["username"]
    phone_number = data["phone_number"]
    public_key = data["public_key"]

    if not all([email, password, username, phone_number, public_key]):
        return web.json_response({"error": "Missing fields"}, status=400)

    user = await db_auth.get_user_by_email(email)
    now = datetime.utcnow()
    code = f"{random.randint(100000, 999999)}"

    if user:
        if user.is_activated_acc:
            return web.json_response({"error": "Email already registered"}, status=400)
        else:
            # повторная отправка кода
            await db_auth.update_verification_code(email, code, now)
            try:
                send_verification_email(email_to=email, code=code)
            except Exception as e:
                return web.json_response({"error": f"Failed to send email: {str(e)}"}, status=500)

            return web.json_response({"message": "Account not confirmed. Verification code sent again."})

    if await db_auth.user_exists_by_username(username):
        return web.json_response({"error": "Username already taken"}, status=400)

    # регистрация нового пользователя
    hashed = hash_password(password)

    user_id = await db_auth.insert_user(
        username=username,
        phone_number=phone_number,
        email=email,
        password_hash=hashed,
    )

    await db_auth.save_public_key(user_id, public_key)
    await db_auth.create_verification_code(user_id, code, now)

    try:
        send_verification_email(email_to=email, code=code)
    except Exception as e:
        return web.json_response({"error": f"Failed to send email: {str(e)}"}, status=500)

    return web.json_response({"message": "User created. Verification code sent."})


@routes.post("/auth/confirm-email")
@docs(tags=["Auth"], summary="Подтверждение почты", description="Сравнивает код и активирует пользователя")
@request_schema(ConfirmEmailSchema)
async def confirm_email(request: web.Request):
    data = await request.json()
    email = data.get("email")
    code = data.get("code")

    user = await db_auth.get_user_by_email(email)
    if not user:
        return web.json_response({"error": "User not found"}, status=404)

    verification = await db_auth.get_verification_by_user_id(user.user_id)
    if not verification or verification.verification_code != code:
        return web.json_response({"error": "Invalid code"}, status=400)

    if (datetime.utcnow() - verification.updated_at).total_seconds() > 600:
        return web.json_response({"error": "Code expired"}, status=400)

    await db_auth.activate_user_account(user.user_id)

    return web.json_response({"message": "Email confirmed"})


@routes.post("/auth/login")
@docs(tags=["Auth"], summary="Вход", description="Получение JWT токена")
@request_schema(LoginSchema)
@response_schema(TokenResponse, 200)
async def login(request: web.Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    user = await db_auth.get_user_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        return web.json_response({"error": "Invalid credentials"}, status=401)

    if not user.is_activated_acc:
        return web.json_response({"error": "Account not activated"}, status=403)

    # будет переделано:
    # if user.is_blocked:
    #     return web.json_response({"error": "User is blocked"}, status=403)

    access_token = create_access_token({
        "sub": str(user.user_id),
        "email": user.email,
    })
    refresh_token = create_refresh_token({
        "sub": str(user.user_id),
        "email": user.email,
    })

    async with engine.begin() as conn:
        await conn.execute(
            insert(RefreshTokens).values(
                user_id=user.user_id,
                token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_EXP_SECONDS)
            )
        )

    return web.json_response({
        "user_id": user.user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


@routes.post('/auth/request-verification')
@docs(tags=["Auth"], summary="Запросить код перед сбросом пароля", description="Шлёт код на email")
@request_schema(EmailSchema)
async def request_verification(request: web.Request):
    data = await request.json()
    email = data.get("email")

    if not email:
        return web.json_response({"error": "Email required"}, status=400)

    code = f"{random.randint(100000, 999999)}"
    now = datetime.utcnow()

    exists = await db_auth.check_email_exists(email)

    if exists:
        await db_auth.update_verification_code(email, code, now)
    else:
        await db_auth.insert_verification_code(code, now)

    try:
        send_verification_email(email_to=email, code=code)
    except Exception as e:
        return web.json_response({"error": f"Failed to send email: {str(e)}"}, status=500)

    return web.json_response({"message": "Verification code sent"})


@routes.post("/auth/reset-password")
@docs(tags=["Auth"], summary="Сброс пароля", description="По email и коду")
@request_schema(ResetPasswordSchema)
async def reset_password(request: web.Request):
    data = await request.json()
    email = data.get("email")
    code = data.get("code")
    new_password = data.get("new_password")

    verification = await db_auth.get_verification_by_email(email)
    if not verification or verification.verification_code != code:
        return web.json_response({"error": "Invalid verification code"}, status=400)

    if (datetime.utcnow() - verification.updated_at).total_seconds() > 600:
        return web.json_response({"error": "Verification code expired"}, status=400)

    user = await db_auth.get_user_by_email(email)
    if not user:
        return web.json_response({"error": "User not found"}, status=404)

    hashed = hash_password(new_password)
    now = datetime.utcnow()

    await db_auth.update_user_password(email, hashed)
    await db_auth.touch_email_verification(email, now)

    return web.json_response({"message": "Password successfully reset"})


@routes.post("/auth/refresh")
@docs(tags=["Auth"], summary="Обновление токенов")
@request_schema(RefreshTokenSchema)
@response_schema(TokenResponse, 200)
async def refresh_tokens(request: web.Request):
    data = await request.json()
    refresh_token = data["refresh_token"]

    # Проверяем токен в базе
    async with engine.connect() as conn:
        result = await conn.execute(
            select(RefreshTokens)
            .where(RefreshTokens.c.token == refresh_token)
            .where(RefreshTokens.c.is_revoked == False)
            .where(RefreshTokens.c.expires_at > datetime.utcnow())
        )
        token_record = result.fetchone()

    if not token_record:
        raise web.HTTPUnauthorized(text="Invalid refresh token")

    # Проверяем подпись токена
    payload = await verify_refresh_token(refresh_token)
    if not payload:
        raise web.HTTPUnauthorized(text="Invalid refresh token")

    # Создаем новую пару токенов
    new_access_token = create_access_token({"sub": payload["sub"], "email": payload["email"]})
    new_refresh_token = create_refresh_token({"sub": payload["sub"], "email": payload["email"]})

    # Обновляем refresh токен в базе
    async with engine.begin() as conn:
        # Отзываем старый токен
        await conn.execute(
            update(RefreshTokens)
            .where(RefreshTokens.c.token_id == token_record.token_id)
            .values(is_revoked=True)
        )

        # Добавляем новый токен
        await conn.execute(
            insert(RefreshTokens).values(
                user_id=payload["sub"],
                token=new_refresh_token,
                expires_at=datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_EXP_SECONDS)
            )
        )

    return web.json_response({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    })


@routes.post("/auth/logout")
@docs(tags=["Auth"], summary="Выход из системы")
@request_schema(RefreshTokenSchema)
async def logout(request: web.Request):
    data = await request.json()
    refresh_token = data["refresh_token"]

    async with engine.begin() as conn:
        await conn.execute(
            update(RefreshTokens)
            .where(RefreshTokens.c.token == refresh_token)
            .values(is_revoked=True)
        )

    return web.json_response({"message": "Logged out successfully"})
