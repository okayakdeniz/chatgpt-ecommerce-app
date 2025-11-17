from fastapi import FastAPI
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings
import logging
import time

from app.mcp_handlers import register_mcp
from app.oauth import register_oauth_routes, CustomTokenVerifier
from app.config import BASE_URL

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# ======================================================
# OAuth Routes
# ======================================================
register_oauth_routes(app)

# ======================================================
# OAuth Settings for MCP
# ======================================================
auth_settings = AuthSettings(
    issuer_url=BASE_URL,
    resource_server_url=BASE_URL
)

# ======================================================
# MCP Server with OAuth
# ======================================================
mcp = FastMCP(
    name="ecommerce-mcp",
    token_verifier=CustomTokenVerifier(),
    auth=auth_settings
)

# Tool'ları kaydet
register_mcp(mcp)

# ======================================================
# MCP SSE Mount
# ======================================================
app.mount("/mcp", mcp.sse_app())

# ======================================================
# Debug endpoints
# ======================================================
@app.get("/__routes__")
async def debug_routes():
    return [route.path for route in app.router.routes]

@app.get("/__debug/tokens")
async def debug_tokens():
    """Debug: Token store'u göster"""
    from app.oauth import TOKENS
    return {
        "token_count": len(TOKENS),
        "tokens": [
            {
                "token": token[:20] + "...",
                "client_id": data["client_id"],
                "expires_in": int(data["expires_at"] - time.time())
            }
            for token, data in TOKENS.items()
        ]
    }

@app.get("/__debug/clients")
async def debug_clients():
    """Debug: Kayıtlı client'ları göster"""
    from app.oauth import CLIENTS
    return {
        "client_count": len(CLIENTS),
        "clients": list(CLIENTS.keys())
    }

if __name__ == "__main__":
    import uvicorn, os

    logger.info(f"Starting MCP server at {BASE_URL}")
    logger.info(f"OAuth metadata: {BASE_URL}/.well-known/oauth-authorization-server")
    logger.info(f"MCP SSE endpoint: {BASE_URL}/mcp/sse")

    #ssl_certfile = "./wsoakdeniz.tailc4b778.ts.net.crt"
    #ssl_keyfile = "./wsoakdeniz.tailc4b778.ts.net.key"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
        #ssl_certfile=ssl_certfile,
        #ssl_keyfile=ssl_keyfile
    )
