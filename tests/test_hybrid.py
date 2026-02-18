"""Tests for engine/calc_hybrid.py — hybrid spell cost pipeline."""
from src.engine.tiers import Tier
from src.engine.calc_hybrid import compute_hybrid_cost
from src.engine.rounding import fmt_cost


class TestHybridCost:
    """
    Hybrid cost formula:
      combined = cost_A + cost_B    (each via get_spell_base_cost, no rounding)
      hybrid   = combined × (2/3)
      → orders of expression discount
      → ceil to 2 decimal places
    """

    def test_two_standard_expert_spells(self):
        """
        Expert Standard + Expert Standard:
        cost_A = 33, cost_B = 33
        combined = 66
        hybrid = 66 × (2/3) = 44  (exact integer)
        """
        spell_a = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        spell_b = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        cost = compute_hybrid_cost(Tier.MASTER, spell_a, spell_b)
        assert cost == 44.0

    def test_two_standard_master_spells(self):
        """
        Master Standard + Master Standard:
        combined = 200
        hybrid = 200 × (2/3) = 133.333… → ceil2 = 133.34
        """
        spell_a = {"tier": Tier.MASTER, "efficiency": "Standard"}
        spell_b = {"tier": Tier.MASTER, "efficiency": "Standard"}
        cost = compute_hybrid_cost(Tier.MASTER, spell_a, spell_b)
        import math
        assert cost == math.ceil(200 * 2 / 3 * 100) / 100   # 133.34

    def test_two_standard_journeyman_spells(self):
        """
        Journeyman Standard + Journeyman Standard:
        combined = 22
        hybrid = 22 × (2/3) = 14.666… → ceil2 = 14.67
        """
        spell_a = {"tier": Tier.JOURNEYMAN, "efficiency": "Standard"}
        spell_b = {"tier": Tier.JOURNEYMAN, "efficiency": "Standard"}
        cost = compute_hybrid_cost(Tier.MASTER, spell_a, spell_b)
        import math
        assert cost == math.ceil(22 * 2 / 3 * 100) / 100

    def test_hybrid_with_mixed_efficiency(self):
        """
        Expert Standard + Expert Efficient:
        cost_A = 33, cost_B = 22
        combined = 55
        hybrid = 55 × (2/3) = 36.666… → ceil2 = 36.67
        """
        spell_a = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        spell_b = {"tier": Tier.EXPERT, "efficiency": "Efficient"}
        cost = compute_hybrid_cost(Tier.MASTER, spell_a, spell_b)
        import math
        assert cost == math.ceil(55 * 2 / 3 * 100) / 100

    def test_hybrid_with_orders(self):
        """
        Expert Standard × 2, 3rd order (15% discount):
        pre-discount hybrid = 44
        discount = 44 × 0.15 = 6.6
        after = 44 − 6.6 = 37.4 → ceil2 = 37.4
        """
        spell_a = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        spell_b = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        cost = compute_hybrid_cost(Tier.MASTER, spell_a, spell_b, orders=3)
        import math
        expected = math.ceil(44 * 0.85 * 100) / 100
        assert cost == expected

    def test_hybrid_with_situational_modifier(self):
        """
        Expert Standard × 2, grove (×0.25):
        pre-situational hybrid = 44
        after × 0.25 = 11.0 → ceil2 = 11.0
        """
        spell_a = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        spell_b = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        cost = compute_hybrid_cost(
            Tier.MASTER, spell_a, spell_b,
            situational_modifier=0.25,
            situational_insertion="after_efficiency",
        )
        assert cost == 11.0

    def test_hybrid_returns_float(self):
        spell_a = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        spell_b = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        cost = compute_hybrid_cost(Tier.MASTER, spell_a, spell_b)
        assert isinstance(cost, float)

    def test_hybrid_display(self):
        spell_a = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        spell_b = {"tier": Tier.EXPERT, "efficiency": "Standard"}
        cost = compute_hybrid_cost(Tier.MASTER, spell_a, spell_b)
        assert fmt_cost(cost) == "44"
