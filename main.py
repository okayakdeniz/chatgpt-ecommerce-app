from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.routes import register_api_routes
from app.mcp_handlers import register_mcp

# =====================================================
# 1) FastAPI app
# =====================================================
app = FastAPI()

# =====================================================
# 2) MCP Server (stateless_http OLMADAN)
# =====================================================
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/mcp/sse",
    message_path="/mcp/messages"
    # stateless_http=True <- BUNU KALDIR!
)

# MCP tools'u kaydet
register_mcp(mcp)

# =====================================================
# 3) MCP route'larını ÖNCE ekle
# =====================================================
mcp_app = mcp.streamable_http_app()  # <-- DOĞRU METOD

# Debug için
print("\n=== MCP Routes ===")
for route in mcp_app.router.routes:
    print(f"  {route.path}")

# MCP route'larını ekle
for route in mcp_app.router.routes:
    app.router.routes.append(route)

# =====================================================
# 4) SONRA Normal API routes
# =====================================================
register_api_routes(app)

# =====================================================
# 5) Debug route
# =====================================================
@app.get("/__routes__")
async def debug_routes():
    return [{"path": route.path} for route in app.router.routes]


if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
