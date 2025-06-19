from aiohttp import web
from aiohttp_swagger3 import SwaggerDocs, SwaggerUiSettings

from app.routes import setup_routes
from app.routes.auth import routes as auth_routes
from app.routes.users import routes as user_routes
from app.config import settings
from app.db import engine
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

    swagger = SwaggerDocs(
        app,
        swagger_ui_settings=SwaggerUiSettings(path="/docs"),
        title="User API",
        version="1.0.0"
    )

    swagger.add_routes(auth_routes)
    swagger.add_routes(user_routes)

    setup_routes(app)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, port=settings.PORT)