"""Wristwatch BMG -> TZ-V6 2.0 hotend-mount adapter with 3010 fan and 2x 3010 blowers.

Parametric build123d model. Run with a Python env that has build123d:
    python cad/toolhead_adapter.py            # builds part + assembly + checks + renders
    python cad/toolhead_adapter.py --nuts     # captive-nut version
Outputs go to ../output/inserts/ or ../output/nuts/.

Captive-nut version: no heat-set inserts and no self-tapping screws. M3 nuts sit in pockets and slots (BMG,
duct lugs, and the X carriage the hotend mount is clamped to), and the 3010 fan and both blowers snap into cradles
with no screws.

Frame used throughout (mm):
    origin = filament axis on the BMG's bottom face (= the adapter's top face)
    +Z up (BMG above, nozzle below), -Y front (heatsink fan side), +Y back (BMG motor side)
The top plate is BMG_RAISE thicker than it needs to be, so the BMG sits that much higher over the X carriage. The
origin stays on the BMG: everything from the plate's underside down (hotend mount, nozzle, fan, blowers, ducts, and
the X carriage it hangs on) sits BMG_RAISE lower in this frame, unchanged relative to each other.

Vendor models (BMG, hotend mount, hotend, fan, blower) are only placed, never modified.
Printed parts: the adapter, and a left and a right duct that screw to the shelf under each blower so they can be
replaced. The two ducts differ (see side_yc).
The adapter hangs on the Voron 0.2 X carriage like the Mini Stealthburner (carriage_mount.py), with the nozzle
where the Mini Stealthburner puts it: the hotend mount's back face sits on the X carriage's front face.
"""
from pathlib import Path
import math
import sys
from build123d import (
    Axis, Box, Compound, Cone, Cylinder, Location, Plane, Polygon, Pos, Rectangle, RegularPolygon, Rot, Text, Vector,
    export_step, export_stl, extrude, import_step, loft,
)

ROOT = Path(__file__).resolve().parent.parent
NUTS = "--nuts" in sys.argv  # captive-nut version (see the module docstring)
OUT = ROOT / "output" / ("nuts" if NUTS else "inserts")
VENDOR = ROOT / "third_party"   # third-party models, not in git (see README)

# ---------------------------------------------------------------- parameters
# Wristwatch BMG (from "Wristwatch BMG v3.step", body 0 = complete assembly)
BMG_FILAMENT = Vector(-21.96, 103.24, 158.6)  # filament axis on bottom face, in the BMG file's coords
BMG_HOLE_X = {-1: -19.5, 1: 17.5}  # 2x M3 on the filament line, not symmetric about it (37 apart, per the BMG file)
BMG_FLANGE_T = 3.0           # BMG flange the screws pass through
BMG_FOOT_Y = (-14.54, 7.96)  # BMG bottom face Y extent
MOTOR_Y = 13.96              # motor sits behind this Y, 3-4 mm above z=0 (measured), so the top face stays flat
BMG_TUBE_SEAT = 6.2          # PTFE seat in the BMG's bottom face: Ø4.4, this deep (measured)

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
FIT = 0.1                    # clearance where the mount slides in behind the front plate
# The X carriage's top-centre boss stands 5.3 above a 6 mm plate's top face (the Mini Stealthburner keeps its
# extruder 15.7 above the hotend mount, so it never meets it). The plate grows up by BMG_RAISE, as one printed
# part, so the BMG's bottom face clears the boss.
BMG_RAISE = 6.0              # BMG this much higher than on a 6 mm plate: 0.7 mm over the boss
PLATE_T = 6.0 + BMG_RAISE    # top plate thickness (mount top sits at z = -PLATE_T)
PLATE_HALF_X = 23.5
FRONT_T = 4.0                # fan plate (between mount face and 3010 fan)
FAN_PLATE_MARGIN = 2.0       # fan plate runs this far below the 3010 fan's bottom edge
INSERT_D, INSERT_L = 4.0, 4.0  # M3 heat-set inserts (M3x5x4 style); set to your inserts
M3_CLEAR, M3_HEAD_D, M3_HEAD_RECESS = 3.4, 6.0, 2.0
FILAMENT_D = 4.2             # PTFE passes BMG -> adapter -> mount

