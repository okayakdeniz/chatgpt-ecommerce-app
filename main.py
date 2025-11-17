from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from mcp.server.fastmcp import FastMCP
import json

from app.routes import register_api_routes
from app.mcp_handlers import register_mcp

# =====================================================
# 1) FastAPI app
# =====================================================
app = FastAPI()

# =====================================================
# 2) MCP Server
# =====================================================
mcp = FastMCP(
    name="ecommerce-mcp",
    sse_path="/mcp/sse",
    message_path="/mcp/messages"
)

register_mcp(mcp)

# =====================================================
# 3) MANUEL SSE ENDPOINT'LERİ EKLE
# =====================================================

@app.get("/mcp/sse")
async def mcp_sse_handler(request: Request):
    """SSE endpoint for MCP streaming"""
    async def event_generator():
        # MCP SSE stream'ini oluştur
        try:
            # FastMCP'nin internal handler'ını çağır
            async for message in mcp._handle_sse_stream():
                yield f"data: {json.dumps(message)}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/mcp/messages")
async def mcp_messages_handler(request: Request):
    """HTTP POST endpoint for MCP messages"""
    try:
        body = await request.json()
        result = await mcp._handle_message(body)
        return result
    except Exception as e:
        return {"error": str(e)}, 500

@app.get("/mcp")
async def mcp_info_handler():
    """MCP server info"""
    return {
        "name": "ecommerce-mcp",
        "version": "1.0.0",
        "protocols": ["sse", "http"],
        "endpoints": {
            "sse": "/mcp/sse",
            "messages": "/mcp/messages"
        }
    }

# =====================================================
# 4) Normal API routes
# =====================================================
register_api_routes(app)

# =====================================================
# 5) Debug route
# =====================================================
@app.get("/__routes__")
async def debug_routes():
    return [{"path": route.path, "methods": list(route.methods) if hasattr(route, 'methods') else None} for route in app.router.routes]


if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))