import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 頁面配置 ---
st.set_page_config(page_title="HK Beam Optimizer", layout="wide")
st.title("Beam Design Calculator")
st.caption("Standard: HK Code of Practice 2013 | Topic 02a Design Tool")

# --- 側邊欄：輸入模組 ---
st.sidebar.header(" 1. Inputs")
# Change slider to number_input
w = st.sidebar.number_input("Ultimate Load w (kN/m)", value=60.0)
L = st.sidebar.number_input("Span L (m)", value=5.0)

st.sidebar.header(" 2. Material Properties & Beam Width (B)")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 320)

st.sidebar.header(" 3. Design K-Value")
K_val = st.sidebar.slider("Target K Value", 0.05, 0.225, 0.156, help="Standard limit for singly reinforced is 0.156")

st.sidebar.header(" 4. Reinforcement")
nbars = st.sidebar.slider("No. of bars", 2, 10, 3)
dia = st.sidebar.selectbox("Diameter (mm)", [12, 16, 20, 25, 32, 40], index=2)

# --- New: Unit Cost Inputs ---
st.sidebar.header(" 5. Unit Cost Settings")
unit_cost_rebar = st.sidebar.number_input("Rebar Cost (HKD/tonne)", value=3805.0)
unit_cost_rc_area = st.sidebar.number_input("RC Formwork Cost (HKD/m²)", value=42.0)

# --- Calculation ---

# 1. Calculation of Shear & Moment
M = (w * L**2) / 8  
V = (w * L) / 2     

# 2. Calculation of d
d_calc = np.sqrt((M * 1e6) / (K_val * fcu * b))
h_recommended = d_calc + 40 

# 3. Steel Area Calculation
z_raw = d_calc * (0.5 + np.sqrt(0.25 - K_val / 0.9)) if K_val <= 0.225 else 0
z = min(z_raw, 0.95 * d_calc) if z_raw > 0 else 0.75 * d_calc
as_req = (M * 1e6) / (0.87 * fy * z)
as_prov = nbars * (np.pi * dia**2 / 4)

# 4. Shear Checking
v_shear = (V * 1000) / (b * d_calc)
v_max = min(0.8 * np.sqrt(fcu), 7.0)

# 5. Deflection Checking
fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (M * 1e6) / (b * d_calc**2)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0)
allowable_ld = 20 * mf_tens 
actual_ld = (L * 1000) / d_calc

# --- UI Dashboard ---
st.subheader(" Design Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Ultimate Load (w)", f"{w} kN/m")
c2.metric("Moment (M)", f"{M:.1f} kNm") 
c3.metric("Required d (On K Line)", f"{d_calc:.1f} mm")

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("Auto Checking")
    
    if as_prov >= as_req:
        st.success(f"Capacity Pass! (As_prov={as_prov:.0f} mm²)")
    else:
        st.error(f"Area not enough! need {as_req:.0f} mm²")

    if v_shear <= v_max:
        st.success(f"Shear Pass! (v={v_shear:.2f} MPa)")
    else:
        st.error(f"Shear Fail!")

    if actual_ld <= allowable_ld:
        st.success(f"Deflection Pass! L/d={actual_ld:.1f} <= {allowable_ld:.1f}")
    else:
        st.error(f"Deflection Fail!")

    st.info(f"Suggested H ≈ {round(h_recommended/10)*10} mm")

with col_right:
    st.subheader(f"Graph (Target K = {K_val})")
    
    widths = np.linspace(200, 800, 100)
    req_depths = np.sqrt((M * 1e6) / (K_val * fcu * widths))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths, 'r-', linewidth=2.5, label=f'Boundary Line (K={K_val})')
    
    ax.axvline(x=b, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.axhline(y=d_calc, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    
    ax.scatter(b, d_calc, color='blue', s=250, zorder=5, label=f'Design Point ({b}, {d_calc:.0f})')
    
    ax.set_xlabel("Width B (mm)", fontsize=11)
    ax.set_ylabel("Effective Depth d (mm)", fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

# --- Cost Calculation ---
st.divider()
# Rebar Cost Calculation: (As_prov in m2) * L * density (7.85 t/m3) * user unit cost
cost_rebar = (as_prov / 1e6 * L * 7.85) * unit_cost_rebar
# RC Area Cost Calculation: (2h + b) * L in meters * user unit cost
area_rc = ((2 * h_recommended + b) / 1000) * L
cost_rc = area_rc * unit_cost_rc_area

total_cost = cost_rebar + cost_rc

# Output format: Cost (hkd$) = Rebar $xxx + RC $xxx = $xxx
st.write(f"Cost (hkd\$) = Rebar \${cost_rebar:.0f} + RC \${cost_rc:.0f} = **\${total_cost:.0f}**")
