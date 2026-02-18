# Antarok Mana Calculator — Project Status

**Project:** Antarok RPG Mana Calculator
**Client/Context:** Antarok forum — custom mana tracking tool for the Arcana magic system
**Last Updated:** 2026-02-18
**Status:** Deployed ✅

---

## Overview

A Streamlit web app that lets Antarok RPG players calculate mana pool totals, log spell casts, and track remaining mana with a full audit ledger. Built to match the rules defined on the Antarok wiki and the existing ManaFormula.xlsx spreadsheet.

---

## Current Feature Set

### Engine (`src/engine/`)
- **Mana Pool** — Sum of absolute tier values per arcana (Ascendant=300, Master=100, Expert=33, Journeyman=11, Apprentice=4, Novice=1)
- **Spell Cast Cost** — Standard = tier value; non-Standard = multiplier × tier below
  - Efficient = 2×, Optimal = 1×, Inefficient = 4×, Strenuous = 5× (relative to tier below)
  - Novice fixed costs: Standard=1.0, Efficient=0.66, Optimal=0.33, Inefficient=1.33, Strenuous=1.66
- **Orders of Expression** — 5% discount per order, capped at 30% at 6th order
- **Hybrid Spells** — (costA + costB) × 2/3, orders applied after combination
- **Situational Modifiers** — Multiplier applied before or after order discount (e.g. 1/4 for grove bonus)
- **Quantity modes** — `bundled` (multiply then ceil once) or `per_cast` (ceil each then sum)
- **Rounding** — Ceiling to 2 decimal places at final display step

### UI (`app_ui.py`)
- **Sidebar character editor** — name, highest tier, arcana list with add/remove; Kirin and Serapis sample loaders
- **Two-column layout** — Main tabs on left, collapsible cast ledger panel on right
- **Pool tab** — Per-arcana breakdown table + full tier/efficiency reference matrix
- **Cast Spell tab** — Form with spell name, arcana, tier, efficiency, orders, quantity, quantity mode, situational modifier, hybrid spell support; live cost preview expander
- **Export tab** — JSON and CSV download; JSON import/restore
- **Persistent ledger** — Always visible in right column regardless of active tab; running balance, cast count in header, Clear All + Undo Last controls; collapsible with ✕ / 📋 Ledger toggle

### Tests (`tests/`)
- 91 tests, 100% passing
- Coverage: pool computation, cast cost pipeline (all tiers × all efficiencies), hybrid cost, rounding/formatting, tiers enum, spreadsheet mode compatibility

---

## Deployment

- **Host:** ranseras1 (`192.168.12.65`)
- **Deploy path:** `~/antarok-mana-calculator/`
- **URL:** `https://test.lairallc.com`
- **Stack:** Docker Compose — two containers on a shared bridge network

| Container | Image | Role |
|---|---|---|
| `antarok-mana-app` | Built from `Dockerfile` (python:3.11-slim) | Streamlit app on internal port 8501 |
| `antarok-cloudflared` | `cloudflare/cloudflared:latest` | Tunnel to Cloudflare edge; routes `test.lairallc.com → app:8501` |

- **Tunnel ID:** `2f8e5f6f-2cba-49dc-8521-63d70609706c` (tunnel name: `antarok-mana`)
- **Credentials:** `~/.cloudflared/2f8e5f6f-2cba-49dc-8521-63d70609706c.json` on ranseras1
- **Cloudflared config:** `~/.cloudflared/antarok-config.yml` on ranseras1
- **DNS:** CNAME `test` → `2f8e5f6f-2cba-49dc-8521-63d70609706c.cfargotunnel.com` in `lairallc.com` zone (Cloudflare dashboard — must be set manually; lairallc.com is not in the same CF account as the server cert)

### Redeploy after code changes

```bash
# From the local project directory
rsync -av --exclude='env/' --exclude='__pycache__/' --exclude='.git/' --exclude='tests/' \
  /home/mzsmith/Desktop/LAIRA/Projects/Antarok/mana-calculator/ \
  mzsmith@192.168.12.65:~/antarok-mana-calculator/

ssh mzsmith@192.168.12.65 \
  "cd ~/antarok-mana-calculator && docker compose build app && docker compose up -d"
```

### Container management

```bash
# SSH into ranseras1 first
ssh mzsmith@192.168.12.65

# View status
cd ~/antarok-mana-calculator && docker compose ps

# View logs
docker logs antarok-mana-app
docker logs antarok-cloudflared

# Restart everything
docker compose restart

# Stop everything
docker compose down

# Stop and remove images
docker compose down --rmi local
```

---

## Architecture

```
src/
├── config.py              # Single source of truth: TIER_VALUES, EFFICIENCY_BELOW_MULT,
│                          #   NOVICE_EFFICIENCY_COSTS, ORDERS_OF_EXPRESSION, TIER_ORDER
└── engine/
    ├── tiers.py           # Tier IntEnum, tier_from_name(), tier_value(), tier_below()
    ├── calc_pool.py       # compute_pool() → (total: float, breakdown: dict)
    ├── calc_cast.py       # get_spell_base_cost(), compute_cast_cost(),
    │                      #   compute_cast_cost_with_quantity()
    ├── calc_hybrid.py     # compute_hybrid_cost()
    ├── rounding.py        # fmt_cost(), fmt_pool(), ceil helpers (Fraction + float)
    └── spreadsheet_mode.py  # Legacy spreadsheet-compatible calculation path (kept for
                             #   reference; UI uses primary float engine)
app_ui.py                  # Streamlit UI — all tabs, sidebar, session state
```

---

## Known Issues / Notes

- **Strenuous efficiency** description on wiki is ambiguous; current implementation uses 5× tier below (matches spreadsheet)
- **Spreadsheet mode** (`spreadsheet_mode.py`) is kept for reference but is not exposed in the UI; primary engine and spreadsheet mode now produce identical results
- **UDP buffer size warning** from cloudflared in container logs (`wanted 7168 kiB, got 416 kiB`) — cosmetic only; tunnel connections establish successfully

---

## Pending / Future Work

| Item | Priority | Notes |
|---|---|---|
| **Macro system** | Medium | Removed from UI to reduce scope. Needs dedicated module + persistent storage (SQLite or external DB). Should expand multiple ledger entries from a single "cast" (e.g. Apparating = Frequency Up + Frequency Down). |
| **Character persistence** | Low | Session state resets on page refresh. Could store character JSON to a file or DB per user. |
| **Multi-character / party view** | Low | Useful for GMs tracking multiple characters at once. |
| **lairallc.com Cloudflare consolidation** | Low | Currently lairallc.com DNS is managed separately from the server's CF account. Consolidating would allow `cloudflared tunnel route dns` to work without manual dashboard steps. |
