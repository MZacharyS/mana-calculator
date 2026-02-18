"""Tests for engine/tiers.py — tier indexing and base_value()."""
import pytest
from fractions import Fraction
from src.engine.tiers import Tier, tier_from_name, base_value, base_value_matrix


class TestTierEnum:
    def test_index_ordering(self):
        assert Tier.NOVICE < Tier.APPRENTICE < Tier.JOURNEYMAN
        assert Tier.JOURNEYMAN < Tier.EXPERT < Tier.MASTER < Tier.ASCENDANT

    def test_index_values(self):
        assert int(Tier.NOVICE) == 0
        assert int(Tier.APPRENTICE) == 1
        assert int(Tier.JOURNEYMAN) == 2
        assert int(Tier.EXPERT) == 3
        assert int(Tier.MASTER) == 4
        assert int(Tier.ASCENDANT) == 5

    def test_tier_from_name_case_insensitive(self):
        assert tier_from_name("master") == Tier.MASTER
        assert tier_from_name("NOVICE") == Tier.NOVICE
        assert tier_from_name("Expert") == Tier.EXPERT


class TestBaseValue:
    """base_value(H, T) = Fraction(1, 3^(H-T))"""

    def test_same_tier_is_one(self):
        for tier in Tier:
            assert base_value(tier, tier) == Fraction(1)

    def test_one_below(self):
        assert base_value(Tier.MASTER, Tier.EXPERT) == Fraction(1, 3)
        assert base_value(Tier.ASCENDANT, Tier.MASTER) == Fraction(1, 3)

    def test_two_below(self):
        assert base_value(Tier.MASTER, Tier.JOURNEYMAN) == Fraction(1, 9)

    def test_three_below(self):
        assert base_value(Tier.MASTER, Tier.APPRENTICE) == Fraction(1, 27)

    def test_four_below(self):
        assert base_value(Tier.MASTER, Tier.NOVICE) == Fraction(1, 81)

    def test_five_below(self):
        assert base_value(Tier.ASCENDANT, Tier.NOVICE) == Fraction(1, 243)

    def test_exceeds_highest_raises(self):
        with pytest.raises(ValueError):
            base_value(Tier.JOURNEYMAN, Tier.MASTER)

    def test_exact_fractions(self):
        # Verify these are exact Fraction objects, not floats
        result = base_value(Tier.MASTER, Tier.EXPERT)
        assert isinstance(result, Fraction)
        assert result.numerator == 1
        assert result.denominator == 3


class TestBaseValueMatrix:
    def test_master_matrix(self):
        matrix = base_value_matrix(Tier.MASTER)
        expected = {
            "Novice":     Fraction(1, 81),
            "Apprentice": Fraction(1, 27),
            "Journeyman": Fraction(1, 9),
            "Expert":     Fraction(1, 3),
            "Master":     Fraction(1),
        }
        assert matrix == expected

    def test_matrix_excludes_tiers_above_highest(self):
        matrix = base_value_matrix(Tier.EXPERT)
        assert "Master" not in matrix
        assert "Ascendant" not in matrix
        assert "Expert" in matrix

    def test_novice_matrix_has_only_novice(self):
        matrix = base_value_matrix(Tier.NOVICE)
        assert matrix == {"Novice": Fraction(1)}

    def test_ascendant_matrix_has_all_six_tiers(self):
        matrix = base_value_matrix(Tier.ASCENDANT)
        assert len(matrix) == 6
