import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.title("EJR Builders — Lined Canal Cover 3D Visualizer")
st.caption(
    "Angle-bar frame + 16 mm bars B/W + PVC sleeves + sliding 12 mm U-bar lifters"
)

# ============================================================
# SIDEBAR CONTROLS
# ============================================================
st.sidebar.header("Cover Dimensions")

COV_L = st.sidebar.number_input(
    "Cover length, m", min_value=0.50, max_value=2.00, value=1.05, step=0.05
)
COV_W = st.sidebar.number_input(
    "Cover width, m", min_value=0.30, max_value=1.00, value=0.50, step=0.05
)
COV_T = st.sidebar.number_input(
    "Cover thickness, m", min_value=0.10, max_value=0.40, value=0.20, step=0.01
)

st.sidebar.header("Lifter Detail")
LIFT_SPC = st.sidebar.number_input(
    "Lifter spacing, m", min_value=0.10, max_value=0.80, value=0.40, step=0.05
)
LEG_SPC = st.sidebar.number_input(
    "Leg spacing, m", min_value=0.08, max_value=0.30, value=0.15, step=0.01
)
GROOVE_D = st.sidebar.number_input(
    "Groove depth, m", min_value=0.01, max_value=0.08, value=0.03, step=0.005
)
raised_right = st.sidebar.slider(
    "Right lifter raised, m", min_value=0.00, max_value=0.20, value=0.10, step=0.01
)

st.sidebar.header("Canal")
CLEAR_W = st.sidebar.number_input(
    "Clear canal width, m", min_value=0.40, max_value=1.50, value=0.90, step=0.05
)
WALL_T = st.sidebar.number_input(
    "Wall thickness, m", min_value=0.10, max_value=0.40, value=0.15, step=0.01
)
WALL_H = st.sidebar.number_input(
    "Wall height, m", min_value=0.50, max_value=2.50, value=1.15, step=0.05
)
SLAB_T = st.sidebar.number_input(
    "Top slab thickness, m", min_value=0.10, max_value=0.40, value=0.15, step=0.01
)

slab_opacity = st.sidebar.slider(
    "Concrete transparency", min_value=0.10, max_value=0.95, value=0.40, step=0.05
)

# ============================================================
# CONSTANTS
# ============================================================
AB_LEG = 0.05
AB_THK = 0.006
BAR16 = 0.016
BAR12 = 0.012
SLEEVE = 0.033
NUT = 0.03
BEARING = max((COV_L - CLEAR_W) / 2, 0)

C_CONC = "#b9b2a6"
C_CONC2 = "#9aa0a6"
C_AB = "#3d4852"
C_BAR16 = "#c0392b"
C_PVC = "#f0f0f0"
C_LIFT = "#2f6db3"
C_NUT = "#1a1a1a"
C_GROOVE = "#7a7267"

# ============================================================
# HELPERS
# ============================================================
def box(fig, col, x0, y0, z0, dx, dy, dz, color, name, opacity=1.0):
    X = [x0 + dx*v for v in (0,0,1,1,0,0,1,1)]
    Y = [y0 + dy*v for v in (0,1,1,0,0,1,1,0)]
    Z = [z0 + dz*v for v in (0,0,0,0,1,1,1,1)]

    fig.add_trace(
        go.Mesh3d(
            x=X,
            y=Y,
            z=Z,
            i=[7,0,0,0,4,4,6,6,4,0,3,2],
            j=[3,4,1,2,5,6,5,2,0,1,6,3],
            k=[0,7,2,3,6,7,1,1,5,5,7,6],
            color=color,
            opacity=opacity,
            name=name,
            hovertext=name,
            hoverinfo="text",
            flatshading=True,
            showlegend=False,
        ),
        row=1,
        col=col,
    )

