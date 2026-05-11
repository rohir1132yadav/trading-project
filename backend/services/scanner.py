"""Stock scanner — Layer 3/4 strategy implementation.

Pipeline (from whiteboard):
  Stocks list  →  Volume > 1000  →  Daily change > 2%
               →  Liquidity check (spread < 2%)
               →  Premium growth > 4%
               →  Generate BUY signal
"""

from sqlalchemy.orm import Session

from backend.config import (
    DAILY_INCREASE_THRESHOLD,
    DEFAULT_STOCKS,
    MIN_VOLUME,
)
from backend.models.models import PriceHistory, Signal, Stock
from backend.services.liquidity import check_liquidity
from backend.services.market_data import fetch_market_data
from backend.services.premium import check_premium_growth


def _ensure_stocks_exist(db: Session) -> list[str]:
    existing = {s.symbol for s in db.query(Stock.symbol).all()}
    for sym in DEFAULT_STOCKS:
        if sym not in existing:
            db.add(Stock(symbol=sym, is_active=True))
    db.commit()

    return [
        s.symbol
        for s in db.query(Stock).filter(Stock.is_active.is_(True)).all()
    ]


def _calculate_daily_change(current_ltp: float, prev_close: float) -> float:
    if prev_close == 0:
        return 0.0
    return round((current_ltp - prev_close) / prev_close * 100, 2)


def run_scan(db: Session) -> list[dict]:
    """Execute the full scan pipeline and return generated signals."""
    symbols = _ensure_stocks_exist(db)
    quotes = fetch_market_data(symbols)

    signals: list[dict] = []

    for q in quotes:
        symbol = q["symbol"]
        ltp = q["ltp"]
        bid = q.get("bid", 0)
        ask = q.get("ask", 0)
        volume = q.get("volume", 0)
        premium = q.get("premium", 0)
        prev_close = q.get("close", ltp)

        db.add(PriceHistory(
            symbol=symbol,
            ltp=ltp,
            open_price=q.get("open"),
            close_price=prev_close,
            high_price=q.get("high"),
            low_price=q.get("low"),
            bid_price=bid,
            ask_price=ask,
            volume=volume,
            premium=premium,
        ))

        if volume < MIN_VOLUME:
            continue

        daily_change = _calculate_daily_change(ltp, prev_close)
        if daily_change < DAILY_INCREASE_THRESHOLD:
            continue

        spread_ok, spread_pct = check_liquidity(bid, ask)
        if not spread_ok:
            continue

        last_price = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol)
            .order_by(PriceHistory.recorded_at.desc())
            .offset(1)
            .first()
        )
        old_premium = last_price.premium if last_price and last_price.premium else premium * 0.9
        premium_ok, premium_growth = check_premium_growth(premium, old_premium)

        signal_type = "BUY" if premium_ok else "HOLD"
        confidence = min(
            100.0,
            (daily_change / DAILY_INCREASE_THRESHOLD) * 30
            + ((2.0 - spread_pct) / 2.0) * 30
            + (premium_growth / 4.0) * 40,
        )

        sig = Signal(
            symbol=symbol,
            signal_type=signal_type,
            daily_change_pct=daily_change,
            spread_pct=spread_pct,
            premium_growth_pct=premium_growth,
            ltp=ltp,
            confidence=round(confidence, 1),
            notes=f"Vol={volume}, Spread={spread_pct}%, PremGrowth={premium_growth}%",
        )
        db.add(sig)
        signals.append({
            "symbol": symbol,
            "signal": signal_type,
            "ltp": ltp,
            "daily_change": daily_change,
            "spread": spread_pct,
            "premium_growth": premium_growth,
            "confidence": round(confidence, 1),
        })

    db.commit()
    return signals
