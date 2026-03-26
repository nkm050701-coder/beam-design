import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 頁面配置 ---
st.set_page_config(page_title="HK Beam Optimizer", layout="wide")
st.title("🏗️ Beam Design Calculator")
st.caption("Standard: HK Code of Practice 2013 | Topic 02a Design Tool")

# --- 側邊欄：輸入模組 ---
st.sidebar.header(" 1. Inputs")

w = st.sidebar.slider("Ultimate Load w (kN/m)", 5.0, 100.0, 60.0)
L = st.sidebar.slider("Span L (m)", 3.0, 15.0, 5.0)

st.sidebar.header("🧱 2. 材料與寬度 (B)")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 320)

st.sidebar.header("🧶 3. Reinforcement")
nbars = st.sidebar.slider("No. of bars", 2, 10, 3)
dia = st.sidebar.selectbox("Diameter (mm)", [12, 16, 20, 25, 32, 40], index=2)

# --- Calculation ---

# 1. Calculation of Shear & Moment
M = (w * L**2) / 8  
V = (w * L) / 2     

# 2. Calculation of d (K=0.156)
d_calc = np.sqrt((M * 1e6) / (0.156 * fcu * b))
h_recommended = d_calc + 40 

# 3. 彎矩配筋計算 (基於自動算的 d)
# K=0.156，z = 0.95d
z = 0.95 * d_calc
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

# --- 主介面顯示 (UI Dashboard) ---
st.subheader(" Design Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Ultimate Load (w)", f"{w} kN/m")
c2.metric("Moment (M)", f"{M:.1f} kNm") # 顯示 M
c3.metric("Required d (On Red Line)", f"{d_calc:.1f} mm")

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("✅ Auto Checking")
    
    # 強度檢查
    if as_prov >= as_req:
        st.success(f"✅ 強度合格! (As_prov={as_prov:.0f} mm²)")
    else:
        st.error(f"❌ Area not enough! need {as_req:.0f} mm²")

    # 剪力檢查
    if v_shear <= v_max:
        st.success(f"✅ Shear Pass! (v={v_shear:.2f} MPa)")
    else:
        st.error(f"❌ Shear Fail!")

    # 撓度檢查
    if actual_ld <= allowable_ld:
        st.success(f"✅ Deflection Pass! L/d={actual_ld:.1f} <= {allowable_ld:.1f}")
    else:
        st.error(f"❌ Deflection Fail!")

    st.info(f"👉 Suggested H ≈ {round(h_recommended/10)*10} mm")

with col_right:
    st.subheader("📈 Graph")
    # 繪製曲線
    widths = np.linspace(200, 800, 100)
    req_depths = np.sqrt((M * 1e6) / (0.156 * fcu * widths))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths, 'r-', linewidth=2.5, label='Boundary Line (K=0.156)')
    
    # 【輔助線】天藍色虛線指向座標軸
    ax.axvline(x=b, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.axhline(y=d_calc, color='skyblue', linestyle='--', alpha=0.8, linewidth=1.5)
    
    # 點精確放在紅線上
    ax.scatter(b, d_calc, color='blue', s=250, zorder=5, label=f'Design Point ({b}, {d_calc:.0f})')
    
    ax.set_xlabel("Width B (mm)", fontsize=11)
    ax.set_ylabel("Effective Depth d (mm)", fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

# 成本估算 (加分項)
st.divider()
vol_rc = (b/1000 * h_recommended/1000 * L)
cost_total = vol_rc * 1300 + (as_prov/1e6 * L * 7850) * 12
st.write(f"預估造價: **${cost_total:.0f}**")
