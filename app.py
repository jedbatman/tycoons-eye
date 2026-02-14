import streamlit as st
import plotly.graph_objects as go

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Tycoon's Eye V2.0", layout="wide")

st.title("🏗️ TYCOON'S EYE V2.0 - MASTER INPUT FORM 🏗️")
st.markdown("**Powered by EJR Builders & Bender AI** | Bauninam Brgy. Engineer. Pota ka.")

# --- UI SIDEBAR (ITO YUNG PUMALIT SA COLAB #@PARAM) ---
st.sidebar.header("1. ELEMENT DIMENSIONS")
Element_Type = st.sidebar.selectbox("Ano ang bubuhusan natin?", ["Beam", "Column"])
Width_mm = st.sidebar.number_input("Width (mm)", value=300)
Depth_or_Height_mm = st.sidebar.number_input("Depth/Height (mm)", value=500)
Length_or_Span_mm = st.sidebar.number_input("Length/Span (mm)", value=4000)
Concrete_Cover_mm = st.sidebar.number_input("Concrete Cover (mm)", value=40)

st.sidebar.header("2. MAIN BARS")
Top_Bars_Qty = st.sidebar.slider("Top Bars Qty (Total Positions)", 2, 10, 3)
Top_Bars_Size_mm = st.sidebar.number_input("Top Bars Size (mm)", value=20)
Top_Bundle_Type = st.sidebar.selectbox("Top Corner Bundles?", ["None", "2-Bar Bundle", "3-Bar Bundle"])

Bottom_Bars_Qty = st.sidebar.slider("Bottom Bars Qty (Total Positions)", 2, 10, 3)
Bottom_Bars_Size_mm = st.sidebar.number_input("Bottom Bars Size (mm)", value=20)
Bottom_Bundle_Type = st.sidebar.selectbox("Bottom Corner Bundles?", ["None", "2-Bar Bundle", "3-Bar Bundle"])

st.sidebar.header("3. EXTRA LAYER BARS")
Extra_Top_Bars_Qty = st.sidebar.slider("Extra Top Bars Qty", 0, 10, 2)
Extra_Top_Bars_Size_mm = st.sidebar.number_input("Extra Top Bars Size (mm)", value=20)
Extra_Bottom_Bars_Qty = st.sidebar.slider("Extra Bottom Bars Qty", 0, 10, 2)
Extra_Bottom_Bars_Size_mm = st.sidebar.number_input("Extra Bottom Bars Size (mm)", value=20)

st.sidebar.header("4. ANILYO & BATO")
Stirrup_Size_mm = st.sidebar.number_input("Stirrup Size (mm)", value=10)
Stirrup_Spacing_Support_mm = st.sidebar.number_input("Support Spacing (mm) [L/4]", value=100)
Stirrup_Spacing_Midspan_mm = st.sidebar.number_input("Midspan Spacing (mm)", value=150)
Aggregate_Type = st.sidebar.selectbox("Aggregate Size", ["3/4 inch (20mm)", "G1 (25mm)", "G1.5 (38mm)"])

# --- HONEYCOMB LOGIC (ANG UTAK NG AI) ---
Gravel_Size_mm = 20 if "20mm" in Aggregate_Type else (25 if "25mm" in Aggregate_Type else 38)

import math # Idagdag sa logic

inner_width = Width_mm - (2 * Concrete_Cover_mm) - (2 * Stirrup_Size_mm)

# Equivalent Diameter Logic for Top Bars
top_n = 1 if Top_Bundle_Type == "None" else (2 if "2-Bar" in Top_Bundle_Type else 3)
top_De = Top_Bars_Size_mm * math.sqrt(top_n)
# Dalawang kanto ang bundled (2 * top_De), yung gitna ay single bars ((Qty - 2) * Size)
top_total_width = (2 * top_De) + ((Top_Bars_Qty - 2) * Top_Bars_Size_mm) if Top_Bars_Qty > 1 else top_De
top_clear_space = (inner_width - top_total_width) / max(1, (Top_Bars_Qty - 1)) if Top_Bars_Qty > 1 else inner_width

