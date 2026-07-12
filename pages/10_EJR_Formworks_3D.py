# ============================================================
#  10_EJR_Formworks_3D.py — STREAMLIT EDITION 🤖⚡
#  EJR BUILDERS — Panel-vs-Panel Self-Tightening Truss v5
#  (diagonals SAGAD sa BOTTOM PLATE — max pressure sa base!)
#
#  ILAGAY SA: pages/10_EJR_Formworks_3D.py sa tycoons-eye repo
#  KAILANGAN SA requirements.txt: streamlit, plotly, numpy
# ============================================================

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(page_title="EJR Formworks 3D", page_icon="🏗️",
                   layout="wide")

st.title("🏗️ EJR Modular Formworks — 3D Truss Visualizer")
st.caption("Panel-vs-panel self-tightening bracing • lahat kahoy-sa-kahoy, "
           "sagad, may kalso • diagonals lumalapat sa BOTTOM PLATE "
           "(kung saan max ang hydrostatic pressure, P = ρgh)")

# ================= SIDEBAR CONTROLS =================
st.sidebar.header("⚙️ Dimensions (meters)")
PANEL_L  = st.sidebar.number_input("Panel length (phenolic)", 1.22, 4.88, 2.44, 0.01)
PANEL_H  = st.sidebar.number_input("Panel height", 0.60, 2.44, 1.22, 0.01)
CLEAR_W  = st.sidebar.number_input("Clear width ng canal", 0.40, 2.00, 0.90, 0.05)
LUM      = st.sidebar.number_input("Lumber size (2x2 ≈ 0.05)", 0.03, 0.10, 0.05, 0.005)
PLY_T    = 0.019
STUD_SPC = st.sidebar.number_input("Stud spacing", 0.30, 1.20, 0.60, 0.05)
WALER_OFF= st.sidebar.number_input("Waler offset (taas/baba)", 0.20, 0.60, 0.40, 0.05)
BAMBOO   = 0.08
WEDGE_GAP= 0.05

st.sidebar.header("🎋 Struts & Diagonals")
n_struts = st.sidebar.slider("Bilang ng horizontal struts", 2, 6, 3)
n_diags  = st.sidebar.slider("Bilang ng diagonals (salit-salit)", 2, 8, 4)

# Auto-compute positions (evenly spaced)
STRUT_X = [PANEL_L*(i+1)/(n_struts+1) for i in range(n_struts)]
DIAG_X  = [PANEL_L*(i+0.5)/n_diags for i in range(n_diags)]

# Bearing faces / heights
Y_WALER_L = PLY_T + 2*LUM
Y_WALER_R = CLEAR_W - PLY_T - 2*LUM
Y_FRAME_L = PLY_T + LUM
Y_FRAME_R = CLEAR_W - PLY_T - LUM
Z_LO   = WALER_OFF
Z_HI   = PANEL_H - WALER_OFF
Z_BASE = LUM/2

# Colors
C_PLY, C_FRAME, C_STUD  = "#3b2f2f", "#c8963e", "#e0aa4e"
C_WALER, C_BAMBOO       = "#8b5a2b", "#7a9b3e"
C_WEDGE                 = "#d94f30"
C_DIAG_A, C_DIAG_B      = "#2f6db3", "#7fb3e8"
C_FLOOR                 = "#b8b0a0"

# ================= GEOMETRY HELPERS =================
def box(fig, col, x0, y0, z0, dx, dy, dz, color, name, opacity=1.0):
    X = [x0 + dx*v for v in (0,0,1,1,0,0,1,1)]
    Y = [y0 + dy*v for v in (0,1,1,0,0,1,1,0)]
    Z = [z0 + dz*v for v in (0,0,0,0,1,1,1,1)]
    fig.add_trace(go.Mesh3d(
        x=X, y=Y, z=Z,
        i=[7,0,0,0,4,4,6,6,4,0,3,2],
        j=[3,4,1,2,5,6,5,2,0,1,6,3],
        k=[0,7,2,3,6,7,1,1,5,5,7,6],
        color=color, opacity=opacity, name=name,
        hovertext=name, hoverinfo="text",
        flatshading=True, showlegend=False
    ), row=1, col=col)

