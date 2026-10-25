"""
tools/travel_tools.py - Week 1, Day 6

The five tools of the Travel Planner:
  get_weather, calculator                               -> reused from tools/tool.py (real)
  search_flights, search_hotels, search_attractions     -> read from mock_data/*.json (mock)

The mock tools fail in USEFUL ways: the error text says what IS possible
("nearest dates with seats: ..."), so the agent can re-plan instead of giving up.
"""
import datetime as dt
import json
from pathlib import Path

from tools.tool import calculator, get_weather

# mock_data/ sits next to the tools/ folder, whatever folder you run Python from
DATA_DIR = Path(__file__).resolve().parent.parent / "mock_data"


def _load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


FLIGHTS = _load("flights.json")
HOTELS = _load("hotels.json")
ATTRACTIONS = _load("attractions.json")

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# --- optional "flaky" mode: the first hotel search fails like a real 503 ---
_FLAKY = {"on": False, "already_failed": False}


def set_flaky(on: bool):
    _FLAKY["on"], _FLAKY["already_failed"] = on, False


def _find(name: str, options) -> str | None:
    """Match a city name ignoring upper/lower case. Returns the official spelling, or None."""
    for option in options:
        if str(name).strip().lower() == option.lower():
            return option
    return None


# ---------------------------------------------------------------
# Tool 3: search_flights
# ---------------------------------------------------------------
_ROUTES = {(r["origin"], r["destination"]): r for r in FLIGHTS["routes"]}
_SOLD_OUT = {(s["origin"], s["destination"], s["date"]) for s in FLIGHTS["sold_out"]}


def search_flights(origin: str, destination: str, date: str) -> dict:
    try:
        day = dt.date.fromisoformat(date)
    except ValueError:
        raise ValueError(f"date '{date}' is not valid. Use YYYY-MM-DD, for example 2026-11-14.")

    # a city without an airport
    for city in (origin, destination):
        key = _find(city, FLIGHTS["no_airport"])
        if key:
            raise ValueError(FLIGHTS["no_airport"][key])

    o = _find(origin, {k[0] for k in _ROUTES})
    d = _find(destination, {k[1] for k in _ROUTES})
    route = _ROUTES.get((o, d))
    if route is None:
        available = ", ".join(f"{a}->{b}" for a, b in _ROUTES)
        raise ValueError(f"No flights from '{origin}' to '{destination}'. Routes available: {available}.")

    # a fully booked date: tell the model which nearby dates DO have seats
    if (o, d, day.isoformat()) in _SOLD_OUT:
        nearby = []
        for shift in (1, -1, 2, -2, 3, -3):
            candidate = (day + dt.timedelta(days=shift)).isoformat()
            if (o, d, candidate) not in _SOLD_OUT:
                nearby.append(candidate)
            if len(nearby) == 2:
                break
        raise ValueError(f"No seats left on {date} for {o} -> {d}. "
                         f"Nearest dates with seats: {', '.join(sorted(nearby))}.")

    weekday = DAYS[day.weekday()]
    surcharge = FLIGHTS["weekend_surcharge_rs"] if weekday in FLIGHTS["weekend_days"] else 0
    return {
        "route": f"{o} -> {d}",
        "date": date,
        "weekday": weekday,
        "weekend_surcharge_included_rs": surcharge,
        "options": [
            {"flight_no": f["flight_no"], "airline": f["airline"], "departs": f["departs"],
             "arrives": f["arrives"], "price_rs": f["price_rs"] + surcharge}
            for f in route["flights"]
        ],
    }


