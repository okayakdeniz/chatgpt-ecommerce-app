# main.py
import os

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.oauth import register_oauth_routes
from app.routes import register_api_routes
from app.mcp_handlers import register_mcp

# ---------------------------------------------------------
# 1) FastAPI ROOT APP
# ---------------------------------------------------------
app = FastAPI(title="Ecommerce MCP Server")

# ---------------------------------------------------------
# 2) OAuth / OIDC / resource metadata endpointleri
# ---------------------------------------------------------
register_oauth_routes(app)

# ---------------------------------------------------------
# 3) Normal REST API (opsiyonel)
# ---------------------------------------------------------
register_api_routes(app)

# ---------------------------------------------------------
# 4) MCP server
# ---------------------------------------------------------
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/mcp",
    message_path="/mcp/messages",
    stateless_http=True,
)

# FastMCP'nin kendi ASGI app'i
mcp_app = mcp.http_app(path="/mcp")

# Lifespan'i FastAPI'ye geçir
app.router.routes.extend(mcp_app.routes)  # MCP route'larını ana app'e ekle

# MCP tool/resource handler'larını kayıt et
register_mcp(mcp)

# ---------------------------------------------------------
# 5) Uvicorn entrypoint
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
