"""Voron 0.2 X carriage on its MGN7H carriage, behind the toolhead adapter, for fit checks.

Same world frame as toolhead_adapter.py:
    origin = filament axis on the BMG's bottom face, +Z up, -Y front (fan side), +Y back (BMG motor side)
Run:
    python cad/carriage_mount.py [--nuts]     # checks the adapter on the carriage + renders
Renders go to ../output/inserts/ or ../output/nuts/ (with --nuts).

Layout: the MGN7H rail lies on top of the X extrusion (running along X), so the carriage faces up, toward the
BMG motor. The adapter hangs on the Voron 0.2 X carriage as the Mini Stealthburner does: the X carriage stays on the
MGN7H carriage with the belts clamped in it, the hotend mount's back face sits against its front face (so the nozzle
is where the Mini Stealthburner puts it), and the two hotend-mount screws (M3x30) run from the adapter's front plate
through the mount into M3 nuts in slots in it. Both versions use the X carriage's
no-heat-set or heat-set variant (third_party/X_Carriage_x1_nuts.stl / _inserts.stl): they only differ away from the
toolhead, so they share every number below. The X carriage is only placed, never modified:
toolhead_adapter.build_part() takes clearance() (the X carriage and, beside it, its belts) out of the adapter.
The BMG sits ta.BMG_RAISE higher than a 6 mm top plate would put it, to clear the boss on the X carriage's top. The
Ø22 heatsink (a stand-in, from the drawing) reaches 0.15 past the hotend mount's back face, so it touches the X
carriage's front face. It would on the Mini Stealthburner too, whose X carriage has the same face in the same place.
"""
from pathlib import Path
import sys
import numpy as np
import trimesh
from build123d import Compound, Location, Plane

sys.path.insert(0, str(Path(__file__).parent))
import toolhead_adapter as ta
from toolhead_adapter import box, interference

OUT = ta.OUT
NUTS = ta.NUTS

# ---------------------------------------------------------------- parameters
# HIWIN MGN7H (mm): rail 7 wide x 4.8 high, rail bottom to carriage top 8, carriage 17 wide x 30.8 long
RAIL_W, RAIL_H, MGN_H = 7.0, 4.8, 8.0
CAR_W, CAR_L = 17.0, 30.8
EXTRUSION = 15.0             # 1515 X extrusion under the rail (reference only)
MOUNT_SCREW_L = 30.0         # the 2 hotend-mount screws, front plate -> nuts in the X carriage

# Voron 0.2 X carriage, measured on X_Carriage_x1_*.stl in its own coords: +X down, Y along the rail, +Z back
XC_FILE = ta.VENDOR / f"X_Carriage_x1_{'nuts' if NUTS else 'inserts'}.stl"
XC_FRONT_Z = 29.326          # front face, against the hotend mount's back face
XC_SCREW_X = 150.537         # hotend-mount screw holes (3.4, through the 8 mm front plate)...
XC_MID_Y = 243.41            # ...at +-12.5 about this
XC_NUT = (2.8, 5.4)          # their nut slots, behind the front face (open on the top)
XC_HOLE_DEPTH = 8.0
XC_MGN_X = 149.287           # face on the MGN7H carriage
XC_MGN_Z = 45.826            # centre of its 4 M2 holes
XC_LOW_X = 173.187           # bottom
XC_HALF_W = 17.0             # along the rail
XC_GAP = 0.5                 # adapter to the X carriage's sides and bottom (clearance())
XC_FACE_GAP = 0.1            # adapter to its front face, so only the hotend mount bears on it
# Belts: 2 per side, 6 mm wide, clamped on combs on the back of its lower plate, leaving its ends along the rail
XC_BELTS_X = [(155.09, 161.49), (164.09, 170.49)]   # their slots (belt width runs along its X)
XC_BELT_Z = 32.426           # comb base: belt teeth side
BELT_T = 1.4                 # GT2, teeth included

# ------------------------------------------------------------- derived values
Y0 = ta.XC_FRONT_Y                                   # X carriage front face, on the hotend mount's back face
SCREW_TIP = ta.Y_FRONT_OUT + ta.M3_HEAD_RECESS + MOUNT_SCREW_L   # hotend-mount screw tip, in the X carriage
# placed with its screw holes on the hotend mount's and its front face on the mount's back face
LOC_XC = Location(Plane(origin=(XC_MID_Y, Y0 - XC_FRONT_Z, ta.SCREW_Z + XC_SCREW_X), x_dir=(0, 0, -1), z_dir=(0, 1, 0)))
CAR_TOP = ta.SCREW_Z + XC_SCREW_X - XC_MGN_X        # MGN7H carriage top, under the X carriage
CAR_Y = Y0 + XC_MGN_Z - XC_FRONT_Z                   # rail centre line
XC_LO = ta.SCREW_Z + XC_SCREW_X - XC_LOW_X
BELT_Y = Y0 + XC_BELT_Z - XC_FRONT_Z                 # belts' front (teeth side)
BELTS_Z = [tuple(ta.SCREW_Z + XC_SCREW_X - x for x in xs[::-1]) for xs in XC_BELTS_X]
RAIL_LO = CAR_TOP - MGN_H
assert abs(BELT_Y - Y0 - ta.BELT_DY) < 0.01, "toolhead_adapter.BELT_DY doesn't match the X carriage"


