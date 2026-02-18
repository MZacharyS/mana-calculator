"""Tests for engine/calc_pool.py — mana pool using absolute tier values."""
from src.engine.tiers import Tier
from src.engine.calc_pool import compute_pool
from src.engine.rounding import fmt_pool


class TestComputePool:
    def test_empty_arcana_list(self):
        total, breakdown = compute_pool(Tier.MASTER, [])
        assert total == 0.0
        assert breakdown == {}

    def test_single_master_arcana(self):
        arcana = [{"name": "Draoidh", "tier": Tier.MASTER}]
        total, breakdown = compute_pool(Tier.MASTER, arcana)
        assert total == 100.0
        assert breakdown == {"Draoidh": 100.0}

    def test_kirin_pool(self):
        """Kirin: Master Draoidh + Master Zephyr → 100 + 100 = 200."""
        arcana = [
            {"name": "Draoidh", "tier": Tier.MASTER},
            {"name": "Zephyr",  "tier": Tier.MASTER},
        ]
        total, breakdown = compute_pool(Tier.MASTER, arcana)
        assert total == 200.0
        assert breakdown["Draoidh"] == 100.0
        assert breakdown["Zephyr"] == 100.0

    def test_serapis_pool(self):
        """Serapis: Master Exodus + Master Fathom + Journeyman Syphon
        = 100 + 100 + 11 = 211.
        """
        arcana = [
            {"name": "Exodus", "tier": Tier.MASTER},
            {"name": "Fathom", "tier": Tier.MASTER},
            {"name": "Syphon", "tier": Tier.JOURNEYMAN},
        ]
        total, breakdown = compute_pool(Tier.MASTER, arcana)
        assert total == 211.0
        assert breakdown["Exodus"] == 100.0
        assert breakdown["Fathom"] == 100.0
        assert breakdown["Syphon"] == 11.0

    def test_all_tier_values(self):
        """Verify each tier contributes its correct absolute value."""
        arcana = [
            {"name": "A", "tier": Tier.ASCENDANT},
            {"name": "B", "tier": Tier.MASTER},
            {"name": "C", "tier": Tier.EXPERT},
            {"name": "D", "tier": Tier.JOURNEYMAN},
            {"name": "E", "tier": Tier.APPRENTICE},
            {"name": "F", "tier": Tier.NOVICE},
        ]
        total, breakdown = compute_pool(Tier.ASCENDANT, arcana)
        assert breakdown["A"] == 300.0
        assert breakdown["B"] == 100.0
        assert breakdown["C"] == 33.0
        assert breakdown["D"] == 11.0
        assert breakdown["E"] == 4.0
        assert breakdown["F"] == 1.0
        assert total == 449.0

    def test_pool_display_kirin(self):
        arcana = [
            {"name": "Draoidh", "tier": Tier.MASTER},
            {"name": "Zephyr",  "tier": Tier.MASTER},
        ]
        total, _ = compute_pool(Tier.MASTER, arcana)
        assert fmt_pool(total) == "200"

    def test_pool_display_serapis(self):
        arcana = [
            {"name": "Exodus", "tier": Tier.MASTER},
            {"name": "Fathom", "tier": Tier.MASTER},
            {"name": "Syphon", "tier": Tier.JOURNEYMAN},
        ]
        total, _ = compute_pool(Tier.MASTER, arcana)
        assert fmt_pool(total) == "211"

    def test_string_tier_input(self):
        """Pool computation should handle string tier names."""
        arcana = [{"name": "Alpha", "tier": "Expert"}]
        total, _ = compute_pool(Tier.MASTER, arcana)
        assert total == 33.0

    def test_pool_is_independent_of_highest_tier(self):
        """Pool value doesn't change based on highest_tier parameter."""
        arcana = [{"name": "X", "tier": Tier.EXPERT}]
        t1, _ = compute_pool(Tier.MASTER, arcana)
        t2, _ = compute_pool(Tier.ASCENDANT, arcana)
        assert t1 == t2 == 33.0
