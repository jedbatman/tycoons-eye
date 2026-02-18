import streamlit as st
import plotly.graph_objects as go
import math

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Tycoon's Eye V2.0", layout="wide")

st.title("🏗️ TYCOON'S EYE V2.0 - MASTER INPUT FORM 🏗️")
st.markdown("**Powered by EJR Builders & Bender AI** | Bauninam Brgy. Engineer. Pota ka.")

# --- UI SIDEBAR ---
st.sidebar.header("1. ELEMENT DIMENSIONS")
Element_Type = st.sidebar.selectbox("Ano ang bubuhusan natin?", ["Beam", "Column"])
Width_mm = st.sidebar.number_input("Width (mm)", value=300)
Depth_or_Height_mm = st.sidebar.number_input("Depth/Height (mm)", value=500)
Length_or_Span_mm = st.sidebar.number_input("Length/Span (mm)", value=4000)
Concrete_Cover_mm = st.sidebar.number_input("Concrete Cover (mm)", value=40)

st.sidebar.header("2. MAIN BARS")
Top_Bars_Qty = st.sidebar.slider("Top Bars Qty (Total Positions)", 2, 10, 5)
Top_Bars_Size_mm = st.sidebar.number_input("Top Bars Size (mm)", value=20, key="t_size")
Top_Bundle_Type = st.sidebar.selectbox("Top Bundle Type", ["None", "2-Bar Bundle", "3-Bar Bundle"])
top_pos_list = [f"Pos {i+1}" for i in range(Top_Bars_Qty)]
Top_Bundle_Locs = st.sidebar.multiselect("Alin ang naka-Bundle? (Top)", top_pos_list, default=[top_pos_list[0], top_pos_list[-1]]) if Top_Bundle_Type != "None" else []

Bottom_Bars_Qty = st.sidebar.slider("Bottom Bars Qty (Total Positions)", 2, 10, 5)
Bottom_Bars_Size_mm = st.sidebar.number_input("Bottom Bars Size (mm)", value=20, key="b_size")
Bottom_Bundle_Type = st.sidebar.selectbox("Bottom Bundle Type", ["None", "2-Bar Bundle", "3-Bar Bundle"])
bot_pos_list = [f"Pos {i+1}" for i in range(Bottom_Bars_Qty)]
Bottom_Bundle_Locs = st.sidebar.multiselect("Alin ang naka-Bundle? (Bot)", bot_pos_list, default=[bot_pos_list[0], bot_pos_list[-1]]) if Bottom_Bundle_Type != "None" else []

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
inner_width = Width_mm - (2 * Concrete_Cover_mm) - (2 * Stirrup_Size_mm)

# --- WARLORD STIRRUP CALCULATOR (STEP 1 PATCH) ---
# Calculate dimensions
Stirrup_W = Width_mm - (2 * Concrete_Cover_mm)
Stirrup_H = Depth_or_Height_mm - (2 * Concrete_Cover_mm)
# Calculate hook length (6 * db or 75mm minimum, whichever is bigger)
Hook_Len = max(6 * Stirrup_Size_mm, 75)
# Calculate total cutting length (Perimeter + 2 hooks)
Total_Stirrup_Len = (2 * (Stirrup_W + Stirrup_H)) + (2 * Hook_Len)

# ... (Dito magpapatuloy ang mga computations mo para sa top_n, bot_n, etc.) ...
top_n = 2 if "2-Bar" in Top_Bundle_Type else (3 if "3-Bar" in Top_Bundle_Type else 1)

top_n = 2 if "2-Bar" in Top_Bundle_Type else (3 if "3-Bar" in Top_Bundle_Type else 1)
top_De = Top_Bars_Size_mm * math.sqrt(top_n) if top_n > 1 else Top_Bars_Size_mm
top_bundled_count = len(Top_Bundle_Locs)
top_single_count = Top_Bars_Qty - top_bundled_count
top_total_width = (top_bundled_count * top_De) + (top_single_count * Top_Bars_Size_mm)
top_clear_space = (inner_width - top_total_width) / max(1, (Top_Bars_Qty - 1)) if Top_Bars_Qty > 1 else inner_width

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