def beam(fig, col, p0, p1, size, color, name):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    w = p1 - p0
    L = np.linalg.norm(w)
    w = w / L
    ref = np.array([0,0,1.0]) if abs(w[2]) < 0.9 else np.array([1.0,0,0])
    u = np.cross(w, ref); u /= np.linalg.norm(u)
    v = np.cross(w, u)
    s = size/2
    pat = [(-s,-s,0),(-s,s,0),(s,s,0),(s,-s,0),
           (-s,-s,L),(-s,s,L),(s,s,L),(s,-s,L)]
    pts = [p0 + a*u + b*v + c*w for a,b,c in pat]
    X, Y, Z = zip(*pts)
    fig.add_trace(go.Mesh3d(
        x=X, y=Y, z=Z,
        i=[7,0,0,0,4,4,6,6,4,0,3,2],
        j=[3,4,1,2,5,6,5,2,0,1,6,3],
        k=[0,7,2,3,6,7,1,1,5,5,7,6],
        color=color, name=name,
        hovertext=name, hoverinfo="text",
        flatshading=True, showlegend=False
    ), row=1, col=col)

def build_panel(fig, col, y_ply, direction, tag=""):
    d = direction
    if d > 0:
        yp, yf, yw = y_ply, y_ply + PLY_T, y_ply + PLY_T + LUM
    else:
        yp, yf, yw = y_ply - PLY_T, y_ply - PLY_T - LUM, y_ply - PLY_T - 2*LUM

    box(fig, col, 0, yp, 0, PANEL_L, PLY_T, PANEL_H, C_PLY,
        f"{tag}Phenolic 3/4\"", opacity=0.95)
    box(fig, col, 0, yf, 0, PANEL_L, LUM, LUM, C_FRAME,
        f"{tag}BOTTOM PLATE 2x2 (bearing ng diagonal!)")
    box(fig, col, 0, yf, PANEL_H-LUM, PANEL_L, LUM, LUM, C_FRAME,
        f"{tag}Top plate 2x2")

    stud_x = [0.0]
    x = STUD_SPC
    while x < PANEL_L - LUM:
        stud_x.append(x - LUM/2)
        x += STUD_SPC
    stud_x.append(PANEL_L - LUM)
    for sx in stud_x:
        box(fig, col, sx, yf, LUM, LUM, LUM, PANEL_H - 2*LUM, C_STUD,
            f"{tag}Vertical stud @ x={sx+LUM/2:.2f}m")

    for zc, lbl in [(Z_LO, "Lower"), (Z_HI, "Upper")]:
        box(fig, col, 0, yw, zc - LUM/2, PANEL_L, LUM, LUM, C_WALER,
            f"{tag}{lbl} waler (z={zc:.2f}m)")

def floor_slab(fig, col):
    box(fig, col, -0.15, -0.30, -0.06, PANEL_L + 0.30, CLEAR_W + 0.60, 0.06,
        C_FLOOR, "Trench floor (cured flooring)", opacity=0.45)

def strut(fig, col, sx, sz):
    span = Y_WALER_R - Y_WALER_L - WEDGE_GAP
    box(fig, col, sx - BAMBOO/2, Y_WALER_L, sz - BAMBOO/2,
        BAMBOO, span, BAMBOO, C_BAMBOO,
        f"Bamboo strut @ x={sx:.2f}, z={sz:.2f}")
    yg = Y_WALER_L + span
    box(fig, col, sx - BAMBOO/2, yg, sz - BAMBOO/2,
        BAMBOO, WEDGE_GAP/2, BAMBOO/2, C_WEDGE, "KALSO #1")
    box(fig, col, sx - BAMBOO/2, yg + WEDGE_GAP/2, sz,
        BAMBOO, WEDGE_GAP/2, BAMBOO/2, C_WEDGE, "KALSO #2")

def diagonal(fig, col, dx_station, flip):
    if not flip:
        p_top = np.array([dx_station, Y_WALER_L, Z_HI])
        p_bot = np.array([dx_station, Y_FRAME_R, Z_BASE])
        color, mem = C_DIAG_A, "A (L-taas → R-PINAKABABA)"
    else:
        p_top = np.array([dx_station, Y_WALER_R, Z_HI])
        p_bot = np.array([dx_station, Y_FRAME_L, Z_BASE])
        color, mem = C_DIAG_B, "B (R-taas → L-PINAKABABA)"
    d = p_bot - p_top
    L = np.linalg.norm(d); d = d / L
    p_bot_short = p_bot - d * WEDGE_GAP
    beam(fig, col, p_top, p_bot_short, LUM, color,
         f"Diagonal {mem} @ x={dx_station:.2f} — sagad sa BOTTOM PLATE")
    kx, ky, kz = p_bot_short
    y_k = min(ky, p_bot[1]) if p_bot[1] > p_top[1] else p_bot[1]
    box(fig, col, kx - LUM/2, y_k, max(kz - LUM/2, 0.0),
        LUM, WEDGE_GAP, LUM, C_WEDGE,
        f"KALSO ng diagonal @ x={dx_station:.2f}")

def all_diagonals(fig, col):
    for n, dx_station in enumerate(DIAG_X):
        diagonal(fig, col, dx_station, flip=(n % 2 == 1))

