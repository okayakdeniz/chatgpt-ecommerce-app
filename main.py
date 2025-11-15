from mcp.server.fastmcp import FastMCP
from app.routes import register_api_routes
from app.mcp_handlers import register_mcp
from fastapi import FastAPI

# MCP server
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/mcp",
    message_path="/mcp/messages",
    stateless_http=True
)

# FastAPI app
app = FastAPI()

# MCP Streamable HTTP mount
mcp_app = mcp.streamable_http_app()
app.mount("/", mcp_app)

# OAuth + OIDC endpointleri mount et
register_api_routes(app)

# MCP tool + resource kayıtları
register_mcp(mcp)

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
