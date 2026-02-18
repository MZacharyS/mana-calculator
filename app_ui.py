"""
Antarok Mana Calculator — Streamlit MVP
Run: streamlit run app_ui.py
"""
import sys
import os
import json
import csv
from io import StringIO

# Ensure the project root is on the path so src.* imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from src.engine.tiers import Tier, tier_from_name
from src.engine.calc_pool import compute_pool
from src.engine.calc_cast import compute_cast_cost, compute_cast_cost_with_quantity
from src.engine.calc_hybrid import compute_hybrid_cost
from src.engine.rounding import fmt_cost, fmt_pool
from src.config import (
    TIER_NAMES,
    TIER_NAMES_HIGH_FIRST,
    TIER_ORDER,
    EFFICIENCY_NAMES,
    TIER_VALUES,
    NOVICE_EFFICIENCY_COSTS,
    EFFICIENCY_BELOW_MULT,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Antarok Mana Calculator",
    page_icon="🔮",
    layout="wide",
)

# ── Session state bootstrap ────────────────────────────────────────────────────
def _init_state():
    if "character" not in st.session_state:
        st.session_state.character = {
            "name": "New Character",
            "highest_tier": "Master",
            "arcana": [],
        }
    if "ledger" not in st.session_state:
        st.session_state.ledger = []
    if "next_id" not in st.session_state:
        st.session_state.next_id = 1
    if "ledger_open" not in st.session_state:
        st.session_state.ledger_open = True

_init_state()

# ── Helpers ────────────────────────────────────────────────────────────────────
def _char() -> dict:
    return st.session_state.character

def _ledger() -> list:
    return st.session_state.ledger

def _highest_tier() -> Tier:
    return tier_from_name(_char()["highest_tier"])

def _arcana_list() -> list[dict]:
    """Return arcana with Tier enum objects for engine use."""
    result = []
    for a in _char()["arcana"]:
        result.append({"name": a["name"], "tier": tier_from_name(a["tier"])})
    return result

def _parse_cost(s: str) -> float:
    """Parse a cost string — handles both '22.0' floats and legacy '34/100' fractions."""
    if "/" in s:
        num, den = s.split("/")
        return int(num) / int(den)
    return float(s)

def _compute_pool() -> tuple[float, dict]:
    try:
        return compute_pool(_highest_tier(), _arcana_list())
    except ValueError:
        return 0.0, {}

def _pool_after_ledger() -> float:
    """Remaining pool after all ledger casts."""
    total, _ = _compute_pool()
    for entry in _ledger():
        total -= _parse_cost(entry["exact_cost"])
    return total

def _next_id() -> int:
    nid = st.session_state.next_id
    st.session_state.next_id += 1
    return nid

def _tier_names_for_character() -> list[str]:
    """Return tier names at or below the character's highest tier, high→low."""
    h = _highest_tier()
    return [t for t in TIER_NAMES_HIGH_FIRST if tier_from_name(t) <= h]

def _arcana_names() -> list[str]:
    return [a["name"] for a in _char()["arcana"]] or ["(no arcana)"]

def _add_ledger_entry(entry: dict):
    st.session_state.ledger.append(entry)

