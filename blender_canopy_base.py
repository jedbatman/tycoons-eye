import bpy
import math
import mathutils

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16)/255.0 for i in (0, 2, 4)) + (1.0,)

def create_material(name, hex_color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = hex_to_rgb(hex_color)
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
    return mat

def create_extrusion_mesh(name, start, end, profile2d, mat):
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    if mat:
        obj.data.materials.append(mat)

    A = mathutils.Vector(start)
    B = mathutils.Vector(end)
    dir_vec = B - A
    L = dir_vec.length
    if L < 1e-6:
        return obj

    vz = dir_vec.normalized()
    v_up = mathutils.Vector((0, 1, 0))
    vx = v_up.cross(vz)
    if vx.length < 1e-6:
        v_up = mathutils.Vector((1, 0, 0))
        vx = v_up.cross(vz)
    vx.normalize()
    vy = vz.cross(vx)

    verts = []
    for p in profile2d:
        verts.append(A + p[0]*vx + p[1]*vy)
    for p in profile2d:
        verts.append(B + p[0]*vx + p[1]*vy)

    faces = []
    n = len(profile2d)
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j+n, i+n))

    # Caps
    faces.append(tuple(range(n)))
    faces.append(tuple(range(n, 2*n)))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return obj

def generate_l_profile(w, t):
    return [
        (0, 0),
        (w, 0),
        (w, t),
        (t, t),
        (t, w),
        (0, w)
    ]

def generate_c_profile(h, f, lip, t):
    return [
        (0, 0),
        (f, 0),
        (f, lip),
        (f-t, lip),
        (f-t, t),
        (t, t),
        (t, h-t),
        (f-t, h-t),
        (f-t, h-lip),
        (f, h-lip),
        (f, h),
        (0, h)
    ]

def generate_canopy():
    # 1. CLEAN SCENE SAFELY (NO CRASH DATA PURGE)
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(confirm=False)

    # Materials
    mat_dark_slate = create_material("DarkSlate", "#334155", metallic=0.8, roughness=0.4)
    mat_silver = create_material("Silver", "#cbd5e1", metallic=0.9, roughness=0.3)
    mat_red = create_material("RedRoof", "#dc2626", metallic=0.1, roughness=0.6)

    # 2. PARAMETERS
    span_x = 8.0
    bays = 8
    col_left_h = 3.2
    col_right_h = 4.5
    truss_depth = 0.5
    purlin_count = 9
    canopy_width = 4.0

    # Profiles
    l_63_5 = generate_l_profile(0.0635, 0.00635)
    l_50_0 = generate_l_profile(0.050, 0.00475)
    c_150 = generate_c_profile(0.150, 0.050, 0.015, 0.002)

    # Helper for simple boxes
    def create_fast_box(name, location, scale, mat=None):
        mesh = bpy.data.meshes.new(name + "_mesh")
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        if mat:
            obj.data.materials.append(mat)
        verts = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
                 (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)]
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj.location = location
        obj.scale = scale
        return obj

    # Columns
    create_fast_box("Left_Column", (0, 0, col_left_h/2), (0.2, 0.2, col_left_h), mat_dark_slate)
    create_fast_box("Right_Column", (span_x, 0, col_right_h/2), (0.2, 0.2, col_right_h), mat_dark_slate)

    bay_w = span_x / bays

    nodes = {} # track nodes for gusset

    def add_member(name, start, end, profile, mat):
        create_extrusion_mesh(name, start, end, profile, mat)

    for i in range(bays):
        x1, x2 = i * bay_w, (i + 1) * bay_w
        z_bot1 = col_left_h + (x1 / span_x) * (col_right_h - col_left_h)
        z_bot2 = col_left_h + (x2 / span_x) * (col_right_h - col_left_h)
        z_top1, z_top2 = z_bot1 + truss_depth, z_bot2 + truss_depth

        # Chords
        add_member(f"TopChord_{i}", (x1, 0, z_top1), (x2, 0, z_top2), l_63_5, mat_dark_slate)
        add_member(f"BotChord_{i}", (x1, 0, z_bot1), (x2, 0, z_bot2), l_63_5, mat_dark_slate)

        # Webs
        if i % 2 == 0:
            add_member(f"Web_{i}", (x1, 0, z_top1), (x2, 0, z_bot2), l_50_0, mat_dark_slate)
        else:
            add_member(f"Web_{i}", (x1, 0, z_bot1), (x2, 0, z_top2), l_50_0, mat_dark_slate)

        # Register nodes for gussets
        nodes[(round(x1, 3), 0.0, round(z_top1, 3))] = True
        nodes[(round(x1, 3), 0.0, round(z_bot1, 3))] = True
        nodes[(round(x2, 3), 0.0, round(z_top2, 3))] = True
        nodes[(round(x2, 3), 0.0, round(z_bot2, 3))] = True

    # Purlins
    for p in range(purlin_count):
        px = (p / (purlin_count - 1)) * span_x
        pz = col_left_h + truss_depth + (px / span_x) * (col_right_h - col_left_h) + 0.0635
        # center purlin over canopy width
        add_member(f"Purlin_{p}", (px, -canopy_width/2, pz), (px, canopy_width/2, pz), c_150, mat_silver)
        # Cleats
        create_fast_box(f"Cleat_{p}", (px, 0, pz - 0.05), (0.05, 0.05, 0.05), mat_silver)

    # Gussets
    for pos in nodes:
        mesh = bpy.data.meshes.new("Gusset_mesh")
        obj = bpy.data.objects.new("Gusset", mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat_silver)

        t = 0.006
        s = 0.15 # size
        verts = [
            (-s, -t/2, -s), (s, -t/2, -s), (0, -t/2, s),
            (-s, t/2, -s), (s, t/2, -s), (0, t/2, s)
        ]
        faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj.location = pos

    # Roof Surface
    roof_z = col_left_h + truss_depth + (col_right_h - col_left_h)/2 + 0.150 + 0.0635
    roof_angle = math.atan2(col_right_h - col_left_h, span_x)

    rmesh = bpy.data.meshes.new("RedRoof_mesh")
    robj = bpy.data.objects.new("RedRoof", rmesh)
    bpy.context.collection.objects.link(robj)
    robj.data.materials.append(mat_red)

    res_x = 20
    res_y = 100
    rverts = []
    rfaces = []
    for i in range(res_x):
        for j in range(res_y):
            u = i / (res_x - 1)
            v = j / (res_y - 1)
            x = u * (span_x + 0.4) - 0.2
            y = v * (canopy_width + 0.4) - (canopy_width + 0.4)/2
            z = 0.02 * math.sin(v * 2 * math.pi * (canopy_width/0.15))
            rverts.append((x, y, z))

    for i in range(res_x - 1):
        for j in range(res_y - 1):
            idx = i * res_y + j
            rfaces.append((idx, idx+1, idx+res_y+1, idx+res_y))

    rmesh.from_pydata(rverts, [], rfaces)
    rmesh.update()

    robj.location = (0, 0, col_left_h + truss_depth + 0.150 + 0.0635)
    robj.rotation_euler = (0, -roof_angle, 0)

    print("⚡ LIGHTWEIGHT 3D WARREN TRUSS GENERATED IN <1.0 SECONDS!")

if __name__ == "__main__":
    try:
        generate_canopy()
    except Exception as e:
        print(f"Failed to generate canopy: {e}")
