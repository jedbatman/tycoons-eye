import streamlit as st
import plotly.graph_objects as go

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Tycoon's Eye - Slab & Footing", layout="wide")

st.title("🏗️ MODULE 2: SLAB & FOOTING VISUALIZER")
st.markdown("**Powered by EJR Builders & Bender AI** | Losa at Zapatas Division")

# ==========================================
# 1. UI FORM INPUTS
# ==========================================
st.sidebar.header("1. ELEMENT DIMENSIONS")
Element_Type = st.sidebar.selectbox("Ano ang bubuhusan natin?", ["Slab", "Footing"])
Mat_Type = st.sidebar.selectbox("Mat Type", ["Single Mat (Bottom Only)", "Double Mat (Top & Bottom)"])
Length_X_mm = st.sidebar.number_input("Length X (mm)", value=4000)
Width_Y_mm = st.sidebar.number_input("Width Y (mm)", value=3000)
Thickness_Z_mm = st.sidebar.number_input("Thickness Z (mm)", value=150)
Concrete_Cover_mm = st.sidebar.number_input("Concrete Cover (mm)", value=20)

st.sidebar.header("2. BAKAL SPECS (MESH / MAT)")
Bar_Size_mm = st.sidebar.number_input("Bar Size (mm)", value=10)
Spacing_X_Axis_mm = st.sidebar.number_input("Spacing X Axis (mm)", value=200)
Spacing_Y_Axis_mm = st.sidebar.number_input("Spacing Y Axis (mm)", value=200)

st.sidebar.header("3. BATO (AGGREGATE) CHECKER")
Aggregate_Type = st.sidebar.selectbox("Aggregate Size", ["3/4 inch (20mm)", "G1 (25mm)"])

# ==========================================
# 2. THE HONEYCOMB PREVENTER LOGIC (SLAB EDITION) 🧠
# ==========================================
Gravel_Size_mm = 20 if "20mm" in Aggregate_Type else 25
required_clearance = Gravel_Size_mm * 1.33

clear_x = Spacing_X_Axis_mm - Bar_Size_mm
clear_y = Spacing_Y_Axis_mm - Bar_Size_mm
tightest_space = min(clear_x, clear_y)

bar_color_bot = "green"
bar_color_top = "magenta"

st.subheader("🤖 AI DIAGNOSTICS & BEHAVIOR CHECK")

if tightest_space >= required_clearance:
    status = "PASSED"
    status_display = f"<span style='color:green'>PASSED ✅ KASYA ANG {Aggregate_Type}!</span>"
else:
    status = "FAILED"
    status_display = f"<span style='color:red'>FAILED ❌ DANGER! Mag-aampaw! Hindi kasya ang {Aggregate_Type}.</span>"
    bar_color_bot = "red"
    bar_color_top = "red"

# SLAB BEHAVIOR LOGIC (One-Way vs Two-Way Checker)
if Element_Type == "Slab":
    long_span = max(Length_X_mm, Width_Y_mm)
    short_span = min(Length_X_mm, Width_Y_mm)
    slab_ratio = long_span / short_span

    if slab_ratio > 2.0:
        slab_type = f"ONE-WAY SLAB (Ratio: {slab_ratio:.2f})"
        advise_msg = f"Main Bars: Nakalatag sa Short Span ({short_span}mm)"
    else:
        slab_type = f"TWO-WAY SLAB (Ratio: {slab_ratio:.2f})"
        advise_msg = "Main Bars: Nakalatag in BOTH directions."
else:
    slab_type = "ISOLATED FOOTING"
    advise_msg = "Load distributed to the ground."

# DIAGNOSTICS DISPLAY
if status == "PASSED":
    st.success(f"✅ CLEARANCE PASSED: Uwang ng lambat ay {tightest_space}mm.")
else:
    st.error(f"❌ CLEARANCE FAILED: Uwang ay {tightest_space}mm lang. Hindi lulusot ang bato!")

