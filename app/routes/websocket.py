from aiohttp import web, WSMsgType
from app.database.db import engine
from app.utils.auth import get_user_from_token
import json

connected_clients = {}


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    token = request.query.get("token")
    user = await get_user_from_token(token)
    if not user:
        await ws.send_json({"error": "unauthorized"})
        await ws.close()
        return ws

    user_id = user.user_id
    connected_clients[user_id] = ws
    print(f"🟢 WebSocket подключён: user_id={user_id}")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                # Пример логики — отправка сообщения пользователю
                to_user_id = data.get("to_user_id")
                payload = data.get("payload")

                if to_user_id in connected_clients:
                    await connected_clients[to_user_id].send_json({
                        "from_user_id": user_id,
                        "payload": payload
                    })

            elif msg.type == WSMsgType.ERROR:
                print(f"❌ WebSocket ошибка: {ws.exception()}")
    finally:
        print(f"🔴 WebSocket отключён: user_id={user_id}")
        del connected_clients[user_id]

    return ws


def setup_websocket_routes(app: web.Application):
    app.router.add_get('/ws', websocket_handler)