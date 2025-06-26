from aiohttp import web
from aiohttp_apispec import setup_aiohttp_apispec

from app.routes.auth import routes as auth_routes
from app.routes.users import routes as user_routes
from app.routes.messages import routes as message_routes
from app.routes.chats import setup_chat_routes

from app.config import settings
from app.database.db import engine
import logging

logger = logging.getLogger(__name__)

async def on_startup(app: web.Application):
    logger.info("Starting up...")

async def on_cleanup(app: web.Application):
    logger.info("Cleaning up...")

def create_app() -> web.Application:
    logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app['db'] = engine

    app.add_routes(auth_routes)
    app.add_routes(user_routes)
    app.add_routes(message_routes)
    setup_chat_routes(app)

    setup_aiohttp_apispec(
        app=app,
        title="User API",
        version="1.0.0",
        url="/docs/swagger.json",
        swagger_path="/docs",
        securityDefinitions={
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT токен. Пример: **Bearer eyJ0eXAi...**"
            },
            "PrivateKey": {
                "type": "apiKey",
                "name": "X-Private-Key",
                "in": "header",
                "description": "PEM-ключ в виде строки (начинается с -----BEGIN PRIVATE KEY-----)"
            }
        },
        security=[
            {"Bearer": []},
            {"PrivateKey": []}
        ]
    )

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, port=settings.PORT)