# Equivalent Diameter Logic for Bottom Bars
bot_n = 1 if Bottom_Bundle_Type == "None" else (2 if "2-Bar" in Bottom_Bundle_Type else 3)
bot_De = Bottom_Bars_Size_mm * math.sqrt(bot_n)
bot_total_width = (2 * bot_De) + ((Bottom_Bars_Qty - 2) * Bottom_Bars_Size_mm) if Bottom_Bars_Qty > 1 else bot_De
bot_clear_space = (inner_width - bot_total_width) / max(1, (Bottom_Bars_Qty - 1)) if Bottom_Bars_Qty > 1 else inner_width

stirrup_clear_space = Stirrup_Spacing_Support_mm - Stirrup_Size_mm

tightest_space = min(top_clear_space, bot_clear_space, stirrup_clear_space)
required_clearance = Gravel_Size_mm * 1.33 

bar_color_override = None
stirrup_color = 'blue'

st.subheader("🤖 AI DIAGNOSTICS")
if tightest_space >= required_clearance:
    st.success(f"PASSED ✅ KASYA ANG {Aggregate_Type}! Walang Honeycomb. Pinakamasikip na uwang ay {tightest_space:.1f}mm.")
    status = "PASSED"
else:
    if tightest_space == stirrup_clear_space:
        st.error(f"FAILED ❌ DANGER: MASYADONG SINSIN ANG ANILYO! Uwang ay {tightest_space:.1f}mm lang. Hindi lulusot ang {Aggregate_Type}!")
        stirrup_color = 'red'
    else:
        st.error(f"FAILED ❌ DANGER: MASYADONG SIKIP ANG MAIN BARS! Uwang ay {tightest_space:.1f}mm lang. Hindi kasya ang {Aggregate_Type}!")
        bar_color_override = 'red'
    status = "FAILED"

# --- 3D VISUALIZER ENGINE ---
fig = go.Figure()
if Element_Type == "Beam":
    L, W, D = Length_or_Span_mm, Width_mm, Depth_or_Height_mm
else:
    W, D, L = Width_mm, Depth_or_Height_mm, Length_or_Span_mm

# Concrete Form
fig.add_trace(go.Mesh3d(
    x=[0, L, L, 0, 0, L, L, 0] if Element_Type=="Beam" else [0, W, W, 0, 0, W, W, 0],
    y=[0, 0, W, W, 0, 0, W, W] if Element_Type=="Beam" else [0, 0, D, D, 0, 0, D, D],
    z=[0, 0, 0, 0, D, D, D, D] if Element_Type=="Beam" else [0, 0, 0, 0, L, L, L, L],
    color='lightblue', opacity=0.15, name='Concrete Form', hoverinfo='none'
))

def draw_bars(qty, size, z_pos, label, color):
    for i in range(qty):
        y_pos = Concrete_Cover_mm + Stirrup_Size_mm + (size/2) + i * ((inner_width - size)/(qty - 1)) if qty > 1 else W / 2
        if Element_Type == "Beam":
            x_coords, y_coords, z_coords = [0, L], [y_pos, y_pos], [z_pos, z_pos]
        else: 
            x_coords, y_coords, z_coords = [y_pos, y_pos], [z_pos, z_pos], [0, L]
        fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords, mode='lines', line=dict(color=color, width=7), name=f"{label} ({size}mm Ø)",
            hovertemplate=f"<b>{label}</b><br>Size: {size}mm Ø<br>Spacing: {tightest_space:.1f}mm gap<extra></extra>"
        ))

# Colors
top_color = bar_color_override if bar_color_override else "green"
bot_color = bar_color_override if bar_color_override else "red"
extra_top_color = bar_color_override if bar_color_override else "magenta"
extra_bot_color = bar_color_override if bar_color_override else "orange"

# Main Bars
top_z = D - Concrete_Cover_mm - Stirrup_Size_mm - (Top_Bars_Size_mm/2)
bot_z = Concrete_Cover_mm + Stirrup_Size_mm + (Bottom_Bars_Size_mm/2)
draw_bars(Top_Bars_Qty, Top_Bars_Size_mm, top_z, "Top Bar", top_color)
draw_bars(Bottom_Bars_Qty, Bottom_Bars_Size_mm, bot_z, "Bottom Bar", bot_color)

# Extra Bars
spacer_gap = 25
if Extra_Top_Bars_Qty > 0:
    draw_bars(Extra_Top_Bars_Qty, Extra_Top_Bars_Size_mm, top_z - (Top_Bars_Size_mm/2) - spacer_gap - (Extra_Top_Bars_Size_mm/2), "Extra Top Bar", extra_top_color)
