from aiohttp import web
import aiohttp_cors
from aiohttp_apispec import setup_aiohttp_apispec

from app.routes.auth import routes as auth_routes
from app.routes.users import setup_user_routes
from app.routes.chats import setup_chat_routes
from app.routes.websocket import setup_websocket_routes

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

    for route in auth_routes:
        app.router.add_route(route.method, route.path, route.handler)

    setup_user_routes(app)

    setup_chat_routes(app)

    setup_websocket_routes(app)

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

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=settings.PORT)