# Voron 0.2 X carriage (carriage_mount.py places it): the hotend mount is clamped straight between the front plate
# and its front face, as on the Mini Stealthburner. Beside it, its belts run off along X.
BELT_DY = 3.1                # belts' front (teeth side) behind the X carriage's front face (measured, carriage_mount.py)
BELT_GAP = 0.55              # beside the X carriage, the sides (arms, blowers, cradles, top plate) stop this short of
                             # the belts: they reach 2.55 behind its front face, as the Mini Stealthburner's cowling

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
BLOWER_DROP = 20.0           # blower centre below the mount top (blower top 5 mm under the plate, leaving height for the duct)

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
MARK_SIZE, MARK_DEPTH = 5.0, 0.4  # L/R letter in the flange's underside: font size, depth (2 layers)

# Fillets. None inside the box (the mount slides in with FIT), in the blower's seat, or on the top face
# (bed face when printing, and the BMG sits on it).
R_CORNER = 3.0               # outer vertical corners: top plate, shelf/duct flange outer corners
R_SMALL = 1.0                # shelf inner corners, lugs, duct flange-to-tube junction
R_ARM_ROOT = 3.0             # concave, top plate underside to arm outer face (blower top sits 5 mm lower)
R_WINDOW = 2.0               # arm window corners

# Built-in supports, in the adapter's STL only (the STEP and the assembly stay without them): thin walls under
# the overhangs that can't bridge. They stop SUP_GAP_Z short of the face they hold up and SUP_GAP_XY clear of
# the part's sides. Where one stands on the part rather than the bed, only short tabs touch it, so it snaps off.
# None go into a nut pocket or slot (nut_keepouts).
SUP_WALL = 0.8               # wall thickness: 2 lines of a 0.4 mm nozzle
SUP_PITCH = 2.5              # max wall spacing
SUP_GAP_Z = 0.2              # air gap under the face held up (one 0.2 mm layer)
SUP_GAP_XY = 0.5             # ...and to the part's sides
SUP_TAB = (1.0, 3.0, 0.4)    # standing on the part: tab length, tab pitch, notch height between the tabs

# ------------------------------------------------------------- derived values
MOUNT_TOP = -PLATE_T
BLOWER_Z = MOUNT_TOP - BLOWER_DROP
BMG_SCREW_L = 10.0 if NUTS else 8.0
BMG_SCREW_DEPTH = BMG_SCREW_L - BMG_FLANGE_T   # BMG screw tip below the top face
NOZZLE_BELOW_MOUNT_TOP = HM_SEAT_DROP + HE_TIP
NOZZLE_Z = MOUNT_TOP - NOZZLE_BELOW_MOUNT_TOP
BLOCK_HALF_X = HE_BLOCK[0] / 2 if HOTEND_ROT % 180 == 0 else HE_BLOCK[1] / 2
Y_FRONT_IN = HM_FRONT - FIT                  # front plate inner face
Y_FRONT_OUT = Y_FRONT_IN - FRONT_T
XC_FRONT_Y = HM_BACK                          # X carriage front face, on the hotend mount's back face
Y_SIDE_BACK = XC_FRONT_Y + BELT_DY - BELT_GAP  # back face of the top plate and both sides, beside the X carriage
SCREW_Z = MOUNT_TOP - HM_SCREW_DROP
FAN_Z = MOUNT_TOP - HM_FAN_DROP
ARM_X0 = HM_W / 2 + ARM_GAP
BL_X0 = ARM_X0 + ARM_T                        # blower inner face
OUT_LO = BLOWER_Z - 15.0                      # blower outlet face Z (+X blower)
SHELF_LO = OUT_LO - SHELF_T                   # shelf underside = duct flange top
FLANGE_LO = SHELF_LO - DUCT_FLANGE_T
OUT_X = (BL_X0 + BL_OUT_Y[0], BL_X0 + BL_OUT_Y[1])         # blower outlet in world X
SHELF_X = (ARM_X0, BL_X0 + 10.5)
SHELF_HALF_Y = DUCT_SCREW_Y + (3.5 if NUTS else 2.5)
DUCT_SCREW_X = sum(OUT_X) / 2
ARM_HALF_Y = 15.0 + CRADLE_FIT + CRADLE_WALL if NUTS else 15.5  # the blower cradle's walls grow off the arm ends
# blower centre Y (both sides): as far back as the belts allow, with its cradle wall (or the blower itself, the
# heat-set arm's last 0.5 mm being cut at Y_SIDE_BACK) on Y_SIDE_BACK
BLOWER_Y = Y_SIDE_BACK - (ARM_HALF_Y if NUTS else 15.0)
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