st.info(f"📐 **STRUCTURAL BEHAVIOR:** {slab_type} | **ADVISE:** {advise_msg}")

# ==========================================
# 3. 3D SLAB/FOOTING VISUALIZATION ENGINE 👁️
# ==========================================
fig = go.Figure()

# A. DRAW CONCRETE (Ghost Mode)
fig.add_trace(go.Mesh3d(
    x=[0, Length_X_mm, Length_X_mm, 0, 0, Length_X_mm, Length_X_mm, 0],
    y=[0, 0, Width_Y_mm, Width_Y_mm, 0, 0, Width_Y_mm, Width_Y_mm],
    z=[0, 0, 0, 0, Thickness_Z_mm, Thickness_Z_mm, Thickness_Z_mm, Thickness_Z_mm],
    color='lightblue', opacity=0.15, name='Concrete Form', hoverinfo='none'
))

# B. DRAW THE MESH (Lambat ng Bakal)
x_bars = list(range(int(Concrete_Cover_mm), int(Length_X_mm - Concrete_Cover_mm) + 1, int(Spacing_X_Axis_mm)))
y_bars = list(range(int(Concrete_Cover_mm), int(Width_Y_mm - Concrete_Cover_mm) + 1, int(Spacing_Y_Axis_mm)))

def draw_mat(z_x, z_y, color, label_prefix):
    for y_pos in y_bars:
        fig.add_trace(go.Scatter3d(
            x=[Concrete_Cover_mm, Length_X_mm - Concrete_Cover_mm], 
            y=[y_pos, y_pos], z=[z_x, z_x], 
            mode='lines', line=dict(color=color, width=6), name=f"{label_prefix} Bar (X)",
            hovertemplate=f"<b>{label_prefix} Bar (X)</b><br>Size: {Bar_Size_mm}mm Ø<br>Spacing: {Spacing_Y_Axis_mm}mm<extra></extra>"
        ))
    for x_pos in x_bars:
        fig.add_trace(go.Scatter3d(
            x=[x_pos, x_pos], 
            y=[Concrete_Cover_mm, Width_Y_mm - Concrete_Cover_mm], z=[z_y, z_y], 
            mode='lines', line=dict(color=color, width=6), name=f"{label_prefix} Bar (Y)",
            hovertemplate=f"<b>{label_prefix} Bar (Y)</b><br>Size: {Bar_Size_mm}mm Ø<br>Spacing: {Spacing_X_Axis_mm}mm<extra></extra>"
        ))

# Bottom Mat
z_bottom_x = Concrete_Cover_mm + (Bar_Size_mm / 2)
z_bottom_y = z_bottom_x + Bar_Size_mm
draw_mat(z_bottom_x, z_bottom_y, bar_color_bot, "Bottom")

# Top Mat
if Mat_Type == "Double Mat (Top & Bottom)":
    z_top_x = Thickness_Z_mm - Concrete_Cover_mm - (Bar_Size_mm / 2)
    z_top_y = z_top_x - Bar_Size_mm
    draw_mat(z_top_x, z_top_y, bar_color_top, "Top")

# D. FORMATTING THE 3D VIEW
title_text = f"<b>{Element_Type} ASSEMBLY: {slab_type} ({Mat_Type})</b><br>{status_display}<br>Pinakamasikip na Uwang: {tightest_space}mm"

fig.update_layout(
    title=title_text,
    scene=dict(
        xaxis_title='Length X (mm)',
        yaxis_title='Width Y (mm)',
        zaxis_title='Thickness Z (mm)',
        aspectmode='data'
    ),
    margin=dict(l=0, r=0, b=0, t=80)
)

st.markdown("---")
st.subheader("📺 THE TYCOON'S DUAL-VIEW DASHBOARD")
st.plotly_chart(fig, use_container_width=True, key="view_1")
st.plotly_chart(fig, use_container_width=True, key="view_2")
