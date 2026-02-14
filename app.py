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
# TOP BARS UI
Top_Bars_Qty = st.sidebar.slider("Top Bars Qty (Total Positions)", 2, 10, 5)
Top_Bars_Size_mm = st.sidebar.number_input("Top Bars Size (mm)", value=20, key="t_size")
Top_Bundle_Type = st.sidebar.selectbox("Top Bundle Type", ["None", "2-Bar Bundle", "3-Bar Bundle"])
top_pos_list = [f"Pos {i+1}" for i in range(Top_Bars_Qty)]
Top_Bundle_Locs = st.sidebar.multiselect("Alin ang naka-Bundle? (Top)", top_pos_list, default=[top_pos_list[0], top_pos_list[-1]]) if Top_Bundle_Type != "None" else []

# BOTTOM BARS UI
Bottom_Bars_Qty = st.sidebar.slider("Bottom Bars Qty (Total Positions)", 2, 10, 5)
Bottom_Bars_Size_mm = st.sidebar.number_input("Bottom Bars Size (mm)", value=20, key="b_size")
Bottom_Bundle_Type = st.sidebar.selectbox("Bottom Bundle Type", ["None", "2-Bar Bundle", "3-Bar Bundle"])
bot_pos_list = [f"Pos {i+1}" for i in range(Bottom_Bars_Qty)]
Bottom_Bundle_Locs = st.sidebar.multiselect("Alin ang naka-Bundle? (Bot)", bot_pos_list, default=[bot_pos_list[0], bot_pos_list[-1]]) if Bottom_Bundle_Type != "None" else []"3-Bar Bundle"])

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

import math # Idagdag mo 'to sa itaas kung wala pa, pero pwede na rin dito.

inner_width = Width_mm - (2 * Concrete_Cover_mm) - (2 * Stirrup_Size_mm)

# Equivalent Diameter & Clear Spacing Logic for Top Bars
top_n = 2 if "2-Bar" in Top_Bundle_Type else (3 if "3-Bar" in Top_Bundle_Type else 1)
top_De = Top_Bars_Size_mm * math.sqrt(top_n) if top_n > 1 else Top_Bars_Size_mm
top_bundled_count = len(Top_Bundle_Locs)
top_single_count = Top_Bars_Qty - top_bundled_count
top_total_width = (top_bundled_count * top_De) + (top_single_count * Top_Bars_Size_mm)
top_clear_space = (inner_width - top_total_width) / max(1, (Top_Bars_Qty - 1)) if Top_Bars_Qty > 1 else inner_width

# Equivalent Diameter & Clear Spacing Logic for Bottom Bars
bot_n = 2 if "2-Bar" in Bottom_Bundle_Type else (3 if "3-Bar" in Bottom_Bundle_Type else 1)
bot_De = Bottom_Bars_Size_mm * math.sqrt(bot_n) if bot_n > 1 else Bottom_Bars_Size_mm
bot_bundled_count = len(Bottom_Bundle_Locs)
bot_single_count = Bottom_Bars_Qty - bot_bundled_count
bot_total_width = (bot_bundled_count * bot_De) + (bot_single_count * Bottom_Bars_Size_mm)
bot_clear_space = (inner_width - bot_total_width) / max(1, (Bottom_Bars_Qty - 1)) if Bottom_Bars_Qty > 1 else inner_width

stirrup_clear_space = Stirrup_Spacing_Support_mm - Stirrup_Size_mm 
tightest_space = min(top_clear_space, bot_clear_space, stirrup_clear_space)
required_clearance = Gravel_Size_mm * 1.33

bar_color_override = None
stirrup_color = 'blue'

st.subheader("🤖 AI DIAGNOSTICS")

# AI Symmetry Checker Logic
def check_sym(locs, qty):
    indices = [int(loc.split(" ")[1]) for loc in locs]
    return all((qty - i + 1) in indices for i in indices)

