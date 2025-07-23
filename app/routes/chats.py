from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from sqlalchemy import select, insert, func
from app.database.db import engine
from app.database.models import (
    Users,
    Chats,
    ChatMembers,
    ChatUserRoles,
    BlockchainTransactions,
    BlockchainPayloads,
    UserKeys,
)
from app.utils.auth import get_jwt_payload, decode_access_token

from app.schemas.chats import (
    ChatCreateSchema,
    ChatResponseSchema,
    ChatListSchema,
    ChatAddMemberSchema,
    ChatMembersResponseSchema
)
from app.schemas.messages import (
    SendMessageSchema,
    SendMessageResponseSchema,
    InboxMessageSchema,
    EncryptedPerUserSchema,
    EncryptedBroadcastListSchema,
    ChatMessageSchema,
    ChatMessageListSchema
)

from app.utils.blockchain import (
    verify_signature,
    generate_block_data,
    calculate_hash,
    encrypt_message,
    decrypt_message
)
from app.database import users as db_users
from app.database import blockchain as db_chain

from random import randint


async def get_current_user_id(request: web.Request) -> int:
    token = request.headers.get("Authorization", "").split("Bearer ")[-1]
    payload = decode_access_token(token)
    return int(payload["sub"])


@docs(tags=["chats"], summary="Создать чат (group, private, channel)")
@request_schema(ChatCreateSchema)
@response_schema(ChatResponseSchema, 201)
async def create_chat(request: web.Request):
    data = await request.json()
    jwt_payload = get_jwt_payload(request)
    user_id = int(jwt_payload["sub"])

    async with engine.begin() as conn:
        # Создаём чат
        result = await conn.execute(
            insert(Chats).values(
                chat_name=data["chat_name"],
                chat_type=data["chat_type"],
                creator_user_id=user_id,
                description=data.get("description")
            ).returning(Chats.c.chat_id)
        )
        chat_id = result.scalar()

        # Добавляем создателя в участники
        await conn.execute(
            insert(ChatMembers).values(
                chat_id=chat_id,
                user_id=user_id
            )
        )

        # Присваиваем роль "admin" (id = 1)
        await conn.execute(
            insert(ChatUserRoles).values(
                chat_id=chat_id,
                user_id=user_id,
                role_id=1
            )
        )

    return web.json_response({"chat_id": chat_id}, status=201)


@docs(tags=["chats"], summary="Получить список чатов текущего пользователя с датой последнего сообщения")
@response_schema(ChatListSchema, 200)
async def get_user_chats(request: web.Request):
    jwt_payload = get_jwt_payload(request)
    user_id = int(jwt_payload["sub"])

    async with engine.connect() as conn:
        result = await conn.execute(
            select(
                Chats,
                func.max(BlockchainTransactions.c.timestamp).label("last_message_time")
            )
            .select_from(
                Chats
                .join(ChatMembers, Chats.c.chat_id == ChatMembers.c.chat_id)
                .outerjoin(BlockchainTransactions, Chats.c.chat_id == BlockchainTransactions.c.chat_id)
            )
            .where(ChatMembers.c.user_id == user_id)
            .group_by(Chats.c.chat_id)
            .order_by(func.max(BlockchainTransactions.c.timestamp).desc())
        )

        chats = []
        for row in result.fetchall():
            chat_data = {col.name: row._mapping[col.name] for col in Chats.c}
            chat_data["last_message_time"] = row._mapping["last_message_time"]
            chats.append(chat_data)

    schema = ChatListSchema()
    return web.json_response(schema.dump({"chats": chats}))


@docs(tags=["chats"], summary="Получить информацию о конкретном чате")
@response_schema(ChatResponseSchema, 200)
async def get_chat_info(request: web.Request):
    jwt_payload = get_jwt_payload(request)
    user_id = int(jwt_payload["sub"])
    chat_id = int(request.match_info["chat_id"])

    async with engine.connect() as conn:
        result = await conn.execute(
            select(Chats)
            .join(ChatMembers, Chats.c.chat_id == ChatMembers.c.chat_id)
            .where(ChatMembers.c.user_id == user_id,
                   Chats.c.chat_id == chat_id)
        )
        chat = result.fetchone()

    if not chat:
        raise web.HTTPForbidden(reason="Чат не найден или доступ запрещён")

    schema = ChatResponseSchema()
    return web.json_response(schema.dump(dict(chat._mapping)))


