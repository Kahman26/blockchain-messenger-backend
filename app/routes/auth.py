from aiohttp import web
from app.utils.email import send_verification_email
from app.utils.auth import create_access_token
from app.utils.password import hash_password, verify_password
from app.schemas.auth import *
from app.database import auth as db_auth
from datetime import datetime
import random

from aiohttp_apispec import docs, request_schema, response_schema

routes = web.RouteTableDef()


@routes.post('/auth/request-verification')
@docs(tags=["Auth"], summary="Запросить код", description="Шлёт код на email")
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
        await db_auth.insert_verification_code(email, code, now)

    try:
        send_verification_email(email_to=email, code=code)
    except Exception as e:
        return web.json_response({"error": f"Failed to send email: {str(e)}"}, status=500)

    return web.json_response({"message": "Verification code sent"})



@routes.post("/auth/register")
@docs(tags=["Auth"], summary="Регистрация", description="Создание нового пользователя")
@request_schema(RegisterSchema)
async def register(request: web.Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    code = data.get("code")

    if not all([email, password, code]):
        return web.json_response({"error": "email, password and code required"}, status=400)

    verification = await db_auth.get_verification_by_email(email)
    if not verification or verification.verification_code != code:
        return web.json_response({"error": "Invalid verification code"}, status=400)

    if (datetime.utcnow() - verification.code_created_at).total_seconds() > 600:
        return web.json_response({"error": "Verification code expired"}, status=400)

    if await db_auth.get_user_by_email(email):
        return web.json_response({"error": "User already exists"}, status=400)

    hashed = hash_password(password)
    user_id = await db_auth.insert_user(email, hashed)

    now = datetime.utcnow()
    await db_auth.update_verification_user_id(email, user_id, now)

    return web.json_response({"message": "User registered successfully"})


@routes.post("/auth/login")
@docs(tags=["Auth"], summary="Вход", description="Получение JWT токена")
@request_schema(LoginSchema)
@response_schema(TokenResponse, 200)
async def login(request: web.Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    user = await db_auth.get_user_by_email(email)
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

    if (datetime.utcnow() - verification.code_created_at).total_seconds() > 600:
        return web.json_response({"error": "Verification code expired"}, status=400)

    user = await db_auth.get_user_by_email(email)
    if not user:
        return web.json_response({"error": "User not found"}, status=404)

    hashed = hash_password(new_password)
    now = datetime.utcnow()

    await db_auth.update_user_password(email, hashed, now)
    await db_auth.touch_email_verification(email, now)

    return web.json_response({"message": "Password successfully reset"})