def draw_bars(qty, size, z_pos, label, color, bundle_type="None", bundled_locs=[]):
    off = size / 2.5 
    L_cut = L / 3  # THE WARLORD L/3 CUT-OFF LOGIC

    for i in range(qty):
        if qty > 1:
            y_center = Concrete_Cover_mm + Stirrup_Size_mm + (size/2) + i * ((inner_width - size)/(qty - 1))
        else:
            y_center = W / 2

        # Check kung kasama ang position na ito sa piniling i-bundle
        pos_label = f"Pos {i+1}"
        current_bundle = bundle_type if pos_label in bundled_locs else "None"

        # --- THE WARLORD CUTTING & LENGTH CALCULATION LOGIC ---
        length_str = "" # Dito natin i-i-store yung haba na babasahin ni Foreman

        if label == "Top Bar" and qty > 2:
            if i == 0 or i == qty - 1:
                # Corner Bars: Tuloy-tuloy mula dulo hanggang dulo
                x_segments = [[0, L]]
                length_str = f"Full Span ({L:.0f}mm)"
            else:
                # Inner Top Bars: Putol sa L/3 sa magkabilang dulo
                x_segments = [[0, L_cut], [L - L_cut, L]]
                length_str = f"L/3 Cut ({L_cut:.0f}mm from support)"
        elif label == "Extra Top Bar":
            # Extra Top Bars: Putol din sa L/3
            x_segments = [[0, L_cut], [L - L_cut, L]]
            length_str = f"L/3 Cut ({L_cut:.0f}mm from support)"
        else:
            # Bottom Bars at Columns: Tuloy-tuloy muna
            x_segments = [[0, L]]
            length_str = f"Full Span ({L:.0f}mm)"

        sub_bars_coords = []
        if current_bundle == "3-Bar Bundle":
            sub_bars_coords = [
                (y_center, z_pos + off),        
                (y_center - off, z_pos - off),  
                (y_center + off, z_pos - off)   
            ]
        elif current_bundle == "2-Bar Bundle":
            sub_bars_coords = [
                (y_center - off, z_pos),
                (y_center + off, z_pos)
            ]
        else:
            sub_bars_coords = [(y_center, z_pos)]

        bundle_tag = f" [{current_bundle}]" if current_bundle != "None" else ""
        
        # --- THE NEW WARLORD HOVER TEXT (ANDITO YUNG MAGIC!) ---
        hover_txt = f"<b>{label}{bundle_tag}</b><br>Size: {size}mm Ø<br>Length: {length_str}<br>Spacing: {tightest_space:.1f}mm gap<extra></extra>"

        # Plotting the coordinates (Ngayon, kasama na ang length pag nag-hover!)
        for y_final, z_final in sub_bars_coords:
            for x_segment in x_segments:
                if Element_Type == "Beam":
                    x_coords, y_coords, z_coords = x_segment, [y_final, y_final], [z_final, z_final]
                else: 
                    x_coords, y_coords, z_coords = [y_final, y_final], [z_final, z_final], x_segment

                fig.add_trace(go.Scatter3d(
                    x=x_coords, y=y_coords, z=z_coords, mode='lines',
                    line=dict(color=color, width=7), name=f"{label} ({size}mm Ø)",
                    hovertemplate=hover_txt
                ))

top_color = bar_color_override if bar_color_override else "green"
bot_color = bar_color_override if bar_color_override else "red"
extra_top_color = bar_color_override if bar_color_override else "magenta"
extra_bot_color = bar_color_override if bar_color_override else "orange"

top_z = D - Concrete_Cover_mm - Stirrup_Size_mm - (Top_Bars_Size_mm/2)
bot_z = Concrete_Cover_mm + Stirrup_Size_mm + (Bottom_Bars_Size_mm/2)

draw_bars(Top_Bars_Qty, Top_Bars_Size_mm, top_z, "Top Bar", top_color, Top_Bundle_Type, Top_Bundle_Locs)
draw_bars(Bottom_Bars_Qty, Bottom_Bars_Size_mm, bot_z, "Bottom Bar", bot_color, Bottom_Bundle_Type, Bottom_Bundle_Locs)

spacer_gap = 25
if Extra_Top_Bars_Qty > 0:
    draw_bars(Extra_Top_Bars_Qty, Extra_Top_Bars_Size_mm, top_z - (Top_Bars_Size_mm/2) - spacer_gap - (Extra_Top_Bars_Size_mm/2), "Extra Top Bar", extra_top_color)
if Extra_Bottom_Bars_Qty > 0:
    draw_bars(Extra_Bottom_Bars_Qty, Extra_Bottom_Bars_Size_mm, bot_z + (Bottom_Bars_Size_mm/2) + spacer_gap + (Extra_Bottom_Bars_Size_mm/2), "Extra Bottom Bar", extra_bot_color)

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

# ... (Pagkatapos ng lahat ng code para sa main `fig`, pero BAGO ang st.markdown("---")) ...

# --- 3D STIRRUP ASSEMBLY VISUALIZER ---
fig_stirrup = go.Figure()

# 1. WARLORD CONCRETE OUTLINE (Pinalitan ng Dashed Lines para 100% kita ang Concrete Cover!)
cx = [0, Width_mm, Width_mm, 0, 0]
cy = [0, 0, Depth_or_Height_mm, Depth_or_Height_mm, 0]
cz = [Stirrup_Size_mm*2.5] * 5

