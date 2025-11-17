from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.routes import register_api_routes
from app.mcp_handlers import register_mcp

# FastAPI Ana App
app = FastAPI()

# MCP Server
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/mcp/sse",
    message_path="/mcp/messages",
    stateless_http=True
)

# MCP alt uygulaması
mcp_app = mcp.streamable_http_app()

# ==============================================================
# *** KRİTİK DÜZELTME ***
# Azure WEBSITES mount edilen alt uygulamaların route'larını drop ediyor.
# Bu yüzden MCP'nin route'larını MANUEL olarak FastAPI ana app'e kopyalıyoruz.
# ==============================================================

for route in mcp_app.router.routes:
    app.router.routes.append(route)

# MCP Tool kayıtları
register_mcp(mcp)

# Diğer API route’ları
register_api_routes(app)

# Debug
APP_VERSION = "1.0.1"  # Her değişiklikte manuel olarak güncellersiniz

@app.get("/__routes__")
async def debug_routes():
    return {
        "version": APP_VERSION,
        "routes": [route.path for route in app.router.routes]
    }

if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
