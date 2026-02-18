# Antarok Mana Calculator

A mana-pool and spell-cost calculator for the **Antarok RPG** Arcana magic system.

Built for the Antarok forums. Rules source: https://wiki.antarok.net/index.php/Arcana#Mana

---

## Quick Start

```bash
cd Projects/Antarok/mana-calculator

# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run app_ui.py

# Run tests
pytest tests/ -v
```

---

## What It Does

| Feature | Status |
|---|---|
| Exact-fraction mana pool (no float drift) | ✅ |
| Single-spell cost pipeline (base → efficiency → orders → ceil) | ✅ |
| Hybrid spell cost (combined × 2/3) | ✅ |
| Repeat/quantity (bundled vs per-cast rounding) | ✅ |
| Situational modifiers (configurable insertion point) | ✅ |
| Spreadsheet Compatibility Mode (ManaFormula.xlsx parity) | ✅ |
| Display modes: ones / hundreds / fractions | ✅ |
| Audit ledger with spell_name + arcana_name + spell_tier | ✅ |
| JSON + CSV export | ✅ |
| JSON import | ✅ |
| Macros (Apparating = Freq Up + Freq Down built-in) | ✅ |
| Custom macro builder | ✅ |
| Sample characters (Kirin, Serapis) | ✅ |

---

## Rules Engine

### Tiers

```
Ascendant=5, Master=4, Expert=3, Journeyman=2, Apprentice=1, Novice=0
```

### Base Value Formula

```
base_value(H, T) = 1 / 3^(H_index - T_index)
```

Examples for a **Master** character:

| Spell Tier | Value | Decimal |
|---|---|---|
| Master | 1/1 | 1.00 |
| Expert | 1/3 | 0.34 (ceiled) |
| Journeyman | 1/9 | 0.12 (ceiled) |
| Apprentice | 1/27 | 0.04 (ceiled) |
| Novice | 1/81 | 0.02 (ceiled) |

### Efficiency Multipliers

| Type | Multiplier | Effect |
|---|---|---|
| Standard | ×1 | Full tier cost |
| Optimal | ×1/3 | Very cheap |
| Efficient | ×2/3 | Cheaper |
| Inefficient | ×4/3 | More expensive |
| Strenuous | ×5/3 | Very expensive |

### Orders of Expression

Each order reduces cost by ~5%, capped at 30% (6th order):

| Order | Discount |
|---|---|
| 0 | 0% |
| 1 | 5% |
| 2 | 10% |
| 3 | 15% |
| 4 | 20% |
| 5 | 25% |
| 6 | 30% |

Configurable in `src/config.py`.

### Cost Calculation (Order of Operations)

```
1. base            = base_value(highest_tier, spell_tier)
2. after_eff       = base × efficiency_multiplier
3. [optional]      = after_eff × situational_modifier   ← default position
4. discount        = working × order_discount_fraction
5. discounted      = working − discount
6. total           = discounted × quantity              (bundled mode)
7. final           = CEILING(total, 0.01)               (ones mode)
```

### Hybrid Spells

```
cost_A   = base_A × eff_A
cost_B   = base_B × eff_B
combined = cost_A + cost_B
hybrid   = combined × (2/3)        ← Efficient modifier on combined
         → apply orders discount
         → apply ceiling
```

### Spreadsheet Compatibility Mode

Reproduces ManaFormula.xlsx with approximate integer tier values:

| Tier | Value |
|---|---|
| Ascendant | 300 |
| Master | 100 |
| Expert | 33 |
| Journeyman | 11 |
| Apprentice | 4 |
| Novice | 1 |

Non-Standard efficiency cost = `MULT × value_of_tier_below`:
- Efficient = 2×, Optimal = 1×, Inefficient = 4×, Strenuous = 5×
- Novice fixed: Efficient=0.66, Optimal=0.33, Inefficient=1.33, Strenuous=1.66

---

## Project Structure

```
mana-calculator/
├── app_ui.py              # Streamlit UI entry point
├── requirements.txt
├── README.md
├── src/
│   ├── config.py          # Tunable config (orders table, efficiency multipliers)
│   └── engine/
│       ├── tiers.py       # Tier enum, base_value()
│       ├── rounding.py    # Ceiling helpers, format_cost(), format_pool()
│       ├── calc_pool.py   # compute_pool()
│       ├── calc_cast.py   # compute_cast_cost(), compute_cast_cost_with_quantity()
│       ├── calc_hybrid.py # compute_hybrid_cost()
│       └── spreadsheet_mode.py  # Spreadsheet compat
├── tests/
│   ├── conftest.py
│   ├── test_tiers.py
│   ├── test_pool.py
│   ├── test_cast.py
│   ├── test_hybrid.py
│   └── test_spreadsheet.py
├── sample_data/
│   ├── kirin.json         # Kirin character (2.00 pool)
│   └── serapis.json       # Serapis character (2.11 pool = 19/9)
└── data/
    └── ManaFormula.xlsx   # Original spreadsheet reference
```

---

## Known Limitations / Next Steps

- **Kirin/Serapis spell sequences**: The exact spell-cast lists from the wiki examples
  are not published. The pool totals are encoded as tests; the ledger sequences must
  be added manually once the wiki details are available.
- **Macros**: Custom macros are session-only; they reset on page reload.
  Next step: persist macros in JSON alongside the character file.
- **Rules updates**: If the Orders of Expression table or efficiency multipliers change,
  update `src/config.py` — the engine and tests will pick up the changes automatically.
- **Multi-character sessions**: Currently one character per session.
- **Mageburn tracking**: The rules mention cast limits per highest-tier discipline.
  This is not yet enforced by the engine (audit/warning only).
