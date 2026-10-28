"""Show the toolhead assembly in the OCP CAD Viewer (VS Code extension), without exporting anything.

    python cad/show.py            # heat-set insert version
    python cad/show.py --nuts     # captive-nut version

Open the viewer first (OCP icon in the VS Code sidebar, or "OCP CAD Viewer: Open Viewer").
Every part is a separate object in the viewer tree, so each can be hidden or isolated.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from build123d import Rot
from ocp_vscode import show
import toolhead_adapter as ta
import carriage_mount as cm

PARTS = {  # name: colour, matching the render captions
    "adapter": "steelblue", "duct_R": "teal", "duct_L": "teal",
    "hotend_mount": "orange", "fan_3010": "red", "blower_R": "green", "blower_L": "green",
    "bmg": "mediumpurple", "hotend": "saddlebrown",
    "mgn7h_carriage": "lightseagreen", "mgn7_rail": "silver", "x_extrusion": "dimgray",
}


def main():
    duct = ta.build_duct()
    objs = {"adapter": ta.build_part(), "duct_R": duct, "duct_L": Rot(0, 0, 180) * duct}
    objs.update(ta.load_vendor())
    objs.update(cm.build_reference())
    names = list(objs)
    show(*objs.values(), names=names, colors=[PARTS[n] for n in names],
         alphas=[0.4 if n in ("mgn7_rail", "x_extrusion") else 1.0 for n in names])


if __name__ == "__main__":
    main()