# ---------------------------------------------------------------
# Tool 4: search_hotels
# ---------------------------------------------------------------
def search_hotels(city: str, nights: int, max_price_per_night: float | None = None) -> dict:
    if _FLAKY["on"] and not _FLAKY["already_failed"]:
        _FLAKY["already_failed"] = True
        raise ConnectionError("Hotel service temporarily unavailable (HTTP 503). Please try again.")

    name = _find(city, HOTELS["cities"])
    if name is None:
        raise ValueError(f"No hotel data for '{city}'. Cities available: {', '.join(HOTELS['cities'])}.")
    if int(nights) < 1:
        raise ValueError("nights must be at least 1.")

    all_hotels = HOTELS["cities"][name]
    matching = [h for h in all_hotels
                if max_price_per_night is None or h["price_per_night_rs"] <= max_price_per_night]
    if not matching:
        cheapest = min(all_hotels, key=lambda h: h["price_per_night_rs"])
        raise ValueError(f"No hotel in {name} at or under Rs. {max_price_per_night:,.0f} per night. "
                         f"The cheapest is {cheapest['name']} at Rs. {cheapest['price_per_night_rs']:,} per night.")

    return {
        "city": name,
        "nights": int(nights),
        "hotels": [{**h, "total_price_rs": h["price_per_night_rs"] * int(nights)}
                   for h in sorted(matching, key=lambda h: -h["rating"])],
    }


# ---------------------------------------------------------------
# Tool 5: search_attractions
# ---------------------------------------------------------------
def search_attractions(city: str, interest: str | None = None) -> dict:
    name = _find(city, ATTRACTIONS["cities"])
    if name is None:
        raise ValueError(f"No attraction data for '{city}'. Cities available: {', '.join(ATTRACTIONS['cities'])}.")

    places = ATTRACTIONS["cities"][name]
    if not interest:
        return {"city": name, "places": places}

    chosen = [p for p in places if interest.strip().lower() in p["category"].lower()]
    if chosen:
        return {"city": name, "interest": interest, "places": chosen}
    return {"city": name, "interest": interest, "places": places,
            "note": f"No '{interest}' places in {name}, so all places are shown."}


# ---------------------------------------------------------------
# The registry the agent loop uses: name -> schema + real function
# ---------------------------------------------------------------
def _schema(name, description, properties, required):
    return {"type": "function",
            "function": {"name": name, "description": description,
                         "parameters": {"type": "object", "properties": properties, "required": required}}}


TRAVEL_TOOLS = {
    "get_weather": {
        "schema": _schema(
            "get_weather",
            "Get the CURRENT real weather for a city (not a forecast). Use it as a rough hint only.",
            {"city": {"type": "string", "description": "City name, e.g. Goa"}},
            ["city"]),
        "fn": get_weather,
    },
    "calculator": {
        "schema": _schema(
            "calculator",
            "Evaluate a math expression like '5200 + 4600 + 3 * 2200'. Supports + - * / % **. "
            "Use it for every budget calculation.",
            {"expression": {"type": "string", "description": "The math expression"}},
            ["expression"]),
        "fn": calculator,
    },
    "search_flights": {
        "schema": _schema(
            "search_flights",
            "Search ONE-WAY flights between two cities on one date. Prices are in Indian rupees. "
            "Call it once for the outbound flight and once for the return flight.",
            {"origin": {"type": "string", "description": "Departure city, e.g. Surat"},
             "destination": {"type": "string", "description": "Arrival city, e.g. Goa"},
             "date": {"type": "string", "description": "Date as YYYY-MM-DD, e.g. 2026-11-14"}},
            ["origin", "destination", "date"]),
        "fn": search_flights,
    },
    "search_hotels": {
        "schema": _schema(
            "search_hotels",
            "Search hotels in a city. Returns hotels sorted by rating, with price per night and total price "
            "for the stay (Rs.). Optionally cap the price per night.",
            {"city": {"type": "string", "description": "City name, e.g. Goa"},
             "nights": {"type": "integer", "description": "Number of nights, at least 1"},
             "max_price_per_night": {"type": "number", "description": "Optional maximum price per night in Rs."}},
            ["city", "nights"]),
        "fn": search_hotels,
    },
    "search_attractions": {
        "schema": _schema(
            "search_attractions",
            "List things to do in a city, with cost, duration and best time of day. Optionally filter by "
            "interest: beach, history, food, nature, shopping, sightseeing or culture.",
            {"city": {"type": "string", "description": "City name, e.g. Goa"},
             "interest": {"type": "string", "description": "Optional category to filter by, e.g. food"}},
            ["city"]),
        "fn": search_attractions,
    },
}