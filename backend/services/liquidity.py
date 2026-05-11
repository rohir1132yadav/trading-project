"""Liquidity checker — ensures bid-ask spread is acceptable for trading.

Spread % = (Ask - Bid) / Spot * 100
Condition: spread < threshold (default 40%)

Trade at Ask price if spread is within threshold.
"""

from backend.config import LIQUIDITY_SPREAD_THRESHOLD


def check_liquidity(
    bid: float, ask: float, spot: float
) -> tuple[bool, float]:
    """Return (is_liquid, spread_percent).

    Uses the formula: (Ask - Bid) / Spot * 100
    """
    if spot <= 0:
        return False, 100.0

    spread_pct = round((ask - bid) / spot * 100, 2)
    return spread_pct < LIQUIDITY_SPREAD_THRESHOLD, spread_pct