def ab_frame(fig, col, ox, oy, oz, exploded=0.0):
    z_top = oz + COV_T
    e = exploded

    for ys, dirn in [(oy - e, -1), (oy + COV_W + e, +1)]:
        y_v = ys if dirn < 0 else ys - AB_THK
        y_h = ys if dirn < 0 else ys - AB_LEG

        box(
            fig, col, ox, y_v, z_top - AB_LEG,
            COV_L, AB_THK, AB_LEG,
            C_AB, "Angle bar — vertical leg"
        )
        box(
            fig, col, ox, y_h, z_top - AB_THK,
            COV_L, AB_LEG, AB_THK,
            C_AB, "Angle bar — horizontal leg"
        )

    for xs, dirn in [(ox - e, -1), (ox + COV_L + e, +1)]:
        x_v = xs if dirn < 0 else xs - AB_THK
        x_h = xs if dirn < 0 else xs - AB_LEG

        box(
            fig, col, x_v, oy, z_top - AB_LEG,
            AB_THK, COV_W, AB_LEG,
            C_AB, "Angle bar — vertical end leg"
        )
        box(
            fig, col, x_h, oy, z_top - AB_THK,
            AB_LEG, COV_W, AB_THK,
            C_AB, "Angle bar — horizontal end leg"
        )

def rebar_mats(fig, col, ox, oy, oz, lift=0.0):
    for zc, lbl in [
        (oz + 0.05 + lift, "BOTTOM"),
        (oz + COV_T - 0.05 + lift, "TOP"),
    ]:
        ny = 4
        for i in range(ny):
            yb = oy + 0.06 + i * (COV_W - 0.12) / max(ny - 1, 1)
            box(
                fig, col,
                ox + 0.03, yb - BAR16/2, zc - BAR16/2,
                COV_L - 0.06, BAR16, BAR16,
                C_BAR16, f"16mm bar along length — {lbl}"
            )

        nx = 7
        for i in range(nx):
            xb = ox + 0.06 + i * (COV_L - 0.12) / max(nx - 1, 1)
            box(
                fig, col,
                xb - BAR16/2, oy + 0.03, zc - BAR16/2,
                BAR16, COV_W - 0.06, BAR16,
                C_BAR16, f"16mm bar along width — {lbl}"
            )

def lifter_xs(ox):
    cx = ox + COV_L/2
    return [cx - LIFT_SPC/2, cx + LIFT_SPC/2]

def sleeves(fig, col, ox, oy, oz, lift=0.0):
    cy = oy + COV_W/2
    for lx in lifter_xs(ox):
        for yl in (cy - LEG_SPC/2, cy + LEG_SPC/2):
            box(
                fig, col,
                lx - SLEEVE/2, yl - SLEEVE/2, oz + lift,
                SLEEVE, SLEEVE, COV_T,
                C_PVC, "PVC sleeve", opacity=0.85
            )

def grooves(fig, col, ox, oy, oz):
    cy = oy + COV_W/2
    for lx in lifter_xs(ox):
        box(
            fig, col,
            lx - 0.035,
            cy - LEG_SPC/2 - 0.03,
            oz + COV_T - GROOVE_D,
            0.07,
            LEG_SPC + 0.06,
            GROOVE_D,
            C_GROOVE,
            "Groove — flush handle pocket",
        )

def lifter(fig, col, lx, oy, oz, raised=0.0):
    cy = oy + COV_W/2
    legs_y = (cy - LEG_SPC/2, cy + LEG_SPC/2)

    handle_z = oz + COV_T - GROOVE_D + raised
    leg_bot = oz - 0.06 + raised

    for yl in legs_y:
        box(
            fig, col,
            lx - BAR12/2, yl - BAR12/2, leg_bot,
            BAR12, BAR12, handle_z - leg_bot,
            C_LIFT, "12mm lifter leg"
        )
        box(
            fig, col,
            lx - NUT/2, yl - NUT/2, leg_bot,
            NUT, NUT, 0.018,
            C_NUT, "Double nuts + flat washer"
        )

    box(
        fig, col,
        lx - BAR12/2, legs_y[0], handle_z,
        BAR12, LEG_SPC, BAR12,
        C_LIFT, "12mm U-handle"
    )

def full_cover(fig, col, ox, oy, oz, lifter_raised=(0.0, 0.0)):
    box(
        fig, col,
        ox, oy, oz,
        COV_L, COV_W, COV_T,
        C_CONC,
        "Concrete cover",
        opacity=slab_opacity
    )

    ab_frame(fig, col, ox, oy, oz)
    rebar_mats(fig, col, ox, oy, oz)
    sleeves(fig, col, ox, oy, oz)
    grooves(fig, col, ox, oy, oz)

    for lx, r in zip(lifter_xs(ox), lifter_raised):
        lifter(fig, col, lx, oy, oz, raised=r)

