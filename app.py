import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(page_title="HK Beam Optimizer", layout="wide")
st.title("Beam Design Calculator")
st.caption("Standard: HK Code of Practice 2013 | Topic 02a Design Tool")

# --- Sidebar: Inputs ---
st.sidebar.header(" 1. Inputs")
w = st.sidebar.number_input("Ultimate Load w (kN/m)", value=60.0)
L = st.sidebar.number_input("Span L (m)", value=5.0)

st.sidebar.header(" 2. Material Properties & Beam Geometry")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45, 60], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 500)
# Change control: Design point d is now driven by H
h = st.sidebar.slider("Height H (mm)", 200, 1000, 450)

st.sidebar.header(" 3. Design K-Value")
K_val = st.sidebar.slider("Target K Value", 0.05, 0.225, 0.156)

st.sidebar.header(" 4. Reinforcement")
nbars = st.sidebar.slider("No. of bars", 2, 10, 4)
dia = st.sidebar.selectbox("Diameter (mm)", [12, 16, 20, 25, 32, 40], index=4)

st.sidebar.header(" 5. Unit Cost Settings")
unit_cost_rebar = st.sidebar.number_input("Rebar Cost (HKD/tonne)", value=3805.0)
unit_cost_rc_area = st.sidebar.number_input("RC Formwork Cost (HKD/m²)", value=42.0)

# --- Calculation ---
# Standard assumptions for d calculation from H
cover = 30
link_dia = 10
d_actual = h - cover - link_dia - (dia / 2)

# 1. Calculation of Shear & Moment
M = (w * L**2) / 8  
V = (w * L) / 2     

# 2. Calculation of d_required on K boundary (for graphing)
# This is the theoretical minimum d for a given B and K
d_req_K = np.sqrt((M * 1e6) / (K_val * fcu * b))

# 3. Steel Area Calculation (Using d_actual from H)
z_raw = d_actual * (0.5 + np.sqrt(0.25 - K_val / 0.9)) if K_val <= 0.225 else 0
z = min(z_raw, 0.95 * d_actual) if z_raw > 0 else 0.75 * d_actual
as_req = (M * 1e6) / (0.87 * fy * z)
as_prov = nbars * (np.pi * dia**2 / 4)

# 4. Shear Checking (Section 6.1.2)
v_shear = (V * 1000) / (b * d_actual)
v_max = min(0.8 * np.sqrt(fcu), 7.0)

# 5. Deflection Checking (Section 8.3)
fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (M * 1e6) / (b * d_actual**2)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0)
allowable_ld = 20 * mf_tens 
actual_ld = (L * 1000) / d_actual
# Min d required to pass deflection check
d_min_defl = (L * 1000) / allowable_ld

# 6. Bar Spacing (Section 9.2.1)
clear_spacing = (b - 2*cover - 2*link_dia - nbars*dia) / (nbars - 1) if nbars > 1 else 0

# --- UI Dashboard ---
st.subheader(" Design Summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Moment (M)", f"{M:.1f} kNm")
c2.metric("Req. d (K Line)", f"{d_req_K:.1f} mm")
c3.metric("Actual d (from H)", f"{d_actual:.1f} mm")
c4.metric("Shear Stress (v)", f"{v_shear:.2f} MPa")
c5.metric("Actual L/d", f"{actual_ld:.1f}")

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("Auto Checking")
    
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

    # 3. Deflection Checking (Serviceability)
    symbol_ld = "≤" if actual_ld <= allowable_ld else ">"
    if actual_ld <= allowable_ld:
        st.success(f"Deflection Pass! (Actual L/d={actual_ld:.1f} {symbol_ld} Allowable={allowable_ld:.1f})")
    else:
        st.error(f"Deflection Fail! (Actual L/d={actual_ld:.1f} {symbol_ld} Allowable={allowable_ld:.1f})")

    # 4. Spacing Checking (Section 9.2.1)
    if clear_spacing >= max(dia, 20):
        st.success(f"Spacing Pass! (Clear={clear_spacing:.1f} mm)")
    else:
        st.error(f"Spacing Fail! (Clear={clear_spacing:.1f} mm)")

with col_right:
    st.subheader(f"Graph (Target K = {K_val})")
    
    widths = np.linspace(200, 800, 100)
    # The boundary curve still shows required d for different B values
    req_depths_K = np.sqrt((M * 1e6) / (K_val * fcu * widths))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths_K, 'r-', linewidth=2.5, label=f'Boundary Line (K={K_val})')
    
    # Design point is now plotted using current B and current d_actual (from H)
    ax.axvline(x=b, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.axhline(y=d_actual, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.scatter(b, d_actual, color='blue', s=250, zorder=5, label=f'Design Point ({b}, {d_actual:.0f})')
    
    # Tutor Comment: purple line for deflection limit
    ax.axhline(y=d_min_defl, color='purple', linestyle=':', alpha=0.7, label='Min d for Deflection')
    
    ax.set_xlabel("Width B (mm)")
    ax.set_ylabel("Effective Depth d (mm)")
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

# --- Cost Calculation ---
st.divider()
# Rebar Cost
cost_rebar = (as_prov / 1e6 * L * 7.85) * unit_cost_rebar
# RC Area Cost (2h + b) * L
area_rc = ((2 * h + b) / 1000) * L
cost_rc = area_rc * unit_cost_rc_area
total_cost = cost_rebar + cost_rc

# Output format: Cost (hkd$) = Rebar $xxx + RC $xxx = $xxx
st.write(f"Cost (hkd\$) = Rebar \${cost_rebar:.0f} + RC \${cost_rc:.0f} = **\${total_cost:.0f}**")