def shelf_box(z0, z1, yc):
    """Shelf / duct flange outline under a +X blower centred at Y=yc, corners rounded."""
    b = box(*SHELF_X, yc - SHELF_HALF_Y, yc + SHELF_HALF_Y, z0, z1)
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
# Both blowers sit at Y=BLOWER_Y, outlet down and inlet out. The left one is the right one turned 180 deg about Z,
# but its outlet is off-centre (BL_OUT_Z), so it can't be a mirror image: it is placed as a +X blower centred at
# -BLOWER_Y and then turned, which puts its outlet at another Y than the right one's. Each side of the part (arm,
# shelf, lugs, cradle, duct) is built the same way, for a +X blower centred at yc = side_yc(side), then turned.
def side_yc(side):
    """Centre Y of the +X blower each side is built for, before side_rot(): 1 = right (+X), -1 = left."""
    return side * BLOWER_Y


def side_rot(side):
    return Rot(0, 0, 90 - 90 * side)


def blower_plane(yc):
    return Plane(origin=(BL_X0, yc, BLOWER_Z), x_dir=(0, 0, 1), z_dir=(0, 1, 0))
# blower local (x, y, z) -> world (x0 + y, yc + z, Z + x): outlet (-X local) points down, inlet faces out


def blower_world(lx, ly, lz, yc):
    return Vector(BL_X0 + ly, yc + lz, BLOWER_Z + lx)


def out_y(yc):
    """Blower outlet's Y span (its X span is OUT_X)."""
    return (yc + BL_OUT_Z[0], yc + BL_OUT_Z[1])


LOC_MOUNT = Pos(0, -HM_AXIS_Y, MOUNT_TOP + HM_TOP_Z) * Rot(0, 180, 0)
LOC_FAN = Pos(0, Y_FRONT_OUT - 5.0, FAN_Z) * Rot(-90, 0, 0) * Pos(225.0, 0, -295.02)  # hub side faces heatsink
LOC_BLOWER_R = side_rot(1) * Location(blower_plane(side_yc(1)))
LOC_BLOWER_L = side_rot(-1) * Location(blower_plane(side_yc(-1)))
LOC_BMG = Pos(-BMG_FILAMENT)
BMG_SOLIDS = [0, 2, 3, 6] + list(range(7, 33))  # complete extruder (body 0 + arm + plate "SOLID" + hardware)


# ------------------------------------------------------------------- the part
def blower_side(side):
    """Arm + duct shelf for the right (side=1) or left (side=-1) blower, built for a +X blower centred at
    side_yc(side) and turned into place. Returns the solid and the cuts."""
    yc = side_yc(side)
    holes = [blower_world(x, 0, z, yc) for x, z in BL_HOLES]
    arm = box(ARM_X0, BL_X0, yc - ARM_HALF_Y, yc + ARM_HALF_Y, SHELF_LO, 0)
    window = box(ARM_X0 - 1, BL_X0 + 1, yc - 7.5, yc + 7.5, BLOWER_Z - 9, BLOWER_Z + 9)
    arm = arm - window.fillet(R_WINDOW, window.edges().filter_by(Axis.X))
    shelf = shelf_box(SHELF_LO, OUT_LO, yc)
    lug_top = OUT_LO + LUG_H
    if NUTS:   # lugs follow the shelf's rounded outline, out past the cradle walls
        lugs = [shelf_box(OUT_LO, lug_top, yc) & box(ARM_X0 - 1, 40, *sorted((yc + sy * LUG_Y0, yc + sy * 40)),
                                                     OUT_LO - 1, lug_top + 1) for sy in (1, -1)]
    else:
        lugs = [box(*OUT_X, yc + LUG_Y0, yc + SHELF_HALF_Y, OUT_LO, lug_top),
                box(*OUT_X, yc - SHELF_HALF_Y, yc - LUG_Y0, OUT_LO, lug_top)]
        lugs = [lug.fillet(R_SMALL, lug.edges().filter_by(Axis.Z)) for lug in lugs]
    solid = arm + shelf + lugs[0] + lugs[1]
    cuts = [box(*OUT_X, *out_y(yc), SHELF_LO - 1, OUT_LO + 0.01)]                # air passage
    if NUTS:
        solid = solid + blower_cradle(yc)
        for sy in (-1, 1):   # M3x10 up through the duct flange and shelf, into a nut dropped in on top of the lug
            y = yc + sy * DUCT_SCREW_Y
            cuts += [cyl_z(M3_CLEAR, DUCT_SCREW_X, y, SHELF_LO - 1, lug_top + 1),
                     nut_pocket("z", DUCT_SCREW_X, y, lug_top - NUT_T, lug_top + 1, "x")]
        # notch for the wire, which leaves the blower's local +z side near the outlet end (right: back, left: front)
        cuts.append(box(BL_X0, 40, yc + 14.0, yc + ARM_HALF_Y + 1, BLOWER_Z + BL_WIRE_X[0], BLOWER_Z + BL_WIRE_X[1]))
    else:
        cuts += [cyl_x(BL_PILOT, p.Y, p.Z, ARM_X0 - 1, BL_X0 + 1) for p in holes]
        cuts += [cyl_z(BL_PILOT, DUCT_SCREW_X, yc + sy * DUCT_SCREW_Y, SHELF_LO - 1, lug_top - 1) for sy in (-1, 1)]
    rot = side_rot(side)
    return rot * solid, rot * Compound(cuts)


