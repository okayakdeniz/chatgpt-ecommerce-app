from fastapi import FastAPI
from fastmcp import FastMCP

from app.routes import register_api_routes
from app.mcp_handlers import register_mcp

# --------------------------------------------------------
# 1) Normal API
# --------------------------------------------------------

api = FastAPI()
register_api_routes(api)

# --------------------------------------------------------
# 2) MCP Server FastAPI Üzerine Eklenir
# --------------------------------------------------------

mcp = FastMCP.from_fastapi(api)

# MCP tool'larını ekle
register_mcp(mcp)

# MCP'nin kendi http_app'i
mcp_app = mcp.http_app(path="/mcp")

# --------------------------------------------------------
# 3) ANA APP = MCP + API ROUTELARI BİR ARADA
# --------------------------------------------------------

app = FastAPI(
    title="Obase Market MCP Server",
    routes=[
        *mcp_app.routes,   # /mcp/sse ve /mcp/messages buradan gelir
        *api.routes,       # /api/... ve OAuth buradan gelir
    ]
)

# --------------------------------------------------------
# 4) Debug routes
# --------------------------------------------------------

@app.get("/__routes__")
async def list_routes():
    return [route.path for route in app.router.routes]


if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
