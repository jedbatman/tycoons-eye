import bpy
import math

# =============================================================================
# EJR BUILDERS & CONSTRUCTION SUPPLY
# Connecting Canopy — Warren Truss 3D Generator (REV 13)
# =============================================================================

# ---------------------------------------------------------------- PARAMETERS
SPAN_X      = 8.0
BAYS        = 8
FRAMES      = 3
TRUSS_SPACING = 4.0
COL_L_H     = 3.2
COL_R_H     = 4.5
TRUSS_DEPTH = 0.50

COL_SIZE    = 0.35

L_CHORD_LEG = 0.0635
L_CHORD_T   = 0.00635
L_WEB_LEG   = 0.0508
L_WEB_T     = 0.00476

LC_H, LC_F, LC_LIP, LC_T = 0.150, 0.050, 0.015, 0.0015

GUSSET_T    = 0.006
DBL_GAP     = 0.006
GUSSET_REACH= 0.16

ROOF_T      = 0.0005
WAVE_PITCH  = 0.076
WAVE_AMP    = 0.018
WAVE_STEPS  = 16
ROOF_SEAT   = 0.006

PURLIN_SPACING = 0.60

ANNOTATE    = True
BLUEPRINT   = False
TXT_SIZE    = 0.40
TICK        = 0.15
DIM_OFF_B   = 2.0
DIM_OFF_T   = 2.5
ANNO_Y      = -1.50

RUN_Y       = (FRAMES - 1) * TRUSS_SPACING
PURLINS     = int(math.ceil(SPAN_X / PURLIN_SPACING)) + 1
PURLIN_LEN  = RUN_Y + 0.30

# ---------------------------------------------------------------- SCENE WIPE
def wipe_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)

wipe_scene()