top_sym = check_sym(Top_Bundle_Locs, Top_Bars_Qty) if Top_Bundle_Locs else True
bot_sym = check_sym(Bottom_Bundle_Locs, Bottom_Bars_Qty) if Bottom_Bundle_Locs else True

if not top_sym or not bot_sym:
    st.warning("⚠️ WARLORD WARNING: Asymmetrical ang latag ng Bundled Bars mo! Baka pumilipit (Torsion) ang biga pag lumindol. I-balanse mo ang kaliwa at kanan!")
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

# --- ANG BAGONG SMART DRAWING FUNCTION ---
def draw_bars(qty, size, z_pos, label, color, bundle_type="None", bundled_locs=[]):
    off = size / 2.5 

    for i in range(qty):
        if qty > 1:
            y_center = Concrete_Cover_mm + Stirrup_Size_mm + (size/2) + i * ((inner_width - size)/(qty - 1))
        else:
            y_center = W / 2

        # Check kung kasama ang position na ito sa piniling i-bundle
        pos_label = f"Pos {i+1}"
        current_bundle = bundle_type if pos_label in bundled_locs else "None"
        
        # ... (YUNG REST NG FUNCTION AY SAME LANG KANINA, wag na baguhin) ...

        # 2. Check if Corner Position (Dito lang may bundle)
        is_corner = (i == 0 or i == qty - 1)
        current_bundle = bundle_type if is_corner else "None"

        # 3. Define Sub-Bar Coordinates based on Bundle Type
        sub_bars_coords = []
        if current_bundle == "3-Bar Bundle":
            # Triangle Formation
            sub_bars_coords = [
                (y_center, z_pos + off),        # Top-Center
                (y_center - off, z_pos - off),  # Bottom-Left
                (y_center + off, z_pos - off)   # Bottom-Right
            ]
        elif current_bundle == "2-Bar Bundle":
            # Side-by-Side Formation
            sub_bars_coords = [
                (y_center - off, z_pos),
                (y_center + off, z_pos)
            ]
        else:
            # Single Bar (Center)
            sub_bars_coords = [(y_center, z_pos)]

        # 4. Hover Text Logic (Para sa request mong specs display)
        bundle_tag = f" [{current_bundle}]" if current_bundle != "None" else ""
        hover_txt = f"<b>{label}{bundle_tag}</b><br>Size: {size}mm Ø<br>Spacing: {tightest_space:.1f}mm gap<extra></extra>"

        # 5. Draw the actual lines
        for y_final, z_final in sub_bars_coords:
            if Element_Type == "Beam":
                x_coords, y_coords, z_coords = [0, L], [y_final, y_final], [z_final, z_final]
            else: # Column
                x_coords, y_coords, z_coords = [y_final, y_final], [z_final, z_final], [0, L]

            fig.add_trace(go.Scatter3d(
                x=x_coords, y=y_coords, z=z_coords, mode='lines',
                line=dict(color=color, width=7), name=f"{label} ({size}mm Ø)",
                hovertemplate=hover_txt
            ))

# Colors
top_color = bar_color_override if bar_color_override else "green"
bot_color = bar_color_override if bar_color_override else "red"
extra_top_color = bar_color_override if bar_color_override else "magenta"
extra_bot_color = bar_color_override if bar_color_override else "orange"

# Main Bars
top_z = D - Concrete_Cover_mm - Stirrup_Size_mm - (Top_Bars_Size_mm/2)
bot_z = Concrete_Cover_mm + Stirrup_Size_mm + (Bottom_Bars_Size_mm/2)

draw_bars(Top_Bars_Qty, Top_Bars_Size_mm, top_z, "Top Bar", top_color, Top_Bundle_Type, Top_Bundle_Locs)
draw_bars(Bottom_Bars_Qty, Bottom_Bars_Size_mm, bot_z, "Bottom Bar", bot_color, Bottom_Bundle_Type, Bottom_Bundle_Locs)

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
