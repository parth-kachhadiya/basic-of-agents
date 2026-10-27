import json

ORDERS = {
    "A101": {"id": "A101", "customer": "Riya Shah", "email": "riya@example.com", "item": "Blue Kettle", "status": "shipped", "address": "12 Ring Rd, Surat", "total": 1299, "created": "2026-10-01", "notes": "gift wrap"},
    "A102": {"id": "A102", "customer": "Arjun Mehta", "email": "arjun@example.com", "item": "Desk Lamp", "status": "processing", "address": "8 Mill St, Ahmedabad", "total": 899, "created": "2026-10-12", "notes": ""},
    "A103": {"id": "A103", "customer": "Neha Patel", "email": "neha@example.com", "item": "Yoga Mat", "status": "delivered", "address": "4 Garden Ln, Vadodara", "total": 650, "created": "2026-09-20", "notes": ""},
    "A104": {"id": "A104", "customer": "Riya Shah", "email": "riya@example.com", "item": "Water Bottle", "status": "processing", "address": "12 Ring Rd, Surat", "total": 450, "created": "2026-10-20", "notes": ""},
    "A105": {"id": "A105", "customer": "Neha Patel", "email": "neha@example.com", "item": "Backpack", "status": "processing", "address": "4 Garden Ln, Vadodara", "total": 2100, "created": "2026-10-22", "notes": "fragile"},
}


def get_data(q):
    q = q.lower()
    return [o for o in ORDERS.values() if q in json.dumps(o).lower()]


def search(query):
    query = query.lower()
    return [o["id"] for o in ORDERS.values() if query in json.dumps(o).lower()]


def update(id, data):
    order = ORDERS.get(id)
    if order is None or order["status"] != "processing":
        return "ERR 4"
    order.update(data)
    return "ok"


def tool(name, desc, props, required):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": required},
    }}


TOOLS_V1 = [
    tool("get_data", "Gets data.", {"q": {"type": "string"}}, ["q"]),
    tool("search", "Search.", {"query": {"type": "string"}}, ["query"]),
    tool("update", "Updates thing.",
         {"id": {"type": "string"}, "data": {"type": "object"}}, ["id", "data"]),
]