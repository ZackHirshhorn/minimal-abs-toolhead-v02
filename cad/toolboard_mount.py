"""BTT EBB36 CAN toolboard mount, on 2 standoffs on the back of the BMG motor (as usual on the Voron 0.2).

Parametric build123d model, same world frame as toolhead_adapter.py:
    origin = filament axis on the BMG's bottom face, +Z up, -Y front (fan side), +Y back (BMG motor side)
Run:
    python cad/toolboard_mount.py [--nuts]    # builds the mount + fit checks + renders
Outputs go to ../output/inserts/ or ../output/nuts/ (with --nuts).

Layout: the 2 screws that hold the LDO-36STH20 motor to the BMG are swapped for longer ones (M3x30 and M3x35,
heads in the BMG as before) whose tips stick out of the motor's back face. An M3 female-female standoff threads
onto each tip, and the mount's plate screws onto the standoffs' other ends. The motor screws sit on a diagonal
(about 28 deg off level), so a board bolted straight onto them would be tilted and its lower corner would hit
the carriage mount's plate under the motor. The plate turns it level instead: the board's 2 holes (43.85 apart,
on its long axis) sit on bosses on a horizontal line, centred on the motor axis.
Print it front face (the motor side) down. No supports needed.
"""
from pathlib import Path
import math
import sys
from build123d import Axis, Compound, Pos, RegularPolygon, Rot, extrude

sys.path.insert(0, str(Path(__file__).parent))
import toolhead_adapter as ta
from toolhead_adapter import box, cyl_y, interference, nut_pocket, prism_z

OUT = ta.OUT
NUTS = ta.NUTS

# ---------------------------------------------------------------- parameters
# Motor screws, measured on "Wristwatch BMG v3.step" (world X, Z; both run along Y), heads inside the BMG
MOTOR_SCREWS = [(-9.25, 32.53), (29.41, 11.92)]
MOTOR_SCREW_HEAD_Y = [3.4, 8.3]   # underside of each screw's head
MOTOR_FACE_Y = ta.MOTOR_Y         # motor's front face, on the BMG's motor plate
MOTOR_L = 20.0                    # LDO-36STH20: 36 mm round, 20 mm body
MOTOR_D = 36.0
MOTOR_SCREW_L = [35.0, 30.0]      # replacement motor screws, so their tips stick out of the motor's back face

STANDOFF_L = 10.0                 # M3 F-F standoff, 5 mm across flats
STANDOFF_AF = 5.0

# BTT EBB36 CAN (V1.1/V1.2): 51.5 x 37 board, 2x M3 on its long axis, 43.85 apart
EBB_SIZE = (51.5, 37.0)
EBB_HOLE = 43.85
EBB_T = 1.6
EBB_ROT = 0.0                     # board's long axis from level, deg
EBB_CORNER_R = 4.0                # board outline corners (stand-in only)

PLATE_T = 6.0
PLATE_PAD_R = 5.0                 # plate outline: hull of a circle this size round each of the 4 holes
HEAD_D, HEAD_H = 6.0, 3.2         # M3 SHCS into the standoffs, counterbored into the back face
WINDOW_D = 18.0                   # air window in the middle, between the motor's back and the board's underside
BOSS_D, BOSS_H = 7.5, 5.0         # under the board's holes: room for the parts on its underside
BOARD_SCREW_L = 6.0 if not NUTS else 16.0   # M3 into an insert in the boss, or through it into a nut on the front face

# ------------------------------------------------------------- derived values
MOTOR_C = tuple((a + b) / 2 for a, b in zip(*MOTOR_SCREWS))    # motor axis (X, Z)
MOTOR_BACK_Y = MOTOR_FACE_Y + MOTOR_L
Y0 = MOTOR_BACK_Y + STANDOFF_L    # plate front face
Y1 = Y0 + PLATE_T                 # plate back face
BOARD_Y = Y1 + BOSS_H             # board's underside
EBB_HOLES = [(MOTOR_C[0] + s * EBB_HOLE / 2 * math.cos(math.radians(EBB_ROT)),
              MOTOR_C[1] + s * EBB_HOLE / 2 * math.sin(math.radians(EBB_ROT))) for s in (-1, 1)]


def prism_y(pts, y0, y1):
    """Prism over an XZ polygon, from y0 to y1."""
    return Rot(90, 0, 0) * prism_z(pts, -y1, -y0)   # Rot(90, 0, 0): (x, y, z) -> (x, -z, y)


def hull(pts):
    """Convex hull (Andrew's monotone chain) of 2D points, counter-clockwise."""
    pts = sorted(set(pts))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(pts[::-1])


def pads(centres, r, n=48):
    return [(x + r * math.cos(2 * math.pi * i / n), z + r * math.sin(2 * math.pi * i / n)) for x, z in centres for i in range(n)]


def build_mount():
    part = prism_y(hull(pads(MOTOR_SCREWS + EBB_HOLES, PLATE_PAD_R)), Y0, Y1)
    for x, z in EBB_HOLES:
        part = part + cyl_y(BOSS_D, x, z, Y1 - 0.01, BOARD_Y)

    cuts = [cyl_y(WINDOW_D, *MOTOR_C, Y0 - 1, Y1 + 1)]
    for x, z in MOTOR_SCREWS:   # M3 through the plate into the standoffs, heads below the back face
        cuts += [cyl_y(ta.M3_CLEAR, x, z, Y0 - 1, Y1 + 1), cyl_y(HEAD_D, x, z, Y1 - HEAD_H, Y1 + 1)]
    for x, z in EBB_HOLES:
        if NUTS:                # board screws through the boss and plate, into a nut dropped into the front face
            cuts += [cyl_y(ta.M3_CLEAR, x, z, Y0 - 1, BOARD_Y + 1), nut_pocket("y", x, z, Y0 - 1, Y0 + ta.NUT_T, "z")]
        else:                   # heat-set insert pressed into the boss top
            cuts.append(cyl_y(ta.INSERT_D, x, z, BOARD_Y - ta.INSERT_L - 1, BOARD_Y + 1))
    for c in cuts:
        part = part - c
    return part.solids()[0] if len(part.solids()) == 1 else part


