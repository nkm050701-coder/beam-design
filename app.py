import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Website Setting ---
st.set_page_config(page_title="HK Beam Optimizer", layout="wide")
st.title("Beam Design Calculator")
st.caption("Design Standard: Code of Practice for Structural Use of Concrete 2013 (2020 Edition) | CON4396 Industrial Based Student Project")

# --- Input ---
st.sidebar.header("1. Inputs of Loading and Geometry of Beams")
w = st.sidebar.number_input("Ultimate Load w (kN/m)", value=60.0)
L = st.sidebar.number_input("Span L (m)", value=5.0)

st.sidebar.header("2. Material Properties & Beam Width (B)")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45, 50, 55, 60], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 320, step=25)

st.sidebar.header("3. Desired K-Value")
K_val = st.sidebar.number_input(
    "Target K Value", 
    min_value=0.050, 
    max_value=0.225, 
    value=0.156, 
    step=0.001, 
    format="%.3f",
    help="Standard limit for singly reinforced is 0.156"
)

st.sidebar.header("4. Steel Reinforcement")
nbars = st.sidebar.slider("No. of bars", 2, 10, 3)
dia = st.sidebar.selectbox("Bar Diameter (mm)", [12, 16, 20, 25, 32, 40], index=2)

st.sidebar.header("5. Detailing & Cover")
nominal_cover = st.sidebar.number_input("Nominal Cover (mm)", value=25)
link_dia = st.sidebar.number_input("Link Diameter (mm)", value=10)

st.sidebar.header("6. Unit Cost Settings")
unit_cost_rebar = st.sidebar.number_input("Steel Reinforcement Cost (HKD/tonne)", value=3805.0)
unit_cost_rc_area = st.sidebar.number_input("Concrete Formwork Cost (HKD/m²)", value=42.0)

# --- Calculation ---

# 1. Calculation of Shear & Moment
M = (w * L**2) / 8  
V_force = (w * L) / 2      

# 2. Calculation of d and h
d_calc = np.sqrt((M * 1e6) / (K_val * fcu * b))
h_recommended = d_calc + nominal_cover + link_dia + (dia / 2)
h_final = np.ceil(h_recommended / 25) * 25
d_prime = nominal_cover + link_dia + (dia / 2) 

# 3. Steel Area Calculation
if fcu <= 45:
    K_limit = 0.156
else:
    K_limit = 0.120

if K_val <= K_limit:
    z_raw = d_calc * (0.5 + np.sqrt(0.25 - K_val / 0.9))
    z = min(z_raw, 0.95 * d_calc)
    as_req = (M * 1e6) / (0.87 * fy * z)
    as_prime_req = 0
else:
    z = d_calc * (0.5 + np.sqrt(0.25 - K_limit / 0.9))
    m_cap = K_limit * fcu * b * d_calc**2
    as_prime_req = (M * 1e6 - m_cap) / (0.87 * fy * (d_calc - d_prime))
    as_req = (m_cap / (0.87 * fy * z)) + as_prime_req

as_prov = nbars * (np.pi * dia**2 / 4)

# Steel Ratio Info
if fy <= 250:
    min_ratio = 0.0024  
else:
    min_ratio = 0.0013  
as_min = min_ratio * b * h_final

current_ratio = as_prov / (b * h_final)

if current_ratio < min_ratio:
    ratio_status = "FAILED (Below Minimum)"
else:
    ratio_status = "PASSED"
    
ratio_percentage = current_ratio * 100

bar_type = "T" if fy = 500 else "R"
reinforcement_text = f"{nbars}{bar_type}{dia} ({ratio_percentage:.2f}%) - {ratio_status}"

# 4. Spacing Calculation
n_spaces = nbars - 1
if n_spaces > 0:
    cc_spacing = (b - 2*nominal_cover - 2*link_dia - dia) / n_spaces
    clear_spacing = (b - 2*nominal_cover - 2*link_dia - nbars*dia) / n_spaces
else:
    cc_spacing = 0
    clear_spacing = 0

# 5. Shear Checking
v_shear = (V_force * 1000) / (b * d_calc)
v_max = min(0.8 * np.sqrt(fcu), 7.0) 
rho_v = max(min(100 * as_prov / (b * d_calc), 3.0), 0.15) 
k1 = max((400 / d_calc)**0.25, 1.0)
k2 = (min(fcu, 40) / 25)**(1/3)
vc = (0.79 * (rho_v**(1/3)) * k1 * k2) / 1.25 

# 6. Deflection Checking
fs = (2.0 / 3.0) * fy * (as_req / as_prov) if as_prov > 0 else 0
mbd2 = (M * 1e6) / (b * d_calc**2)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0)
allowable_ld = 20 * mf_tens 
actual_ld = (L * 1000) / d_calc
d_min_deflection = (L * 1000) / allowable_ld

# --- UI Dashboard ---
st.subheader("Design Summary")

r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
r1_c1.metric("Ultimate Load (w)", f"{w} kN/m")
r1_c2.metric("Design Moment (M)", f"{M:.1f} kNm")
r1_c3.metric("Design Shear (V)", f"{V_force:.1f} kN")
r1_c4.metric("Shear Stress (v)", f"{v_shear:.2f} MPa")

