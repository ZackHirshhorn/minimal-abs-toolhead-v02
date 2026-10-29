# Assembly

![assembly](output/inserts/render_assembly.png)

Directions used below: **front** is the 3010 fan side, **back** is the BMG motor side, **left/right** are the blower sides.

## Bill of materials

### Printed parts

| Qty | Part | File | Material | Orientation |
|---|---|---|---|---|
| 1 | Adapter | `output/inserts/toolhead_adapter.stl` | ABS/ASA | Upside down, top plate on the bed. Supports are built in: turn slicer supports off |
| 2 | Duct (both sides use the same part) | `output/inserts/2x_duct.stl` | ABS/ASA, or something more heat-resistant | Flange down, flat top face of the flange on the bed |
| 1 | Toolboard mount (optional, for an EBB36) | `output/inserts/toolboard_mount.stl` | ABS/ASA | Front face (the flat side without bosses) on the bed. No supports |

The STL files are already turned to these orientations and sit on the bed. Import them as they are.

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
| 6 | M3 heat-set insert, Ø5 × 4 mm long (for a Ø4.0 hole) | 2 top plate, 4 front plate |
| 2 | M3 hex nut (5.5 mm across flats, 2.4 mm thick) | Carriage mount flange, for the hotend-mount screws |
| 2 | M3×8 socket head screw | BMG to the top plate |
| 2 | M3×35 socket head screw | Hotend mount module to the frame, into the nuts in the carriage mount flange. The tip ends about 1.2 mm past the nut, inside the flange |
| 4 | M2×5 socket head screw | Adapter to the MGN7H carriage. 5 mm, no longer, or they hit the rail |
| 2 | M3×35 and M3×30 socket head screw, 1 each (toolboard) | Replace the 2 motor screws, so their tips stick out of the motor's back for the standoffs |
| 2 | M3×10 female-female standoff, 5 mm across flats (toolboard) | On the motor screw tips, behind the motor |
| 2 | M3×8 socket head screw (toolboard) | Toolboard mount to the standoffs |
| 2 | M3 heat-set insert, Ø5 × 4 mm (toolboard) | Toolboard mount's bosses |
| 2 | M3×6 socket head screw (toolboard) | EBB36 to the mount, into the inserts |
| 4 | M3×12 screw | 3010 fan to the front plate. Don't go longer than 14 mm, or the screws hit the hotend mount |
| 4 | M2.5 self-tapping screw | Blowers to the arms, 2 each. Length = blower ear thickness + up to 3 mm (M2.5×12 for full-height 10 mm ears). Any longer and the tip hits the hotend mount |
| 4 | M2.5×8 self-tapping screw | Ducts to the shelves, 2 each |
| 4 | M2.5×6 hotend screws | Heatsink to the mount module. Use the ones from the hotend kit, as on the Mini Stealthburner |

If your inserts aren't Ø5 × 4 mm, change `INSERT_D` / `INSERT_L` in `cad/toolhead_adapter.py` and rebuild before printing.

### Tools

Soldering iron with a heat-set insert tip, 2.5 mm and 1.5 mm hex keys, Phillips screwdriver for the self-tapping screws, PTFE tube cutter or a sharp blade.

## Steps

### 1. Prepare the printed parts

1. Remove the built-in supports: the combs under each shelf and duct lug, and the ribs in the fan opening. Break them off at their tabs with pliers. Then clean the tab marks off the faces they stood on.
2. Test-fit the hotend mount module in the gap between the front plate and the back tab. It should slide in by hand without force (0.1 mm clearance per side). Sand or scrape the inner faces if it binds.
3. Clear the blower and duct pilot holes with a 2.2 mm drill if they came out undersized.

### 2. Install the heat-set inserts (6×)

Press each insert in square to the face until it sits flush. Let it cool before moving on.

1. **Top plate, 2×:** from the top face, in the two holes either side of the filament hole.
2. **Front plate, 4×:** from the front face, at the corners of the Ø28 fan opening.

### 3. Attach the hotend to the mount module

1. Leave out the kit's top part. The heatsink's top face seats directly on the underside of the mount's plate.
2. Fix the heatsink with its 4 screws.
3. Rotate the hotend so the heater's 10 mm side (the one with the ears) runs left–right, toward the blowers. The ducts are sized for this. Turning it 90° also works and adds 0.9 mm of duct clearance.
4. Fit the silicone sock.
5. Route the heater and thermistor wires out to the side. The carriage mount's flange covers the back of the mount module.

### 4. Fit the mount module into the frame

1. Drop an M3 nut into each of the two slots in the top face of the carriage mount, just behind the back tab. They fall to the bottom of the slot, in line with the screw holes.
2. With the ducts still off, slide the mount module up into the frame from below, between the front plate and the back tab, plate side up, until it stops against the underside of the top plate.
3. Push 2× M3×35 screws in from the front, through the counterbored holes, the mount's horizontal holes and the back tab, into the nuts.
4. Tighten them evenly. Stop once they're snug, or the screws will bow the back tab.

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
4. Check that neither duct touches the heater block or the sock. There should be about 5 mm of air gap to the bare block, and the lowest point of each duct should sit about 4.5 mm above the nozzle tip.

### 9. Mount the BMG

If the toolhead goes on a Voron 0.2, bolt it to the carriage first (see [MGN7H carriage](#mgn7h-carriage-voron-02)). The motor covers those screws.

1. Set the BMG on the top plate with its motor toward the back, over the carriage mount.
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

## MGN7H carriage (Voron 0.2)

The carriage mount is part of the adapter. Its plate sits on top of the MGN7H carriage, under the BMG motor, and its flange is fused to the back tab. The two hotend-mount screws end in nuts in that flange.

1. Before mounting the BMG, bolt the adapter to the carriage with 4× M2×5 socket head screws, down through the counterbored holes in the plate. Use 5 mm, no longer, or the screws hit the rail.
2. Then mount the BMG. Its motor sits over the M2 screws and the nut slots.

To take the toolhead off the carriage, take the BMG off first (2 screws), then remove the 4 M2 screws.

## EBB36 toolboard (optional)

The mount holds a BTT EBB36 CAN on the back of the BMG motor, on two M3 female-female standoffs threaded onto the motor screws. The motor screws sit on a diagonal, so the mount turns the board level and centres it on the motor. That keeps its bottom edge about 4 mm above the adapter's top face and clear of the carriage mount under the motor.

1. Take out the BMG's 2 motor screws, one at a time so the motor stays put. Put in longer ones the same way, heads in the BMG: M3×35 in the upper hole, M3×30 in the lower one. Their tips should stick out about 4.3 mm past the motor's back face. If yours stick out more than 5 mm, use a shorter screw, or the mount screw won't have room in the standoff.
2. Thread an M3×10 female-female standoff onto each tip until it seats on the motor.
3. Press an M3 heat-set insert into the top of each of the mount's two bosses.
4. Fix the mount to the standoffs with 2× M3×8 through the counterbored holes, heads on the board side.
5. Screw the EBB36 to the two bosses. It goes either way round, so turn its connectors where your wiring needs them.

## Replacing a duct

Remove its 2 screws, fit the new duct, and screw it back in. Nothing else has to come off.
