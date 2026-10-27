"""Wristwatch BMG -> TZ-V6 2.0 hotend-mount adapter with 3010 fan and 2x 3010 blowers.

Parametric build123d model. Run with a Python env that has build123d:
    python cad/toolhead_adapter.py            # builds part + assembly + checks + renders
Outputs go to ../output/.

Frame used throughout (mm):
    origin = filament axis on the BMG's bottom face
    +Z up (BMG above, nozzle below), -Y front (heatsink fan side), +Y back (BMG motor side)

Vendor models (BMG, hotend mount, fan, blower) are only placed, never modified.
"""
from pathlib import Path
import math
from build123d import (
    Box, Compound, Cylinder, Location, Plane, Pos, Rectangle, Rot, Vector,
    export_step, export_stl, import_step, loft,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

# ---------------------------------------------------------------- parameters
# Wristwatch BMG (from "Wristwatch BMG v3.step", body 0 = complete assembly)
BMG_FILAMENT = Vector(-21.96, 103.24, 158.6)  # filament axis on bottom face, in the BMG file's coords
BMG_HOLE_X = 18.5            # 2x M3 at +-18.5 on the filament line (screws come down through the BMG flange)
BMG_FOOT_Y = (-14.54, 7.96)  # BMG bottom face Y extent
MOTOR_Y = 13.96              # motor sits behind this Y and dips ~0.6 mm below z=0

# Hotend mount (hotend_mount.STEP, flipped so its plate faces up)
HM_AXIS_Y = 90.44            # filament axis Y in the mount's own file
HM_TOP_Z = -21.5             # plate face (becomes top) in the mount's own file
HM_W = 30.8                  # X width
HM_FRONT, HM_BACK = 79.1 - HM_AXIS_Y, 101.29 - HM_AXIS_Y   # Y extent relative to axis
HM_HEIGHT = 42.4
HM_SCREW_X = 12.5            # 2x horizontal M3 through the mount plate (along Y)
HM_SCREW_DROP = 3.5          # ...this far below the mount top
HM_FAN_DROP = 21.5           # centre of the 28 mm fan opening below mount top

# Hotend: nozzle tip below the mount's top face. Not in any supplied model - MEASURE AND SET.
NOZZLE_BELOW_MOUNT_TOP = 61.0

# Printed part
FIT = 0.1                    # clearance per side where the mount slides between front/back plates
PLATE_T = 6.0                # top plate thickness (mount top sits at z = -PLATE_T)
PLATE_HALF_X = 23.5
FRONT_T = 4.0                # fan plate (between mount face and 3010 fan)
BACK_T = 4.0                 # back tab that takes the mount screws
BACK_TAB_H = 8.0
MOTOR_RELIEF = (13.0, 1.5)   # (from Y, depth) step on the top-back edge under the motor
INSERT_D, INSERT_L = 4.0, 4.0  # M3 heat-set inserts (M3x5x4 style); set to your inserts
M3_CLEAR, M3_HEAD_D, M3_HEAD_RECESS = 3.4, 6.0, 2.0
FILAMENT_D = 4.2             # PTFE passes BMG -> adapter -> mount

# Fan 3010 (axial, heatsink)
FAN_HOLE = 12.0              # holes at +-12, +-12
FAN_BORE = 28.0

# Blower 3010 (local file coords: 30x30 face in XZ, thickness Y 0..10, inlet on +Y face,
# outlet on -X edge spanning z -12..9, y 1.5..9, mounting holes at (x,z)=(12,-12),(-12,12))
BL_OUT_Z = (-12.0, 9.0)
BL_OUT_Y = (1.5, 9.0)
BL_HOLES = [(12.0, -12.0), (-12.0, 12.0)]
BL_PILOT = 2.2               # self-tapping pilot for M2.5 screws through the blower ears
ARM_T = 3.0
ARM_GAP = 0.2                # arm to mount side wall
BLOWER_Y = 0.0               # blower centre Y (right blower)
BLOWER_Z = -30.0             # blower centre Z

# Ducts
DUCT_WALL = 1.2
DUCT_EXIT = (16.0, 4.0)      # exit opening (along Y, across)
DUCT_EXIT_R = 13.0           # exit centre distance from nozzle axis
DUCT_CLEAR = 3.0             # lowest point of duct above nozzle tip
DUCT_AIM_BELOW_TIP = 0.0     # aim point relative to tip

# ------------------------------------------------------------- derived values
MOUNT_TOP = -PLATE_T
NOZZLE_Z = MOUNT_TOP - NOZZLE_BELOW_MOUNT_TOP
Y_FRONT_IN = HM_FRONT - FIT                  # front plate inner face
Y_FRONT_OUT = Y_FRONT_IN - FRONT_T
Y_BACK_IN = HM_BACK + FIT
Y_BACK_OUT = Y_BACK_IN + BACK_T
SCREW_Z = MOUNT_TOP - HM_SCREW_DROP
FAN_Z = MOUNT_TOP - HM_FAN_DROP
ARM_X0 = HM_W / 2 + ARM_GAP
BL_X0 = ARM_X0 + ARM_T                        # blower inner face


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_y(d, x, z, y0, y1):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(d / 2, abs(y1 - y0))


def cyl_x(d, y, z, x0, x1):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, abs(x1 - x0))


