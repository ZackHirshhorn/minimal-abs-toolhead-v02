"""List the assembly tree of a STEP file: names, solid counts, bounding boxes."""
import sys
from build123d import import_step


def walk(node, depth=0):
    bb = node.bounding_box()
    ns = len(node.solids())
    print(f"{'  '*depth}- {node.label or '<unnamed>'}  solids={ns}  min={tuple(round(v,1) for v in bb.min)} size={tuple(round(v,1) for v in bb.size)}")
    for ch in getattr(node, "children", ()):
        walk(ch, depth + 1)


shape = import_step(sys.argv[1])
walk(shape)
