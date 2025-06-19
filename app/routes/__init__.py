from aiohttp import web
from .auth import routes as auth_routes
# если позже появятся другие модули: from .users import routes as user_routes

def setup_routes(app: web.Application):
    app.add_routes(auth_routes)
    # app.add_routes(user_routes)