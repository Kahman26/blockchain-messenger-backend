from aiohttp import web
from sqlalchemy import select, insert, update, delete
from app.models import users
from app.db import engine
from app.utils.auth import decode_access_token
from app.utils.password import hash_password
from datetime import datetime

routes = web.RouteTableDef()


async def get_current_user(request: web.Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise web.HTTPUnauthorized(text="Missing or invalid token")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)

    async with engine.begin() as conn:
        result = await conn.execute(select(users).where(users.c.id == int(payload["sub"])))
        user = result.fetchone()

        if not user:
            raise web.HTTPUnauthorized(text="Invalid user")

        return user


@routes.post("/users")
async def create_user(request: web.Request):
    current_user = await get_current_user(request)
    if not current_user.is_admin:
        raise web.HTTPForbidden(text="Only admin can create users")

    data = await request.json()
    now = datetime.utcnow()

    async with engine.begin() as conn:
        result = await conn.execute(insert(users).values(
            first_name=data["first_name"],
            last_name=data["last_name"],
            login=data["login"],
            password=hash_password(data["password"]),
            birth_date=datetime.fromisoformat(data["birth_date"]),
            is_admin=data["is_admin"],
            is_blocked=False,
            created_at=now,
            updated_at=now
        ))

        user_id = result.inserted_primary_key[0]
        return web.json_response({"message": "User created", "user_id": user_id})


@routes.get("/users")
async def list_users(request: web.Request):
    current_user = await get_current_user(request)

    async with engine.begin() as conn:
        result = await conn.execute(select(users))
        all_users = [dict(row._mapping) for row in result.fetchall()]
        return web.json_response(all_users)


@routes.get("/users/{user_id}")
async def get_user(request: web.Request):
    current_user = await get_current_user(request)
    user_id = int(request.match_info["user_id"])

    async with engine.begin() as conn:
        result = await conn.execute(select(users).where(users.c.id == user_id))
        user = result.fetchone()

        if not user:
            raise web.HTTPNotFound(text="User not found")

        return web.json_response(dict(user._mapping))


@routes.put("/users/{user_id}")
async def update_user(request: web.Request):
    current_user = await get_current_user(request)
    if not current_user.is_admin:
        raise web.HTTPForbidden(text="Only admin can update users")

    user_id = int(request.match_info["user_id"])
    data = await request.json()
    now = datetime.utcnow()

    async with engine.begin() as conn:
        values = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "login": data["login"],
            "birth_date": datetime.fromisoformat(data["birth_date"]),
            "is_admin": data["is_admin"],
            "updated_at": now
        }

        if "password" in data:
            values["password"] = hash_password(data["password"])

        await conn.execute(update(users).where(users.c.id == user_id).values(**values))
        return web.json_response({"message": "User updated"})


@routes.delete("/users/{user_id}")
async def delete_user(request: web.Request):
    current_user = await get_current_user(request)
    if not current_user.is_admin:
        raise web.HTTPForbidden(text="Only admin can delete users")

    user_id = int(request.match_info["user_id"])

    async with engine.begin() as conn:
        await conn.execute(delete(users).where(users.c.id == user_id))
        return web.json_response({"message": "User deleted"})




