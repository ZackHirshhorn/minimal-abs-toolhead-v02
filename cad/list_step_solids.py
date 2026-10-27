"""List every solid of a STEP assembly in world coordinates with its tree path."""
import sys
from build123d import import_step


def walk(node, path=""):
    p = f"{path}/{node.label or '?'}"
    kids = list(getattr(node, "children", ()))
    if kids:
        for ch in kids:
            yield from walk(ch, p)
    else:
        for s in node.solids():
            yield p, s


shape = import_step(sys.argv[1])
for i, (p, s) in enumerate(walk(shape)):
    bb = s.bounding_box()
    print(f"{i:2d} {p:70s} V={s.volume:9.0f} min={tuple(round(v,1) for v in bb.min)} max={tuple(round(v,1) for v in bb.max)}")