def clearance():
    """The room the X carriage takes, grown by XC_GAP (XC_FACE_GAP at its front face), and beside it, over its
    height, everything behind ta.Y_SIDE_BACK: ta.BELT_GAP in front of the belts. The shelves and duct lugs, below
    the X carriage, may run further back."""
    w, z0 = XC_HALF_W + XC_GAP, XC_LO - XC_GAP
    return box(-w, w, Y0 - XC_FACE_GAP, Y0 + 40, z0, 10) + box(-60, 60, ta.Y_SIDE_BACK, Y0 + 40, z0, 10)


def load_x_carriage():
    """The X carriage as a mesh (trimesh), placed."""
    mesh = trimesh.load(XC_FILE)
    m = LOC_XC.wrapped.Transformation()
    mesh.apply_transform([[m.Value(i, j) for j in range(1, 5)] for i in range(1, 4)] + [[0, 0, 0, 1]])
    return mesh


COLUMN = 0.25                # mesh_columns() cell size


def mesh_columns(mesh, lo, hi, step=COLUMN):
    """The mesh as boxes over the XY box lo..hi: per step x step cell, one box per stretch of material on a vertical
    ray through its centre (for solids that won't make a closed mesh: they're checked against these as BRep)."""
    t = mesh.triangles
    a, e1, e2 = t[:, 0], t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
    den = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
    keep = np.abs(den) > 1e-12                       # vertical triangles: a vertical ray never crosses them
    a, e1, e2, den = a[keep], e1[keep], e2[keep], den[keep]
    out = []
    for x in np.arange(lo[0] + step / 2, hi[0], step):
        for y in np.arange(lo[1] + step / 2, hi[1], step):
            px, py = x - a[:, 0], y - a[:, 1]
            u, w = (px * e2[:, 1] - py * e2[:, 0]) / den, (e1[:, 0] * py - e1[:, 1] * px) / den
            hit = (u >= 0) & (w >= 0) & (u + w <= 1)
            z = np.unique(np.round(a[hit, 2] + u[hit] * e1[hit, 2] + w[hit] * e2[hit, 2], 4))   # shared edges: once
            out += [box(x - step / 2, x + step / 2, y - step / 2, y + step / 2, z0, z1) for z0, z1 in zip(z[::2], z[1::2])]
    return out


def mesh_interference(mesh, shape):
    """Overlap volume of a mesh and a shape, solid by solid, and its bbox (the shape tessellated, manifold3d boolean).
    A solid that won't make a closed mesh is intersected as BRep with mesh_columns() instead (to about COLUMN)."""
    vol, boxes, approx = 0.0, [], 0
    lo, hi = mesh.bounds
    for s in shape.solids():
        bb = s.bounding_box()
        if any(tuple(bb.min)[i] > hi[i] or lo[i] > tuple(bb.max)[i] for i in range(3)):
            continue
        try:
            v, t = s.tessellate(0.02, 0.2)
            sm = trimesh.Trimesh([tuple(p) for p in v], t)
        except AttributeError:   # a vendor STEP face that won't tessellate
            sm = None
        if sm is None or not sm.is_volume:
            approx += 1
            for c in mesh_columns(mesh, np.maximum(lo, tuple(bb.min)), np.minimum(hi, tuple(bb.max))):
                r = s & c
                rv = sum(q.volume for q in r.solids()) if r is not None else 0
                if rv > 1e-4:
                    vol += rv
                    rb = r.bounding_box()
                    boxes.append((tuple(rb.min), tuple(rb.max)))
            continue
        r = trimesh.boolean.intersection([mesh, sm], engine="manifold")
        if r.volume > 1e-3:
            vol += r.volume
            boxes.append(r.bounds)
    msg = f"{vol:.2f}"
    if boxes:
        b = np.array(boxes)
        msg += f"  in {tuple(np.round(b[:, 0].min(0), 2).tolist())}..{tuple(np.round(b[:, 1].max(0), 2).tolist())}"
    if approx:
        msg += f"  ({approx} solids not watertight: checked as BRep against {COLUMN} mm columns of the mesh)"
    return msg