def blower_cradle(yc):
    """Snap-in cradle for a +X blower centred at Y=yc: a block filling the gap above it up to the top plate (reaching
    the top face, so it prints on the bed), and front/back walls growing off the arm ends. The walls are free of the
    shelf (SNAP_GAP), so they flex as the blower is pushed in; ramped lips at their bottom outer corners then
    hold its outer face. The block above stops it from tipping out about those lips."""
    x1 = BL_X0 + 10.0 + CRADLE_FIT                       # blower outer face, plus fit
    x2 = x1 + SNAP_LIP[1]
    top = box(BL_X0, x2, yc - ARM_HALF_Y, yc + ARM_HALF_Y, BLOWER_Z + 15.0 + CRADLE_FIT, 0)
    y_in = 15.0 + CRADLE_FIT
    cradle = top
    for sy in (-1, 1):
        cradle = cradle + box(BL_X0 - 0.01, x2, *sorted((yc + sy * y_in, yc + sy * ARM_HALF_Y)), OUT_LO + SNAP_GAP, 0)
        lip = [(x1, yc + sy * y_in), (x1, yc + sy * (y_in - SNAP_LIP[0])), (x2, yc + sy * y_in)]
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


def duct_mark(side):
    """The duct's letter, to cut into its flange's underside (the top face in print): between the tube and the head of
    the back screw (before side_rot()), outside the air path, reading from below with its top toward the blower."""
    yc = side_yc(side)
    y0, y1 = out_y(yc)[1] + DUCT_WALL + R_SMALL, yc + DUCT_SCREW_Y - M3_HEAD_D / 2
    pl = Plane(origin=(sum(SHELF_X) / 2, (y0 + y1) / 2, FLANGE_LO), x_dir=(0, 1, 0), z_dir=(0, 0, -1))
    return extrude(pl * Text("R" if side > 0 else "L", font_size=MARK_SIZE), -MARK_DEPTH)


def build_duct(side):
    """Replaceable duct for the right (side=1) or left (side=-1) blower, from its outlet to the exit in front of
    the nozzle. The two differ (the blower outlets sit at different Y, see side_yc), and each only fits its own side."""
    yc = side_yc(side)
    oy = out_y(yc)
    exit_c, d = duct_exit()
    in_c = Vector(sum(OUT_X) / 2, sum(oy) / 2, FLANGE_LO)
    in_w, in_h = oy[1] - oy[0], OUT_X[1] - OUT_X[0]
    ex_w, ex_h = DUCT_EXIT
    in_pl = Plane(origin=in_c, x_dir=(0, 1, 0), z_dir=(0, 0, -1))
    ex_pl = Plane(origin=exit_c, x_dir=(0, 1, 0), z_dir=d)
    w2 = 2 * DUCT_WALL
    outer = loft([in_pl * Rectangle(in_w + w2, in_h + w2), ex_pl * Rectangle(ex_w + w2, ex_h + w2)])
    inner = loft([in_pl.offset(-0.5) * Rectangle(in_w, in_h), ex_pl.offset(0.5) * Rectangle(ex_w, ex_h)])
    flange = shelf_box(FLANGE_LO, SHELF_LO, yc)
    duct = flange + outer
    # tube outline on the flange; its outer side runs 0.3 mm from the flange edge, too close to fillet
    in_x = (in_c.X - (in_h + w2) / 2 - 0.01, min(in_c.X + (in_h + w2) / 2 + 0.01, SHELF_X[1] - R_SMALL))
    duct = fillet_where(duct, R_SMALL, None, lambda c: near(c.Z, FLANGE_LO) and in_x[0] < c.X < in_x[1]
                        and abs(c.Y - in_c.Y) < (in_w + w2) / 2 + 0.01)
    duct = duct - inner - box(*OUT_X, *oy, FLANGE_LO - 0.01, SHELF_LO + 1) - duct_mark(side)
    for sy in (-1, 1):
        duct = duct - cyl_z(DUCT_SCREW_CLEAR, DUCT_SCREW_X, yc + sy * DUCT_SCREW_Y, FLANGE_LO - 1, SHELF_LO + 1)
    duct = side_rot(side) * duct
    return duct.solids()[0] if len(duct.solids()) == 1 else duct


