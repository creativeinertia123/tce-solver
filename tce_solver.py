#!/usr/bin/env python3
"""
TCE Economics Solver - Streamlit Edition
航次租金测算器 - Streamlit版本

A standalone Streamlit application that implements the full TCE calculation chain
with dual-input caching (active value + cached fallback) for every parameter.

Run with: streamlit run tce_solver.py
"""

import streamlit as st
import pandas as pd

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="TCE Economics Solver",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Calibri', sans-serif !important; color: #000000 !important; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    .stMetric { background: #ffffff; border: 1px solid #000000; border-radius: 0px; padding: 10px; }
    .stMetric label { color: #000000 !important; font-size: 12px !important; font-weight: bold !important; }
    .stMetric .metric-value { color: #000000 !important; font-family: 'Calibri', sans-serif !important; font-size: 14px !important; }
    div[data-testid="stTextInput"] label, div[data-testid="stNumberInput"] label { color: #000000 !important; font-size: 12px !important; font-weight: bold !important; }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input { 
        background: #ffffff !important; 
        color: #000000 !important; 
        border: 1px solid #000000 !important;
        font-family: 'Calibri', sans-serif !important;
        border-radius: 0px !important;
    }
    .cached-row {
        background: #f5f5f5;
        border-left: 2px solid #000000;
        padding: 4px 12px;
        margin-top: 2px;
        font-family: 'Calibri', sans-serif;
        font-size: 11px;
        color: #555555;
    }
    .result-card {
        background: #ffffff;
        border-left: 2px solid #000000;
        padding: 10px 14px;
        margin: 6px 0;
    }
    .result-underline {
        text-decoration: underline;
        text-decoration-thickness: 2px;
    }
    .formula-pill {
        display: inline-block;
        background: #ffffff;
        border: 1px solid #000000;
        padding: 2px 10px;
        font-size: 10px;
        color: #000000;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-family: 'Calibri', sans-serif;
    }
    .segment-header {
        font-family: 'Calibri', sans-serif;
        font-size: 16px;
        font-weight: bold;
        color: #000000;
        margin-bottom: 2px;
    }
    .segment-sub {
        font-size: 11px;
        color: #555555;
        margin-bottom: 10px;
    }
    hr.segment-divider {
        border: none;
        border-top: 2px solid #000000;
        margin: 16px 0;
    }
    hr.formula-connector {
        border: none;
        border-top: 1px solid #cccccc;
        margin: 8px 0;
        text-align: center;
        overflow: visible;
    }
    hr.formula-connector::after {
        content: attr(data-formula);
        display: inline-block;
        position: relative;
        top: -10px;
        background: #ffffff;
        border: 1px solid #000000;
        padding: 2px 10px;
        font-size: 10px;
        color: #000000;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-family: 'Calibri', sans-serif;
    }
    div[data-testid="stContainer"] { border-color: #000000 !important; }
    .default-badge {
        color: #00008B;
        font-weight: bold;
        font-size: 11px;
        margin-top: -6px;
        margin-bottom: 4px;
        font-family: 'Calibri', sans-serif;
    }
    .default-value-text {
        color: #0000FF;
        text-decoration: underline;
        font-family: 'Calibri', sans-serif;
    }
    .rec-box {
        background: #ffffff;
        border: 2px solid #000000;
        padding: 16px;
        margin-bottom: 16px;
    }
    .rec-title {
        font-family: 'Calibri', sans-serif;
        font-size: 14px;
        font-weight: bold;
        color: #000000;
        margin-bottom: 8px;
    }
    .rec-item {
        font-family: 'Calibri', sans-serif;
        font-size: 11px;
        color: #555555;
        margin-bottom: 2px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
def init_session():
    """Initialize all dual-value fields in session state if not present."""
    defaults = {
        # Segment 1: Ship & Voyage (dual: active_label, active_value, cached_label, cached_value)
        "speed_active_label": "", "speed_active_value": 0.0, "speed_cached_label": "", "speed_cached_value": 0.0,
        "bl_speed_active_label": "", "bl_speed_active_value": 0.0, "bl_speed_cached_label": "", "bl_speed_cached_value": 0.0,
        "ld_speed_active_label": "", "ld_speed_active_value": 0.0, "ld_speed_cached_label": "", "ld_speed_cached_value": 0.0,
        "ballast_port_active_label": "", "ballast_port_active_value": "", "ballast_port_cached_label": "", "ballast_port_cached_value": "",
        "load_port_active_label": "", "load_port_active_value": "", "load_port_cached_label": "", "load_port_cached_value": "",
        "disch_port_active_label": "", "disch_port_active_value": "", "disch_port_cached_label": "", "disch_port_cached_value": "",
        "bl_distance_active_label": "", "bl_distance_active_value": 0.0, "bl_distance_cached_label": "", "bl_distance_cached_value": 0.0,
        "ld_distance_active_label": "", "ld_distance_active_value": 0.0, "ld_distance_cached_label": "", "ld_distance_cached_value": 0.0,
        "load_rate_active_label": "", "load_rate_active_value": 0.0, "load_rate_cached_label": "", "load_rate_cached_value": 0.0,
        "disch_rate_active_label": "", "disch_rate_active_value": 0.0, "disch_rate_cached_label": "", "disch_rate_cached_value": 0.0,
        "qty_mt_active_label": "", "qty_mt_active_value": 0.0, "qty_mt_cached_label": "", "qty_mt_cached_value": 0.0,

        # Segment 2: Fuel Consumption Specs
        "b_vlsfo_active_label": "", "b_vlsfo_active_value": 0.0, "b_vlsfo_cached_label": "", "b_vlsfo_cached_value": 0.0,
        "b_mgo_active_label": "", "b_mgo_active_value": 0.0, "b_mgo_cached_label": "", "b_mgo_cached_value": 0.0,
        "l_vlsfo_active_label": "", "l_vlsfo_active_value": 0.0, "l_vlsfo_cached_label": "", "l_vlsfo_cached_value": 0.0,
        "l_mgo_active_label": "", "l_mgo_active_value": 0.0, "l_mgo_cached_label": "", "l_mgo_cached_value": 0.0,
        "idle_vlsfo_active_label": "", "idle_vlsfo_active_value": 0.0, "idle_vlsfo_cached_label": "", "idle_vlsfo_cached_value": 0.0,
        "idle_mgo_active_label": "", "idle_mgo_active_value": 0.0, "idle_mgo_cached_label": "", "idle_mgo_cached_value": 0.0,
        "work_vlsfo_active_label": "", "work_vlsfo_active_value": 0.0, "work_vlsfo_cached_label": "", "work_vlsfo_cached_value": 0.0,
        "work_mgo_active_label": "", "work_mgo_active_value": 0.0, "work_mgo_cached_label": "", "work_mgo_cached_value": 0.0,

        # Segment 4: Fuel Prices
        "vlsfo_price_active_label": "", "vlsfo_price_active_value": 0.0, "vlsfo_price_cached_label": "", "vlsfo_price_cached_value": 0.0,
        "mgo_price_active_label": "", "mgo_price_active_value": 0.0, "mgo_price_cached_label": "", "mgo_price_cached_value": 0.0,

        # Segment 5: Freight
        "freight_rate_active_label": "", "freight_rate_active_value": 0.0, "freight_rate_cached_label": "", "freight_rate_cached_value": 0.0,
        "commission_active_label": "", "commission_active_value": 0.0, "commission_cached_label": "", "commission_cached_value": 0.0,

        # Segment 6: Port Charges
        "load_port_fee_active_label": "", "load_port_fee_active_value": 0.0, "load_port_fee_cached_label": "", "load_port_fee_cached_value": 0.0,
        "disch_port_fee_active_label": "", "disch_port_fee_active_value": 0.0, "disch_port_fee_cached_label": "", "disch_port_fee_cached_value": 0.0,

        # Segment 6b: Other Expenses
        "misc_expense_active_label": "", "misc_expense_active_value": 0.0, "misc_expense_cached_label": "", "misc_expense_cached_value": 0.0,
        "oil_expense_active_label": "", "oil_expense_active_value": 0.0, "oil_expense_cached_label": "", "oil_expense_cached_value": 0.0,

        # Segment 3: Time overrides
        "true_time_active_label": "", "true_time_active_value": 0.0, "true_time_cached_label": "", "true_time_cached_value": 0.0,
        "bl_time_override": None,
        "ld_time_override": None,
        "load_time_override": None,
        "disch_time_override": None,

        # Reverse mode target
        "target_day_rate_active_label": "", "target_day_rate_active_value": 0.0, "target_day_rate_cached_label": "", "target_day_rate_cached_value": 0.0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session()


# ============================================================
# APPLY DEFAULTS
# ============================================================
def apply_all_defaults():
    """Apply all recommended default values (no fixed ship)."""
    defaults_map = {
        # Segment 1
        "speed": (12.0, "default"),
        "bl_speed": (12.0, "default"),
        "ld_speed": (11.5, "default"),
        "ballast_port": ("South China", "default"),
        "load_port": ("Samarinda", "default"),
        "disch_port": ("Guangzhou", "default"),
        "bl_distance": (1850.0, "default"),
        "ld_distance": (1680.0, "default"),
        "load_rate": (27000.0, "default"),
        "disch_rate": (13500.0, "default"),
        "qty_mt": (68000.0, "default"),
        # Segment 2
        "b_vlsfo": (23.0, "default"),
        "b_mgo": (0.15, "default"),
        "l_vlsfo": (25.0, "default"),
        "l_mgo": (0.15, "default"),
        "idle_vlsfo": (0.5, "default"),
        "idle_mgo": (0.05, "default"),
        "work_vlsfo": (4.0, "default"),
        "work_mgo": (0.2, "default"),
        # Segment 4
        "vlsfo_price": (780.0, "default"),
        "mgo_price": (1550.0, "default"),
        # Segment 5
        "freight_rate": (10.2, "default"),
        "commission": (0.025, "default"),
        # Segment 6
        "load_port_fee": (45000.0, "default"),
        "disch_port_fee": (36000.0, "default"),
        # Segment 6b
        "misc_expense": (4000.0, "default"),
        "oil_expense": (2000.0, "default"),
        # Segment 3
        "true_time": (1.5, "default"),
        # Reverse
        "target_day_rate": (19000.0, "default"),
    }
    for key, (val, label) in defaults_map.items():
        active_val_key = f"{key}_active_value"
        active_label_key = f"{key}_active_label"
        cached_val_key = f"{key}_cached_value"
        cached_label_key = f"{key}_cached_label"
        # Push current active to cached
        st.session_state[cached_val_key] = st.session_state[active_val_key]
        st.session_state[cached_label_key] = st.session_state[active_label_key]
        # Set default as active
        st.session_state[active_val_key] = val
        st.session_state[active_label_key] = label


# ============================================================
# DUAL-INPUT WIDGET
# ============================================================
def dual_input_cell(key_prefix: str, label: str, unit: str = "", step: float = 0.01,
                    presets: list = None, is_text: bool = False):
    """
    Renders a dual-input cell: active input on top, cached fallback below with swap button.
    
    Args:
        key_prefix: unique prefix for session_state keys (e.g., "speed")
        label: field label shown to user
        unit: unit suffix (e.g., "knots", "USD/mt")
        step: number step for spinner
        presets: list of {label, value} dicts for quick selection
        is_text: if True, uses text_input; otherwise number_input
    """
    active_val_key = f"{key_prefix}_active_value"
    active_label_key = f"{key_prefix}_active_label"
    cached_val_key = f"{key_prefix}_cached_value"
    cached_label_key = f"{key_prefix}_cached_label"

    col1, col2 = st.columns([4, 1])

    with col1:
        # Active input
        if is_text:
            new_val = st.text_input(
                label,
                value=st.session_state[active_val_key],
                key=f"{key_prefix}_input",
                label_visibility="visible",
            )
        else:
            new_val = st.number_input(
                f"{label} {unit}",
                value=float(st.session_state[active_val_key]),
                step=step,
                key=f"{key_prefix}_input",
                label_visibility="visible",
                format="%.4f" if step < 1 else "%.0f",
            )

        # Update active value if changed
        if new_val != st.session_state[active_val_key]:
            st.session_state[active_val_key] = new_val
            st.session_state[active_label_key] = "Custom"
            st.rerun()

        # Default badge for active value
        if str(st.session_state.get(active_label_key, "")).lower() == "default":
            st.markdown('<div class="default-badge">DEFAULT</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↔ Swap", key=f"{key_prefix}_swap", use_container_width=True):
            # Swap active and cached
            old_active_val = st.session_state[active_val_key]
            old_active_label = st.session_state[active_label_key]
            st.session_state[active_val_key] = st.session_state[cached_val_key]
            st.session_state[active_label_key] = st.session_state[cached_label_key]
            st.session_state[cached_val_key] = old_active_val
            st.session_state[cached_label_key] = old_active_label
            st.rerun()

    # Cached fallback display
    cached_val = st.session_state[cached_val_key]
    cached_label = st.session_state[cached_label_key] or "—"
    display_val = cached_val if cached_val != 0 and cached_val != "" else "—"
    if str(cached_label).lower() == "default":
        st.markdown(
            f'<div class="cached-row"><span style="color:#00008B;font-weight:bold;">DEFAULT</span> <span class="default-value-text">{display_val}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="cached-row">({cached_label}, {display_val})</div>',
            unsafe_allow_html=True,
        )

    # Preset buttons
    if presets:
        preset_cols = st.columns(min(len(presets), 4))
        for i, preset in enumerate(presets):
            with preset_cols[i % 4]:
                if st.button(f"{preset['label']}: {preset['value']}", key=f"{key_prefix}_preset_{i}", use_container_width=True):
                    # Push current active to cached
                    st.session_state[cached_val_key] = st.session_state[active_val_key]
                    st.session_state[cached_label_key] = st.session_state[active_label_key]
                    # Set preset as active
                    st.session_state[active_val_key] = preset["value"]
                    st.session_state[active_label_key] = preset["label"]
                    st.rerun()

    return st.session_state[active_val_key]


# ============================================================
# CALCULATION ENGINE
# ============================================================
def compute_all():
    """Run the full TCE calculation chain from session state."""
    s = st.session_state

    # Segment 1
    speed = float(s["speed_active_value"]) if s["speed_active_value"] else 0.0
    bl_speed = float(s["bl_speed_active_value"]) if s["bl_speed_active_value"] else speed
    ld_speed = float(s["ld_speed_active_value"]) if s["ld_speed_active_value"] else speed
    bl_distance = float(s["bl_distance_active_value"]) if s["bl_distance_active_value"] else 0.0
    ld_distance = float(s["ld_distance_active_value"]) if s["ld_distance_active_value"] else 0.0
    load_rate = float(s["load_rate_active_value"]) if s["load_rate_active_value"] else 0.0
    disch_rate = float(s["disch_rate_active_value"]) if s["disch_rate_active_value"] else 0.0
    qty_mt = float(s["qty_mt_active_value"]) if s["qty_mt_active_value"] else 0.0

    # Segment 2
    b_vlsfo = float(s["b_vlsfo_active_value"]) if s["b_vlsfo_active_value"] else 0.0
    b_mgo = float(s["b_mgo_active_value"]) if s["b_mgo_active_value"] else 0.0
    l_vlsfo = float(s["l_vlsfo_active_value"]) if s["l_vlsfo_active_value"] else 0.0
    l_mgo = float(s["l_mgo_active_value"]) if s["l_mgo_active_value"] else 0.0
    idle_vlsfo = float(s["idle_vlsfo_active_value"]) if s["idle_vlsfo_active_value"] else 0.0
    idle_mgo = float(s["idle_mgo_active_value"]) if s["idle_mgo_active_value"] else 0.0
    work_vlsfo = float(s["work_vlsfo_active_value"]) if s["work_vlsfo_active_value"] else 0.0
    work_mgo = float(s["work_mgo_active_value"]) if s["work_mgo_active_value"] else 0.0

    # Segment 4 prices
    vlsfo_price = float(s["vlsfo_price_active_value"]) if s["vlsfo_price_active_value"] else 0.0
    mgo_price = float(s["mgo_price_active_value"]) if s["mgo_price_active_value"] else 0.0

    # Segment 5 freight
    freight_rate = float(s["freight_rate_active_value"]) if s["freight_rate_active_value"] else 0.0
    commission = float(s["commission_active_value"]) if s["commission_active_value"] else 0.0

    # Segment 6 port charges
    load_port_fee = float(s["load_port_fee_active_value"]) if s["load_port_fee_active_value"] else 0.0
    disch_port_fee = float(s["disch_port_fee_active_value"]) if s["disch_port_fee_active_value"] else 0.0

    # Segment 6b other expenses
    misc_expense = float(s["misc_expense_active_value"]) if s["misc_expense_active_value"] else 0.0
    oil_expense = float(s["oil_expense_active_value"]) if s["oil_expense_active_value"] else 0.0

    # Segment 3 time
    safe_bl_speed = bl_speed if bl_speed > 0 else 1.0
    safe_ld_speed = ld_speed if ld_speed > 0 else 1.0
    safe_load_rate = load_rate if load_rate > 0 else 1.0
    safe_disch_rate = disch_rate if disch_rate > 0 else 1.0

    bl_time = s["bl_time_override"] if s["bl_time_override"] is not None else bl_distance / safe_bl_speed / 24.0
    ld_time = s["ld_time_override"] if s["ld_time_override"] is not None else ld_distance / safe_ld_speed / 24.0
    load_time = s["load_time_override"] if s["load_time_override"] is not None else qty_mt / safe_load_rate
    disch_time = s["disch_time_override"] if s["disch_time_override"] is not None else qty_mt / safe_disch_rate
    true_time = float(s["true_time_active_value"]) if s["true_time_active_value"] else 0.0
    total_time = bl_time + ld_time + load_time + disch_time + true_time

    # Fuel consumption per segment
    bl_vlsfo = b_vlsfo * bl_time
    bl_mgo = b_mgo * bl_time
    ld_vlsfo = l_vlsfo * ld_time
    ld_mgo = l_mgo * ld_time
    load_vlsfo = work_vlsfo * load_time
    load_mgo = work_mgo * load_time
    dis_vlsfo = work_vlsfo * disch_time
    dis_mgo = work_mgo * disch_time
    true_vlsfo = idle_vlsfo * true_time
    true_mgo = idle_mgo * true_time

    # Fuel totals
    total_vlsfo = bl_vlsfo + ld_vlsfo + load_vlsfo + dis_vlsfo + true_vlsfo
    total_mgo = bl_mgo + ld_mgo + load_mgo + dis_mgo + true_mgo
    vlsfo_cost = total_vlsfo * vlsfo_price
    mgo_cost = total_mgo * mgo_price
    total_fuel_cost = vlsfo_cost + mgo_cost

    # Freight
    total_freight = qty_mt * freight_rate * (1.0 - commission)

    # Port charges
    total_port_charges = load_port_fee + disch_port_fee

    # TCE
    tce_revenue = total_freight - total_fuel_cost - total_port_charges
    tce_day_rate = tce_revenue / total_time if total_time > 0 else 0.0

    # Reverse: required freight for target day rate
    target_day_rate = float(s["target_day_rate_active_value"]) if s["target_day_rate_active_value"] else 0.0
    required_total_freight = target_day_rate * total_time + total_fuel_cost + total_port_charges
    safe_qty = qty_mt if qty_mt > 0 else 1.0
    safe_comm = (1.0 - commission) if (1.0 - commission) > 0 else 0.001
    required_freight_rate = required_total_freight / (safe_qty * safe_comm)

    # Cost-plus freight rate (算运费): (油 + 港费 + 租船 + 其他费用) / 货量
    total_oil_cost = total_fuel_cost + oil_expense
    charter_cost = target_day_rate * total_time
    total_other_cost = total_oil_cost + total_port_charges + charter_cost + misc_expense
    cost_plus_freight_rate = total_other_cost / safe_qty

    return {
        "bl_time": bl_time, "ld_time": ld_time, "load_time": load_time,
        "disch_time": disch_time, "true_time": true_time, "total_time": total_time,
        "bl_vlsfo": bl_vlsfo, "bl_mgo": bl_mgo, "ld_vlsfo": ld_vlsfo, "ld_mgo": ld_mgo,
        "load_vlsfo": load_vlsfo, "load_mgo": load_mgo, "dis_vlsfo": dis_vlsfo, "dis_mgo": dis_mgo,
        "true_vlsfo": true_vlsfo, "true_mgo": true_mgo,
        "total_vlsfo": total_vlsfo, "total_mgo": total_mgo,
        "vlsfo_cost": vlsfo_cost, "mgo_cost": mgo_cost, "total_fuel_cost": total_fuel_cost,
        "total_freight": total_freight, "total_port_charges": total_port_charges,
        "tce_revenue": tce_revenue, "tce_day_rate": tce_day_rate,
        "target_day_rate": target_day_rate,
        "required_freight_rate": required_freight_rate,
        "required_total_freight": required_total_freight,
        "misc_expense": misc_expense,
        "oil_expense": oil_expense,
        "total_oil_cost": total_oil_cost,
        "charter_cost": charter_cost,
        "total_other_cost": total_other_cost,
        "cost_plus_freight_rate": cost_plus_freight_rate,
    }


# ============================================================
# UI HELPERS
# ============================================================
def formula_connector(formula: str):
    st.markdown(f'<hr class="formula-connector" data-formula="{formula}">', unsafe_allow_html=True)


def result_block(label: str, value: float, prefix: str = "$", suffix: str = "", decimals: int = 2, is_result: bool = False):
    fmt = f"{prefix}{value:,.{decimals}f}{suffix}" if value != 0 else f"{prefix}—{suffix}"
    value_style = "text-decoration: underline; text-decoration-thickness: 2px; font-weight: bold;" if is_result else "font-weight: bold;"
    st.markdown(f"""
    <div class="result-card">
        <div style="font-size: 11px; color: #555555; margin-bottom: 4px;">{label}</div>
        <div style="font-size: 16px; color: #000000; font-family: 'Calibri', sans-serif; {value_style}">{fmt}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str):
    st.markdown(f"""
    <div style="margin-bottom: 12px;">
        <div class="segment-header">{title}</div>
        <div class="segment-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# MAIN APP
# ============================================================
def main():
    # Header
    st.markdown("""
    <div style="margin-bottom: 24px; border-bottom: 2px solid #000000; padding-bottom: 12px;">
        <div style="font-size: 12px; color: #555555; font-family: 'Calibri', sans-serif; margin-top: 4px;">TCE Solver</div>
        <div style="font-size: 12px; color: #555555; font-family: 'Calibri', sans-serif; margin-top: 4px;">TCE Solver</div>
    </div>
    """, unsafe_allow_html=True)

    c = compute_all()

    # ============================================================
    # RECOMMENDED VALUES SECTION
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("推荐参数 Recommended Values", "No fixed ship — apply all defaults with one click")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Apply Defaults", use_container_width=True, type="primary"):
                apply_all_defaults()
                st.rerun()
        with col2:
            st.markdown("""
            <div class="rec-box">
                <div class="rec-title">Default Parameters 默认参数</div>
                <div style="display: flex; flex-wrap: wrap; gap: 16px;">
                    <div class="rec-item">• 空放航速 BL Speed: <b>12 knots</b></div>
                    <div class="rec-item">• 载货航速 LD Speed: <b>11.5 knots</b></div>
                    <div class="rec-item">• 空放油耗 VLSFO: <b>23 mt/day</b></div>
                    <div class="rec-item">• 载货油耗 VLSFO: <b>25 mt/day</b></div>
                    <div class="rec-item">• 作业油耗 VLSFO: <b>4.0 mt/day</b></div>
                    <div class="rec-item">• 压港等待 True Time: <b>1.5 days</b></div>
                    <div class="rec-item">• 载货航速 shave-off: <b>speed − 0.5 knots</b> (load-dispatch default)</div>
                    <div class="rec-item">• 空放港口: <b>South China</b></div>
                    <div class="rec-item">• 日租金 TC: <b>19,000 USD/day</b></div>
                    <div class="rec-item">• 杂费 Misc: <b>4,000 USD</b></div>
                    <div class="rec-item">• 油杂 Oil Misc: <b>2,000 USD</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ============================================================
    # SEGMENT 1: Ship & Voyage Config
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("船货参数 Ship & Voyage Config", "Vessel speed, ports, distances, cargo quantity")
        col1, col2 = st.columns(2)
        with col1:
            dual_input_cell("speed", "船速 Speed", "knots", step=0.1,
                           presets=[{"label": "ECO", "value": 12.0}, {"label": "Full", "value": 13.0}])
            dual_input_cell("bl_speed", "空放航速 BL Speed", "knots", step=0.1,
                           presets=[{"label": "default", "value": 12.0}, {"label": "ECO", "value": 12.0}])
            dual_input_cell("ballast_port", "空放港口 Ballast Port", is_text=True,
                           presets=[{"label": "Qingdao", "value": "Qingdao"}, {"label": "South China", "value": "South China"}])
            dual_input_cell("load_port", "装港 Load Port", is_text=True,
                           presets=[{"label": "Samarinda", "value": "Samarinda"}, {"label": "Taboneo", "value": "Taboneo"}])
            dual_input_cell("disch_port", "卸港 Discharge Port", is_text=True,
                           presets=[{"label": "Guangzhou", "value": "Guangzhou"}, {"label": "Shenzhen", "value": "Shenzhen"}])
            dual_input_cell("bl_distance", "空放-装港距离 BL Distance", "nm", step=1.0,
                           presets=[{"label": "Route B", "value": 1850.0}, {"label": "Route C", "value": 2100.0}])
        with col2:
            dual_input_cell("ld_speed", "载货航速 LD Speed", "knots", step=0.1,
                           presets=[{"label": "default", "value": 11.5}, {"label": "ECO", "value": 11.5}])
            dual_input_cell("ld_distance", "装港-卸港距离 LD Distance", "nm", step=1.0,
                           presets=[{"label": "Alt", "value": 1680.0}, {"label": "Long", "value": 1850.0}])
            dual_input_cell("load_rate", "装港速率 Load Rate", "mt/day", step=1000.0,
                           presets=[{"label": "Weather adj.", "value": 27000.0}, {"label": "Fast", "value": 35000.0}])
            dual_input_cell("disch_rate", "卸港速率 Discharge Rate", "mt/day", step=1000.0,
                           presets=[{"label": "Weather adj.", "value": 13500.0}, {"label": "Fast", "value": 20000.0}])
            dual_input_cell("qty_mt", "货量 Qty", "mt", step=1000.0,
                           presets=[{"label": "Draft lim.", "value": 68000.0}, {"label": "Max", "value": 75000.0}])
            dual_input_cell("true_time", "压港等待 True Time", "days", step=0.1,
                           presets=[{"label": "default", "value": 1.5}, {"label": "Short", "value": 0.5}])

    formula_connector("distance / speed / 24")

    # ============================================================
    # SEGMENT 2: Fuel Consumption Specs
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("油耗船规 Fuel Consumption Specs", "Daily consumption rates by voyage segment")
        col1, col2 = st.columns(2)
        with col1:
            dual_input_cell("b_vlsfo", "空放油耗 VLSFO", "mt/day", step=0.1,
                           presets=[{"label": "default", "value": 23.0}, {"label": "Full", "value": 24.0}])
            dual_input_cell("b_mgo", "空放油耗 MGO", "mt/day", step=0.01,
                           presets=[{"label": "ECO", "value": 0.15}, {"label": "Full", "value": 0.25}])
            dual_input_cell("l_vlsfo", "Loaded油耗 VLSFO", "mt/day", step=0.1,
                           presets=[{"label": "default", "value": 25.0}, {"label": "Full", "value": 26.0}])
            dual_input_cell("l_mgo", "Loaded油耗 MGO", "mt/day", step=0.01,
                           presets=[{"label": "ECO", "value": 0.15}, {"label": "Full", "value": 0.25}])
        with col2:
            dual_input_cell("idle_vlsfo", "待泊/Idle油耗 VLSFO", "mt/day", step=0.1,
                           presets=[{"label": "Cold iron", "value": 0.5}, {"label": "Std", "value": 3.8}])
            dual_input_cell("idle_mgo", "待泊/Idle油耗 MGO", "mt/day", step=0.01,
                           presets=[{"label": "Cold iron", "value": 0.05}, {"label": "Std", "value": 0.2}])
            dual_input_cell("work_vlsfo", "作业/Working油耗 VLSFO", "mt/day", step=0.1,
                           presets=[{"label": "default", "value": 4.0}, {"label": "Grab", "value": 6.5}])
            dual_input_cell("work_mgo", "作业/Working油耗 MGO", "mt/day", step=0.01,
                           presets=[{"label": "Grab", "value": 0.25}, {"label": "Std", "value": 0.2}])

    formula_connector("consumption × time")

    # ============================================================
    # SEGMENT 3: Voyage Time Breakdown
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("航段时间 Voyage Time Breakdown", "Calculated voyage duration by segment")

        time_data = [
            ("空放航段 Birth→Load", c["bl_time"], c["bl_vlsfo"], c["bl_mgo"]),
            ("装货航段 Load→Discharge", c["ld_time"], c["ld_vlsfo"], c["ld_mgo"]),
            ("装港作业 Load Port", c["load_time"], c["load_vlsfo"], c["load_mgo"]),
            ("卸港作业 Discharge Port", c["disch_time"], c["dis_vlsfo"], c["dis_mgo"]),
            ("压港等待 True Time", c["true_time"], c["true_vlsfo"], c["true_mgo"]),
        ]

        total_pct = c["total_time"] if c["total_time"] > 0 else 1

        for name, t, v, m in time_data:
            pct = (t / total_pct) * 100 if total_pct > 0 else 0
            st.markdown(f"""
            <div style="position: relative; background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin-bottom: 6px; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; height: 100%; width: {pct}%; background: rgba(0,0,0,0.06); transition: width 0.3s;"></div>
                <div style="position: relative; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 11px; color: #555555;">{name}</div>
                        <div style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">{t:.4f} days</div>
                    </div>
                    <div style="display: flex; gap: 12px; text-align: right;">
                        <div>
                            <div style="font-size: 10px; color: #555555;">VLSFO</div>
                            <div style="font-size: 12px; font-family: 'Calibri', sans-serif; color: #000000;">{v:.2f}</div>
                        </div>
                        <div>
                            <div style="font-size: 10px; color: #555555;">MGO</div>
                            <div style="font-size: 12px; font-family: 'Calibri', sans-serif; color: #000000;">{m:.3f}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Total row
        st.markdown(f"""
        <div style="background: #f5f5f5; border: 2px solid #000000; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 13px; font-weight: bold; color: #000000; font-family: 'Calibri', sans-serif;">航行总时间 Total Voyage Time</div>
                <div style="font-size: 10px; color: #555555;">{c['total_time']:.4f} days</div>
            </div>
            <div style="display: flex; gap: 16px;">
                <div style="text-align: right;">
                    <div style="font-size: 10px; color: #555555;">重油油耗 VLSFO</div>
                    <div style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">{c['total_vlsfo']:.3f} mt</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 10px; color: #555555;">轻油油耗 MGO</div>
                    <div style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">{c['total_mgo']:.3f} mt</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    formula_connector("time × consumption × price")

    # ============================================================
    # SEGMENT 4: Fuel Cost
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("燃油费用 Fuel Cost", "Bunker prices and calculated fuel expenditure")
        col1, col2 = st.columns(2)
        with col1:
            dual_input_cell("vlsfo_price", "重油油价 VLSFO", "USD/mt", step=1.0,
                           presets=[{"label": "Platts", "value": 780.0}, {"label": "Market", "value": 750.0}])
        with col2:
            dual_input_cell("mgo_price", "轻油油价 MGO", "USD/mt", step=1.0,
                           presets=[{"label": "Platts", "value": 1550.0}, {"label": "Market", "value": 1500.0}])

        c1, c2 = st.columns(2)
        with c1:
            result_block("重油油耗 × 油价", c["vlsfo_cost"])
        with c2:
            result_block("轻油油耗 × 油价", c["mgo_cost"])
        result_block("总油费 Total Fuel Cost", c["total_fuel_cost"], decimals=2, is_result=True)

    formula_connector("qty × rate × (1 − commission)")

    # ============================================================
    # SEGMENT 5: Freight Revenue
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("运费收入 Freight Revenue", "Freight rate, commission and total revenue")
        col1, col2 = st.columns(2)
        with col1:
            dual_input_cell("freight_rate", "运费单价 Freight Rate", "USD/mt", step=0.1,
                           presets=[{"label": "Market", "value": 10.2}, {"label": "Low", "value": 8.0}])
        with col2:
            dual_input_cell("commission", "佣金 Commission", "fraction", step=0.001,
                           presets=[{"label": "Brokers", "value": 0.025}, {"label": "Full", "value": 0.15}])

        st.caption(f"Formula: {c['total_freight'] / (1 - float(st.session_state['commission_active_value'] or 0)) / (float(st.session_state['qty_mt_active_value'] or 1)):.1f} mt × $ {st.session_state['freight_rate_active_value']} × (1 − {st.session_state['commission_active_value']})")
        result_block("总运费 Total Freight", c["total_freight"], decimals=2, is_result=True)

    formula_connector("load + discharge")

    # ============================================================
    # SEGMENT 6: Port Charges
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("港使费 Port Charges", "Loading and discharge port fees")
        col1, col2 = st.columns(2)
        with col1:
            dual_input_cell("load_port_fee", "装港港费 Load Port Fee", "USD", step=1000.0,
                           presets=[{"label": "Discounted", "value": 45000.0}, {"label": "Budget", "value": 40000.0}])
        with col2:
            dual_input_cell("disch_port_fee", "卸港港费 Discharge Port Fee", "USD", step=1000.0,
                           presets=[{"label": "Discounted", "value": 36000.0}, {"label": "Budget", "value": 32000.0}])

        result_block("总港使费 Total Port Charges", c["total_port_charges"], decimals=0, is_result=True)

    formula_connector("freight − fuel − port = tce")

    # ============================================================
    # SEGMENT 6b: Other Expenses
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("其他费用 Other Expenses", "Miscellaneous and additional oil expenses for cost-plus freight")
        col1, col2 = st.columns(2)
        with col1:
            dual_input_cell("misc_expense", "杂费 Miscellaneous", "USD", step=1000.0,
                           presets=[{"label": "default", "value": 4000.0}, {"label": "High", "value": 8000.0}])
        with col2:
            dual_input_cell("oil_expense", "油杂 Oil Expense", "USD", step=1000.0,
                           presets=[{"label": "default", "value": 2000.0}, {"label": "High", "value": 5000.0}])

    formula_connector("oil + port + charter + misc = cost-plus freight")

    # ============================================================
    # SEGMENT 7: TCE Result - BOTH MODES SIDE BY SIDE
    # ============================================================
    st.markdown('<hr class="segment-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: #f5f5f5; border-top: 3px solid #000000; padding: 20px;">
    """, unsafe_allow_html=True)

    section_header("租金测算结果 TCE Result", "Forward and reverse TCE calculations")

    left, right = st.columns(2)

    with left:
        st.markdown('<div style="font-size: 13px; font-weight: bold; color: #000000; margin-bottom: 8px; text-decoration: underline;">算租金 Calculate TCE</div>', unsafe_allow_html=True)
        st.caption("总运费 − 总油费 − 港使费 = TCE")

        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">总运费</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['total_freight']:,.0f}</span>
        </div>
        <div style="text-align: center; color: #000000; font-size: 12px; font-weight: bold;">−</div>
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">总油费</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['total_fuel_cost']:,.0f}</span>
        </div>
        <div style="text-align: center; color: #000000; font-size: 12px; font-weight: bold;">−</div>
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">港使费</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['total_port_charges']:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        result_block("租金总费用 TCE Revenue", c["tce_revenue"], decimals=2, is_result=True)

        st.markdown(f"""
        <div style="background: #ffffff; border: 2px solid #000000; padding: 16px; text-align: center;">
            <div style="font-size: 11px; color: #555555; letter-spacing: 0.05em; font-weight: bold;">日租金 TCE DAY RATE</div>
            <div style="font-size: 36px; font-weight: bold; color: #000000; font-family: 'Calibri', sans-serif; text-decoration: underline; text-decoration-thickness: 2px;">${c['tce_day_rate']:,.2f}</div>
            <div style="font-size: 11px; color: #555555;">USD / day</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown('<div style="font-size: 13px; font-weight: bold; color: #000000; margin-bottom: 8px; text-decoration: underline;">算运费 Calculate Freight</div>', unsafe_allow_html=True)
        st.caption("target_day_rate × total_time + fuel + port = required_freight")

        dual_input_cell("target_day_rate", "目标日租金 Target Day Rate", "USD/day", step=100.0,
                       presets=[{"label": "default", "value": 19000.0}, {"label": "Market", "value": 20000.0}])

        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">目标租金 = 日租金 × 总时间</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['target_day_rate'] * c['total_time']:,.0f}</span>
        </div>
        <div style="text-align: center; color: #000000; font-size: 12px; font-weight: bold;">−</div>
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">总油费</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['total_fuel_cost']:,.0f}</span>
        </div>
        <div style="text-align: center; color: #000000; font-size: 12px; font-weight: bold;">−</div>
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">港使费</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['total_port_charges']:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        result_block("Required Freight Rate 所需运费单价", c["required_freight_rate"], decimals=2, is_result=True)
        result_block("Required Total Freight 所需总运费", c["required_total_freight"], decimals=2, is_result=True)

        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-size: 12px; font-weight: bold; color: #000000; margin-bottom: 6px; text-decoration: underline;">算运费 (Cost-Plus) = (油 + 港费 + 租船 + 其他) / 货量</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">油费 (Fuel + Oil Misc)</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['total_oil_cost']:,.0f}</span>
        </div>
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">港使费 Port Charges</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['total_port_charges']:,.0f}</span>
        </div>
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">租船 Charter (TC × Time)</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['charter_cost']:,.0f}</span>
        </div>
        <div style="background: #ffffff; border: 1px solid #000000; padding: 8px 12px; margin: 4px 0; display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #555555;">杂费 Miscellaneous</span>
            <span style="font-size: 13px; font-family: 'Calibri', sans-serif; color: #000000; font-weight: bold;">${c['misc_expense']:,.0f}</span>
        </div>
        <div style="text-align: center; color: #000000; font-size: 12px; font-weight: bold;">÷ 货量 {float(st.session_state['qty_mt_active_value'] or 0):,.0f} mt</div>
        """, unsafe_allow_html=True)

        result_block("算运费 Cost-Plus Freight Rate", c["cost_plus_freight_rate"], decimals=2, is_result=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # BOTTOM SUMMARY STRIP
    # ============================================================
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    sum1, sum2, sum3, sum4 = st.columns(4)
    with sum1:
        st.metric("航行总时间", f"{c['total_time']:.2f} days")
    with sum2:
        st.metric("总油费", f"${c['total_fuel_cost']:,.0f}")
    with sum3:
        st.metric("总港使费", f"${c['total_port_charges']:,.0f}")
    with sum4:
        st.metric("日租金 TCE", f"${c['tce_day_rate']:,.0f}/day")


if __name__ == "__main__":
    main()