def _build_cast_entry(
    spell_name: str,
    arcana_name: str,
    spell_tier_str: str,
    efficiency: str,
    orders: int,
    quantity: int,
    quantity_mode: str,
    situational_str: str,
    is_hybrid: bool,
    hybrid_b: dict | None = None,
) -> dict:
    """Compute cost and build a ledger entry dict."""
    h = _highest_tier()
    spell_tier = tier_from_name(spell_tier_str)

    sit_mod = None
    if situational_str.strip():
        try:
            parts = situational_str.strip().split("/")
            if len(parts) == 2:
                sit_mod = int(parts[0]) / int(parts[1])
            else:
                sit_mod = float(parts[0])
        except Exception:
            sit_mod = None

    if is_hybrid and hybrid_b:
        spell_a_dict = {"tier": spell_tier, "efficiency": efficiency}
        spell_b_tier = tier_from_name(hybrid_b["tier"])
        spell_b_dict = {"tier": spell_b_tier, "efficiency": hybrid_b["efficiency"]}
        raw_cost = compute_hybrid_cost(
            h, spell_a_dict, spell_b_dict,
            orders=orders,
            situational_modifier=sit_mod,
        )
    else:
        raw_cost = compute_cast_cost_with_quantity(
            h, spell_tier, efficiency, orders,
            quantity=quantity,
            quantity_mode=quantity_mode,
            situational_modifier=sit_mod,
        )

    return {
        "id": _next_id(),
        "spell_name": spell_name,
        "arcana_name": arcana_name,
        "spell_tier": spell_tier_str,
        "efficiency": efficiency,
        "orders": orders,
        "quantity": quantity,
        "quantity_mode": quantity_mode,
        "situational": situational_str,
        "is_hybrid": is_hybrid,
        "hybrid_b_tier": hybrid_b["tier"] if hybrid_b else "",
        "hybrid_b_efficiency": hybrid_b["efficiency"] if hybrid_b else "",
        "exact_cost": str(raw_cost),
    }


# ── Sidebar — Character Editor ─────────────────────────────────────────────────
with st.sidebar:
    st.title("🔮 Mana Calculator")
    st.caption("Antarok RPG — Arcana System")
    st.divider()

    # Character basics
    st.subheader("Character")
    char_name = st.text_input(
        "Name", value=_char()["name"], key="char_name_input"
    )
    _char()["name"] = char_name

    highest_tier = st.selectbox(
        "Highest Tier",
        options=TIER_NAMES_HIGH_FIRST,
        index=TIER_NAMES_HIGH_FIRST.index(_char()["highest_tier"]),
        key="highest_tier_select",
    )
    _char()["highest_tier"] = highest_tier

    st.divider()

    # Arcana list
    st.subheader("Arcana")

    # Display current arcana with remove buttons
    arcana_to_remove = None
    for i, arc in enumerate(_char()["arcana"]):
        col_a, col_b, col_c = st.columns([3, 2, 1])
        with col_a:
            st.write(f"**{arc['name']}**")
        with col_b:
            st.write(arc["tier"])
        with col_c:
            if st.button("✕", key=f"rm_arc_{i}", help="Remove"):
                arcana_to_remove = i

    if arcana_to_remove is not None:
        _char()["arcana"].pop(arcana_to_remove)
        st.rerun()

    # Add arcana form
    with st.expander("+ Add Arcana", expanded=len(_char()["arcana"]) == 0):
        new_arc_name = st.text_input("Arcana Name", key="new_arc_name")
        # Only tiers at or below highest tier
        valid_tiers = [t for t in TIER_NAMES_HIGH_FIRST if tier_from_name(t) <= tier_from_name(highest_tier)]
        new_arc_tier = st.selectbox("Tier", valid_tiers, key="new_arc_tier")
        if st.button("Add Arcana", key="add_arc_btn"):
            if new_arc_name.strip():
                _char()["arcana"].append({"name": new_arc_name.strip(), "tier": new_arc_tier})
                st.rerun()
            else:
                st.warning("Arcana name cannot be empty.")

    # Load sample characters
    st.divider()
    st.subheader("Load Sample")
    col_kirin, col_serapis = st.columns(2)
    with col_kirin:
        if st.button("Kirin", width="stretch"):
            st.session_state.character = {
                "name": "Kirin",
                "highest_tier": "Master",
                "arcana": [
                    {"name": "Draoidh", "tier": "Master"},
                    {"name": "Zephyr",  "tier": "Master"},
                ],
            }
            st.session_state.ledger = []
            st.session_state.next_id = 1
            st.rerun()
    with col_serapis:
        if st.button("Serapis", width="stretch"):
            st.session_state.character = {
                "name": "Serapis",
                "highest_tier": "Master",
                "arcana": [
                    {"name": "Exodus", "tier": "Master"},
                    {"name": "Fathom", "tier": "Master"},
                    {"name": "Syphon", "tier": "Journeyman"},
                ],
            }
            st.session_state.ledger = []
            st.session_state.next_id = 1
            st.rerun()