if Extra_Bottom_Bars_Qty > 0:
    draw_bars(Extra_Bottom_Bars_Qty, Extra_Bottom_Bars_Size_mm, bot_z + (Bottom_Bars_Size_mm/2) + spacer_gap + (Extra_Bottom_Bars_Size_mm/2), "Extra Bottom Bar", extra_bot_color)

# Stirrups (L/4 Zoned Logic)
L_quarter = Length_or_Span_mm / 4
stirrup_x = []
current_x = Concrete_Cover_mm
while current_x <= L_quarter:
    stirrup_x.append(current_x)
    current_x += Stirrup_Spacing_Support_mm
current_x = stirrup_x[-1] + Stirrup_Spacing_Midspan_mm 
while current_x < Length_or_Span_mm - L_quarter:
    stirrup_x.append(current_x)
    current_x += Stirrup_Spacing_Midspan_mm
current_x = stirrup_x[-1] + Stirrup_Spacing_Support_mm 
while current_x <= Length_or_Span_mm - Concrete_Cover_mm:
    stirrup_x.append(current_x)
    current_x += Stirrup_Spacing_Support_mm

for x_pos in stirrup_x:
    if x_pos <= L_quarter or x_pos >= Length_or_Span_mm - L_quarter:
        current_spacing_text = f"{Stirrup_Spacing_Support_mm}mm O.C. (Support Zone)"
    else:
        current_spacing_text = f"{Stirrup_Spacing_Midspan_mm}mm O.C. (Midspan Zone)"

    if Element_Type == "Beam":
        sy = [Concrete_Cover_mm, W - Concrete_Cover_mm, W - Concrete_Cover_mm, Concrete_Cover_mm, Concrete_Cover_mm]
        sz = [Concrete_Cover_mm, Concrete_Cover_mm, D - Concrete_Cover_mm, D - Concrete_Cover_mm, Concrete_Cover_mm]
        sx = [x_pos] * 5
    else:
        sx = [Concrete_Cover_mm, W - Concrete_Cover_mm, W - Concrete_Cover_mm, Concrete_Cover_mm, Concrete_Cover_mm]
        sy = [Concrete_Cover_mm, Concrete_Cover_mm, D - Concrete_Cover_mm, D - Concrete_Cover_mm, Concrete_Cover_mm]
        sz = [x_pos] * 5
    fig.add_trace(go.Scatter3d(x=sx, y=sy, z=sz, mode='lines', line=dict(color=stirrup_color, width=4), showlegend=False, name="Anilyo", hovertemplate=f"<b>Stirrup (Anilyo)</b><br>Size: {Stirrup_Size_mm}mm Ø<br>Spacing: {current_spacing_text}<extra></extra>"))

# --- ANG BAGONG EMBEDDED TITLE PATCH ---
if Element_Type == "Beam":
    title_text = f"BEAM ASSEMBLY (Span: {Length_or_Span_mm}mm)"
else:
    title_text = f"COLUMN ASSEMBLY (Height: {Length_or_Span_mm}mm)"

if status == "PASSED":
    status_display = f"<span style='color:green'>PASSED ✅ Walang Honeycomb! Kasya ang {Aggregate_Type}.</span>"
else:
    status_display = f"<span style='color:red'>FAILED ❌ DANGER! Mag-aampaw! Hindi kasya ang {Aggregate_Type}.</span>"

fig.update_layout(
    title=f"<b>{title_text}</b><br>{status_display}<br>Pinakamasikip na Uwang: {tightest_space:.1f}mm",
    scene=dict(aspectmode='data'), 
    margin=dict(l=0, r=0, b=0, t=80) 
)

# =========================================================
# THE TYCOON QUIRK: DUAL-VIEW DASHBOARD 📺📺
# =========================================================
st.markdown("---")
st.subheader("📺 THE TYCOON'S DUAL-VIEW DASHBOARD")
st.markdown("*I-lock ang isang screen sa Isometric View, at yung isa sa Top/Side view para walang kawala ang foreman!*")

# First View
st.plotly_chart(fig, use_container_width=True, key="view_1")

# Second View (Ang paborito mong quirk!)
st.plotly_chart(fig, use_container_width=True, key="view_2")
