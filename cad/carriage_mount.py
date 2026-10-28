"""MGN7H carriage mount for the toolhead adapter (Voron 0.2 X axis).

Parametric build123d model, same world frame as toolhead_adapter.py:
    origin = filament axis on the BMG's bottom face, +Z up, -Y front (fan side), +Y back (BMG motor side)
Run:
    python cad/carriage_mount.py              # builds part + checks + renders
Outputs go to ../output/inserts/ or ../output/nuts/ (with --nuts).

Layout: the MGN7H rail lies on top of the X extrusion (running along X), so the carriage faces up, toward the
BMG motor. The mount is an L: a plate that sits on top of the carriage, under the motor, plus a flange that
bolts against the adapter's back face. The flange takes the two hotend-mount screws (M3x35 instead of M3x30)
in heat-set inserts, so those inserts move from the adapter's back tab into the flange.
With --nuts, M3 nuts instead: dropped into slots that open on the top face, before the toolhead goes on.
To take the toolhead off, remove those two screws from the front. The mount stays on the carriage.
"""
from pathlib import Path
import sys
from build123d import Axis, Compound, Pos, export_step, export_stl

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

MOTOR_LOW_Z = -0.6           # lowest point of the BMG motor (sits behind MOTOR_Y)
MOTOR_CLEAR = 1.0            # plate top below the motor
PLATE_T = 5.0                # plate on top of the carriage
FLANGE_T = 7.0               # flange against the adapter's back face (holds the inserts, M3x35 tip ends inside)
FLANGE_SIDE_GAP = 0.2        # flange X edge to the blowers
CAR_GAP = 2.5                # flange back face to the carriage front edge (room for the inside fillet)
PLATE_MARGIN = 2.0           # plate past the carriage's back edge
NUT_WALL = 2.0               # flange in front of the nut slots (takes the screw load)
M2_CLEAR, M2_HEAD_D, M2_HEAD_RECESS = 2.4, 4.2, 2.0   # M2x5 SHCS: 3 mm plate under the head + 2 mm thread
R_CORNER, R_INSIDE = 3.0, 2.0

# ------------------------------------------------------------- derived values
Y0 = ta.Y_BACK_OUT                                   # adapter back face = flange front face
ARM_RELIEF = ta.ARM_HALF_Y - Y0 + 0.35               # the blower arms stand proud of the back tab: relief in the flange
Y_FLANGE = Y0 + FLANGE_T
TOP_Z = MOTOR_LOW_Z - MOTOR_CLEAR                    # top face of plate and flange (flat, the print bed face)
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
        # relief for the blower arms' back faces
        cuts.append(box(*sorted((sx * (ta.ARM_X0 - 0.3), sx * (HALF_X + 1))), Y0 - 1, Y0 + ARM_RELIEF, FLANGE_LO - 1, TOP_Z + 1))
        x = sx * ta.HM_SCREW_X
        cuts.append(cyl_y(ta.M3_CLEAR, x, ta.SCREW_Z, Y0 - 1, Y_FLANGE + 1))
        if ta.NUTS:   # hotend-mount screws: nut dropped into a slot from the top face, corners up/down
            ny = Y0 + NUT_WALL
            cuts += [nut_pocket("y", x, ta.SCREW_Z, ny, ny + ta.NUT_T, "z"),
                     box(x - ta.NUT_AF / 2, x + ta.NUT_AF / 2, ny, ny + ta.NUT_T, ta.SCREW_Z, TOP_Z + 1)]
        else:         # hotend-mount screws: insert from the front (contact) face
            cuts.append(cyl_y(ta.INSERT_D, x, ta.SCREW_Z, Y0 - 1, Y0 + ta.INSERT_L + 0.5))
        for sy in (-1, 1):                               # M2 into the carriage, heads recessed in the top face
            hx, hy = sx * CAR_HOLE_ALONG / 2, CAR_Y + sy * CAR_HOLE_ACROSS / 2
            cuts += [cyl_z(M2_CLEAR, hx, hy, CAR_TOP - 1, TOP_Z + 1),
                     cyl_z(M2_HEAD_D, hx, hy, TOP_Z - M2_HEAD_RECESS, TOP_Z + 1)]
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
    mount = build_mount()
    mount.label = "carriage_mount"
    ta.export(mount, "carriage_mount")
    print(f"carriage mount: {len(mount.solids())} solid(s), volume {mount.volume:.0f} mm3, bbox {mount.bounding_box().size}")
    tip = ta.Y_FRONT_OUT + ta.M3_HEAD_RECESS + 35 - Y0
    print(f"mount screws M3x35: tip {tip:.2f} behind the flange's front face (flange {FLANGE_T}"
          + (f", nut {NUT_WALL:.1f}..{NUT_WALL + 2.4:.1f})" if ta.NUTS else f", insert 0..{ta.INSERT_L:.1f})"))
    print(f"rail centre Y={CAR_Y:.2f} (filament axis Y=0), carriage top z={CAR_TOP:.2f}, rail bottom z={RAIL_LO:.2f}, "
          f"nozzle z={ta.NOZZLE_Z:.2f}  ->  nozzle {CAR_Y:.2f} in front of the rail, {CAR_TOP - ta.NOZZLE_Z:.2f} below the carriage top")

    adapter, ducts = ta.build_part(), Compound([ta.build_duct(), ta.Rot(0, 0, 180) * ta.build_duct()])
    ref = build_reference()
    vendor = ta.load_vendor()
    print("interference volumes (mm3):")
    for k, v in [("adapter", adapter), ("ducts", ducts)] + list(ref.items()) + list(vendor.items()):
        print(f"  carriage_mount x {k}: {interference(mount, v)}")
    for k in ("x_extrusion", "mgn7_rail"):
        for n, v in [("adapter", adapter), ("ducts", ducts)] + list(vendor.items()):
            print(f"  {k} x {n}: {interference(ref[k], v)}")
    print(f"gap mount to BMG: {mount.distance_to(vendor['bmg']):.2f} mm (motor not modelled: top face {MOTOR_CLEAR} mm under z={MOTOR_LOW_Z})")

    if render_png:
        from render import render
        render(OUT / "render_carriage_mount.png", [mount], "MGN7H carriage mount")
        render(OUT / "render_assembly_carriage.png",
               [adapter, mount, vendor["fan_3010"], Compound([vendor["blower_R"], vendor["blower_L"]]),
                vendor["bmg"], Compound([ref["mgn7h_carriage"], ref["mgn7_rail"]]), vendor["hotend"]],
               "adapter(blue) carriage mount(orange) fan(red) blowers(green) BMG(purple) MGN7H(teal) hotend(brown)")
    return mount


if __name__ == "__main__":
    main()