# ============================================================
# BUILD FIGURE
# ============================================================
fig = make_subplots(
    rows=1,
    cols=3,
    specs=[[{"type": "scene"}] * 3],
    subplot_titles=(
        "Scene 1 — Exploded assembly",
        "Scene 2 — Assembled cover",
        "Scene 3 — Seated on canal",
    ),
    horizontal_spacing=0.01,
)

box(
    fig, 1, 0, 0, 0,
    COV_L, COV_W, COV_T,
    C_CONC, "Concrete body", opacity=0.20
)
ab_frame(fig, 1, 0, 0, 0, exploded=0.12)
rebar_mats(fig, 1, 0, 0, 0, lift=0.35)
sleeves(fig, 1, 0, 0, 0, lift=0.70)
grooves(fig, 1, 0, 0, 0)

for lx in lifter_xs(0):
    lifter(fig, 1, lx, 0, 0, raised=1.00)

full_cover(
    fig, 2, 0, 0, 0,
    lifter_raised=(0.0, raised_right),
)

CAN_L = 1.6

for y0, lbl in [
    (0.0, "LEFT"),
    (WALL_T + CLEAR_W, "RIGHT"),
]:
    box(
        fig, 3,
        0, y0, 0,
        CAN_L, WALL_T, WALL_H,
        C_CONC2, f"Canal wall {lbl}", opacity=0.90
    )

def seated_cover(fig, col, x0, z0, tag):
    oy = WALL_T - BEARING

    box(
        fig, col,
        x0, oy, z0,
        COV_W, COV_L, COV_T,
        C_CONC,
        f"{tag} correct orientation",
        opacity=0.95
    )

    box(
        fig, col,
        x0, oy, z0 + COV_T - AB_THK,
        COV_W, AB_LEG, AB_THK,
        C_AB, "Angle-bar bearing edge"
    )
    box(
        fig, col,
        x0, oy + COV_L - AB_LEG, z0 + COV_T - AB_THK,
        COV_W, AB_LEG, AB_THK,
        C_AB, "Angle-bar bearing edge"
    )

z_seat = WALL_H + SLAB_T - COV_T
seated_cover(fig, 3, 0.25, z_seat, "Cover 1")
seated_cover(fig, 3, 0.25 + COV_W, z_seat, "Cover 2")

axis_style = dict(
    aspectmode="data",
    xaxis=dict(title=dict(text="x (m)"), backgroundcolor="#f5f0e8"),
    yaxis=dict(title=dict(text="y (m)"), backgroundcolor="#efe8dc"),
    zaxis=dict(title=dict(text="z (m)"), backgroundcolor="#e8e0d0"),
    camera=dict(eye=dict(x=1.6, y=-1.6, z=1.0)),
)

fig.update_layout(
    scene=axis_style,
    scene2=axis_style,
    scene3=axis_style,
    height=650,
    margin=dict(l=0, r=0, t=60, b=0),
    title_text="EJR Concrete Canal Cover — Angle Bar Assembly",
)

try:
    st.plotly_chart(fig, use_container_width=True)
except Exception as exc:
    st.error("3D renderer failed. Reload the page or check the app logs.")
    st.exception(exc)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Cover Size", f"{COV_L:.2f} × {COV_W:.2f} × {COV_T:.2f} m")
c2.metric("Bearing / Side", f"{BEARING:.3f} m")
c3.metric("Lifter Spacing", f"{LIFT_SPC:.2f} m")
c4.metric("Leg Spacing", f"{LEG_SPC:.2f} m")

st.subheader("Field Assembly Notes")

st.markdown(
    """
1. Weld the 2 × 2 × 6 mm angle-bar perimeter frame.
2. Install the 16 mm top and bottom reinforcement mats.
3. Fix four PVC sleeves and form two recessed grooves.
4. Insert the two 12 mm sliding U-bar lifters.
5. Install double nuts and flat-bar washers below each lifter leg.
6. Verify that each lifter slides freely before concrete placement.
7. Place the 1.05 m side across the canal opening.
8. Maintain the required bearing on both canal walls.
"""
)

st.warning(
    "Visualizer only. Final bar spacing, welding, lifting capacity, "
    "wheel-load capacity, cover and dimensions must follow the approved plans."
)
