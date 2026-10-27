"""Render STEP/shape views to PNG (shaded triangle mesh) for visual checks.

usage: python render.py out.png file1.step [file2.step ...]
Each input is drawn in its own colour; views: iso, front(-Y), right(+X), top(+Z).
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from build123d import import_step

COLORS = ["#8ab4f8", "#f6ae2d", "#e15759", "#59a14f", "#b07aa1", "#76b7b2", "#9c755f"]
VIEWS = {"iso": (25, -60), "front (-Y)": (0, -90), "right (+X)": (0, 0), "top (+Z)": (90, -90)}


def tris(shape, tol=0.1):
    out = []
    for f in shape.faces():  # per face, so one bad face in a vendor STEP doesn't kill the render
        try:
            verts, faces = f.tessellate(tol, 0.3)
        except AttributeError:
            continue
        if faces:
            v = np.array([(p.X, p.Y, p.Z) for p in verts])
            out.append(v[np.array(faces)])
    return np.concatenate(out)


def render(out, shapes, title=""):
    meshes = [tris(s) for s in shapes]
    allv = np.concatenate([m.reshape(-1, 3) for m in meshes])
    lo, hi = allv.min(0), allv.max(0)
    c, r = (lo + hi) / 2, (hi - lo).max() / 2 * 1.05
    fig = plt.figure(figsize=(16, 16))
    for i, (name, (el, az)) in enumerate(VIEWS.items()):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d", proj_type="ortho")
        light = np.array([np.cos(np.radians(el)) * np.cos(np.radians(az)), np.cos(np.radians(el)) * np.sin(np.radians(az)), np.sin(np.radians(el))])
        light = light + np.array([0.3, -0.2, 0.5])
        light /= np.linalg.norm(light)
        for k, m in enumerate(meshes):
            n = np.cross(m[:, 1] - m[:, 0], m[:, 2] - m[:, 0])
            n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
            shade = 0.35 + 0.65 * np.abs(n @ light)
            base = np.array(matplotlib.colors.to_rgb(COLORS[k % len(COLORS)]))
            pc = Poly3DCollection(m, facecolors=np.clip(base * shade[:, None], 0, 1), edgecolors="none")
            ax.add_collection3d(pc)
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_title(name)
        ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    fig.suptitle(title); fig.tight_layout(); fig.savefig(out, dpi=70); plt.close(fig)


if __name__ == "__main__":
    render(sys.argv[1], [import_step(p) for p in sys.argv[2:]], " | ".join(sys.argv[2:]))
