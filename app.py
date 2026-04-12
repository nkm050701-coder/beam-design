import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Website Setting ---
st.set_page_config(page_title="HK Beam Optimizer Pro", layout="wide")
st.title("Beam Design Calculator (HKCOP 2013)")

# --- Sidebar Inputs ---
st.sidebar.header("1. Loading & Geometry")
w = st.sidebar.number_input("Ultimate Load w (kN/m)", value=60.0)
L = st.sidebar.number_input("Span L (m)", value=5.0)

st.sidebar.header("2. Material & Size")
fcu = st.sidebar.selectbox("fcu (N/mm²)", [25, 30, 35, 40, 45], index=2)
fy = st.sidebar.selectbox("fy (N/mm²)", [250, 500], index=1)
b = st.sidebar.slider("Width B (mm)", 200, 800, 300)
h = st.sidebar.slider("Overall Height H (mm)", 300, 1200, 600) # 改為手動調整H

st.sidebar.header("3. Reinforcement")
dia = st.sidebar.selectbox("Main Bar Dia (mm)", [16, 20, 25, 32, 40], index=2)
nbars = st.sidebar.slider("No. of Tension Bars", 2, 10, 4)
nominal_cover = st.sidebar.number_input("Nominal Cover (mm)", value=25)
link_dia = st.sidebar.number_input("Link Diameter (mm)", value=10)

# --- Calculation Logic ---

# 1. Moment & Effective Depth
M = (w * L**2) / 8
d = h - nominal_cover - link_dia - (dia / 2)
d_prime = nominal_cover + link_dia + (dia / 2) # 壓筋中心深度

# 2. K-Value Calculation
K = (M * 1e6) / (fcu * b * d**2)
K_limit = 0.156 # HKCOP 2013 limit for singly reinforced

# 3. Steel Area Logic (Doubly Reinforced)
as_prime_req = 0
if K <= K_limit:
    # Singly Reinforced
    z = min(d * (0.5 + np.sqrt(0.25 - K / 0.9)), 0.95 * d)
    as_req = (M * 1e6) / (0.87 * fy * z)
    design_type = "Singly Reinforced"
else:
    # Doubly Reinforced
    design_type = "Doubly Reinforced"
    z = 0.775 * d
    m_cap = K_limit * fcu * b * d**2 # 混凝土能承受的最大彎矩
    as_prime_req = (M * 1e6 - m_cap) / (0.87 * fy * (d - d_prime))
    as_req = (m_cap / (0.87 * fy * z)) + as_prime_req

as_prov = nbars * (np.pi * dia**2 / 4)
as_min = 0.0013 * b * h

# --- Drawing Function ---
def draw_beam_section(b, h, nbars, dia, cover, link_dia, as_prime_req):
    fig, ax = plt.subplots(figsize=(5, 6))
    
    # 1. Concrete Outline
    rect = patches.Rectangle((0, 0), b, h, linewidth=2, edgecolor='black', facecolor='#F5F5F5', label='Concrete')
    ax.add_patch(rect)
    
    # 2. Link (Stirrup)
    link = patches.Rectangle((cover, cover), b - 2*cover, h - 2*cover, 
                             linewidth=2, edgecolor='#FF4B4B', fill=False, label='Link')
    ax.add_patch(link)
    
    # 3. Tension Bars (Bottom)
    spacing = (b - 2*cover - 2*link_dia - dia) / (nbars - 1) if nbars > 1 else 0
    for i in range(nbars):
        x = cover + link_dia + dia/2 + i * spacing
        y = cover + link_dia + dia/2
        circle = patches.Circle((x, y), dia/2, color='#1C83E1', zorder=3)
        ax.add_patch(circle)
        
    # 4. Compression Bars (Top) 
    # 如果是雙筋則畫實心，單筋則畫空心（Nominal bars）
    top_nbars = 2 if as_prime_req == 0 else max(2, int(np.ceil(as_prime_req / (np.pi * 16**2 / 4))))
    top_spacing = (b - 2*cover - 2*link_dia - 16) / (top_nbars - 1) if top_nbars > 1 else 0
    for i in range(top_nbars):
        x = cover + link_dia + 16/2 + i * top_spacing
        y = h - cover - link_dia - 16/2
        color = '#1C83E1' if as_prime_req > 0 else 'white'
        circle = patches.Circle((x, y), 16/2, edgecolor='#1C83E1', facecolor=color, linewidth=1, zorder=3)
        ax.add_patch(circle)

    ax.set_xlim(-50, b + 50)
    ax.set_ylim(-50, h + 50)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.title(f"Section: {b}x{h} mm", fontsize=12)
    return fig

# --- UI Dashboard ---
st.subheader("Design Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Design Type", design_type)
c2.metric("Moment M", f"{M:.1f} kNm")
c3.metric("K Value", f"{K:.3f}")
c4.metric("Status", "PASS" if as_prov >= as_req else "FAIL", delta=None)

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Structural Checking")
    
    # Tension Steel Check
    if as_prov >= as_req:
        st.success(f"Tension Steel: OK (Prov: {as_prov:.0f} > Req: {as_req:.0f} mm²)")
    else:
        st.error(f"Tension Steel: FAIL (Prov: {as_prov:.0f} < Req: {as_req:.0f} mm²)")
        
    # Compression Steel Check
    if as_prime_req > 0:
        st.warning(f"Compression Steel Required: {as_prime_req:.0f} mm²")
    else:
        st.info("No Compression Steel required (Singly Reinforced)")

    # Detail Check (Spacing)
    clear_spacing = (b - 2*nominal_cover - 2*link_dia - nbars*dia) / (nbars - 1) if nbars > 1 else 0
    if clear_spacing >= max(dia, 25):
        st.success(f"Spacing: {clear_spacing:.1f} mm (OK)")
    else:
        st.error(f"Spacing: {clear_spacing:.1f} mm (Too Tight!)")

with col_right:
    st.subheader("Cross Section Visualization")
    fig = draw_beam_section(b, h, nbars, dia, nominal_cover, link_dia, as_prime_req)
    st.pyplot(fig)

# --- Cost Estimation ---
st.divider()
st.subheader("Cost Estimation")
rebar_tonnage = (as_prov * 1e-6) * L * 7.85
cost_rebar = rebar_tonnage * unit_cost_rebar
area_rc = ((2 * h_final + b) / 1000) * L
cost_rc = area_rc * unit_cost_rc_area
total_cost = cost_rebar + cost_rc

st.markdown(f"Cost (HKD) = Steel Reinforcement \${cost_rebar:.0f} + Concrete \${cost_rc:.0f} = **\${total_cost:.0f}**")
