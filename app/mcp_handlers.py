from mcp.server import FastMCP
from .catalog import search_catalog, CATALOG
from .cart import CART, build_cart_summary


def register_mcp(mcp: FastMCP):
    """MCP tool registration"""

    @mcp.tool()
    async def search_products(query: str = "") -> dict:
        """Katalogda ürün ara"""
        results = search_catalog(query)
        return {
            "products": results,
            "count": len(results),
            "message": f"{len(results)} ürün bulundu"
        }

    @mcp.tool()
    async def add_to_cart(productId: str) -> dict:
        """Sepete ürün ekle"""
        product = next((p for p in CATALOG if p["id"] == productId), None)
        if not product:
            return {"success": False, "message": "Ürün bulunamadı"}

        CART[productId] = CART.get(productId, 0) + 1
        summary = build_cart_summary()

        return {
            "success": True,
            "message": f"{product['name']} sepete eklendi",
            "cart": summary
        }

    @mcp.tool()
    async def remove_from_cart(productId: str) -> dict:
        """Sepetten ürün çıkar"""
        if productId not in CART:
            return {"success": False, "message": "Ürün sepette değil"}

        del CART[productId]
        summary = build_cart_summary()

        return {
            "success": True,
            "message": "Ürün sepetten çıkarıldı",
            "cart": summary
        }

    @mcp.tool()
    async def get_cart() -> dict:
        """Sepeti göster"""
        summary = build_cart_summary()

        if not CART:
            return {
                "isEmpty": True,
                "message": "Sepetiniz boş",
                "cart": summary
            }

        return {
            "isEmpty": False,
            "message": f"Sepetinizde {summary['totalQuantity']} ürün var",
            "cart": summary
        }

    @mcp.tool()
    async def checkout() -> dict:
        """Siparişi tamamla ve öde"""
        summary = build_cart_summary()

        if not CART:
            return {
                "success": False,
                "message": "Sepet boş, sipariş verilemez"
            }

        order_summary = {
            "orderId": f"ORD-{hash(str(CART)) % 10000:04d}",
            "items": summary["items"],
            "total": summary["totalAmountFormatted"],
            "itemCount": summary["totalQuantity"]
        }

        CART.clear()

        return {
            "success": True,
            "message": f"Siparişiniz alındı! Toplam: {order_summary['total']}",
            "order": order_summary
        }