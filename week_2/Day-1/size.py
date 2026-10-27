import json
from tools_v1 import get_data
from tools_v2 import search_orders

print("v1 chars:", len(json.dumps(get_data("riya"))))
print("v2 chars:", len(json.dumps(search_orders(customer="riya"))))