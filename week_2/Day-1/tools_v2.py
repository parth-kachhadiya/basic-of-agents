from tools_v1 import ORDERS, tool


def get_order(order_id, response_format="concise"):
    o = ORDERS.get(order_id)
    if o is None:
        return (f"No order '{order_id}'. IDs look like A101. "
                "Use search_orders to find an order by customer name or email.")
    if response_format == "concise":
        return {k: o[k] for k in ("id", "item", "status", "total")}
    return o


def search_orders(customer=None, status=None, limit=5, cursor=0):
    rows = [
        o for o in ORDERS.values()
        if (customer is None or customer.lower() in (o["customer"] + o["email"]).lower())
        and (status is None or o["status"] == status)
    ]
    page = rows[cursor:cursor + limit]
    nxt = cursor + limit if cursor + limit < len(rows) else None
    return {
        "orders": [{k: o[k] for k in ("id", "customer", "item", "status")} for o in page],
        "next_cursor": nxt,
    }


def cancel_order(order_id):
    o = ORDERS.get(order_id)
    if o is None:
        return f"No order '{order_id}'. Use search_orders to find the right ID first."
    if o["status"] != "processing":
        return (f"Order {order_id} is '{o['status']}'. Only 'processing' orders can be "
                "cancelled. Tell the user to request a return instead.")
    o["status"] = "cancelled"
    return f"Order {order_id} cancelled."


def update_shipping_address(order_id, new_address):
    o = ORDERS.get(order_id)
    if o is None:
        return f"No order '{order_id}'. Use search_orders to find the right ID first."
    if o["status"] != "processing":
        return (f"Order {order_id} is '{o['status']}'. Address can only change while "
                "'processing'. Tell the user it can no longer be changed.")
    o["address"] = new_address
    return f"Order {order_id} now ships to {new_address}."


S = {"type": "string"}

TOOLS_V2 = [
    tool("get_order",
         "Get ONE order by its exact ID (e.g. A101). Use when the user gives an order ID. "
         "Do NOT use to find orders by customer name; use search_orders for that. "
         "Use response_format='detailed' only if address, email or notes are needed.",
         {"order_id": S, "response_format": {"type": "string", "enum": ["concise", "detailed"]}},
         ["order_id"]),
    tool("search_orders",
         "Find orders by customer name or email, and/or by status "
         "(processing, shipped, delivered, cancelled). Returns a short list with IDs. "
         "Use this when the user gives a name or email instead of an order ID. "
         "If next_cursor is not null, call again with that cursor for more.",
         {"customer": S, "status": S, "limit": {"type": "integer"}, "cursor": {"type": "integer"}},
         []),
    tool("cancel_order",
         "Cancel one order by exact ID. Works only for 'processing' orders. "
         "If you only have a customer name, call search_orders first to get the ID.",
         {"order_id": S}, ["order_id"]),
    tool("update_shipping_address",
         "Change the shipping address of one order by exact ID. Works only for "
         "'processing' orders. Do NOT use for cancelling.",
         {"order_id": S, "new_address": S}, ["order_id", "new_address"]),
]