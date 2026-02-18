"""Tests for engine/calc_cast.py — spell cost pipeline."""
import math
import pytest
from src.engine.tiers import Tier
from src.engine.calc_cast import (
    get_spell_base_cost,
    compute_cast_cost,
    compute_cast_cost_with_quantity,
)
from src.engine.rounding import fmt_cost


class TestGetSpellBaseCost:
    """Base cost before orders/situational — no rounding applied here."""

    # ── Standard (same-tier value) ─────────────────────────────────────────────
    def test_ascendant_standard(self):
        assert get_spell_base_cost(Tier.ASCENDANT, "Standard") == 300.0

    def test_master_standard(self):
        assert get_spell_base_cost(Tier.MASTER, "Standard") == 100.0

    def test_expert_standard(self):
        assert get_spell_base_cost(Tier.EXPERT, "Standard") == 33.0

    def test_journeyman_standard(self):
        assert get_spell_base_cost(Tier.JOURNEYMAN, "Standard") == 11.0

    def test_apprentice_standard(self):
        assert get_spell_base_cost(Tier.APPRENTICE, "Standard") == 4.0

    def test_novice_standard(self):
        assert get_spell_base_cost(Tier.NOVICE, "Standard") == 1.0

    # ── Efficient = 2 × tier_below ────────────────────────────────────────────
    def test_master_efficient(self):
        # 2 × Expert(33) = 66
        assert get_spell_base_cost(Tier.MASTER, "Efficient") == 66.0

    def test_expert_efficient(self):
        # 2 × Journeyman(11) = 22
        assert get_spell_base_cost(Tier.EXPERT, "Efficient") == 22.0

    def test_journeyman_efficient(self):
        # 2 × Apprentice(4) = 8
        assert get_spell_base_cost(Tier.JOURNEYMAN, "Efficient") == 8.0

    def test_apprentice_efficient(self):
        # 2 × Novice(1) = 2
        assert get_spell_base_cost(Tier.APPRENTICE, "Efficient") == 2.0

    def test_novice_efficient_fixed(self):
        assert get_spell_base_cost(Tier.NOVICE, "Efficient") == 0.66

    # ── Optimal = 1 × tier_below ──────────────────────────────────────────────
    def test_master_optimal(self):
        # 1 × Expert(33) = 33
        assert get_spell_base_cost(Tier.MASTER, "Optimal") == 33.0

    def test_expert_optimal(self):
        # 1 × Journeyman(11) = 11
        assert get_spell_base_cost(Tier.EXPERT, "Optimal") == 11.0

    def test_novice_optimal_fixed(self):
        assert get_spell_base_cost(Tier.NOVICE, "Optimal") == 0.33

    # ── Inefficient = 4 × tier_below ─────────────────────────────────────────
    def test_master_inefficient(self):
        # 4 × Expert(33) = 132
        assert get_spell_base_cost(Tier.MASTER, "Inefficient") == 132.0

    def test_expert_inefficient(self):
        # 4 × Journeyman(11) = 44
        assert get_spell_base_cost(Tier.EXPERT, "Inefficient") == 44.0

    def test_novice_inefficient_fixed(self):
        assert get_spell_base_cost(Tier.NOVICE, "Inefficient") == 1.33

    # ── Strenuous = 5 × tier_below ───────────────────────────────────────────
    def test_master_strenuous(self):
        # 5 × Expert(33) = 165
        assert get_spell_base_cost(Tier.MASTER, "Strenuous") == 165.0

    def test_expert_strenuous(self):
        # 5 × Journeyman(11) = 55
        assert get_spell_base_cost(Tier.EXPERT, "Strenuous") == 55.0

    def test_novice_strenuous_fixed(self):
        assert get_spell_base_cost(Tier.NOVICE, "Strenuous") == 1.66


