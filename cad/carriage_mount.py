"""MGN7H carriage mount (Voron 0.2 X axis), fused onto the back of the toolhead adapter.

Parametric build123d model, same world frame as toolhead_adapter.py:
    origin = filament axis on the BMG's bottom face, +Z up, -Y front (fan side), +Y back (BMG motor side)
Run:
    python cad/carriage_mount.py [--nuts]     # checks the adapter on the carriage + renders
toolhead_adapter.build_part() adds build_mount() to the adapter, so there's no separate part to export.
Renders go to ../output/inserts/ or ../output/nuts/ (with --nuts).

Layout: the MGN7H rail lies on top of the X extrusion (running along X), so the carriage faces up, toward the
BMG motor. The mount is an L: a plate that sits on top of the carriage, under the motor, plus a flange fused to
the adapter's back face. The two hotend-mount screws (M3x35) run through the back tab into M3 nuts in the
flange, dropped into slots that open on the top face (in both versions: an insert there couldn't be pressed in).
The 4 M2 carriage screws sit under the BMG motor, so the BMG comes off to take the toolhead off the carriage.
"""
from pathlib import Path
import sys
from build123d import Axis, Compound

sys.path.insert(0, str(Path(__file__).parent))
import toolhead_adapter as ta
from toolhead_adapter import box, cyl_y, cyl_z, fillet_where, near, interference, nut_pocket

OUT = ta.OUT

# ---------------------------------------------------------------- parameters
# HIWIN MGN7H (mm): rail 7 wide x 4.8 high, rail bottom to carriage top 8, carriage 17 wide x 30.8 long,
# 4x M2 at 12 (across the rail) x 13 (along it), 2.5 deep thread
RAIL_W, RAIL_H, MGN_H = 7.0, 4.8, 8.0
CAR_W, CAR_L = 17.0, 30.8
CAR_HOLE_ACROSS, CAR_HOLE_ALONG = 12.0, 13.0
EXTRUSION = 15.0             # 1515 X extrusion under the rail (reference only)

PLATE_T = 6.6                # plate on top of the carriage, top face flush with the adapter's (z=0, the bed face)
FLANGE_T = 7.0               # flange on the adapter's back face (holds the nuts, M3x35 tip ends inside)
FLANGE_SIDE_GAP = 0.2        # flange X edge to the blowers
CAR_GAP = 2.5                # flange back face to the carriage front edge (room for the inside fillet)
PLATE_MARGIN = 2.0           # plate past the carriage's back edge
NUT_WALL = 2.0               # flange in front of the nut slots (takes the screw load)
MOUNT_SCREW_L = 35.0         # the 2 hotend-mount screws, front plate -> nuts in the flange
M2_CLEAR, M2_HEAD_D, M2_UNDER_HEAD = 2.4, 4.2, 3.0   # M2x5 SHCS: 3 mm plate under the head + 2 mm thread
R_CORNER, R_INSIDE = 3.0, 2.0

# ------------------------------------------------------------- derived values
Y0 = ta.Y_BACK_OUT                                   # adapter back face = flange front face
Y_FLANGE = Y0 + FLANGE_T
SCREW_TIP = ta.Y_FRONT_OUT + ta.M3_HEAD_RECESS + MOUNT_SCREW_L   # hotend-mount screw tip, inside the flange
TOP_Z = 0.0                                          # top face of plate and flange, flush with the adapter's
CAR_TOP = TOP_Z - PLATE_T
FLANGE_LO = ta.MOUNT_TOP - ta.BACK_TAB_H             # flange runs down as far as the back tab
CAR_Y = Y_FLANGE + CAR_GAP + CAR_W / 2               # rail centre line
PLATE_Y1 = CAR_Y + CAR_W / 2 + PLATE_MARGIN
HALF_X = ta.BL_X0 - FLANGE_SIDE_GAP
RAIL_LO = CAR_TOP - MGN_H