@docs(tags=["chats"], summary="Добавить участника в чат (group, channel, или второй участник private-чата)")
@request_schema(ChatAddMemberSchema)
async def add_chat_member(request: web.Request):
    jwt_payload = get_jwt_payload(request)
    requester_id = int(jwt_payload["sub"])
    chat_id = int(request.match_info["chat_id"])
    data = await request.json()
    new_user_id = data["user_id"]

    async with engine.begin() as conn:
        # Получаем тип чата
        result = await conn.execute(
            select(Chats.c.chat_type).where(Chats.c.chat_id == chat_id)
        )
        chat = result.fetchone()
        if not chat:
            raise web.HTTPNotFound(reason="Чат не найден")

        result = await conn.execute(
            select(ChatMembers).where(
                (ChatMembers.c.chat_id == chat_id) &
                (ChatMembers.c.user_id == requester_id)
            )
        )
        if not result.first():
            raise web.HTTPForbidden(reason="Вы не участник этого чата")

        result = await conn.execute(
            select(ChatMembers.c.user_id).where(ChatMembers.c.chat_id == chat_id)
        )
        existing_members = {row.user_id for row in result.fetchall()}

        if new_user_id in existing_members:
            raise web.HTTPConflict(reason="Пользователь уже в чате")

        if chat.chat_type == "private":
            if len(existing_members) >= 2:
                raise web.HTTPBadRequest(reason="В личном чате не может быть больше двух участников")

        # Добавляем нового участника
        await conn.execute(
            insert(ChatMembers).values(
                chat_id=chat_id,
                user_id=new_user_id
            )
        )

    return web.json_response({"message": "Пользователь добавлен"})


@docs(
    tags=["chats"],
    summary="Получить список участников чата",
    description="Возвращает список участников с их username, public_key и last_seen"
)
@response_schema(ChatMembersResponseSchema, 200)
async def get_chat_members(request: web.Request):
    # Получаем user_id текущего пользователя
    jwt_payload = get_jwt_payload(request)
    current_user_id = int(jwt_payload["sub"])

    chat_id = int(request.match_info["chat_id"])

    async with engine.connect() as conn:
        # Проверка: является ли пользователь участником чата
        result = await conn.execute(
            select(ChatMembers).where(
                (ChatMembers.c.chat_id == chat_id) &
                (ChatMembers.c.user_id == current_user_id)
            )
        )
        if not result.fetchone():
            raise web.HTTPForbidden(text="Вы не участник этого чата")

        # Получение участников чата
        result = await conn.execute(
            select(
                Users.c.user_id,
                Users.c.username,
                Users.c.last_seen,
                UserKeys.c.public_key
            )
            .select_from(ChatMembers
                .join(Users, ChatMembers.c.user_id == Users.c.user_id)
                .join(UserKeys, UserKeys.c.user_id == Users.c.user_id)
            )
            .where(ChatMembers.c.chat_id == chat_id)
        )

        members = []
        for row in result.fetchall():
            members.append({
                "id": row.user_id,
                "username": row.username,
                "public_key": row.public_key,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None
            })

    return web.json_response({"members": members})


@docs(tags=["chats"], summary="Удалить участника из чата (только для админов)")
async def remove_chat_member(request: web.Request):
    jwt_payload = get_jwt_payload(request)
    admin_id = int(jwt_payload["sub"])
    chat_id = int(request.match_info["chat_id"])
    target_user_id = int(request.match_info["user_id"])

    async with engine.begin() as conn:
        # Проверка: admin_id является админом чата
        result = await conn.execute(
            select(ChatUserRoles)
            .where(
                (ChatUserRoles.c.chat_id == chat_id) &
                (ChatUserRoles.c.user_id == admin_id)
            )
        )
        role = result.first()
        if not role:
            raise web.HTTPForbidden(reason="Вы не админ этого чата")

        # Удаление участника
        await conn.execute(
            ChatMembers.delete().where(
                (ChatMembers.c.chat_id == chat_id) &
                (ChatMembers.c.user_id == target_user_id)
            )
        )

    return web.json_response({"message": "Пользователь удалён"})