def cyl_z(d, x, y, z0, z1):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, abs(z1 - z0))


# --------------------------------------------------------- vendor placements
BLOWER_PLANE = Plane(origin=(BL_X0, BLOWER_Y, BLOWER_Z), x_dir=(0, 0, 1), z_dir=(0, 1, 0))
# blower local (x, y, z) -> world (x0 + y, Y + z, Z + x): outlet (-X local) points down, inlet faces out


def blower_world(lx, ly, lz):
    return Vector(BL_X0 + ly, BLOWER_Y + lz, BLOWER_Z + lx)


LOC_MOUNT = Pos(0, -HM_AXIS_Y, MOUNT_TOP + HM_TOP_Z) * Rot(0, 180, 0)
LOC_FAN = Pos(0, Y_FRONT_OUT - 5.0, FAN_Z) * Rot(-90, 0, 0) * Pos(225.0, 0, -295.02)  # hub side faces heatsink
LOC_BLOWER_R = Location(BLOWER_PLANE)
LOC_BLOWER_L = Rot(0, 0, 180) * LOC_BLOWER_R
LOC_BMG = Pos(-BMG_FILAMENT)
BMG_SOLIDS = [0, 2, 3, 6] + list(range(7, 33))  # complete extruder (body 0 + arm + plate "SOLID" + hardware)


# ------------------------------------------------------------------- the part
def blower_side():
    """Arm + duct for the +X blower; the -X side is this rotated 180 deg about Z."""
    out_lo = BLOWER_Z + (-15.0)                       # blower outlet face Z
    holes = [blower_world(x, 0, z) for x, z in BL_HOLES]
    arm = box(ARM_X0, BL_X0, -15.5, 15.5, out_lo - 3.0, 0)
    window = box(ARM_X0 - 1, BL_X0 + 1, -7.5, 7.5, BLOWER_Z - 9, BLOWER_Z + 9)
    arm = arm - window

    inlet_c = blower_world(-15.0, sum(BL_OUT_Y) / 2, sum(BL_OUT_Z) / 2)
    in_w, in_h = BL_OUT_Z[1] - BL_OUT_Z[0], BL_OUT_Y[1] - BL_OUT_Y[0]
    aim = Vector(0, 0, NOZZLE_Z - DUCT_AIM_BELOW_TIP)
    # exit centre: DUCT_EXIT_R out from the axis, low enough that the duct clears the tip by DUCT_CLEAR
    ex_w, ex_h = DUCT_EXIT
    ez = NOZZLE_Z + DUCT_CLEAR + ex_h / 2 + DUCT_WALL + 1.0
    exit_c = Vector(DUCT_EXIT_R, 0, ez)
    d = (aim - exit_c).normalized()
    in_pl = Plane(origin=inlet_c, x_dir=(0, 1, 0), z_dir=(0, 0, -1))
    ex_pl = Plane(origin=exit_c, x_dir=(0, 1, 0), z_dir=d)
    w2 = 2 * DUCT_WALL
    outer = loft([in_pl * Rectangle(in_w + w2, in_h + w2), ex_pl * Rectangle(ex_w + w2, ex_h + w2)])
    inner = loft([in_pl.offset(-0.5) * Rectangle(in_w, in_h), ex_pl.offset(0.5) * Rectangle(ex_w, ex_h)])
    bridge = box(ARM_X0, inlet_c.X, -12.0, 9.0, out_lo - 3.0, out_lo)
    solid = arm + bridge + outer
    cuts = inner + Compound([cyl_x(BL_PILOT, p.Y, p.Z, ARM_X0 - 1, BL_X0 + 1) for p in holes])
    return solid, cuts


