import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import sys

def create_extrusion(A, B, profile2d, v_up=np.array([0, 1, 0])):
    A = np.array(A, dtype=float)
    B = np.array(B, dtype=float)
    dir_vec = B - A
    L = np.linalg.norm(dir_vec)
    if L < 1e-6:
        return np.array([]), []
    vz = dir_vec / L
    vx = np.cross(v_up, vz)
    if np.linalg.norm(vx) < 1e-6:
        v_up_alt = np.array([1.0, 0.0, 0.0])
        vx = np.cross(v_up_alt, vz)
        if np.linalg.norm(vx) < 1e-6:
            v_up_alt = np.array([0.0, 1.0, 0.0])
            vx = np.cross(v_up_alt, vz)
    vx = vx / np.linalg.norm(vx)
    vy = np.cross(vz, vx)

    vertices = []
    for p in profile2d:
        vA = A + p[0] * vx + p[1] * vy
        vB = B + p[0] * vx + p[1] * vy
        vertices.append(vA)
        vertices.append(vB)

    vertices = np.array(vertices)
    faces = []
    n = len(profile2d)
    for i in range(n):
        j = (i + 1) % n
        faces.append([2*i, 2*i+1, 2*j])
        faces.append([2*j, 2*i+1, 2*j+1])

    if n == 6: # L-profile capping
        faces.extend([[0, 2, 4], [0, 4, 6], [0, 6, 10], [6, 8, 10]])
        faces.extend([[1, 5, 3], [1, 7, 5], [1, 11, 7], [7, 11, 9]])
    elif n == 4:
        faces.extend([[0, 2, 4], [0, 4, 6]])
        faces.extend([[1, 5, 3], [1, 7, 5]])

    return vertices, faces

def generate_gusset(node, dirs, thickness=0.006, size=0.2):
    # node: center point (A)
    # dirs: list of vectors pointing to other nodes connected to A
    node = np.array(node, dtype=float)
    if len(dirs) < 2:
        return np.array([]), []

    # We create a simple polygonal plate that covers the vectors
    # For a triangular gusset, take two main direction vectors.
    dir1 = np.array(dirs[0])
    dir2 = np.array(dirs[-1])

    d1_len = np.linalg.norm(dir1)
    d2_len = np.linalg.norm(dir2)

    if d1_len < 1e-6 or d2_len < 1e-6:
        return np.array([]), []

    dir1 = dir1 / d1_len
    dir2 = dir2 / d2_len

    p1 = node
    p2 = node + dir1 * size
    p3 = node + dir2 * size

    normal = np.cross(dir1, dir2)
    n_norm = np.linalg.norm(normal)
    if n_norm > 1e-6:
        normal = normal / n_norm
    else:
        normal = np.array([0.0, 1.0, 0.0])

    v1 = p1 - normal * thickness / 2
    v2 = p2 - normal * thickness / 2
    v3 = p3 - normal * thickness / 2
    v4 = p1 + normal * thickness / 2
    v5 = p2 + normal * thickness / 2
    v6 = p3 + normal * thickness / 2

    vertices = np.array([v1, v2, v3, v4, v5, v6])
    faces = [
        [0, 1, 2],
        [3, 5, 4],
        [0, 3, 1], [1, 3, 4],
        [1, 4, 2], [2, 4, 5],
        [2, 5, 0], [0, 5, 3]
    ]
    return vertices, faces

def generate_geometry():
    # Architectural parameters
    span = 8.0
    bays = 8
    col_h_left = 3.5
    col_h_right = 4.8
    truss_depth = 0.6
    canopy_width = 4.0

    x_nodes = np.linspace(0, span, bays + 1)
    y_nodes = np.zeros_like(x_nodes)

    z_bot = col_h_left + (col_h_right - col_h_left) * (x_nodes / span)
    z_top = z_bot + truss_depth

    # Profile generation
    w = 0.0635 # 2.5 inches in meters
    t = 0.00635 # 1/4 inch in meters
    l_profile = np.array([[0, 0], [w, 0], [w, t], [t, t], [t, w], [0, w]]) - np.array([w/2, w/2])

    mesh_vertices = []
    mesh_faces = []
    vertex_offset = 0

    def add_mesh(verts, fcs):
        nonlocal vertex_offset
        if len(verts) == 0:
            return
        mesh_vertices.extend(verts)
        mesh_faces.extend([[fi + vertex_offset for fi in fc] for fc in fcs])
        vertex_offset += len(verts)

    # Dictionary to keep track of connections for gusset plates
    # node_key -> list of vectors to connected nodes
    connections = {}

    def add_member(A, B, profile):
        v, f = create_extrusion(A, B, profile)
        add_mesh(v, f)

        # Add to connections
        A_tuple = (round(A[0], 3), round(A[1], 3), round(A[2], 3))
        B_tuple = (round(B[0], 3), round(B[1], 3), round(B[2], 3))

        vecAB = np.array(B) - np.array(A)
        vecBA = np.array(A) - np.array(B)

        if A_tuple not in connections: connections[A_tuple] = []
        connections[A_tuple].append(vecAB)

        if B_tuple not in connections: connections[B_tuple] = []
        connections[B_tuple].append(vecBA)

    # 1. Columns
    col_profile = np.array([[-0.1, -0.1], [0.1, -0.1], [0.1, 0.1], [-0.1, 0.1]])
    add_member([0, 0, 0], [0, 0, z_bot[0]], col_profile)
    add_member([span, 0, 0], [span, 0, z_bot[-1]], col_profile)

    # 2. Bottom Chord
    for i in range(bays):
        add_member([x_nodes[i], 0, z_bot[i]], [x_nodes[i+1], 0, z_bot[i+1]], l_profile)

    # 3. Top Chord
    for i in range(bays):
        add_member([x_nodes[i], 0, z_top[i]], [x_nodes[i+1], 0, z_top[i+1]], l_profile)

    # 4. Warren Web
    for i in range(bays):
        if i % 2 == 0:
            add_member([x_nodes[i], 0, z_top[i]], [x_nodes[i+1], 0, z_bot[i+1]], l_profile)
        else:
            add_member([x_nodes[i], 0, z_bot[i]], [x_nodes[i+1], 0, z_top[i+1]], l_profile)

    # 5. Vertical End Posts
    add_member([0, 0, z_bot[0]], [0, 0, z_top[0]], l_profile)
    add_member([span, 0, z_bot[-1]], [span, 0, z_top[-1]], l_profile)

    # Add Gusset plates at joints
    for node_key, dirs in connections.items():
        if len(dirs) > 1: # Joint
            v, f = generate_gusset(node_key, dirs)
            add_mesh(v, f)

    # 6. C-Purlins
    purlin_lines = []
    for i in range(len(x_nodes)):
        purlin_lines.append([(x_nodes[i], -canopy_width/2, z_top[i]),
                             (x_nodes[i], canopy_width/2, z_top[i])])

    # 7. Roof
    x_roof = np.linspace(0, span, 200)
    y_roof = np.linspace(-canopy_width/2, canopy_width/2, 200)
    X, Y = np.meshgrid(x_roof, y_roof)
    Z = col_h_left + truss_depth + (col_h_right - col_h_left) * (X / span)
    Z += 0.02 * np.sin(2 * np.pi * Y / 0.15)

    return np.array(mesh_vertices), mesh_faces, purlin_lines, X, Y, Z, span