def build_reference():
    """MGN7H carriage, a stretch of rail and 1515 extrusion, and the belts beside the X carriage, as plain boxes for
    fit checks and renders."""
    carriage = box(-CAR_L / 2, CAR_L / 2, CAR_Y - CAR_W / 2, CAR_Y + CAR_W / 2, RAIL_LO + 1.5, CAR_TOP)
    rail = box(-60, 60, CAR_Y - RAIL_W / 2, CAR_Y + RAIL_W / 2, RAIL_LO, RAIL_LO + RAIL_H)
    extrusion = box(-60, 60, CAR_Y - EXTRUSION / 2, CAR_Y + EXTRUSION / 2, RAIL_LO - EXTRUSION, RAIL_LO)
    belts = Compound([box(*sorted((sx * XC_HALF_W, sx * 60)), BELT_Y, BELT_Y + BELT_T, *z) for sx in (-1, 1) for z in BELTS_Z])
    return {"mgn7h_carriage": carriage - rail, "mgn7_rail": rail, "x_extrusion": extrusion, "belts": belts}


def main(render_png=True):
    OUT.mkdir(parents=True, exist_ok=True)
    adapter, ducts = ta.build_part(), Compound([ta.build_duct(1), ta.build_duct(-1)])
    print(f"adapter: {len(adapter.solids())} solid(s), bbox {adapter.bounding_box().size}")
    print(f"mount screws M3x{MOUNT_SCREW_L:.0f}: tip {SCREW_TIP - Y0:.2f} behind the X carriage's front face "
          f"(nut {XC_NUT[0]:.1f}..{XC_NUT[1]:.1f}, hole {XC_HOLE_DEPTH:.1f} deep)")
    print(f"nozzle {Y0:.2f} in front of the X carriage's front face (Mini Stealthburner: 10.85)")
    print(f"rail centre Y={CAR_Y:.2f} (filament axis Y=0), carriage top z={CAR_TOP:.2f}, rail bottom z={RAIL_LO:.2f}, "
          f"nozzle z={ta.NOZZLE_Z:.2f}  ->  nozzle {CAR_Y:.2f} in front of the rail, {CAR_TOP - ta.NOZZLE_Z:.2f} below the carriage top")
    print(f"X carriage front face Y={Y0:.2f}; belts beside it at Y {BELT_Y:.2f}..{BELT_Y + BELT_T:.2f}, "
          f"z {BELTS_Z[0][1]:.2f}..{BELTS_Z[0][0]:.2f} and {BELTS_Z[1][1]:.2f}..{BELTS_Z[1][0]:.2f}")

    ref = build_reference()
    vendor = ta.load_vendor()
    others = [("adapter", adapter), ("ducts", ducts)] + list(vendor.items())
    print("interference volumes (mm3):")
    for k in ref:
        for n, v in others:
            print(f"  {k} x {n}: {interference(ref[k], v)}")
    print("  belts: gap to the adapter "
          f"{ref['belts'].distance_to(adapter):.2f}, to the blowers {ref['belts'].distance_to(Compound([vendor['blower_R'], vendor['blower_L']])):.2f} mm")
    xc = load_x_carriage()
    print(f"X carriage ({XC_FILE.name}): watertight {xc.is_watertight}, bounds {np.round(xc.bounds, 2).tolist()}")
    # the hotend mount's back face and the MGN7H's top and front side touch it: shift them 0.01 away from it so that
    # contact isn't counted
    away = {"hotend_mount": ta.Pos(0, -0.01, 0), "mgn7h_carriage": ta.Pos(0, 0.01, -0.01)}
    for n, v in others + list(ref.items()):
        print(f"  x_carriage x {n}: {mesh_interference(xc, away[n] * v if n in away else v)}")
    top, gb = xc.bounds[1][2], -xc.bounds[1][2] - 0.05
    print(f"  BMG raised {ta.BMG_RAISE:.1f}: its bottom face (z=0) clears the X carriage's top (z={top:.2f}) by {-top:.2f} mm; "
          f"x_carriage x bmg, moved {gb:.2f} down: {mesh_interference(xc, ta.Pos(0, 0, -gb) * vendor['bmg']).split()[0]}")
    g, gf = XC_GAP - 0.05, XC_FACE_GAP - 0.05
    grown = [ta.Pos(*d) * adapter for d in [(g, 0, 0), (-g, 0, 0), (0, 0, g), (0, gf, 0)]]
    print(f"  x_carriage x adapter, moved {g:.2f} toward it (+X, -X, +Z) and {gf:.2f} back (+Y): "
          + ", ".join(mesh_interference(xc, s).split()[0] for s in grown))

    if render_png:
        from render import render
        render(OUT / "render_assembly_carriage.png",
               [adapter, vendor["fan_3010"], Compound([vendor["blower_R"], vendor["blower_L"]]),
                vendor["bmg"], Compound([ref["mgn7h_carriage"], ref["mgn7_rail"], ref["belts"]]), vendor["hotend"], xc],
               "adapter(blue) fan(orange) blowers(red) BMG(green) MGN7H+belts(purple) hotend(teal) X carriage(brown)")
    return adapter


if __name__ == "__main__":
    main()
