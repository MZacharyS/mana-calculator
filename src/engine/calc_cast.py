"""
Single-spell cast cost engine.

Cost formula
────────────
Standard spell:
    cost = TIER_VALUES[spell_tier]

Non-Standard efficiency (Efficient / Optimal / Inefficient / Strenuous):
    cost = EFFICIENCY_BELOW_MULT[efficiency] × TIER_VALUES[tier_one_step_below]

Novice (no tier below):
    cost = NOVICE_EFFICIENCY_COSTS[efficiency]   (fixed decimals)

Orders of Expression (applied after efficiency):
    cost = cost × (1 − order_discount)

Quantity:
    bundled  → ceil(cost × N, 2 decimal places)   ← ceiling applied once
    per_cast → ceil(cost, 2) × N

Situational modifier (optional, e.g. Fraction(1,4) for grove):
    Applied after efficiency by default; configurable to after expression.

All arithmetic uses floats; ceiling is applied at the quantity step.
"""
import math
from fractions import Fraction
from .tiers import Tier, tier_value, tier_below
from ..config import TIER_VALUES, NOVICE_EFFICIENCY_COSTS, EFFICIENCY_BELOW_MULT, get_order_discount


def get_spell_base_cost(spell_tier: Tier, efficiency: str) -> float:
    """
    Return the unmodified base cost for a spell (before orders/situational).

    Standard  → same-tier value        (e.g. Expert=33, Master=100)
    Others    → MULT × tier_below      (e.g. Expert Efficient = 2 × 11 = 22)
    Novice    → fixed decimal           (e.g. Novice Efficient = 0.66)
    """
    if spell_tier == Tier.NOVICE:
        return float(NOVICE_EFFICIENCY_COSTS[efficiency])

    if efficiency == "Standard":
        return tier_value(spell_tier)

    below = tier_below(spell_tier)
    mult = EFFICIENCY_BELOW_MULT[efficiency]
    return float(mult * TIER_VALUES[below.name.title()])


def compute_cast_cost(
    highest_tier: Tier,                         # accepted for API compat; not used
    spell_tier: Tier,
    efficiency: str = "Standard",
    orders: int = 0,
    situational_modifier: Fraction | float | None = None,
    situational_insertion: str = "after_efficiency",
) -> float:
    """
    Return the UNROUNDED mana cost of a single spell cast (quantity=1).

    Parameters
    ----------
    highest_tier          : Character's highest tier (API compat; not used).
    spell_tier            : Tier at which the spell is cast.
    efficiency            : Standard / Optimal / Efficient / Inefficient / Strenuous.
    orders                : Orders of Expression (0–6+).
    situational_modifier  : Optional multiplier (e.g. 0.25 or Fraction(1,4) for grove).
    situational_insertion : "after_efficiency" (default) or "after_expression".

    Returns
    -------
    float — unrounded cost.
    """
    working = get_spell_base_cost(spell_tier, efficiency)

    if situational_modifier is not None and situational_insertion == "after_efficiency":
        working *= float(situational_modifier)

    discount = float(get_order_discount(orders)) * working
    working -= discount

    if situational_modifier is not None and situational_insertion == "after_expression":
        working *= float(situational_modifier)

    return working


def _ceil2(value: float) -> float:
    """Ceiling to 2 decimal places."""
    return math.ceil(value * 100) / 100


def compute_cast_cost_with_quantity(
    highest_tier: Tier,                         # API compat; not used
    spell_tier: Tier,
    efficiency: str = "Standard",
    orders: int = 0,
    quantity: int = 1,
    quantity_mode: str = "bundled",             # "bundled" or "per_cast"
    situational_modifier: Fraction | float | None = None,
    situational_insertion: str = "after_efficiency",
    display_mode: str = "ones",                 # accepted for API compat; not used
) -> float:
    """
    Return the ROUNDED total cost for *quantity* casts.

    bundled  (default): ceil(unrounded × N, 2dp) — ceiling applied once.
    per_cast           : ceil(unrounded, 2dp) × N — ceiling per individual cast.
    """
    unrounded = compute_cast_cost(
        highest_tier, spell_tier, efficiency, orders,
        situational_modifier, situational_insertion,
    )

    if quantity_mode == "bundled":
        return _ceil2(unrounded * quantity)
    else:  # per_cast
        return _ceil2(unrounded) * quantity
