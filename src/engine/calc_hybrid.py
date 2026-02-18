"""
Hybrid spell cost engine.

A Hybrid Spell combines two spells cast simultaneously:
  1. Compute each component cost via get_spell_base_cost() (no rounding).
  2. combined  = cost_A + cost_B
  3. hybrid    = combined × (2/3)   ← the Efficient modifier applied to combined
  4. Apply optional situational modifier.
  5. Apply Orders of Expression discount.
  6. Apply ceiling rounding once at the end (2 decimal places).

Both component spells must be the same tier (validated by caller/UI).
"""
import math
from fractions import Fraction
from .tiers import Tier
from .calc_cast import get_spell_base_cost, _ceil2
from ..config import get_order_discount

_HYBRID_MULT = 2 / 3


def compute_hybrid_cost(
    highest_tier: Tier,                         # API compat; not used
    spell_a: dict,
    spell_b: dict,
    orders: int = 0,
    situational_modifier: Fraction | float | None = None,
    situational_insertion: str = "after_efficiency",
    display_mode: str = "ones",                 # API compat; not used
) -> float:
    """
    Return the ROUNDED total cost of a hybrid spell.

    Parameters
    ----------
    highest_tier   : Character's highest tier (API compat; not used).
    spell_a / spell_b : Dicts with keys:
                        "tier"       (Tier)
                        "efficiency" (str, default "Standard")
    orders         : Orders of Expression (applied to combined hybrid cost).
    situational_modifier : Optional multiplier (Fraction or float).
    situational_insertion: "after_efficiency" (default) or "after_expression".
    display_mode   : Accepted for API compat; not used.

    Returns
    -------
    float — ceiling-rounded hybrid cost.
    """
    tier_a = spell_a["tier"]
    tier_b = spell_b["tier"]
    eff_a = spell_a.get("efficiency", "Standard")
    eff_b = spell_b.get("efficiency", "Standard")

    # Step 1: individual unrounded base costs (no orders/situational here)
    cost_a = get_spell_base_cost(tier_a, eff_a)
    cost_b = get_spell_base_cost(tier_b, eff_b)

    # Step 2-3: combine and apply hybrid efficient modifier
    combined = cost_a + cost_b
    hybrid = combined * _HYBRID_MULT

    # Step 4: situational modifier (default: after_efficiency = after hybrid mult)
    if situational_modifier is not None and situational_insertion == "after_efficiency":
        hybrid *= float(situational_modifier)

    # Step 5: Orders of Expression
    discount = float(get_order_discount(orders)) * hybrid
    hybrid -= discount

    # Step 4 alt: after expression
    if situational_modifier is not None and situational_insertion == "after_expression":
        hybrid *= float(situational_modifier)

    # Step 6: ceiling rounding
    return _ceil2(hybrid)
