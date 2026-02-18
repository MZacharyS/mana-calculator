"""
Spreadsheet Compatibility Mode — reproduces ManaFormula.xlsx behaviour.

This is an APPROXIMATE calculator that matches the integer-rounded tier values
from the spreadsheet.  It is explicitly separate from the exact-fraction engine.

Tier values (from spreadsheet):
  Ascendant=300, Master=100, Expert=33, Journeyman=11, Apprentice=4, Novice=1

For non-Standard efficiency types (tiers above Novice):
  cost = MULT × value_of_tier_below

  Efficient   → 2 × tier_below
  Optimal     → 1 × tier_below
  Inefficient → 4 × tier_below
  Strenuous   → 5 × tier_below

Novice has no tier below; fixed costs are used (0.66 / 0.33 / 1.33 / 1.66).
Standard always costs the same-tier value.
"""
from ..config import (
    SPREADSHEET_TIER_VALUES,
    SPREADSHEET_TIER_ORDER,
    SPREADSHEET_NOVICE_COSTS,
    SPREADSHEET_EFFICIENCY_BELOW_MULT,
)


def _tier_below_value(tier_name: str) -> float | None:
    """Return the spreadsheet value of the tier one step below *tier_name*."""
    idx = SPREADSHEET_TIER_ORDER.index(tier_name)
    if idx + 1 >= len(SPREADSHEET_TIER_ORDER):
        return None  # Novice has no tier below
    return SPREADSHEET_TIER_VALUES[SPREADSHEET_TIER_ORDER[idx + 1]]


def get_spreadsheet_spell_cost(tier_name: str, efficiency: str) -> float:
    """
    Return the mana cost for one cast of a spell in spreadsheet mode.

    Parameters
    ----------
    tier_name  : e.g. "Master"
    efficiency : e.g. "Efficient"
    """
    if tier_name == "Novice":
        return SPREADSHEET_NOVICE_COSTS[efficiency]

    if efficiency == "Standard":
        return float(SPREADSHEET_TIER_VALUES[tier_name])

    below = _tier_below_value(tier_name)
    mult = SPREADSHEET_EFFICIENCY_BELOW_MULT[efficiency]
    return float(mult * below)


def compute_spreadsheet_pool(arcana_list: list[dict]) -> float:
    """
    Compute total mana pool in spreadsheet mode.

    Parameters
    ----------
    arcana_list : list of dicts with keys "name" (str) and "tier" (str, e.g. "Master").

    Returns
    -------
    float — total pool using spreadsheet integer-rounded values.
    """
    total = 0.0
    for arcana in arcana_list:
        tier_name = arcana["tier"] if isinstance(arcana["tier"], str) else arcana["tier"].name.title()
        total += SPREADSHEET_TIER_VALUES[tier_name]
    return total


def compute_spreadsheet_remaining(
    total_pool: float,
    spell_log: list[dict],
) -> float:
    """
    Compute remaining mana in spreadsheet mode.

    Parameters
    ----------
    total_pool : float — from compute_spreadsheet_pool().
    spell_log  : list of dicts with keys:
                   "tier"       (str, e.g. "Expert")
                   "efficiency" (str, e.g. "Efficient")
                   "quantity"   (int, default 1)

    Returns
    -------
    float — remaining mana.
    """
    used = 0.0
    for spell in spell_log:
        tier_name = spell["tier"] if isinstance(spell["tier"], str) else spell["tier"].name.title()
        cost = get_spreadsheet_spell_cost(tier_name, spell.get("efficiency", "Standard"))
        used += cost * spell.get("quantity", 1)
    return total_pool - used
