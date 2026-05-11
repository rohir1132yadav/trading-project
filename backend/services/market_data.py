"""Market data fetcher — pulls data from the demo trading account API.

When a real demo API is not configured, generates realistic simulated
market data so the app can be developed and tested end-to-end.
"""

import random
from datetime import datetime
from typing import Any

import requests

from backend.config import DEMO_API_BASE_URL

_SIMULATED_BASE_PRICES: dict[str, float] = {
    "RELIANCE": 2450.0, "TCS": 3520.0, "INFY": 1480.0,
    "HDFCBANK": 1620.0, "ICICIBANK": 980.0, "KOTAKBANK": 1750.0,
    "SBIN": 620.0, "BHARTIARTL": 1150.0, "ITC": 440.0, "LT": 3380.0,
    "AXISBANK": 1080.0, "WIPRO": 460.0, "HCLTECH": 1320.0,
    "MARUTI": 10200.0, "SUNPHARMA": 1180.0, "TATAMOTORS": 640.0,
    "ULTRACEMCO": 8500.0, "NTPC": 350.0, "POWERGRID": 290.0,
    "TITAN": 3200.0, "BAJFINANCE": 6800.0, "ASIANPAINT": 2800.0,
    "NESTLEIND": 2400.0, "TECHM": 1280.0, "HINDUNILVR": 2550.0,
}


def _simulate_quote(symbol: str) -> dict[str, Any]:
    base = _SIMULATED_BASE_PRICES.get(symbol, 1000.0)
    change_pct = random.uniform(-4.0, 5.0)
    ltp = round(base * (1 + change_pct / 100), 2)

    spread_pct = random.uniform(0.05, 3.5)
    half_spread = ltp * spread_pct / 200
    bid = round(ltp - half_spread, 2)
    ask = round(ltp + half_spread, 2)

    volume = random.randint(500, 50000)
    premium = round(ltp * random.uniform(0.01, 0.08), 2)

    return {
        "symbol": symbol,
        "ltp": ltp,
        "open": round(base, 2),
        "close": round(base, 2),
        "high": round(max(ltp, base) * 1.005, 2),
        "low": round(min(ltp, base) * 0.995, 2),
        "bid": bid,
        "ask": ask,
        "volume": volume,
        "premium": premium,
        "timestamp": datetime.utcnow().isoformat(),
    }


def fetch_market_data(symbols: list[str]) -> list[dict[str, Any]]:
    """Fetch market data for a list of stock symbols.

    Tries the configured demo API first; falls back to simulated data.
    """
    if DEMO_API_BASE_URL and DEMO_API_BASE_URL != "https://demo-api.com":
        try:
            resp = requests.get(
                f"{DEMO_API_BASE_URL}/market-data",
                params={"symbols": ",".join(symbols)},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            pass

    return [_simulate_quote(s) for s in symbols]


def fetch_single_quote(symbol: str) -> dict[str, Any]:
    return fetch_market_data([symbol])[0]
