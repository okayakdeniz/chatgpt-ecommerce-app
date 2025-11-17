from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.routes import register_api_routes
from app.mcp_handlers import register_mcp


# =====================================================
# 1) MCP Server Tanımı
# =====================================================
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/sse",
    message_path="/messages",
    stateless_http=True
)

# =====================================================
# 2) FastAPI Ana App
# =====================================================
app = FastAPI()

# MCP Streamable HTTP uygulamasını oluştur
mcp_app = mcp.streamable_http_app()

# Azure dahil tüm ortamlar için doğru mount
# Bu yapı ile gerçek endpoint'ler:
#   /mcp/sse
#   /mcp/messages
app.mount("/mcp", mcp_app)

# =====================================================
# 3) OAuth + API + MCP Tool Kayıtları
# =====================================================
register_api_routes(app)
register_mcp(mcp)

# =====================================================
# 4) Debug Endpoint — Tüm route’ları gösterir
# =====================================================
@app.get("/__routes__")
async def debug_routes():
    return [route.path for route in app.router.routes]


# =====================================================
# 5) Local run
# =====================================================
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