def build_part():
    top = box(-PLATE_HALF_X, PLATE_HALF_X, Y_FRONT_OUT, Y_BACK_OUT, -PLATE_T, 0)
    front = box(-HM_W / 2, HM_W / 2, Y_FRONT_OUT, Y_FRONT_IN, FAN_Z - 15.0, 0)
    back = box(-HM_W / 2, HM_W / 2, Y_BACK_IN, Y_BACK_OUT, MOUNT_TOP - BACK_TAB_H, 0)
    side_r, cuts_r = blower_side()
    side_l, cuts_l = Rot(0, 0, 180) * side_r, Rot(0, 0, 180) * cuts_r
    part = top + front + back + side_r + side_l

    cuts = [
        box(-50, 50, MOTOR_RELIEF[0], 50, -MOTOR_RELIEF[1], 1),                 # under the motor
        cyl_z(FILAMENT_D, 0, 0, -PLATE_T - 1, 1),
        cyl_y(FAN_BORE, 0, FAN_Z, Y_FRONT_OUT - 1, Y_FRONT_IN + 1),
        cuts_r, cuts_l,
    ]
    for sx in (-1, 1):
        cuts += [
            cyl_z(INSERT_D, sx * BMG_HOLE_X, 0, -PLATE_T, 1),                   # BMG screws (insert from top)
            cyl_y(M3_CLEAR, sx * HM_SCREW_X, SCREW_Z, Y_FRONT_OUT - 1, Y_BACK_IN),  # mount screws
            cyl_y(M3_HEAD_D, sx * HM_SCREW_X, SCREW_Z, Y_FRONT_OUT - 1, Y_FRONT_OUT + M3_HEAD_RECESS),
            cyl_y(INSERT_D, sx * HM_SCREW_X, SCREW_Z, Y_BACK_OUT - INSERT_L - 0.5, Y_BACK_OUT + 1),
        ]
        for sz in (-1, 1):                                                      # fan inserts
            cuts.append(cyl_y(INSERT_D, sx * FAN_HOLE, FAN_Z + sz * FAN_HOLE, Y_FRONT_OUT - 1, Y_FRONT_IN + 0.01))
    for c in cuts:
        part = part - c
    return part.solids()[0] if len(part.solids()) == 1 else part


# ------------------------------------------------------------ vendor geometry
def load_vendor():
    bmg = import_step(ROOT / "Wristwatch BMG v3.step").solids()
    return {
        "bmg": LOC_BMG * Compound([bmg[i] for i in BMG_SOLIDS]),
        "hotend_mount": LOC_MOUNT * import_step(ROOT / "hotend_mount.STEP"),
        "fan_3010": LOC_FAN * import_step(ROOT / "3010 fan.step"),
        "blower_R": LOC_BLOWER_R * import_step(ROOT / "3010 blower.STEP"),
        "blower_L": LOC_BLOWER_L * import_step(ROOT / "3010 blower.STEP"),
    }


def _t(v):
    return (v.X, v.Y, v.Z)


def interference(a, b):
    """Overlap volume and its bbox, solid by solid (compound booleans on vendor STEPs are unreliable)."""
    vol, boxes, failed = 0.0, [], 0
    for sa in a.solids():
        for sb in b.solids():
            ba, bb = sa.bounding_box(), sb.bounding_box()
            if any(_t(ba.min)[i] > _t(bb.max)[i] or _t(bb.min)[i] > _t(ba.max)[i] for i in range(3)):
                continue
            try:
                r = sa & sb
            except Exception:
                failed += 1
                continue
            for s in (r.solids() if r is not None else []):
                if s.volume > 1e-3:
                    vol += s.volume
                    boxes.append(s.bounding_box())
    msg = f"{vol:.2f}"
    if boxes:
        lo = [min(_t(bx.min)[i] for bx in boxes) for i in range(3)]
        hi = [max(_t(bx.max)[i] for bx in boxes) for i in range(3)]
        msg += f"  in {tuple(round(v, 2) for v in lo)}..{tuple(round(v, 2) for v in hi)}"
    if failed:
        msg += f"  ({failed} solid pairs failed)"
    return msg


def main(render_png=True):
    OUT.mkdir(exist_ok=True)
    part = build_part()
    part.label = "toolhead_adapter"
    export_step(part, OUT / "toolhead_adapter.step")
    export_stl(part, OUT / "toolhead_adapter.stl", tolerance=0.01, angular_tolerance=0.1)
    print(f"part: {len(part.solids())} solid(s), volume {part.volume:.0f} mm3, bbox {part.bounding_box().size}")

    vendor = load_vendor()
    for k, v in vendor.items():
        v.label = k
    asm = Compound([part] + list(vendor.values()))
    export_step(asm, OUT / "toolhead_assembly.step")

    print("interference volumes (mm3):")
    names = list(vendor)
    for k in names:
        print(f"  part x {k}: {interference(part, vendor[k])}")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            print(f"  {a} x {b}: {interference(vendor[a], vendor[b])}")
    print(f"nozzle tip (estimated) at z={NOZZLE_Z:.1f}, part lowest point z={part.bounding_box().min.Z:.1f}")

    if render_png:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from render import render
        render(OUT / "render_part.png", [part], "toolhead_adapter")
        render(OUT / "render_assembly.png",
               [part, vendor["hotend_mount"], vendor["fan_3010"], Compound([vendor["blower_R"], vendor["blower_L"]]), vendor["bmg"]],
               "assembly: adapter(blue) mount(orange) fan(red) blowers(green) BMG(purple)")
    return part, vendor


if __name__ == "__main__":
    main()
