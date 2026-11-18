# ithalat reference

The deep reference for ithalat: why it is shaped this way, what the build makes, how it is checked, and every setting.

## TL;DR

- **Shape:** a crowned bar, 270.98 x 85 mm. The trackpad island is the highest point, level with the switchplate (11.8 mm).
- **Variants:** `glass` (1.1 mm overlay) or `bare` TPS65. Each one works with both connectors, magnetic pogo or USB-C.
- **Optional soft top:** a PETG base plus a TPU insert over the front 30.25 mm, the nose and the ends. Together they have exactly the rigid rest's shape ([TPU insert](#tpu-insert-optional-top)).
- **Docks:** a printed dock replaces the two centre front-row keys. No case modification.
- **Checks:** `make verify` measures the meshes. The default build passes 434 checks with 5 advisory warnings.
- **Settings:** every `config.py` constant is in the [Configuration reference](#configuration-reference). Override any of them with `--set NAME=VALUE`.
- **Stuck?** Go to [Troubleshooting](#troubleshooting).

**Jump to**

- **Understand it:** [Design rationale](#design-rationale) · [Variants](#variants) · [TPU insert](#tpu-insert-optional-top) · [The docks](#the-docks) · [USB-C dock and grip](#usb-c-dock-and-grip)
- **Build it:** [Outputs](#outputs) · [Verification](#verification) · [Configuration reference](#configuration-reference)
- **Make it:** [Printing](#printing) · [Printing the TPU top](#printing-the-tpu-top) · [Assembly order](#assembly-order) · [Ballast and bumpers](#ballast-and-bumpers) · [Glass handling](#glass-handling)
- **Fix it:** [Troubleshooting](#troubleshooting)

**Other docs**

- [README](../README.md): the overview, the connector choice and the quick start.
- [wiring.md](../wiring.md): the wiring.
- [bom.md](bom.md): the parts and costs.
- [where-to-buy.md](where-to-buy.md): example shops, prices and stock.
- [wiring-details.md](wiring-details.md): the wiring background (electrical notes, protection parts, full tests).

File names in `code`, such as `stl/ithalat-glass.stl`, are relative to the repository root.

## Design rationale

The rest is modelled on a classic walnut keyboard rest, with the trackpad level with the switchplate.

### Shape

| Part | Size | Note |
|---|---|---|
| Bar | 270.98 x 85 mm | as wide as the keyboard |
| Ends | bulge out gently by 2 mm | |
| Plan corners | R16 front, R2.8 back | back corners match the keyboard's |
| Top, at the back | 11.8 mm high | level with the switchplate |
| Top, to the crown peak | flat, up to 28 mm in | |
| Top, at the front | falls convexly to 6.5 mm | |
| Front nose | soft and elliptic, 9 x 4.5 mm | no edge under your wrists |
| Edge rounds | R5 ends, R1.2 back top edge | |
| Trackpad island | flat at 11.8 mm for 5 mm | then blends into the crown over 14 mm |

- **Smooth top:** the surface is crowned and C1-smooth, with no creases anywhere. Adjacent facets turn by at most about 5°.
- **Crease-free back corners:** next to the small back corners, the end round fades in over 24 mm (`REST_END_TAPER`).
- **Highest point:** the trackpad island, exactly `REST_HEIGHT`.

### Why these choices

- **Trackpad level with the switchplate**
  - `REST_HEIGHT` defaults to `KEYBOARD_HEIGHT` (11.8 mm, caliper-measured).
  - Your thumbs slide from the front row onto the pad without a step.
  - The rest's back edge meets the keyboard at the same height, so nothing catches.
- **Lower at the front**
  - The 6.5 mm front edge and the nose keep the wrists in a neutral, slightly lowered position, as on wooden rests.
  - A rest that is flat at keyboard height pushes the wrists up.
- **Pad on the centre line, close to the keys**
  - The module is centred on the keyboard's centre line (X 135.49).
  - Its back edge is 9 mm from the rest's back.
  - It is within thumb reach of the home row and away from the wrists.
- **Top-loaded stepped pocket**
  - The module drops in from the top onto a flat ledge.
  - Its surface sits 0.15 mm below the rim, so the glass edges never take a knock.
  - Two push-out holes from below remove it without touching the components.
  - No glue, no screws: the TPS65 has no mounting holes.
- **Separate, pluggable rest**
  - The rest is not fixed to the keyboard, so you can move or store it.
  - With the magnetic pogo connector it also breaks away if the cable snags.
  - The USB-C connector does not break away, so you unplug it first.
  - The cable leaves at the top of the back face, so it is never pinched between the rest and the keyboard.
- **Dock in place of two keys, no case modification**
  - The two centre front-row keys (Scroll Lock and right click in the stock keymap) sit right in front of the OLED/Pico block.
  - A printed dock clips into their switch cut-outs. It needs no drilling, filing or PCB change, and you can remove it again.
  - Its wires come from the OLED header, the switchplate TB1 socket or the Pico pins.
  - The wires lie flat on the switchplate under the OLED cover. Only the cover comes off.
- **Shared I2C bus**
  - QMK supports one I2C peripheral.
  - The TPS65 (0x74) shares the OLED's bus (0x3C) on GP2/GP3.
  - It is a 3.3 V part, so it is powered from 3V3(OUT).
- **Ballast**
  - A printed rest of about 130 g slides around.
  - Two steel bars (about 122 g) in the wrist wings fix that.
  - They stay at least 20 mm from the pad, because metal near a capacitive sensor disturbs it.

> [!WARNING]
> The TPS65 is a 3.3 V part. Power it from 3V3(OUT), never 5 V.

## Outputs

- **Committed:** the STLs and `preview/index.html` always match the default config.
- **Scratch:** `build/` is scratch.

### Files

| File | What it is | Size |
|---|---|---|
| `stl/ithalat-glass.stl` | rest for the TPS65 **with** the 1.1 mm glass overlay, both connectors | ~5.2 MB |
| `stl/ithalat-bare.stl` | rest for the **bare** TPS65, no glass, both connectors | ~5.2 MB |
| `stl/ithalat-glass-tpu-base.stl` | TPU top only: the glass rest's rigid base, with the tray floor and 4 pegs | ~3.8 MB |
| `stl/ithalat-bare-tpu-base.stl` | TPU top only: the bare rest's rigid base, with the tray floor and 4 pegs | ~3.8 MB |
| `stl/ithalat-tpu-insert.stl` | TPU top only: the soft insert, the same for both variants | ~1.6 MB |
| `stl/ithalat-dock-pogo.stl` | keyboard dock for the magnetic pogo connector | ~0.1 MB |
| `stl/ithalat-dock-usbc.stl` | keyboard dock for the USB-C female board | ~0.1 MB |
| `stl/ithalat-usbc-grip-top.stl`, `stl/ithalat-usbc-grip-bottom.stl` | the two clamshell halves of the USB-C grip around the male board | |
| `stl/ithalat-usbc-retainer.stl` | USB-C board retainer (details below) | |
| `stl/ithalat-dock-jst.stl` | JST-SH (Qwiic) dock, only written when `jst_sh4` is selected | |
| `preview/index.html` | interactive 3D preview (details below) | |
| `build/manifest.json` | dimensions, part placement matrices, cable path, stats (consumed by the preview) | |
| `build/artifact.html` | the same preview as an HTML fragment for publishing (scratch, git-ignored) | |

- **Print orientation:** both docks, both grip halves and the retainer are already in print orientation.
- **TPU files:** written only while `TPU_ENABLED` is True. `generate.py` deletes them when you turn it off.
- **Retainer** (`stl/ithalat-usbc-retainer.stl`): screwed down with 2 x M2x4. It:
  - holds the female board down in the dock;
  - presses the receptacle shell onto the board;
  - closes the shoulder window;
  - covers the Schottky diode;
  - locks the dock's back clips with its two prongs. There is no separate lock part.
- **Preview** (`preview/index.html`):
  - shows the glass/bare variants, the two connectors, filament colours, explode, section cut, x-ray, underside view, dimensions, parts with masses, pinout and print notes;
  - lists the STLs for the picked variant and connector under *Download STLs*: one link per file, plus *Download all* (a .zip made in the browser with JSZip from cdnjs);
  - is one file. It loads three.js and the fonts from a CDN, so it needs a network connection.

### Frames and orientation

- **Rest STLs:** exported in the assembly frame, which is also their print orientation (bottom on the bed). The two TPU bases are exported the same way.
- **TPU insert STL:** also in the assembly frame (z 3.0–11.8), so it loads aligned with a base. Loaded alone, the slicer drops it onto its flat underside.
- **The assembly frame:**
  - origin at the rest's front-left-bottom corner;
  - +X to the right;
  - +Y toward the keyboard;
  - +Z up.
- **Docks and USB-C parts:** exported in their print orientations (the docks upside down).
- **Placement in the manifest:** for every part, the manifest gives a 4x4 matrix (three.js `Matrix4.elements` order) that places it in the assembly.
- **Connector in the manifest:** each part also lists the connector it belongs to (`connector`: `pogo`, `usbc` or none for the rests).
- **Top in the manifest:** each part has a `top` key: `rigid` for the two rests, `tpu` for the two TPU bases and the insert (role `insert`), none for the docks and USB-C parts. With `TPU_ENABLED`, the manifest also has `tops` (the preview's Top switch) and a `tpu` block with the floor, depth, collar, pegs, thicknesses and mass.

## Verification

- **Command:** `make verify` (`tools/verify.py`).
- **Method:** it measures the meshes themselves, using ray casts, slices, point-in-solid tests and signed distances.
- **Default build:** passes 434 checks with 5 advisory warnings (the pogo plug magnets and the USB-C metal distances, below).
- **Rigid build only:** with `--set TPU_ENABLED=False` it runs the 365 checks of the rigid parts, unchanged.
- **Count changes with the config:** rows for absent features are skipped (for example 424 with `--set TPU_PEGS=[]`, 410 with `--no-ballast`).
- **TPU top skipped:** a rest override that leaves no room for a sound insert, with no `TPU_*` setting (for example `--set REST_FRONT_HEIGHT=5`), skips the TPU rows with one WARN, just as `generate` skips the TPU STLs.
- **Failure:** it exits 1 on any failure.

### What it checks

| Area | In short |
|---|---|
| Mesh | watertight, positive volume, STL ≤ 12 MB |
| Size | bounding box, max Z, top-surface smoothness |
| Pocket | opening, rim, ledge, depth, relief, solder well, push holes, floor |
| Cable | open path, swept cable clearance, tunnel, riser, notch |
| Plug | plug bay, plug clearance to the rest |
| Underside | bumper recesses, ballast, engraving |
| Docks | watertight, plugs, body fit, connector face, STL matches the build |
| USB-C parts | dock, retainer, grip, clearances, retention, printability |
| TPU base | mesh, bounding box, flat tray floor, floor over the recesses, pegs, ballast wall, no new overhang |
| TPU insert | mesh, bounds, pocket clearance, thickness, front edge angle, prints without supports, bed chamfer, peg holes |
| TPU split | base + insert = the rigid rest minus only the designed fit slack, no overlap, flush seams |
| Assembly | manifest, part placement, cable route |

<details><summary>Full list of checks</summary>

- **Mesh:** watertight and winding-consistent, positive volume, STL ≤ 12 MB.
- **Size:**
  - bounding box = width/depth/height within ±0.05 mm;
  - max Z == `REST_HEIGHT`;
  - top-surface smoothness (max facet angle).
- **Pocket:**
  - opening size, position and corner radius (`POCKET_CORNER_R`), and that the module and the glass, with their own corner radii, fit the opening;
  - rim height at the pocket wall ≥ glass/film top + 0.05 mm, so a sideways knock meets the wall;
  - ledge Z at six points around the module;
  - pocket depth per variant, and glass/PCB top = rim − `TP_SURFACE_RECESS`;
  - the relief covers the component box + 1 mm;
  - solder well under all 6 pads and the ZIF;
  - push holes open;
  - floor ≥ 2.0 mm under every pocket and channel.
- **Cable:**
  - open path well → tunnel → riser → notch;
  - a `CABLE_D` cable swept along groove, tunnel and riser clears the walls;
  - tunnel skin ≥ 1.6 mm and height ≥ cable Ø;
  - riser → notch passage at least the channel width;
  - notch floor and width on the back face;
  - back face closed below the notch.
- **Plug:**
  - plug bay floor, width and length;
  - the docked plug's housing and its strain-relief envelope (`PLUG_RELIEF_*`) clear the rest by ≥ `PLUG_MIN_CLEARANCE` (0.5 mm);
  - with `PLUG_EXIT='down'`, the loose wires drop into the riser.
- **Underside:**
  - bumper recess depths;
  - ballast depth, top skin ≥ 3 mm, wall ≥ 3 mm at the bed, plan distance ≥ 20 mm from the pad, and bar = `BALLAST_SIZE`;
  - engraving depth.
- **Docks** (one per connector):
  - watertight;
  - each plug < the 14 mm switch cut-out inside the plate thickness;
  - plugs on the removed switch centres and `DOCK_PLUG_DEPTH` deep;
  - body covers both cut-outs, keeps the front setback and ≥ 0.5 mm to the neighbouring key cells;
  - connector face flush and the pocket open;
  - the STL matches the build.
- **USB-C parts, the dock:**
  - the well: width, height, depth, 45° entry chamfer, bottom-wall sag allowance;
  - shoulder wall, window clearance and the window's crush ribs on the receptacle;
  - receptacle mouth flush with the well floor (±`USBC_MOUTH_TOL`);
  - board pocket, rim and rear stop;
  - 30° catches on the back-wall blades;
  - finger-brace flats either side of the well;
  - the taller dock below the keycap tops (`KEYCAP_TOP_Z`) and clear of the OLED cover.
- **USB-C parts, the retainer:**
  - presses the board rim and, with its ribs, the receptacle shell;
  - closes the window;
  - its screws' pilot holes and thread length;
  - its hold-down margin against the upward share of the pull;
  - its lock prongs slide in behind the back blades, are backed at the lip by the backing rib, and keep ≥ 0.15 mm of lip engagement.
- **USB-C parts, the grip:**
  - nose walls;
  - nose clearance in the well, and the tilt before the nose bears on the wall;
  - nose stopping short of the floor;
  - push rib, side and rear walls;
  - wire band over the rib and at the slot;
  - screw thread length and peg walls;
  - the board clamp: crush-rib height, ceiling, and the interference left after rounding both faces to `USBC_PRINT_LAYER`;
  - the shell collar and the epoxy key groove.
- **USB-C parts, clearances:**
  - no printed material inside any hardware box (both boards, both shells, the diode);
  - the grip clear of the dock and the retainer;
  - the grip floating above the rest, mated and withdrawn (`USBC_WITHDRAW`);
  - the grip's rear clear of the trackpad pocket, and its wire exit above the riser;
  - wire slack ≥ the plug's travel out of the well.
- **USB-C parts, strength and printing:**
  - dock retention margins: pull with and without the retainer, and push;
  - widest bridge and steepest overhang of each USB-C part in print orientation.
- **TPU base** (per variant, `stl/ithalat-<variant>-tpu-base.stl`):
  - STL size, watertight, winding, positive volume, one body;
  - bounding box = the rigid rest's;
  - tray floor flat at `TPU_FLOOR_Z` (422 rays);
  - floor over the front bumper recesses and the bottom engraving ≥ `MIN_FLOOR` (2.4 mm by default);
  - peg count and position, peg tops at `TPU_FLOOR_Z + TPU_PEG_H`, peg diameter;
  - rigid wall between the insert and each ballast pocket ≥ `TPU_BALLAST_GAP`;
  - no new overhang: the same downward-facing area as the rigid rest (44.791 cm²).
- **TPU insert** (`stl/ithalat-tpu-insert.stl`):
  - STL size, watertight, winding, positive volume, one body;
  - flat underside at `TPU_FLOOR_Z`, top at `REST_HEIGHT`, back edge at the insert depth;
  - clear of the trackpad pocket by `TPU_POCKET_COLLAR`;
  - with `ENGRAVE_FACE='top'`: clear of the text by `TPU_TEXT_KEEPOUT`;
  - TPU thickness inside the edge round-overs ≥ `TPU_MIN_T` (1080 rays), plus two rows at the nose crest;
  - front edge angle ≥ `TPU_MIN_EDGE_ANGLE`, computed and measured on the mesh (the mesh row allows 5° for faceting);
  - prints alone without supports: no downward faces besides the bed face, the 45° bed chamfers and the peg-hole roofs;
  - bed chamfer `TPU_BED_CHAMFER` along the seams and round the hole mouths (9 rays);
  - peg-hole roof bridges ≤ Ø4, hole Ø = `TPU_PEG_D` + 2 × `TPU_PEG_CLEARANCE`, hole depth = `TPU_PEG_H` + `TPU_PEG_HEADROOM`, TPU over the holes ≥ `TPU_PEG_MIN_COVER`.
- **TPU split** (per variant, base + insert):
  - no overlap;
  - (base + insert) adds nothing to the rigid rest (≤ 0.002 cm³);
  - what it lacks lies only in the bed-chamfer strip and the peg holes. This carries every rigid-rest check (pocket, cable, plug, ballast) over to the TPU build;
  - that relief volume = the designed one (0.059 cm³ by default);
  - the insert's bed face = the tray floor minus the chamfer strips and hole mouths;
  - flush back seam and collar seams.
- **Assembly** (`build/manifest.json`):
  - manifest built with the same config (the TPU settings included);
  - with `TPU_ENABLED`: `tops`, the rests tagged `rigid`, the TPU parts listed with their STLs, and the `tpu` block equal to the generator's values (or, when the TPU top is skipped, no `tops` and no TPU parts);
  - all parts and STLs present;
  - keyboard origin;
  - dock matrix = placement × inverse print transform;
  - placed dock behind the keyboard front edge and clear of the OLED cover;
  - connector face;
  - per variant, the cable starts at the TPS65 pads, leaves through the notch, its sleeve starts at the groove's end, and it ends at the dock connector face (USB-C: at the male pads in the grip);
  - the route (plus the USB-C slack) fits the pigtail length.

</details>

### Advisories (WARN, never fail)

- **Short ballast bar:** a ballast bar was shortened below `BALLAST_SIZE`. This happens only when an override makes it not fit.
- **Pogo plug magnets:** the docked pogo plug's two magnets are closer to the pad than `TP_METAL_KEEPOUT` (15 mm).
  - This always warns when the pogo connector is built: they sit about 7.35 mm from the module outline.
  - It is accepted because they do not move while the pad is powered, and the controller calibrates at power-up.
  - Check for drift at the first power-up (see the [drift check](wiring-details.md#first-power-up)).
- **USB-C metal:** with USB-C, the plug shell (about 13 mm) and the male board's copper pads (about 5.5 mm) are closer to the pad than `TP_METAL_KEEPOUT`.
  - It is reported once per rest variant.
  - Neither is magnetic, and both are fixed in place while the pad is powered.
- **Back edge height:** the rest's back edge is level with the switchplate. It warns on purpose with `--height 13`, for example.

## Variants

| Variant | Pocket depth (default) | Stack in the pocket, bottom → top |
|---|---|---|
| `glass` | 2.38 mm | ledge · PCB 1.0 · adhesive 0.13 · glass 1.1 → glass top 0.15 mm below the rim |
| `bare` | 1.28 mm | ledge · PCB 1.0 · adhesive/liner 0.13 → top 0.15 mm below the rim |

- **Shared geometry:** both variants share the rest of the geometry.
- **Add your own:** one STL is written per `VARIANTS` entry. For example: `--set "VARIANTS={'glass07': 0.7, 'film': 0.2}"`.
- **Connector is separate:** the connector is a second, separate choice ([Pick your connector](../README.md#pick-your-connector)).
- **Any combination works:** every rest variant works with every connector, and the preview shows each variant × connector combination.

### Pocket layout

The pocket, top to bottom:

| Layer | Size | Notes |
|---|---|---|
| 1. Opening | 65.5 x 49.5 mm, R2.5 corners | 0.25 mm clearance per side (`POCKET_CORNER_R` sets the corners) |
| 2. Support ledge | flat, at least 2 mm wide all around | in fact it covers the module's whole component-free back |
| 3. Component relief | 1.6 mm deep | under the component box + 1 mm |
| 4. Solder well | 3.5 mm deep | under the six solder pads and the ZIF connector, next to the long edge that faces the keyboard |
| 5. Push-out holes | two Ø6 holes through the floor | under the flat front area of the module |

- **Corner fit:** the module and the glass have corners of about R4, which leaves a 0.97 mm gap at each corner. Any part corner of R1.65 or more fits.
- **Measure your glass:** the glass corner radius is not published, so check yours with a caliper or radius gauge.
- **Rim bevel:** 0.4 mm wide and 0.08 mm high (`POCKET_RIM_CHAMFER`, `POCKET_RIM_CHAMFER_H`). The vertical pocket wall still rises 0.07 mm above the glass or film top.
- **Push-out:** push the module out from below with a pen. You never touch the components.

### Cable route

The pigtail runs from the TPS65 pads to the dock, in this order:

1. **S-bend groove:** the cable's sleeve is clamped in an S-bend groove in the well floor (strain relief).
2. **Tunnel:** 4.5 x 4 mm, 1.6 mm under the ledge and the back rim. The tunnel floor is at 3.82 mm on the glass variant, so a 3.5 mm cable fits with 1.6 mm of material above it.
3. **Riser:** the last 15 mm are loose wires (`CABLE_PLUG_LOOSE_LEN`). They rise through the riser.
4. **Notch:** a 6 x 4 mm U-notch in the back-top edge, on the centre line.
5. **Plug:** the wires turn straight back into the pigtail's plug (`PLUG_EXIT='down'`).

- **Plug bay:** the plug hangs on the dock face over a 26 x 7 x 2 mm recess in the back-top edge (`PLUG_BAY_*`, floor at z 9.8).
- **Plug clearance:** the plug housing clears the rest by 3.1 mm.
- **Relief clearance:** the 3 x 6 mm envelope behind the housing, for the solder tails, heat-shrink and glue (`PLUG_RELIEF_L/H`), clears the rest by 2.2 mm.
- **Length:** the whole route from the pads to the dock face is about 52 mm.
- **Never pinched:** the cable is never pinched between the rest and the keyboard.
- **Printable:** every overhang is either open to the top or a 4.5 mm bridge.

**With the USB-C connector:**

- **Same route up to the notch.**
- **Into the grip:** the four loose wires rise straight up into the grip's underside. Its wire slot sits right above the riser.
- **Slack loop:** a 12 mm slack S-loop (`USBC_WIRE_SLACK`) is stored in the plug bay. It lets you pull the grip back the 10.65 mm it takes for the plug to clear the well.
- **Float:** the plugged grip floats about 1.6 mm above the rest (1.25 mm when pulled back 7.5 mm), so wrist movement never pushes on it.

## TPU insert (optional top)

A second, optional top: a rigid base plus a soft TPU insert over the front of the rest, where wrists and palms land (`geometry/tpu.py`).

- **Files:** `stl/ithalat-<variant>-tpu-base.stl` (PETG or PLA) plus `stl/ithalat-tpu-insert.stl` (TPU), *instead of* `stl/ithalat-<variant>.stl`.
- **Same shape:** base + insert has the rigid rest's outside, its 11.8 mm back and its pocket with the pad 0.15 mm below the rim. The only difference is hidden fit slack at the floor (0.059 cm³): a 0.4 mm chamfer on the insert's underside edges and peg holes 0.4 mm deeper than the pegs ([Pegs](#pegs)).
- **Some give:** 5.2–8.8 mm of TPU, firm-rubber feel, firmest at the nose. About 29 g of TPU at 10 % gyroid.
- **Front slope only:** the crown behind the insert, its highest part, stays PETG.
- **One pair of STLs, two routes:** print the insert alone and press it onto 4 pegs, or print both in one multi-material job ([Printing the TPU top](#printing-the-tpu-top)).
- **One insert for both variants:** the glass and bare bases take the same insert.
- **Turn it off:** `--set TPU_ENABLED=False` builds only the rigid parts. verify then runs the 365 rigid checks.
- **Skipped on its own:** if a rest override (for example `--set REST_FRONT_HEIGHT=5`) leaves no room for a sound insert and you set no `TPU_*` constant, `generate` logs `WARNING: TPU top skipped` and builds the rigid parts as before. With any `TPU_*` override it is a config error instead.
- **Untested in print:** the feel, the peg fit and the one-job bond. Print the [test slice](#tpu-test-slice) first.

### Why an insert

The concern: printed PETG/PLA is hard, and the gently curved crown prints as wide layer terraces. A TPU top changes the feel, but only if it is thick.

- **Thin solid TPU feels like hard rubber.** A 1.2–2.4 mm TPU skin over PETG is matte and grippy, but firm.
- **Softness needs thickness and air:** about 4 mm or more of TPU (ideally 5–8 mm) with 5–15 % gyroid under a ≥ 1.2 mm top skin. Low-density gyroid compresses smoothly, while 2D infill patterns buckle and feel harsh (Nace et al., 2021).
- **Expect a firm rubber pad, not foam:** 95A–98A is hard for a TPU. Thin TPU with walls, top and bottom skins is nearly solid, so the nose (2–5 mm of TPU) is the firmest part.
- **Only 95A–98A TPU was in stock** in the Turkish shops checked on 2026-11-18 ([where to buy](where-to-buy.md#tpu-filament-tpu-top-only)). So the softness has to come from the geometry, not from a softer filament.

| Option | Verdict | Why |
|---|---|---|
| **Flat-bottomed front insert** (this) | **chosen** | prints on any TPU printer, flat side down, no supports; one STL pair for both routes; 5–9 mm of TPU gives some cushion even in 98A |
| Thin conformal skin (1.6 mm) over the whole top | not in v1 | feels like hard rubber; printed alone it needs supports under 166 cm² of curved underside, so it is multi-material only; at most 1.88 mm at the nose |
| Flat pads printed touch side down, bent into recesses | rejected | only fits the parts of the top that unroll flat; leaves seams in the contact zone; thin, so hard rubber |
| Pause at one height and swap filament | rejected | a flat cut: TPU lands only above it (the back plateau), not at the front, and the pocket walls turn TPU |
| Whole rest in TPU | rejected | the pocket ledge gives and the pad rocks; the dock alignment suffers |
| Stick-on covers, soft-touch paint, cast silicone, a gel pad | rejected | covers add height and peel; soft-touch coatings turn sticky; platinum silicone is import-only; a gel pad is not part of the rest |

### What is TPU and what stays rigid

| Zone | Material | Detail |
|---|---|---|
| Front 30.25 mm, the nose, the front corners, the front of both ends | **TPU** | 76 cm² footprint; x 0.17–270.81, y 0.20–30.25, z 3.0–11.8. The depth is automatic: `TPU_BALLAST_GAP` (2 mm) in front of the ballast pockets |
| Trackpad pocket plus a 3 mm collar (`TPU_POCKET_COLLAR`) | rigid | rim, bevel, walls, ledge, relief, well and push holes. The seam lies on the flat island, flush at 11.8 mm. The TPU stays ≥ 3.25 mm from the module |
| Everything behind y 30.25 | rigid | ballast, cable tunnel, riser, notch, plug bay, R1.2 back edge |
| The tray floor, z 0–3.0 (`TPU_FLOOR_Z`) | rigid | every bottom feature. 2.4 mm of floor over the 3 front bumper recesses and the bottom engraving (≥ `MIN_FLOOR` 2); 2.0 mm of rigid wall to each ballast pocket |
| Top engraving (`--engrave-face top` only) | rigid | the text's bounding box + 1 mm (`TPU_TEXT_KEEPOUT`) stays rigid, and the insert goes around it. `generate` logs a NOTE |

**Thickness and edges** (default config):

| Where | Value |
|---|---|
| TPU inside the edge round-overs | 5.16–8.80 mm (verify measures ≥ 5.27 mm on 1080 rays; the limit is `TPU_MIN_T` 3) |
| On the nose (wing): y 2 / 4 / 6 / 9 mm | 2.2 / 3.5 / 4.3 / 5.0 mm |
| Nose crest (y 9) | 5.04 mm (wing), 5.16 mm (centre) |
| Front edge | a 65.9° wedge where the floor plane meets the nose (68.8° measured on the mesh), flush with the PETG nose foot below |
| Back seam (y 30.25) | vertical TPU/PETG face, flush on top. The PETG top there is 10.63 mm; the crown peaks at 11.8 mm at y 57 |
| Collar seam | vertical face, 8.8 mm tall, flush at 11.8 mm on the flat island |
| Seam bottoms | a 0.4 mm 45° chamfer on the insert's underside edge along every seam (`TPU_BED_CHAMFER`): room for elephant foot and the base's inside corner |
| Volume | 42.77 cm³ of TPU; the glass base is 171.67 cm³ (the rigid rest: 214.50) |

- **Lower floor = thicker, softer TPU,** but the floor must leave `MIN_FLOOR` over the bumper recesses (`TPU_FLOOR_Z` ≥ 2.6) and keep the front edge at 45° or more (`TPU_FLOOR_Z` ≤ 4.0).
- **Wrist contact:** the palm heel lands on the front 0–30 mm and the nose while you type, and on the nose when your hand is on the pad. This is an estimate from the keyboard geometry, not a measurement.
- **The crown stays PETG:** everything behind y 30.25, including the highest part. Under load the TPU sinks a little and the PETG edge at the seam can stand proud. For a deeper insert, see [Deeper cushion](#deeper-cushion-and-other-options).

### Pegs

- **Where:** 4 pegs on the tray floor, 2 per wing, at x 31.44 / 70.31 / 200.68 / 239.55 and y 24.2 (`TPU_PEGS = None`, auto: 0.8 × the insert depth). That is near the back of the insert, where the TPU is thickest (7.05 mm), behind the middle of the estimated palm band.
- **Shape:** Ø5 x 2.5 mm with a 0.5 mm 45° top chamfer (`TPU_PEG_D`, `TPU_PEG_H`, `TPU_PEG_CHAMFER`).
- **Holes in the insert:** Ø5 (`TPU_PEG_CLEARANCE` 0) and 2.9 mm deep: 0.4 mm deeper than the pegs are tall (`TPU_PEG_HEADROOM`). So a sagging roof bridge or a slightly tall peg cannot lift the insert.
- **Above the holes:** Ø4 roof bridges with 3.9–4.2 mm of TPU over them. A 0.4 mm 45° countersink round each mouth guides the peg in.
- **Fit:** printed TPU holes come out slightly small, so the fit is a snug press fit. In a one-job print the pegs fuse and key the two parts.
- **Locked in every direction:** the back wall stops it moving back, the collar notch and the pegs stop it moving sideways, the pegs stop it moving forward, and friction (or glue) holds it down.
- **Other layouts:** `--set TPU_PEGS=[]` for no pegs (glue only), or your own, for example `--set "TPU_PEGS=[(40,15),(230,15)]"`.

### Fit and attachment

- [ ] **Press it on:** set the base on the desk, line the insert's holes up with the pegs, and press down from the back to the front.
- [ ] **Permanent (optional):** coat the floor and the insert's underside with contact cement (polychloroprene, for example Pattex or UHU Kontakt), wait until touch-dry, then press. Test the solvent on a PETG scrap first. A flexible glue (E6000-type, or a flexible CA such as Loctite 406) also works.
- **Avoid tape under the insert:** even thin double-sided tape (about 0.1 mm) lifts it and leaves a step at every seam, including the collar beside the trackpad. Use contact cement or a flexible glue instead.
- **Avoid:** epoxy (rigid, and weak in peel on TPU: 0.2 N/mm in a TPU bonding benchmark), and plain CA on PETG.
- **To remove it:** lift the front edge with a fingernail or a spudger. There is no PETG wall at the front.
- **Fit problems:** see [Troubleshooting, TPU top](#tpu-top).

### Feel and care

- **Hardness:** 98A is about a hard skate wheel, 95A about a shopping-cart wheel. Nominal ratings run high: BASF's "TPU 95A" measures 92 Shore A.
- **Surface:** matte and grippier than PETG. Friction rises when the skin is wet, so sweaty wrists grip more. Resting is fine; sliding drags a little. 95A–98A is less tacky than 85A.
- **Give:** a little, like a firm rubber pad, not foam. Firmest at the nose, where the TPU is only 2–5 mm thick and prints nearly solid. For more give, use 2 walls and 5 % gyroid.
- **Layer lines stay:** the insert's top prints facing up. TPU softens how the steps feel; it does not remove them. Use thin layers (0.1 mm, see [Printing the TPU top](#printing-the-tpu-top)).
- **Sanding:** sanding along the curve (400 → 800, then wet from about 1000 to 1500 grit) smooths the PETG crown behind the insert and the whole rigid rest. PETG is tougher to sand than PLA; water keeps it from heating up. It does not work on TPU. Keep off the pocket rim.
- **Clean it** with mild soap and water, then dry it. A quick alcohol wipe is fine. Never soak it in alcohol, and never use acetone (it swells TPU).
- **Colour:** pick a dark or mid colour. TPU yellows slowly (UV, heat), and white or natural shows skin oil.
- **Heat and dents:** TPU's heat deflection temperature is about 50 °C, and it gets softer when warm. BASF 95A's compression set is 38 % at 23 °C but 90 % at 70 °C, so a rest left under a heavy object in a hot car can keep a dent.
- **Wear:** TPU resists abrasion far better than a PETG/PLA surface.
- **Skin contact:** none of the Turkish listings claim a skin-contact certification (ISO 10993), or say whether the TPU is polyether (resists sweat better over years) or polyester.
- **Keep the ballast:** a grippier top pushes the rest sideways harder.

> [!WARNING]
> **Non-conductive TPU only.** Azoteq says the trackpad's stack must contain no conductive material, and conductive parts close to the sensor cut its sensitivity. Carbon-filled TPU really conducts (NinjaTek Eel: 5,500 Ω/sq). Never use carbon, CF, ESD/antistatic, conductive, metal-filled or glitter TPU. Unsure about a black TPU? A multimeter on a printed scrap should read open (MΩ or more).

### Deeper cushion and other options

| Override | Insert | Note |
|---|---|---|
| default | 30.25 mm deep, 42.77 cm³ (about 29 g) | the crown (peak 11.8 mm at y 57) stays PETG; verify: 434 checks |
| `--set BALLAST_CENTER_Y=57` | 44.75 mm deep, 66.35 cm³ (about 40 g) | the bars stay 78 mm. Moves the ballast back, in the rigid rest too, so the rigid STLs change; verify: 434 checks |
| `--set BALLAST_CENTER_Y=70` | 57.75 mm deep, 88.82 cm³ (about 50 g) | reaches the crown's peak. The bars shorten to 64.5 mm (about 101 g instead of 122 g: buy that size); the rigid STLs change; verify: 430 checks, plus 4 ballast WARNs |
| `--no-ballast` | 42.5 mm deep, 62.54 cm³ | not recommended: the grippier top needs the ballast; verify: 410 checks |
| `--set REST_DEPTH=90` | 32.75 mm deep | verify: 434 checks |
| `--engrave-face top` | goes around the text | the text area stays rigid; verify: 433 checks |
| `--glass-t 0.7` | unchanged | verify: 434 checks |
| `--set REST_FRONT_HEIGHT=5` | none: skipped with a WARNING | the floor plane would cut the lower nose too thin. The rigid parts build as before (verify: 366 checks, 1 extra WARN). Add `--set TPU_FLOOR_Z=2.7` to get the insert (434 checks) |

- **Not built (owner decision):** a TPU-only ballast position, so a deeper insert leaves the rigid STLs alone, or a 45° scarf back seam, so the cushion fades out instead of ending at a step. Both would change the "base + insert = rigid rest" rule that lets verify carry the rigid checks over.

**Config errors.** A TPU setting that cannot give a sound part stops `generate` and `verify` with `config error: ...`. The message names the setting and ends with "(or --set TPU_ENABLED=False)". A rest-only override with no `TPU_*` setting is not an error: the TPU top is skipped with a WARNING (last row above).

| Override | Why it stops |
|---|---|
| `TPU_FLOOR_Z=4.5` | the front edge would be 36.8°, below `TPU_MIN_EDGE_ANGLE` (45°): keep `TPU_FLOOR_Z` ≤ 4.0 |
| `TPU_FLOOR_Z=2.0` | only 1.40 mm of floor over a bumper recess, below `MIN_FLOOR`: raise `TPU_FLOOR_Z` |
| `TPU_INSERT_DEPTH=40` | runs into the ballast pocket: keep it ≤ 30.25 |
| `TPU_POCKET_COLLAR=6` (or 1.0) | must stay between `POCKET_RIM_CHAMFER` + 1 (1.4) and `TP_BEZEL` (5), so the seam stays on the flat island |
| `TPU_INSERT_DEPTH=8` | an insert shallower than `REST_FRONT_NOSE_R` + 3 (12 mm) |
| `TPU_PEGS=[(5,15)]` | a peg outside the insert, or closer than `TPU_PEG_EDGE` to its edge |
| `TPU_PEG_H=6` | less than `TPU_PEG_MIN_COVER` (2 mm) of TPU over the peg hole |
| `TPU_PEG_H=0.8` | the 0.4 mm bed chamfer must stay below the straight part of the pegs (`TPU_PEG_H` − `TPU_PEG_CHAMFER` = 0.3) |
| `REST_FRONT_HEIGHT=5` plus any `TPU_*` setting | the floor plane would leave a feather edge at the nose (38.6°): keep `TPU_FLOOR_Z` ≤ 2.7. Without a `TPU_*` setting the TPU top is skipped instead |

<details><summary>Sources for this section</summary>

- Azoteq, [AZD008 design guidelines for touchpads](https://www.azoteq.com/images/stories/pdf/azd008_design_guidelines_for_touchpads.pdf) and [AZD061 auto-tuning article](https://www.azoteq.com/images/stories/pdf/azd061_azoteq_auto_tuning_article.pdf): no conductive overlay, conductive housings cut sensitivity.
- NinjaTek, [Eel TDS](https://ninjatek.com/wp-content/uploads/TDS_EEL-Revision1_26-06_V1.pdf): carbon-filled TPU, 5,500 Ω/sq.
- BASF, [Ultrafuse TPU 95A TDS](https://cdn.shopify.com/s/files/1/0264/8791/4555/files/Ultrafuse_TPU_95A_TDS_EN_v1.0.pdf): 92 Shore A, abrasion, compression set, drying.
- UltiMaker, [TPU 95A TDS](https://um-support-files.ultimaker.com/materials/2.85mm/tds/TPU-95A/TDS-TPU95A-V2.01-250915.pdf): HDT about 50 °C, chemical resistance.
- Nace et al., [compression of TPU printed in four infill patterns for comfort applications](https://emerald.com/insight/content/doi/10.1108/RPJ-07-2020-0155/full/html), Rapid Prototyping Journal 27(11), 2021.
- Printed TPU friction, higher wet than dry: [Friction (Springer), 2020](https://link.springer.com/article/10.1007/s40544-020-0472-2).
- TPU bonding benchmark (CA + primer, epoxy, MMA): [Weerasinghe et al., Scientific Reports, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12824215/).
- Polyether vs polyester TPU: [Wikipedia, Thermoplastic polyurethane](https://en.wikipedia.org/wiki/Thermoplastic_polyurethane).
- Sanding prints: [Prusa blog, post-processing step by step](https://blog.prusa3d.com/postprocessing-of-3d-prints-step-by-step_29270/) (coarse to fine grit, dry or wet) and [3D Insider, PETG post-processing](https://3dinsider.com/petg-post-processing) (PETG is ductile and harder to sand; wet-sand from about 1000 grit).
- Printer support for soft TPU: see [Printing the TPU top](#printing-the-tpu-top).

</details>

## The docks

- **One dock per connector** (`geometry/dock.py`).
- **Same mount for all:** every dock replaces SW44/SW43 (front row, columns 6 and 7) and clips into their switch cut-outs in the same way.
- **Order here:** the pogo dock (`stl/ithalat-dock-pogo.stl`) first, then the USB-C dock and its grip.

### Pogo dock

A rounded block, 36.6 x 19 x 7 mm, that sits on the switchplate.

- **Dock plugs:** two hollow 13.85 mm plugs drop 3.4 mm into the empty 14 mm switch cut-outs. In the dock sections, "plug" means these two stubs, not the pogo plug or the USB-C plug.
- **Snap clips:** four thin blades with 0.45 mm lips catch under the 1.2 mm switchplate, like MX switches.
  - Blades: 0.8 mm thick, free length 6.35 mm, about 1.1 % bend strain.
  - The catch faces are 45°, so a firm pull (about 20 N) takes the dock out without opening the case.
  - `--set DOCK_CLIP_CATCH_DEG=0` gives a flat, permanent catch.
- **Connector pocket:** the keyboard half of the pogo pair is press-fitted into the front face (crush ribs, stop ledge), facing the rest, 3.2 mm above the plate.
  - Pin 1 (SDA) is at the typist's left. A triangle on the top face marks it.
  - Add a drop of CA glue: the magnets pull the connector outward on every unplug.
- **Wire paths:**
  - **Recommended:** a 3 x 2.8 mm open-bottom channel runs out of the back at plate level, under the OLED cover's front edge, to the OLED header, the switchplate TB1 socket or the Pico. It needs no case modification.
  - **Optional:** a 5 mm hole drops into each plug, for an adapter board under the plate.
  - **Blocked:** an acrylic bar blocks the route from the OLED header to the dock *under* the switchplate. Going that way means filing a notch in it (see [wiring-details.md, Where wires can and cannot run](wiring-details.md#where-wires-can-and-cannot-run)).
- **Fit:**
  - The front face is 0.6 mm behind the keyboard front edge.
  - The body covers both cut-outs.
  - It keeps 0.75 mm to the neighbouring key cells and 2.5 mm to the OLED cover.
- **JST option:** `--connector jst_sh4` (or the old `DOCK_CONN_TYPE='jst_sh4'`) builds `stl/ithalat-dock-jst.stl`.
  - It has a bare JST SM04B-SRSS-TB header in place of the pogo pocket.
  - Pinout: Qwiic / STEMMA QT (GND, 3V3, SDA, SCL).
  - The header's tab sizes are estimates. Check them against the part.

### USB-C dock and grip

- **Higher forces:** USB-C needs a 5–20 N push to plug in and an 8–20 N pull to unplug. The magnetic pogo needs only a few newtons.
- **Force path:** the USB-C parts route that force through printed plastic. It never passes through the wire solder joints.
- **Connector joints:** the printed parts keep the force off the connectors' own mounting joints as far as they can. The receptacle still hangs on its shell legs and the plug on its straddle tails, as in any USB-C device.
- **Layout:** the parts follow the "well" layout from the design study.
- **Same rest:** the USB-C parts use the same rest, notch, riser and tunnel as the pogo.

> [!IMPORTANT]
> **Measure your boards.** Every board dimension is a `USBC_*` constant in `config.py`, marked "measure your boards". Cheap boards vary by seller, so measure yours with calipers and regenerate before you print (see [wiring.md, Step 2b](../wiring.md#step-2b-usb-c-dock), Part A, and [Preparing the breakout boards](wiring-details.md#preparing-the-breakout-boards)).

- **Male board length:** boards from 16.0 to 17.1 mm long build and verify.
- **Short male boards:** below about 16.4 mm the grip has no room for its pegs. verify warns, and the push rib still aligns the halves.

#### The USB-C dock

`stl/ithalat-dock-usbc.stl` has the same plugs, clips and rear wire channel as the pogo dock, with these changes.

- **Well:**
  - The female board's receptacle mouth sits flush with the floor of a 4.45 mm deep, 11.64 x 5.95 mm well in the dock face, with a 1 mm × 45° entry chamfer.
  - The grip's nose goes into the well with 0.15 mm clearance per side. So after about 2.7° of tilt the well walls take side loads, instead of the plug shell.
  - The well's bottom wall prints as a bridge, so it sits 0.15 mm lower (`USBC_BRIDGE_SAG`).
  - The depth is automatic (`USBC_WELL_DEPTH = None`): as deep as your female board leaves the 1.2 mm rear stop, between 3.5 and 4.45 mm.
  - The well keeps the plugged male board short, so the grip stays 1.95 mm clear of the trackpad pocket. The pocket starts 9 mm in front of the rest's back face.
- **Board capture:**
  - The female board drops in from the top.
  - Its front edge bears on a 1.5 mm printed shoulder: a front wall with a 9.24 x 3.71 mm window, just larger than the receptacle shell.
  - Two vertical crush ribs in the window grip the shell sides (0.1 mm).
  - The shoulder takes the unplug pull.
  - The board's rear edge sits against a 1.25 mm rear stop, which takes the plug-in push.
- **Retainer** (`stl/ithalat-usbc-retainer.stl`):
  - It drops in from the top until it is flush with the dock top, and two M2x4 self-tapping screws hold it.
  - It holds the board down by its rim and closes the window over the shell.
  - Three half-round ribs press the receptacle shell onto the board (0.1 mm). A plug that is levered up or down then bears on plastic instead of on the shell's legs.
  - Glue or crush ribs alone would not survive the unplug force.
- **Diode cradle:**
  - The 1N5817/1N5819 Schottky (DO-41, 5.2 x Ø2.7 mm) lies across the female board, between the receptacle's legs and the pads, in a cradle under the retainer.
  - For a SOT-23 BAT54, set `USBC_DIODE=(3.0, 1.4)`.
  - If a diode does not fit the cradle, the dimension row says so, and it goes inline at the tap.
- **Taller and deeper body:**
  - 36.6 x 20.9 x 9 mm with R0.6 edges (pogo: 36.6 x 19 x 7 mm).
  - The connector axis is 4.25 mm above the plate (pogo: 3.2 mm), so the plugged grip floats above the rest.
  - The body stays 4.2 mm below the keycap tops (`KEYCAP_TOP_Z`, an estimate) and 0.6 mm in front of the OLED cover.
  - Its top is 0.2 mm below the cover's underside, so it still seats if your cover's front edge sits further forward than the drawing says.
- **Stronger hold:**
  - The catch faces are flatter, 30° from horizontal (`USBC_CLIP_CATCH_DEG`), so they hold harder.
  - The retainer's two prongs lock the back clips (numbers below).
  - **To take the dock out:** undo the two retainer screws and lever the retainer up at its two pry notches first.
- **Finger-brace flats:** on the dock face, beside the well. To unplug, brace a fingertip there and pull the grip. The force then stays inside your hand.

<details><summary>Dock hold: why and the numbers</summary>

- A 20 N pull a few millimetres above the plate tips the dock about its front edge and loads the two rear clips.
- The pogo dock's 45° catches would let go at about 2.5 N per clip in PETG.
- The USB-C dock's 30° catches alone hold that pull with a margin of 1.65 (3.57 N needed per back clip, 5.88 N available in PETG).
- Its back clips sit on the plugs' back walls.
- The retainer's two prongs slide in behind them, backed by a rib below the plate.
- So the clips cannot bend while the retainer is fitted (margin 16: the lips would have to shear).

</details>

#### The grip

`stl/ithalat-usbc-grip-top.stl` + `stl/ithalat-usbc-grip-bottom.stl` form a clamshell around the male board.

- **Body:** an 18 x 13.3 x 6.5 mm clamshell, split at the male board, aligned by two pegs and closed by two M2x4 self-tapping pan-head screws from below.
- **Nose:**
  - It fits the well with 0.15 mm clearance per side and a 1 mm × 45° chamfer, which catches the nose within about ±1 mm.
  - With the plug fully seated (6.2 mm), the nose stops 0.3 mm short of the well floor.
  - The nose is not symmetric top to bottom, so the grip goes in one way up only.
- **Pull path:** the pull goes into the plug shell, not the board.
  - The shell is bedded in 2-part epoxy in a key groove around it inside the nose, so pulling the grip pulls the shell directly.
  - The board is also clamped: two half-round crush ribs per side under its edge strips (0.3 mm, still 0.2 mm after the slicer rounds both faces to 0.2 mm layers).
  - A collar in front of the board stops its front corners.
  - A push rib behind the board takes the plug-in push.
- **Wire clamp:**
  - The wires are pinched over the push rib and again in a slot behind it, so pulling on them never loads the solder joints.
  - Over the rib the band is as wide as the pad row. The slot then narrows to 4.2 mm.
  - The wires leave through the grip's underside, straight above the rest's notch and riser.
- **Finger ridges:** on the sides, to give you something to hold.

## Configuration reference

**How to read this.** This is every constant in `config.py`, grouped as in the file.

- **One block per group:** open a group to see its table.
- **One row per constant:** its name, its default, and what it means.
- **Units:** all values are in mm unless noted.
- **Overrides:** `--set NAME=VALUE` overrides any of them.
- **Derived rows:** rows marked *(derived: recomputed after overrides)* are computed from other constants, and they are recomputed after your overrides.

**The frames** (described in the `config.py` docstring):

- **Assembly frame:** the rest, as in [Outputs](#outputs).
- **Keyboard-local frame:** origin at the keyboard's front-left-bottom corner, top view.
- **TPS65 front view:** x from the module's left edge looking at the touch side, y from the long edge with the connector.
- **Dock-local frame:** origin midway between the two removed switch centres on the switchplate top (see `geometry/dock.py`).

**Groups** (336 constants):

| Group | Count | Covers |
|---|---|---|
| [Keyboard](#keyboard) | 19 | outline, layers, key grid, OLED cover, Pico |
| [Wrist-rest body](#wrist-rest-body) | 20 | size, heights, profile, edge rounds, mesh |
| [Trackpad: Azoteq TPS65](#trackpad-azoteq-tps65) | 22 | module, pads, placement, keep-out, bezel |
| [Glass overlay](#glass-overlay) | 7 | thickness, outline, variants |
| [Stepped pocket](#stepped-pocket) | 12 | ledge, relief, well, rim, push holes |
| [Cable](#cable) | 18 | tunnel, notch, riser, S-bend, wires |
| [Pigtail plug and plug bay](#pigtail-plug-and-plug-bay) | 14 | plug body, relief, exit, bay |
| [Engraving](#engraving) | 8 | text, face, depth, font |
| [Underside: bumpers and ballast](#underside-bumpers-and-ballast) | 15 | bumpers, ballast bars |
| [Material and mass estimate](#material-and-mass-estimate) | 3 | density, shell, STL size |
| [TPU insert](#tpu-insert) | 17 | on/off, floor, depth, collar, pegs, limits, TPU mass |
| [Connector variants](#connector-variants) | 3 | which connectors, ids, labels |
| [Keyboard dock](#keyboard-dock) | 23 | cut-out, plugs, body, housing, pinout |
| [Keyboard dock internals](#keyboard-dock-internals) | 38 | clips, connector pocket, cavity, JST |
| [USB-C variant](#usb-c-variant) | 111 | boards, diode, well, retainer, grip |
| [Dock retention](#dock-retention) | 6 | clip model, design pull, margin |

### Keyboard

Yakamoz, verified from the KiCad/DXF files + caliper measurements.

<details><summary>Keyboard: 19 constants (outline, layers, key grid, OLED cover, keycap tops, Pico, bumpers)</summary>

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

</details>

### Wrist-rest body

Ergonomics first: crowned bar, generously rounded edges.

<details><summary>Wrist-rest body: 20 constants (size, heights, profile, nose, edge rounds, corners, mesh)</summary>

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

</details>

### Trackpad: Azoteq TPS65

From datasheet v1.06 + photo measurements.

<details><summary>Trackpad: 22 constants (module size, pads, ZIF, placement, margins, metal keep-out, bezel)</summary>

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

</details>

### Glass overlay

keycapsss: 65 x 49 x 1.1, black, no adhesive.

<details><summary>Glass overlay: 7 constants (thickness, outline, corner, density, variants)</summary>

| Name | Default | Meaning |
|---|---|---|
| `GLASS_T` | `1.1` | glass overlay thickness (--glass-t); 0.5..3 mm supported by the TPS65 |
| `GLASS_WIDTH` | `65` | glass outline (same as the module) |
| `GLASS_DEPTH` | `49` | glass outline |
| `GLASS_CORNER_R` | `4` | glass corner radius (not published - measure it); the pocket corner POCKET_CORNER_R is checked against it |
| `GLASS_DENSITY` | `2.5` | g/cm3 (mass estimate only) |
| `VARIANTS` | `{'glass': 1.1, 'bare': 0.0}` | id -> glass thickness, one STL each *(derived: recomputed after overrides)* |
| `VARIANT_LABELS` | `{'glass': 'With glass', 'bare': 'Without glass'}` | preview tab labels |

</details>

### Stepped pocket

<details><summary>Stepped pocket: 12 constants (ledge, relief, solder well, corners, rim bevel, push holes, floor)</summary>

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

</details>

### Cable

5-core pigtail from the TPS65 pads to the dock.

<details><summary>Cable: 18 constants (diameter, tunnel, notch, riser, S-bend, loose wires, colours, pigtail length)</summary>

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

</details>

### Pigtail plug and plug bay

The cable half of the connector, and the plug bay in the rest.

<details><summary>Pigtail plug and plug bay: 14 constants (plug body, strain relief, exit, clearance, bay)</summary>

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

</details>

### Engraving

<details><summary>Engraving: 8 constants (text, face, depth, height, font, placement)</summary>

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

</details>

### Underside: bumpers and ballast

<details><summary>Underside: 15 constants (bumpers, ballast bar size and placement rules, steel density)</summary>

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

</details>

### Material and mass estimate

<details><summary>Material and mass: 3 constants (PLA density, shell thickness, STL size limit)</summary>

| Name | Default | Meaning |
|---|---|---|
| `PLA_DENSITY` | `1.24` | g/cm3 |
| `MASS_SHELL_T` | `1.2` | avg solid shell (perimeters + top/bottom) for the infill mass approximation |
| `STL_MAX_MB` | `12` | verify: max size of a rest STL |

</details>

### TPU insert

Optional second "Top" (`geometry/tpu.py`). A flat-bottomed soft TPU insert replaces the front of the rest: base + insert has exactly the rigid rest's shape, with a little hidden fit slack at the floor. See [TPU insert (optional top)](#tpu-insert-optional-top).

<details><summary>TPU insert: 20 constants (on/off, labels, floor, depth, collar, text keep-out, limits, pegs and their fit slack, TPU density and mass)</summary>

| Name | Default | Meaning |
|---|---|---|
| `TPU_ENABLED` | `True` | also write `stl/ithalat-<variant>-tpu-base.stl` + `stl/ithalat-tpu-insert.stl`. If another override leaves no room for a sound insert and no TPU_* constant was set, generate / verify skip the TPU top with a WARNING (rigid parts only); with any TPU_* override it is a config error |
| `TPU_TOP_LABELS` | `{'rigid': 'Rigid', 'tpu': 'TPU insert'}` | preview "Top" switch / manifest labels |
| `TPU_FLOOR_Z` | `3` | tray floor = the insert's flat underside (z above the bed). Must leave MIN_FLOOR over every underside recess below the insert (bumpers and bottom engraving, 0.6 deep -> >= 2.6) and keep the front edge at least TPU_MIN_EDGE_ANGLE (-> <= ~4.0). Lower = thicker, softer TPU |
| `TPU_INSERT_DEPTH` | `None` | insert back edge, mm from the front; None = auto: TPU_BALLAST_GAP in front of the ballast pockets (30.25), REST_DEPTH / 2 without ballast |
| `TPU_BALLAST_GAP` | `2` | rigid wall between the insert and a ballast pocket (plan, >= 4 lines) |
| `TPU_POCKET_COLLAR` | `3` | rigid collar around the pocket opening: rim, walls and ledge stay PETG/PLA. <= TP_BEZEL keeps the seam on the flat island (flush at H) |
| `TPU_TEXT_KEEPOUT` | `1` | ENGRAVE_FACE='top': the text's bounding box + this stays rigid |
| `TPU_MIN_T` | `3` | config error / verify: min TPU thickness (vertical) inside the edge round-overs; thinner TPU gives no cushion |
| `TPU_MIN_EDGE_ANGLE` | `45` | config error: min angle (deg) between the insert's flat underside and the outer surface where the floor plane cuts the nose / ends |
| `TPU_PEGS` | `None` | locating pegs on the tray floor [(x, y), ...]; None = auto: 2 per wing at 25 % / 75 % of the wing span, y = 0.8 x the insert depth (the peg edge >= TPU_PEG_EDGE + 0.5 from the insert's back edge): near the back of the insert, where the TPU over them is thickest; [] = none |
| `TPU_PEG_D` | `5` | peg diameter (the insert's hole: + 2 x TPU_PEG_CLEARANCE) |
| `TPU_PEG_H` | `2.5` | peg height above the floor (hole depth: + TPU_PEG_HEADROOM) |
| `TPU_PEG_CHAMFER` | `0.5` | 45 deg chamfer on the peg top (lead-in; the hole roof bridges D - 2 x this) |
| `TPU_PEG_HEADROOM` | `0.4` | hole deeper than the peg is tall: a sagging TPU roof bridge or a tall peg cannot lift the insert off the floor |
| `TPU_PEG_CLEARANCE` | `0` | radial peg -> hole clearance (printed TPU holes come out a little small: 0 = a snug press fit) |
| `TPU_BED_CHAMFER` | `0.4` | 45 deg chamfer on the insert's underside edges along the seams and round the peg-hole mouths: room for elephant foot and the base's inside corners, so the insert seats flush (0 = none) |
| `TPU_PEG_MIN_COVER` | `2` | config error: min TPU above a peg-hole roof |
| `TPU_PEG_EDGE` | `3` | config error: min plan distance peg edge -> insert edge |
| `TPU_DENSITY` | `1.21` | g/cm3, TPU 95A-98A (mass estimate only) |
| `TPU_MASS_INFILLS` | `(5, 10, 15)` | % gyroid the insert mass is estimated at (10 = recommended) |

</details>

### Connector variants

The builder picks one; every listed variant is generated.

<details><summary>Connector variants: 3 constants (connectors to build, ids, labels)</summary>

| Name | Default | Meaning |
|---|---|---|
| `CONNECTORS` | `('pogo5', 'usbc')` | connector variants to generate (--connector NAME, repeatable); the first one is the preview default. 'pogo5' = 5-pin magnetic pogo, 'usbc' = USB-C breakout pair (USBC_* below), 'jst_sh4' = Qwiic JST-SH header |
| `CONNECTOR_IDS` | `{'pogo5': 'pogo', 'usbc': 'usbc', 'jst_sh4': 'jst'}` | file / manifest ids |
| `CONNECTOR_LABELS` | `{'pogo5': 'Magnetic pogo', 'usbc': 'USB-C', 'jst_sh4': 'JST-SH 4-pin'}` | preview / manifest labels (the Connector control) |

</details>

### Keyboard dock

Read by `geometry/dock.py`; keyboard-local where noted.

<details><summary>Keyboard dock: 23 constants (cut-out, plugs, body, connector housing, pinout)</summary>

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

</details>

### Keyboard dock internals

`geometry/dock.py`; dock-local frame, see its docstring.

<details><summary>Dock internals: 38 constants (plug wall, snap clips, connector pocket, wire cavity, pin-1 mark, JST)</summary>

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

</details>

### USB-C variant

Used when `'usbc'` is in `CONNECTORS`; read by `geometry/usbc.py`, in the dock-local frame.

- **Boards:** the female (blue) breakout sits in the dock. The male (green) breakout sits in a printed grip on the rest's pigtail.
- **Pads used:** only the 4 big pads.

| Pad | Signal |
|---|---|
| G | GND |
| V | 3V3, through a series Schottky at the keyboard end |
| D+ | SDA |
| D- | SCL |

There is no RDY on USB-C.

> [!IMPORTANT]
> The breakout boards differ from seller to seller. MEASURE YOUR BOARDS with calipers and override every board / shell value below before printing.

The 111 USB-C constants are split into five blocks, in file order.

<details><summary>USB-C 1/5: boards, shells and pads (22 constants)</summary>

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

</details>

<details><summary>USB-C 2/5: series Schottky diode (4 constants)</summary>

| Name | Default | Meaning |
|---|---|---|
| `USBC_DIODE` | `(5.2, 2.7)` | series Schottky body L x D: 1N5817/1N5819 DO-41 (BAT54 SOT-23: (3.0, 1.4)); anode -> Pico 3V3, cathode -> V pad |
| `USBC_DIODE_CLEARANCE` | `0.15` | cradle clearance around the diode body |
| `USBC_DIODE_LIFT` | `0.1` | diode body above the female board top (tape it, Kapton) |
| `USBC_DIODE_ROOF` | `1` | min retainer material over the diode cradle (else: inline diode) |

</details>

<details><summary>USB-C 3/5: dock body, well, shoulder, board pocket, clips, print limits (29 constants)</summary>

| Name | Default | Meaning |
|---|---|---|
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

</details>

<details><summary>USB-C 4/5: retainer, screws, lock prongs, pry notches (20 constants)</summary>

| Name | Default | Meaning |
|---|---|---|
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

</details>

<details><summary>USB-C 5/5: grip, withdraw travel, wire slack (36 constants)</summary>

| Name | Default | Meaning |
|---|---|---|
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

</details>

### Dock retention

Both docks. Cantilever clip model, see `geometry/usbc.py` `retention()`.

<details><summary>Dock retention: 6 constants (clip material, friction, lip shear, design pull, margin)</summary>

| Name | Default | Meaning |
|---|---|---|
| `CLIP_E_MPA` | `2000` | blade material modulus (PETG ~2.0 GPa; PLA ~3.5) |
| `CLIP_MU` | `0.3` | friction catch face <-> switchplate edge |
| `CLIP_LIP_SHEAR_MPA` | `15` | conservative lip shear strength (locked blade failure mode) |
| `USBC_PULL_N` | `20` | design pull: USB-C max extraction force |
| `USBC_PULL_UP_DEG` | `20` | design pull direction: this far above horizontal |
| `USBC_RETENTION_MIN` | `1.5` | verify: required margin on the dock tipping load |

</details>

## Printing

Print the rest, plus the parts for **your** connector:

- **Magnetic pogo:** the pogo dock.
- **USB-C:** the USB-C dock, both grip halves and the retainer.
- **Soft top (optional):** the TPU base *instead of* the rest, plus the TPU insert ([Printing the TPU top](#printing-the-tpu-top)).

> [!WARNING]
> **No conductive or metal-filled filament** near the trackpad. That includes TPU: no carbon, CF, ESD or conductive TPU.

### Slicer settings

| Setting | Rest | Docks (pogo, USB-C) | USB-C grip halves, retainer |
|---|---|---|---|
| Material | PLA or PETG | **PETG** (or a well-tuned PLA) | PETG or PLA |
| Orientation | as exported, **bottom down** | as exported, **upside down** | as exported (see below) |
| Supports | **none** | **none** | **none** |
| Layer height | **0.12–0.16 mm**, or adaptive | 0.12–0.16 mm | 0.12–0.16 mm |
| Walls | **4 perimeters** | 3 perimeters | 3 perimeters |
| Top / bottom | **6+ top**, 4–5 bottom | 4 / 4 | 4 / 4 |
| Infill | **25–40 % gyroid** | 100 % or 4+ perimeters | 100 % |
| Seam | rear, or aligned to the back face | rear | rear, away from the nose |

**Rest notes:**

- **Material:** PETG copes better with warm wrists and is less brittle.
- **Orientation:** bottom down, pocket up.
- **Layers:** use 0.12–0.16 mm or variable/adaptive layers, so the curved top and front nose don't stair-step under your wrists.
- **Top layers:** 6+, and ≥ 1 mm on the curved top.
- **Infill:** use more if you skip the ballast.
- **First layer:** the 0.5 mm bottom chamfer absorbs elephant-foot. Keep the first layer clean for the mirrored engraving.

**Dock notes:**

- **Material:** PETG (or a well-tuned PLA), because the snap blades bend across their layer lines.
- **Orientation:** upside down, top face on the bed.
- **Walls:** 3 perimeters, because the plug walls are 1.2 mm and the blades 0.8 mm.
- **Infill:** 100 % or 4+ perimeters (small part).
- **First layer:** the pin-1 marker is on the bed, so keep the first layer clean.

**USB-C grip and retainer notes:**

- **Material:** no conductive filament.
- **Orientation:** lower grip half on its bottom face, upper half on its flat split face, retainer upside down (top plate on the bed).
- **Layers:** 0.12–0.16 mm, because the nose must fit the well cleanly.
- **Infill:** 100 %, because these are small parts that take the 8–20 N unplug force.
- **First layer:** keep elephant-foot off the nose, or it binds in the well.

### Printing the TPU top

Two routes, with the same two STLs: the base for your variant and the insert.

| | Separate print (default) | One multi-material job |
|---|---|---|
| Printers | any printer that prints 95A–98A TPU. Direct drive preferred; 98A also goes through a Bowden tube, slowly | a printer that feeds soft TPU next to PETG: a second nozzle, a toolchanger or an IDEX |
| Loading | base and insert as separate prints | base and insert loaded **together** as one object with two parts |
| Joint | flush seams, 4 pegs; glue optional. A 0.4 mm bed chamfer and 0.4 mm of peg headroom leave room for elephant foot and a sagging hole roof | fused; the pegs key the parts |
| Layer height | **0.1 mm on both parts** (or 0.2 mm on both), so the seams meet on a layer line | any: both parts share one layer grid |
| Supports | none | none |

**Which printers can co-print soft TPU:**

| Printer or system | Soft TPU next to PETG in one job? |
|---|---|
| Bambu H2D (two nozzles) | yes, with TPU on the right nozzle only |
| Prusa XL (toolchanger) | yes, with care: long filament path |
| Snapmaker U1 (toolchanger), J1 / J1s (IDEX) | yes, TPU 90A or harder |
| Other IDEX printers with direct drive on both heads | probably; not checked |
| Bambu AMS, AMS lite, AMS 2 Pro, AMS HT on one nozzle | **no**: soft TPU is not AMS-compatible |
| Prusa MMU3 | **no** |
| Creality CFS (K2 series) | **no**: "CFS does not support TPU" |
| Any single-nozzle printer | separate print only |

- **Bambu "TPU for AMS"** feeds through an AMS, but it is 68D and nearly rigid: no cushion.
- **Bed size:** the base is 271 x 85 mm, like the rest (diagonal on a 256 x 256 bed). The insert is 271 x 30 mm: turn it about 30° on a 256 x 256 or 250 x 210 bed.

**Separate print settings:**

| Setting | TPU base | TPU insert |
|---|---|---|
| Material | PETG (preferred) or PLA | TPU 95A–98A, non-conductive, dark or mid colour |
| Before printing | as usual | dry the TPU: 55–70 °C for 4–8 h (wet TPU strings and pits) |
| Orientation | as exported, bottom down | as loaded: the slicer drops it onto its flat underside |
| Supports | none | none |
| Layer height | **0.1 mm** (first layer 0.2 or 0.1 mm), the same as the insert | **0.1 mm** (first layer 0.2 or 0.1 mm), the same as the base |
| Elephant foot | as the rest (its 0.5 mm bottom chamfer absorbs it) | compensation about 0.15 mm. The seams have a 0.4 mm chamfer; the outer front edge has none |
| Walls | 4 perimeters | 2–3 (2 gives more give) |
| Top / bottom | as the rest | top ≥ 1.2 mm (12 layers at 0.1 mm), 3–4 bottom; monotonic top lines |
| Infill | 25–40 % gyroid | **10 % gyroid** (5 % softer, 15 % firmer) |
| Speed | as the rest | 20–40 mm/s (about 3–4 mm³/s); short or no retraction; part fan on |
| Temperatures | as the rest | follow the spool: Porima 98A 220–240 °C, bed 50–70 °C; Filamix 95A 210–250 °C, bed 40–60 °C |
| Bed surface | as the rest | follow your plate maker's TPU advice. Skip the glue only on a plate that allows it (Prusa's powder-coated textured sheet needs none). On smooth or satin PEI, use glue stick as a release layer: TPU can tear PEI |

- **Why 0.1 mm on both parts:** the floor (3.0 mm), the insert's height (8.8 mm) and the rim (11.8 mm) then all land on a layer line, in both prints. With 0.12 mm layers and a 0.2 mm first layer they fall between layers (3.0 lies between 2.96 and 3.08), so a seam can step by up to about 0.1 mm. 0.2 mm on both parts also lines up, but shows coarser steps on the top. Variable layer heights break the match.
- **The tray floor** of the base is a flat top face. Ironing it is optional.
- **Z contouring:** OrcaSlicer 2.4 or newer can raise top-surface lines to follow the curve. It is untested on TPU. Ironing does not help a TPU top.

**One multi-material job:**

- [ ] **Load both STLs in one import** and answer *Yes* to "load as a single object with multiple parts". Never load the insert alone for this route: it would drop to the bed.
- [ ] **Assign filaments:** PETG (or PLA) for the base, TPU for the insert.
- [ ] **Insert settings per part:** 10 % gyroid, 2–3 walls, top ≥ 1.2 mm.
- [ ] **Prime tower on,** with PETG as the tower filament. **Interface shells on.**
- [ ] **Beam interlocking:** optional. The TPU is ≥ 3 mm thick, so it has room; check the slicer preview. The pegs already key the parts.
- [ ] **Bed at the PETG temperature:** the first 3 mm are all PETG. Leave the door or lid open: a warm chamber softens TPU in the feed path.
- [ ] **TPU speed** limited by flow, for example 3.6 mm³/s for Bambu TPU 95A HF.
- **Expect** one material change per layer from z 3 to 11.8: about 44 layers at 0.2 mm, or 74 at 0.12 mm.

<details><summary>Sources for the printing notes</summary>

- Bambu Lab, [H2D soft and hard filament multi-material guide](https://wiki.bambulab.com/en/h2/manual/soft-and-hard-filament-multi-material-printing-guide) (TPU on the right nozzle, beam interlocking).
- Bambu Lab store, [TPU 95A HF](https://us.store.bambulab.com/products/tpu-95a-hf) ("All AMS Series NOT Compatible") and [TPU for AMS](https://us.store.bambulab.com/products/tpu-for-ams); [TPU for AMS TDS](https://cdn.shopify.com/s/files/1/1339/4265/files/Bambu_TPU_for_AMS_Technical_Data_Sheet.pdf) (68D).
- Prusa, [Flexible materials](https://help.prusa3d.com/article/flexible-materials_2057) (speed, retraction, glue stick on smooth or satin PEI, none on the powder-coated textured sheet) and [Combining materials (XL)](https://help.prusa3d.com/article/combining-materials-xl_498103); [TPU on the MMU3](https://forum.prusa3d.com/forum/original-prusa-i3-mmu3-hardware-firmware-and-software-help/tpu-on-mmu3) (forum).
- Creality, [K2 Plus CFS FAQ](https://forum.creality.com/t/creality-k2-plus-cfs-frequently-asked-questions-you-should-know/21698).
- Snapmaker, [U1 FAQ](https://wiki.snapmaker.com/en/FAQ/u1) and [J1 product page](https://shop.snapmaker.com/products/snapmaker-j1-independent-dual-extruder-3D-printer).
- OrcaSlicer wiki, [Z contouring](https://www.orcaslicer.com/wiki/print_settings/quality/quality_settings_z_contouring) and [multimaterial (interlocking) settings](https://www.orcaslicer.com/wiki/print_settings/multimaterial/multimaterial_settings_advanced.html).

</details>

### Fit test

- [ ] **Dock first:** print one dock as a fit test. It should click into the two cut-outs and come out again with a firm pull.
- [ ] **USB-C dock:** with the retainer fitted, the dock should not come out under a firm pull.
- [ ] **USB-C boards, before you solder:** test-fit the bare female board in the USB-C dock and the bare male board in the grip.
- [ ] **USB-C nose:** check that the grip's nose slides into the well without force.

### TPU test slice

Try the feel and the fit before you print the whole insert. No extra STL is needed.

- [ ] **Cut a slice:** with the slicer's cut tool, cut a 40–50 mm slice out of both the base and the insert, around one peg, for example x 10–55 mm round the peg at x 31.44.
- [ ] **Print that pair** with the settings you plan to use (0.1 mm layers on both).
- [ ] **Check the feel** at 5 / 10 / 15 % gyroid, and 95A vs 98A.
- [ ] **Press right over the peg:** you should not feel a hard spot. If you do, try `--set TPU_PEG_H=2.0`.
- [ ] **Run a fingertip across the seams:** the back seam and the collar should be flush, with no step. If not, see [Troubleshooting, TPU top](#tpu-top).
- [ ] **Check the peg fit:** snug, and the insert sits flat on the floor.

### Bridges and overhangs

Things that print over air:

- **Bottom engraving:** prints against the bed. The first solid layer above it bridges over the recessed letters.
- **Bumper recesses:** 0.6 mm-high Ø10 bridges.
- **Cable tunnel:** a 4.5 mm bridge. The plug bay and the notch are open to the top.
- **Ballast pocket ceilings:** about 20.5 mm bridges across the bar width.
  - Any tuned printer bridges this.
  - A little sag is hidden and is absorbed by the 0.25 mm depth clearance.
  - If your printer can't bridge it, use 10 mm-wide bars (one per side) and `--set "BALLAST_SIZE=(78,10,5)"`. That makes a 10.5 mm bridge and halves the ballast to about 61 g.
- **TPU base:** the same bridges as the rest, and no new overhang (verify: 44.791 cm² of downward-facing area, the same as the rigid rest). The tray floor is a flat top face, and the pegs have 45° top chamfers.
- **TPU insert:** flat on the bed. Its only other downward faces are the four peg-hole roofs: Ø4 bridges with a 45° chamfer ring.
- **Docks:** the pocket, cavity and plug floors are flat bridges of at most 20.4 mm. The lips and the top edge are 45° overhangs.
- **USB-C dock, retainer and grip:**
  - The widest bridge is 10.0 mm (the leg relief under the female board).
  - The well's bottom wall (about 9.5 mm) and the shoulder window floor (9.24 mm) come next.
  - Both of those face a fit, so they sit `USBC_BRIDGE_SAG` (0.15 mm) further away to absorb the sag. Scrape off strings before the first fit.
  - The only overhangs steeper than 48.6° are the 30° clip lips, 0.45 mm wide. The window's crush ribs and the screw counterbores are smaller.
  - verify measures both (`USBC_MAX_BRIDGE`, `USBC_MAX_OVERHANG`).

### Mass

Approximate mass of the default glass rest in PLA, from the generator output:

| Infill | Mass |
|---|---|
| 15 % | ~109 g |
| 25 % | ~128 g |
| solid | ~266 g |

- **On the desk:** with the two steel bars (+122 g), the trackpad and the glass, it weighs about 266 g at 25 % infill. That is the 128 g rest plus the add-ons; it only happens to match the solid figure above.
- **Pogo dock:** about 5 g.
- **USB-C parts:** the dock is about 6.3 g, the grip about 1.2 g (both halves) and the retainer about 1.2 g (solid PLA).

**TPU top:**

| Part | 5 % | 10 % | 15 % | 25 % | solid |
|---|---|---|---|---|---|
| Glass TPU base (PLA) | | | ~103 g | ~116 g | ~213 g |
| TPU insert (TPU, gyroid) | ~28 g | **~29 g** | ~30 g | | ~52 g |

- **The base** is about 20 % smaller in volume than the rigid rest (171.67 vs 214.50 cm³). The bare base: ~104 g / ~117 g / ~217 g.
- **The insert estimate** uses a 1.2 mm solid shell (`MASS_SHELL_T`) and 1.21 g/cm³ (`TPU_DENSITY`).

## Assembly order

The short version. The full steps and pinout are in [wiring.md](../wiring.md), the protection parts in [wiring-details.md](wiring-details.md#optional-protection-parts); the parts are in [bom.md](bom.md).

> [!WARNING]
> **VDDHI is 3.3 V max, never 5 V.**

1. **Order and print**
   - [ ] Buy the parts for your connector in [bom.md](bom.md).
   - [ ] Print the rest variant that matches your trackpad (glass / bare). For the soft top, print that variant's TPU base and the TPU insert instead ([Printing the TPU top](#printing-the-tpu-top)).
   - [ ] Print the parts for your connector ([Printing](#printing)).
2. **Keyboard side, both connectors** (full steps: [wiring.md, Step 1](../wiring.md#step-1-keyboard-side-both-connectors))
   - [ ] Pull SW44/SW43 and take off the OLED cover. Nothing else is opened, cut or filed.
   - [ ] Connect the wires to tap A or tap B:
     - **tap A:** the OLED header joints, or a male header plugged into the switchplate TB1 socket;
     - **tap B:** the Pico pins.
   - [ ] Wire SDA to GP2, SCL to GP3, 3V3(OUT) and GND. With the pogo, optionally RDY on GP15.
   - [ ] Lay the wires flat on the switchplate under the cover, into the dock's rear channel.
3. **Keyboard half of the connector**
   - **Magnetic pogo** (full steps: [wiring.md, Step 2a](../wiring.md#step-2a-magnetic-pogo-dock)):
     - [ ] Press the receptacle into the pogo dock with pin 1 at the left.
     - [ ] Glue it.
     - [ ] Click the dock into the two cut-outs.
   - **USB-C** (full steps: [wiring.md, Step 2b](../wiring.md#step-2b-usb-c-dock)):
     - [ ] Remove the two 5.1 kΩ resistors from the female board.
     - [ ] Put the Schottky diode in the 3V3 line, band toward the V pad.
     - [ ] Check that the receptacle's shell legs are soldered.
     - [ ] Solder the board.
     - [ ] Press it into the USB-C dock behind the shoulder.
     - [ ] Click the dock in.
     - [ ] Press the retainer in until it is flush, and drive its two M2x4 screws. It holds the board, presses the shell and locks the clips.
4. **Prepare the pigtail** (full steps: [wiring.md, Step 3](../wiring.md#step-3-rest-side-trackpad-pigtail))
   - [ ] Cut very flexible 28 AWG wires to `CABLE_PIGTAIL_LEN` (120 mm). You trim them later.
   - [ ] Solder them to the TPS65's 2.0 mm solder pads: SDA, SCL, VDDHI (3V3), GND, and with the pogo optionally RDY. That is five wires for the pogo and four for USB-C.
   - [ ] Leave NRST open.
   - [ ] Sleeve about 18 mm of the bundle for the groove, and leave the end loose.
   - Reminder: VDDHI is 3.3 V max, never 5 V (see the warning above).
5. **Route the cable**
   - [ ] Lay the sleeve into the S-groove in the solder well (a dab of hot glue is fine).
   - [ ] Run it through the tunnel and up out of the back-top notch.
   - Neither the pogo plug nor the USB-C male board fits through the tunnel, so you solder it last.
   - **Magnetic pogo:**
     - [ ] Cut the loose wires (about 15 mm) to reach the docked plug's tails.
     - [ ] Use only 1.5 mm heat-shrink on the joints.
     - [ ] Keep tails, heat-shrink and glue within 3 mm behind the housing and 6 mm tall.
   - **USB-C** (full steps: [wiring.md, Step 3](../wiring.md#step-3-rest-side-trackpad-pigtail), Part B):
     - [ ] Solder the male board, with the wires on the front half of each pad.
     - [ ] Beep end to end both ways up with the bare board, before you close the grip. The grip fits the well only one way up.
     - [ ] Bed the plug shell in 2-part epoxy in the nose's key groove.
     - [ ] Lay the board in the lower grip half.
     - [ ] Lead the wires over the push rib and down the slot.
     - [ ] Close the grip with two M2x4 screws.
     - [ ] Store the 12 mm slack loop in the plug bay.
     - [ ] Let the epoxy cure before the first plug-in.
6. **Fit the module**
   - [ ] **TPU top:** press the insert onto the base's 4 pegs first. Glue is optional ([Fit and attachment](#fit-and-attachment)).
   - [ ] **Glass variant:** bond the glass to the module first (see [Glass handling](#glass-handling)).
   - [ ] Drop the module in, touch side up, with the pad/ZIF edge toward the keyboard. It rests on the ledge.
   - No glue is needed. A few dots of thin double-sided tape on the ledge keep it from lifting.
   - To remove the module, push it out from below through the two holes.
7. **Connect and test**
   - [ ] Set the rest in front of the keyboard (1.5 mm gap).
   - **Magnetic pogo:**
     - [ ] Dock the pigtail's magnetic plug.
     - [ ] Run the end-to-end test in [wiring.md, Step 4](../wiring.md#step-4-test-before-power-up) before you power it.
   - **USB-C:**
     - [ ] Steady the keyboard with one hand and push the grip straight into the well with the other (see [wiring.md, Plugging and unplugging](../wiring.md#plugging-and-unplugging)).
     - [ ] Run the beep test once more with the closed grip before you power it (see [wiring.md, Step 4](../wiring.md#step-4-test-before-power-up)). Both plug orientations were checked with the bare board in step 5.
     - [ ] Label both halves "NOT USB".
8. **Firmware** (full steps: [firmware/README.md](../firmware/README.md))
   - [ ] Build and flash the `ithalat` keymap.
   - [ ] Plug the pad in before the first power-up: unplug USB, connect the pad, plug USB back in.
   - [ ] Wait for `Pad: on` on the OLED.
   - [ ] Calibrate the axes ([calibration](../firmware/README.md#calibration-30-seconds)).
   - After that, the keymap detects a re-plugged pad within about 1.3 s and re-initialises it (see the [hot-plug section](../firmware/README.md#hot-plug-behaviour-and-limits)). Stock QMK would only initialise it at boot.

## Ballast and bumpers

### Ballast

- **Pockets:** two pockets from the underside, one in each wrist wing, take steel flat bar.
- **Bar size:** 78 x 20 x 5 mm each (`BALLAST_SIZE`), about 61 g each and 122 g per pair.
- **Cut to 78 mm:** the pockets are 78.5 x 20.5 x 5.25 mm, so cut the bar to 78 mm. A longer bar does not fit.
- **Why 78 mm:** it is the longest bar that stays ≥ 20 mm from the trackpad and keeps a 3 mm wall at the bed with the default rest.
- **Top skin:** the pockets keep ≥ 3 mm of plastic above them.
- **Fixing:** glue the bars in (a few dots of silicone, CA or epoxy), or close the pockets with the anti-slip pad.
- **Overrides:** if an override makes a bar not fit, the generator shortens it or makes its pocket shallower (`BALLAST_AUTO_SHORTEN = True`), logs it, and verify WARNs with the size to buy. With `BALLAST_AUTO_SHORTEN = False` that is a config error instead.

### Metal near the pad

> [!WARNING]
> **No loose metal near the pad.** Keep steel, magnets and coins at least 15 mm (`TP_METAL_KEEPOUT`; Azoteq AZD068 says 15–20 mm) from the TPS65. Moving conductors are the worst case for capacitive sensing.

- **The one exception, the docked pogo plug:** its two small magnets sit about 7.35 mm from the module outline. verify flags that as a WARN.
- **USB-C:** the connector has no magnets. Its plug shell sits about 13 mm from the module and the male board's copper pads about 5.5 mm. verify also lists these as advisories.
- **Why they are accepted:** they are fixed in place while the pad is powered (the plug is what powers it), and the controller calibrates at power-up.
- **Drift check:** do it at the first power-up (see the [drift check](wiring-details.md#first-power-up)). If the cursor drifts near the back edge, raise `TP_BACK_MARGIN`.

### Bumpers

- **Recesses:** six Ø10 x 0.6 mm locating recesses take the same type of silicone bumper as the keyboard.
- **Positions:** four near the corners, and two on the centre line, front and back, which support the trackpad area.
- **Auto-shift:** the back-middle one moves sideways automatically to stay clear of the cable tunnel.

> [!IMPORTANT]
> **Use bumpers 0.6 mm (`BUMPER_RECESS`) taller than the keyboard's**, because they sit in 0.6 mm recesses. Then the rest's top is level with the switchplate.

- **Wrong height:** bumpers of the keyboard's own height leave the rest 0.6 mm low.
- **Exact value:** set `KEYBOARD_BUMPER_H` to your measured keyboard bumper height, and the preview's print notes give the exact value.

## Glass handling

- **Overlay:** the keycapsss overlay is 65 x 49 x 1.1 mm, black, with no adhesive.

> [!WARNING]
> **The glass is fragile at the edges.** Never force or clamp the glass edges, and never press the module in by its corners.

### How the pocket protects it

- **Recessed:** the pocket keeps the glass top 0.15 mm below the rim. That protects the edges from knocks and from your wrists.
- **Clearance:** the pocket gives 0.25 mm clearance per side.
- **Corners:** the pocket corners are R2.5 (`POCKET_CORNER_R`), so any glass corner of R1.65 or more fits, with a 0.97 mm gap at R4.
- **Full support:** the ledge supports the PCB over its whole flat back, so taps never flex it or point-load the glass.

### Bonding the glass

- [ ] **Measure your glass corner** before you bond it. The radius is not published.
- [ ] **Bond** the glass with the module's own 3M 468MP adhesive.
- [ ] **No air gap:** air gaps hurt sensitivity.
- [ ] **Roll it down** from one short edge.
- [ ] **Press evenly** across the face, not at the edges.

### Other tips

- **Thinner glass:** Azoteq's own option is 0.7 mm. Use `--glass-t 0.7`.
- **Bare variant:** the solder mask or adhesive liner is the touch surface. A thin PET or PEI sheet on top feels better than the liner.
- **Pogo plug:** never lay the magnetic pogo plug on the glass.

## Troubleshooting

Find your symptom, then follow the fix.

### Build and verify

| Symptom | Cause and fix |
|---|---|
| `make verify` fails right after an override | `generate` and `verify` got different `GEN_ARGS` (stale STLs or manifest).<br>Run `make generate verify GEN_ARGS="..."` together. |
| `config error: ...` or `unknown config name` | A value cannot produce a valid part, or the name is misspelt.<br>Every valid name is listed in the [Configuration reference](#configuration-reference). |
| `--set` value is cut off, or a shell error | Quote it: `GEN_ARGS="--set 'REST_PROFILE=[(0,11.8),(85,6)]'"`. |
| A `WARN` row in the verify report | An advisory, not a failure.<br>See the WARN notes below this table. |
| `plug ... clearance to the rest` FAILs | The docked plug or its strain-relief envelope would touch the rest.<br>See the plug fixes below this table. |
| Ballast bars are shorter than `BALLAST_SIZE` (WARN) | An override made the default bar not fit, so the generator shortened it to stay 20 mm from the pad and keep its walls (see the `[rest]` log lines and `log` in the manifest).<br>Buy the size the WARN row prints. |
| Rest STL over 12 MB | Raise `--mesh-edge-len` (default 0.8 mm). |
| Preview is blank or says "3D preview needs WebGL" | It needs WebGL and a network connection for three.js and the fonts. The dimension, parts and pinout panels work without either.<br>Run `make preview` after every `generate`. |

**WARN notes:**

- **Pogo magnets:** the pogo plug-magnets row always warns when the pogo connector is built.
- **USB-C metal:** the two USB-C metal-distance rows (per rest variant) warn when USB-C is built. See [Ballast and bumpers](#ballast-and-bumpers).
- **Height override:** `--height 13`, for example, also warns that the rest's back edge is 1.2 mm higher than the switchplate.

**Plug clearance fixes:**

- [ ] Keep `PLUG_BAY_DEPTH` > 0.
- [ ] Measure your plug and set `DOCK_CONN_W/H/D` (or `PLUG_BODY_JST`) and `PLUG_RELIEF_L/H`.
- [ ] Keep `PLUG_EXIT='down'`. `'rear'` has no room for the cable's turn with the default rest.

### Fit

| Symptom | Cause and fix |
|---|---|
| Module rocks in the pocket | A wire or glue blob is on the ledge.<br>Keep everything inside the 3.5 mm solder well. |
| Glass sits proud of the rim | Wrong variant.<br>Print `ithalat-glass.stl` for glass, or set `--glass-t` to the real thickness. |
| Dock is loose / too tight in the cut-outs | Adjust `DOCK_PLUG_SIZE` (default 13.85 for a 14.0 cut-out) or `DOCK_CLIP_LIP`.<br>Print in PETG. |
| Pogo receptacle loose in the dock | Raise `DOCK_CONN_RIB_H`, or measure the housing and set `DOCK_CONN_W/H/D`.<br>Glue it with CA. |
| Rest sits lower than the switchplate | The rest's bumpers are the keyboard's height.<br>Use bumpers 0.6 mm taller. |

### TPU top

| Symptom | Cause and fix |
|---|---|
| `config error: TPU_...` | A TPU setting cannot give a sound part (floor too high or too low, insert too deep, collar too wide, a peg in the wrong place).<br>The message names the limit. See the config errors in [Deeper cushion and other options](#deeper-cushion-and-other-options), or add `--set TPU_ENABLED=False`. |
| verify fails on TPU rows after a `TPU_*` override | Stale STLs or manifest.<br>Run `make generate verify GEN_ARGS="..."` with the same arguments. |
| `WARNING: TPU top skipped` | A rest override (for example `REST_FRONT_HEIGHT=5`) leaves no room for a sound insert. The rigid parts build as before; the message names the limit.<br>Adjust the `TPU_*` setting it names (then a remaining problem is a config error), or add `--set TPU_ENABLED=False` to silence it. |
| Insert sits proud at the seams (separate print) | Elephant foot on the insert, a sagging hole roof, layer rounding, or tape under it.<br>Use elephant-foot compensation of about 0.15 mm, 0.1 mm layers on both parts, and glue instead of tape. If the pegs still lift it, raise `TPU_PEG_HEADROOM`. |
| Insert sits proud or off to one side in a multi-material job | The two STLs were loaded as separate objects, so the slicer arranged them apart.<br>Load both in one import as one object with two parts. |
| Insert is too tight on the pegs | Printed TPU holes come out a little small.<br>Reprint the insert with X-Y hole compensation of +0.05 to +0.1 mm (OrcaSlicer, Bambu Studio), or XY size compensation of −0.05 to −0.1 mm (PrusaSlicer). |
| Insert is tight against the collar or the back wall | Reprint the insert with X-Y contour compensation of −0.05 to −0.1 mm. |
| Insert is loose on the pegs | Put a drop of flexible glue in each hole, or glue the whole floor ([Fit and attachment](#fit-and-attachment)). |
| Front edge of the insert lifts | Glue it down with contact cement or a flexible glue. |
| Strings, bubbles or pits on the TPU | Wet filament.<br>Dry it (55–70 °C, 4–8 h), print slower, use short or no retraction. |
| TPU top feels hard | Too much infill or too thick a top skin.<br>Use 5–10 % gyroid, 2–3 walls, a top of about 1.2 mm. |
| Erratic tracking after fitting the insert | A conductive TPU (carbon, CF, ESD).<br>Check a scrap with a multimeter (it should read open), and reprint in a plain TPU. |

### USB-C

| Symptom | Cause and fix |
|---|---|
| USB-C grip is hard to plug in, or will not go fully home | See the grip checklist below this table. |
| USB-C dock lifts out when you unplug | Press the retainer fully home, flush with the dock top, and tighten its two screws: its two prongs lock the back clips.<br>Unplug with a fingertip braced on the dock face beside the well, so the pull stays in your hand (see [wiring.md, Plugging and unplugging](../wiring.md#plugging-and-unplugging)). |
| Pulling the rest away drags the keyboard (USB-C) | Expected: USB-C does not break away.<br>Unplug the grip before you move the rest. |
| OLED freezes while something is plugged into the USB-C dock | A USB charger or cable is in the dock instead of the grip. Most chargers short D+ to D−, which shorts SDA to SCL.<br>Unplug it. If the OLED stays frozen, re-plug the keyboard's USB (see [wiring-details.md, It is not USB](wiring-details.md#it-is-not-usb-chargers-and-laptops)). |
| USB-C pad fails, but works with the bare male board turned over | The female board wires only one of its two D+/D− contact pairs, and the grip fits the well one way up only.<br>Replace the female board with one that joins both pairs (see [wiring.md, Step 4](../wiring.md#step-4-test-before-power-up)). |
| VDDHI reads about 3.0–3.1 V (USB-C) | Normal: the series Schottky drops a few tenths of a volt (up to about 3.25 V while the pad idles). The TPS65 runs from 1.65 V.<br>If it equals the Pico's 3V3 exactly, the diode is shorted or bypassed (see [wiring.md, Step 4](../wiring.md#step-4-test-before-power-up)). |

**Grip checklist:**

- [ ] Plug it in straight, without rocking it.
- [ ] Check that the receptacle mouth sits flush with the floor of the well.
- [ ] Check that the grip's nose slides into the well freely.
- [ ] If either check fails, measure both boards, set the `USBC_*` constants and reprint (see [wiring.md, Step 2b](../wiring.md#step-2b-usb-c-dock), Part A).
- [ ] Clean any elephant-foot off the grip's nose.

### Tracking and firmware

| Symptom | Cause and fix |
|---|---|
| Cursor moves the wrong way, or no pad after replugging | Firmware side: see [calibration](../firmware/README.md#calibration-30-seconds) and [hot-plug](../firmware/README.md#hot-plug-behaviour-and-limits) in firmware/README.md. |
| Erratic tracking | Metal, magnets or conductive filament near the pad, a 5 V supply, or an air gap under the glass.<br>See the [electrical notes](wiring-details.md#electrical-notes) in wiring-details.md. |
| Cursor drift near the back edge with the pogo plug docked | Re-plug so the pad recalibrates, or raise `TP_BACK_MARGIN`. |