@docs(
    tags=["Messages"],
    summary="Отправка индивидуально зашифрованных сообщений участникам чата (включая себя)",
    description="Каждому участнику (включая себя) отправляется своя копия зашифрованного сообщения"
)
@request_schema(EncryptedBroadcastListSchema)
async def send_chat_message(request: web.Request):
    sender_id = await get_current_user_id(request)
    chat_id = int(request.match_info["chat_id"])
    messages = await request.json()

    if not isinstance(messages, list) or not messages:
        raise web.HTTPBadRequest(text="Ожидается массив сообщений")

    async with engine.connect() as conn:
        result = await conn.execute(
            select(ChatMembers.c.user_id)
            .where(ChatMembers.c.chat_id == chat_id)
        )
        valid_receivers = {row.user_id for row in result.fetchall()}

    last_block = await db_chain.get_last_block()
    prev_hash = last_block.block_hash if last_block else "0" * 64
    nonce = randint(100000, 999999)
    block_id, _ = await db_chain.create_block(prev_hash, nonce, creator_user_id=sender_id)

    tx_ids = []

    for msg in messages:
        receiver_id = msg["receiver_id"]
        encrypted = msg["encrypted_message"]
        signature = msg["signature"]

        if receiver_id not in valid_receivers:
            continue

        tx_id = await db_chain.add_transaction(
            block_id=block_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            chat_id=chat_id,
            payload_hash=calculate_hash({"data": encrypted}),
            signature=signature
        )
        await db_chain.store_encrypted_payload(tx_id, encrypted)
        tx_ids.append(tx_id)

    return web.json_response({
        "message": f"Успешно отправлено {len(tx_ids)} сообщений",
        "transaction_ids": tx_ids
    })


@docs(
    tags=["Messages"],
    summary="Получить все сообщения чата (зашифрованные)",
    description="По одному сообщению из каждого блока, включает username, подпись и зашифрованный текст"
)
@response_schema(ChatMessageListSchema, 200)
async def get_chat_messages(request: web.Request):
    user_id = await get_current_user_id(request)
    chat_id = int(request.match_info["chat_id"])

    async with engine.connect() as conn:
        # Проверка участия в чате
        result = await conn.execute(
            select(ChatMembers).where(
                (ChatMembers.c.chat_id == chat_id) &
                (ChatMembers.c.user_id == user_id)
            )
        )
        if not result.fetchone():
            raise web.HTTPForbidden(text="Вы не состоите в этом чате")

        # Транзакции по чату, где пользователь участник
        tx_result = await conn.execute(
            select(
                BlockchainTransactions.c.transaction_id,
                BlockchainTransactions.c.sender_id,
                BlockchainTransactions.c.signature,
                BlockchainTransactions.c.timestamp,
                BlockchainPayloads.c.encrypted_data,
                Users.c.username
            )
            .select_from(
                BlockchainTransactions
                .join(BlockchainPayloads, BlockchainTransactions.c.transaction_id == BlockchainPayloads.c.transaction_id)
                .join(Users, BlockchainTransactions.c.sender_id == Users.c.user_id)
            )
            .where(
                (BlockchainTransactions.c.chat_id == chat_id) &
                (
                    (BlockchainTransactions.c.receiver_id == user_id) |
                    (BlockchainTransactions.c.sender_id == user_id)
                )
            )
            .order_by(BlockchainTransactions.c.timestamp.asc())
        )

        tx_list = tx_result.fetchall()

        # Группировка по block_id
        all_tx_result = await conn.execute(
            select(
                BlockchainTransactions.c.transaction_id,
                BlockchainTransactions.c.block_id,
                BlockchainTransactions.c.sender_id,
                BlockchainTransactions.c.receiver_id
            ).where(BlockchainTransactions.c.chat_id == chat_id)
        )
        all_tx_by_block = {}
        for tx in all_tx_result.fetchall():
            all_tx_by_block.setdefault(tx.block_id, []).append(tx)

        # Уникальные сообщения: по одной транзакции с приоритетом входящей
        selected_tx_ids = set()
        for block_id, group in all_tx_by_block.items():
            preferred = next((tx for tx in group if tx.receiver_id == user_id), group[0])
            selected_tx_ids.add(preferred.transaction_id)

        # Формирование ответа
        messages = []
        for row in tx_list:
            if row.transaction_id not in selected_tx_ids:
                continue
            messages.append({
                "message_id": row.transaction_id,
                "from_user_id": row.sender_id,
                "from_username": row.username,
                "encrypted_data": row.encrypted_data,
                "signature": row.signature,
                "timestamp": row.timestamp.isoformat()
            })

    return web.json_response({"messages": messages})





def setup_chat_routes(app: web.Application):
    app.router.add_post("/chats/", create_chat)
    app.router.add_get("/chats/", get_user_chats, allow_head=False)
    app.router.add_get("/chats/{chat_id}", get_chat_info, allow_head=False)
    app.router.add_post("/chats/{chat_id}/members", add_chat_member)
    app.router.add_get("/chats/{chat_id}/members", get_chat_members, allow_head=False)
    app.router.add_delete("/chats/{chat_id}/members/{user_id}", remove_chat_member)
    app.router.add_post("/chats/{chat_id}/send", send_chat_message)
    app.router.add_get("/chats/{chat_id}/messages", get_chat_messages, allow_head=False)


