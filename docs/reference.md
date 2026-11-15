# ithalat reference

This is the detailed reference for ithalat. The [README](../README.md) has the
overview, the connector choice and the quick start; [wiring.md](../wiring.md)
has the wiring, and [bom.md](bom.md) the parts and costs. File names in
`code`, such as `stl/ithalat-glass.stl`, are relative to the repository root.

Contents:

- [Design rationale](#design-rationale)
- [Outputs](#outputs)
- [Verification](#verification)
- [Variants](#variants)
- [The docks](#the-docks) and the [USB-C dock and grip](#usb-c-dock-and-grip)
- [Configuration reference](#configuration-reference)
- [Printing](#printing)
- [Assembly order](#assembly-order)
- [Ballast and bumpers](#ballast-and-bumpers)
- [Glass handling](#glass-handling)
- [Troubleshooting](#troubleshooting)

## Design rationale

**Shape.** The rest is modelled on a classic walnut keyboard rest:

- **Bar.** A long bar, 270.98 x 85 mm (as wide as the keyboard). The ends bulge out gently by 2 mm. The front corners are R16 and the back corners R2.8, matching the keyboard's corners.
- **Top surface.** The surface is crowned and C1-smooth, with no creases anywhere (adjacent facets turn by at most about 5°):
  - It is 11.8 mm high at the back, level with the switchplate.
  - It stays flat to the crown peak 28 mm in.
  - It then falls convexly to 6.5 mm at the front.
  - It ends in a soft elliptic front nose (9 x 4.5 mm), so there is no edge under your wrists.
- **Edge rounds.** The ends are rounded R5 and the back top edge R1.2. Next to the small back corners the end round fades in over 24 mm (`REST_END_TAPER`), so the corners stay crease-free.
- **Trackpad island.** The area around the trackpad is exactly flat at 11.8 mm for 5 mm, then blends into the crown over 14 mm.
- **Highest point.** The trackpad island is the highest point, exactly `REST_HEIGHT`.

**Why these choices:**

- **Trackpad level with the switchplate.** `REST_HEIGHT` defaults to `KEYBOARD_HEIGHT` (11.8 mm, caliper-measured). Your thumbs slide from the front row onto the pad without a step, and the rest's back edge meets the keyboard at the same height, so nothing catches.
- **Lower at the front.** The 6.5 mm front edge and the nose keep the wrists in a neutral, slightly lowered position, as on wooden rests. A rest that is flat at keyboard height pushes the wrists up.
- **Pad on the centre line, close to the keys.** The module is centred on the keyboard's centre line (X 135.49) with its back edge 9 mm from the rest's back. It is within thumb reach of the home row and away from the wrists.
- **Top-loaded stepped pocket.** The module drops in from the top onto a flat ledge. Its surface sits 0.15 mm below the rim, so the glass edges never take a knock. Two push-out holes from below remove it without touching the components. No glue, no screws: the TPS65 has no mounting holes.
- **Separate, pluggable rest.** The rest is not fixed to the keyboard, so it can be moved or stored. With the magnetic pogo connector it also breaks away if the cable snags. The USB-C connector does not break away, so you unplug it first. The cable leaves at the top of the back face, so it is never pinched between the rest and the keyboard.
- **Dock in place of two keys, no case modification.** The two centre front-row keys (`MS_BTN1`/`MS_BTN2` in the current keymap) sit right in front of the OLED/Pico block. A printed dock that clips into their switch cut-outs needs no drilling, filing or PCB change, and it can be removed again. Its wires come from the OLED header, the switchplate TB1 socket or the Pico pins, lying flat on the switchplate under the OLED cover. Only the cover comes off.
- **Shared I2C bus.** QMK supports one I2C peripheral. The TPS65 (0x74) shares the OLED's bus (0x3C) on GP2/GP3. It is a 3.3 V part, so it is powered from 3V3(OUT), never 5 V.
- **Ballast.** A printed rest of about 130 g slides around. Two steel bars (about 122 g) in the wrist wings fix that. They stay at least 20 mm from the pad, because metal near a capacitive sensor disturbs it.

## Outputs

| Output | What |
|---|---|
| `stl/ithalat-glass.stl` | rest for the TPS65 **with** the 1.1 mm glass overlay, for both connectors (about 5.2 MB) |
| `stl/ithalat-bare.stl` | rest for the **bare** TPS65, no glass, for both connectors (about 5.2 MB) |
| `stl/ithalat-dock-pogo.stl` | keyboard dock for the magnetic pogo connector, already in print orientation (about 0.1 MB) |
| `stl/ithalat-dock-usbc.stl` | keyboard dock for the USB-C female board, in print orientation (about 0.1 MB) |
| `stl/ithalat-usbc-grip-top.stl`, `stl/ithalat-usbc-grip-bottom.stl` | the two clamshell halves of the USB-C grip around the male board, in print orientation |
| `stl/ithalat-usbc-retainer.stl` | USB-C board retainer, in print orientation: screwed down with 2 x M2x4, it holds the female board down in the dock, presses the receptacle shell onto the board, closes the shoulder window, covers the Schottky diode, and its two prongs lock the dock's back clips (there is no separate lock part) |
| `stl/ithalat-dock-jst.stl` | JST-SH (Qwiic) dock, only written when `jst_sh4` is selected |
| `preview/index.html` | interactive 3D preview: glass/bare variants, the two connectors, filament colours, explode, section cut, x-ray, underside view, dimensions, parts with masses, pinout, print notes. One file; it loads three.js and the fonts from a CDN, so it needs a network connection. |
| `build/manifest.json` | dimensions, part placement matrices, cable path, stats (consumed by the preview) |
| `build/artifact.html` | the same preview as an HTML fragment for publishing (scratch, git-ignored) |

The STLs and `preview/index.html` are committed and always match the default
config. `build/` is scratch.

The rest STLs are exported in the assembly frame, which is also their print
orientation (bottom on the bed). The frame:

- origin at the rest's front-left-bottom corner;
- +X to the right;
- +Y toward the keyboard;
- +Z up.

The docks and the USB-C parts are exported in their print orientations (the
docks upside down). For every part the manifest gives a 4x4 matrix (three.js
`Matrix4.elements` order) that places it in the assembly, and the connector it
belongs to (`connector`: `pogo`, `usbc` or none for the rests).

## Verification

`make verify` (`tools/verify.py`) measures the meshes themselves, using ray
casts, slices, point-in-solid tests and signed distances. The default build
passes 365 checks with 5
advisory warnings (the pogo plug magnets and the USB-C metal distances, below). It exits 1 on any failure.
It checks:

- **Mesh:** watertight and winding-consistent, positive volume, STL ≤ 12 MB.
- **Size:** bounding box = width/depth/height within ±0.05 mm, max Z == `REST_HEIGHT`, top-surface smoothness (max facet angle).
- **Pocket:**
  - opening size, position and corner radius (`POCKET_CORNER_R`), and that the module and the glass, with their own corner radii, fit the opening;
  - rim height at the pocket wall ≥ glass/film top + 0.05 mm, so a sideways knock meets the wall;
  - ledge Z at six points around the module;
  - pocket depth per variant, and glass/PCB top = rim − `TP_SURFACE_RECESS`;
  - the relief covers the component box + 1 mm;
  - solder well under all 6 pads and the ZIF;
  - push holes open;
  - floor ≥ 2.0 mm under every pocket and channel.
- **Cable:** open path well → tunnel → riser → notch; a `CABLE_D` cable swept along groove, tunnel and riser clears the walls; tunnel skin ≥ 1.6 mm and height ≥ cable Ø; riser → notch passage at least the channel width; notch floor and width on the back face; back face closed below the notch.
- **Plug:** plug bay floor, width and length; the docked plug's housing and its strain-relief envelope (`PLUG_RELIEF_*`) clear the rest by ≥ `PLUG_MIN_CLEARANCE` (0.5 mm), and with `PLUG_EXIT='down'` the loose wires drop into the riser.
- **Underside:** bumper recess depths; ballast depth, top skin ≥ 3 mm, wall ≥ 3 mm at the bed, plan distance ≥ 20 mm from the pad, and bar = `BALLAST_SIZE`; engraving depth.
- **Docks** (one per connector): watertight; each plug < the 14 mm switch cut-out inside the plate thickness; plugs on the removed switch centres and `DOCK_PLUG_DEPTH` deep; body covers both cut-outs, keeps the front setback and ≥ 0.5 mm to the neighbouring key cells; connector face flush and the pocket open; the STL matches the build.
- **USB-C parts:** the dock's well (width, height, depth, 45° entry chamfer, bottom-wall sag allowance), shoulder wall, window clearance and its crush ribs on the receptacle, receptacle mouth flush with the well floor (±`USBC_MOUTH_TOL`), board pocket, rim and rear stop, 30° catches on the back-wall blades, finger-brace flats either side of the well; the retainer presses the board rim and (with its ribs) the receptacle shell, closes the window, its screws' pilot holes and thread length, its hold-down margin against the upward share of the pull, and its lock prongs slide in behind the back blades, are backed at the lip by the backing rib and keep ≥ 0.15 mm of lip engagement; the grip's nose walls, nose clearance in the well (and the tilt before the nose bears on the wall), nose stopping short of the floor, push rib, side and rear walls, wire band over the rib and at the slot, screw thread length, peg walls, the board clamp (crush-rib height, ceiling, and the interference left after rounding both faces to `USBC_PRINT_LAYER`), the shell collar and the epoxy key groove; no printed material inside any hardware box (both boards, both shells, the diode); the grip clear of the dock and the retainer, floating above the rest (mated and withdrawn `USBC_WITHDRAW`), its rear clear of the trackpad pocket and its wire exit above the riser; wire slack ≥ the plug's travel out of the well; dock retention margins (pull with and without the retainer, push); widest bridge and steepest overhang of each USB-C part in print orientation; the taller dock below the keycap tops (`KEYCAP_TOP_Z`) and clear of the OLED cover.
- **Assembly** (`build/manifest.json`): manifest built with the same config; all parts and STLs present; keyboard origin; dock matrix = placement × inverse print transform; placed dock behind the keyboard front edge and clear of the OLED cover; connector face; per variant, the cable starts at the TPS65 pads, leaves through the notch, its sleeve starts at the groove's end, it ends at the dock connector face (USB-C: at the male pads in the grip), and the route (plus the USB-C slack) fits the pigtail length.
- **Advisories (WARN, never fail):**
  - a ballast bar was shortened below `BALLAST_SIZE` (only when an override makes it not fit);
  - the docked pogo plug's two magnets are closer to the pad than `TP_METAL_KEEPOUT` (15 mm). This always warns when the pogo connector is built: they sit about 7.35 mm from the module outline. It is accepted because they do not move while the pad is powered and the controller calibrates at power-up; check for drift at the first power-up ([wiring.md §6](../wiring.md#6-test-procedure));
  - with USB-C, the plug shell (about 13 mm) and the male board's copper pads (about 5.5 mm) are closer to the pad than `TP_METAL_KEEPOUT`, reported once per rest variant. Neither is magnetic, and both are fixed in place while the pad is powered;
  - the rest's back edge is level with the switchplate. It warns on purpose with `--height 13`, for example.

## Variants

| Variant | Pocket depth (default) | Stack in the pocket, bottom → top |
|---|---|---|
| `glass` | 2.38 mm | ledge · PCB 1.0 · adhesive 0.13 · glass 1.1 → glass top 0.15 mm below the rim |
| `bare` | 1.28 mm | ledge · PCB 1.0 · adhesive/liner 0.13 → top 0.15 mm below the rim |

Both variants share the rest of the geometry. One STL is written per
`VARIANTS` entry, so you can add your own, for example
`--set "VARIANTS={'glass07': 0.7, 'film': 0.2}"`.

The connector is a second, separate choice ([Pick your connector](../README.md#pick-your-connector)).
Every rest variant works with every connector, and the preview shows each
variant × connector combination.

**The pocket**, top to bottom:

1. **Opening.** 65.5 x 49.5 mm (0.25 mm clearance per side) with R2.5 corners (`POCKET_CORNER_R`). The module and the glass have corners of about R4, which leaves a 0.97 mm gap at each corner; any part corner of R1.65 or more fits. The glass corner radius is not published, so check yours with a caliper or radius gauge. The rim has a 0.4 mm wide, 0.08 mm high bevel (`POCKET_RIM_CHAMFER`, `POCKET_RIM_CHAMFER_H`), so the vertical pocket wall still rises 0.07 mm above the glass or film top.
2. **Support ledge.** Flat, at least 2 mm wide all around. In fact it covers the module's whole component-free back.
3. **Component relief.** 1.6 mm deep under the component box + 1 mm.
4. **Solder well.** 3.5 mm deep under the six solder pads and the ZIF connector, next to the long edge that faces the keyboard.
5. **Push-out holes.** Two Ø6 holes through the floor under the flat front area of the module. Push the module out from below with a pen; you never touch the components.

**The cable** has its sleeve clamped in an **S-bend groove** in the well floor
(strain relief). It runs through a 4.5 x 4 mm tunnel 1.6 mm under the ledge
and the back rim (tunnel floor at 3.82 mm on the glass variant, so a 3.5 mm
cable fits with 1.6 mm of material above it). Its last 15 mm are loose wires
(`CABLE_PLUG_LOOSE_LEN`): they rise through the riser into a 6 x 4 mm
U-notch in the back-top edge on the centre line and turn straight back into
the pigtail's plug (`PLUG_EXIT='down'`). The plug hangs on the dock face over
a **plug bay**, a 26 x 7 x 2 mm recess in the back-top edge (`PLUG_BAY_*`,
floor at z 9.8). The plug housing clears the rest by 3.1 mm, and the
3 x 6 mm envelope behind it for the solder tails, heat-shrink and glue
(`PLUG_RELIEF_L/H`) clears it by 2.2 mm. The whole route from the pads to
the dock face is about 52 mm. The cable is never pinched between the rest
and the keyboard. Every overhang is either open to the top or a 4.5 mm
bridge.

With the **USB-C** connector the route is the same up to the notch. There the
four loose wires rise straight up into the grip's underside (its wire slot sits
right above the riser), with a 12 mm slack S-loop (`USBC_WIRE_SLACK`) stored in
the plug bay. The loop lets you pull the grip back the 10.65 mm it takes for the
plug to clear the well. The plugged grip floats about 1.6 mm above the rest
(1.25 mm when pulled back 7.5 mm), so wrist movement never pushes on it.

## The docks

Each connector has its own dock (`geometry/dock.py`). Every dock replaces
SW44/SW43 (front row, columns 6 and 7) and clips into their switch cut-outs in
the same way. The pogo dock (`stl/ithalat-dock-pogo.stl`) is described first;
the USB-C dock and its grip follow.

The pogo dock is a rounded block, 36.6 x 19 x 7 mm, that sits on the
switchplate:

- **Plugs.** Two hollow 13.85 mm plugs drop 3.4 mm into the empty 14 mm switch cut-outs.
- **Snap clips.** Four thin blades (0.8 mm, free length 6.35 mm, about 1.1 % bend strain) with 0.45 mm lips catch under the 1.2 mm switchplate, like MX switches. The catch faces are 45°, so a firm pull (about 20 N) takes the dock out without opening the case. `--set DOCK_CLIP_CATCH_DEG=0` gives a flat, permanent catch.
- **Connector pocket.** The keyboard half of the pogo pair is press-fitted into the front face (crush ribs, stop ledge), facing the rest, 3.2 mm above the plate. Pin 1 (SDA) is at the typist's left and is marked by a triangle on the top face. Add a drop of CA glue: the magnets pull the connector outward on every unplug.
- **Wire paths.** A 3 x 2.8 mm open-bottom channel runs out of the back at plate level, under the OLED cover's front edge, to the OLED header, the switchplate TB1 socket or the Pico. This is the recommended route, and it needs no case modification. A 5 mm hole drops into each plug for an optional adapter board under the plate. An acrylic bar blocks the route from the OLED header to the dock *under* the switchplate; going that way means filing a notch in it (see [wiring.md §3.3](../wiring.md#33-where-wires-can-and-cannot-run)).
- **Fit.** The front face is 0.6 mm behind the keyboard front edge; the body covers both cut-outs, keeps 0.75 mm to the neighbouring key cells and 2.5 mm to the OLED cover.
- **JST option.** `--connector jst_sh4` (or the old `DOCK_CONN_TYPE='jst_sh4'`) builds `stl/ithalat-dock-jst.stl`, with a bare JST SM04B-SRSS-TB header in place of the pogo pocket (Qwiic / STEMMA QT pinout: GND, 3V3, SDA, SCL). The header's tab sizes are estimates; check them against the part.

### USB-C dock and grip

USB-C needs a 5–20 N push to plug in and an 8–20 N pull to unplug. The magnetic
pogo needs only a few newtons. So the USB-C parts route that force through
printed plastic: it never passes through the wire solder joints, and the printed
parts keep it off the connectors' own mounting joints as far as they can. (The
receptacle still hangs on its shell legs and the plug on its straddle tails,
as in any USB-C device.) The parts follow the "well" layout from the design
study:

- **`stl/ithalat-dock-usbc.stl`** has the same plugs, clips and rear wire channel as the pogo dock, with these changes:
  - **Well.** The female board's receptacle mouth sits flush with the floor of a 4.45 mm deep, 11.64 x 5.95 mm well in the dock face, with a 1 mm × 45° entry chamfer. The grip's nose goes into the well with 0.15 mm clearance per side, so the well walls take side loads after about 2.7° of tilt instead of the plug shell. The well's bottom wall prints as a bridge, so it sits 0.15 mm lower (`USBC_BRIDGE_SAG`). The depth is automatic (`USBC_WELL_DEPTH = None`): as deep as your female board leaves the 1.2 mm rear stop, between 3.5 and 4.45 mm. The well keeps the plugged male board short, so the grip stays 1.95 mm clear of the trackpad pocket (the pocket starts 9 mm in front of the rest's back face).
  - **Board capture.** The female board drops in from the top. Its front edge bears on a 1.5 mm printed shoulder, a front wall with a 9.24 x 3.71 mm window just larger than the receptacle shell; two vertical crush ribs in the window grip the shell sides (0.1 mm). The shoulder takes the unplug pull. The board's rear edge sits against a 1.25 mm rear stop, which takes the plug-in push. The retainer (`stl/ithalat-usbc-retainer.stl`) drops in from the top until it is flush with the dock top and is held by two M2x4 self-tapping screws. It holds the board down by its rim, closes the window over the shell, and three half-round ribs press the receptacle shell onto the board (0.1 mm), so a plug that is levered up or down bears on plastic instead of on the shell's legs. Glue or crush ribs alone would not survive the unplug force.
  - **Diode cradle.** The 1N5817/1N5819 Schottky (DO-41, 5.2 x Ø2.7 mm) lies across the female board between the receptacle's legs and the pads, in a cradle under the retainer. For a SOT-23 BAT54 set `USBC_DIODE=(3.0, 1.4)`. If a diode does not fit the cradle, the dimension row says so and it goes inline at the tap.
  - **Taller and deeper body.** 36.6 x 20.9 x 9 mm with R0.6 edges (pogo: 36.6 x 19 x 7 mm). The connector axis is 4.25 mm above the plate (pogo: 3.2 mm), so the plugged grip floats above the rest. The body stays 4.2 mm below the keycap tops (`KEYCAP_TOP_Z`, an estimate) and 0.6 mm in front of the OLED cover, and its top is 0.2 mm below the cover's underside, so it still seats if your cover's front edge sits further forward than the drawing says.
  - **Stronger hold.** A 20 N pull a few millimetres above the plate tips the dock about its front edge and loads the two rear clips. The pogo dock's 45° catches would let go at about 2.5 N per clip in PETG. The USB-C dock's catch faces are flatter, 30° from horizontal (`USBC_CLIP_CATCH_DEG`), so they hold harder: alone they hold that pull with a margin of 1.65 (3.57 N needed per back clip, 5.88 N available in PETG). Its back clips sit on the plugs' back walls, and the retainer's two prongs slide in behind them, backed by a rib below the plate, so the clips cannot bend while the retainer is fitted (margin 16: the lips would have to shear). To take the dock out, undo the two retainer screws and lever the retainer up at its two pry notches first.
  - **Finger-brace flats** on the dock face, beside the well. To unplug, brace a fingertip there and pull the grip. The force then stays inside your hand.
- **The grip** (`stl/ithalat-usbc-grip-top.stl` + `stl/ithalat-usbc-grip-bottom.stl`) is a clamshell around the male board:
  - its nose fits the well with 0.15 mm clearance per side and a 1 mm × 45° chamfer, which catches the nose within about ±1 mm. With the plug fully seated (6.2 mm) the nose stops 0.3 mm short of the well floor. The nose is not symmetric top to bottom, so the grip goes in one way up only;
  - **the pull goes into the plug shell, not the board:** the shell is bedded in 2-part epoxy in a key groove around it inside the nose, so pulling the grip pulls the shell directly. The board is also clamped: two half-round crush ribs per side under its edge strips (0.3 mm, still 0.2 mm after the slicer rounds both faces to 0.2 mm layers), and a collar in front of the board stops its front corners. A push rib behind the board takes the plug-in push;
  - the wires are pinched over the push rib and again in a slot behind it, so pulling on them never loads the solder joints. Over the rib the band is as wide as the pad row; the slot then narrows to 4.2 mm, and the wires leave through the grip's underside, straight above the rest's notch and riser;
  - finger ridges on the sides give you something to hold;
  - it is an 18 x 13.3 x 6.5 mm clamshell split at the male board, aligned by two pegs and closed by two M2x4 self-tapping pan-head screws from below.
- **Every board dimension is a `USBC_*` constant** in `config.py`, marked "measure your boards". Cheap boards vary by seller, so measure yours with calipers and regenerate before you print ([wiring.md §7.4](../wiring.md#74-prepare-the-breakout-boards)). Male boards from 16.0 to 17.1 mm long build and verify; below about 16.4 mm the grip has no room for its pegs (verify warns, the push rib still aligns the halves).
- **Same rest.** The USB-C parts use the same rest, notch, riser and tunnel as the pogo.

## Configuration reference

All values are in mm unless noted. This list is every constant in
`config.py`, grouped as in the file; `--set NAME=VALUE` overrides any of
them. The frames are described in the `config.py` docstring:

- **Assembly frame:** the rest, as above.
- **Keyboard-local frame:** origin at the keyboard's front-left-bottom corner, top view.
- **TPS65 front view:** x from the module's left edge looking at the touch side, y from the long edge with the connector.
- **Dock-local frame:** origin midway between the two removed switch centres on the switchplate top (see `geometry/dock.py`).

### Keyboard (Yakamoz, verified from the KiCad/DXF files + caliper measurements)

| Name | Default | Meaning |
|---|---|---|
| `KEYBOARD_WIDTH` | `270.98` | plate / PCB outline width |
| `KEYBOARD_DEPTH` | `81` | plate / PCB outline depth |
| `KEYBOARD_HEIGHT` | `11.8` | bottom acrylic underside -> switchplate top (caliper) |
| `KEYBOARD_CORNER_R` | `2.8` | acrylic outline corner radius |
| `KEYBOARD_LAYERS` | `5 layers: 3 + 2 + 1.6 + 4 + 1.2` | bottom -> top: (name, thickness, material) |
| `KEY_PITCH` | `19.05` | 1U |
| `FRONT_ROW_Y` | `11.93` | front row (row index 3) key centre Y, keyboard-local |
| `FIRST_KEY_X` | `11.65` | column 0 key centre X, keyboard-local |
| `KEY_ROWS` | `4` | switch rows (row 0 = back, row KEY_ROWS-1 = front) |
| `KEY_COLS` | `14` | switch columns (column 0 = left) |
| `KEY_ABSENT` | `[(0, 6), (0, 7), (1, 6), (1, 7), (2, 6), (2, 7)]` | (row, col) grid positions without a switch (OLED cover / Pico area) |
| `REMOVED_KEYS` | `[(3, 6), (3, 7)]` | (row, col) replaced by the dock (SW44/SW43) |
| `OLED_COVER` | `(117.1, 22.1, 153.9, 81.0)` | x0, y0, x1, y1 keyboard-local |
| `OLED_COVER_TOP_Z` | `24` | smoked acrylic cover top (M2x10 standoffs) |
| `OLED_COVER_T` | `3` | cover thickness (2 or 3 mm, unverified; 3 = the conservative value for the dock clearance check) |
| `KEYCAP_TOP_Z` | `25` | keycap tops above the desk (assembly z, estimate); verify: every dock top must stay below it |
| `PICO_CENTER` | `(135.49, 52.69)` | keyboard-local; USB end faces the back |
| `PICO_SIZE` | `(21.0, 51.0)` | w (X) x l (Y) |
| `KEYBOARD_BUMPER_H` | `None` | height of the keyboard's own bumpers (measure them); None = unknown. The rest needs bumpers BUMPER_RECESS taller, because they sit in recesses |

### Wrist-rest body (ergonomics first: crowned bar, generously rounded edges)

| Name | Default | Meaning |
|---|---|---|
| `REST_WIDTH` | `270.98` | bbox width incl. the end bulges *(derived: recomputed after overrides)* |
| `REST_DEPTH` | `85` | front (wrist side) -> back (keyboard side) |
| `REST_HEIGHT` | `11.8` | max height = trackpad island height *(derived: recomputed after overrides)* |
| `REST_BACK_HEIGHT` | `11.8` | top height at the back edge, meets the keyboard *(derived: recomputed after overrides)* |
| `REST_FRONT_HEIGHT` | `6.5` | profile height at the front edge, before the nose round |
| `REST_PEAK_FROM_BACK` | `28` | crown peak, measured from the back edge |
| `REST_PROFILE` | `None` | optional [(distance_from_back, height), ...]: a monotone C1 spline (PCHIP) replaces the simple back/peak/front profile; normalised so its max == REST_HEIGHT |
| `REST_FALL_POWER` | `2` | shape of the peak->front fall: z = H - dH * t^p (p > 1 keeps the slope 0 at the peak -> C1) |
| `REST_BACK_EDGE_R` | `1.2` | back top edge round-over (against the keyboard) |
| `REST_FRONT_NOSE_R` | `9` | front nose: horizontal semi-axis of the elliptic lip |
| `REST_FRONT_NOSE_V` | `None` | front nose vertical semi-axis; None = auto: min(REST_FRONT_NOSE_R / 2, front wall budget) |
| `REST_END_EDGE_R` | `5` | left/right end round-over |
| `REST_END_TAPER` | `24` | the end round-over fades in from the back-corner radius over this length along the end (keeps the small back corners crease-free) |
| `REST_MIN_WALL` | `0.8` | min vertical wall left above the bottom chamfer |
| `REST_PLAN_FRONT_CORNER_R` | `16` | plan-view front corner radius |
| `REST_PLAN_BACK_CORNER_R` | `2.8` | plan-view back corner radius (= keyboard corners) |
| `REST_END_BULGE` | `2` | ends bulge outward by this sagitta (gentle arc, >= 0) |
| `REST_BOTTOM_CHAMFER` | `0.5` | 45 deg bottom chamfer (anti elephant-foot) |
| `REST_KEYBOARD_GAP` | `1.5` | gap between rest back face and keyboard front face |
| `MESH_EDGE_LEN` | `0.8` | target triangle edge on the curved top surface |

### Trackpad: Azoteq TPS65 (datasheet v1.06 + photo measurements)

| Name | Default | Meaning |
|---|---|---|
| `TP_WIDTH` | `65` | module outline (+-0.2) |
| `TP_DEPTH` | `49` | module outline (+-0.2), the connector edge is a long edge |
| `TP_CORNER_R` | `4` | photo fit, +-0.5 |
| `TP_PCB_T` | `1` | FR4 |
| `TP_ADHESIVE_T` | `0.13` | 3M 468MP front adhesive |
| `TP_COMPONENT_H` | `1.1` | tallest back-side part (0603 C2) incl. tolerance |
| `TP_COMPONENT_BOX` | `(12.9, 52.0, 4.4, 31.0)` | x0, x1, y0, y1 (front view) |
| `TP_PADS_BOX` | `(19.9, 30.8, 4.9, 7.1)` | six 2.0 mm-pitch solder pads |
| `TP_ZIF_BOX` | `(21.2, 29.7, 8.8, 14.2)` | 6-pin 0.5 mm ZIF J1 incl. actuator |
| `TP_PAD_NAMES` | `['SDA', 'SCL', 'VDDHI', 'GND', 'NRST', 'RDY']` | front view, left->right |
| `TP_CONNECTOR_EDGE` | `'back'` | the pad/ZIF long edge faces the keyboard (+Y) |
| `TP_CENTER_X` | `135.49` | module centre X (keyboard centre line) *(derived: recomputed after overrides)* |
| `TP_BACK_MARGIN` | `9` | rest back edge -> pocket opening back edge |
| `TP_MIN_SIDE_MARGIN` | `15` | min rest material left / right of the pocket opening |
| `TP_MIN_FRONT_MARGIN` | `8` | min rest material in front of the pocket opening |
| `TP_CLEARANCE` | `0.25` | pocket clearance per side (module +-0.2) |
| `TP_PCB_DENSITY` | `1.85` | g/cm3, FR4 (mass estimate only) |
| `TP_PARTS_MASS` | `1` | g, components on the module (mass estimate only) |
| `TP_METAL_KEEPOUT` | `15` | advisory: keep loose steel / magnets this far from the module outline (AZD068: 15-20 mm); verify WARNs about the docked pogo plug's two magnets and the USB-C plug shell / male board |
| `TP_SURFACE_RECESS` | `0.15` | glass / PCB top sits this far below the rim |
| `TP_BEZEL` | `5` | surface is exactly flat at REST_HEIGHT this far around the pocket ... |
| `TP_BLEND` | `14` | ... then blends (smoothstep, C1) into the profile |

### Glass overlay (keycapsss: 65 x 49 x 1.1, black, no adhesive)

| Name | Default | Meaning |
|---|---|---|
| `GLASS_T` | `1.1` | glass overlay thickness (--glass-t); 0.5..3 mm supported by the TPS65 |
| `GLASS_WIDTH` | `65` | glass outline (same as the module) |
| `GLASS_DEPTH` | `49` | glass outline |
| `GLASS_CORNER_R` | `4` | glass corner radius (not published - measure it); the pocket corner POCKET_CORNER_R is checked against it |
| `GLASS_DENSITY` | `2.5` | g/cm3 (mass estimate only) |
| `VARIANTS` | `{'glass': 1.1, 'bare': 0.0}` | id -> glass thickness, one STL each *(derived: recomputed after overrides)* |
| `VARIANT_LABELS` | `{'glass': 'With glass', 'bare': 'Without glass'}` | preview tab labels |

### Stepped pocket

| Name | Default | Meaning |
|---|---|---|
| `POCKET_LEDGE` | `2` | min flat support ledge under the module edge |
| `POCKET_CAVITY_DEPTH` | `1.6` | component relief below the PCB bottom |
| `POCKET_CAVITY_MARGIN` | `1` | relief = component box + this margin |
| `POCKET_WELL_DEPTH` | `3.5` | solder well below the PCB bottom (pads + ZIF) |
| `POCKET_WELL_MARGIN` | `1.5` | well = pads/ZIF box + this margin |
| `POCKET_INNER_R` | `1` | corner radius of the relief / well |
| `POCKET_CORNER_R` | `2.5` | plan corner radius of the pocket opening. A part fits only if its corner R >= POCKET_CORNER_R - 3.41 x TP_CLEARANCE, so a small radius is safe for an unmeasured module / glass corner (it costs a sub-mm corner gap); TP_CORNER_R still shapes the ledge |
| `POCKET_RIM_CHAMFER` | `0.4` | rim bevel: horizontal width ... |
| `POCKET_RIM_CHAMFER_H` | `0.08` | ... and height. Must be <= TP_SURFACE_RECESS - 0.05, so the vertical pocket wall rises above the glass / film top edge (a sideways knock meets the wall) |
| `PUSH_HOLE_D` | `6` | push-out holes through the floor (pen from below) |
| `PUSH_HOLE_POS` | `[(16.0, 38.0), (49.0, 38.0)]` | front-view module coords, component-free area (box ends at y = 31) |
| `MIN_FLOOR` | `2` | min material under every pocket / channel |

### Cable (5-core pigtail from the TPS65 pads to the dock)

| Name | Default | Meaning |
|---|---|---|
| `CABLE_D` | `3.5` | pigtail jacket diameter |
| `CABLE_CHANNEL_W` | `4.5` | tunnel / groove width |
| `CABLE_TUNNEL_H` | `4` | tunnel height (cable + clearance) *(derived: recomputed after overrides)* |
| `CABLE_NOTCH_W` | `6` | back-top-edge exit notch width (U-shaped) |
| `CABLE_NOTCH_DEPTH` | `4` | notch depth from the top |
| `CABLE_NOTCH_LEN` | `7` | notch length from the back face (leaves a 2 mm wall to the pocket) *(derived: recomputed after overrides)* |
| `CABLE_NOTCH_X` | `135.475` | notch / tunnel / riser centre X = KB_X0 + DOCK_CENTER_X (derived: straight below the dock connector) *(recomputed after overrides)* |
| `CABLE_RISER_BACK_WALL` | `2` | riser (tunnel -> notch) stops this far from the back face, so the cable can only leave through the notch. Riser length CABLE_NOTCH_LEN - this must be >= CABLE_D + 1 |
| `CABLE_RISER_TOP` | `None` | riser top z; None = auto: 0.3 mm above the height at which the U-notch is CABLE_CHANNEL_W wide, so the riser -> notch passage is never narrower than the channel |
| `CABLE_SKIN` | `1.6` | min material above the tunnel |
| `CABLE_SBEND` | `5` | strain-relief S-bend sideways offset in the well |
| `CABLE_GROOVE_PAD_SETBACK` | `1` | the S-bend starts this far in front of the pad row |
| `CABLE_GROOVE_TAIL` | `4` | straight groove end after the S-bend = where the cable sleeve ends (loose wires from there to the pads) |
| `CABLE_PLUG_LOOSE_LEN` | `15` | unsleeved wire length at the plug end (route length from the plug's tails back to the sleeve end) |
| `CABLE_WIRE_D` | `0.9` | one core (28 AWG silicone) outer diameter (preview) |
| `CABLE_WIRE_COLORS` | `{'SDA': '#2f6fd6', '3V3': '#d63a2f', 'GND': '#1d1f21', 'SCL': '#e3c22b', 'RDY': '#3a9a4a'}` | wiring.md colours (preview) |
| `CABLE_BEND_R` | `5` | centreline bend radius of the sleeved cable (route / preview drawing) |
| `CABLE_PIGTAIL_LEN` | `120` | total pigtail length (BOM / preview) |

### Pigtail plug (cable half of the connector) and the plug bay in the rest

| Name | Default | Meaning |
|---|---|---|
| `PLUG_BODY` | `(20.1, 4.0, 4.2)` | housing W (X) x D (mating axis, Y) x H (Z) outside the dock face; derived from DOCK_CONN_TYPE (pogo5: the MG005 housing, same as the keyboard half's DOCK_CONN_W/D/H; jst_sh4: PLUG_BODY_JST) *(recomputed after overrides)* |
| `PLUG_BODY_JST` | `(6.0, 2.0, 2.95)` | 'jst_sh4': the part of the SHR-04V-S cable plug left outside the header face (estimate) |
| `PLUG_RELIEF_W` | `None` | strain relief behind the housing (solder tails, joint heat-shrink, glue): width, None = PLUG_BODY width ... |
| `PLUG_RELIEF_L` | `3` | ... length behind the housing's back face ... |
| `PLUG_RELIEF_H` | `6` | ... and height, centred on the connector axis |
| `PLUG_TAIL_L` | `1.75` | solder tails out of the housing's back (MG005 drawing) |
| `PLUG_EXIT` | `'down'` | 'down': the loose wires turn straight down into the plug bay and riser right behind the relief (or use a right-angle pogo pair, Adafruit 5359); 'rear': the sleeved cable leaves the relief toward the user (needs room for the turn - fails verify by default) |
| `PLUG_WIRE_BEND_R` | `1` | 'down': the wires drop this far in front of the relief |
| `PLUG_MIN_CLEARANCE` | `0.5` | verify FAILs when the plug envelope comes closer to the rest than this |
| `PLUG_BAY_W` | `26` | plug bay cut into the back-top edge, centred on the notch: width (X) ... |
| `PLUG_BAY_L` | `7` | ... length from the back face (derived) ... *(recomputed after overrides)* |
| `PLUG_BAY_DEPTH` | `2` | ... depth below REST_HEIGHT (0 = no bay) |
| `PLUG_BAY_R` | `1` | bay plan corner radius |
| `PLUG_BAY_CHAMFER` | `0.4` | 45 deg chamfer on the bay's top edges (0 = none) |

### Engraving

| Name | Default | Meaning |
|---|---|---|
| `ENGRAVE_TEXT` | `'ithalat'` | engraved text ('' = none) |
| `ENGRAVE_FACE` | `'bottom'` | 'bottom' (mirrored, reads right when flipped) \| 'top' |
| `ENGRAVE_DEPTH` | `0.6` | 3 layers at 0.2 mm |
| `ENGRAVE_HEIGHT` | `12` | cap height |
| `ENGRAVE_FONT` | `'LiberationSans-Bold'` | font file stem (fonts-liberation) or a .ttf path |
| `ENGRAVE_CENTER_Y` | `None` | text centre Y; None = auto (front half, clear of bumpers / push holes; in front of the pad on 'top') |
| `ENGRAVE_MARGIN` | `2` | 'bottom': min distance text <-> bed footprint edge |
| `ENGRAVE_PAD_GAP` | `3` | 'top' auto placement: gap text top <-> pocket opening |

### Underside: bumpers and ballast

| Name | Default | Meaning |
|---|---|---|
| `BUMPER_D` | `10` | silicone bumper diameter (same type as the keyboard) |
| `BUMPER_RECESS` | `0.6` | locating recess depth |
| `BUMPER_INSET` | `11` | bumper centre inset from the bbox edges |
| `BUMPER_POSITIONS` | `None` | None = auto: 4 corners + front/back middle |
| `BALLAST_ENABLED` | `True` | steel ballast pockets in the two wrist wings (--no-ballast) |
| `BALLAST_SIZE` | `(78.0, 20.0, 5.0)` | steel flat bar L (X) x W (Y) x T = the longest bar that keeps the rules below with the default rest |
| `BALLAST_AUTO_SHORTEN` | `True` | True: a bar that does not fit is shortened / its pocket made shallower (logged, verify WARNs); False: that is a config error |
| `BALLAST_CLEARANCE` | `0.25` | pocket = bar + this per side (and on the depth) |
| `BALLAST_MIN_DIST_FROM_TP` | `20` | plan distance pocket <-> trackpad opening |
| `BALLAST_MIN_TOP_SKIN` | `3` | material above the pocket |
| `BALLAST_WALL` | `3` | min wall pocket <-> outside, measured at the bed (the footprint inside the bottom chamfer) |
| `BALLAST_MIN_LEN` | `20` | shorter pocket than this: omitted |
| `BALLAST_MIN_DEPTH` | `1.5` | shallower pocket than this: omitted |
| `BALLAST_CENTER_Y` | `None` | None = auto (mid depth) |
| `STEEL_DENSITY` | `7.85` | g/cm3 |

### Material / mass estimate

| Name | Default | Meaning |
|---|---|---|
| `PLA_DENSITY` | `1.24` | g/cm3 |
| `MASS_SHELL_T` | `1.2` | avg solid shell (perimeters + top/bottom) for the infill mass approximation |
| `STL_MAX_MB` | `12` | verify: max size of a rest STL |

### Connector variants (the builder picks one; every listed variant is generated)

| Name | Default | Meaning |
|---|---|---|
| `CONNECTORS` | `('pogo5', 'usbc')` | connector variants to generate (--connector NAME, repeatable); the first one is the preview default. 'pogo5' = 5-pin magnetic pogo, 'usbc' = USB-C breakout pair (USBC_* below), 'jst_sh4' = Qwiic JST-SH header |
| `CONNECTOR_IDS` | `{'pogo5': 'pogo', 'usbc': 'usbc', 'jst_sh4': 'jst'}` | file / manifest ids |
| `CONNECTOR_LABELS` | `{'pogo5': 'Magnetic pogo', 'usbc': 'USB-C', 'jst_sh4': 'JST-SH 4-pin'}` | preview / manifest labels (the Connector control) |

### Keyboard dock (read by geometry/dock.py; keyboard-local where noted)

| Name | Default | Meaning |
|---|---|---|
| `DOCK_ENABLED` | `True` | build stl/ithalat-dock-<connector>.stl (--no-dock) |
| `DOCK_SWITCH_CUTOUT` | `14` | switchplate cut-out (square) |
| `DOCK_PLUG_SIZE` | `13.85` | plug that drops into the cut-out |
| `DOCK_PLATE_T` | `1.2` | switchplate thickness (derived: KEYBOARD_LAYERS[-1]) *(recomputed after overrides)* |
| `DOCK_PLUG_DEPTH` | `3.4` | plug length below the plate top |
| `DOCK_CLIP_LIP` | `0.45` | snap lip under the plate |
| `DOCK_KEYS` | `2` | number of switch positions the dock replaces |
| `DOCK_BODY_W` | `36.6` | dock body above the plate: width (X, < 2U minus keycap clearance) |
| `DOCK_BODY_D` | `19` | dock body depth (Y); >= 18.9 so the body also covers the back edge of the 14 mm cut-outs (contract had 18.0) |
| `DOCK_BODY_H` | `7` | dock body height above the switchplate top |
| `DOCK_BODY_R` | `2` | dock body corner radius |
| `DOCK_FRONT_SETBACK` | `0.6` | dock front face behind the keyboard front face |
| `DOCK_CENTER_X` | `135.475` | midpoint of the removed switches (derived: REMOVED_KEYS) *(recomputed after overrides)* |
| `DOCK_SWITCH_CENTER_Y` | `11.93` | removed switch centre Y (derived: REMOVED_KEYS rows) *(recomputed after overrides)* |
| `DOCK_CONN_TYPE` | `'pogo5'` | legacy single-connector switch: derived = CONNECTORS[0]; overriding it alone (--set DOCK_CONN_TYPE=jst_sh4) generates only that connector |
| `DOCK_CONN_W` | `20.1` | connector housing width (5-pin magnetic pogo) |
| `DOCK_CONN_H` | `4.2` | connector housing height |
| `DOCK_CONN_D` | `4` | connector housing depth (mating axis) |
| `DOCK_CONN_CLEARANCE` | `0.15` | press-fit clearance per side |
| `DOCK_CONN_Z` | `3.2` | connector centreline above the switchplate top |
| `DOCK_WIRE_HOLE` | `5` | wire entry hole into the dock |
| `CONNECTOR_PINOUT` | `['SDA', '3V3', 'GND', 'SCL', 'RDY']` | pins 1..5, both halves (GND centre) |
| `KB_X0` | `0` | keyboard origin X in the assembly (centred) *(derived: recomputed after overrides)* |

### Keyboard dock internals (geometry/dock.py; dock-local frame, see its docstring)

| Name | Default | Meaning |
|---|---|---|
| `DOCK_PLUG_WALL` | `1.2` | plug wall: 3 perimeters at 0.4 mm |
| `DOCK_UNDERPLATE_GAP` | `4` | switchplate underside -> main PCB top (upper-middle acrylic; derived: KEYBOARD_LAYERS[-2]) *(recomputed after overrides)* |
| `DOCK_KEY_CLEARANCE` | `0.7` | min body inset from the 2-key cell edge, per side |
| `DOCK_CLIP_T` | `0.8` | snap blade thickness (2 perimeters) |
| `DOCK_CLIP_W` | `3.6` | snap blade width (shrunk automatically if it does not fit) |
| `DOCK_CLIP_SLOT` | `0.5` | slots on both sides of a blade |
| `DOCK_CLIP_OUTER_GAP` | `0.4` | gap between blade and body on the blade's outer side |
| `DOCK_CLIP_RELIEF` | `0.7` | free space behind a blade |
| `DOCK_CLIP_ROOT_SKIN` | `2` | solid body above the slot tops (blade root = BODY_H - this) |
| `DOCK_CLIP_CATCH_DEG` | `45` | catch face angle from horizontal (0 = flat MX-style catch, permanent) |
| `DOCK_CLIP_BACK_WALL` | `'inner'` | where the back-half blades sit: 'inner' = the walls facing each other (pogo / JST dock), 'back' = the plugs' back walls, outer half (the USB-C dock: its female board covers the web between the plugs) |
| `DOCK_CLIP_LAND` | `0.15` | vertical land at full lip height |
| `DOCK_CLIP_LEADIN_DEG` | `30` | lead-in ramp angle from vertical (insertion) |
| `DOCK_CLIP_EMBED` | `0.3` | lip prism overlap into the blade (boolean robustness) |
| `DOCK_CONN_RIB_H` | `0.25` | crush rib protrusion into the connector pocket (0 = no ribs) |
| `DOCK_CONN_RIB_R` | `0.6` | crush rib radius (half-round) |
| `DOCK_CONN_STOP` | `0.6` | stop ledge width at the pocket bottom (x ends) |
| `DOCK_CONN_STOP_Z` | `0.4` | stop ledge height at the pocket bottom (top/bottom) |
| `DOCK_CONN_NECK_D` | `1` | depth of the stop "neck" behind the pocket |
| `DOCK_CONN_PROUD` | `0` | connector face proud of the dock face (+) / recessed (-) |
| `DOCK_CONN_MIN_WALL` | `0.6` | min material below / above the connector pocket |
| `DOCK_CAV_FLOOR` | `1` | wire cavity floor z (floor over the plugs) |
| `DOCK_CAV_ROOF` | `1.6` | solid top skin over the wire cavity |
| `DOCK_CAV_MIN_D` | `4` | min wire-cavity depth behind the neck (solder tails + joints) |
| `DOCK_CAV_MARGIN` | `0.2` | wire hole -> cavity wall margin |
| `DOCK_REAR_CH_W` | `3` | rear wire channel width (5 x 30 AWG side by side) |
| `DOCK_REAR_CH_H` | `2.8` | rear wire channel height above the plate (open bottom) |
| `DOCK_MARK_DEPTH` | `0.4` | pin-1 marker depth on the top face (2 layers) |
| `DOCK_MARK_SIZE` | `1.6` | pin-1 triangle base width / height |
| `DOCK_SEGMENTS` | `48` | circle resolution of the dock's round features |
| `POGO5_PITCH` | `2.54` | 5-pin magnetic pogo pin pitch (Adafruit 5413 / MG005) |
| `DOCK_JST_W` | `6` | 'jst_sh4': SM04B-SRSS-TB body width |
| `DOCK_JST_H` | `2.95` | 'jst_sh4': body height (mounting height) |
| `DOCK_JST_D` | `4.25` | 'jst_sh4': body depth (mating axis) |
| `DOCK_JST_TAB_W` | `7` | 'jst_sh4': width across the SMD fitting nails (estimate) |
| `DOCK_JST_TAB_H` | `0.9` | 'jst_sh4': fitting nail height above the body bottom (estimate) |
| `JST_SH4_PITCH` | `1` | 'jst_sh4': pin pitch |
| `JST_SH4_PINOUT` | `['GND', '3V3', 'SDA', 'SCL']` | 'jst_sh4': Qwiic / STEMMA QT pins 1..4 |

### USB-C variant ('usbc' in CONNECTORS; geometry/usbc.py, dock-local frame)

Female (blue) breakout in the dock, male (green) breakout in a printed grip on the rest's pigtail. Only the 4 big pads are used: G = GND, V = 3V3 through a series Schottky at the keyboard end, D+ = SDA, D- = SCL (no RDY). The breakout boards differ from seller to seller: MEASURE YOUR BOARDS with calipers and override every board / shell value below before printing.

| Name | Default | Meaning |
|---|---|---|
| `USBC_F_BOARD` | `(13.0, 13.5, 1.0)` | female board W (X) x L (mating axis) x T - measure |
| `USBC_F_SHELL` | `(8.94, 3.26, 7.35)` | receptacle shell W x H x L (mouth -> back) - measure |
| `USBC_F_SHELL_PROUD` | `1.5` | receptacle mouth ahead of the female board's front edge - measure |
| `USBC_F_SHELL_SINK` | `0` | shell bottom below the board top (0 = top mount; mid-mount receptacles sink into a board cut-out) - measure |
| `USBC_F_SHELL_X` | `0` | receptacle centre right of the board centre (X) - measure |
| `USBC_F_LEG_RELIEF` | `0.5` | recess under the board for shell-leg stubs / solder |
| `USBC_F_RIM` | `1.5` | the board rests on (and the retainer presses) this edge rim; the relief inside it is the dock's widest bridge (<= 10 mm) |
| `USBC_F_DEPTH` | `6.2` | receptacle mating depth: mouth -> tip of a fully seated plug (USB-IF reference 6.20) |
| `USBC_F_PADS` | `['G', 'D', 'D', 'V']` | female pads, left -> right in the dock (beep-test them) |
| `USBC_F_PAD_L` | `3` | female pad row length (Y) at the board's rear end - measure |
| `USBC_F_LEGS_L` | `1` | SMD signal-leg row behind the shell (kept free of the diode) |
| `USBC_M_BOARD` | `(8.64, 16.5, 0.8)` | male board W x L (plug tip -> board rear end) x T - measure; sellers' boards run about 8.0-8.64 x 16.0-17.1: every length in that range builds and verifies; below ~16.4 the grip is too short for its alignment pegs (dropped, verify warns) |
| `USBC_M_SHELL` | `(8.25, 2.4)` | plug shell W x H (USB-C spec) - measure |
| `USBC_M_SHELL_R` | `1` | plug shell corner radius (grip cavity corner chamfer) |
| `USBC_M_PLUG_L` | `9` | plug length from the tip; the PCB (straddle tails) starts behind it - measure |
| `USBC_M_PADS` | `['V', 'D-', 'D+', 'G']` | male pads, left -> right as assembled (beep-test them) |
| `USBC_M_PAD_L` | `3` | pad length (Y) at the male board's rear end - measure |
| `USBC_M_TAIL_H` | `0.4` | straddle tails / solder above and below the board (grip relief) |
| `USBC_M_JOINT_H` | `1.5` | solder joints + wires above the pads (grip cavity height) |
| `USBC_M_RIM` | `0.8` | the grip clamps the male board on edge strips this wide |
| `USBC_M_TAB_L` | `2` | plug shell side tabs + their solder on the board edges reach this far behind the board's front edge: no clamp strips there (relief USBC_M_TAIL_H above and below) - measure |
| `USBC_SIGNALS` | `{'G': 'GND', 'V': '3V3', 'D+': 'SDA', 'D-': 'SCL'}` | breakout pad -> signal |
| `USBC_DIODE` | `(5.2, 2.7)` | series Schottky body L x D: 1N5817/1N5819 DO-41 (BAT54 SOT-23: (3.0, 1.4)); anode -> Pico 3V3, cathode -> V pad |
| `USBC_DIODE_CLEARANCE` | `0.15` | cradle clearance around the diode body |
| `USBC_DIODE_LIFT` | `0.1` | diode body above the female board top (tape it, Kapton) |
| `USBC_DIODE_ROOF` | `1` | min retainer material over the diode cradle (else: inline diode) |
| `USBC_CONN_Z` | `4.25` | connector axis above the switchplate top (grip floats over the rest) |
| `USBC_DOCK_H` | `9` | USB-C dock body height above the plate (keycap tops ~13 above); the top stays under the OLED cover's underside (9.2 above the plate with a 3 mm cover), so a cover edge further forward than OLED_COVER cannot block the dock - measure the cover edge |
| `USBC_DOCK_R` | `0.6` | USB-C dock corner / top-edge radius (DOCK_BODY_R for this dock) |
| `USBC_DOCK_D` | `20.9` | USB-C dock depth (Y): back face 0.6 in front of the OLED cover |
| `USBC_FACE_FLAT_MIN` | `0.3` | flat dock face kept between the well's entry chamfer and the top-edge round |
| `USBC_WELL_DEPTH` | `None` | chamfered well in the dock face; the receptacle mouth sits at its floor and the grip nose enters it (side loads -> printed walls); None = auto: as deep as the female board leaves rear stop (USBC_REAR_STOP_MIN), within USBC_WELL_DEPTH_RANGE (4.45 with the default board); deeper = longer nose engagement and the grip further from the trackpad edge |
| `USBC_WELL_DEPTH_RANGE` | `(3.5, 4.45)` | auto well depth limits (a deeper well shortens the grip body: no room for its pegs / screws; shallower: grip nearer the pad) |
| `USBC_WELL_CLEARANCE` | `0.15` | grip nose -> well wall, per side (verify prints the tilt the nose takes before it bears on the wall, ~2.7 deg by default) |
| `USBC_WELL_CHAMFER` | `1` | 45 deg entry chamfer (capture range) |
| `USBC_WELL_FLOOR_MIN` | `0.6` | min material between the well / its entry chamfer and the plate |
| `USBC_BRIDGE_SAG` | `0.15` | sag allowance: the dock's bridged faces that face a fit (the well's bottom wall, the shoulder window floor) sit this much further away (they print as bridges and sag toward the fit) |
| `USBC_SHOULDER_T` | `None` | front shoulder wall well floor -> board front edge; None = auto: max(USBC_SHOULDER_MIN_T, USBC_F_SHELL_PROUD) (flush mouth) |
| `USBC_SHOULDER_MIN_T` | `1.2` | verify: min shoulder wall (takes the 20 N pull) |
| `USBC_MOUTH_TOL` | `0.2` | verify: receptacle mouth vs well floor |
| `USBC_WINDOW_CLEARANCE` | `0.15` | shoulder window = receptacle shell + this per side |
| `USBC_WINDOW_RIB` | `(0.25, 0.5)` | vertical crush ribs on the window's side walls: protrusion, radius (protrusion - USBC_WINDOW_CLEARANCE = grip on the shell) |
| `USBC_BOARD_CLEARANCE` | `0.15` | board pocket = female board + this per side (X) |
| `USBC_BOARD_PLAY` | `0.2` | board pocket length = board L + this (Y) |
| `USBC_REAR_STOP_MIN` | `1.2` | verify: min rear stop wall behind the board (takes the 20 N push) |
| `USBC_REAR_CH_W` | `4` | rear wire channel width (4 wires side by side) |
| `USBC_REAR_CH_H` | `None` | rear channel height above the plate (open bottom); None = board top + USBC_REAR_CH_ABOVE_BOARD |
| `USBC_REAR_CH_ABOVE_BOARD` | `1.3` | ... (the wires leave the pads over the board's rear edge) |
| `USBC_CLIP_CATCH_DEG` | `30` | USB-C dock catch face angle from horizontal: flatter than the pogo dock's 45 deg, so its clips hold harder (20 N pulls) |
| `USBC_CLIP_ROOT_Z` | `5` | blade root height above the plate (as in the pogo dock: 6.35 mm free length, ~1.1 % strain; taller = softer clips) |
| `USBC_CLIP_RELIEF` | `1.2` | free space behind a blade (the lock prong fills it) |
| `USBC_CLIP_BACK_WALL` | `'back'` | DOCK_CLIP_BACK_WALL for the USB-C dock |
| `USBC_BRACE_MIN_W` | `8` | verify: flat dock face either side of the well (finger brace) |
| `USBC_MAX_BRIDGE` | `10.5` | verify: widest bridge of a USB-C part in print orientation |
| `USBC_MAX_OVERHANG` | `0.6` | verify: widest steeper-than-48.6 deg overhang (the 30 deg catch lips print as 0.45 mm overhangs) |
| `USBC_RET_ENABLED` | `True` | print stl/ithalat-usbc-retainer.stl (holds the board down, closes the window, carries the clip lock prongs); without it nothing holds the female board down: epoxy it in |
| `USBC_RET_CLEARANCE` | `0.1` | retainer -> opening clearance per side |
| `USBC_RET_PLATE_T` | `2.4` | retainer top plate (arms) thickness = recess depth (holds the screw heads' counterbores) |
| `USBC_RET_ARM_W` | `2.4` | arm width (Y) from the central block to the prongs |
| `USBC_RET_CAV_H` | `1.6` | wire cavity height above the female board's pads |
| `USBC_RET_BUMP` | `0.25` | crush bumps on the prong sides (interference = this - USBC_LOCK_PRONG_X_CLR); they locate the retainer, screws hold it |
| `USBC_RET_BUMP_W` | `0.6` | crush bump width (Y) |
| `USBC_RET_BUMP_Z` | `(0.4, 0.3)` | bump band: starts this far above the blade root, ends this far below the arm recess floor |
| `USBC_RET_SHELL_PRESS` | `(0.1, 0.5, 3)` | half-round ribs under the retainer's shell channel that press the receptacle shell onto the board (one over the window): interference, radius, count; side loads then bear on plastic |
| `USBC_RET_SCREW` | `(2.0, 1.6, 2.3, 3.9, 1.4, 4.0)` | 2 x M2x4 self-tapping pan head down through the arms into the dock (positive hold-down): nominal, pilot D (dock), clearance D (arm), head counterbore D, its depth, pilot depth |
| `USBC_RET_SCREW_L` | `4` | retainer screw length (M2x4, the same screw as the grip) |
| `USBC_RET_SCREW_X` | `None` | screw centres +-X on the arms; None = midway between the board pocket and the back blade's side slot |
| `USBC_SCREW_PULLOUT_N` | `60` | verify: conservative pull-out of one M2 self-tapping screw with >= 2.5 mm of thread in PETG / PLA |
| `USBC_LOCK` | `True` | 2 prongs behind the back clip blades: positive dock lock |
| `USBC_LOCK_PRONG_T` | `1.05` | prong thickness (Y) in the USBC_CLIP_RELIEF gap |
| `USBC_LOCK_BACK_CLR` | `0.05` | prong -> slot back wall (and backing rib); the rest of the relief is the prong -> blade gap |
| `USBC_LOCK_PRONG_X_CLR` | `0.2` | prong -> slot side walls (X), per side |
| `USBC_LOCK_BACKING` | `1` | backing rib (Y) in the plug hollow below the plate: backs the prong down past the lip, so the blade cannot push it away |
| `USBC_LOCK_PRONG_BELOW` | `2.4` | prong reaches this far below the switchplate top (past the lip) |
| `USBC_PRY_NOTCH` | `(1.2, 3.0, 1.0)` | pry notches at the arm ends: width (X), length (Y), depth |
| `USBC_GRIP_W` | `18` | grip body width (pinch faces) |
| `USBC_GRIP_BELOW` | `3` | grip body (and nose) bottom below the axis |
| `USBC_GRIP_ABOVE` | `3.5` | grip body top above the axis |
| `USBC_GRIP_FACE_GAP` | `0.5` | grip body front -> dock face (mated) |
| `USBC_GRIP_WALL` | `1.6` | min grip wall |
| `USBC_GRIP_NOSE_WALL` | `1.2` | min nose wall (the part that enters the well) |
| `USBC_GRIP_NOSE_CHAMFER` | `1` | 45 deg chamfer on the nose's long edges (well bridge <= 10) |
| `USBC_GRIP_NOSE_LEADIN` | `0.4` | chamfer around the nose face |
| `USBC_EMBED` | `0.3` | overlap of merged solids (nose root in the body; boolean robustness only) |
| `USBC_NUDGE` | `0.00731` | odd offset on the plug-shell cavity's chamfer so its corners never sit exactly on a relief face (mesh robustness only) |
| `USBC_GRIP_CAV_CLEARANCE` | `0.1` | grip cavity around the plug shell / male board |
| `USBC_GRIP_CAV_CHAMFER` | `0.6` | 45 deg corner chamfer of the plug-shell cavity (clears the shell's USBC_M_SHELL_R corners, keeps the nose corner wall) |
| `USBC_GRIP_EDGE` | `0.6` | 45 deg chamfer on the body's top / bottom edges |
| `USBC_GRIP_R` | `2` | body plan corner radius |
| `USBC_SHELL_EXPOSED` | `6.5` | plug shell exposed in front of the grip nose; the nose stops (this - USBC_F_DEPTH) before the well floor when seated |
| `USBC_GRIP_BOARD_SQUEEZE` | `0` | flat board-pocket ceiling below the board top (+) or above it (-); the crush ribs below do the clamping |
| `USBC_GRIP_CLAMP_RIB` | `(0.3, 2)` | half-round crush ribs across the bottom half's seat under the board's edge strips: height (= radius), count per side; the screws crush them, so the clamp survives layer rounding |
| `USBC_PRINT_LAYER` | `0.2` | verify: layer height the grip clamp is checked at |
| `USBC_GRIP_COLLAR` | `(0.03, 0.6)` | shell collar at the male board's front edge: clearance per side around the plug shell, length; its rear face stops the board's front corners (boards wider than the shell) |
| `USBC_GRIP_GLUE_GROOVE` | `(0.4, 1.2, 0.2)` | epoxy key groove around the plug shell (sides and bottom): depth (the sides keep USBC_GRIP_NOSE_WALL), length, gap after the collar; cured epoxy locks the shell to the grip |
| `USBC_GRIP_BOARD_GAP` | `0.1` | male board rear edge -> push rib |
| `USBC_GRIP_PUSH_RIB` | `0.8` | rib behind the board's rear edge (takes the insertion push) |
| `USBC_GRIP_WIRE_SQUEEZE` | `0.1` | wire clamp: slot = CABLE_WIRE_D - this (zig-zag pinch) |
| `USBC_GRIP_WIRE_BAND` | `4.2` | wire slot width (X) at the grip's underside (4 wires side by side); over the push rib the band is as wide as the pad row (male board W - 2 x USBC_M_RIM) and the slot tapers to this |
| `USBC_GRIP_JOINT_MARGIN` | `0.5` | solder-joint cavity reaches this far past the pad row |
| `USBC_GRIP_SCREW` | `(2.0, 1.6, 2.3, 3.9, 1.4, 3.0)` | M2x4 self-tapping pan head: nominal, pilot D (top half), clearance D, head counterbore D, its depth (bottom face), pilot depth |
| `USBC_GRIP_SCREW_L` | `4` | grip screw length (M2x4) |
| `USBC_GRIP_SCREW_X` | `6.25` | screw / peg centres beside the male board (+-X); the screws sit beside the board's middle, kept inside the grip body |
| `USBC_GRIP_PEG` | `(1.8, 1.5, 0.2)` | alignment pegs: D, height, hole oversize (printed holes shrink) |
| `USBC_GRIP_PEG_WALL` | `0.6` | min wall peg hole <-> screw hole; less (short boards): no pegs |
| `USBC_GRIP_RIDGES` | `(0.4, 1.0, 2.0)` | finger ridges on the sides: depth, width, pitch |
| `USBC_GRIP_RIDGE_MARGIN` | `0.3` | ridges stop this far from the edge chamfers / counterbores |
| `USBC_GRIP_MIN_FLOAT` | `0.5` | verify: grip bottom above the rest top (mated and withdrawn) |
| `USBC_GRIP_POCKET_CLEAR` | `1` | verify: grip rear end -> trackpad pocket opening (plan) |
| `USBC_WITHDRAW` | `7.5` | travel that frees the plug (verify sweeps the grip back) |
| `USBC_WIRE_SLACK` | `12` | extra loose wire (S-loop in the plug bay) so the grip can be withdrawn; verify: >= plug tip -> dock face (plug clears the well) |

### Dock retention (both docks): cantilever clip model, see geometry/usbc.py retention()

| Name | Default | Meaning |
|---|---|---|
| `CLIP_E_MPA` | `2000` | blade material modulus (PETG ~2.0 GPa; PLA ~3.5) |
| `CLIP_MU` | `0.3` | friction catch face <-> switchplate edge |
| `CLIP_LIP_SHEAR_MPA` | `15` | conservative lip shear strength (locked blade failure mode) |
| `USBC_PULL_N` | `20` | design pull: USB-C max extraction force |
| `USBC_PULL_UP_DEG` | `20` | design pull direction: this far above horizontal |
| `USBC_RETENTION_MIN` | `1.5` | verify: required margin on the dock tipping load |

## Printing

Print the rest, plus the parts for **your** connector: the pogo dock, or the
USB-C dock, both grip halves and the retainer.

| Setting | Rest | Docks (pogo, USB-C) | USB-C grip halves, retainer |
|---|---|---|---|
| Material | PLA or PETG. PETG copes better with warm wrists and is less brittle. **No conductive or metal-filled filament** near the trackpad. | **PETG** (or a well-tuned PLA): the snap blades bend across their layer lines. | PETG or PLA. No conductive filament. |
| Orientation | As exported: **bottom down**, pocket up. **No supports.** | As exported: **upside down**, top face on the bed. **No supports.** | As exported: lower grip half on its bottom face, upper half on its flat split face, retainer upside down (top plate on the bed). **No supports.** |
| Layer height | **0.12–0.16 mm**, or variable/adaptive layers, so the curved top and front nose don't stair-step under your wrists. | 0.12–0.16 mm | 0.12–0.16 mm (the nose must fit the well cleanly) |
| Walls | **4 perimeters** | 3 perimeters (the plug walls are 1.2 mm, the blades 0.8 mm) | 3 perimeters |
| Top / bottom | **6+ top layers** (≥ 1 mm on the curved top), 4–5 bottom layers | 4 / 4 | 4 / 4 |
| Infill | **25–40 % gyroid** (more if you skip the ballast) | 100 % or 4+ perimeters (small part) | 100 % (small parts that take the 8–20 N unplug force) |
| Seam | rear or aligned to the back face | rear | rear, away from the nose |
| First layer | the 0.5 mm bottom chamfer absorbs elephant-foot; keep the first layer clean for the mirrored engraving | the pin-1 marker is on the bed; keep the first layer clean | keep elephant-foot off the nose, or it binds in the well |

Print one dock first as a fit test: it should click into the two cut-outs and
come out again with a firm pull. With USB-C, the dock with the retainer fitted
should not come out under a firm pull. Before you solder, test-fit the bare
female board in the USB-C dock and the bare male board in the grip, and check
that the grip's nose slides into the well without force.

Things that print over air:

- **The bottom engraving** prints against the bed: the first solid layer above it bridges over the recessed letters.
- **The bumper recesses** are 0.6 mm-high Ø10 bridges.
- **The cable tunnel** is a 4.5 mm bridge. The plug bay and the notch are open to the top.
- **The ballast pocket ceilings** are about 20.5 mm bridges across the bar width. Any tuned printer bridges this. A little sag is hidden and is absorbed by the 0.25 mm depth clearance. If your printer can't bridge it, use 10 mm-wide bars (one per side) and `--set "BALLAST_SIZE=(78,10,5)"`. That makes a 10.5 mm bridge and halves the ballast to about 61 g.
- **The dock's** pocket, cavity and plug floors are flat bridges of at most 20.4 mm; the lips and the top edge are 45° overhangs.
- **The USB-C dock, retainer and grip:** the widest bridge is 10.0 mm (the leg relief under the female board); the well's bottom wall (about 9.5 mm) and the shoulder window floor (9.24 mm) come next. Both of those face a fit, so they sit `USBC_BRIDGE_SAG` (0.15 mm) further away to absorb the sag; scrape off strings before the first fit. The only overhangs steeper than 48.6° are the 30° clip lips, 0.45 mm wide (the window's crush ribs and the screw counterbores are smaller). verify measures both (`USBC_MAX_BRIDGE`, `USBC_MAX_OVERHANG`).

Approximate mass of the default glass rest in PLA, from the generator output:

| Infill | Mass |
|---|---|
| 15 % | ~109 g |
| 25 % | ~128 g |
| solid | ~266 g |

With the two steel bars (+122 g), the trackpad and the glass, it weighs about
**266 g on the desk** at 25 % infill. The pogo dock is about 5 g. The USB-C
dock is about 6.3 g, the grip about 1.2 g (both halves) and the retainer
about 1.2 g (solid PLA).

## Assembly order

The full steps, pinout and protection parts are in [wiring.md](../wiring.md);
the parts are in [bom.md](bom.md). The short version:

1. **Order and print.** Buy the parts for your connector in [bom.md](bom.md). Print the rest variant that matches your trackpad (glass / bare) and the parts for your connector ([Printing](#printing)).
2. **Keyboard side, both connectors** ([wiring.md §3](../wiring.md#3-keyboard-side-step-by-step)). Pull SW44/SW43 and take off the OLED cover; nothing else is opened, cut or filed. Connect the wires to tap A (the OLED header joints or a male header plugged into the switchplate TB1 socket) or tap B (the Pico pins): SDA GP2, SCL GP3, 3V3(OUT), GND, and with the pogo optionally RDY on GP15. Lay them flat on the switchplate under the cover, into the dock's rear channel.
3. **Keyboard half of the connector.**
   - **Magnetic pogo** ([wiring.md §3.5](../wiring.md#35-magnetic-pogo-solder-the-receptacle-and-fit-the-dock)): press the receptacle into the pogo dock with pin 1 at the left, glue it, and click the dock into the two cut-outs.
   - **USB-C** ([wiring.md §7.4–7.5](../wiring.md#74-prepare-the-breakout-boards)): remove the two 5.1 kΩ resistors from the female board, put the Schottky diode in the 3V3 line (band toward the V pad), check the receptacle's shell legs are soldered, solder the board, press it into the USB-C dock behind the shoulder, click the dock in, then press the retainer in until it is flush and drive its two M2x4 screws (it holds the board, presses the shell and locks the clips).
4. **Prepare the pigtail** ([wiring.md §4](../wiring.md#4-wrist-rest-side-step-by-step)). Solder very flexible 28 AWG wires (cut to `CABLE_PIGTAIL_LEN`, 120 mm, and trimmed later) to the TPS65's 2.0 mm solder pads: SDA, SCL, VDDHI (3V3), GND, and with the pogo optionally RDY. That is five wires for the pogo and four for USB-C. Leave NRST open. Sleeve about 18 mm of the bundle for the groove and leave the end loose. **VDDHI is 3.3 V max, never 5 V.**
5. **Route the cable.** Lay the sleeve into the S-groove in the solder well (a dab of hot glue is fine), through the tunnel and up out of the back-top notch. Neither the pogo plug nor the USB-C male board fits through the tunnel, so you solder it last.
   - **Magnetic pogo:** cut the loose wires (about 15 mm) to reach the docked plug's tails, use only 1.5 mm heat-shrink on the joints, and keep tails, heat-shrink and glue within 3 mm behind the housing and 6 mm tall.
   - **USB-C** ([wiring.md §7.6](../wiring.md#76-rest-side-male-board-in-the-grip)): solder the male board (wires on the front half of each pad), bed the plug shell in 2-part epoxy in the nose's key groove, lay the board in the lower grip half, lead the wires over the push rib and down the slot, close the grip with two M2x4 screws, and store the 12 mm slack loop in the plug bay. Let the epoxy cure before the first plug-in.
6. **Fit the module.**
   - **Glass variant:** bond the glass to the module first (see *Glass handling*).
   - Drop the module in, touch side up, with the pad/ZIF edge toward the keyboard. It rests on the ledge.
   - No glue is needed. A few dots of thin double-sided tape on the ledge keep it from lifting. To remove the module, push it out from below through the two holes.
7. **Connect and test.** Set the rest in front of the keyboard (1.5 mm gap).
   - **Magnetic pogo:** dock the pigtail's magnetic plug, and run the end-to-end test in [wiring.md §6](../wiring.md#6-test-procedure) before you power it.
   - **USB-C:** steady the keyboard with one hand and push the grip straight into the well with the other ([wiring.md §7.8](../wiring.md#78-plugging-and-unplugging)). Run the beep test in both plug orientations ([wiring.md §7.7](../wiring.md#77-test-procedure-usb-c)) before you power it. Label both halves "NOT USB".
8. **Firmware.** Build and flash the `ardakilic_trackpad` keymap and calibrate the axes: [firmware/README.md](../firmware/README.md). Plug the pad in before the first power-up. After that, the keymap detects a re-plugged pad within about 1.3 s and re-initialises it (see the [hot-plug section](../firmware/README.md#hot-plug-behaviour-and-limits)); stock QMK would only initialise it at boot.

## Ballast and bumpers

- **Ballast.**
  - Two pockets from the underside, one in each wrist wing, take steel flat bar.
  - The bars are **78 x 20 x 5 mm** each (`BALLAST_SIZE`), about 61 g each and 122 g per pair. The pockets are 78.5 x 20.5 x 5.25 mm, so cut the bar to 78 mm; a longer bar does not fit. 78 mm is the longest bar that stays **≥ 20 mm from the trackpad** and keeps a 3 mm wall at the bed with the default rest.
  - The pockets keep ≥ 3 mm of plastic above them.
  - If an override makes a bar not fit, the generator shortens it or makes its pocket shallower (`BALLAST_AUTO_SHORTEN = True`), logs it, and verify WARNs with the size to buy. With `BALLAST_AUTO_SHORTEN = False` that is a config error instead.
  - Glue the bars in (CA or epoxy) or close the pockets with the anti-slip pad.
  - **No loose metal near the pad:** keep steel, magnets and coins at least 15 mm (`TP_METAL_KEEPOUT`; Azoteq AZD068 says 15–20 mm) from the TPS65. Moving conductors are the worst case for capacitive sensing.
  - **The one exception is the docked pogo plug.** Its two small magnets sit about 7.35 mm from the module outline, and verify flags that as a WARN. (The USB-C connector has no magnets; its plug shell sits about 13 mm from the module and the male board's copper pads about 5.5 mm, which verify also lists as advisories.) They are accepted because they are fixed in place while the pad is powered (the plug is what powers it) and the controller calibrates at power-up. Do the drift check at the first power-up ([wiring.md §6](../wiring.md#6-test-procedure)); if the cursor drifts near the back edge, raise `TP_BACK_MARGIN`.
- **Bumpers.**
  - Six Ø10 x 0.6 mm locating recesses take the same type of silicone bumper as the keyboard: four near the corners and two on the centre line, front and back, which support the trackpad area. The back-middle one moves sideways automatically to stay clear of the cable tunnel.
  - **Use bumpers 0.6 mm (`BUMPER_RECESS`) taller than the keyboard's**, because they sit in 0.6 mm recesses. Then the rest's top is level with the switchplate. Bumpers of the keyboard's own height leave the rest 0.6 mm low. Set `KEYBOARD_BUMPER_H` to your measured keyboard bumper height and the preview's print notes give the exact value.

## Glass handling

- The keycapsss overlay is 65 x 49 x 1.1 mm, black, with no adhesive. **It is fragile at the edges.**
- The pocket keeps the glass top **0.15 mm below the rim**. That protects the edges from knocks and from your wrists.
- The pocket gives 0.25 mm clearance per side. **Never force or clamp the glass edges**, and never press the module in by its corners.
- The pocket corners are R2.5 (`POCKET_CORNER_R`), so any glass corner of R1.65 or more fits with a 0.97 mm gap at R4. Measure your glass corner before you bond it; the radius is not published.
- Bond the glass with the module's own 3M 468MP adhesive. Use **no air gap**, because air gaps hurt sensitivity. Roll it down from one short edge and press evenly across the face, not at the edges.
- The PCB is supported over its whole flat back by the ledge, so taps never flex it or point-load the glass.
- To use thinner glass (Azoteq's own option is 0.7 mm): `--glass-t 0.7`.
- The bare variant leaves the solder mask or adhesive liner as the touch surface. A thin PET or PEI sheet on top feels better than the liner.
- Never lay the magnetic pogo plug on the glass.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `make verify` fails right after an override | `generate` and `verify` got different `GEN_ARGS` (stale STLs or manifest). Run `make generate verify GEN_ARGS="..."` together. |
| `config error: ...` or `unknown config name` | A value cannot produce a valid part, or the name is misspelt. Every valid name is listed above. |
| `--set` value is cut off or a shell error | Quote it: `GEN_ARGS="--set 'REST_PROFILE=[(0,11.8),(85,6)]'"`. |
| A `WARN` row in the verify report | An advisory, not a failure. The pogo plug-magnets row always warns when the pogo connector is built, and the two USB-C metal-distance rows (per rest variant) when USB-C is built (see *Ballast and bumpers*). `--height 13`, for example, also warns that the rest's back edge is 1.2 mm higher than the switchplate. |
| `plug ... clearance to the rest` FAILs | The docked plug or its strain-relief envelope would touch the rest. Keep `PLUG_BAY_DEPTH` > 0, measure your plug and set `DOCK_CONN_W/H/D` (or `PLUG_BODY_JST`) and `PLUG_RELIEF_L/H`, and keep `PLUG_EXIT='down'` (`'rear'` has no room for the cable's turn with the default rest). |
| Ballast bars are shorter than `BALLAST_SIZE` (WARN) | An override made the default bar not fit, so the generator shortened it to stay 20 mm from the pad and keep its walls (see the `[rest]` log lines and `log` in the manifest). Buy the size the WARN row prints. |
| Rest STL over 12 MB | Raise `--mesh-edge-len` (default 0.8 mm). |
| Preview is blank or says "3D preview needs WebGL" | It needs WebGL and a network connection for three.js and the fonts. The dimension, parts and pinout panels work without either. Run `make preview` after every `generate`. |
| Module rocks in the pocket | A wire or glue blob is on the ledge; keep everything inside the 3.5 mm solder well. |
| Glass sits proud of the rim | Wrong variant: print `ithalat-glass.stl` for glass, or set `--glass-t` to the real thickness. |
| Dock is loose / too tight in the cut-outs | Adjust `DOCK_PLUG_SIZE` (default 13.85 for a 14.0 cut-out) or `DOCK_CLIP_LIP`; print in PETG. |
| Pogo receptacle loose in the dock | Raise `DOCK_CONN_RIB_H`, or measure the housing and set `DOCK_CONN_W/H/D`; glue it with CA. |
| USB-C grip is hard to plug in, or will not go fully home | Plug it in straight, without rocking it. Then check the fit: the receptacle mouth must sit flush with the floor of the well, and the grip's nose must slide into the well freely. If either fails, measure both boards, set the `USBC_*` constants and reprint ([wiring.md §7.4](../wiring.md#74-prepare-the-breakout-boards)). Clean any elephant-foot off the grip's nose. |
| USB-C dock lifts out when you unplug | Press the retainer fully home, flush with the dock top, and tighten its two screws: its two prongs lock the back clips. Unplug with a fingertip braced on the dock face beside the well, so the pull stays in your hand ([wiring.md §7.8](../wiring.md#78-plugging-and-unplugging)). |
| Pulling the rest away drags the keyboard (USB-C) | Expected: USB-C does not break away. Unplug the grip before you move the rest. |
| OLED freezes while something is plugged into the USB-C dock | A USB charger or cable is in the dock instead of the grip. Most chargers short D+ to D−, which shorts SDA to SCL. Unplug it. If the OLED stays frozen, re-plug the keyboard's USB ([wiring.md §7.9](../wiring.md#79-it-is-not-usb-labels-chargers-and-laptops)). |
| USB-C pad fails, but works with the bare male board turned over | The female board wires only one of its two D+/D− contact pairs, and the grip fits the well one way up only. Replace the female board with one that joins both pairs ([wiring.md §7.7](../wiring.md#77-test-procedure-usb-c)). |
| VDDHI reads about 3.0–3.1 V (USB-C) | Normal: the series Schottky drops a few tenths of a volt (up to about 3.25 V while the pad idles). The TPS65 runs from 1.65 V. If it equals the Pico's 3V3 exactly, the diode is shorted or bypassed ([wiring.md §7.7](../wiring.md#77-test-procedure-usb-c)). |
| Cursor moves the wrong way, or no pad after replugging | Firmware side: see the calibration and hot-plug sections in [firmware/README.md](../firmware/README.md). |
| Erratic tracking | Metal, magnets or conductive filament near the pad, a 5 V supply, or an air gap under the glass. See [wiring.md §5](../wiring.md#5-electrical-notes). Cursor drift near the back edge with the pogo plug docked: re-plug so the pad recalibrates, or raise `TP_BACK_MARGIN`. |
| Rest sits lower than the switchplate | The rest's bumpers are the keyboard's height; use bumpers 0.6 mm taller. |
