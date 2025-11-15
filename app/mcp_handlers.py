from mcp.server.fastmcp import FastMCP
import mcp.types as types
from .widget import widget, widget_meta
from .catalog import search_catalog
from .cart import CART, build_cart_summary

def register_mcp(mcp: FastMCP):

    @mcp._mcp_server.list_tools()
    async def list_tools():
        meta = widget_meta(widget)
        return [
            types.Tool(name="search_products", title="Ürün ara", description="Katalogda ara",
                       inputSchema={"type": "object","properties":{"query":{"type":"string"}}},
                       _meta=meta),
            types.Tool(name="add_to_cart", title="Sepete ekle", description="Sepete ürün",
                       inputSchema={"type":"object","properties":{"productId":{"type":"string"}}},
                       _meta=meta),
            types.Tool(name="remove_from_cart", title="Sepetten çıkar", description="Kaldır",
                       inputSchema={"type":"object","properties":{"productId":{"type":"string"}}},
                       _meta=meta),
            types.Tool(name="get_cart", title="Sepeti göster", description="Sepet durumunu getir",
                       inputSchema={"type":"object","properties":{}},
                       _meta=meta),
            types.Tool(name="checkout", title="Ödeme", description="Mock ödeme",
                       inputSchema={"type":"object","properties":{}},
                       _meta=meta),
        ]

    # diğer MCP handler’lar buraya...
