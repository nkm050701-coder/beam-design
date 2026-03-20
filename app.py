import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 頁面佈局 ---
st.set_page_config(page_title="HK RC Beam Designer", layout="wide")
st.title("🏗️ RC Beam Design System (HK Code 2013)")
st.caption("Professional Design Tool for Topic 02a | Final Year Project")

# --- 側邊欄：設計輸入 (User Inputs) ---
st.sidebar.header("📋 1. 荷重與跨度 (Loading & Geometry)")
gk = st.sidebar.slider("永久荷載 Gk (kN/m)", 5.0, 50.0, 20.0)
qk = st.sidebar.slider("可變荷載 Qk (kN/m)", 0.0, 50.0, 15.0)
L = st.sidebar.slider("跨度 Span L (m)", 3.0, 12.0, 6.0)

st.sidebar.header("🧱 2. 材料與截面")
fcu = st.sidebar.selectbox("混凝土強度 fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("鋼筋強度 fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("選擇梁寬 b (mm)", 200, 800, 300)

# --- 核心運算引擎 ---
# 1. 荷重分析
w_total = 1.35 * gk + 1.5 * qk
mu = (w_total * L**2) / 8  # kNm

# 2. 【核心修改】計算剛好落在紅線上的有效高度 d_limit (K=0.156)
# 公式: d = sqrt(Mu / (0.156 * fcu * b))
d_limit = np.sqrt((mu * 1e6) / (0.156 * fcu * b))
h_recommended = d_limit + 40 # 加上保護層後的總高度

# 3. 彎矩設計 (使用臨界值)
K_limit = 0.156
z = 0.95 * d_limit # 臨界狀態通常取 0.95d
as_req = (mu * 1e6) / (0.87 * fy * z)

# --- 主介面顯示 ---
c1, c2, c3 = st.columns(3)
c1.metric("Ultimate Load (w)", f"{w_total:.1f} kN/m")
c2.metric("Moment (Mu)", f"{mu:.1f} kNm")
c3.metric("推薦最小深度 d", f"{d_limit:.1f} mm")

st.divider()

res1, res2 = st.columns([1, 1.2])

with res1:
    st.subheader("📍 臨界設計點數據 (On Red Line)")
    st.info(f"根據你選擇的寬度 **B = {b} mm**：")
    st.write(f"👉 **所需最小有效高度 d** = `{d_limit:.1f}` mm")
    st.write(f"👉 **建議梁總高度 H** ≈ `{round(h_recommended/10)*10}` mm")
    st.write(f"👉 **此狀態下需求鋼筋 As,req** = `{as_req:.0f}` mm²")
    
    st.warning("提示：這條紅線代表 K=0.156。點落在線上表示斷面利用率達到最高，且不需要壓筋(Compression Steel)。")

with res2:
    st.subheader("📈 設計曲線與定位圖")
    # 繪製曲線圖
    widths = np.linspace(200, 800, 100)
    req_depths = np.sqrt((mu * 1e6) / (0.156 * fcu * widths))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(widths, req_depths, 'r-', linewidth=2, label='Required Min Depth (K=0.156)')
    
    # 【新增】畫出像你手繪圖一樣的藍色輔助虛線
    ax.axvline(x=b, color='skyblue', linestyle='--', alpha=0.8)
    ax.axhline(y=d_limit, color='skyblue', linestyle='--', alpha=0.8)
    
    # 【新增】將點精確放在紅線上
    ax.scatter(b, d_limit, color='blue', s=200, zorder=5, label=f'Selected Design ({b}, {d_limit:.0f})')
    
    # 設置標籤
    ax.set_xlabel("Width b (mm)", fontsize=12)
    ax.set_ylabel("Effective Depth d (mm)", fontsize=12)
    ax.set_title(f"Design Point for M = {mu:.1f} kNm", fontsize=14)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    
    st.pyplot(fig)

