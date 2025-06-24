from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from sqlalchemy import select, insert, update, delete
from app.database.models import Users, Admins
from app.database.db import engine
from app.utils.auth import decode_access_token
from app.utils.password import hash_password
from datetime import datetime
from app.schemas.users import CreateUserSchema, UpdateUserSchema, UserResponseSchema

routes = web.RouteTableDef()


async def get_current_user(request: web.Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise web.HTTPUnauthorized(text="Missing or invalid token")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)

    async with engine.connect() as conn:
        result = await conn.execute(select(Users).where(Users.c.user_id == int(payload["sub"])))
        user = result.fetchone()

        if not user:
            raise web.HTTPUnauthorized(text="Invalid user")

        return user


async def is_admin(user_id: int) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(select(Admins).where(Admins.c.user_id == user_id))
        return result.fetchone() is not None


@routes.post("/users")
@docs(tags=["Users"], summary="Создать пользователя", description="Доступно только администраторам.")
@request_schema(CreateUserSchema)
async def create_user(request: web.Request):
    current_user = await get_current_user(request)
    if not await is_admin(current_user.user_id):
        raise web.HTTPForbidden(text="Only admin can create users")

    data = await request.json()
    now = datetime.utcnow()
    birth_date = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()

    async with engine.begin() as conn:
        result = await conn.execute(insert(Users).values(
            username=data["login"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=None,
            email=data["login"],
            password_hash=hash_password(data["password"]),
            birth_date=birth_date,
        ))
        user_id = result.inserted_primary_key[0]

        if data["is_admin"]:
            await conn.execute(insert(Admins).values(user_id=user_id, assigned_at=now, active=True))

    return web.json_response({"message": "User created", "user_id": user_id})


@routes.get("/users", allow_head=False)
@docs(tags=["Users"], summary="Список всех пользователей")
@response_schema(UserResponseSchema(many=True), 200)
async def list_users(request: web.Request):
    await get_current_user(request)

    async with engine.connect() as conn:
        result = await conn.execute(select(Users))
        users = result.fetchall()

        output = []
        for user in users:
            is_admin_flag = await conn.execute(select(Admins).where(Admins.c.user_id == user.user_id))
            is_admin = is_admin_flag.fetchone() is not None

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

    async with engine.connect() as conn:
        result = await conn.execute(select(Users).where(Users.c.user_id == user_id))
        user = result.fetchone()

        if not user:
            raise web.HTTPNotFound(text="User not found")

        is_admin_flag = await conn.execute(select(Admins).where(Admins.c.user_id == user.user_id))
        is_admin = is_admin_flag.fetchone() is not None

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
    if not await is_admin(current_user.user_id):
        raise web.HTTPForbidden(text="Only admin can update users")

    user_id = int(request.match_info["user_id"])
    data = await request.json()

    async with engine.begin() as conn:
        values = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "email": data["login"],
            "username": data["login"],
            "birth_date": data["birth_date"]
        }

        if "password" in data and data["password"]:
            values["password_hash"] = hash_password(data["password"])

        await conn.execute(update(Users).where(Users.c.user_id == user_id).values(**values))

        is_admin_flag = await conn.execute(select(Admins).where(Admins.c.user_id == user_id))
        exists = is_admin_flag.fetchone() is not None

        if data["is_admin"] and not exists:
            await conn.execute(insert(Admins).values(user_id=user_id, assigned_at=datetime.utcnow(), active=True))
        elif not data["is_admin"] and exists:
            await conn.execute(delete(Admins).where(Admins.c.user_id == user_id))

    return web.json_response({"message": "User updated"})


@routes.delete("/users/{user_id}")
@docs(tags=["Users"], summary="Удалить пользователя", description="Удаляет пользователя по ID. Только админ.")
async def delete_user(request: web.Request):
    current_user = await get_current_user(request)
    if not await is_admin(current_user.user_id):
        raise web.HTTPForbidden(text="Only admin can delete users")

    user_id = int(request.match_info["user_id"])

    async with engine.begin() as conn:
        await conn.execute(delete(Users).where(Users.c.user_id == user_id))
        await conn.execute(delete(Admins).where(Admins.c.user_id == user_id))

    return web.json_response({"message": "User deleted"})
