"""Premium growth checker — validates option premium increase.

Premium Growth % = (Current - Old) / Old * 100
Condition: growth > threshold (default 4%)
"""

from backend.config import PREMIUM_GROWTH_THRESHOLD


def check_premium_growth(
    current_premium: float,
    old_premium: float,
) -> tuple[bool, float]:
    """Return (passes_threshold, growth_percent)."""
    if old_premium <= 0:
        return False, 0.0

    growth_pct = round((current_premium - old_premium) / old_premium * 100, 2)
    return growth_pct > PREMIUM_GROWTH_THRESHOLD, growth_pct
