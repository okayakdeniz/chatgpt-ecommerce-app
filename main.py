# main.py
from fastapi import FastAPI
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings

import logging
import time

from app.mcp_handlers import register_mcp
from app.oauth import register_oauth_routes, CustomTokenVerifier
from app.config import BASE_URL

# ======================================================
# Logging
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ======================================================
# FastAPI root app
# ======================================================
app = FastAPI(title="Ecommerce MCP Server")

register_oauth_routes(app)

mcp = FastMCP(name="ecommerce-mcp")

# Tool kayıtları
register_mcp(mcp)
sse_app = mcp.create_sse_app()


app.mount("/mcp", sse_app)

# ======================================================
# Debug routes
# ======================================================
APP_VERSION = "3.0.0"

@app.get("/__routes__")
async def debug_routes():
    return {
        "version": APP_VERSION,
        "routes": [route.path for route in app.router.routes]
    }

# ======================================================
# Uvicorn
# ======================================================
if __name__ == "__main__":
    import uvicorn, os

    logger.info(f"Starting MCP server at {BASE_URL}")
    logger.info(f"OAuth server metadata: {BASE_URL}/.well-known/oauth-authorization-server")
    logger.info(f"MCP SSE endpoint:       {BASE_URL}/mcp/sse")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