def render_plotly(verts, faces, purlin_lines, X, Y, Z, span):
    fig = go.Figure()

    if len(verts) > 0:
        fig.add_trace(go.Mesh3d(
            x=verts[:, 0], y=verts[:, 1], z=verts[:, 2],
            i=[f[0] for f in faces], j=[f[1] for f in faces], k=[f[2] for f in faces],
            color='#64748b', name='Steel Structure', flatshading=True
        ))

    purlin_x, purlin_y, purlin_z = [], [], []
    for pline in purlin_lines:
        purlin_x.extend([pline[0][0], pline[1][0], None])
        purlin_y.extend([pline[0][1], pline[1][1], None])
        purlin_z.extend([pline[0][2], pline[1][2], None])

    fig.add_trace(go.Scatter3d(
        x=purlin_x, y=purlin_y, z=purlin_z,
        mode='lines', line=dict(color='#cbd5e1', width=8),
        name='C-Purlins'
    ))

    for bx in [0, span]:
        fig.add_trace(go.Mesh3d(
            x=[bx-0.3, bx+0.3, bx+0.3, bx-0.3],
            y=[-0.3, -0.3, 0.3, 0.3],
            z=[0, 0, 0, 0],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color='#64748b', name='Base Plate', showlegend=False
        ))

    fig.add_trace(go.Surface(
        x=X[0,:], y=Y[:,0], z=Z,
        colorscale=[[0, '#dc2626'], [1, '#dc2626']],
        showscale=False,
        name='Corrugated Roof',
        opacity=0.95
    ))

    fig.update_layout(
        scene=dict(
            aspectmode='data',
            xaxis_title='Length (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)'
        ),
        title='3D Sloped Warren Truss Canopy',
        margin=dict(l=0, r=0, b=0, t=40)
    )

    fig.write_html('truss_visualizer.html')
    print("Plotly visualization successfully saved to 'truss_visualizer.html'.")
    return fig

def render_matplotlib(verts, faces, purlin_lines, X, Y, Z, span):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    if len(verts) > 0:
        triangles = [[verts[f[0]], verts[f[1]], verts[f[2]]] for f in faces]
        mesh = Poly3DCollection(triangles, facecolors='#64748b', edgecolors=None, linewidths=0, antialiased=False)
        ax.add_collection3d(mesh)

    for pline in purlin_lines:
        ax.plot([pline[0][0], pline[1][0]], [pline[0][1], pline[1][1]], [pline[0][2], pline[1][2]], color='#cbd5e1', linewidth=3)

    for bx in [0, span]:
        px = [bx-0.3, bx+0.3, bx+0.3, bx-0.3, bx-0.3]
        py = [-0.3, -0.3, 0.3, 0.3, -0.3]
        pz = [0, 0, 0, 0, 0]
        ax.plot(px, py, pz, color='#64748b')

    ax.plot_surface(X, Y, Z, color='#dc2626', alpha=0.9, antialiased=False, shade=True)

    max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0
    mid_x = (X.max()+X.min()) * 0.5
    mid_y = (Y.max()+Y.min()) * 0.5
    mid_z = (Z.max()+Z.min()) * 0.5
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    ax.set_xlabel('Length (m)')
    ax.set_ylabel('Width (m)')
    ax.set_zlabel('Height (m)')
    ax.set_title('3D Sloped Warren Truss Canopy')

    plt.savefig('truss_render.png', dpi=300, bbox_inches='tight')
    print("Matplotlib render successfully saved to 'truss_render.png'.")

def main():
    print("Generating 3D structural geometry...")
    verts, faces, purlin_lines, X, Y, Z, span = generate_geometry()

    print("Rendering Interactive Plotly visualization...")
    fig = render_plotly(verts, faces, purlin_lines, X, Y, Z, span)

    print("Rendering Static Matplotlib visualization...")
    render_matplotlib(verts, faces, purlin_lines, X, Y, Z, span)

    if 'ipykernel' in sys.modules or 'google.colab' in sys.modules:
        print("Detected Jupyter/Colab environment. Displaying interactive Plotly visualization...")
        fig.show()

if __name__ == "__main__":
    main()
