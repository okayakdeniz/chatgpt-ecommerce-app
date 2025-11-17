from mcp.server.fastmcp import FastMCP
from app.routes import register_api_routes
from app.mcp_handlers import register_mcp
from fastapi import FastAPI

# MCP server
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/sse",
    message_path="/messages",
    stateless_http=True
)

# FastAPI ana app
app = FastAPI()

# MCP Streamable HTTP uygulamasını mount et
# ÖNEMLİ: "/" DEĞİL! Çünkü "/" olursa tüm FastAPI route'larını override eder.
mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)

# OAuth + API endpoint'lerini kaydet
register_api_routes(app)

# MCP tool + resource kayıtları
register_mcp(mcp)

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
