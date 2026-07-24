import bpy
import math
import time
from mathutils import Vector

"""
EJR BUILDERS — Lightweight Warren Truss Canopy Generator
All dimensions are in metres.

Geometry is generated directly with Mesh.from_pydata. No repeated primitive
operators, modifiers, booleans, or orphan-data purge calls are used.
"""

START_TIME = time.perf_counter()

# -----------------------------------------------------------------------------
# 1. SAFE SCENE CLEANUP
# -----------------------------------------------------------------------------
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

for obj in tuple(bpy.context.scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# -----------------------------------------------------------------------------
# 2. ENGINEERING PARAMETERS
# -----------------------------------------------------------------------------
SPAN_X = 8.0
BAYS = 8
COLUMN_LEFT_H = 3.2
COLUMN_RIGHT_H = 4.5
TRUSS_DEPTH = 0.50
CANOPY_HALF_WIDTH_Y = 1.40
PURLIN_COUNT = 9
ROOF_OVERHANG_X = 0.20
ROOF_OVERHANG_Y = 0.15

# Equal-leg angle sections
CHORD_LEG = 0.0635       # 2.5 in
CHORD_T = 0.00635        # 1/4 in
WEB_LEG = 0.0500         # 2 in nominal
WEB_T = 0.00475          # 3/16 in

# LC150 section
PURLIN_H = 0.150
PURLIN_FLANGE = 0.050
PURLIN_LIP = 0.015
PURLIN_T = 0.002
CLEAT_SIZE = 0.050
CLEAT_T = 0.006

GUSSET_T = 0.006
GUSSET_RADIUS = 0.115
ROOF_BMT = 0.0005
ROOF_RIB_PITCH = 0.200
ROOF_RIB_DEPTH = 0.025

# -----------------------------------------------------------------------------
# 3. MATERIALS
# -----------------------------------------------------------------------------
def hex_rgba(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)


def make_pbr_material(name, color_hex, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_rgba(color_hex)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


MAT_STEEL = make_pbr_material("Dark Metallic Slate Grey", "#334155", 0.82, 0.28)
MAT_GALV = make_pbr_material("Galvanized Metallic Silver", "#cbd5e1", 0.72, 0.34)
MAT_ROOF = make_pbr_material("Pre-painted Satin Red", "#dc2626", 0.48, 0.26)

# -----------------------------------------------------------------------------
# 4. LOW-OVERHEAD MESH HELPERS
# -----------------------------------------------------------------------------
def create_mesh_object(name, vertices, faces, material=None):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def extrude_profile_x(name, profile_yz, length, material, start_point, end_point):
    """Extrude a closed YZ profile along local X, then align X to the member axis."""
    n = len(profile_yz)
    half = length * 0.5
    verts = [(-half, y, z) for y, z in profile_yz]
    verts += [(half, y, z) for y, z in profile_yz]

    faces = []
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))

    obj = create_mesh_object(name, verts, faces, material)
    p0 = Vector(start_point)
    p1 = Vector(end_point)
    axis = p1 - p0
    obj.location = (p0 + p1) * 0.5
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = axis.to_track_quat("X", "Z")
    return obj


def angle_profile(leg, thickness):
    """Closed equal-leg L profile in local YZ, centered near its heel."""
    h = leg * 0.5
    t = thickness
    return [
        (-h, -h), (h, -h), (h, -h + t),
        (-h + t, -h + t), (-h + t, h), (-h, h)
    ]


def c_channel_profile(height, flange, lip, thickness):
    """Closed thin-walled lipped C profile in local YZ."""
    h = height * 0.5
    f = flange
    l = lip
    t = thickness
    return [
        (0.0, -h), (f, -h), (f, -h + l), (f - t, -h + l),
        (f - t, -h + t), (t, -h + t), (t, h - t),
        (f - t, h - t), (f - t, h - l), (f, h - l),
        (f, h), (0.0, h)
    ]


def create_box_between(name, p0, p1, width, depth, material):
    profile = [(-width / 2, -depth / 2), (width / 2, -depth / 2),
               (width / 2, depth / 2), (-width / 2, depth / 2)]
    return extrude_profile_x(name, profile, (Vector(p1) - Vector(p0)).length,
                             material, p0, p1)


