"""Wristwatch BMG -> TZ-V6 2.0 hotend-mount adapter with 3010 fan and 2x 3010 blowers.

Parametric build123d model. Run with a Python env that has build123d:
    python cad/toolhead_adapter.py            # builds part + assembly + checks + renders
    python cad/toolhead_adapter.py --nuts     # captive-nut version
Outputs go to ../output/inserts/ or ../output/nuts/.

Captive-nut version: no heat-set inserts and no self-tapping screws. M3 nuts sit in pockets and slots (BMG,
back tab, duct lugs), and the 3010 fan and both blowers snap into cradles with no screws.

Frame used throughout (mm):
    origin = filament axis on the BMG's bottom face
    +Z up (BMG above, nozzle below), -Y front (heatsink fan side), +Y back (BMG motor side)

Vendor models (BMG, hotend mount, hotend, fan, blower) are only placed, never modified.
Printed parts: the adapter, and a duct (x2) that screws to the shelf under each blower so it can be replaced.
"""
from pathlib import Path
import math
import sys
from build123d import (
    Axis, Box, Compound, Cone, Cylinder, Location, Plane, Polygon, Pos, Rectangle, RegularPolygon, Rot, Vector,
    export_step, export_stl, extrude, import_step, loft,
)

ROOT = Path(__file__).resolve().parent.parent
NUTS = "--nuts" in sys.argv  # captive-nut version (see the module docstring)
OUT = ROOT / "output" / ("nuts" if NUTS else "inserts")

# ---------------------------------------------------------------- parameters
# Wristwatch BMG (from "Wristwatch BMG v3.step", body 0 = complete assembly)
BMG_FILAMENT = Vector(-21.96, 103.24, 158.6)  # filament axis on bottom face, in the BMG file's coords
BMG_HOLE_X = 17.5            # 2x M3 at +-17.5 on the filament line (screws come down through the BMG flange)
BMG_FLANGE_T = 3.0           # BMG flange the screws pass through
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

# Hotend: TZ-V6 2.0, from Trianglelab's dimension drawing. There is no vendor model: build_hotend() makes a
# stand-in from these. Used like the Mini Stealthburner: without the kit's top part, so the heatsink's top face
# seats on the mount and takes its 4 M2.5 screws (11.5 mm square).
HE_SINK_D, HE_SINK_H = 22.0, 20.0   # heatsink; its bottom is 25.6 above the tip
HE_TIP = 45.6                # nozzle tip below the heatsink top face
HE_BLOCK = (10.0, 8.2)       # ceramic heater footprint incl. its ears (along X, along Y at HOTEND_ROT=0)
HE_BLOCK_H, HE_BLOCK_LO = 17.0, 3.5  # heater height, and its bottom above the tip (scaled off the drawing)
HOTEND_ROT = 0               # about the nozzle axis; the mount's 4 screws allow 0/90. 0 = 10 mm side faces the ducts (worst case)

# Printed part
FIT = 0.1                    # clearance per side where the mount slides between front/back plates
PLATE_T = 6.0                # top plate thickness (mount top sits at z = -PLATE_T)
PLATE_HALF_X = 23.5
FRONT_T = 4.0                # fan plate (between mount face and 3010 fan)
FAN_PLATE_MARGIN = 2.0       # fan plate runs this far below the 3010 fan's bottom edge
BACK_T = 5.0 if NUTS else 4.0  # back tab that takes the mount screws (thicker behind a nut pocket)
BACK_TAB_H = 8.0
MOTOR_RELIEF = (13.0, 1.5)   # (from Y, depth) step on the top-back edge under the motor
INSERT_D, INSERT_L = 4.0, 4.0  # M3 heat-set inserts (M3x5x4 style); set to your inserts
M3_CLEAR, M3_HEAD_D, M3_HEAD_RECESS = 3.4, 6.0, 2.0
FILAMENT_D = 4.2             # PTFE passes BMG -> adapter -> mount