def build_part(carriage=True):
    """The adapter, cut clear of the X carriage and its belts (carriage=False leaves that out, for the fit test).
    There is no back plate: the hotend mount is clamped between the front plate and the X carriage, and the top
    plate is cut back over the X carriage (carriage_mount.clearance) but runs on beside it, out to Y_SIDE_BACK."""
    top = box(-PLATE_HALF_X, PLATE_HALF_X, Y_FRONT_OUT, Y_SIDE_BACK, -PLATE_T, 0)
    top = top.fillet(R_CORNER, top.edges().filter_by(Axis.Z))
    # the front plate runs out to the blower arms' outer faces
    front = box(-BL_X0, BL_X0, Y_FRONT_OUT, Y_FRONT_IN, FAN_Z - 15.0 - FAN_PLATE_MARGIN, 0)
    (side_r, cuts_r), (side_l, cuts_l) = blower_side(1), blower_side(-1)
    # concave fillet under the top plate's overhang at each arm, as a solid trimmed to the plate's outline
    # (an edge fillet fails there: the plate's front/back faces sit a fraction of a mm off the arm's)
    r, h = R_ARM_ROOT, max(-Y_FRONT_OUT, Y_SIDE_BACK) + 1
    root = box(BL_X0, BL_X0 + r, -h, h, -PLATE_T - r, -PLATE_T) - cyl_y(2 * r, BL_X0 + r, -PLATE_T - r, -h - 1, h + 1)
    roots = [(rr & Pos(0, 0, -PLATE_T) * top) for rr in (root, Rot(0, 0, 180) * root)]
    part = top + front + side_r + side_l + roots[0] + roots[1]
    if NUTS:
        part = part + fan_cradle()

    cuts = [
        cyl_z(FILAMENT_D, 0, 0, -PLATE_T - 1, 1),
        cyl_y(FAN_BORE, 0, FAN_Z, Y_FRONT_OUT - 1, Y_FRONT_IN + 1),
        cuts_r, cuts_l,
    ]
    for sx in (-1, 1):
        x = sx * HM_SCREW_X
        cuts += [
            # mount screws: through the front plate and the mount, into nuts in the X carriage behind it
            cyl_y(M3_CLEAR, x, SCREW_Z, Y_FRONT_OUT - 1, Y_FRONT_IN + 1),
            cyl_y(M3_HEAD_D, x, SCREW_Z, Y_FRONT_OUT - 1, Y_FRONT_OUT + M3_HEAD_RECESS),
        ]
        if NUTS:
            # BMG screws: M3x10 down into a nut slid in from the side edge, under BMG_NUT_ROOF of plate
            bx, nz = BMG_HOLE_X[sx], -BMG_NUT_ROOF
            cuts += [cyl_z(M3_CLEAR, bx, 0, -BMG_SCREW_DEPTH - 1, 1),
                     nut_pocket("z", bx, 0, nz - NUT_T, nz, "x"),
                     box(*sorted((bx, sx * 40)), -NUT_AF / 2, NUT_AF / 2, nz - NUT_T, nz)]
        else:
            # BMG screws: insert from the top, in a blind hole 1 mm past the screw tip (the plate stays solid below it)
            cuts.append(cyl_z(INSERT_D, BMG_HOLE_X[sx], 0, -BMG_SCREW_DEPTH - 1, 1))
            for sz in (-1, 1):                                                  # fan inserts
                cuts.append(cyl_y(INSERT_D, sx * FAN_HOLE, FAN_Z + sz * FAN_HOLE, Y_FRONT_OUT - 1, Y_FRONT_IN + 0.01))
    for c in cuts:
        part = part - c
    if carriage:
        import carriage_mount   # imports this module, so only at call time
        part = part - carriage_mount.clearance()
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