def create_gusset(name, center, slope_angle, material):
    """Triangular plate lying in the truss XZ plane with thickness along Y."""
    cx, cy, cz = center
    r = GUSSET_RADIUS
    local = [(-r, 0.0), (r, 0.0), (0.0, r * 1.20)]
    ca, sa = math.cos(slope_angle), math.sin(slope_angle)
    xz = [(cx + x * ca - z * sa, cz + x * sa + z * ca) for x, z in local]
    y0, y1 = cy - GUSSET_T / 2, cy + GUSSET_T / 2
    verts = [(x, y0, z) for x, z in xz] + [(x, y1, z) for x, z in xz]
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3),
             (1, 2, 5, 4), (2, 0, 3, 5)]
    return create_mesh_object(name, verts, faces, material)

# -----------------------------------------------------------------------------
# 5. STRUCTURAL DATUM FUNCTIONS
# -----------------------------------------------------------------------------
def bottom_z(x):
    return COLUMN_LEFT_H + (x / SPAN_X) * (COLUMN_RIGHT_H - COLUMN_LEFT_H)


def top_z(x):
    return bottom_z(x) + TRUSS_DEPTH


ROOF_ANGLE = math.atan2(COLUMN_RIGHT_H - COLUMN_LEFT_H, SPAN_X)
BAY_W = SPAN_X / BAYS

# -----------------------------------------------------------------------------
# 6. COLUMNS
# -----------------------------------------------------------------------------
create_box_between("Left_Column", (0, 0, 0), (0, 0, COLUMN_LEFT_H), 0.20, 0.20, MAT_STEEL)
create_box_between("Right_Column", (SPAN_X, 0, 0), (SPAN_X, 0, COLUMN_RIGHT_H), 0.20, 0.20, MAT_STEEL)

# -----------------------------------------------------------------------------
# 7. WARREN TRUSS: TRUE L-ANGLE MEMBERS
# -----------------------------------------------------------------------------
chord_profile = angle_profile(CHORD_LEG, CHORD_T)
web_profile = angle_profile(WEB_LEG, WEB_T)

for i in range(BAYS):
    x1 = i * BAY_W
    x2 = (i + 1) * BAY_W

    extrude_profile_x(
        f"TopChord_{i:02d}", chord_profile,
        math.hypot(BAY_W, top_z(x2) - top_z(x1)), MAT_STEEL,
        (x1, 0, top_z(x1)), (x2, 0, top_z(x2))
    )
    extrude_profile_x(
        f"BottomChord_{i:02d}", chord_profile,
        math.hypot(BAY_W, bottom_z(x2) - bottom_z(x1)), MAT_STEEL,
        (x1, 0, bottom_z(x1)), (x2, 0, bottom_z(x2))
    )

    if i % 2 == 0:
        p0 = (x1, 0, bottom_z(x1))
        p1 = (x2, 0, top_z(x2))
    else:
        p0 = (x1, 0, top_z(x1))
        p1 = (x2, 0, bottom_z(x2))

    extrude_profile_x(
        f"WarrenWeb_{i:02d}", web_profile,
        (Vector(p1) - Vector(p0)).length, MAT_STEEL, p0, p1
    )

# -----------------------------------------------------------------------------
# 8. GUSSET PLATES AT PANEL JOINTS
# -----------------------------------------------------------------------------
for i in range(BAYS + 1):
    x = i * BAY_W
    create_gusset(f"Gusset_Bottom_{i:02d}", (x, 0, bottom_z(x)), ROOF_ANGLE, MAT_GALV)
    create_gusset(f"Gusset_Top_{i:02d}", (x, 0, top_z(x)), ROOF_ANGLE + math.pi, MAT_GALV)