fig_stirrup.add_trace(go.Scatter3d(
    x=cx, y=cy, z=cz, mode='lines',
    line=dict(color='gray', width=4, dash='dash'),
    name='Concrete Edge', hoverinfo='skip'
))

# 2. MAIN STIRRUP BODY (Blue Anilyo)
sx_coords = [Concrete_Cover_mm, Width_mm - Concrete_Cover_mm, Width_mm - Concrete_Cover_mm, Concrete_Cover_mm, Concrete_Cover_mm]
sy_coords = [Concrete_Cover_mm, Concrete_Cover_mm, Depth_or_Height_mm - Concrete_Cover_mm, Depth_or_Height_mm - Concrete_Cover_mm, Concrete_Cover_mm]
sz_coords = [Stirrup_Size_mm*2.5] * 5 

stirrup_hover = f"<b>Main Stirrup Body</b><br>Size: {Stirrup_Size_mm}mm Ø<br>Outer Dim: {Stirrup_W:.0f}mm x {Stirrup_H:.0f}mm<extra></extra>"
fig_stirrup.add_trace(go.Scatter3d(x=sx_coords, y=sy_coords, z=sz_coords, mode='lines+text', line=dict(color='blue', width=10), name='Anilyo Body', hovertemplate=stirrup_hover))

# 3. REALISTIC 135-DEGREE HOOKS (Inayos ang Bend Offset para hindi Ipit!)
corner_x = Width_mm - Concrete_Cover_mm
corner_y = Depth_or_Height_mm - Concrete_Cover_mm

# Hook 1 (Galing sa Top Bar, papasok) - Inatras nang kaunti sa X-axis
h1x = [corner_x - (Stirrup_Size_mm * 1.5), corner_x - (Hook_Len * 0.707)] 
h1y = [corner_y, corner_y - (Hook_Len * 0.707)]
h1z = [Stirrup_Size_mm*2.5, Stirrup_Size_mm*2.5 + Stirrup_Size_mm]
fig_stirrup.add_trace(go.Scatter3d(x=h1x, y=h1y, z=h1z, mode='lines', line=dict(color='red', width=8), name='135° Hook', hoverinfo='skip'))

# Hook 2 (Galing sa Right Bar, papasok) - Inatras nang kaunti sa Y-axis
h2x = [corner_x, corner_x - (Hook_Len * 0.85)]
h2y = [corner_y - (Stirrup_Size_mm * 1.5), corner_y - (Hook_Len * 0.5)]
h2z = [Stirrup_Size_mm*2.5, Stirrup_Size_mm*2.5 - Stirrup_Size_mm]
fig_stirrup.add_trace(go.Scatter3d(x=h2x, y=h2y, z=h2z, mode='lines', line=dict(color='red', width=8), name='135° Hook', showlegend=False, hoverinfo='skip'))

# 4. LAYOUT UPDATE (Nilagyan ng extra "padding" sa camera para kita ang cover!)
fig_stirrup.update_layout(
    title=f"<b>STIRRUP ASSEMBLY GUIDE</b><br>Total Cut Length: <span style='color:blue'>{Total_Stirrup_Len:.0f}mm</span><br>Hook Length (H.L.): {Hook_Len:.0f}mm (135°)",
    scene=dict(
        aspectmode='data', 
        xaxis=dict(title="Width (mm)", visible=False, range=[-50, Width_mm + 50]), # EXTRA PADDING DITO!
        yaxis=dict(title="Depth (mm)", visible=False, range=[-50, Depth_or_Height_mm + 50]), # EXTRA PADDING DITO!
        zaxis=dict(title="", visible=False, range=[0, Stirrup_Size_mm*10]), 
        camera=dict(eye=dict(x=0, y=0.1, z=2.5))
    ),
    margin=dict(l=0, r=0, b=0, t=80), showlegend=True
)

# =========================================================
# THE TYCOON QUIRK: DUAL-VIEW DASHBOARD 📺📺
# =========================================================
st.markdown("---")
st.subheader("📺 THE TYCOON'S DUAL-VIEW DASHBOARD")
st.markdown("*I-lock ang isang screen sa Isometric View, at yung isa sa Top/Side view para walang kawala ang foreman!*")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig, use_container_width=True, key="view_1_main")
with col2:
    st.plotly_chart(fig, use_container_width=True, key="view_2_main")

st.markdown("---")
st.subheader("🔨 STEELMAN'S CORNER: STIRRUP ASSEMBLY GUIDE")
st.markdown("*Ito ang gayahin ng latero. Bawal ang 90-degrees na hook sa seismic zone!*")
st.plotly_chart(fig_stirrup, use_container_width=True, key="view_3_stirrup")
