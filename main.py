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

# ======================================================
# OAuth Routes (ChatGPT uyumlu)
# ======================================================
register_oauth_routes(app)

# ======================================================
# MCP Auth Settings
# ======================================================
auth_settings = AuthSettings(
    issuer_url=BASE_URL,
    resource_server_url=BASE_URL,
)

# ======================================================
# MCP Server
# ======================================================
mcp = FastMCP(
    name="ecommerce-mcp",
    token_verifier=CustomTokenVerifier(),
    auth=auth_settings,
)

# Tool kayıtları
register_mcp(mcp)

# ======================================================
# Mount SSE transport
# ======================================================
# ChatGPT connector’ın bağlanacağı yer:
#   GET  /mcp/sse
#   POST /mcp/messages
app.mount("/mcp", mcp.sse_app())

# ======================================================
# Debug routes
# ======================================================
APP_VERSION = "2.0.0"

@app.get("/__routes__")
async def debug_routes():
    return {
        "version": APP_VERSION,
        "routes": [route.path for route in app.router.routes]
    }


@app.get("/__debug/tokens")
async def debug_tokens():
    """Access token store'u gösterir."""
    from app.oauth import TOKENS
    return {
        "token_count": len(TOKENS),
        "tokens": [
            {
                "token": token[:16] + "...",
                "client_id": data["client_id"],
                "scope": data["scope"],
                "expires_in": int(data["expires_at"] - time.time())
            }
            for token, data in TOKENS.items()
        ]
    }


@app.get("/__debug/clients")
async def debug_clients():
    """Kayıtlı client'lar."""
    from app.oauth import CLIENTS
    return {
        "client_count": len(CLIENTS),
        "clients": CLIENTS
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
