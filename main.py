from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.routes import register_api_routes
from app.mcp_handlers import register_mcp

app = FastAPI()

# MCP Sunucusu
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/sse",
    message_path="/messages",
    stateless_http=True
)

# MCP HTTP uygulaması
mcp_app = mcp.streamable_http_app()

# /mcp altında mount et
app.mount("/mcp", mcp_app)

# MCP tool kayıtları
register_mcp(mcp)

# Normal API kayıtları
register_api_routes(app)

# Debug
@app.get("/__routes__")
async def routes():
    return [route.path for route in app.router.routes]


if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
