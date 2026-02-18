"""
Mana pool computation.

Pool = Σ TIER_VALUES[arcana_tier]  for every arcana the character possesses.

Each arcana contributes its absolute tier value regardless of the character's
highest tier.  (The highest_tier parameter is accepted for API compatibility
but is no longer part of the pool calculation.)

Tier values: Ascendant=300, Master=100, Expert=33, Journeyman=11, Apprentice=4, Novice=1
"""
from .tiers import Tier, tier_from_name, tier_value


def compute_pool(
    highest_tier: Tier,       # accepted for API compatibility; not used in calc
    arcana_list: list[dict],
) -> tuple[float, dict[str, float]]:
    """
    Compute a character's total mana pool and per-arcana breakdown.

    Parameters
    ----------
    highest_tier : Tier
        The character's highest tier (kept in signature for compatibility).
    arcana_list : list of dict
        Each dict must have keys "name" (str) and "tier" (Tier or str).

    Returns
    -------
    total_pool : float
        Sum of absolute tier values for all arcana.
    breakdown : dict[str, float]
        {arcana_name: tier_value} for display.

    Examples
    --------
    Kirin  (Master Draoidh + Master Zephyr):  100 + 100 = 200
    Serapis (Master Exodus + Master Fathom + Journeyman Syphon): 100+100+11 = 211
    """
    breakdown: dict[str, float] = {}
    total = 0.0

    for arcana in arcana_list:
        t = arcana["tier"]
        if isinstance(t, str):
            t = tier_from_name(t)
        val = tier_value(t)
        breakdown[arcana["name"]] = val
        total += val

    return total, breakdown
