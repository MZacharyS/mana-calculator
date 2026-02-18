# Antarok Mana Calculator

A mana pool and spell cost calculator for the **Antarok RPG** Arcana magic system.

Built for the Antarok forum community. Rules source: https://wiki.antarok.net/index.php/Arcana#Mana

---

## Quick Start (Local Dev)

```bash
# Create and activate a virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run app_ui.py

# Run tests
pytest tests/ -v
```

App runs at `http://localhost:8501`.

---

## Features

| Feature | Status |
|---|---|
| Mana pool from arcana list (absolute tier values) | ✅ |
| Single-spell cost: Standard, Efficient, Optimal, Inefficient, Strenuous | ✅ |
| Hybrid spell cost (costA + costB) × 2/3 | ✅ |
| Orders of Expression discount (5% per order, max 30%) | ✅ |
| Situational modifiers (before or after order discount) | ✅ |
| Quantity modes — bundled vs per-cast ceiling | ✅ |
| Audit ledger with spell name, arcana, tier, running balance | ✅ |
| Collapsible persistent ledger panel (visible across all tabs) | ✅ |
| JSON export (audit-ready) + CSV export | ✅ |
| JSON import / restore | ✅ |
| Sample characters — Kirin (200 pool), Serapis (211 pool) | ✅ |
| 91 unit tests — 100% passing | ✅ |

---

## Rules Engine

### Tier Values

Mana values are absolute integers, not relative fractions:

| Tier | Pool Value |
|---|---|
| Ascendant | 300 |
| Master | 100 |
| Expert | 33 |
| Journeyman | 11 |
| Apprentice | 4 |
| Novice | 1 |

A character's total mana pool is the sum of each arcana's tier value.

**Example — Kirin** (Master Draoidh + Master Zephyr): 100 + 100 = **200**
**Example — Serapis** (Master Exodus + Master Fathom + Journeyman Syphon): 100 + 100 + 11 = **211**

### Spell Cost

**Standard** spells cost the spell's own tier value.

**Non-Standard** spells cost a multiplier of the tier *one step below* the spell tier:

| Efficiency | Multiplier | Expert example (tier below = Journeyman = 11) |
|---|---|---|
| Efficient | 2× tier below | 22 |
| Optimal | 1× tier below | 11 |
| Inefficient | 4× tier below | 44 |
| Strenuous | 5× tier below | 55 |
| Standard | (tier value) | 33 |

Novice spells use fixed values: Standard=1.0, Efficient=0.66, Optimal=0.33, Inefficient=1.33, Strenuous=1.66

### Orders of Expression

Each order reduces cost by 5%, capped at 30% at the 6th order:

| Orders | Discount |
|---|---|
| 0 | 0% |
| 1 | 5% |
| 2 | 10% |
| 3 | 15% |
| 4 | 20% |
| 5 | 25% |
| 6 | 30% |

### Cost Pipeline (Order of Operations)

```
1. base_cost       = tier value (Standard) OR mult × tier_below value (non-Standard)
2. [situational]   = base_cost × modifier          ← "after_efficiency" position
3. after_orders    = base_cost × (1 − order_discount)
4. [situational]   = after_orders × modifier        ← "after_expression" position
5. total           = after_orders × quantity         (bundled mode)
                   = ceil(after_orders) × quantity   (per_cast mode)
6. final           = ceiling(total, 0.01)
```

### Hybrid Spells

```
combined = get_base_cost(spell_A) + get_base_cost(spell_B)
hybrid   = combined × (2/3)
         → apply Orders of Expression discount
         → apply ceiling to 2 decimal places
```

---

## Project Structure

```
mana-calculator/
├── app_ui.py               # Streamlit UI — sidebar, tabs, ledger panel
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── STATUS.md               # Deployment status, ops commands, backlog
├── src/
│   ├── config.py           # Source of truth: TIER_VALUES, EFFICIENCY_BELOW_MULT,
│   │                       #   NOVICE_EFFICIENCY_COSTS, ORDERS_OF_EXPRESSION
│   └── engine/
│       ├── tiers.py        # Tier IntEnum, tier_from_name(), tier_value(), tier_below()
│       ├── calc_pool.py    # compute_pool() → (total, breakdown)
│       ├── calc_cast.py    # get_spell_base_cost(), compute_cast_cost(),
│       │                   #   compute_cast_cost_with_quantity()
│       ├── calc_hybrid.py  # compute_hybrid_cost()
│       ├── rounding.py     # fmt_cost(), fmt_pool(), ceiling helpers
│       └── spreadsheet_mode.py  # Legacy reference path (not exposed in UI)
├── tests/
│   ├── conftest.py
│   ├── test_tiers.py
│   ├── test_pool.py
│   ├── test_cast.py
│   ├── test_hybrid.py
│   └── test_spreadsheet.py
├── sample_data/
│   ├── kirin.json          # Kirin — Master Draoidh + Master Zephyr (pool: 200)
│   └── serapis.json        # Serapis — 2× Master + Journeyman Syphon (pool: 211)
└── data/
    └── ManaFormula.xlsx    # Original reference spreadsheet
```

---

## Configuration

All tunable values live in `src/config.py`. Changing a value there automatically propagates through the engine and tests — no other files need editing.

Key constants:
- `TIER_VALUES` — absolute integer value per tier name
- `TIER_ORDER` — canonical tier ordering high → low
- `EFFICIENCY_BELOW_MULT` — multipliers for non-Standard efficiencies
- `NOVICE_EFFICIENCY_COSTS` — fixed cost overrides for Novice tier
- `ORDERS_OF_EXPRESSION` — discount fractions keyed by order number (0–6)

---

## Pending / Future Work

- **Macro system** — Removed from UI; planned as a dedicated module with persistent storage. Will expand a single macro entry (e.g. "Apparating") into multiple ledger entries automatically.
- **Character persistence** — Session state resets on page refresh. Planned: save/load character JSON per user.
- **Mageburn tracking** — Cast limits per highest-tier discipline exist in the rules but are not yet enforced by the engine.
- **Multi-character / party view** — Useful for GMs running multiple characters simultaneously.
