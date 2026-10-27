"""Wristwatch BMG -> TZ-V6 2.0 hotend-mount adapter with 3010 fan and 2x 3010 blowers.

Parametric build123d model. Run with a Python env that has build123d:
    python cad/toolhead_adapter.py            # builds part + assembly + checks + renders
Outputs go to ../output/.

Frame used throughout (mm):
    origin = filament axis on the BMG's bottom face
    +Z up (BMG above, nozzle below), -Y front (heatsink fan side), +Y back (BMG motor side)

Vendor models (BMG, hotend mount, hotend, fan, blower) are only placed, never modified.
Printed parts: the adapter, and a duct (x2) that screws to the shelf under each blower so it can be replaced.
"""
from pathlib import Path
import math
from build123d import (
    Axis, Box, Compound, Cylinder, Location, Plane, Pos, Rectangle, Rot, Vector,
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

HM_SEAT_DROP = 12.9          # heatsink top face below the mount top (underside of the mount's plate, z=-8.6 in its file)

# Hotend (assy hotend kit.stp, axis along kit Y). Used like the Mini Stealthburner: without the kit's top
# part (solid 1), so the heatsink's own top face (kit Y=-16.5) seats on the mount and takes its 4 screws.
HE_SOLIDS = [0, 2]           # heatsink, nozzle + heater
HE_TOP_Y = -16.5             # heatsink top face in the kit file
HE_TIP = 46.0                # nozzle tip below the heatsink top face (kit Y=-62.5)
HE_BLOCK = (14.0, 11.0)      # heater block footprint (kit X, kit Z); 20 mm tall, bottom 3 mm above the tip
HOTEND_ROT = 0               # about the nozzle axis; the mount's 4 screws allow 0/90. 0 = 14 mm side faces the ducts (worst case)

# Printed part
FIT = 0.1                    # clearance per side where the mount slides between front/back plates
PLATE_T = 6.0                # top plate thickness (mount top sits at z = -PLATE_T)
PLATE_HALF_X = 23.5
FRONT_T = 4.0                # fan plate (between mount face and 3010 fan)
FAN_PLATE_MARGIN = 2.0       # fan plate runs this far below the 3010 fan's bottom edge
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
BLOWER_Z = -26.0             # blower centre Z (top 5 mm under the plate, leaving height for the duct)

# Ducts: separate replaceable parts, screwed up into a shelf under each blower outlet
DUCT_WALL = 1.2
DUCT_EXIT = (16.0, 4.0)      # exit opening (along Y, across)
DUCT_BLOCK_GAP = 5.0         # min air gap from duct to the bare heater block side (sets the exit radius)
DUCT_CLEAR = 3.0             # lowest point of duct above nozzle tip
DUCT_AIM_BELOW_TIP = 0.0     # aim point relative to tip
SHELF_T = 4.0                # shelf under the blower outlet (part of the adapter)
DUCT_FLANGE_T = 2.0          # duct flange that screws to the shelf underside
DUCT_SCREW_Y = 18.0          # 2x M2.5x8 self-tapping per duct, just outside the blower's +-15 footprint
DUCT_SCREW_CLEAR = 2.8
LUG_H = 4.0                  # screw lugs above the shelf, beside the blower, for thread length

# Fillets. None inside the box (the mount slides in with FIT), in the blower's seat, or on the top face
# (bed face when printing, and the BMG sits on it).
R_CORNER = 3.0               # outer vertical corners: top plate, shelf/duct flange outer corners
R_SMALL = 1.0                # shelf inner corners, lugs, duct flange-to-tube junction
R_ARM_ROOT = 3.0             # concave, top plate underside to arm outer face (blower top sits 5 mm lower)
R_WINDOW = 2.0               # arm window corners

# ------------------------------------------------------------- derived values
MOUNT_TOP = -PLATE_T
NOZZLE_BELOW_MOUNT_TOP = HM_SEAT_DROP + HE_TIP
NOZZLE_Z = MOUNT_TOP - NOZZLE_BELOW_MOUNT_TOP
BLOCK_HALF_X = HE_BLOCK[0] / 2 if HOTEND_ROT % 180 == 0 else HE_BLOCK[1] / 2
Y_FRONT_IN = HM_FRONT - FIT                  # front plate inner face
Y_FRONT_OUT = Y_FRONT_IN - FRONT_T
Y_BACK_IN = HM_BACK + FIT
Y_BACK_OUT = Y_BACK_IN + BACK_T
SCREW_Z = MOUNT_TOP - HM_SCREW_DROP
FAN_Z = MOUNT_TOP - HM_FAN_DROP
ARM_X0 = HM_W / 2 + ARM_GAP
BL_X0 = ARM_X0 + ARM_T                        # blower inner face
OUT_LO = BLOWER_Z - 15.0                      # blower outlet face Z (+X blower)
SHELF_LO = OUT_LO - SHELF_T                   # shelf underside = duct flange top
FLANGE_LO = SHELF_LO - DUCT_FLANGE_T
OUT_X = (BL_X0 + BL_OUT_Y[0], BL_X0 + BL_OUT_Y[1])         # blower outlet in world X
OUT_Y = (BLOWER_Y + BL_OUT_Z[0], BLOWER_Y + BL_OUT_Z[1])   # ...and world Y
SHELF_X = (ARM_X0, BL_X0 + 10.5)
SHELF_HALF_Y = DUCT_SCREW_Y + 2.5
DUCT_SCREW_X = sum(OUT_X) / 2


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def fillet_where(shape, r, axis, where):
    """Fillet the edges parallel to axis (any edge if None) whose centre satisfies where(centre)."""
    edges = shape.edges() if axis is None else shape.edges().filter_by(axis)
    edges = [e for e in edges if where(e.center())]
    assert edges, "fillet_where: no edges matched"
    return shape.fillet(r, edges)


def near(a, b, tol=0.01):
    return abs(a - b) < tol


def shelf_box(z0, z1):
    """Shelf / duct flange outline under the +X blower, corners rounded."""
    b = box(*SHELF_X, -SHELF_HALF_Y, SHELF_HALF_Y, z0, z1)
    b = fillet_where(b, R_CORNER, Axis.Z, lambda c: near(c.X, SHELF_X[1]))
    return fillet_where(b, R_SMALL, Axis.Z, lambda c: near(c.X, SHELF_X[0]))


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
LOC_HOTEND = Pos(0, 0, MOUNT_TOP - HM_SEAT_DROP) * Rot(0, 0, HOTEND_ROT) * Rot(90, 0, 0) * Pos(0, -HE_TOP_Y, 0)  # kit Y -> world Z
LOC_BMG = Pos(-BMG_FILAMENT)
BMG_SOLIDS = [0, 2, 3, 6] + list(range(7, 33))  # complete extruder (body 0 + arm + plate "SOLID" + hardware)


# ------------------------------------------------------------------- the part
def blower_side():
    """Arm + duct shelf for the +X blower; the -X side is this rotated 180 deg about Z."""
    holes = [blower_world(x, 0, z) for x, z in BL_HOLES]
    arm = box(ARM_X0, BL_X0, -15.5, 15.5, SHELF_LO, 0)
    window = box(ARM_X0 - 1, BL_X0 + 1, -7.5, 7.5, BLOWER_Z - 9, BLOWER_Z + 9)
    arm = arm - window.fillet(R_WINDOW, window.edges().filter_by(Axis.X))
    shelf = shelf_box(SHELF_LO, OUT_LO)
    lugs = [box(*OUT_X, 15.3, SHELF_HALF_Y, OUT_LO, OUT_LO + LUG_H),
            box(*OUT_X, -SHELF_HALF_Y, -15.3, OUT_LO, OUT_LO + LUG_H)]
    lugs = [lug.fillet(R_SMALL, lug.edges().filter_by(Axis.Z)) for lug in lugs]
    solid = arm + shelf + lugs[0] + lugs[1]
    cuts = [box(*OUT_X, *OUT_Y, SHELF_LO - 1, OUT_LO + 0.01)]                  # air passage
    cuts += [cyl_x(BL_PILOT, p.Y, p.Z, ARM_X0 - 1, BL_X0 + 1) for p in holes]
    cuts += [cyl_z(BL_PILOT, DUCT_SCREW_X, sy * DUCT_SCREW_Y, SHELF_LO - 1, OUT_LO + LUG_H - 1) for sy in (-1, 1)]
    return solid, Compound(cuts)


def duct_exit():
    """Exit centre and air direction: as low as DUCT_CLEAR allows, out far enough to clear the block by DUCT_BLOCK_GAP."""
    h = DUCT_EXIT[1] / 2 + DUCT_WALL                  # half of the exit's outer size across the airflow
    ez = NOZZLE_Z + DUCT_CLEAR + h + 1.0
    aim = Vector(0, 0, NOZZLE_Z - DUCT_AIM_BELOW_TIP)
    r = BLOCK_HALF_X + DUCT_BLOCK_GAP + h
    for _ in range(20):                               # innermost exit edge sits h*|d.Z| inside the centre
        d = (aim - Vector(r, 0, ez)).normalized()
        r = BLOCK_HALF_X + DUCT_BLOCK_GAP + h * abs(d.Z)
    return Vector(r, 0, ez), d


def build_duct():
    """Replaceable duct for the +X blower. Print 2: the -X one is the same part turned 180 deg about Z."""
    exit_c, d = duct_exit()
    in_c = Vector(sum(OUT_X) / 2, sum(OUT_Y) / 2, FLANGE_LO)
    in_w, in_h = OUT_Y[1] - OUT_Y[0], OUT_X[1] - OUT_X[0]
    ex_w, ex_h = DUCT_EXIT
    in_pl = Plane(origin=in_c, x_dir=(0, 1, 0), z_dir=(0, 0, -1))
    ex_pl = Plane(origin=exit_c, x_dir=(0, 1, 0), z_dir=d)
    w2 = 2 * DUCT_WALL
    outer = loft([in_pl * Rectangle(in_w + w2, in_h + w2), ex_pl * Rectangle(ex_w + w2, ex_h + w2)])
    inner = loft([in_pl.offset(-0.5) * Rectangle(in_w, in_h), ex_pl.offset(0.5) * Rectangle(ex_w, ex_h)])
    flange = shelf_box(FLANGE_LO, SHELF_LO)
    duct = flange + outer
    # tube outline on the flange; its outer side runs 0.3 mm from the flange edge, too close to fillet
    in_x = (in_c.X - (in_h + w2) / 2 - 0.01, min(in_c.X + (in_h + w2) / 2 + 0.01, SHELF_X[1] - R_SMALL))
    duct = fillet_where(duct, R_SMALL, None, lambda c: near(c.Z, FLANGE_LO) and in_x[0] < c.X < in_x[1]
                        and abs(c.Y - in_c.Y) < (in_w + w2) / 2 + 0.01)
    duct = duct - inner - box(*OUT_X, *OUT_Y, FLANGE_LO - 0.01, SHELF_LO + 1)
    for sy in (-1, 1):
        duct = duct - cyl_z(DUCT_SCREW_CLEAR, DUCT_SCREW_X, sy * DUCT_SCREW_Y, FLANGE_LO - 1, SHELF_LO + 1)
    return duct.solids()[0] if len(duct.solids()) == 1 else duct


def build_part():
    top = box(-PLATE_HALF_X, PLATE_HALF_X, Y_FRONT_OUT, Y_BACK_OUT, -PLATE_T, 0)
    top = top.fillet(R_CORNER, top.edges().filter_by(Axis.Z))
    # front plate and back tab run out to the blower arms' outer faces, closing the frame into a box
    front = box(-BL_X0, BL_X0, Y_FRONT_OUT, Y_FRONT_IN, FAN_Z - 15.0 - FAN_PLATE_MARGIN, 0)
    back = box(-BL_X0, BL_X0, Y_BACK_IN, Y_BACK_OUT, MOUNT_TOP - BACK_TAB_H, 0)
    side_r, cuts_r = blower_side()
    side_l, cuts_l = Rot(0, 0, 180) * side_r, Rot(0, 0, 180) * cuts_r
    # concave fillet under the top plate's overhang at each arm, as a solid trimmed to the plate's outline
    # (an edge fillet fails there: the plate's front/back faces sit a fraction of a mm off the arm's)
    r = R_ARM_ROOT
    root = (box(BL_X0, BL_X0 + r, -SHELF_HALF_Y, SHELF_HALF_Y, -PLATE_T - r, -PLATE_T)
            - cyl_y(2 * r, BL_X0 + r, -PLATE_T - r, -SHELF_HALF_Y - 1, SHELF_HALF_Y + 1))
    roots = [(rr & Pos(0, 0, -PLATE_T) * top) for rr in (root, Rot(0, 0, 180) * root)]
    part = top + front + back + side_r + side_l + roots[0] + roots[1]

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
    he = import_step(ROOT / "assy hotend kit.stp").solids()
    return {
        "bmg": LOC_BMG * Compound([bmg[i] for i in BMG_SOLIDS]),
        "hotend_mount": LOC_MOUNT * import_step(ROOT / "hotend_mount.STEP"),
        "hotend": LOC_HOTEND * Compound([he[i] for i in HE_SOLIDS]),
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
    duct = build_duct()
    duct.label = "duct"
    export_step(duct, OUT / "duct.step")
    export_stl(duct, OUT / "duct.stl", tolerance=0.01, angular_tolerance=0.1)
    print(f"duct (print 2): volume {duct.volume:.0f} mm3, bbox {duct.bounding_box().size}")
    printed = {"adapter": part, "duct_R": duct, "duct_L": Rot(0, 0, 180) * duct}

    vendor = load_vendor()
    for k, v in list(vendor.items()) + list(printed.items()):
        v.label = k
    asm = Compound(list(printed.values()) + list(vendor.values()))
    export_step(asm, OUT / "toolhead_assembly.step")

    print("interference volumes (mm3):")
    names = list(vendor)
    for p in printed:
        for k in names:
            print(f"  {p} x {k}: {interference(printed[p], vendor[k])}")
    for p in ("duct_R", "duct_L"):
        print(f"  adapter x {p}: {interference(part, printed[p])}")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            print(f"  {a} x {b}: {interference(vendor[a], vendor[b])}")
    block = vendor["hotend"].solids()[-1]
    print(f"nozzle tip at z={NOZZLE_Z:.1f}, adapter lowest z={part.bounding_box().min.Z:.1f}, "
          f"duct lowest z={duct.bounding_box().min.Z:.1f}")
    print(f"duct exit r={duct_exit()[0].X:.1f}; gap duct to heater block: R {printed['duct_R'].distance_to(block):.2f}, "
          f"L {printed['duct_L'].distance_to(block):.2f} mm")

    if render_png:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from render import render
        ducts = Compound([printed["duct_R"], printed["duct_L"]])
        render(OUT / "render_part.png", [part, ducts], "adapter(blue) + 2 ducts(orange)")
        render(OUT / "render_duct.png", [duct], "duct (print 2)")
        render(OUT / "render_assembly.png",
               [part, vendor["hotend_mount"], vendor["fan_3010"], Compound([vendor["blower_R"], vendor["blower_L"]]),
                vendor["bmg"], ducts, vendor["hotend"]],
               "assembly: adapter(blue) mount(orange) fan(red) blowers(green) BMG(purple) ducts(teal) hotend(brown)")
    return part, duct, vendor


if __name__ == "__main__":
    main()
