import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 頁面佈局 ---
st.set_page_config(page_title="HK RC Beam Designer", layout="wide")
st.title("🏗️ RC Beam Design System (HK Code 2013)")
st.caption("Professional Design Tool for Topic 02a | Final Year Project")

# --- 側邊欄：設計輸入 (User Inputs) ---
st.sidebar.header("📋 1. 荷重與幾何 (Loading & Geometry)")
gk = st.sidebar.slider("永久荷載 Gk (kN/m)", 5.0, 50.0, 20.0)
qk = st.sidebar.slider("可變荷載 Qk (kN/m)", 0.0, 50.0, 15.0)
L = st.sidebar.slider("跨距 Span L (m)", 3.0, 12.0, 6.0)

st.sidebar.header("🧱 2. 材料與截面")
fcu = st.sidebar.selectbox("混凝土強度 fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("鋼筋強度 fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("梁寬 b (mm)", 200, 600, 300)
h = st.sidebar.slider("梁高 h (mm)", 300, 1000, 600)
d = h - 40 # 假設保護層 40mm

st.sidebar.header("🧶 3. 配筋選擇 (Rebar Selection)")
nbars = st.sidebar.slider("鋼筋根數 (No. of bars)", 2, 10, 3)
dia = st.sidebar.selectbox("鋼筋直徑 (mm)", [12, 16, 20, 25, 32, 40], index=2)

# --- 核心運算引擎 (Engineering Engine) ---
# 1. 荷重分析 (Analysis)
w_total = 1.35 * gk + 1.5 * qk
mu = (w_total * L**2) / 8  # 設計彎矩 kNm
vu = (w_total * L) / 2     # 設計剪力 kN

# 2. 彎矩計算 (HK Code 2013 Cl 6.1.2.4)
K = (mu * 1e6) / (fcu * b * d**2)
K_limit = 0.156
z_raw = d * (0.5 + np.sqrt(0.25 - K / 0.9)) if K <= K_limit else 0
z = min(z_raw, 0.95 * d) if z_raw > 0 else 0
as_req = (mu * 1e6) / (0.87 * fy * z) if z > 0 else 0

# 3. 實際配筋與最小配筋 (Cl 9.2.1.1)
as_prov = nbars * (np.pi * dia**2 / 4)
as_min = 0.0013 * b * h

# 4. 撓度檢查 (Cl 7.3.2.2) - 這裡就是解決 Min 報錯的地方
fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (mu * 1e6) / (b * d**2)
# 修正係數 MF_tens (上限 2.0)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0) if as_req > 0 else 1.0
allowable_ld = 20 * mf_tens # 簡支梁 Basic Ratio = 20
actual_ld = (L * 1000) / d

# --- 主介面顯示 (UI Dashboard) ---
c1, c2, c3 = st.columns(3)
c1.metric("Ultimate Load (w)", f"{w_total:.1f} kN/m")
c2.metric("Moment (Mu)", f"{mu:.1f} kNm")
c3.metric("Shear (Vu)", f"{vu:.1f} kN")

st.divider()

res1, res2 = st.columns([1, 1.2])
with res1:
    st.subheader("✅ 設計檢查結果")
    
    # 彎矩檢查
    if K > K_limit:
        st.error(f"❌ 斷面太小! K={K:.3f} > {K_limit}")
    elif as_prov < as_req:
        st.warning(f"❌ 鋼筋不足! 需求 {as_req:.0f} mm² > 實配 {as_prov:.0f} mm²")
    else:
        st.success(f"✅ 強度合格! As_prov={as_prov:.0f} mm²")
    
    # 撓度檢查
    if actual_ld <= allowable_ld:
        st.success(f"✅ 撓度合格! L/d={actual_ld:.1f} <= {allowable_ld:.1f}")
    else:
        st.error(f"❌ 撓度超標! L/d={actual_ld:.1f} > {allowable_ld:.1f}")
        
    # 最小配筋檢查
    if as_prov >= as_min:
        st.success(f"✅ 最小配筋檢查 OK (>{as_min:.0f} mm²)")
    else:
        st.warning(f"⚠️ 低於最小配筋率要求")

with res2:
    st.subheader("📈 設計曲線圖表")
    # 繪製曲線圖 (對應你提供的圖片效果)
    widths = np.linspace(200, 800, 100)
    req_depths = np.sqrt((mu * 1e6) / (0.156 * fcu * widths))
    fig, ax = plt.subplots()
    ax.plot(widths, req_depths, 'r-', label='Required Min Depth (K=0.156)')
    ax.scatter(b, d, color='blue', s=150, label='Your Design (b, d)')
    ax.set_xlabel("Width b (mm)")
    ax.set_ylabel("Effective Depth d (mm)")
    ax.grid(True, linestyle='--')
    ax.legend()
    st.pyplot(fig)

# 成本與進階功能 (B2 分數)
st.divider()
st.subheader("💰 成本與估算 (Advanced Functions)")
cost_conc = (b/1000 * h/1000 * L) * 1200 # $1200/m3
cost_steel = (as_prov/1e6 * L * 7850) * 10 # $10/kg
total_cost = cost_conc + cost_steel
st.write(f"混凝土成本: ${cost_conc:.0f} | 鋼筋成本: ${cost_steel:.0f} | **總預算: ${total_cost:.0f}**")