# ---------------------------------------------------------------- MATERIALS
def make_material(name, hex_color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    h = hex_color.lstrip("#")
    srgb = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    for key, val in (("Metallic", metallic), ("Roughness", roughness)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = val
    mat.diffuse_color = (*lin, 1.0)
    return mat

def make_emission_material(name, hex_color, strength=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    h = hex_color.lstrip("#")
    srgb = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]

    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
        if "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*lin, 1.0)
        elif "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*lin, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = strength
    mat.diffuse_color = (*lin, 1.0)
    return mat

MAT_STEEL = make_material("Steel_Slate_Grey",  "#334155", 0.90, 0.42)
MAT_GALV  = make_material("Galvanized_Silver", "#cbd5e1", 0.85, 0.30)
MAT_ROOF  = make_material("Prepainted_Red",    "#dc2626", 0.35, 0.45)
MAT_CONC  = make_material("Concrete_Column",   "#9aa1ab", 0.00, 0.85)

MAT_TEXT_ORANGE = make_emission_material("Text_Neon_Orange", "#FF6B00", 1.0)
MAT_TEXT_WHITE  = make_emission_material("Text_Bright_White", "#FFFFFF", 1.0)

# ---------------------------------------------------------------- MESH CORE
def build_object(name, verts, faces, material, location=(0, 0, 0), rotation=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = rotation
    mesh.materials.append(material)
    bpy.context.collection.objects.link(obj)
    return obj

def sweep_profile(profile, length):
    n = len(profile)
    half = length / 2.0
    verts = [(-half, y, z) for (y, z) in profile] + [( half, y, z) for (y, z) in profile]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    return verts, faces

def plate_xz(points_xz, thickness):
    n = len(points_xz)
    ht = thickness / 2.0
    verts = [(px, -ht, pz) for (px, pz) in points_xz] + [(px,  ht, pz) for (px, pz) in points_xz]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return verts, faces

def L_angle_pair(leg, t, gap, flip_z=False):
    base = [(0.0, 0.0), (leg, 0.0), (leg, t), (t, t), (t, leg), (0.0, leg)]
    cz = leg * 0.30
    left, right = [], []
    for (y, z) in base:
        zz = -(z - cz) if flip_z else (z - cz)
        right.append((y + gap / 2.0, zz))
        left.append((-(y + gap / 2.0), zz))
    if flip_z:
        right = right[::-1]
    else:
        left = left[::-1]
    return [right, left]

def C_purlin_profile(h, f, lip, t):
    hh = h / 2.0
    return [
        (0.0,   -hh), (f,     -hh), (f,     -hh + lip), (f - t, -hh + lip),
        (f - t, -hh + t), (t,  -hh + t), (t,      hh - t), (f - t,  hh - t),
        (f - t,  hh - lip), (f,  hh - lip), (f,      hh), (0.0,    hh),
    ]

def rotate_profile(profile, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [(y * c - z * s, y * s + z * c) for (y, z) in profile]

def box_verts_faces(sx, sy, sz):
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    verts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
             (-hx, -hy,  hz), (hx, -hy,  hz), (hx, hy,  hz), (-hx, hy,  hz)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
    return verts, faces

def member_between(name, p1, p2, profile, material, y_offset=0.0):
    x1, z1 = p1
    x2, z2 = p2
    length = math.hypot(x2 - x1, z2 - z1)
    if length < 1e-6:
        return None
    verts, faces = sweep_profile(profile, length)
    pitch = -math.atan2(z2 - z1, x2 - x1)
    loc = ((x1 + x2) / 2.0, y_offset, (z1 + z2) / 2.0)
    return build_object(name, verts, faces, material, loc, (0.0, pitch, 0.0))

def make_text(name, body, x, z, size=None, align="CENTER", y=None, material=None):
    cur = bpy.data.curves.new(name + "_font", type='FONT')
    cur.body = body
    cur.size = size if size else TXT_SIZE
    cur.align_x = align
    cur.align_y = 'CENTER'
    cur.extrude = 0.01
    obj = bpy.data.objects.new(name, cur)
    obj.location = (x, ANNO_Y if y is None else y, z)
    obj.rotation_euler = (math.pi / 2, 0.0, 0.0)
    if material:
        cur.materials.append(material)
    bpy.context.collection.objects.link(obj)
    return obj

def poly_line(name, points, material, y=None, width=0.015):
    yy = ANNO_Y if y is None else y
    verts, faces = [], []
    half = width / 2.0
    for (px, pz) in points:
        verts.append((px, yy, pz - half))
        verts.append((px, yy, pz + half))
    for i in range(len(points) - 1):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    return build_object(name, verts, faces, material)

def dim_line(name, p1, p2, label, material, y=None, tick=TICK):
    out = []
    (x1, z1), (x2, z2) = p1, p2
    out.append(poly_line(name + "_line", [p1, p2], material, y))
    dx, dz = x2 - x1, z2 - z1
    L = math.hypot(dx, dz) or 1.0
    nx, nz = -dz / L, dx / L

    s = tick * 1.5
    dir_x, dir_y = dx/L, dz/L

    out.append(poly_line(f"{name}_arr1a", [p1, (x1 + nx*s + dir_x*s, z1 + nz*s + dir_y*s)], material, y))
    out.append(poly_line(f"{name}_arr1b", [p1, (x1 - nx*s + dir_x*s, z1 - nz*s + dir_y*s)], material, y))
    out.append(poly_line(f"{name}_arr2a", [p2, (x2 + nx*s - dir_x*s, z2 + nz*s - dir_y*s)], material, y))
    out.append(poly_line(f"{name}_arr2b", [p2, (x2 - nx*s - dir_x*s, z2 - nz*s - dir_y*s)], material, y))

    mx, mz = (x1 + x2) / 2.0, (z1 + z2) / 2.0
    out.append(make_text(name + "_txt", label, mx + nx * (tick + 0.4), mz + nz * (tick + 0.4), material=material, y=y))
    return out

def callout_45(name, target, label, direction, material, y=None, up=True):
    tx, tz = target
    delta_z_sign = 1 if up else -1

    if direction == "LEFT":
        margin_x = -3.5
        delta_x = tx - margin_x
        text_xz = (margin_x, tz + delta_x * delta_z_sign)
        tail_x = margin_x - 0.5
        align = "RIGHT"
        pad = -0.15
        leader_pts = [target, text_xz, (tail_x, text_xz[1])]
    else:
        margin_x = SPAN_X + 3.5
        delta_x = margin_x - tx
        text_xz = (margin_x, tz + delta_x * delta_z_sign)
        tail_x = margin_x + 0.5
        align = "LEFT"
        pad = 0.15
        leader_pts = [target, text_xz, (tail_x, text_xz[1])]

    out = [poly_line(name + "_leader", leader_pts, material, y, width=0.015)]
    out.append(make_text(name + "_txt", label, tail_x + pad, text_xz[1], size=TXT_SIZE * 0.8, align=align, material=material, y=y))
    return out

def pair_between(name, p1, p2, profiles, material, y_offset=0.0):
    out = []
    for tag, prof in zip(("A", "B"), profiles):
        obj = member_between(f"{name}_{tag}", p1, p2, prof, material, y_offset)
        if obj is not None:
            out.append(obj)
    return out

# ---------------------------------------------------------------- GEOMETRY
def bottom_z(x):
    return COL_L_H + (x / SPAN_X) * (COL_R_H - COL_L_H)

def chord_top_z(x):
    return bottom_z(x) + TRUSS_DEPTH

bay_w = SPAN_X / BAYS

def node_pt(i, top):
    x = i * bay_w
    z = bottom_z(x) + (TRUSS_DEPTH if top else 0.0)
    return (x, z)

def web_partner(i, top):
    out = []
    for j in (i - 1, i):
        if j < 0 or j >= BAYS:
            continue
        even = (j % 2 == 0)
        a_top = not even
        b_top = even
        if j == i and (a_top == top):
            out.append(node_pt(j + 1, b_top))
        elif j == i - 1 and (b_top == top):
            out.append(node_pt(j, a_top))
    return out

def _convex_hull(points):
    P = sorted(set(points))
    if len(P) < 3:
        return P
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for p in P:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(P):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]

def gusset_polygon(i, top):
    ox, oz = node_pt(i, top)
    dirs = []
    if i > 0:
        px, pz = node_pt(i - 1, top)
        dirs.append((px - ox, pz - oz))
    if i < BAYS:
        nx, nz = node_pt(i + 1, top)
        dirs.append((nx - ox, nz - oz))
    for (wx, wz) in web_partner(i, top):
        dirs.append((wx - ox, wz - oz))
    if not dirs:
        return None

    inward = -1.0 if top else 1.0
    pts = []
    for (dx, dz) in dirs:
        L = math.hypot(dx, dz)
        if L < 1e-9:
            continue
        pts.append((ox + dx / L * GUSSET_REACH,
                    oz + dz / L * GUSSET_REACH + inward * GUSSET_REACH * 0.35))
    pts.append((ox, oz + inward * GUSSET_REACH * 0.55))
    pts.append((ox, oz))
    hull = _convex_hull(pts)
    return hull if len(hull) >= 3 else None

objects = []

for fr in range(FRAMES):
    fy = fr * TRUSS_SPACING
    for tag, x in (("L", 0.0), ("R", SPAN_X)):
        h = bottom_z(x)
        v, f = box_verts_faces(COL_SIZE, COL_SIZE, h)
        objects.append(build_object(f"Column_F{fr:02d}{tag}", v, f, MAT_CONC,
                                    (x, fy, h / 2)))

chord_top = L_angle_pair(L_CHORD_LEG, L_CHORD_T, DBL_GAP, flip_z=True)
chord_bot = L_angle_pair(L_CHORD_LEG, L_CHORD_T, DBL_GAP)
web_prof  = L_angle_pair(L_WEB_LEG, L_WEB_T, DBL_GAP)

for fr in range(FRAMES):
    fy = fr * TRUSS_SPACING
    for i in range(BAYS):
        objects += pair_between(f"TopChord_F{fr:02d}_{i:02d}", node_pt(i, True),
                                node_pt(i + 1, True), chord_top, MAT_STEEL, fy)
        objects += pair_between(f"BotChord_F{fr:02d}_{i:02d}", node_pt(i, False),
                                node_pt(i + 1, False), chord_bot, MAT_STEEL, fy)

for fr in range(FRAMES):
    fy = fr * TRUSS_SPACING
    for i in range(BAYS):
        if i % 2 == 0:
            p1, p2 = node_pt(i, False), node_pt(i + 1, True)
        else:
            p1, p2 = node_pt(i, True), node_pt(i + 1, False)
        objects += pair_between(f"Web_F{fr:02d}_{i:02d}", p1, p2,
                                web_prof, MAT_STEEL, fy)

for fr in range(FRAMES):
    fy = fr * TRUSS_SPACING
    for i in range(BAYS + 1):
        if i == 0:
            name = f"EndPost_F{fr:02d}L"
        elif i == BAYS:
            name = f"EndPost_F{fr:02d}R"
        else:
            name = f"Vertical_F{fr:02d}_{i:02d}"
        objects += pair_between(name, node_pt(i, False), node_pt(i, True),
                                web_prof, MAT_STEEL, fy)

for fr in range(FRAMES):
    fy = fr * TRUSS_SPACING
    for i in range(BAYS + 1):
        for top in (False, True):
            poly = gusset_polygon(i, top)
            if not poly or len(poly) < 3:
                continue
            v, f = plate_xz(poly, GUSSET_T)
            tag = "Top" if top else "Bot"
            objects.append(build_object(f"Gusset_F{fr:02d}{tag}_{i:02d}", v, f,
                                        MAT_GALV, (0.0, fy, 0.0)))

slope = math.atan2(COL_R_H - COL_L_H, SPAN_X)
purlin_prof = rotate_profile(C_purlin_profile(LC_H, LC_F, LC_LIP, LC_T), -slope)
_pz = [z for (_, z) in purlin_prof]
PURLIN_UP   = max(_pz)
PURLIN_DOWN = -min(_pz)

CHORD_HEEL  = L_CHORD_LEG / 2.0
PURLIN_CTR  = CHORD_HEEL + PURLIN_DOWN
PURLIN_TOP  = PURLIN_CTR + PURLIN_UP

SHEET_DROP  = WAVE_AMP + ROOF_T + 0.003
SLOPE_PROJ  = LC_F * math.tan(slope)
ROOF_OFFSET = PURLIN_TOP + SHEET_DROP + ROOF_SEAT + SLOPE_PROJ

for p in range(PURLINS):
    px = p * PURLIN_SPACING
    if px > SPAN_X + 0.1: # prevent going too far off
        continue
    chord_z = chord_top_z(px)
    verts, faces = sweep_profile(purlin_prof, PURLIN_LEN)
    objects.append(build_object(f"Purlin_{p:02d}", verts, faces, MAT_GALV,
                                (px, RUN_Y / 2.0, chord_z + PURLIN_CTR),
                                (0.0, 0.0, math.pi / 2)))

def sine_corrugated_sheet(name, x1, z1, x2, z2, width, pitch, amp, thickness, material):
    span = math.hypot(x2 - x1, z2 - z1)
    n = max(12, int(round(width / pitch * WAVE_STEPS)))
    top_surf, bot = [], []
    for i in range(n + 1):
        y = -width / 2.0 + width * i / n
        z = amp * math.sin(2.0 * math.pi * y / pitch)
        top_surf.append((y, z))
        bot.append((y, z - thickness - 0.003))
    profile = top_surf + bot[::-1]
    verts, faces = sweep_profile(profile, span)
    pitch_rot = -math.atan2(z2 - z1, x2 - x1)
    loc = ((x1 + x2) / 2.0, 0.0, (z1 + z2) / 2.0)
    return build_object(name, verts, faces, material, loc,
                        (0.0, pitch_rot, 0.0))

ROOF_OVER = 0.15
roof_x1, roof_x2 = -ROOF_OVER, SPAN_X + ROOF_OVER
roof_z1 = chord_top_z(roof_x1) + ROOF_OFFSET
roof_z2 = chord_top_z(roof_x2) + ROOF_OFFSET
roof = sine_corrugated_sheet(
    "Roof_Corrugated_Red", roof_x1, roof_z1, roof_x2, roof_z2,
    RUN_Y + 0.60, WAVE_PITCH, WAVE_AMP, ROOF_T, MAT_ROOF)
roof.location.y = RUN_Y / 2.0
objects.append(roof)

# ---------------------------------------------------------------- BLUEPRINT
if ANNOTATE:
    anno = []
    z_ground = 0.0
    z_low, z_high = bottom_z(0.0), bottom_z(SPAN_X)
    top_l = z_low + TRUSS_DEPTH
    top_r = z_high + TRUSS_DEPTH

    # dimensions (Orange) CLEARLY BELOW the column base and ABOVE the roof pitch
    anno += dim_line("Dim_Span", (0.0, -DIM_OFF_B), (SPAN_X, -DIM_OFF_B),
                     f"{SPAN_X:.2f} m CLEAR SPAN", MAT_TEXT_ORANGE)
    anno += dim_line("Dim_ColL", (-2.0, z_ground), (-2.0, z_low),
                     f"{z_low:.2f} m (LOW)", MAT_TEXT_ORANGE)
    anno += dim_line("Dim_ColR", (SPAN_X + 2.0, z_ground), (SPAN_X + 2.0, z_high),
                     f"{z_high:.2f} m (HIGH)", MAT_TEXT_ORANGE)

    # Purlin spacing dimension ABOVE the roof
    p0x = 0.0
    p1x = PURLIN_SPACING
    pz0 = roof_z1 + DIM_OFF_T
    pz1 = chord_top_z(p1x) + ROOF_OFFSET + DIM_OFF_T
    anno += dim_line("Dim_Purlin", (p0x, pz0), (p1x, pz1),
                     f"{p1x - p0x:.2f} m O.C. PURLINS", MAT_TEXT_ORANGE,
                     tick=TICK * 0.7)

    # total run, drawn in plan off to the side
    anno += dim_line("Dim_Run", (0.0, -DIM_OFF_B - 1.5), (SPAN_X, -DIM_OFF_B - 1.5),
                     f"{RUN_Y:.2f} m TOTAL RUN  ({FRAMES} FRAMES @ "
                     f"{TRUSS_SPACING:.2f} m)", MAT_TEXT_ORANGE)

    # Tech Specs (White) LEFT and RIGHT margins
    ch_txt = (f'2L {L_CHORD_LEG*1000:.1f} x {L_CHORD_LEG*1000:.1f} x '
              f'{L_CHORD_T*1000:.2f} mm ANGLE, BACK-TO-BACK')
    wb_txt = (f'2L {L_WEB_LEG*1000:.1f} x {L_WEB_LEG*1000:.1f} x '
              f'{L_WEB_T*1000:.2f} mm ANGLE')

    # Top Chord -> Right
    anno += callout_45("Call_TopChord", (SPAN_X * 0.75, chord_top_z(SPAN_X * 0.75)),
                       "TOP CHORD: " + ch_txt, "RIGHT", MAT_TEXT_WHITE, up=True)

    # Bot Chord -> Left
    anno += callout_45("Call_BotChord", (SPAN_X * 0.25, bottom_z(SPAN_X * 0.25)),
                       "BOT CHORD: " + ch_txt, "LEFT", MAT_TEXT_WHITE, up=False)

    # Web -> Right
    anno += callout_45("Call_Web", (SPAN_X * 0.5, bottom_z(SPAN_X * 0.5) + TRUSS_DEPTH * 0.5),
                       "WEBS + VERTICALS: " + wb_txt, "RIGHT", MAT_TEXT_WHITE, up=False)

    # Gusset -> Left
    anno += callout_45("Call_Gusset", (SPAN_X * 0.125, bottom_z(SPAN_X * 0.125)),
                       f"GUSSET: {GUSSET_T*1000:.0f} mm STEEL PLATE IN {DBL_GAP*1000:.0f} mm GAP",
                       "LEFT", MAT_TEXT_WHITE, up=False)

    # Purlins -> Right
    anno += callout_45("Call_Purlin", (SPAN_X * 0.625, chord_top_z(SPAN_X * 0.625) + PURLIN_CTR),
                       f"PURLINS: LC{LC_H*1000:.0f} x {LC_F*1000:.0f} x {LC_LIP*1000:.0f} x {LC_T*1000:.1f} mm @ {PURLIN_SPACING:.2f} m O.C.",
                       "RIGHT", MAT_TEXT_WHITE, up=True)

    # Roof -> Left
    anno += callout_45("Call_Roof", (SPAN_X * 0.375, chord_top_z(SPAN_X * 0.375) + ROOF_OFFSET + WAVE_AMP),
                       f"ROOFING: {ROOF_T*1000:.2f} mm PRE-PAINTED SINUSOIDAL CORRUGATED SHEET",
                       "LEFT", MAT_TEXT_WHITE, up=True)

    # Base -> Right
    anno += callout_45("Call_Base", (SPAN_X, 0.18),
                       "BASE PLATE: 10 mm STEEL w/ 4 - 16 mm ANCHOR BOLTS",
                       "RIGHT", MAT_TEXT_WHITE, up=False)

    make_text("Title_Main", "CONNECTING CANOPY — TYPICAL TRUSS ELEVATION",
              SPAN_X / 2.0, -DIM_OFF_B - 2.5, size=TXT_SIZE * 1.30, material=MAT_TEXT_WHITE)

    cam_data = bpy.data.cameras.new("2D_Blueprint_Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = SPAN_X + 12.0
    cam = bpy.data.objects.new("2D_Blueprint_Camera", cam_data)
    cam.location = (SPAN_X / 2.0, -28.0, (top_r + z_ground) / 2.0)
    cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    objects += [o for o in anno if o is not None]

built = [o for o in objects if o is not None]
faces = sum(len(o.data.polygons) for o in built)

print("=" * 66)
print("EJR CANOPY — WARREN TRUSS (REV 13, blueprint annotations)")
print(f"  Objects           : {len(built)}")
print(f"  Faces             : {faces}")
print(f"  Span / bays       : {SPAN_X:.2f} m / {BAYS}")
print(f"  Purlin Spacing    : {PURLIN_SPACING:.2f} m O.C.")
print("=" * 66)