# ── Main content ───────────────────────────────────────────────────────────────
# Compute pools once
pool_total, pool_breakdown = _compute_pool()
remaining = _pool_after_ledger()

st.title(f"🔮 {_char()['name'] or 'Unnamed'} — Mana Calculator")

# ── Layout: two columns when ledger open, full width when collapsed ─────────────
if st.session_state.ledger_open:
    col_main, col_ledger = st.columns([3, 2])
else:
    col_main = st.container()

# ============================================================
# LEFT COLUMN — Pool metrics + tabs
# ============================================================
with col_main:
    # Pool metrics row — includes "Show Ledger" button when panel is collapsed
    if st.session_state.ledger_open:
        c1, c2, c3 = st.columns(3)
    else:
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        with c4:
            st.write("")  # vertical nudge
            if st.button("📋 Ledger", help="Show cast ledger"):
                st.session_state.ledger_open = True
                st.rerun()
    c1.metric("Total Pool", fmt_pool(pool_total))
    c2.metric("Remaining", fmt_pool(remaining))
    c3.metric("Highest Tier", _char()["highest_tier"])

    st.divider()

    tab_pool, tab_cast, tab_export = st.tabs(["Pool", "Cast Spell", "Export"])

    # ============================================================
    # TAB 1: Pool
    # ============================================================
    with tab_pool:
        st.subheader("Mana Pool Breakdown")

        if not _char()["arcana"]:
            st.info("Add arcana in the sidebar to see your pool.")
        else:
            # Per-arcana breakdown
            rows = []
            for name, val in pool_breakdown.items():
                rows.append({
                    "Arcana": name,
                    "Tier": next(a["tier"] for a in _char()["arcana"] if a["name"] == name),
                    "Mana Value": fmt_pool(val),
                })
            st.table(rows)
            st.metric("Total Pool", fmt_pool(pool_total))

            st.divider()
            st.subheader("Tier Value Reference")
            st.caption(
                "Mana values from config. "
                "Standard = tier value. "
                "Non-Standard = multiplier × tier below (Novice uses fixed decimals)."
            )

            def _efficiency_cost(tier_name: str, efficiency: str) -> str:
                """Compute display cost directly from TIER_NAMES / TIER_VALUES."""
                if efficiency == "Standard":
                    return fmt_pool(TIER_VALUES[tier_name])
                if tier_name == "Novice":
                    return fmt_pool(NOVICE_EFFICIENCY_COSTS[efficiency])
                tier_below_name = TIER_ORDER[TIER_ORDER.index(tier_name) + 1]
                return fmt_pool(EFFICIENCY_BELOW_MULT[efficiency] * TIER_VALUES[tier_below_name])

            matrix_rows = []
            for tier_name in TIER_NAMES_HIGH_FIRST:          # Ascendant → Novice
                matrix_rows.append({
                    "Tier":        tier_name,
                    "Pool Value":  fmt_pool(TIER_VALUES[tier_name]),
                    "Standard":    _efficiency_cost(tier_name, "Standard"),
                    "Efficient":   _efficiency_cost(tier_name, "Efficient"),
                    "Optimal":     _efficiency_cost(tier_name, "Optimal"),
                    "Inefficient": _efficiency_cost(tier_name, "Inefficient"),
                    "Strenuous":   _efficiency_cost(tier_name, "Strenuous"),
                })
            st.table(matrix_rows)

    # ============================================================
    # TAB 2: Cast Spell
    # ============================================================
    with tab_cast:
        st.subheader("Add Cast to Ledger")

        with st.form("cast_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                spell_name = st.text_input("Spell Name *", placeholder="e.g. Wind Gust")
                arcana_choices = _arcana_names()
                arcana_name = st.selectbox("Arcana", arcana_choices)
                spell_tier = st.selectbox(
                    "Spell Tier", _tier_names_for_character()
                )
                efficiency = st.selectbox("Efficiency", EFFICIENCY_NAMES)

            with col2:
                orders = st.slider(
                    "Orders of Expression", 0, 6, 0,
                    help="Each order applies ~5% discount, max 30% at 6th order.",
                )
                quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
                qty_mode = st.radio(
                    "Quantity Rounding",
                    ["bundled", "per_cast"],
                    help=(
                        "**bundled**: multiply then ceil once (cheaper).\n\n"
                        "**per_cast**: ceil each cast, then sum."
                    ),
                )
                situational = st.text_input(
                    "Situational Modifier",
                    placeholder="e.g. 1/4 (grove bonus)",
                    help="Enter as fraction (e.g. 1/4) or integer multiplier.",
                )

            is_hybrid = st.checkbox(
                "Hybrid Spell (combine two spells)",
                help="Both spells must be the same tier. The Efficient modifier (×2/3) is applied to the combined cost.",
            )

            hybrid_b_tier = None
            hybrid_b_eff = None
            if is_hybrid:
                st.caption("— Second Spell (Spell B) —")
                hb_col1, hb_col2 = st.columns(2)
                with hb_col1:
                    hybrid_b_tier = st.selectbox(
                        "Spell B Tier", _tier_names_for_character(), key="hb_tier"
                    )
                with hb_col2:
                    hybrid_b_eff = st.selectbox(
                        "Spell B Efficiency", EFFICIENCY_NAMES, key="hb_eff"
                    )

            submitted = st.form_submit_button("⚡ Add to Ledger", type="primary")

            if submitted:
                if not spell_name.strip():
                    st.error("Spell name is required.")
                else:
                    hybrid_b = (
                        {"tier": hybrid_b_tier, "efficiency": hybrid_b_eff}
                        if is_hybrid and hybrid_b_tier
                        else None
                    )
                    try:
                        entry = _build_cast_entry(
                            spell_name=spell_name.strip(),
                            arcana_name=arcana_name if arcana_name != "(no arcana)" else "",
                            spell_tier_str=spell_tier,
                            efficiency=efficiency,
                            orders=orders,
                            quantity=quantity,
                            quantity_mode=qty_mode,
                            situational_str=situational,
                            is_hybrid=is_hybrid,
                            hybrid_b=hybrid_b,
                        )
                        _add_ledger_entry(entry)
                        st.success(
                            f"Added **{spell_name}** — cost: "
                            f"{fmt_cost(_parse_cost(entry['exact_cost']))}"
                        )
                        st.rerun()
                    except ValueError as e:
                        st.error(f"Error: {e}")

        # Live cost preview (outside form)
        st.divider()
        st.subheader("Cost Preview")
        st.caption("Fill in the form above and use this to preview before submitting.")
        with st.expander("Preview calculator", expanded=False):
            pv_tier = st.selectbox("Tier", _tier_names_for_character(), key="pv_tier")
            pv_eff = st.selectbox("Efficiency", EFFICIENCY_NAMES, key="pv_eff")
            pv_orders = st.slider("Orders", 0, 6, 0, key="pv_orders")
            pv_qty = st.number_input("Qty", 1, 100, 1, key="pv_qty")
            try:
                pv_cost = compute_cast_cost_with_quantity(
                    _highest_tier(), tier_from_name(pv_tier), pv_eff, pv_orders,
                    quantity=pv_qty, quantity_mode="bundled",
                )
                st.metric("Estimated Cost", fmt_cost(pv_cost))
                remaining_after = remaining - pv_cost
                st.metric("Remaining After Cast", fmt_pool(remaining_after))
            except ValueError as e:
                st.error(str(e))

    # ============================================================
    # TAB 3: Export / Import
    # ============================================================
    with tab_export:
        st.subheader("Export & Import")

        # ── Export ────────────────────────────────────────────────
        st.write("**Export ledger as JSON (audit-ready)**")

        export_data = {
            "character": _char(),
            "total_pool": str(pool_total),
            "remaining": str(_pool_after_ledger()),
            "ledger": _ledger(),
        }
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            "⬇ Download JSON",
            data=json_str,
            file_name=f"{_char()['name'].replace(' ', '_')}_mana_ledger.json",
            mime="application/json",
        )

        st.write("**Export ledger as CSV**")
        if _ledger():
            csv_buf = StringIO()
            fieldnames = [
                "id", "spell_name", "arcana_name", "spell_tier",
                "efficiency", "orders", "quantity", "quantity_mode",
                "situational", "is_hybrid", "hybrid_b_tier", "hybrid_b_efficiency",
                "exact_cost",
            ]
            writer = csv.DictWriter(csv_buf, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in _ledger():
                writer.writerow(row)
            st.download_button(
                "⬇ Download CSV",
                data=csv_buf.getvalue(),
                file_name=f"{_char()['name'].replace(' ', '_')}_mana_ledger.csv",
                mime="text/csv",
            )
        else:
            st.info("No ledger entries to export.")

        st.divider()

        # ── Import ────────────────────────────────────────────────
        st.write("**Import from JSON**")
        uploaded = st.file_uploader("Upload JSON file", type="json", key="import_upload")
        if uploaded:
            try:
                data = json.load(uploaded)
                if st.button("✅ Load imported data"):
                    if "character" in data:
                        st.session_state.character = data["character"]
                    if "ledger" in data:
                        st.session_state.ledger = data["ledger"]
                        st.session_state.next_id = (
                            max((e.get("id", 0) for e in data["ledger"]), default=0) + 1
                        )
                    st.success("Data loaded successfully.")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to parse JSON: {e}")


# ============================================================
# RIGHT COLUMN — Collapsible Cast Ledger
# ============================================================
if st.session_state.ledger_open:
    with col_ledger:
        with st.container(border=True):
            # Header row with close button
            hdr_col, close_col = st.columns([5, 1])
            with hdr_col:
                cast_count = len(_ledger())
                label = f"📋 Cast Ledger ({cast_count})" if cast_count else "📋 Cast Ledger"
                st.subheader(label)
            with close_col:
                st.write("")  # vertical nudge
                if st.button("✕", help="Collapse ledger", key="close_ledger"):
                    st.session_state.ledger_open = False
                    st.rerun()

            if not _ledger():
                st.caption("No casts recorded yet. Use **Cast Spell** to add entries.")
            else:
                # Build display rows with running total
                running = pool_total
                rows = []
                for entry in _ledger():
                    cost_val = _parse_cost(entry["exact_cost"])
                    running -= cost_val
                    rows.append({
                        "#":         entry["id"],
                        "Spell":     entry["spell_name"],
                        "Arcana":    entry["arcana_name"],
                        "Tier":      entry["spell_tier"],
                        "Eff.":      entry["efficiency"],
                        "Ord.":      entry["orders"],
                        "Qty":       entry["quantity"],
                        "Hybrid":    "✓" if entry.get("is_hybrid") else "",
                        "Cost":      fmt_cost(cost_val),
                        "Remaining": fmt_pool(running),
                    })
                st.dataframe(rows, width="stretch", hide_index=True)

            st.divider()

            # Ledger controls
            col_clear, col_undo = st.columns(2)
            with col_clear:
                if st.button("🗑 Clear All", type="secondary", width="stretch"):
                    st.session_state.ledger = []
                    st.session_state.next_id = 1
                    st.rerun()
            with col_undo:
                if st.button("↩ Undo Last", width="stretch", disabled=not bool(_ledger())):
                    if st.session_state.ledger:
                        st.session_state.ledger.pop()
                        st.rerun()