# Captive-nut version
NUT_AF, NUT_T = 5.7, 2.7     # pocket across flats / thickness for M3 nuts (5.5 x 2.4)
BMG_NUT_ROOF = 2.5           # top plate above the BMG nut slots (slots run in from the side edges)
CRADLE_FIT = 0.15            # per side, fan and blowers in their snap-in cradles
CRADLE_WALL = 1.6
SNAP_LIP = (1.0, 1.2)        # lip overlap onto the fan/blower's outer face, lip thickness (ramped for snapping in)
SNAP_GAP = 0.5               # slot that frees a blower cradle wall from the shelf so it can flex
FAN_PEG_D, FAN_PEG_L = 2.8, 3.0  # pegs into the fan's two lower holes
BL_WIRE_X = (-10.0, -2.0)    # notch for the blower's wire, in blower-local x; it leaves the local +z side

# Fan 3010 (axial, heatsink)
FAN_HOLE = 12.0              # holes at +-12, +-12
FAN_BORE = 28.0
SNAP_LIP_Z = 7.0             # fan/blower lips only beyond this distance from its centre (corners, clear of the inlet)

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
DUCT_SCREW_Y = 20.5 if NUTS else 18.0  # 2 screws per duct, outside the blower's +-15 footprint (and its cradle)
DUCT_SCREW_CLEAR = M3_CLEAR if NUTS else 2.8  # M3x10 into a nut on the lug, or M2.5x8 self-tapping
LUG_H = 4.0                  # screw lugs above the shelf, beside the blower, for thread length

# Fillets. None inside the box (the mount slides in with FIT), in the blower's seat, or on the top face
# (bed face when printing, and the BMG sits on it).
R_CORNER = 3.0               # outer vertical corners: top plate, shelf/duct flange outer corners
R_SMALL = 1.0                # shelf inner corners, lugs, duct flange-to-tube junction
R_ARM_ROOT = 3.0             # concave, top plate underside to arm outer face (blower top sits 5 mm lower)
R_WINDOW = 2.0               # arm window corners

# ------------------------------------------------------------- derived values
MOUNT_TOP = -PLATE_T
BMG_SCREW_L = 10.0 if NUTS else 8.0
BMG_SCREW_DEPTH = BMG_SCREW_L - BMG_FLANGE_T   # BMG screw tip below the top face
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
SHELF_HALF_Y = DUCT_SCREW_Y + (3.5 if NUTS else 2.5)
DUCT_SCREW_X = sum(OUT_X) / 2
ARM_HALF_Y = 15.0 + CRADLE_FIT + CRADLE_WALL if NUTS else 15.5  # the blower cradle's walls grow off the arm ends
LUG_Y0 = ARM_HALF_Y + SNAP_GAP if NUTS else 15.3
FAN_FACE_Y = Y_FRONT_OUT - 10.0 - CRADLE_FIT  # fan's outer (intake) face, against the cradle lips


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


def nut_pocket(axis, a, b, l0, l1, corners):
    """Hex pocket for an M3 nut along axis "z" (at x=a, y=b) or "y" (at x=a, z=b), from l0 to l1 on that axis.
    corners: the world axis its corners point along ("x", or "y"/"z" across the other way)."""
    hexagon = RegularPolygon(NUT_AF / math.sqrt(3), 6)          # corners along local X
    if corners != "x":
        hexagon = Rot(0, 0, 90) * hexagon
    prism = extrude(hexagon, abs(l1 - l0))
    if axis == "z":
        return Pos(a, b, min(l0, l1)) * prism
    return Pos(a, max(l0, l1), b) * Rot(90, 0, 0) * prism       # local Z -> -Y, local Y -> Z


