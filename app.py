import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 頁面配置 ---
st.set_page_config(page_title="HK RC Beam Design Pro", layout="wide")
st.title("🏗️ RC Beam Design & Check System")
st.caption("Standard: HK Code of Practice 2013 (2020 Edition) | Professional Module")

# --- 側邊欄：輸入模組 (Input Module) ---
st.sidebar.header("📋 1. 荷重與跨度 (Analysis)")
gk = st.sidebar.slider("永久荷載 Gk (kN/m)", 5.0, 50.0, 20.0)
qk = st.sidebar.slider("可變荷載 Qk (kN/m)", 0.0, 50.0, 15.0)
L = st.sidebar.slider("有效跨度 Span L (m)", 3.0, 12.0, 6.0)

st.sidebar.header("🧱 2. 材料與截面 (Properties)")
fcu = st.sidebar.selectbox("混凝土強度 fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("鋼筋強度 fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("梁寬 B (mm)", 200, 600, 300)
h = st.sidebar.slider("梁高 H (mm)", 300, 1000, 500)
d = h - 40 # 預設保護層 40mm

st.sidebar.header("🧶 3. 鋼筋配置 (Reinforcement)")
nbars = st.sidebar.slider("鋼筋根數 (No. of bars)", 2, 10, 3)
dia = st.sidebar.selectbox("鋼筋直徑 (mm)", [12, 16, 20, 25, 32, 40], index=2)

# --- 核心計算引擎 (Engineering Engine) ---

# 1. 荷重分析 (Structural Analysis)
w_total = 1.35 * gk + 1.5 * qk
mu = (w_total * L**2) / 8  # kNm
vu = (w_total * L) / 2     # kN

# 2. 彎矩設計與檢查 (Moment Check)
K = (mu * 1e6) / (fcu * b * d**2)
K_limit = 0.156
z_raw = d * (0.5 + np.sqrt(0.25 - K / 0.9)) if K <= 0.225 else 0
z = min(z_raw, 0.95 * d) if z_raw > 0 else 0
as_req = (mu * 1e6) / (0.87 * fy * z) if z > 0 else 0
as_prov = nbars * (np.pi * dia**2 / 4)

# 3. 剪力檢查 (Shear Check - Cl 6.1.2.5)
v_shear = (vu * 1000) / (b * d)
v_max = min(0.8 * np.sqrt(fcu), 7.0)

# 4. 撓度檢查 (Deflection - Cl 7.3.2.2)
fs = (2 * fy * as_req) / (3 * as_prov) if as_prov > 0 else 0
mbd2 = (mu * 1e6) / (b * d**2)
# 修正係數 MF_tens (上限 2.0，這解決了 GeoGebra 之前的報錯問題)
mf_tens = min(0.55 + (477 - fs) / (120 * (0.9 + mbd2)), 2.0) if as_req > 0 else 1.0
allowable_ld = 20 * mf_tens # 簡支梁 Basic Ratio = 20
actual_ld = (L * 1000) / d

# --- UI 儀表板 (Dashboard) ---
st.subheader("📊 結構分析摘要 (Analysis Summary)")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ultimate Load (w)", f"{w_total:.1f} kN/m")
m2.metric("Moment (Mu)", f"{mu:.1f} kNm")
m3.metric("Shear (Vu)", f"{vu:.1f} kN")
m4.metric("K Value", f"{K:.3f}")

st.divider()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("✅ 規範檢查 (Code Compliance)")
    
    # 彎矩檢查 (Moment Check)
    if K > K_limit:
        st.error(f"❌ 斷面太小! K > {K_limit}。請增加 B 或 H。")
    elif as_prov < as_req:
        st.warning(f"❌ 鋼筋不足! 需求 {as_req:.0f} mm² > 實配 {as_prov:.0f} mm²")
    else:
        st.success(f"✅ 彎矩強度合格! (As_prov={as_prov:.0f} mm²)")

    # 剪力檢查 (Shear Check)
    if v_shear <= v_max:
        st.success(f"✅ 剪力極限合格! v={v_shear:.2f} < {v_max:.2f} MPa")
    else:
        st.error(f"❌ 剪力超過極限! 必須加大斷面尺寸。")

    # 撓度檢查 (Deflection Check)
    if actual_ld <= allowable_ld:
        st.success(f"✅ 撓度合格! L/d={actual_ld:.1f} <= {allowable_ld:.1f}")
    else:
        st.error(f"❌ 撓度不合格! 梁太細長，請增加 H。")

    # 最小配筋率 (Min Steel)
    as_min = 0.0013 * b * h
    if as_prov >= as_min:
        st.success(f"✅ 符合最小配筋率 (>{as_min:.0f} mm²)")
    else:
        st.warning(f"⚠️ 低於最小配筋率要求。")

with col_right:
    st.subheader("📈 設計定位圖表 (Design Boundary)")
    # 繪製曲線圖
    widths = np.linspace(200, 800, 100)
    req_depths = np.sqrt((mu * 1e6) / (0.156 * fcu * widths))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths, 'r-', linewidth=2, label='Min Required d (K=0.156)')
    
    # 【手繪圖還原】畫出點到座標軸的虛線
    ax.axvline(x=b, color='skyblue', linestyle='--', alpha=0.7)
    ax.axhline(y=d, color='skyblue', linestyle='--', alpha=0.7)
    
    # 標示目前的設計點
    point_color = 'blue' if K <= K_limit else 'orange'
    ax.scatter(b, d, color=point_color, s=200, zorder=5, label=f'Your Design ({b}, {d})')
    
    ax.set_xlabel("Beam Width B (mm)")
    ax.set_ylabel("Effective Depth d (mm)")
    ax.set_ylim(bottom=150)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    st.pyplot(fig)
    
    if K > K_limit:
        st.caption("⚠️ 點在紅線上方表示斷面不足，請將點移至紅線下方。")