# ================= BUILD FIGURE =================
fig = make_subplots(
    rows=1, cols=3,
    specs=[[{"type": "scene"}]*3],
    subplot_titles=(
        "STAGE 1 — Panels + BOTTOM struts",
        "STAGE 2 — + UPPER struts + diagonals sa BASE",
        "STAGE 3 — Locked truss + concrete pour",
    ),
    horizontal_spacing=0.01,
)

for c in (1, 2, 3):
    floor_slab(fig, c)
    build_panel(fig, c, y_ply=0,       direction=+1, tag="[LEFT] ")
    build_panel(fig, c, y_ply=CLEAR_W, direction=-1, tag="[RIGHT] ")
    for sx in STRUT_X:
        strut(fig, c, sx, Z_LO)
        if c >= 2:
            strut(fig, c, sx, Z_HI)
    if c >= 2:
        all_diagonals(fig, c)

box(fig, 3, 0, -0.15, 0, PANEL_L, 0.15, PANEL_H, "#9aa0a6",
    "CONCRETE (LEFT) — max pressure sa BABA!", opacity=0.30)
box(fig, 3, 0, CLEAR_W, 0, PANEL_L, 0.15, PANEL_H, "#9aa0a6",
    "CONCRETE (RIGHT) — max pressure sa BABA!", opacity=0.30)

axis_style = dict(
    xaxis_title="Length (m)", yaxis_title="Depth (m)", zaxis_title="Height (m)",
    aspectmode="data",
    xaxis=dict(backgroundcolor="#f5f0e8"),
    yaxis=dict(backgroundcolor="#efe8dc"),
    zaxis=dict(backgroundcolor="#e8e0d0"),
    camera=dict(eye=dict(x=1.7, y=-1.7, z=0.9)),
)
fig.update_layout(
    scene=axis_style, scene2=axis_style, scene3=axis_style,
    height=600, margin=dict(l=0, r=0, t=40, b=0),
)

st.plotly_chart(fig, use_container_width=True)

# ================= FIELD PROTOCOL =================
with st.expander("📋 FIELD PROTOCOL para kay Dannyboy (i-screenshot!)"):
    st.markdown(f"""
**KONSEPTO:** Ang dalawang porma ang MAGLALABAN. Lahat ng braces ay
kahoy-sa-kahoy (2x2 walers / bottom plate), SAGAD, may kalso.
WALANG tukod sa semento. Ang hydrostatic pressure (P = ρgh) ay
pinakamalakas sa PINAKA-ILALIM — kaya doon lumalapat ang mga diagonal.

1. Ibaba ang **LEFT panel**; hawakan ng isang laborer.
2. Ibaba AGAD ang **RIGHT panel** sa kabilang linya ng tansi.
3. **BOTTOM struts** (kawayan) sa LOWER walers @ x = {[f"{x:.2f}" for x in STRUT_X]} — pukpukin ang kalso. TAYO NA SILA!
4. **UPPER struts** sa UPPER walers, kalso ulit.
5. **DIAGONALS** @ x = {[f"{x:.2f}" for x in DIAG_X]}, SALIT-SALIT:
   odd = LEFT upper waler → RIGHT bottom plate; even = baliktad.
   Sagad kahoy-sa-kahoy; kalso sa babang dulo (ipukpok PAHIGA).
6. **BUHOS:** sabay/halinhinan layer-by-layer sa kaliwa't kanan —
   ang pressure mismo ang nagpapahigpit ng truss!
7. **BAKLAS:** pukpukin ang mga kalso → laglag ang braces →
   hilahin ang panels sa susunod na bay. **ZERO PAKO!**
8. Hindi sapat ang internal struts! OBLIGADO")
magbaon ng kongkretong pako (Concrete Nails) o gumamit ng drill at tox para i-bolt ang 2x2 Bottom Plate
sa mismong Cured Day-1 Flooring! Kailangang naka-lock ito pababa

""")

# ================= BOM =================
with st.expander("🧮 Bill of Materials (per panel)"):
    n_int = max(0, int((PANEL_L - LUM) / STUD_SPC))
    lm_plates = 2 * PANEL_L
    lm_studs  = (2 + n_int) * (PANEL_H - 2*LUM)
    lm_walers = 2 * PANEL_L
    total = lm_plates + lm_studs + lm_walers
    st.write(f"Top+bottom plates: **{lm_plates:.2f} LM**")
    st.write(f"Vertical studs x{2+n_int}: **{lm_studs:.2f} LM**")
    st.write(f"Walers x2: **{lm_walers:.2f} LM**")
    st.write(f"**TOTAL: {total:.2f} LM per panel** → x30 panels = "
             f"**{total*30:.1f} LM** ≈ {total*30/3.65:.0f} pcs @ 12ft")
