import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys

def generate_geometry():
    # Architectural parameters
    span = 8.0
    bays = 8
    col_h_left = 3.5
    col_h_right = 4.8
    truss_depth = 0.6
    canopy_width = 4.0

    # Node coordinates along the X-axis
    x_nodes = np.linspace(0, span, bays + 1)
    y_nodes = np.zeros_like(x_nodes)

    # Z-coordinates for the sloped bottom and top chords
    z_bot = col_h_left + (col_h_right - col_h_left) * (x_nodes / span)
    z_top = z_bot + truss_depth

    # Store all structural line segments as pairs of 3D points
    lines = []

    # 1. Columns (Two Steel I-Beam supports at ends)
    lines.append([(0, 0, 0), (0, 0, z_bot[0])])
    lines.append([(span, 0, 0), (span, 0, z_bot[-1])])

    # 2. Bottom Chord
    for i in range(bays):
        lines.append([(x_nodes[i], 0, z_bot[i]), (x_nodes[i+1], 0, z_bot[i+1])])

    # 3. Top Chord
    for i in range(bays):
        lines.append([(x_nodes[i], 0, z_top[i]), (x_nodes[i+1], 0, z_top[i+1])])

    # 4. Warren Web (Zig-zagging diagonal members)
    for i in range(bays):
        if i % 2 == 0:
            # Top to Bottom
            lines.append([(x_nodes[i], 0, z_top[i]), (x_nodes[i+1], 0, z_bot[i+1])])
        else:
            # Bottom to Top
            lines.append([(x_nodes[i], 0, z_bot[i]), (x_nodes[i+1], 0, z_top[i+1])])

    # 5. Vertical End Posts for Structural Integrity
    lines.append([(0, 0, z_bot[0]), (0, 0, z_top[0])])
    lines.append([(span, 0, z_bot[-1]), (span, 0, z_top[-1])])

    # 6. C-Purlins (Mounted perpendicular on top chords)
    purlin_lines = []
    for i in range(len(x_nodes)):
        purlin_lines.append([(x_nodes[i], -canopy_width/2, z_top[i]),
                             (x_nodes[i], canopy_width/2, z_top[i])])

    # 7. Pre-painted Red Corrugated Roofing Sheet
    # High-resolution mesh for the corrugation effect
    x_roof = np.linspace(0, span, 200)
    y_roof = np.linspace(-canopy_width/2, canopy_width/2, 200)
    X, Y = np.meshgrid(x_roof, y_roof)
    # Base sloped plane
    Z = col_h_left + truss_depth + (col_h_right - col_h_left) * (X / span)
    # Add sine wave for the corrugated/rib-type texture along the Y axis
    Z += 0.02 * np.sin(2 * np.pi * Y / 0.15)

    return lines, purlin_lines, X, Y, Z, span

def render_plotly(lines, purlin_lines, X, Y, Z, span):
    fig = go.Figure()

    # Bundle lines to avoid slow rendering with too many traces
    truss_x, truss_y, truss_z = [], [], []
    for line in lines:
        truss_x.extend([line[0][0], line[1][0], None])
        truss_y.extend([line[0][1], line[1][1], None])
        truss_z.extend([line[0][2], line[1][2], None])

    fig.add_trace(go.Scatter3d(
        x=truss_x, y=truss_y, z=truss_z,
        mode='lines', line=dict(color='#64748b', width=6),
        name='Steel Columns & Truss'
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

    # Base Connection Plates at column footings
    for bx in [0, span]:
        fig.add_trace(go.Mesh3d(
            x=[bx-0.3, bx+0.3, bx+0.3, bx-0.3],
            y=[-0.3, -0.3, 0.3, 0.3],
            z=[0, 0, 0, 0],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color='#64748b', name='Base Plate', showlegend=False
        ))

    # Corrugated Roof Surface
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

def render_matplotlib(lines, purlin_lines, X, Y, Z, span):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot Trusses and Columns
    for line in lines:
        ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], [line[0][2], line[1][2]], color='#64748b', linewidth=2)

    # Plot Purlins
    for pline in purlin_lines:
        ax.plot([pline[0][0], pline[1][0]], [pline[0][1], pline[1][1]], [pline[0][2], pline[1][2]], color='#cbd5e1', linewidth=3)

    # Plot Base Plates
    for bx in [0, span]:
        px = [bx-0.3, bx+0.3, bx+0.3, bx-0.3, bx-0.3]
        py = [-0.3, -0.3, 0.3, 0.3, -0.3]
        pz = [0, 0, 0, 0, 0]
        ax.plot(px, py, pz, color='#64748b')

    # Plot Roof Surface
    ax.plot_surface(X, Y, Z, color='#dc2626', alpha=0.9, antialiased=False, shade=True)

    # Make aspect ratio 1:1:1
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
    lines, purlin_lines, X, Y, Z, span = generate_geometry()

    print("Rendering Interactive Plotly visualization...")
    fig = render_plotly(lines, purlin_lines, X, Y, Z, span)

    print("Rendering Static Matplotlib visualization...")
    render_matplotlib(lines, purlin_lines, X, Y, Z, span)

    # Enable Google Colab and Jupyter Notebook inline display support
    if 'ipykernel' in sys.modules or 'google.colab' in sys.modules:
        print("Detected Jupyter/Colab environment. Displaying interactive Plotly visualization...")
        fig.show()

if __name__ == "__main__":
    main()