def prism_z(pts, z0, z1):
    """Prism over an XY polygon, from z0 to z1."""
    area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    if area2 < 0:                                                # counter-clockwise, so it extrudes up
        pts = pts[::-1]
    return Pos(0, 0, z0) * extrude(Polygon(*pts, align=None), z1 - z0)


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
    """Arm + duct shelf for the +X blower; the -X side is this rotated 180 deg about Z."""
    holes = [blower_world(x, 0, z) for x, z in BL_HOLES]
    arm = box(ARM_X0, BL_X0, -ARM_HALF_Y, ARM_HALF_Y, SHELF_LO, 0)
    window = box(ARM_X0 - 1, BL_X0 + 1, -7.5, 7.5, BLOWER_Z - 9, BLOWER_Z + 9)
    arm = arm - window.fillet(R_WINDOW, window.edges().filter_by(Axis.X))
    shelf = shelf_box(SHELF_LO, OUT_LO)
    lug_top = OUT_LO + LUG_H
    if NUTS:   # lugs follow the shelf's rounded outline, out past the cradle walls
        lugs = [shelf_box(OUT_LO, lug_top) & box(ARM_X0 - 1, 40, *sorted((sy * LUG_Y0, sy * 40)), OUT_LO - 1, lug_top + 1)
                for sy in (1, -1)]
    else:
        lugs = [box(*OUT_X, LUG_Y0, SHELF_HALF_Y, OUT_LO, lug_top), box(*OUT_X, -SHELF_HALF_Y, -LUG_Y0, OUT_LO, lug_top)]
        lugs = [lug.fillet(R_SMALL, lug.edges().filter_by(Axis.Z)) for lug in lugs]
    solid = arm + shelf + lugs[0] + lugs[1]
    cuts = [box(*OUT_X, *OUT_Y, SHELF_LO - 1, OUT_LO + 0.01)]                  # air passage
    if NUTS:
        solid = solid + blower_cradle()
        for sy in (-1, 1):   # M3x10 up through the duct flange and shelf, into a nut dropped in on top of the lug
            y = sy * DUCT_SCREW_Y
            cuts += [cyl_z(M3_CLEAR, DUCT_SCREW_X, y, SHELF_LO - 1, lug_top + 1),
                     nut_pocket("z", DUCT_SCREW_X, y, lug_top - NUT_T, lug_top + 1, "x")]
        # notch for the wire, which leaves the blower's back side (+Y) near the outlet end
        cuts.append(box(BL_X0, 40, 14.0, ARM_HALF_Y + 1, BLOWER_Z + BL_WIRE_X[0], BLOWER_Z + BL_WIRE_X[1]))
    else:
        cuts += [cyl_x(BL_PILOT, p.Y, p.Z, ARM_X0 - 1, BL_X0 + 1) for p in holes]
        cuts += [cyl_z(BL_PILOT, DUCT_SCREW_X, sy * DUCT_SCREW_Y, SHELF_LO - 1, lug_top - 1) for sy in (-1, 1)]
    return solid, Compound(cuts)


def blower_cradle():
    """Snap-in cradle for the +X blower: a block filling the gap above it up to the top plate (reaching the
    top face, so it prints on the bed), and front/back walls growing off the arm ends. The walls are free of the
    shelf (SNAP_GAP), so they flex as the blower is pushed in; ramped lips at their bottom outer corners then
    hold its outer face. The block above stops it from tipping out about those lips."""
    x1 = BL_X0 + 10.0 + CRADLE_FIT                       # blower outer face, plus fit
    x2 = x1 + SNAP_LIP[1]
    top = box(BL_X0, x2, -ARM_HALF_Y, ARM_HALF_Y, BLOWER_Z + 15.0 + CRADLE_FIT, 0)
    y_in = 15.0 + CRADLE_FIT
    cradle = top
    for sy in (-1, 1):
        cradle = cradle + box(BL_X0 - 0.01, x2, *sorted((sy * y_in, sy * ARM_HALF_Y)), OUT_LO + SNAP_GAP, 0)
        lip = [(x1, sy * y_in), (x1, sy * (y_in - SNAP_LIP[0])), (x2, sy * y_in)]
        cradle = cradle + prism_z(lip, OUT_LO + SNAP_GAP, BLOWER_Z - SNAP_LIP_Z)
    return cradle


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
    if NUTS:
        part = part + fan_cradle()

    cuts = [
        box(-50, 50, MOTOR_RELIEF[0], 50, -MOTOR_RELIEF[1], 1),                 # under the motor
        cyl_z(FILAMENT_D, 0, 0, -PLATE_T - 1, 1),
        cyl_y(FAN_BORE, 0, FAN_Z, Y_FRONT_OUT - 1, Y_FRONT_IN + 1),
        cuts_r, cuts_l,
    ]
    for sx in (-1, 1):
        x = sx * HM_SCREW_X
        cuts += [
            cyl_y(M3_CLEAR, x, SCREW_Z, Y_FRONT_OUT - 1, Y_BACK_IN),            # mount screws
            cyl_y(M3_HEAD_D, x, SCREW_Z, Y_FRONT_OUT - 1, Y_FRONT_OUT + M3_HEAD_RECESS),
        ]
        if NUTS:
            # BMG screws: M3x10 down into a nut slid in from the side edge, under BMG_NUT_ROOF of plate
            bx, nz = sx * BMG_HOLE_X, -BMG_NUT_ROOF
            cuts += [cyl_z(M3_CLEAR, bx, 0, -BMG_SCREW_DEPTH - 1, 1),
                     nut_pocket("z", bx, 0, nz - NUT_T, nz, "x"),
                     box(*sorted((bx, sx * 40)), -NUT_AF / 2, NUT_AF / 2, nz - NUT_T, nz),
                     # mount screws: nut in a pocket in the back face, corners up/down so it prints unsupported
                     nut_pocket("y", x, SCREW_Z, Y_BACK_OUT - NUT_T, Y_BACK_OUT + 1, "z")]
        else:
            cuts += [cyl_z(INSERT_D, sx * BMG_HOLE_X, 0, -PLATE_T, 1),          # BMG screws (insert from top)
                     cyl_y(INSERT_D, x, SCREW_Z, Y_BACK_OUT - INSERT_L - 0.5, Y_BACK_OUT + 1)]
            for sz in (-1, 1):                                                  # fan inserts
                cuts.append(cyl_y(INSERT_D, sx * FAN_HOLE, FAN_Z + sz * FAN_HOLE, Y_FRONT_OUT - 1, Y_FRONT_IN + 0.01))
    for c in cuts:
        part = part - c
    return part.solids()[0] if len(part.solids()) == 1 else part


