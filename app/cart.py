from .catalog import CATALOG

CART = {}

def format_price(amount: float) -> str:
    return f"{amount:,.2f} ₺".replace(",", ".")

def build_cart_summary():
    items = []
    total_amount = 0
    total_qty = 0

    for pid, qty in CART.items():
        product = next((p for p in CATALOG if p["id"] == pid), None)
        if not product:
            continue

        subtotal = product["price"] * qty
        items.append({
            "id": pid,
            "name": product["name"],
            "quantity": qty,
            "unitPrice": product["price"],
            "unitPriceFormatted": format_price(product["price"]),
            "subtotal": subtotal,
            "subtotalFormatted": format_price(subtotal)
        })

        total_amount += subtotal
        total_qty += qty

    return {
        "items": items,
        "totalAmount": total_amount,
        "totalAmountFormatted": format_price(total_amount),
        "totalQuantity": total_qty
    }