class TestComputeCastCost:
    """Full pipeline: base + orders + situational (unrounded)."""

    def test_no_discount(self):
        cost = compute_cast_cost(Tier.MASTER, Tier.EXPERT)
        assert cost == 33.0

    def test_third_order_discount(self):
        # Expert Standard × (1 − 0.15) = 33 × 0.85 = 28.05
        cost = compute_cast_cost(Tier.MASTER, Tier.EXPERT, "Standard", orders=3)
        assert abs(cost - 28.05) < 1e-9

    def test_sixth_order_is_max(self):
        cost_6 = compute_cast_cost(Tier.MASTER, Tier.EXPERT, orders=6)
        cost_7 = compute_cast_cost(Tier.MASTER, Tier.EXPERT, orders=7)
        assert cost_6 == cost_7

    def test_zero_orders_no_change(self):
        assert compute_cast_cost(Tier.MASTER, Tier.EXPERT, orders=0) == 33.0

    def test_situational_after_efficiency(self):
        # Expert Standard × 0.25 = 33 × 0.25 = 8.25
        cost = compute_cast_cost(
            Tier.MASTER, Tier.EXPERT, "Standard", orders=0,
            situational_modifier=0.25,
            situational_insertion="after_efficiency",
        )
        assert abs(cost - 8.25) < 1e-9

    def test_situational_after_expression(self):
        # Expert Standard + 3rd order = 28.05, then × 0.25 = 7.0125
        cost = compute_cast_cost(
            Tier.MASTER, Tier.EXPERT, "Standard", orders=3,
            situational_modifier=0.25,
            situational_insertion="after_expression",
        )
        assert abs(cost - 7.0125) < 1e-9


class TestCeilRounding:
    """Ceiling applied at quantity step."""

    def test_whole_number_unchanged(self):
        # Expert Standard = 33 (whole number)
        assert fmt_cost(33.0) == "33"

    def test_fractional_ceils_up(self):
        # 28.05 → ceil(28.05 × 100)/100 = 28.05 (already 2dp exact)
        assert fmt_cost(28.05) == "28.05"

    def test_repeating_decimal_ceils_up(self):
        # e.g. 28.049999 due to float arithmetic → should ceil to 28.05
        val = 33 * 0.85      # 28.05, but check float noise
        ceiled = math.ceil(val * 100) / 100
        assert ceiled == 28.05

    def test_novice_efficient_display(self):
        # 0.66 is already 2dp
        assert fmt_cost(0.66) == "0.66"


class TestQuantityRounding:
    """Bundled vs per-cast ceiling with quantity."""

    def test_bundled_whole_quantity(self):
        # Expert Standard × 3 = 33 × 3 = 99
        cost = compute_cast_cost_with_quantity(Tier.MASTER, Tier.EXPERT, quantity=3)
        assert cost == 99.0

    def test_per_cast_whole_quantity(self):
        # ceil(33) × 3 = 33 × 3 = 99 (same when no fractional part)
        cost = compute_cast_cost_with_quantity(
            Tier.MASTER, Tier.EXPERT, quantity=3, quantity_mode="per_cast"
        )
        assert cost == 99.0

    def test_bundled_with_order_discount(self):
        # Expert Standard + 3rd order = 28.05 unrounded × 1 = 28.05 ceiled to 28.05
        cost = compute_cast_cost_with_quantity(
            Tier.MASTER, Tier.EXPERT, orders=3, quantity=1
        )
        assert cost == 28.05

    def test_bundled_cheaper_or_equal_than_per_cast(self):
        # When costs have fractional parts, bundled ≤ per_cast
        cost_b = compute_cast_cost_with_quantity(
            Tier.MASTER, Tier.EXPERT, orders=3, quantity=3, quantity_mode="bundled"
        )
        cost_p = compute_cast_cost_with_quantity(
            Tier.MASTER, Tier.EXPERT, orders=3, quantity=3, quantity_mode="per_cast"
        )
        assert cost_b <= cost_p

    def test_zero_quantity(self):
        cost = compute_cast_cost_with_quantity(Tier.MASTER, Tier.EXPERT, quantity=0)
        assert cost == 0.0

    def test_efficient_expert_quantity_bundled(self):
        # Expert Efficient = 22 × 3 = 66
        cost = compute_cast_cost_with_quantity(
            Tier.MASTER, Tier.EXPERT, "Efficient", quantity=3
        )
        assert cost == 66.0