def fan_cradle():
    """Snap-in cradle for the 3010 fan on the front plate: side walls with ramped lips over its outer face's
    corners, and two pegs into its lower holes so it can't slide. No top wall: the mount screws' heads are there."""
    x_in = 15.0 + CRADLE_FIT
    y_lip = FAN_FACE_Y - SNAP_LIP[1]
    z0, z1 = FAN_Z - 15.0, FAN_Z + 15.0
    cradle = None
    for sx in (-1, 1):
        wall = box(*sorted((sx * x_in, sx * (x_in + CRADLE_WALL))), y_lip, Y_FRONT_OUT + 0.01, z0, z1)
        lip = [(sx * x_in, FAN_FACE_Y), (sx * (x_in - SNAP_LIP[0]), FAN_FACE_Y), (sx * x_in, y_lip)]
        wall = wall + prism_z(lip, z0, FAN_Z - SNAP_LIP_Z) + prism_z(lip, FAN_Z + SNAP_LIP_Z, z1)
        peg = cyl_y(FAN_PEG_D, sx * FAN_HOLE, FAN_Z - FAN_HOLE, Y_FRONT_OUT - FAN_PEG_L, Y_FRONT_OUT + 0.01)
        cradle = wall + peg if cradle is None else cradle + wall + peg
    return cradle


def build_fit_test(part):
    """Two small pieces cut from the adapter to check the snap fits before printing it all, laid out for printing:
    the fan cradle on a 2 mm slice of the front plate (plate face down), and the right blower's cradle with its
    shelf, lugs and the BMG nut slot (top face down, as in the adapter)."""
    fan = part & box(-19, 19, FAN_FACE_Y - 5, Y_FRONT_OUT + 2.0, FAN_Z - 18, FAN_Z + 18)
    blower = part & box(ARM_X0, 40, -SHELF_HALF_Y - 1, SHELF_HALF_Y + 1, SHELF_LO - 1, 1)
    fan, blower = on_bed(fan, Rot(-90, 0, 0)), on_bed(blower, PRINT_ROT)   # Rot(-90, 0, 0): +Y face down
    gap = 4.0
    return Compound([Pos(-fan.bounding_box().size.X / 2 - gap / 2, 0, 0) * fan,
                     Pos(blower.bounding_box().size.X / 2 + gap / 2, 0, 0) * blower])