def build_mount():
    flange = box(-HALF_X, HALF_X, Y0, Y_FLANGE, FLANGE_LO, TOP_Z)
    plate = box(-HALF_X, HALF_X, Y0, PLATE_Y1, CAR_TOP, TOP_Z)
    plate = fillet_where(plate, R_CORNER, Axis.Z, lambda c: near(c.Y, PLATE_Y1))
    part = flange + plate
    part = fillet_where(part, R_INSIDE, Axis.X, lambda c: near(c.Y, Y_FLANGE) and near(c.Z, CAR_TOP))
    part = fillet_where(part, R_CORNER / 2, Axis.Y, lambda c: near(c.Z, FLANGE_LO) and abs(c.X) > HALF_X - 0.01)

    cuts = []
    for sx in (-1, 1):
        x = sx * ta.HM_SCREW_X
        cuts.append(cyl_y(ta.M3_CLEAR, x, ta.SCREW_Z, Y0 - 1, SCREW_TIP + 0.5))   # blind, closed at the back face
        ny = Y0 + NUT_WALL   # hotend-mount screws: nut dropped into a slot from the top face, corners up/down
        cuts += [nut_pocket("y", x, ta.SCREW_Z, ny, ny + ta.NUT_T, "z"),
                 box(x - ta.NUT_AF / 2, x + ta.NUT_AF / 2, ny, ny + ta.NUT_T, ta.SCREW_Z, TOP_Z + 1)]
        for sy in (-1, 1):                               # M2 into the carriage, heads recessed in the top face
            hx, hy = sx * CAR_HOLE_ALONG / 2, CAR_Y + sy * CAR_HOLE_ACROSS / 2
            cuts += [cyl_z(M2_CLEAR, hx, hy, CAR_TOP - 1, TOP_Z + 1),
                     cyl_z(M2_HEAD_D, hx, hy, CAR_TOP + M2_UNDER_HEAD, TOP_Z + 1)]
    for c in cuts:
        part = part - c
    return part.solids()[0] if len(part.solids()) == 1 else part


def build_reference():
    """MGN7H carriage, a stretch of rail and 1515 extrusion, as plain boxes for fit checks and renders."""
    carriage = box(-CAR_L / 2, CAR_L / 2, CAR_Y - CAR_W / 2, CAR_Y + CAR_W / 2, RAIL_LO + 1.5, CAR_TOP)
    rail = box(-60, 60, CAR_Y - RAIL_W / 2, CAR_Y + RAIL_W / 2, RAIL_LO, RAIL_LO + RAIL_H)
    extrusion = box(-60, 60, CAR_Y - EXTRUSION / 2, CAR_Y + EXTRUSION / 2, RAIL_LO - EXTRUSION, RAIL_LO)
    return {"mgn7h_carriage": carriage - rail, "mgn7_rail": rail, "x_extrusion": extrusion}


def main(render_png=True):
    OUT.mkdir(parents=True, exist_ok=True)
    adapter, ducts = ta.build_part(), Compound([ta.build_duct(), ta.Rot(0, 0, 180) * ta.build_duct()])
    print(f"adapter with carriage mount: {len(adapter.solids())} solid(s), bbox {adapter.bounding_box().size}")
    print(f"mount screws M3x{MOUNT_SCREW_L:.0f}: tip {SCREW_TIP - Y0:.2f} behind the back tab (nut {NUT_WALL:.1f}..{NUT_WALL + 2.4:.1f}, "
          f"flange {FLANGE_T}, {Y_FLANGE - SCREW_TIP - 0.5:.2f} wall behind the blind hole)")
    print(f"rail centre Y={CAR_Y:.2f} (filament axis Y=0), carriage top z={CAR_TOP:.2f}, rail bottom z={RAIL_LO:.2f}, "
          f"nozzle z={ta.NOZZLE_Z:.2f}  ->  nozzle {CAR_Y:.2f} in front of the rail, {CAR_TOP - ta.NOZZLE_Z:.2f} below the carriage top")

    ref = build_reference()
    vendor = ta.load_vendor()
    print("interference volumes (mm3):")
    for k in ref:
        for n, v in [("adapter", adapter), ("ducts", ducts)] + list(vendor.items()):
            print(f"  {k} x {n}: {interference(ref[k], v)}")
    print(f"M2x5 carriage screws: heads recessed {PLATE_T - M2_UNDER_HEAD:.1f} mm, {M2_UNDER_HEAD:.1f} mm of plate under them")

    if render_png:
        from render import render
        render(OUT / "render_assembly_carriage.png",
               [adapter, vendor["fan_3010"], Compound([vendor["blower_R"], vendor["blower_L"]]),
                vendor["bmg"], Compound([ref["mgn7h_carriage"], ref["mgn7_rail"]]), vendor["hotend"]],
               "adapter(blue) fan(orange) blowers(red) BMG(green) MGN7H(purple) hotend(teal)")
    return adapter


if __name__ == "__main__":
    main()