r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
r2_c1.metric("Concrete Shear Strength (vc)", f"{vc:.2f} MPa")
r2_c2.metric("Actual L/d Ratio", f"{actual_ld:.1f}")
r2_c3.metric("Limiting L/d Ratio", f"{allowable_ld:.1f}")
r2_c4.metric("Minimum Required Effective Depth to Fulfill Deflection Check", f"{d_min_deflection:.1f} mm")

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("Member Design")
    
    # 1. Capacity Checking
    if as_prov < as_min:
        st.error(f"Minimum Steel Fail! (Asprov={as_prov:.0f} < Asmin={as_min:.0f} mm²)")
    elif as_prov >= as_req:
        st.success(f"Design of Moment Pass! (Asprov={as_prov:.0f} >= Asreq={as_req:.0f} mm²)")
    else:
        st.error(f"Design of Moment Fail! (Asprov={as_prov:.0f} < Asreq={as_req:.0f} mm²)")

    # 2. Doubly Reinforced Info
    if as_prime_req > 0:
        st.warning(f"Doubly Reinforced Required! (As' req = {as_prime_req:.0f} mm²)")
    else:
        st.info("Singly Reinforced Design")

    # 3. Simplified Spacing Checking
    if nbars > 1:
        if cc_spacing <= 150:
            st.success(f"Bar Spacing = {cc_spacing:.1f} mm <= 150 mm c/c, ok")
        else:
            st.error(f"Bar Spacing = {cc_spacing:.1f} mm > 150 mm c/c, not ok")
        
        if clear_spacing >= 80:
            st.success(f"Clear Spacing = {clear_spacing:.1f} mm >= 80 mm, ok")
        else:
            st.error(f"Clear Spacing = {clear_spacing:.1f} mm < 80 mm, not ok")
    
    # 4. Shear Checking
    if v_shear > v_max:
        st.error(f"Design of Shear Crushing! (v={v_shear:.2f} > vmax={v_max:.2f} MPa)")
    elif v_shear <= (vc + 0.4):
        st.success(f"Design of Shear Pass (Nominal Links)! (v={v_shear:.2f} <= vc+0.4={vc+0.4:.2f})")
    else:
        st.warning(f"Shear Reinforcement Required! (v={v_shear:.2f} > vc+0.4={vc+0.4:.2f})")

    # 5. Deflection Checking
    if actual_ld <= allowable_ld:
        st.success(f"Design of Deflection Pass! (Actual L/d={actual_ld:.1f} <= Allowable={allowable_ld:.1f})")
    else:
        st.error(f"Design of Deflection Fail! (Actual L/d={actual_ld:.1f} > Allowable={allowable_ld:.1f})")

    st.markdown(f"**Suggested Tension Reinforcement:** `{reinforcement_text}`")
    st.markdown(f"**Final Beam Size:** `{b} x {int(h_final)} mm`")

with col_right:
    st.subheader("Beam Section")
    fig, ax = plt.subplots(figsize=(6, 7))
    rect = patches.Rectangle((0, 0), b, h_final, linewidth=2, edgecolor='black', facecolor='#f9f9f9')
    ax.add_patch(rect)
    link = patches.Rectangle((nominal_cover, nominal_cover), b - 2*nominal_cover, h_final - 2*nominal_cover, 
                             linewidth=1.5, edgecolor='red', fill=False, linestyle='--')
    ax.add_patch(link)
    
    for i in range(nbars):
        x = nominal_cover + link_dia + dia/2 + i * cc_spacing
        y = nominal_cover + link_dia + dia/2
        circle = patches.Circle((x, y), dia/2, color='#1f77b4', zorder=3)
        ax.add_patch(circle)
        
    top_nbars = 2 if as_prime_req == 0 else max(2, int(np.ceil(as_prime_req / (np.pi * 12**2 / 4))))
    top_spacing = (b - 2*nominal_cover - 2*link_dia - 12) / (top_nbars - 1) if top_nbars > 1 else 0
    for i in range(top_nbars):
        x = nominal_cover + link_dia + 12/2 + i * top_spacing
        y = h_final - nominal_cover - link_dia - 12/2
        bar_color = '#1f77b4' if as_prime_req > 0 else 'none'
        circle = patches.Circle((x, y), 12/2, edgecolor='#1f77b4', facecolor=bar_color, linewidth=1, zorder=3)
        ax.add_patch(circle)

    ax.set_xlim(-50, b + 50)
    ax.set_ylim(-50, h_final + 50)
    ax.set_aspect('equal')
    ax.axis('off')
    st.pyplot(fig)

st.divider()
st.subheader("Cost Estimation")
rebar_tonnage = (as_prov * 1e-6) * L * 7.85
cost_rebar = rebar_tonnage * unit_cost_rebar
area_rc = ((2 * h_final + b) / 1000) * L
cost_rc = area_rc * unit_cost_rc_area
total_cost = cost_rebar + cost_rc
st.markdown(f"Cost (HKD) = Steel Reinforcement \${cost_rebar:.0f} + Concrete \${cost_rc:.0f} = **\${total_cost:.0f}**")