def union(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out + s
    return out


def spaced(lo, hi):
    """Wall centres from lo to hi (walls flush with both ends), at most SUP_PITCH apart."""
    lo, hi = lo + SUP_WALL / 2, hi - SUP_WALL / 2
    n = max(1, math.ceil((hi - lo) / SUP_PITCH))
    return [lo + (hi - lo) * i / n for i in range(n + 1)]


def nut_keepouts():
    """Every captive-nut pocket and slot in the adapter, grown by SUP_GAP_XY and run out through the side it's
    loaded from (the duct lugs' out to the bed), so no support ends up in one."""
    g, r = SUP_GAP_XY, NUT_AF / math.sqrt(3) + SUP_GAP_XY   # r: nut corner radius, grown
    outs = []
    for sx in (-1, 1) if NUTS else ():
        bx, nz = BMG_HOLE_X[sx], -BMG_NUT_ROOF                 # BMG: slots open on the side faces
        outs.append(box(*sorted((bx - sx * r, sx * 40)), -NUT_AF / 2 - g, NUT_AF / 2 + g, nz - NUT_T - g, nz + g))
        lug_top = OUT_LO + LUG_H                               # duct lugs: pockets open on the lug tops
        # both sides' lugs sit at BLOWER_Y +- DUCT_SCREW_Y (side_yc, turned)
        outs += [cyl_z(2 * r, sx * DUCT_SCREW_X, BLOWER_Y + sy * DUCT_SCREW_Y, lug_top - NUT_T - g, 1) for sy in (-1, 1)]
    return outs


def build_supports(part):
    """Built-in supports for part (the adapter, with or without its carriage clearance), in the assembly frame.
    Each support is a column under an overhang, cut down to a comb of walls; the part, grown by the gaps, is then
    taken out of it, leaving each comb between the face it holds up and whatever is under it in print: the bed,
    or the part, which only its tabs touch."""
    cols, tabs = [], []
    t_len, t_pitch, t_h = SUP_TAB

    def comb(region, ys=(), xs=()):
        """region cut to walls along X (at each y in ys) and along Y (at each x in xs), plus their tabs."""
        bb = region.bounding_box()
        z0, z1 = bb.min.Z - 1, bb.max.Z + 1
        x0, x1, y0, y1 = bb.min.X - 1, bb.max.X + 1, bb.min.Y - 1, bb.max.Y + 1
        walls = ([box(x0, x1, y - SUP_WALL / 2, y + SUP_WALL / 2, z0, z1) for y in ys]
                 + [box(x - SUP_WALL / 2, x + SUP_WALL / 2, y0, y1, z0, z1) for x in xs])
        cols.append(region & union(walls))
        w = SUP_WALL / 2 + 0.1
        tabs.extend(box(x - t_len / 2, x + t_len / 2, y - w, y + w, z0, z1)
                    for y in ys for x in [bb.min.X + t_len / 2 + i * t_pitch for i in range(int(bb.size.X / t_pitch) + 1)])
        tabs.extend(box(x - w, x + w, y - t_len / 2, y + t_len / 2, z0, z1)
                    for x in xs for y in [bb.min.Y + t_len / 2 + i * t_pitch for i in range(int(bb.size.Y / t_pitch) + 1)])

    import carriage_mount as cm   # imports this module, so only at call time
    for s in (1, -1):   # right side, and the left: each built for its +X blower at side_yc, then turned
        yc, rot = side_yc(s), side_rot(s)
        # shelf over the blower bay, and the lug tops, minus the air passage (and the ledge beside it, on the arm),
        # the heat-set version's blind duct screw holes, and the arm's notch for the X carriage: its ceiling is a
        # ledge held on two sides that needs none, and a comb in there would be a free-standing sliver
        region = shelf_box(OUT_LO, 0, yc) - box(ARM_X0 - 1, OUT_X[1], *out_y(yc), OUT_LO - 1, 1)
        if not NUTS:
            for sy in (-1, 1):
                region = region - cyl_z(BL_PILOT + 2 * SUP_GAP_XY, DUCT_SCREW_X, yc + sy * DUCT_SCREW_Y, OUT_LO - 1, 1)
        notch = box(*sorted((s * (ARM_X0 - 1), s * (cm.XC_HALF_W + cm.XC_GAP))), cm.Y0 - cm.XC_FACE_GAP - 1, Y_SIDE_BACK,
                    cm.XC_LO - cm.XC_GAP - 1, 1)
        comb(rot * region - notch, ys=[s * y for y in spaced(yc - SHELF_HALF_Y, yc + SHELF_HALF_Y)],
             xs=[s * (OUT_X[1] + SHELF_X[1]) / 2])
        if NUTS:   # the cradle wall left under the blower's wire notch
            x2 = BL_X0 + 10.0 + CRADLE_FIT + SNAP_LIP[1]
            region = box(BL_X0, x2, yc + 15.0 + CRADLE_FIT, yc + ARM_HALF_Y, *(BLOWER_Z + z for z in BL_WIRE_X))
            comb(rot * region, ys=[s * (yc + 15.0 + CRADLE_FIT + CRADLE_WALL / 2)])
    if NUTS:       # tops of the fan cradle's side walls
        x_in = 15.0 + CRADLE_FIT
        for sx in (-1, 1):
            region = box(*sorted((sx * (x_in - SNAP_LIP[0]), sx * (x_in + CRADLE_WALL))),
                         FAN_FACE_Y - SNAP_LIP[1], Y_FRONT_OUT, FAN_Z, 0)
            comb(region, xs=[sx * (x_in + CRADLE_WALL / 2)])
    # fan bore: the part of its top (in print) steeper than 45 deg
    r45 = FAN_BORE / 2 * math.sqrt(0.5)
    region = cyl_y(FAN_BORE, 0, FAN_Z, Y_FRONT_OUT, Y_FRONT_IN) & box(-r45, r45, Y_FRONT_OUT, Y_FRONT_IN, FAN_Z - 20, FAN_Z + 20)
    comb(region, xs=spaced(-r45, r45))

    sup = union(cols)
    for d in [(0, 0, 0), (0, 0, SUP_GAP_Z), (SUP_GAP_XY, 0, 0), (-SUP_GAP_XY, 0, 0), (0, SUP_GAP_XY, 0), (0, -SUP_GAP_XY, 0)]:
        sup = sup - Pos(*d) * part
    # standing on the part: notch the bottom (in print) of each wall between its tabs
    sup = sup - ((sup & (Pos(0, 0, -t_h) * part)) - union(tabs))
    if nut_keepouts():
        sup = sup - union(nut_keepouts())
    keep = [s for s in sup.solids() if s.bounding_box().size.Z > 1.0 and s.volume > 0.5]   # drop slivers in gaps
    return Compound(keep)


def build_fit_test(part):
    """Two small pieces cut from the adapter to check the snap fits before printing it all, laid out for printing:
    the fan cradle on a 2 mm slice of the front plate (plate face down), and the right blower's cradle with its
    shelf, lugs and the BMG nut slot (top face down, as in the adapter, with its built-in supports)."""
    fan = part & box(-19, 19, FAN_FACE_Y - 5, Y_FRONT_OUT + 2.0, FAN_Z - 18, FAN_Z + 18)
    cut = box(ARM_X0, 40, BLOWER_Y - SHELF_HALF_Y - 1, BLOWER_Y + SHELF_HALF_Y + 1, SHELF_LO - 1, 1)
    blower = Compound([part & cut] + [s for s in (build_supports(part) & cut).solids() if s.volume > 0.5])
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
    bmg = import_step(VENDOR / "Wristwatch BMG v3.step").solids()
    return {
        "bmg": LOC_BMG * Compound([bmg[i] for i in BMG_SOLIDS]),
        "hotend_mount": LOC_MOUNT * import_step(VENDOR / "hotend_mount.STEP"),
        "hotend": build_hotend(),
        "fan_3010": LOC_FAN * import_step(VENDOR / "3010 fan.step"),
        "blower_R": LOC_BLOWER_R * import_step(VENDOR / "3010 blower.STEP"),
        "blower_L": LOC_BLOWER_L * import_step(VENDOR / "3010 blower.STEP"),
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


def export(shape, name, rot=PRINT_ROT, supports=None):
    """STEP in the assembly frame, STL turned to its print orientation (rot=None: already laid out).
    supports go in the STL only."""
    export_step(shape, OUT / f"{name}.step")
    stl = shape if supports is None else Compound([shape, supports])
    stl = stl if rot is None else on_bed(stl, rot)
    export_stl(stl, OUT / f"{name}.stl", tolerance=0.01, angular_tolerance=0.1)


def main(render_png=True):
    OUT.mkdir(parents=True, exist_ok=True)
    part = build_part()
    part.label = "toolhead_adapter"
    supports = build_supports(part)
    export(part, "toolhead_adapter", supports=supports)
    print(f"part: {len(part.solids())} solid(s), volume {part.volume:.0f} mm3, bbox {part.bounding_box().size}")
    print(f"built-in supports: {len(supports.solids())} solid(s), volume {supports.volume:.0f} mm3; "
          f"overlap with the part {interference(part, supports)}, with the nut pockets and slots "
          f"{interference(supports, Compound(nut_keepouts()))}")
    ducts = {"duct_R": build_duct(1), "duct_L": build_duct(-1)}
    for k, d in ducts.items():
        d.label = k
        export(d, k)
        print(f"{k}: volume {d.volume:.0f} mm3, bbox {d.bounding_box().size}")
    print(f"blowers at Y={BLOWER_Y:.2f}, outlets Y {out_y(side_yc(1))[0]:.2f}..{out_y(side_yc(1))[1]:.2f} (R), "
          f"{-out_y(side_yc(-1))[1]:.2f}..{-out_y(side_yc(-1))[0]:.2f} (L); sides end at Y={Y_SIDE_BACK:.2f} beside the "
          f"X carriage ({Y_SIDE_BACK - XC_FRONT_Y:.2f} behind its front face)")
    if NUTS:
        fit_test = build_fit_test(build_part(carriage=False))
        export(fit_test, "fit_test", rot=None)
    printed = {"adapter": part, **ducts}

    vendor = load_vendor()
    for k, v in list(vendor.items()) + list(printed.items()):
        v.label = k
    asm = Compound(list(printed.values()) + list(vendor.values()))
    export_step(asm, OUT / f"toolhead_assembly.step")

    print("interference volumes (mm3):")
    names = list(vendor)
    # the BMG sits on the top face and the fan on the front plate: shift them 0.01 away so that contact isn't counted
    away = {"bmg": Pos(0, 0, 0.01), "fan_3010": Pos(0, -0.01, 0)}
    for p in printed:
        for k in names:
            print(f"  {p} x {k}: {interference(printed[p], away[k] * vendor[k] if k in away else vendor[k])}")
    for p in ducts:
        print(f"  adapter x {p}: {interference(part, printed[p])}")
    print(f"  duct_R x duct_L: {interference(ducts['duct_R'], ducts['duct_L'])}")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            print(f"  {a} x {b}: {interference(vendor[a], vendor[b])}")
    block = vendor["hotend"].solids()[-1]
    print(f"nozzle tip at z={NOZZLE_Z:.1f}, adapter lowest z={part.bounding_box().min.Z:.1f}, "
          f"duct lowest z: R {ducts['duct_R'].bounding_box().min.Z:.1f}, L {ducts['duct_L'].bounding_box().min.Z:.1f}")
    print(f"duct exit r={duct_exit()[0].X:.1f}; gap duct to heater block: R {printed['duct_R'].distance_to(block):.2f}, "
          f"L {printed['duct_L'].distance_to(block):.2f} mm")
    print(f"BMG screws M3x{BMG_SCREW_L:.0f}: tip {BMG_SCREW_DEPTH:.1f} below the top face"
          + (f", nut {BMG_NUT_ROOF:.1f}..{BMG_NUT_ROOF + 2.4:.1f}" if NUTS else f", insert 0..{INSERT_L:.1f}"))

    print(f"BMG raised {BMG_RAISE:.1f}: top plate {PLATE_T:.1f} thick, BMG's bottom face {PLATE_T:.1f} above the mount top")
    print(f"PTFE: {HM_SEAT_DROP + PLATE_T + BMG_TUBE_SEAT:.1f} above the heatsink's top face ({BMG_TUBE_SEAT:.1f} above the "
          f"adapter's top face, into the BMG's seat), plus what goes down into the heatsink")

    if render_png:
        sys.path.insert(0, str(Path(__file__).parent))
        from render import render
        both = Compound(list(ducts.values()))
        render(OUT / "render_part.png", [part, both], "adapter(blue) + ducts(orange)")
        render(OUT / "render_ducts.png", list(ducts.values()), "duct_R(blue), duct_L(orange), in place")
        render(OUT / "render_print.png", [PRINT_ROT * part, PRINT_ROT * supports],
               "adapter(blue) as printed, with its built-in supports(orange)")
        if NUTS:
            render(OUT / "render_fit_test.png", [fit_test], "fit test: fan cradle, blower cradle")
        render(OUT / "render_assembly.png",
               [part, vendor["hotend_mount"], vendor["fan_3010"], Compound([vendor["blower_R"], vendor["blower_L"]]),
                vendor["bmg"], both, vendor["hotend"]],
               "assembly: adapter(blue) mount(orange) fan(red) blowers(green) BMG(purple) ducts(teal) hotend(brown)")
    return part, ducts, vendor


if __name__ == "__main__":
    main()
