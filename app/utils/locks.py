from collections import defaultdict
import asyncio

_locks = defaultdict(asyncio.Lock)

def get_user_lock(user_id: int) -> asyncio.Lock:
    return _locks[user_id]
