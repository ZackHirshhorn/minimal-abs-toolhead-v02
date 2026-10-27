# Assembly

![assembly](output/render_assembly.png)

Directions used below: **front** is the 3010 fan side, **back** is the BMG motor side, **left/right** are the blower sides.

## Bill of materials

### Printed parts

| Qty | Part | File | Material | Orientation |
|---|---|---|---|---|
| 1 | Adapter | `output/toolhead_adapter.stl` | ABS/ASA | Upside down, top plate on the bed |
| 2 | Duct (both sides use the same part) | `output/duct.stl` | ABS/ASA, or something more heat-resistant | Flange down, flat top face of the flange on the bed |

### Purchased parts

| Qty | Part | Notes |
|---|---|---|
| 1 | Wristwatch BMG extruder | Complete, with its motor and hardware, built to its own instructions |
| 1 | TZ-V6 2.0 hotend | The kit's top part is not used |
| 1 | TZ-V6 2.0 hotend mount module | The one the Mini Stealthburner uses (`hotend_mount.STEP`) |
| 1 | Silicone sock for the heater block | Required: the ducts sit about 5 mm from the block |
| 1 | 3010 axial fan (30×30×10) | Heatsink fan |
| 2 | 3010 radial blower (30×30×10) | Part cooling |
| 1 | PTFE tube, 4 mm OD | Runs from the BMG down into the heatsink. Cut to length during assembly |

### Hardware

| Qty | Part | Where it goes |
|---|---|---|
| 8 | M3 heat-set insert, Ø5 × 4 mm long (for a Ø4.0 hole) | 2 top plate, 2 back tab, 4 front plate |
| 2 | M3×8 socket head screw | BMG to the top plate |
| 2 | M3×30 socket head screw | Hotend mount module to the frame. M3×28 also works and ends flush with the back tab. M3×30 sticks out about 1.6 mm behind it |
| 4 | M3×12 screw | 3010 fan to the front plate. Don't go longer than 14 mm, or the screws hit the hotend mount |
| 4 | M2.5 self-tapping screw | Blowers to the arms, 2 each. Length = blower ear thickness + up to 3 mm (M2.5×12 for full-height 10 mm ears). Any longer and the tip hits the hotend mount |
| 4 | M2.5×8 self-tapping screw | Ducts to the shelves, 2 each |
| 4 | Hotend screws | Heatsink to the mount module. Use the ones from the hotend kit, as on the Mini Stealthburner |

If your inserts aren't Ø5 × 4 mm, change `INSERT_D` / `INSERT_L` in `cad/toolhead_adapter.py` and rebuild before printing.

### Tools

Soldering iron with a heat-set insert tip, 2.5 mm hex key, Phillips screwdriver for the self-tapping screws, PTFE tube cutter or a sharp blade.

## Steps

### 1. Prepare the printed parts

1. Remove any supports, mostly from under the shelves and arms.
2. Test-fit the hotend mount module in the gap between the front plate and the back tab. It should slide in by hand without force (0.1 mm clearance per side). Sand or scrape the inner faces if it binds.
3. Clear the blower and duct pilot holes with a 2.2 mm drill if they came out undersized.

### 2. Install the heat-set inserts (8×)

Press each insert in square to the face until it sits flush. Let it cool before moving on.

1. **Top plate, 2×:** from the top face, in the two holes either side of the filament hole.
2. **Back tab, 2×:** from the back face, in line with the two counterbored holes in the front plate.
3. **Front plate, 4×:** from the front face, at the corners of the Ø28 fan opening.

### 3. Attach the hotend to the mount module

1. Leave out the kit's top part. The heatsink's top face seats directly on the underside of the mount's plate.
2. Fix the heatsink with its 4 screws.
3. Rotate the hotend so the heater block's 14 mm length runs left–right, toward the blowers. The ducts are sized for this. Turning it 90° also works and adds 1.5 mm of duct clearance.
4. Fit the silicone sock.
5. Route the heater and thermistor wires up along the back of the mount.

