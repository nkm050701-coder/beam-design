import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(page_title="HK Beam Optimizer", layout="wide")
st.title("Beam Design Calculator")
st.caption("Design Standard: Code of Practice for Structural Use of Concrete 2013 (2020 Edition) | CON4396 Industrial Based Student Project")

# --- Sidebar: Inputs ---
st.sidebar.header(" 1. Inputs")
w = st.sidebar.number_input("Ultimate Load w (kN/m)", value=60.0) # [cite: 16]
L = st.sidebar.number_input("Span L (m)", value=5.0) # [cite: 18]

st.sidebar.header(" 2. Material Properties & Beam Geometry")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45, 60], index=2) # [cite: 24, 25, 26]
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
# User now controls H instead of B to determine the design point
h = st.sidebar.slider("Height H (mm)", 200, 1000, 450) # [cite: 22, 32]

st.sidebar.header(" 3. Design K-Value")
K_val = st.sidebar.slider("Target K Value", 0.05, 0.225, 0.156) # [cite: 37, 38, 52]

st.sidebar.header(" 4. Reinforcement")
nbars = st.sidebar.slider("No. of bars", 2, 10, 4) # [cite: 41]
dia = st.sidebar.selectbox("Diameter (mm)", [12, 16, 20, 25, 32, 40], index=4) # [cite: 42]

st.sidebar.header(" 5. Unit Cost Settings")
unit_cost_rebar = st.sidebar.number_input("Rebar Cost (HKD/tonne)", value=3805.0) # [cite: 45, 46]
unit_cost_rc_area = st.sidebar.number_input("RC Formwork Cost (HKD/m²)", value=42.0) # [cite: 48, 49]

# --- Calculation ---
# 1. Determine d from H
cover = 30
link_dia = 10
d_actual = h - cover - link_dia - (dia / 2) # [cite: 12, 60]

# 2. Calculation of Moment
M = (w * L**2) / 8 # [cite: 11]

# 3. Calculate the REQUIRED B to stay exactly on the K Line
# Formula: B = (M * 1e6) / (K_val * fcu * d_actual^2)
b_required = (M * 1e6) / (K_val * fcu * d_actual**2) # [cite: 81]

# 4. Steel Area Calculation (Using d_actual)
z_raw = d_actual * (0.5 + np.sqrt(0.25 - K_val / 0.9)) if K_val <= 0.225 else 0
z = min(z_raw, 0.95 * d_actual) if z_raw > 0 else 0.75 * d_actual
as_req = (M * 1e6) / (0.87 * fy * z)
as_prov = nbars * (np.pi * dia**2 / 4) # [cite: 9, 36]

# 5. Shear Checking
V = (w * L) / 2 # [cite: 5, 28]
v_shear = (V * 1000) / (b_required * d_actual) # [cite: 13]
v_max = min(0.8 * np.sqrt(fcu), 7.0)

# 6. Deflection Checking (Standard logic)
fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (M * 1e6) / (b_required * d_actual**2)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0)
allowable_ld = 20 * mf_tens 
actual_ld = (L * 1000) / d_actual # [cite: 14, 30]

# --- UI Dashboard ---
st.subheader(" Design Summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Moment (M)", f"{M:.1f} kNm") # [cite: 11]
c2.metric("Fixed B (on K Line)", f"{b_required:.1f} mm") # [cite: 81]
c3.metric("Actual d (from H)", f"{d_actual:.1f} mm") # [cite: 12]
c4.metric("Shear Stress (v)", f"{v_shear:.2f} MPa") # [cite: 13]
c5.metric("Actual L/d", f"{actual_ld:.1f}") # [cite: 14]

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("Auto Checking") # [cite: 20]
    
    # 1. Capacity Checking
    symbol_as = "≥" if as_prov >= as_req else "<"
    if as_prov >= as_req:
        st.success(f"Capacity Pass! (As_prov={as_prov:.0f} {symbol_as} As_req={as_req:.0f} mm²)")
    else:
        st.error(f"Area Fail! (As_prov={as_prov:.0f} {symbol_as} As_req={as_req:.0f} mm²)")

    # 2. Shear Checking
    symbol_v = "≤" if v_shear <= v_max else ">"
    if v_shear <= v_max:
        st.success(f"Shear Pass! (v={v_shear:.2f} {symbol_v} vc={v_max:.2f} MPa)")
    else:
        st.error(f"Shear Fail! (v={v_shear:.2f} {symbol_v} vc={v_max:.2f} MPa)")

    # 3. Deflection Checking
    symbol_ld = "≤" if actual_ld <= allowable_ld else ">"
    if actual_ld <= allowable_ld:
        st.success(f"Deflection Pass! (Actual L/d={actual_ld:.1f} {symbol_ld} Allowable={allowable_ld:.1f})")
    else:
        st.error(f"Deflection Fail! (Actual L/d={actual_ld:.1f} {symbol_ld} Allowable={allowable_ld:.1f})")

with col_right:
    st.subheader(f"Graph (Target K = {K_val})") # [cite: 59]
    
    widths = np.linspace(100, 1000, 100)
    req_depths_K = np.sqrt((M * 1e6) / (K_val * fcu * widths)) # [cite: 78]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths_K, 'r-', linewidth=2.5, label=f'Boundary Line (K={K_val})') # [cite: 78]
    
    # Design Point is now locked to the intersection of B_required and d_actual
    ax.axvline(x=b_required, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.axhline(y=d_actual, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.scatter(b_required, d_actual, color='blue', s=250, zorder=5, label=f'Design Point ({b_required:.0f}, {d_actual:.0f})') # [cite: 79, 81]
    
    ax.set_xlabel("Width B (mm)") # [cite: 90]
    ax.set_ylabel("Effective Depth d (mm)") # [cite: 60]
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

# --- Cost Calculation ---
st.divider() # [cite: 74]
cost_rebar = (as_prov / 1e6 * L * 7.85) * unit_cost_rebar
area_rc = ((2 * h + b_required) / 1000) * L
cost_rc = area_rc * unit_cost_rc_area
total_cost = cost_rebar + cost_rc

st.write(f"Cost (hkd\$) = Rebar \${cost_rebar:.0f} + RC \${cost_rc:.0f} = **\${total_cost:.0f}**") # [cite: 75]
