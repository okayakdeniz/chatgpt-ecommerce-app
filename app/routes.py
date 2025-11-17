from fastapi import APIRouter, Query
from app.oauth import register_oauth_routes
from app.catalog import search_catalog, CATALOG
from app.cart import CART, build_cart_summary

def register_api_routes(app):

    # OAuth endpointleri
    register_oauth_routes(app)

    # ---------------------------------------------------
    # E-TİCARET API ROUTELARI (ChatGPT Actions için gerekli)
    # ---------------------------------------------------
    router = APIRouter(prefix="/api", tags=["ecommerce"])

    # 1) Ürün arama
    @router.get("/products")
    async def search_products_endpoint(query: str = Query("", description="Arama terimi")):
        results = search_catalog(query)
        return {
            "products": results,
            "count": len(results),
            "message": f"{len(results)} ürün bulundu"
        }

    # 2) Sepete ekleme
    @router.post("/cart/add")
    async def add_to_cart_endpoint(productId: str):
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

    # 3) Sepetten çıkarma
    @router.post("/cart/remove")
    async def remove_from_cart_endpoint(productId: str):
        if productId not in CART:
            return {"success": False, "message": "Ürün sepette değil"}

        del CART[productId]
        summary = build_cart_summary()

        return {
            "success": True,
            "message": "Ürün sepetten çıkarıldı",
            "cart": summary
        }

    # 4) Sepeti görüntüleme
    @router.get("/cart")
    async def get_cart_endpoint():
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

    # 5) Ödeme / sipariş tamamlama
    @router.post("/checkout")
    async def checkout_endpoint():
        summary = build_cart_summary()

        if len(CART) == 0:
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

    app.include_router(router)
