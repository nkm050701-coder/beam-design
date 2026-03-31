import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Website Setting ---
st.set_page_config(page_title="HK Beam Optimizer", layout="wide")
st.title("Beam Design Calculator")
st.caption("Design Standard: Code of Practice for Structural Use of Concrete 2013 (2020 Edition) | CON4396 Industrial Based Student Project")

# --- Input ---
st.sidebar.header("1. Inputs of Loading and Geometry of Beams")
w = st.sidebar.number_input("Ultimate Load w (kN/m)", value=60.0)
L = st.sidebar.number_input("Span L (m)", value=5.0)

st.sidebar.header("2. Material Properties & Beam Width (B)")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 320)

st.sidebar.header("3. Desired K-Value")
K_val = st.sidebar.slider("Target K Value", 0.05, 0.225, 0.156, help="Standard limit for singly reinforced is 0.156")

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

# 3. Steel Area Calculation
z_raw = d_calc * (0.5 + np.sqrt(0.25 - K_val / 0.9)) if K_val <= 0.225 else 0
z = min(z_raw, 0.95 * d_calc) if z_raw > 0 else 0.75 * d_calc
as_req = (M * 1e6) / (0.87 * fy * z)
as_prov = nbars * (np.pi * dia**2 / 4)

# 4. Spacing Calculation (Custom Logic)
n_spaces = nbars - 1
if n_spaces > 0:
    cc_spacing = (b - 2*nominal_cover - 2*link_dia - dia) / n_spaces
    clear_spacing = (b - 2*nominal_cover - 2*link_dia - nbars*dia) / n_spaces
else:
    cc_spacing = 0
    clear_spacing = 0

# 5. Shear Checking (Section 6.3.2 - 6.3.4)
v_shear = (V_force * 1000) / (b * d_calc)
v_max = min(0.8 * np.sqrt(fcu), 7.0) 

rho = min(100 * as_prov / (b * d_calc), 3.0) 
k1 = (400 / d_calc)**0.25 if d_calc <= 400 else 1.0
k2 = (fcu / 25)**(1/3) if fcu <= 40 else (40 / 25)**(1/3)

vc = (0.79 * (rho**(1/3)) * k1 * k2) / 1.25 

# 6. Deflection Checking
fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (M * 1e6) / (b * d_calc**2)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0)
allowable_ld = 20 * mf_tens 
actual_ld = (L * 1000) / d_calc

# --- UI Dashboard ---
st.subheader("Design Summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Ultimate Load (w)", f"{w} kN/m")
c2.metric("Moment (M)", f"{M:.1f} kNm") 
c3.metric("Required d", f"{d_calc:.1f} mm")
c4.metric("Bar c/c Spacing", f"{cc_spacing:.1f} mm")
c5.metric("Clear Spacing", f"{clear_spacing:.1f} mm")

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("Auto Checking")
    
    # 1. Capacity Checking
    symbol_as = "≥" if as_prov >= as_req else "<"
    if as_prov >= as_req:
        st.success(f"Capacity Pass! (Asprov={as_prov:.0f} {symbol_as} Asreq={as_req:.0f} mm²)")
    else:
        st.error(f"Capacity Fail! (Asprov={as_prov:.0f} {symbol_as} Asreq={as_req:.0f} mm²)")

    # 2. Spacing Checking
    if nbars > 1:
        # c/c Check
        symbol_cc = "≤" if cc_spacing <= 150 else ">"
        if cc_spacing <= 150:
            st.success(f"c/c Spacing Pass! ({cc_spacing:.1f}mm {symbol_cc} 150mm)")
        else:
            st.error(f"c/c Spacing Fail! ({cc_spacing:.1f}mm {symbol_cc} 150mm)")
        
        # Clear Check
        symbol_clear = "≤" if clear_spacing <= 70 else ">"
        if clear_spacing <= 70:
            st.success(f"Clear Spacing Pass! ({clear_spacing:.1f}mm {symbol_clear} 70mm)")
        else:
            st.error(f"Clear Spacing Fail! ({clear_spacing:.1f}mm {symbol_clear} 70mm)")
    
    # 3. Shear Checking (Section 6.3.2)
    if v_shear > v_max:
        st.error(f"Shear Crushing! (v={v_shear:.2f} > vmax={v_max:.2f} MPa)")
    elif v_shear <= vc:
        st.success(f"Shear Pass! (v={v_shear:.2f} ≤ vc={vc:.2f} MPa)")
    elif v_shear <= (vc + 0.4):
        st.success(f"Shear Pass! (v={v_shear:.2f} ≤ vc+0.4={vc+0.4:.2f} MPa)")
    else:
        st.warning(f"Shear Reinforcement Required! (v={v_shear:.2f} > vc+0.4={vc+0.4:.2f} MPa)")
    # 4. Deflection Checking
    symbol_ld = "≤" if actual_ld <= allowable_ld else ">"
    if actual_ld <= allowable_ld:
        st.success(f"Deflection Pass! (Actual L/d={actual_ld:.1f} {symbol_ld} Allowable={allowable_ld:.1f})")
    else:
        st.error(f"Deflection Fail! (Actual L/d={actual_ld:.1f} {symbol_ld} Allowable={allowable_ld:.1f})")

    st.info(f"Final Beam Size: {b} x {int(h_final)} mm")

with col_right:
    st.subheader(f"Graph (Target K = {K_val})")
    widths = np.linspace(200, 800, 100)
    req_depths = np.sqrt((M * 1e6) / (K_val * fcu * widths))
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths, 'r-', linewidth=2.5, label=f'Boundary Line (K={K_val})')
    ax.axvline(x=b, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.axhline(y=d_calc, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.scatter(b, d_calc, color='blue', s=250, zorder=5, label=f'Design Point')
    ax.set_xlabel("Width B (mm)")
    ax.set_ylabel("Effective Depth d (mm)")
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

# --- Cost Calculation ---
st.divider()
st.subheader("Cost Estimation")
rebar_tonnage = (as_prov * 1e-6) * L * 7.85
cost_rebar = rebar_tonnage * unit_cost_rebar
area_rc = ((2 * h_final + b) / 1000) * L
cost_rc = area_rc * unit_cost_rc_area
total_cost = cost_rebar + cost_rc

st.write(f"Cost (hkd\$) = Rebar \${cost_rebar:.0f} + RC \${cost_rc:.0f} = **\${total_cost:.0f}**")
