from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.routes import register_api_routes
from app.mcp_handlers import register_mcp


# =====================================================
# 1) MCP Server
# =====================================================
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/mcp/sse",
    message_path="/mcp/messages",
    stateless_http=True
)

# FastAPI app
app = FastAPI()

# =====================================================
# 2) MCP ROUTELARINI FASTAPI İÇİNE EKLE
# =====================================================
mcp_app = mcp.streamable_http_app()

# mcp_app içindeki tüm route’ları FastAPI’ye manuel ekle
for route in mcp_app.router.routes:
    app.router.routes.append(route)

# =====================================================
# 3) Normal API + OAuth + MCP Tools
# =====================================================
register_api_routes(app)
register_mcp(mcp)

# =====================================================
# 4) Debug route
# =====================================================
@app.get("/__routes__")
async def debug_routes():
    return [route.path for route in app.router.routes]


if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
