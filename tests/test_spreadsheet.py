"""Tests for engine/spreadsheet_mode.py — ManaFormula.xlsx compatibility."""
from src.engine.tiers import Tier
from src.engine.spreadsheet_mode import (
    get_spreadsheet_spell_cost,
    compute_spreadsheet_pool,
    compute_spreadsheet_remaining,
)


class TestSpreadsheetTierValues:
    """Verify the spreadsheet tier integer values are correct."""

    def test_master_standard_cost(self):
        assert get_spreadsheet_spell_cost("Master", "Standard") == 100.0

    def test_expert_standard_cost(self):
        assert get_spreadsheet_spell_cost("Expert", "Standard") == 33.0

    def test_journeyman_standard_cost(self):
        assert get_spreadsheet_spell_cost("Journeyman", "Standard") == 11.0

    def test_apprentice_standard_cost(self):
        assert get_spreadsheet_spell_cost("Apprentice", "Standard") == 4.0

    def test_novice_standard_cost(self):
        assert get_spreadsheet_spell_cost("Novice", "Standard") == 1.0

    def test_ascendant_standard_cost(self):
        assert get_spreadsheet_spell_cost("Ascendant", "Standard") == 300.0


class TestSpreadsheetEfficiencyCosts:
    """Verify non-Standard efficiency costs match formula: mult × tier_below."""

    def test_master_efficient(self):
        # Efficient = 2 × Expert(33) = 66
        assert get_spreadsheet_spell_cost("Master", "Efficient") == 66.0

    def test_master_optimal(self):
        # Optimal = 1 × Expert(33) = 33
        assert get_spreadsheet_spell_cost("Master", "Optimal") == 33.0

    def test_master_inefficient(self):
        # Inefficient = 4 × Expert(33) = 132
        assert get_spreadsheet_spell_cost("Master", "Inefficient") == 132.0

    def test_master_strenuous(self):
        # Strenuous = 5 × Expert(33) = 165
        assert get_spreadsheet_spell_cost("Master", "Strenuous") == 165.0

    def test_expert_efficient(self):
        # Efficient = 2 × Journeyman(11) = 22
        assert get_spreadsheet_spell_cost("Expert", "Efficient") == 22.0

    def test_ascendant_efficient(self):
        # Efficient = 2 × Master(100) = 200
        assert get_spreadsheet_spell_cost("Ascendant", "Efficient") == 200.0

    def test_novice_efficient(self):
        assert get_spreadsheet_spell_cost("Novice", "Efficient") == 0.66

    def test_novice_optimal(self):
        assert get_spreadsheet_spell_cost("Novice", "Optimal") == 0.33

    def test_novice_inefficient(self):
        assert get_spreadsheet_spell_cost("Novice", "Inefficient") == 1.33

    def test_novice_strenuous(self):
        assert get_spreadsheet_spell_cost("Novice", "Strenuous") == 1.66


class TestSpreadsheetPool:
    """Verify SUMPRODUCT pool calculation."""

    def test_kirin_pool(self):
        """Kirin: Master Draoidh + Master Zephyr = 100 + 100 = 200."""
        arcana = [
            {"name": "Draoidh", "tier": "Master"},
            {"name": "Zephyr",  "tier": "Master"},
        ]
        assert compute_spreadsheet_pool(arcana) == 200.0

    def test_serapis_pool(self):
        """Serapis: Master Exodus + Master Fathom + Journeyman Syphon = 100+100+11 = 211."""
        arcana = [
            {"name": "Exodus", "tier": "Master"},
            {"name": "Fathom", "tier": "Master"},
            {"name": "Syphon", "tier": "Journeyman"},
        ]
        assert compute_spreadsheet_pool(arcana) == 211.0

    def test_mixed_tier_pool(self):
        arcana = [
            {"name": "A", "tier": "Expert"},      # 33
            {"name": "B", "tier": "Journeyman"},  # 11
            {"name": "C", "tier": "Apprentice"},  # 4
        ]
        assert compute_spreadsheet_pool(arcana) == 48.0

    def test_spreadsheet_remaining(self):
        """After 2 Master Standard casts (100 each), pool 200 → remaining 0."""
        spell_log = [
            {"tier": "Master", "efficiency": "Standard", "quantity": 1},
            {"tier": "Master", "efficiency": "Standard", "quantity": 1},
        ]
        remaining = compute_spreadsheet_remaining(200.0, spell_log)
        assert remaining == 0.0

    def test_spreadsheet_remaining_efficient(self):
        """Pool 200, 1 Master Efficient cast (66) → remaining 134."""
        spell_log = [{"tier": "Master", "efficiency": "Efficient", "quantity": 1}]
        remaining = compute_spreadsheet_remaining(200.0, spell_log)
        assert remaining == 134.0

    def test_spreadsheet_remaining_with_quantity(self):
        """Pool 200, 2 Expert Standard (33 each) → remaining 134."""
        spell_log = [{"tier": "Expert", "efficiency": "Standard", "quantity": 2}]
        remaining = compute_spreadsheet_remaining(200.0, spell_log)
        assert remaining == 134.0

    def test_spreadsheet_reproduces_xlsx_formula(self):
        """
        Reproduce the sample ManaFormula.xlsx scenario:
          Arcana: Ascendant×1, Master×2, Expert×3, Journeyman×1, Apprentice×1
          Spells:
            Ascendant Standard×1   = 300
            Master Efficient×1     = 66
            Expert Inefficient×1   = 44 (4×11)
            Journeyman Optimal×1   = 4  (1×4)
            Apprentice Strenuous×1 = 5  (5×1)
          Total pool  = 300 + 200 + 99 + 11 + 4 = 614
          Total spent = 300 + 66 + 44 + 4 + 5 = 419
          Remaining   = 614 - 419 = 195
        """
        arcana = [
            {"name": "A1", "tier": "Ascendant"},
            {"name": "M1", "tier": "Master"},
            {"name": "M2", "tier": "Master"},
            {"name": "E1", "tier": "Expert"},
            {"name": "E2", "tier": "Expert"},
            {"name": "E3", "tier": "Expert"},
            {"name": "J1", "tier": "Journeyman"},
            {"name": "P1", "tier": "Apprentice"},
        ]
        pool = compute_spreadsheet_pool(arcana)
        assert pool == 300 + 100 + 100 + 33 + 33 + 33 + 11 + 4  # 614

        spells = [
            {"tier": "Ascendant",  "efficiency": "Standard",    "quantity": 1},  # 300
            {"tier": "Master",     "efficiency": "Efficient",   "quantity": 1},  # 66
            {"tier": "Expert",     "efficiency": "Inefficient", "quantity": 1},  # 4×11=44
            {"tier": "Journeyman", "efficiency": "Optimal",     "quantity": 1},  # 1×4=4
            {"tier": "Apprentice", "efficiency": "Strenuous",   "quantity": 1},  # 5×1=5
        ]
        remaining = compute_spreadsheet_remaining(pool, spells)
        assert remaining == 614 - 300 - 66 - 44 - 4 - 5  # 195
