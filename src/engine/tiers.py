"""
Tier system for the Antarok mana engine.

Tiers are indexed low→high: Novice=0 … Ascendant=5.

Primary values (used by the engine):
    Ascendant=300, Master=100, Expert=33, Journeyman=11, Apprentice=4, Novice=1

Each tier is ~1/3 the cost of the one above it.
"""
from enum import IntEnum
from fractions import Fraction
from ..config import TIER_VALUES, TIER_ORDER


class Tier(IntEnum):
    NOVICE = 0
    APPRENTICE = 1
    JOURNEYMAN = 2
    EXPERT = 3
    MASTER = 4
    ASCENDANT = 5


# Human-readable names, low → high
TIER_NAMES: list[str] = [t.name.title() for t in Tier]
# High → low (useful for UI dropdowns)
TIER_NAMES_HIGH_FIRST: list[str] = list(reversed(TIER_NAMES))


def tier_from_name(name: str) -> Tier:
    """Parse a tier name (case-insensitive) into a Tier enum value."""
    return Tier[name.upper()]


def base_value(highest_tier: Tier, target_tier: Tier) -> Fraction:
    """
    Return the exact mana value of *target_tier* for a character whose
    highest tier is *highest_tier*.

        base_value(H, T) = Fraction(1, 3 ** (H - T))

    Raises ValueError if target_tier > highest_tier.
    """
    diff = int(highest_tier) - int(target_tier)
    if diff < 0:
        raise ValueError(
            f"Target tier {target_tier.name} ({int(target_tier)}) exceeds "
            f"highest tier {highest_tier.name} ({int(highest_tier)})"
        )
    return Fraction(1, 3 ** diff)


def base_value_matrix(highest_tier: Tier) -> dict[str, Fraction]:
    """
    Return a dict of {tier_name: base_value} for every tier at or below
    *highest_tier*.  Useful for building tables and tests.
    (Legacy exact-fraction helper — kept for reference.)
    """
    return {
        t.name.title(): base_value(highest_tier, t)
        for t in Tier
        if t <= highest_tier
    }


# ── Primary tier value helpers ─────────────────────────────────────────────────

def tier_value(tier: Tier) -> float:
    """
    Return the absolute mana value for a tier.

    Ascendant→300, Master→100, Expert→33, Journeyman→11, Apprentice→4, Novice→1
    """
    return float(TIER_VALUES[tier.name.title()])


def tier_below(tier: Tier) -> "Tier | None":
    """
    Return the Tier one step below *tier*, or None if *tier* is Novice.
    Used when looking up efficiency costs (which are multiples of the tier below).
    """
    if tier == Tier.NOVICE:
        return None
    return Tier(int(tier) - 1)


def tier_value_matrix() -> dict[str, float]:
    """Return {tier_name: value} for all tiers, high → low."""
    return {name: float(TIER_VALUES[name]) for name in TIER_ORDER}
