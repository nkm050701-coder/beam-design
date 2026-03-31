import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Page Configuration ---
st.set_page_config(page_title="HK Beam Optimizer Pro", layout="wide")
st.title("Beam Design Calculator")
st.caption("Standard: HK Code of Practice 2013 | Enhanced per Tutor Comments")

# --- Sidebar: Inputs ---
st.sidebar.header("1. Inputs")
w = st.sidebar.number_input("Ultimate Load w (kN/m)", value=60.0)
L = st.sidebar.number_input("Span L (m)", value=5.0)

st.sidebar.header("2. Material & Geometry")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45, 60], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 500)
h = st.sidebar.slider("Height H (mm)", 200, 1200, 410) # Manual height input [cite: 32]

st.sidebar.header("3. Design Parameters")
K_val = st.sidebar.slider("Target K Value", 0.05, 0.225, 0.156)

st.sidebar.header("4. Reinforcement")
nbars = st.sidebar.slider("No. of bars", 2, 10, 4)
dia = st.sidebar.selectbox("Diameter (mm)", [12, 16, 20, 25, 32, 40], index=4)

st.sidebar.header("5. Unit Cost Settings")
unit_cost_rebar = st.sidebar.number_input("Steel Cost (HKD/tonne)", value=10000.0) # [cite: 47]
unit_cost_rc_area = st.sidebar.number_input("Concrete Formwork (HKD/m²)", value=50.0) # [cite: 49]

# --- Calculations ---
cover = 30
link_dia = 10
d_actual = h - cover - link_dia - (dia / 2) # Actual effective depth based on H

# 1. Moment & Shear
M = (w * L**2) / 8  
V = (w * L) / 2     

# 2. Required d based on K
d_req_K = np.sqrt((M * 1e6) / (K_val * fcu * b))

# 3. Steel Area & Percentage
z_raw = d_actual * (0.5 + np.sqrt(0.25 - K_val / 0.9)) if K_val <= 0.225 else 0
z = min(z_raw, 0.95 * d_actual) if z_raw > 0 else 0.75 * d_actual
as_req = (M * 1e6) / (0.87 * fy * z)
as_prov = nbars * (np.pi * dia**2 / 4)
rho_pct = (as_prov / (b * d_actual)) * 100 # 

# 4. Shear & Deflection
v_shear = (V * 1000) / (b * d_actual)
v_max = min(0.8 * np.sqrt(fcu), 7.0) # Simplified vc check

fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (M * 1e6) / (b * d_actual**2)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0)
allowable_ld = 20 * mf_tens 
actual_ld = (L * 1000) / d_actual

# Minimum d required for deflection check [cite: 6, 70]
d_min_defl = (L * 1000) / allowable_ld

# --- UI Dashboard ---
st.subheader("Design Summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Moment (M)", f"{M:.1f} kNm")
c2.metric("Req. d (K Line)", f"{d_req_K:.1f} mm")
c3.metric("Actual d", f"{d_actual:.1f} mm")
c4.metric("Shear Stress (v)", f"{v_shear:.2f} MPa")
c5.metric("L/d Ratio", f"{actual_ld:.1f}")

st.divider()

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("Auto Checking")
    
    # Capacity
    if as_prov >= as_req:
        st.success(f"Capacity Pass! (As_prov={as_prov:.0f} ≥ As_req={as_req:.0f} mm²)")
    else:
        st.error(f"Area Fail! (As_prov={as_prov:.0f} < As_req={as_req:.0f} mm²)")

    # Shear
    if v_shear <= v_max:
        st.success(f"Shear Pass! (v={v_shear:.2f} ≤ vc={v_max:.2f} MPa)")
    else:
        st.error(f"Shear Fail! (v={v_shear:.2f} > vc={v_max:.2f} MPa)")

    # Deflection
    if actual_ld <= allowable_ld:
        st.success(f"Deflection Pass! (Actual={actual_ld:.1f} ≤ Allowable={allowable_ld:.1f})")
    else:
        st.error(f"Deflection Fail! (Actual={actual_ld:.1f} > Allowable={allowable_ld:.1f})")

    # Bar Spacing Check [cite: 54, 55]
    clear_spacing = (b - 2*cover - 2*link_dia - nbars*dia) / (nbars - 1) if nbars > 1 else 0
    if clear_spacing >= max(dia, 20):
        st.success(f"Spacing Pass! (Clear={clear_spacing:.1f} mm)")
    else:
        st.warning(f"Spacing Tight! (Clear={clear_spacing:.1f} mm)")

    # Beam Section Drawing 
    st.write("**Beam Section Preview**")
    fig2, ax2 = plt.subplots(figsize=(4, 4))
    # Draw Beam Outline
    ax2.add_patch(patches.Rectangle((0, 0), b, h, facecolor='#f0f0f0', edgecolor='black', lw=2))
    # Draw Links
    ax2.add_patch(patches.Rectangle((cover, cover), b-2*cover, h-2*cover, fill=False, edgecolor='red', lw=1, ls='--'))
    # Draw Bars
    bar_x = np.linspace(cover + link_dia + dia/2, b - cover - link_dia - dia/2, nbars)
    for x in bar_x:
        ax2.add_patch(patches.Circle((x, cover + link_dia + dia/2), dia/2, color='blue'))
    ax2.set_xlim(-50, b+50); ax2.set_ylim(-50, h+50)
    ax2.axis('off')
    st.pyplot(fig2)
    st.info(f"Tension Reinf: {nbars}T{dia} ({rho_pct:.2f}%)") # [cite: 36]

with col_right:
    st.subheader(f"Graph (Target K = {K_val})")
    widths = np.linspace(200, 800, 100)
    req_depths_K = np.sqrt((M * 1e6) / (K_val * fcu * widths))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths_K, 'r-', linewidth=2, label=f'Boundary Line (K={K_val})')
    
    # Deflection Limit Line 
    ax.axhline(y=d_min_defl, color='purple', linestyle='--', alpha=0.6, label='Deflection Limit')
    ax.text(210, d_min_defl + 5, f"Min d for Deflection: {d_min_defl:.1f}mm", color='purple', fontsize=9)
    
    # Current Design Point
    ax.scatter(b, d_actual, color='blue', s=200, zorder=5, label=f'Design Point ({b}, {d_actual:.0f})')
    
    # Fulfilling Area shading
    ax.fill_between(widths, req_depths_K, 700, color='red', alpha=0.05, label='K-Limit Zone')

    ax.set_xlabel("Width B (mm)"); ax.set_ylabel("Effective Depth d (mm)")
    ax.set_ylim(250, 650); ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

# --- Cost Calculation ---
st.divider()
cost_rebar = (as_prov / 1e6 * L * 7.85) * unit_cost_rebar
cost_rc = (((2 * h + b) / 1000) * L) * unit_cost_rc_area
total_cost = cost_rebar + cost_rc
st.write(f"Cost (hkd\$) = Rebar \${cost_rebar:.0f} + RC \${cost_rc:.0f} = **\${total_cost:.0f}**")