# ------------------------------------------------------------ vendor geometry
def build_hotend():
    """Stand-in TZ-V6 2.0 from the drawing: heatsink, heat break, nozzle, heater (last: used for the duct gap)."""
    top = MOUNT_TOP - HM_SEAT_DROP
    block_lo = NOZZLE_Z + HE_BLOCK_LO
    bx, by = HE_BLOCK if HOTEND_ROT % 180 == 0 else HE_BLOCK[::-1]
    return Compound([
        cyl_z(HE_SINK_D, 0, 0, top - HE_SINK_H, top),
        cyl_z(5.0, 0, 0, block_lo + HE_BLOCK_H, top - HE_SINK_H),
        Pos(0, 0, NOZZLE_Z + HE_BLOCK_LO / 2) * Cone(0.5, 3.5, HE_BLOCK_LO),
        box(-bx / 2, bx / 2, -by / 2, by / 2, block_lo, block_lo + HE_BLOCK_H),
    ])


def load_vendor():
    bmg = import_step(ROOT / "Wristwatch BMG v3.step").solids()
    return {
        "bmg": LOC_BMG * Compound([bmg[i] for i in BMG_SOLIDS]),
        "hotend_mount": LOC_MOUNT * import_step(ROOT / "hotend_mount.STEP"),
        "hotend": build_hotend(),
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


PRINT_ROT = Rot(180, 0, 0)   # every part prints upside down, on its flat top face


def on_bed(shape, rot):
    """shape turned by rot, centred on the origin with its lowest point on z=0."""
    shape = rot * shape
    bb = shape.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * shape


def export(shape, name, rot=PRINT_ROT):
    """STEP in the assembly frame, STL turned to its print orientation (rot=None: already laid out)."""
    export_step(shape, OUT / f"{name}.step")
    stl = shape if rot is None else on_bed(shape, rot)
    export_stl(stl, OUT / f"{name}.stl", tolerance=0.01, angular_tolerance=0.1)


def main(render_png=True):
    OUT.mkdir(parents=True, exist_ok=True)
    part = build_part()
    part.label = "toolhead_adapter"
    export(part, "toolhead_adapter")
    print(f"part: {len(part.solids())} solid(s), volume {part.volume:.0f} mm3, bbox {part.bounding_box().size}")
    duct = build_duct()
    duct.label = "duct"
    export(duct, "2x_duct")
    print(f"duct (print 2): volume {duct.volume:.0f} mm3, bbox {duct.bounding_box().size}")
    if NUTS:
        export(build_fit_test(part), "fit_test", rot=None)
    printed = {"adapter": part, "duct_R": duct, "duct_L": Rot(0, 0, 180) * duct}

    vendor = load_vendor()
    for k, v in list(vendor.items()) + list(printed.items()):
        v.label = k
    asm = Compound(list(printed.values()) + list(vendor.values()))
    export_step(asm, OUT / f"toolhead_assembly.step")

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
    print(f"BMG screws M3x{BMG_SCREW_L:.0f}: tip {BMG_SCREW_DEPTH:.1f} below the top face"
          + (f", nut {BMG_NUT_ROOF:.1f}..{BMG_NUT_ROOF + 2.4:.1f}" if NUTS else f", insert 0..{INSERT_L:.1f}"))
    head = Y_FRONT_OUT + M3_HEAD_RECESS
    print(f"mount screws M3x30: tip {head + 30 - Y_BACK_OUT:+.2f} past the back face"
          + (f" (needs > {2.4 - NUT_T:+.1f} to pass through the nut)" if NUTS else ""))

    if render_png:
        sys.path.insert(0, str(Path(__file__).parent))
        from render import render
        ducts = Compound([printed["duct_R"], printed["duct_L"]])
        render(OUT / "render_part.png", [part, ducts], "adapter(blue) + 2 ducts(orange)")
        render(OUT / "render_2x_duct.png", [duct], "duct (print 2)")
        if NUTS:
            render(OUT / "render_fit_test.png", [build_fit_test(part)], "fit test: fan cradle, blower cradle")
        render(OUT / "render_assembly.png",
               [part, vendor["hotend_mount"], vendor["fan_3010"], Compound([vendor["blower_R"], vendor["blower_L"]]),
                vendor["bmg"], ducts, vendor["hotend"]],
               "assembly: adapter(blue) mount(orange) fan(red) blowers(green) BMG(purple) ducts(teal) hotend(brown)")
    return part, duct, vendor


if __name__ == "__main__":
    main()
