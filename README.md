# Minimal ABS Toolhead v02

A single printed adapter that hangs a TZ-V6 2.0 hotend under a **Wristwatch BMG** extruder, with a 3010 heatsink fan and two 3010 part-cooling blowers. No casing or shrouding, only structure and two short ducts.

![assembly](output/render_assembly.png)

## What's in the part

- **Top plate:** the BMG bolts on with 2× M3×8 screws, going down through its flange into M3 heat-set inserts at ±18.5 mm. The PTFE tube passes straight through on the filament axis.
- **Hotend mount module:** slides up between a front plate and a back tab. It's held by 2× M3×30 screws through its horizontal holes into inserts in the back tab.
- **3010 fan:** mounts on the front plate over the Ø28 opening with 4× M3 inserts. Fit it so it blows into the heatsink.
- **2× 3010 blowers:** one on each side, held by M2.5 self-tapping screws through their diagonal ears. The outlets feed short ducts aimed at the nozzle tip.

Print it upside down (top plate on the bed), in ABS/ASA.

## Files

| Path | Contents |
|---|---|
| `output/toolhead_adapter.stl` / `.step` | The printable adapter |
| `output/render_*.png` | Renders of the part and of the full assembly |
| `cad/toolhead_adapter.py` | Parametric build123d model; every dimension is a named constant at the top |
| `cad/render.py`, `cad/inspect_step.py`, `cad/list_step_*.py` | Helpers to render and inspect STEP files |

## Rebuilding

The model places third-party parts to check fit, and those parts aren't redistributed here. Before running the script, put these files in the repo root:

- `Wristwatch BMG v3.step`: the Wristwatch BMG assembly
- `hotend_mount.STEP`: the TZ-V6 2.0 mount module
- `3010 fan.step`: a 30×30×10 axial fan
- `3010 blower.STEP`: a 30×30×10 radial blower

Then:

```
pip install -r cad/requirements.txt
python cad/toolhead_adapter.py
```

This rebuilds `output/`, including `toolhead_assembly.step`, and prints interference checks between every pair of parts.

## Check before printing

- `NOZZLE_BELOW_MOUNT_TOP` (61 mm) is an estimate. Measure your hotend and set it, because the duct height depends on it.
- `DUCT_EXIT_R` sets how close the duct tips come to the heater block.
- `INSERT_D` must match your heat-set inserts (default Ø4.0).

## License

GPL-3.0. See [LICENSE](LICENSE). This covers the adapter design and the code in this repo, not the third-party models listed above.
