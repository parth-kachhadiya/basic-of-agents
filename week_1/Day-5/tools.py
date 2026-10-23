"""
tools.py - Week 1, Day 2
 
Three real tools + a registry (TOOLS) that agent.py uses.
Install first:  uv add requests


Helper :
    ast library:
        The Python ast (Abstract Syntax Trees) module is a built-in library used to parse Python source code into a hierarchical tree structure. 
        This allows you to programmatically analyze, modify, or execute Python code without running it directly
"""

import ast, time
import operator as op
from pathlib import Path

import requests


# ---------------------------------------------------------------
# Helper: build the schema the model sees
# ---------------------------------------------------------------
def make_schema(name, description, properties, required):
    return {
        'type' : 'function',
        'function' : {
            'name' : name,
            'description' : description,
            'parameters' : {
                'type' : 'object',
                'properties' : properties,
                'required' : required
            }
        }
    }

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


# ---------------------------------------------------------------
# Tool 3: local file search (only inside ./notes)
# ---------------------------------------------------------------
SEARCH_ROOT = Path("notes")  # change to Path(".") to search the whole project
 
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".idea", ".vscode"}
SKIP_FILES = {".env", "calls.jsonl"}  # never show secrets or logs to the model
MAX_FILE_BYTES = 1_000_000  # skip files bigger than ~1 MB
 
 
def _is_text_file(path: Path) -> bool:
    """Binary files (images, pdf, zip...) contain null bytes in the first chunk."""
    try:
        with open(path, "rb") as f:
            return b"\0" not in f.read(2048)
    except OSError:
        return False
 
 
def search_files(keyword: str) -> dict:
    if not SEARCH_ROOT.exists():
        raise FileNotFoundError(f"folder '{SEARCH_ROOT}' does not exist")
 
    matches = []
    files_checked = 0
    for path in SEARCH_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts) or path.name in SKIP_FILES:
            continue
        if path.stat().st_size > MAX_FILE_BYTES or not _is_text_file(path):
            continue
 
        files_checked += 1
        for line_no, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            if keyword.lower() in line.lower():
                matches.append({"file": str(path), "line": line_no, "text": line.strip()[:200]})
                if len(matches) >= 10:  # keep output small so we don't flood the context
                    return {"keyword": keyword, "matches": matches, "truncated": True}
    return {"keyword": keyword, "files_checked": files_checked, "matches": matches, "truncated": False}
 
 

# ---------------------------------------------------------------
# Registry: name -> schema + real function
# ---------------------------------------------------------------
TOOLS = {
    'calculator' : {
        'schema' : make_schema(
            'calculator',
            "Evaluate a math expression like '(31 - 28) * 2'. Supports + - * / % **.",
            {"expression": {"type": "string", "description": "The math expression"}},
            ["expression"],
        ),
        'fn' : calculator
    },

    'get_weather' : { 
        'schema' : make_schema(
            'get_weather',
            "Get the current real weather (temperature in C, wind, condition) for a city.",
            {"city": {"type": "string", "description": "City name, e.g. Surat"}},
            ["city"],
        ),
        'fn' : get_weather
    },

    'search_files' : {
        'schema' : make_schema(
            'search_files',
            "Search all text files in the user's local folder for a keyword. Returns matching lines with file names.",
            {'keyword' : {"type": "string", "description": "Word or phrase to look for"}},
            ["keyword"],
        ),
        "fn": search_files,
    },
}