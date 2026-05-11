"""Liquidity checker — ensures bid-ask spread is tight enough to trade.

Spread % = (Ask - Bid) / Ask * 100
Condition: spread < threshold (default 2%)
"""

from backend.config import LIQUIDITY_SPREAD_THRESHOLD


def check_liquidity(bid: float, ask: float) -> tuple[bool, float]:
    """Return (is_liquid, spread_percent)."""
    if ask <= 0:
        return False, 100.0

    spread_pct = round((ask - bid) / ask * 100, 2)
    return spread_pct < LIQUIDITY_SPREAD_THRESHOLD, spread_pct