def build_reference():
    """Motor, standoffs and the EBB36 (a plain board, no parts on it), for fit checks and renders."""
    motor = cyl_y(MOTOR_D, *MOTOR_C, MOTOR_FACE_Y, MOTOR_BACK_Y)
    standoffs = Compound([Pos(x, (MOTOR_BACK_Y + Y0) / 2, z) * Rot(90, 0, 0)
                          * extrude(RegularPolygon(STANDOFF_AF / math.sqrt(3), 6), STANDOFF_L / 2, both=True)
                          for x, z in MOTOR_SCREWS])
    w, h = EBB_SIZE
    board = box(-w / 2, w / 2, BOARD_Y, BOARD_Y + EBB_T, -h / 2, h / 2)
    board = board.fillet(EBB_CORNER_R, board.edges().filter_by(Axis.Y))
    for s in (-1, 1):
        board = board - cyl_y(3.2, s * EBB_HOLE / 2, 0, BOARD_Y - 1, BOARD_Y + EBB_T + 1)
    board = Pos(MOTOR_C[0], 0, MOTOR_C[1]) * Rot(0, -EBB_ROT, 0) * board
    return {"motor": motor, "standoffs": standoffs, "ebb36": board}


def main(render_png=True):
    OUT.mkdir(parents=True, exist_ok=True)
    mount = build_mount()
    mount.label = "toolboard_mount"
    ta.export(mount, "toolboard_mount", rot=Rot(90, 0, 0))   # front face (motor side) on the bed
    print(f"toolboard mount: {len(mount.solids())} solid(s), volume {mount.volume:.0f} mm3, bbox {mount.bounding_box().size}")
    print(f"motor axis (X, Z) = ({MOTOR_C[0]:.2f}, {MOTOR_C[1]:.2f}), motor screws {math.dist(*MOTOR_SCREWS):.2f} apart, "
          f"{math.degrees(math.atan2(MOTOR_SCREWS[0][1] - MOTOR_SCREWS[1][1], MOTOR_SCREWS[1][0] - MOTOR_SCREWS[0][0])):.1f} deg off level")
    for (x, z), hy, l in zip(MOTOR_SCREWS, MOTOR_SCREW_HEAD_Y, MOTOR_SCREW_L):
        print(f"motor screw at ({x:.2f}, {z:.2f}): M3x{l:.0f}, tip {hy + l - MOTOR_BACK_Y:.1f} past the motor's back face "
              f"(into the M3x{STANDOFF_L:.0f} standoff, leaving {STANDOFF_L - (hy + l - MOTOR_BACK_Y):.1f} for the mount screw)")
    print(f"mount screws M3x8: {8 - (PLATE_T - HEAD_H):.1f} into the standoffs")
    if NUTS:
        print(f"board screws M3x{BOARD_SCREW_L:.0f}: tip {BOARD_SCREW_L - EBB_T - BOSS_H - PLATE_T:.1f} past the plate's front face "
              f"(the motor is {STANDOFF_L:.0f} away), nut in the front face")
    else:
        print(f"board screws M3x{BOARD_SCREW_L:.0f}: {BOARD_SCREW_L - EBB_T:.1f} into the boss (insert {ta.INSERT_L:.0f} deep)")
    print(f"plate y {Y0:.1f}..{Y1:.1f}, board y {BOARD_Y:.1f}..{BOARD_Y + EBB_T:.1f}; "
          f"board z {MOTOR_C[1] - EBB_SIZE[1] / 2:.1f}..{MOTOR_C[1] + EBB_SIZE[1] / 2:.1f}, "
          f"mount z {mount.bounding_box().min.Z:.1f}..{mount.bounding_box().max.Z:.1f} (adapter top face z=0)")

    import carriage_mount as cm
    adapter, vendor, ref, car = ta.build_part(), ta.load_vendor(), build_reference(), cm.build_reference()
    print("interference volumes (mm3):")
    others = {"adapter": adapter, "bmg": vendor["bmg"], "mgn7h_carriage": car["mgn7h_carriage"], "x_extrusion": car["x_extrusion"]}
    for k, v in [("toolboard_mount", mount)] + list(ref.items()):
        for n, o in others.items():
            print(f"  {k} x {n}: {interference(v, o)}")
    print(f"  toolboard_mount x motor: {interference(mount, ref['motor'])}")
    print(f"gap mount to adapter: {mount.distance_to(adapter):.2f}, board to adapter: {ref['ebb36'].distance_to(adapter):.2f}, "
          f"board to BMG: {ref['ebb36'].distance_to(vendor['bmg']):.2f} mm")

    if render_png:
        from render import render
        render(OUT / "render_toolboard_mount.png", [mount], "toolboard mount (EBB36 CAN)")
        render(OUT / "render_assembly_toolboard.png",
               [adapter, mount, Compound([ref["motor"], ref["standoffs"]]), vendor["bmg"], ref["ebb36"],
                Compound([car["mgn7h_carriage"], car["mgn7_rail"]])],
               "adapter(blue) toolboard mount(orange) motor+standoffs(red) BMG(green) EBB36(purple) MGN7H(teal)")
    return mount


if __name__ == "__main__":
    main()
