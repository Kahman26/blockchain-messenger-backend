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


@routes.post("/auth/register")
@docs(tags=["Auth"], summary="Регистрация", description="Создание нового пользователя и отправка кода подтверждения")
@request_schema(RegisterSchema)
async def register(request: web.Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return web.json_response({"error": "Email and password required"}, status=400)

    if await db_auth.get_user_by_email(email):
        return web.json_response({"error": "User already exists"}, status=400)

    hashed = hash_password(password)
    user_id = await db_auth.insert_user(email, hashed)

    code = f"{random.randint(100000, 999999)}"
    now = datetime.utcnow()

    await db_auth.create_verification_code(user_id=user_id, code=code, now=now)

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
    # будет переделано:
    # if user.is_blocked:
    #     return web.json_response({"error": "User is blocked"}, status=403)

    token = create_access_token({
        "sub": str(user.user_id),
        "email": user.email,
    })

    return web.json_response({"access_token": token})


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
