"""Print bounding boxes and cylindrical features (holes/bosses) of STEP files."""
import sys
from collections import Counter
from build123d import import_step, GeomType

for path in sys.argv[1:]:
    shape = import_step(path)
    bb = shape.bounding_box()
    print(f"\n=== {path}")
    print(f"solids={len(shape.solids())}  bbox min={tuple(round(v,2) for v in bb.min)} max={tuple(round(v,2) for v in bb.max)} size={tuple(round(v,2) for v in bb.size)}")
    cyl = Counter()
    for f in shape.faces():
        if f.geom_type == GeomType.CYLINDER:
            s = f.geom_adaptor().Cylinder()
            loc, d = s.Location(), s.Axis().Direction()
            ax = tuple(round(v, 2) for v in (d.X(), d.Y(), d.Z()))
            fb = f.bounding_box()
            key = (round(s.Radius()*2, 2), ax, round(loc.X(),2), round(loc.Y(),2), round(loc.Z(),2) if abs(ax[2])<0.9 else None,
                   round(fb.min.Z,2), round(fb.max.Z,2)) if abs(ax[2])>0.9 else \
                  (round(s.Radius()*2, 2), ax, round(loc.X(),2) if abs(ax[0])<0.9 else None, round(loc.Y(),2) if abs(ax[1])<0.9 else None, round(loc.Z(),2) if abs(ax[2])<0.9 else None)
            cyl[key] += 1
    for k, n in sorted(cyl.items(), key=lambda kv: -kv[0][0]):
        print("  dia", k[0], "axis", k[1], "pos/extent", k[2:], "x", n)
