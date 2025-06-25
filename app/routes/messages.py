from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from app.schemas.messages import SendMessageSchema, SendMessageResponseSchema, InboxMessageSchema
from app.utils.auth import decode_access_token
from app.utils import blockchain
from app.utils.blockchain import (
    verify_signature,
    generate_block_data,
    calculate_hash
)
from app.database import users as db_users
from app.database import blockchain as db_chain
from app.database.db import engine
from app.database.models import BlockchainTransactions, BlockchainPayloads
from sqlalchemy import select


from datetime import datetime
from random import randint

routes = web.RouteTableDef()


async def get_current_user_id(request: web.Request) -> int:
    token = request.headers.get("Authorization", "").split("Bearer ")[-1]
    payload = decode_access_token(token)
    return int(payload["sub"])


@routes.post("/messages/send")
@docs(tags=["Messages"], summary="Отправка зашифрованного сообщения")
@request_schema(SendMessageSchema)
@response_schema(SendMessageResponseSchema, 200)
async def send_message(request: web.Request):
    sender_id = await get_current_user_id(request)
    data = await request.json()

    receiver_id = data["receiver_id"]
    encrypted = data["encrypted_message"]
    signature = data["signature"]
    original = data.get("original_message")

    sender_key = await db_users.get_user_key(sender_id)
    receiver_key = await db_users.get_user_key(receiver_id)
    if not sender_key or not receiver_key:
        raise web.HTTPBadRequest(text="Keys not found")

    if original:
        if not verify_signature(original, signature, sender_key.public_key):
            raise web.HTTPBadRequest(text="Invalid signature")

    # блокчейн: найти последний блок и создать новый
    last_block = await db_chain.get_last_block()
    prev_hash = last_block.block_hash if last_block else "0" * 64
    nonce = randint(100000, 999999)

    block_data = generate_block_data(prev_hash, [encrypted], nonce)
    block_hash = calculate_hash(block_data)
    block_id, _ = await db_chain.create_block(prev_hash, nonce, creator_user_id=sender_id)

    # транзакция
    tx_id = await db_chain.add_transaction(
        block_id=block_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        payload_hash=calculate_hash({"data": encrypted}),
        signature=signature,
    )

    # зашифрованное тело
    await db_chain.store_encrypted_payload(tx_id, encrypted)

    return web.json_response({
        "message": "Encrypted message recorded on blockchain",
        "transaction_id": tx_id
    })

@routes.get("/messages/inbox", allow_head=False)
@docs(
    tags=["Messages"],
    summary="Просмотр входящих сообщений",
    description="Получить расшифрованные сообщения, отправленные текущему пользователю"
)
@response_schema(InboxMessageSchema(many=True), 200)
async def inbox(request: web.Request):
    receiver_id = await get_current_user_id(request)

    # Для теста: приватный ключ можно передать в заголовке
    priv_key = request.headers.get("X-Private-Key")
    if not priv_key:
        raise web.HTTPBadRequest(text="Provide X-Private-Key in headers")

    # Найти все входящие транзакции
    async with engine.connect() as conn:
        tx_result = await conn.execute(
            BlockchainTransactions.select().where(
                BlockchainTransactions.c.receiver_id == receiver_id
            )
        )
        transactions = tx_result.fetchall()

        messages = []

        for tx in transactions:
            payload_result = await conn.execute(
                BlockchainPayloads.select().where(
                    BlockchainPayloads.c.transaction_id == tx.transaction_id
                )
            )
            payload = payload_result.fetchone()
            if not payload:
                continue

            encrypted_data = payload.encrypted_data
            try:
                decrypted = blockchain.decrypt_message(encrypted_data, priv_key)
            except Exception:
                decrypted = "[Ошибка расшифровки]"

            messages.append({
                "from_user_id": tx.sender_id,
                "message": decrypted,
                "timestamp": tx.timestamp.isoformat()
            })

    return web.json_response(messages)
