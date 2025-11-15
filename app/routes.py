from app.oauth import register_routes as register_oauth_routes

def register_api_routes(app):
    register_oauth_routes(app)
