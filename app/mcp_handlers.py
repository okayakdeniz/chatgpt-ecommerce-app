from mcp.server.fastmcp import FastMCP
from .catalog import search_catalog
from .cart import CART, build_cart_summary

def register_mcp(mcp: FastMCP):
    """MCP tool'larını kaydet"""
    
    @mcp.tool()
    async def search_products(query: str = "") -> dict:
        """Katalogda ürün ara
        
        Args:
            query: Arama terimi (boş ise tüm ürünler)
        """
        results = search_catalog(query)
        return {
            "products": results,
            "count": len(results),
            "message": f"{len(results)} ürün bulundu"
        }
    
    @mcp.tool()
    async def add_to_cart(productId: str) -> dict:
        """Sepete ürün ekle
        
        Args:
            productId: Ürün ID (örn: p1, p2)
        """
        from .catalog import CATALOG
        
        # Ürün var mı kontrol et
        product = next((p for p in CATALOG if p["id"] == productId), None)
        if not product:
            return {"success": False, "message": "Ürün bulunamadı"}
        
        # Sepete ekle
        CART[productId] = CART.get(productId, 0) + 1
        summary = build_cart_summary()
        
        return {
            "success": True,
            "message": f"{product['name']} sepete eklendi",
            "cart": summary
        }
    
    @mcp.tool()
    async def remove_from_cart(productId: str) -> dict:
        """Sepetten ürün çıkar
        
        Args:
            productId: Çıkarılacak ürün ID
        """
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
        
        if len(CART) == 0:
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
        
        if len(CART) == 0:
            return {
                "success": False,
                "message": "Sepet boş, sipariş verilemez"
            }
        
        # Sipariş bilgisi
        order_summary = {
            "orderId": f"ORD-{hash(str(CART)) % 10000:04d}",
            "items": summary["items"],
            "total": summary["totalAmountFormatted"],
            "itemCount": summary["totalQuantity"]
        }
        
        # Sepeti temizle
        CART.clear()
        
        return {
            "success": True,
            "message": f"✅ Siparişiniz alındı! Toplam: {order_summary['total']}",
            "order": order_summary
        }