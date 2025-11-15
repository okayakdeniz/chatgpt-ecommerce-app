CATALOG = [
    {"id": "p1", "name": "Laptop", "price": 25000, "description": "14'' iş laptopu"},
    {"id": "p2", "name": "Kulaklık", "price": 1500, "description": "Bluetooth kulaklık"},
    {"id": "p3", "name": "Mouse", "price": 600, "description": "Kablosuz mouse"},
    {"id": "p4", "name": "Klavye", "price": 900, "description": "Mekanik klavye"},
]

def search_catalog(query: str | None):
    if not query:
        return CATALOG
    q = query.lower()
    return [p for p in CATALOG if q in p["name"].lower() or q in p["description"].lower()]
