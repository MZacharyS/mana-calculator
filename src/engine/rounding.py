"""
Rounding utilities for the Antarok mana engine.

All spell costs are rounded UP (ceiling) at the final display step.
Pool values are displayed with standard rounding (not ceiling).

Display modes
─────────────
  "ones"      — decimal, e.g. 0.34  (cost ceiled to hundredths)
  "hundreds"  — cost × 100 as whole number, e.g. 34  (ceiled)
  "fractions" — exact rational string, e.g. "1/3"  (no rounding)
"""
import math
from fractions import Fraction


# ── Core ceiling helpers ───────────────────────────────────────────────────────

def ceil_to_hundredths(value: Fraction) -> Fraction:
    """
    Return *value* rounded UP to 2 decimal places.

    E.g.  Fraction(1, 3) → Fraction(34, 100)   (0.3333… → 0.34)
          Fraction(1, 4) → Fraction(25, 100)    (0.25 exactly → 0.25)
    """
    ceiled = math.ceil(value.numerator * 100 / value.denominator)
    return Fraction(ceiled, 100)


def ceil_to_ones(value: Fraction) -> Fraction:
    """
    Return *value* rounded UP to the nearest whole number.

    E.g.  Fraction(4, 3) → Fraction(2)   (1.333… → 2)
          Fraction(3, 3) → Fraction(1)   (1.0 exactly → 1)
    """
    ceiled = math.ceil(value.numerator / value.denominator)
    return Fraction(ceiled)


# ── Cost rounding (spell costs, NOT pool) ─────────────────────────────────────

def round_cost(value: Fraction, mode: str) -> Fraction:
    """
    Apply the display-mode ceiling rule to a spell cost.

    mode="ones"     → ceil to hundredths  (e.g. 1/3 → 34/100)
    mode="hundreds" → ceil(value × 100) / 100  (same underlying fraction,
                       displayed as an integer when multiplied by 100)
    mode="fractions"→ no rounding (return exact)
    """
    if mode == "ones":
        return ceil_to_hundredths(value)
    elif mode == "hundreds":
        # ceil to nearest 'hundred unit' (1 unit = 1/100 in 'ones' scale)
        return ceil_to_hundredths(value)   # same ceiling; display layer ×100
    elif mode == "fractions":
        return value
    else:
        raise ValueError(f"Unknown display mode: {mode!r}")


# ── Formatting ─────────────────────────────────────────────────────────────────

def format_cost(value: Fraction, mode: str) -> str:
    """Format a SPELL COST for display (ceiling applied)."""
    if mode == "ones":
        ceiled = ceil_to_hundredths(value)
        return f"{float(ceiled):.2f}"
    elif mode == "hundreds":
        ceiled = ceil_to_ones(value * 100)
        return str(int(ceiled))
    elif mode == "fractions":
        return _fmt_fraction(value)
    else:
        raise ValueError(f"Unknown display mode: {mode!r}")


def format_pool(value: Fraction, mode: str) -> str:
    """
    Format a POOL value for display (standard rounding, not ceiling).
    The pool represents what you *have*; we show it honestly.
    """
    if mode == "ones":
        # Standard round to 2 decimal places
        return f"{float(value):.2f}"
    elif mode == "hundreds":
        return f"{float(value * 100):.2f}"
    elif mode == "fractions":
        return _fmt_fraction(value)
    else:
        raise ValueError(f"Unknown display mode: {mode!r}")


def _fmt_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


# ── Float-based helpers (primary engine) ───────────────────────────────────────

def fmt_value(value: float) -> str:
    """
    Format a float mana value cleanly:
      • Whole numbers → integer string  (e.g. 100 → "100",  22 → "22")
      • Fractional    → 2 decimal places (e.g. 28.05 → "28.05", 0.66 → "0.66")
    Ceiling is NOT applied here; apply _ceil2() before calling if needed.
    """
    v = round(value, 10)          # strip floating-point noise (e.g. 99.9999…)
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}"


def fmt_cost(value: float) -> str:
    """Format a spell cost float: ceiling to 2dp, then clean integer/decimal."""
    import math
    ceiled = math.ceil(value * 100) / 100
    return fmt_value(ceiled)


def fmt_pool(value: float) -> str:
    """Format a pool float (no ceiling — show what you have)."""
    return fmt_value(value)