### 4. Fit the mount module into the frame

1. With the ducts still off, slide the mount module up into the frame from below, between the front plate and the back tab, plate side up, until it stops against the underside of the top plate.
2. Push 2× M3×30 screws in from the front, through the counterbored holes, through the mount's horizontal holes, and into the back tab inserts.
3. Tighten them evenly. Stop once they're snug, or the screws will bow the back tab.

### 5. Fit the PTFE tube

1. Push the PTFE tube down through the filament hole in the top plate until it bottoms out in the heatsink.
2. Cut it so it reaches up into the BMG's tube seat when the BMG sits flat on the top plate. Use the Wristwatch BMG's own guide for how far the tube should reach.
3. Cut the end square and chamfer the inside edge lightly.

### 6. Mount the heatsink fan

1. Put the 3010 fan on the front plate over the Ø28 opening so that it **blows into the heatsink**. On most fans, that means the label and strut side faces the heatsink.
2. Fix it with 4× M3×12 into the front plate inserts.

### 7. Mount the blowers (both sides)

1. Hold the blower against the outer face of the arm with its outlet pointing **down** into the opening in the shelf and its inlet facing outward.
2. Its two diagonal ears line up with the two pilot holes in the arm.
3. Drive 2× M2.5 self-tapping screws through the ears into the arm. Stop when the blower is snug, because the threads are cut in plastic.
4. Repeat on the other side.

### 8. Fit the ducts (both sides)

1. Hold a duct with its flange against the underside of the shelf so the outlet points in toward the nozzle.
2. Fix it with 2× M2.5×8 self-tapping screws up into the shelf.
3. Repeat on the other side with the second duct. It's the same part, turned 180°.
4. Check that neither duct touches the heater block or the sock. There should be about 5 mm of air gap to the bare block, and the lowest point of each duct should sit about 3 mm above the nozzle tip.

### 9. Mount the BMG

1. Set the BMG on the top plate with its motor toward the back, over the stepped-down relief at the back edge.
2. Make sure the PTFE tube enters its tube seat.
3. Fix it with 2× M3×8 screws down through the BMG flange into the top plate inserts.

### 10. Wire up and check

1. Connect the hotend fan, the blowers, the heater and the thermistor. Use the same pins and fan config as on your Mini Stealthburner, and check that the fan voltage matches your board.
2. Tie the wires so none can reach the heater block or sit in front of the blower inlets.
3. Heat to printing temperature and check the following:
   - The heatsink fan blows into the heatsink.
   - Both blowers blow out of the duct tips.
   - Nothing touches the block or the sock.
   - Filament feeds through smoothly.
4. Re-tighten the nozzle hot as usual for the TZ-V6.

## MGN7H carriage mount (Voron 0.2)

`output/carriage_mount.stl`: print 1 in ABS/ASA, upside down (flat top face on the bed).

The mount is an L-bracket. Its plate sits on top of the MGN7H carriage, under the BMG motor, and its flange sits against the adapter's back face. It shares the two hotend-mount screws, which changes step 2 and step 4:

- **Step 2:** skip the 2 back tab inserts. Put those 2 inserts in the flange instead, pressed in from its front face (the face that touches the adapter).
- **Step 4:** use 2× M3×35 instead of M3×30. They go through the front plate, the mount module and the back tab, then into the flange inserts.

To fit it:

1. Bolt the mount to the carriage with 4× M2×5 socket head screws. Use 5 mm, no longer, or the screws hit the rail.
2. Hold the toolhead against the flange and drive the 2× M3×35 in from the front.

To take the toolhead off, remove those 2 screws. The mount stays on the carriage.

The flange covers the back of the mount module, so route the hotend wires out to the side.

## Replacing a duct

Remove its 2 screws, fit the new duct, and screw it back in. Nothing else has to come off.
