from sqlalchemy import select, insert
from app.database.db import engine
from app.database.models import BlockchainBlocks, BlockchainTransactions, BlockchainPayloads
from datetime import datetime
from app.utils.blockchain import calculate_hash

async def get_last_block():
    async with engine.connect() as conn:
        result = await conn.execute(
            select(BlockchainBlocks).order_by(BlockchainBlocks.c.block_id.desc()).limit(1)
        )
        return result.fetchone()

async def create_block(prev_hash: str, nonce: int, creator_user_id: int):
    block_data = {
        "previous_hash": prev_hash,
        "timestamp": datetime.utcnow(),
        "nonce": nonce,
        "creator_user_id": creator_user_id,
    }
    block_hash = calculate_hash(block_data)
    block_data["block_hash"] = block_hash

    async with engine.begin() as conn:
        result = await conn.execute(
            insert(BlockchainBlocks).values(**block_data)
        )
        block_id = result.inserted_primary_key[0]
    return block_id, block_hash

async def add_transaction(block_id: int, sender_id: int, receiver_id: int, payload_hash: str, signature: str):
    async with engine.begin() as conn:
        result = await conn.execute(
            insert(BlockchainTransactions).values(
                block_id=block_id,
                sender_id=sender_id,
                receiver_id=receiver_id,
                payload_hash=payload_hash,
                signature=signature,
                timestamp=datetime.utcnow(),
            )
        )
        return result.inserted_primary_key[0]

async def store_encrypted_payload(transaction_id: int, encrypted_data: str):
    async with engine.begin() as conn:
        await conn.execute(
            insert(BlockchainPayloads).values(
                transaction_id=transaction_id,
                encrypted_data=encrypted_data,
            )
        )
