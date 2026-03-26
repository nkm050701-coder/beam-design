import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 頁面配置 ---
st.set_page_config(page_title="HK Beam Optimizer Pro", layout="wide")
st.title("🏗️ Professional Beam Design & Research Tool")
st.caption("Standard: HK Code of Practice 2013 | Enhanced Parametric Module")

# --- 側邊欄：輸入模組 ---
st.sidebar.header("📋 1. Inputs")
w = st.sidebar.slider("Ultimate Load w (kN/m)", 5.0, 100.0, 60.0)
L = st.sidebar.slider("Span L (m)", 3.0, 15.0, 5.0)

st.sidebar.header("🧱 2. Material & Width (B)")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 320)

# 【新增】K 值選擇器 (HK Code 限制通常到 0.225)
st.sidebar.header("🎯 3. Design Strategy")
K_target = st.sidebar.slider("Target K value (Limit=0.156)", 0.05, 0.225, 0.156, help="Standard limit is 0.156 for singly reinforced sections.")

st.sidebar.header("🧶 4. Reinforcement")
nbars = st.sidebar.slider("No. of bars", 2, 10, 3)
dia = st.sidebar.selectbox("Diameter (mm)", [12, 16, 20, 25, 32, 40], index=2)

# --- 核心運算模組 ---

# 1. 計算彎矩與剪力
M = (w * L**2) / 8  
V = (w * L) / 2     

# 2. 【核心更新】使用選擇的 K 值計算 d
# 公式: d = sqrt(M * 10^6 / (K_target * fcu * B))
d_calc = np.sqrt((M * 1e6) / (K_target * fcu * b))
h_recommended = d_calc + 40 

# 3. 配筋計算 (注意：若 K > 0.156，此公式僅計算拉伸筋需求，未計壓筋)
z = min(d_calc * (0.5 + np.sqrt(0.25 - K_target / 0.9)), 0.95 * d_calc)
as_req = (M * 1e6) / (0.87 * fy * z)
as_prov = nbars * (np.pi * dia**2 / 4)

# 4. 檢查
v_shear = (V * 1000) / (b * d_calc)
v_max = min(0.8 * np.sqrt(fcu), 7.0)
fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (M * 1e6) / (b * d_calc**2)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0)
allowable_ld = 20 * mf_tens 
actual_ld = (L * 1000) / d_calc

# --- UI Dashboard ---
st.subheader("📍 Design Summary (Target K = " + str(K_target) + ")")
c1, c2, c3 = st.columns(3)
c1.metric("Moment (M)", f"{M:.1f} kNm")
c2.metric("Required d", f"{d_calc:.1f} mm")
c3.metric("Lever Arm z", f"{z:.1f} mm")

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("✅ Auto Checking")
    
    # K 值警告
    if K_target > 0.156:
        st.warning(f"⚠️ K ({K_target}) > 0.156: Compression steel may be required.")
    else:
        st.success(f"✅ K ({K_target}) <= 0.156: Singly reinforced OK.")

    if as_prov >= as_req:
        st.success(f"✅ Strength Pass!")
    else:
        st.error(f"❌ Steel not enough!")

    if actual_ld <= allowable_ld:
        st.success(f"✅ Deflection Pass!")
    else:
        st.error(f"❌ Deflection Fail!")

    st.info(f"👉 Suggested H ≈ {round(h_recommended/10)*10} mm")

with col_right:
    st.subheader("📈 Design Graph")
    
    widths = np.linspace(200, 800, 100)
    # 畫出兩條線：一條是標準 0.156，一條是你的 Target K
    curve_std = np.sqrt((M * 1e6) / (0.156 * fcu * widths))
    curve_target = np.sqrt((M * 1e6) / (K_target * fcu * widths))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, curve_std, 'r--', alpha=0.5, label='Standard Limit (K=0.156)')
    ax.plot(widths, curve_target, 'r-', linewidth=2, label=f'Target Boundary (K={K_target})')
    
    # 輔助線
    ax.axvline(x=b, color='skyblue', linestyle='--', alpha=0.8)
    ax.axhline(y=d_calc, color='skyblue', linestyle='--', alpha=0.8)
    
    # 點精確放在你設定的 Target K 線上
    ax.scatter(b, d_calc, color='blue', s=250, zorder=5, label=f'Current Point (K={K_target})')
    
    ax.set_xlabel("Width B (mm)")
    ax.set_ylabel("Effective Depth d (mm)")
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

# 成本估算
st.divider()
vol_rc = (b/1000 * h_recommended/1000 * L)
cost_total = vol_rc * 1300 + (as_prov/1e6 * L * 7850) * 12
st.write(f"Estimated Cost: **${cost_total:.0f}**")