# -----------------------------------------------------------------------------
# 9. LC150 C-PURLINS AND 50 mm CLEATS
# -----------------------------------------------------------------------------
purlin_profile = c_channel_profile(PURLIN_H, PURLIN_FLANGE, PURLIN_LIP, PURLIN_T)
for p in range(PURLIN_COUNT):
    x = (p / (PURLIN_COUNT - 1)) * SPAN_X
    z = top_z(x) + 0.075
    p0 = (x, -CANOPY_HALF_WIDTH_Y, z)
    p1 = (x, CANOPY_HALF_WIDTH_Y, z)
    extrude_profile_x(
        f"LC150_Purlin_{p:02d}", purlin_profile,
        (Vector(p1) - Vector(p0)).length, MAT_GALV, p0, p1
    )

    # Two compact cleats straddling the truss plane.
    create_box_between(
        f"PurlinCleat_L_{p:02d}",
        (x, -CLEAT_SIZE * 0.55, top_z(x)),
        (x, -CLEAT_SIZE * 0.55, z),
        CLEAT_SIZE, CLEAT_T, MAT_GALV
    )
    create_box_between(
        f"PurlinCleat_R_{p:02d}",
        (x, CLEAT_SIZE * 0.55, top_z(x)),
        (x, CLEAT_SIZE * 0.55, z),
        CLEAT_SIZE, CLEAT_T, MAT_GALV
    )

# -----------------------------------------------------------------------------
# 10. SINGLE-MESH CORRUGATED ROOFING SHEET
# -----------------------------------------------------------------------------
def create_corrugated_roof():
    x_min = -ROOF_OVERHANG_X
    x_max = SPAN_X + ROOF_OVERHANG_X
    y_min = -CANOPY_HALF_WIDTH_Y - ROOF_OVERHANG_Y
    y_max = CANOPY_HALF_WIDTH_Y + ROOF_OVERHANG_Y

    # Ribs run downslope (X direction); corrugation varies across Y.
    rib_count = max(2, int(math.ceil((y_max - y_min) / ROOF_RIB_PITCH)))
    y_steps = rib_count * 4
    x_steps = BAYS * 2
    verts = []

    def roof_base_z(x):
        return top_z(x) + PURLIN_H * 0.5 + 0.020

    for ix in range(x_steps + 1):
        x = x_min + (x_max - x_min) * ix / x_steps
        for iy in range(y_steps + 1):
            y = y_min + (y_max - y_min) * iy / y_steps
            phase = 2.0 * math.pi * (y - y_min) / ROOF_RIB_PITCH
            corrugation = ROOF_RIB_DEPTH * (0.5 + 0.5 * math.cos(phase))
            verts.append((x, y, roof_base_z(x) + corrugation + ROOF_BMT * 0.5))

    faces = []
    row = y_steps + 1
    for ix in range(x_steps):
        for iy in range(y_steps):
            a = ix * row + iy
            b = a + 1
            c = a + row + 1
            d = a + row
            faces.append((a, b, c, d))

    obj = create_mesh_object("Corrugated_Prepainted_Red_Roof", verts, faces, MAT_ROOF)
    # Solidify is intentionally avoided. The specified 0.5 mm BMT is represented
    # by datum placement and metadata to retain sub-second lightweight execution.
    obj["base_metal_thickness_m"] = ROOF_BMT
    obj["rib_pitch_m"] = ROOF_RIB_PITCH
    obj["rib_depth_m"] = ROOF_RIB_DEPTH
    return obj


create_corrugated_roof()

# -----------------------------------------------------------------------------
# 11. MODEL METADATA
# -----------------------------------------------------------------------------
scene = bpy.context.scene
scene["project"] = "EJR Builders Warren Truss Canopy"
scene["chord_section"] = 'L 2.5 x 2.5 x 1/4 in (63.5 x 63.5 x 6.35 mm)'
scene["web_section"] = 'L 2 x 2 x 3/16 in (50 x 50 x 4.75 mm)'
scene["purlin_section"] = 'LC150: 150 x 50 x 15 x 2.0 mm'
scene["gusset_thickness_mm"] = 6.0
scene["roof_bmt_mm"] = 0.5

elapsed = time.perf_counter() - START_TIME
print(f"⚡ EJR ENGINEERING WARREN TRUSS GENERATED IN {elapsed:.3f} SECONDS")
