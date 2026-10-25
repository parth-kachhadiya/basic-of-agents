import ast
import operator as op
import requests


# ---------------------------------------------------------------
# Tool 1: calculator (safe, no eval())
# ---------------------------------------------------------------
_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")

def calculator(expression: str) -> dict:
    tree = ast.parse(expression, mode="eval")
    return {"expression": expression, "result": _eval(tree.body)}


# ---------------------------------------------------------------
# Tool 2: weather via Open-Meteo (free, no API key)
# ---------------------------------------------------------------
_WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 80: "rain showers",
    95: "thunderstorm",
}
 
 
def get_weather(city: str) -> dict:
    # Step 1: city name -> latitude/longitude
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo.raise_for_status()
    results = geo.json().get("results")
    if not results:
        raise ValueError(f"city '{city}' not found")
    place = results[0]
 
    # Step 2: lat/lon -> current weather
    w = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,weather_code,wind_speed_10m",
        },
        timeout=10,
    )
    w.raise_for_status()
    cur = w.json()["current"]
    
    # In order to check whether timeout error is raising or not..
    # time.sleep(30) 

    return {
        "city": place["name"],
        "country": place.get("country"),
        "temp_c": cur["temperature_2m"],
        "wind_kmh": cur["wind_speed_10m"],
        "condition": _WEATHER_CODES.get(cur["weather_code"], f"code {cur['weather_code']}"),
    }
