from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from datetime import datetime

from app.database import users as db_users

from app.utils.auth import get_jwt_payload, decode_access_token
from app.utils.password import hash_password
from app.utils.locks import get_user_lock

from app.schemas.users import CreateUserSchema, UpdateUserSchema, UserResponseSchema, UserLastSeenSchema

# потом убрать и сделать отдельный файл с бд
from sqlalchemy import select, insert, func
from app.database.db import engine
from app.database.models import Users

routes = web.RouteTableDef()


async def get_current_user(request: web.Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise web.HTTPUnauthorized(text="Missing or invalid token")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)

    user = await db_users.get_user_by_id(int(payload["sub"]))
    if not user:
        raise web.HTTPUnauthorized(text="Invalid user")

    return user


@routes.post("/users")
@docs(tags=["Users"], summary="Создать пользователя", description="Доступно только администраторам.")
@request_schema(CreateUserSchema)
async def create_user(request: web.Request):
    current_user = await get_current_user(request)
    if not await db_users.is_admin(current_user.user_id):
        raise web.HTTPForbidden(text="Only admin can create users")

    data = await request.json()
    birth_date = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
    hashed = hash_password(data["password"])

    lock = get_user_lock(current_user.user_id)
    async with lock:
        user_id = await db_users.insert_user(data, hashed, birth_date)
        if data["is_admin"]:
            await db_users.add_admin(user_id)

    return web.json_response({"message": "User created", "user_id": user_id})


@routes.get("/users", allow_head=False)
@docs(tags=["Users"], summary="Список всех пользователей")
@response_schema(UserResponseSchema(many=True), 200)
async def list_users(request: web.Request):
    await get_current_user(request)

    users = await db_users.get_all_users()
    output = []
    for user in users:
        is_admin = await db_users.is_admin(user.user_id)
        output.append({
            "id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "login": user.email,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            "is_admin": is_admin,
            "is_blocked": False,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        })

    return web.json_response(output)


@routes.get("/users/{user_id}", allow_head=False)
@docs(tags=["Users"], summary="Получить пользователя по ID")
@response_schema(UserResponseSchema, 200)
async def get_user(request: web.Request):
    await get_current_user(request)
    user_id = int(request.match_info["user_id"])

    user = await db_users.get_user_by_id(user_id)
    if not user:
        raise web.HTTPNotFound(text="User not found")

    is_admin = await db_users.is_admin(user.user_id)
    return web.json_response({
        "id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "login": user.email,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "is_admin": is_admin,
        "is_blocked": False,
        "last_seen": user.last_seen.isoformat() if user.last_seen else None,
    })


@routes.put("/users/{user_id}")
@docs(tags=["Users"], summary="Обновить пользователя", description="Только для администраторов.")
@request_schema(UpdateUserSchema)
async def update_user(request: web.Request):
    current_user = await get_current_user(request)
    if not await db_users.is_admin(current_user.user_id):
        raise web.HTTPForbidden(text="Only admin can update users")

    user_id = int(request.match_info["user_id"])
    data = await request.json()

    birth_date = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
    values = {
        "username": data["username"],
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "phone_number": data["phone_number"],
        "email": data["email"],
        "birth_date": birth_date
    }

    if "password" in data and data["password"]:
        values["password_hash"] = hash_password(data["password"])

    lock = get_user_lock(user_id)
    async with lock:
        await db_users.update_user(user_id, values)

        is_admin_now = await db_users.is_admin(user_id)
        if data["is_admin"] and not is_admin_now:
            await db_users.add_admin(user_id)
        elif not data["is_admin"] and is_admin_now:
            await db_users.remove_admin(user_id)

    return web.json_response({"message": "User updated"})


@routes.delete("/users/{user_id}")
@docs(tags=["Users"], summary="Удалить пользователя", description="Удаляет пользователя по ID. Только админ.")
async def delete_user(request: web.Request):
    current_user = await get_current_user(request)
    if not await db_users.is_admin(current_user.user_id):
        raise web.HTTPForbidden(text="Only admin can delete users")

    user_id = int(request.match_info["user_id"])

    lock = get_user_lock(user_id)
    async with lock:
        await db_users.delete_user(user_id)

    return web.json_response({"message": "User deleted"})


@routes.get("/users/{user_id}/last-seen", allow_head=False)
@docs(
    tags=["Users"],
    summary="Получить время последнего входа пользователя",
    description="Возвращает user_id, username и last_seen"
)
@response_schema(UserLastSeenSchema, 200)
async def get_user_last_seen(request: web.Request):
    jwt_payload = get_jwt_payload(request)
    requester_id = int(jwt_payload["sub"])

    user_id = int(request.match_info["user_id"])

    async with engine.connect() as conn:
        result = await conn.execute(
            select(
                Users.c.user_id,
                Users.c.username,
                Users.c.last_seen
            ).where(Users.c.user_id == user_id)
        )
        user = result.fetchone()

    if not user:
        raise web.HTTPNotFound(text="Пользователь не найден")

    return web.json_response({
        "user_id": user.user_id,
        "username": user.username,
        "last_seen": user.last_seen.isoformat() if user.last_seen else None
    })


def setup_user_routes(app: web.Application):
    app.add_routes(routes)
