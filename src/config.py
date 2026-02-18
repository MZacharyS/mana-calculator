"""
Global configuration for the Antarok Mana Calculator.
Edit this file to adjust Orders of Expression discounts or other tunable values.
"""
from fractions import Fraction

# ── Tier names ─────────────────────────────────────────────────────────────────
# Ordered low → high (matches Tier IntEnum values 0-5)
TIER_NAMES = ["Novice", "Apprentice", "Journeyman", "Expert", "Master", "Ascendant"]
TIER_NAMES_HIGH_FIRST = list(reversed(TIER_NAMES))

# ── Orders of Expression ───────────────────────────────────────────────────────
# order_index → discount fraction.  Rules state ~5%/order, cap 30%.
# Change values here to update the entire app + tests.
ORDERS_OF_EXPRESSION: dict[int, Fraction] = {
    0: Fraction(0),
    1: Fraction(5, 100),
    2: Fraction(10, 100),
    3: Fraction(15, 100),
    4: Fraction(20, 100),
    5: Fraction(25, 100),
    6: Fraction(30, 100),
}
MAX_ORDER_DISCOUNT: Fraction = Fraction(30, 100)


def get_order_discount(order: int) -> Fraction:
    """Return the expression discount for the given order (capped at max)."""
    if order <= 0:
        return Fraction(0)
    return ORDERS_OF_EXPRESSION.get(order, MAX_ORDER_DISCOUNT)


# ── Spell Efficiency Names ─────────────────────────────────────────────────────
EFFICIENCY_NAMES = ["Standard", "Optimal", "Efficient", "Inefficient", "Strenuous"]

# ── Primary Tier Values ────────────────────────────────────────────────────────
# Each tier is 1/3 the cost of the one above (rounded to integers).
# These are the canonical mana values used throughout the engine.
#   Ascendant=300, Master=100, Expert=33, Journeyman=11, Apprentice=4, Novice=1
TIER_VALUES: dict[str, int | float] = {
    "Ascendant":  300,
    "Master":     100,
    "Expert":     33,
    "Journeyman": 11,
    "Apprentice": 4,
    "Novice":     1,
}

# Tier order, high → low (used for "tier below" lookups)
TIER_ORDER: list[str] = ["Ascendant", "Master", "Expert", "Journeyman", "Apprentice", "Novice"]

# Novice has no tier below — use these fixed decimal costs instead.
NOVICE_EFFICIENCY_COSTS: dict[str, float] = {
    "Standard":    1.00,
    "Efficient":   0.66,
    "Optimal":     0.33,
    "Inefficient": 1.33,
    "Strenuous":   1.66,
}

# For non-Standard efficiency at tiers above Novice:
#   cost = EFFICIENCY_BELOW_MULT[efficiency] × TIER_VALUES[tier_one_step_below]
#
# Efficient   → 2 × tier_below   (cheaper than standard)
# Optimal     → 1 × tier_below   (cheapest non-novice)
# Inefficient → 4 × tier_below   (more expensive)
# Strenuous   → 5 × tier_below   (most expensive)
EFFICIENCY_BELOW_MULT: dict[str, int] = {
    "Efficient":   2,
    "Optimal":     1,
    "Inefficient": 4,
    "Strenuous":   5,
}

# ── Legacy aliases (kept for spreadsheet_mode.py backward compat) ──────────────
SPREADSHEET_TIER_VALUES = TIER_VALUES
SPREADSHEET_TIER_ORDER = TIER_ORDER
SPREADSHEET_NOVICE_COSTS = NOVICE_EFFICIENCY_COSTS
SPREADSHEET_EFFICIENCY_BELOW_MULT = EFFICIENCY_BELOW_MULT

# ── Built-in Macros ────────────────────────────────────────────────────────────
# Default macro templates.  "arcana_name" left blank for the user to fill.
DEFAULT_MACROS: list[dict] = [
    {
        "name": "Apparating (Frequency Up + Down)",
        "description": (
            "Teleportation requires two separate casts: Frequency Up and Frequency Down. "
            "Logging them as one 'Apparating' entry is a known audit error."
        ),
        "spells": [
            {
                "spell_name": "Frequency Up",
                "arcana_name": "",
                "tier": "Journeyman",
                "efficiency": "Standard",
                "orders": 0,
                "quantity": 1,
            },
            {
                "spell_name": "Frequency Down",
                "arcana_name": "",
                "tier": "Journeyman",
                "efficiency": "Standard",
                "orders": 0,
                "quantity": 1,
            },
        ],
    }
]
