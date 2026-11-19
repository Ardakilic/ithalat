"""ithalat - single source of truth for every dimension (millimetres, degrees).

Frames
------
Assembly frame (all rest STLs, manifest): origin = wrist-rest front-left-bottom
corner, +X right (as the typist sees it), +Y toward the keyboard, +Z up. The
rest occupies X[0, REST_WIDTH] Y[0, REST_DEPTH] Z[0, REST_HEIGHT].
Keyboard-local frame (KEY*, OLED*, PICO*, DOCK_CENTER_X, DOCK_SWITCH_CENTER_Y):
origin = keyboard front-left-bottom corner, top view, +Y toward the back.
TPS65 "front view" frame (TP_COMPONENT_BOX, TP_PADS_BOX, TP_ZIF_BOX,
PUSH_HOLE_POS): x from the module's left edge looking at the TOUCH side, y from
the long edge nearest the connector (that edge faces +Y / the keyboard).

Overrides
---------
Every UPPER_CASE name can be overridden from the CLI:
    python3 generate.py --set REST_DEPTH=90 --set "REST_PROFILE=[(0,11.8),(30,11.8),(85,6)]"
Names listed in DERIVED (bottom of this file) are recomputed from the others
AFTER the overrides are applied, unless they are overridden themselves - so
e.g. --glass-t 0.7 also changes VARIANTS['glass'], and --set KEYBOARD_HEIGHT=12.2
also moves REST_HEIGHT and REST_BACK_HEIGHT.
"""

# ---------------------------------------------------------------------------
# Keyboard (Yakamoz, verified from the KiCad/DXF files + caliper measurements)
# ---------------------------------------------------------------------------
KEYBOARD_WIDTH = 270.98      # plate / PCB outline width
KEYBOARD_DEPTH = 81.0        # plate / PCB outline depth
KEYBOARD_HEIGHT = 11.8       # bottom acrylic underside -> switchplate top (caliper)
KEYBOARD_CORNER_R = 2.8      # acrylic outline corner radius
KEYBOARD_LAYERS = [          # bottom -> top: (name, thickness, material)
    ('bottom', 3.0, 'acrylic'),
    ('bottom-middle', 2.0, 'acrylic'),
    ('main PCB', 1.6, 'pcb'),
    ('upper-middle', 4.0, 'acrylic'),
    ('switchplate', 1.2, 'pcb'),
]
KEY_PITCH = 19.05            # 1U
FRONT_ROW_Y = 11.93          # front row (row index 3) key centre Y, keyboard-local
FIRST_KEY_X = 11.65          # column 0 key centre X, keyboard-local
KEY_ROWS = 4                 # switch rows (row 0 = back, row KEY_ROWS-1 = front)
KEY_COLS = 14                # switch columns (column 0 = left)
KEY_ABSENT = [(0, 6), (0, 7), (1, 6), (1, 7), (2, 6), (2, 7)]  # (row, col) grid
                             # positions without a switch (OLED cover / Pico area)
REMOVED_KEYS = [(3, 6), (3, 7)]   # (row, col) replaced by the dock (SW44/SW43)
OLED_COVER = (117.1, 22.1, 153.9, 81.0)   # x0, y0, x1, y1 keyboard-local
OLED_COVER_TOP_Z = 24.0      # smoked acrylic cover top (M2x10 standoffs)
OLED_COVER_T = 3.0           # cover thickness (2 or 3 mm, unverified; 3 = the
                             # conservative value for the dock clearance check)
KEYCAP_TOP_Z = 25.0          # keycap tops above the desk (assembly z, estimate);
                             # verify: every dock top must stay below it
PICO_CENTER = (135.49, 52.69)  # keyboard-local; USB end faces the back
PICO_SIZE = (21.0, 51.0)       # w (X) x l (Y)
KEYBOARD_BUMPER_H = None     # height of the keyboard's own bumpers (measure them);
                             # None = unknown. The rest needs bumpers BUMPER_RECESS
                             # taller, because they sit in recesses

# ---------------------------------------------------------------------------
# Wrist-rest body (ergonomics first: crowned bar, generously rounded edges)
# ---------------------------------------------------------------------------
REST_WIDTH = KEYBOARD_WIDTH  # bbox width incl. the end bulges
REST_DEPTH = 85.0            # front (wrist side) -> back (keyboard side)
REST_HEIGHT = KEYBOARD_HEIGHT  # max height = trackpad island height
REST_BACK_HEIGHT = REST_HEIGHT  # top height at the back edge, meets the keyboard
REST_FRONT_HEIGHT = 6.5      # profile height at the front edge, before the nose round
REST_PEAK_FROM_BACK = 28.0   # crown peak, measured from the back edge
REST_PROFILE = None          # optional [(distance_from_back, height), ...]: a
                             # monotone C1 spline (PCHIP) replaces the simple
                             # back/peak/front profile; normalised so its max
                             # == REST_HEIGHT
REST_FALL_POWER = 2.0        # shape of the peak->front fall: z = H - dH * t^p
                             # (p > 1 keeps the slope 0 at the peak -> C1)
REST_BACK_EDGE_R = 1.2       # back top edge round-over (against the keyboard)
REST_FRONT_NOSE_R = 9.0      # front nose: horizontal semi-axis of the elliptic lip
REST_FRONT_NOSE_V = None     # front nose vertical semi-axis; None = auto:
                             # min(REST_FRONT_NOSE_R / 2, front wall budget)
REST_END_EDGE_R = 5.0        # left/right end round-over
REST_END_TAPER = 24.0        # the end round-over fades in from the back-corner
                             # radius over this length along the end (keeps the
                             # small back corners crease-free)
REST_MIN_WALL = 0.8          # min vertical wall left above the bottom chamfer
REST_PLAN_FRONT_CORNER_R = 16.0  # plan-view front corner radius
REST_PLAN_BACK_CORNER_R = 2.8    # plan-view back corner radius (= keyboard corners)
REST_END_BULGE = 2.0         # ends bulge outward by this sagitta (gentle arc, >= 0)
REST_BOTTOM_CHAMFER = 0.5    # 45 deg bottom chamfer (anti elephant-foot)
REST_KEYBOARD_GAP = 1.5      # gap between rest back face and keyboard front face
MESH_EDGE_LEN = 0.8          # target triangle edge on the curved top surface

# ---------------------------------------------------------------------------
# Trackpad: Azoteq TPS65 (datasheet v1.06 + photo measurements)
# ---------------------------------------------------------------------------
TP_WIDTH = 65.0              # module outline (+-0.2)
TP_DEPTH = 49.0              # module outline (+-0.2), the connector edge is a long edge
TP_CORNER_R = 4.0            # photo fit, +-0.5
TP_PCB_T = 1.0               # FR4
TP_ADHESIVE_T = 0.13         # 3M 468MP front adhesive
TP_COMPONENT_H = 1.1         # tallest back-side part (0603 C2) incl. tolerance
TP_COMPONENT_BOX = (12.9, 52.0, 4.4, 31.0)  # x0, x1, y0, y1 (front view)
TP_PADS_BOX = (19.9, 30.8, 4.9, 7.1)        # six 2.0 mm-pitch solder pads
TP_ZIF_BOX = (21.2, 29.7, 8.8, 14.2)        # 6-pin 0.5 mm ZIF J1 incl. actuator
TP_PAD_NAMES = ['SDA', 'SCL', 'VDDHI', 'GND', 'NRST', 'RDY']  # front view, left->right
TP_CONNECTOR_EDGE = 'back'   # the pad/ZIF long edge faces the keyboard (+Y)
TP_CENTER_X = REST_WIDTH / 2  # module centre X (keyboard centre line)
TP_BACK_MARGIN = 9.0         # rest back edge -> pocket opening back edge
TP_MIN_SIDE_MARGIN = 15.0    # min rest material left / right of the pocket opening
TP_MIN_FRONT_MARGIN = 8.0    # min rest material in front of the pocket opening
TP_CLEARANCE = 0.25          # pocket clearance per side (module +-0.2)
TP_PCB_DENSITY = 1.85        # g/cm3, FR4 (mass estimate only)
TP_PARTS_MASS = 1.0          # g, components on the module (mass estimate only)
TP_METAL_KEEPOUT = 15.0      # advisory: keep loose steel / magnets this far from
                             # the module outline (AZD068: 15-20 mm); verify WARNs
                             # about the docked pogo plug's two magnets and the
                             # USB-C plug shell / male board
TP_SURFACE_RECESS = 0.15     # glass / PCB top sits this far below the rim
TP_BEZEL = 5.0               # surface is exactly flat at REST_HEIGHT this far
                             # around the pocket ...
TP_BLEND = 14.0              # ... then blends (smoothstep, C1) into the profile

# Glass overlay (keycapsss: 65 x 49 x 1.1, black, no adhesive)
GLASS_T = 1.1                # glass overlay thickness (--glass-t); 0.5..3 mm supported by the TPS65
GLASS_WIDTH = 65.0           # glass outline (same as the module)
GLASS_DEPTH = 49.0           # glass outline
GLASS_CORNER_R = 4.0         # glass corner radius (not published - measure it); the
                             # pocket corner POCKET_CORNER_R is checked against it
GLASS_DENSITY = 2.5          # g/cm3 (mass estimate only)
VARIANTS = {'glass': GLASS_T, 'bare': 0.0}   # id -> glass thickness, one STL each
VARIANT_LABELS = {'glass': 'With glass', 'bare': 'Without glass'}  # preview tab labels

# Stepped pocket
POCKET_LEDGE = 2.0           # min flat support ledge under the module edge
POCKET_CAVITY_DEPTH = 1.6    # component relief below the PCB bottom
POCKET_CAVITY_MARGIN = 1.0   # relief = component box + this margin
POCKET_WELL_DEPTH = 3.5      # solder well below the PCB bottom (pads + ZIF)
POCKET_WELL_MARGIN = 1.5     # well = pads/ZIF box + this margin
POCKET_INNER_R = 1.0         # corner radius of the relief / well
POCKET_CORNER_R = 2.5        # plan corner radius of the pocket opening. A part fits
                             # only if its corner R >= POCKET_CORNER_R - 3.41 x
                             # TP_CLEARANCE, so a small radius is safe for an
                             # unmeasured module / glass corner (it costs a sub-mm
                             # corner gap); TP_CORNER_R still shapes the ledge
POCKET_RIM_CHAMFER = 0.4     # rim bevel: horizontal width ...
POCKET_RIM_CHAMFER_H = 0.08  # ... and height. Must be <= TP_SURFACE_RECESS - 0.05,
                             # so the vertical pocket wall rises above the glass /
                             # film top edge (a sideways knock meets the wall)
PUSH_HOLE_D = 6.0            # push-out holes through the floor (pen from below)
PUSH_HOLE_POS = [(16.0, 38.0), (49.0, 38.0)]  # front-view module coords,
                             # component-free area (box ends at y = 31)
MIN_FLOOR = 2.0              # min material under every pocket / channel

# ---------------------------------------------------------------------------
# Cable (5-core pigtail from the TPS65 pads to the dock)
# ---------------------------------------------------------------------------
CABLE_D = 3.5                # pigtail jacket diameter
CABLE_CHANNEL_W = 4.5        # tunnel / groove width
CABLE_TUNNEL_H = CABLE_D + 0.5  # tunnel height (cable + clearance)
CABLE_NOTCH_W = 6.0          # back-top-edge exit notch width (U-shaped)
CABLE_NOTCH_DEPTH = 4.0      # notch depth from the top
CABLE_NOTCH_LEN = TP_BACK_MARGIN - 2.0  # notch length from the back face (leaves
                             # a 2 mm wall to the pocket)
CABLE_NOTCH_X = 135.475      # notch / tunnel / riser centre X = KB_X0 + DOCK_CENTER_X
                             # (derived: straight below the dock connector)
CABLE_RISER_BACK_WALL = 2.0  # riser (tunnel -> notch) stops this far from the back
                             # face, so the cable can only leave through the notch.
                             # Riser length CABLE_NOTCH_LEN - this must be >= CABLE_D + 1
CABLE_RISER_TOP = None       # riser top z; None = auto: 0.3 mm above the height at
                             # which the U-notch is CABLE_CHANNEL_W wide, so the
                             # riser -> notch passage is never narrower than the channel
CABLE_SKIN = 1.6             # min material above the tunnel
CABLE_SBEND = 5.0            # strain-relief S-bend sideways offset in the well
CABLE_GROOVE_PAD_SETBACK = 1.0  # the S-bend starts this far in front of the pad row
CABLE_GROOVE_TAIL = 4.0      # straight groove end after the S-bend = where the cable
                             # sleeve ends (loose wires from there to the pads)
CABLE_PLUG_LOOSE_LEN = 15.0  # unsleeved wire length at the plug end (route length
                             # from the plug's tails back to the sleeve end)
CABLE_WIRE_D = 0.9           # one core (28 AWG silicone) outer diameter (preview)
CABLE_WIRE_COLORS = {'SDA': '#2f6fd6', '3V3': '#d63a2f', 'GND': '#1d1f21',
                     'SCL': '#e3c22b', 'RDY': '#3a9a4a'}  # wiring.md colours (preview)
CABLE_BEND_R = 5.0           # centreline bend radius of the sleeved cable (route /
                             # preview drawing)
CABLE_PIGTAIL_LEN = 120      # total pigtail length (BOM / preview)

# ---------------------------------------------------------------------------
# Pigtail plug (cable half of the connector) and the plug bay in the rest
# ---------------------------------------------------------------------------
PLUG_BODY = (20.1, 4.0, 4.2)  # housing W (X) x D (mating axis, Y) x H (Z) outside
                             # the dock face; derived from DOCK_CONN_TYPE (pogo5:
                             # the MG005 housing, same as the keyboard half's
                             # DOCK_CONN_W/D/H; jst_sh4: PLUG_BODY_JST)
PLUG_BODY_JST = (6.0, 2.0, 2.95)  # 'jst_sh4': the part of the SHR-04V-S cable plug
                             # left outside the header face (estimate)
PLUG_RELIEF_W = None         # strain relief behind the housing (solder tails, joint
                             # heat-shrink, glue): width, None = PLUG_BODY width ...
PLUG_RELIEF_L = 3.0          # ... length behind the housing's back face ...
PLUG_RELIEF_H = 6.0          # ... and height, centred on the connector axis
PLUG_TAIL_L = 1.75           # solder tails out of the housing's back (MG005 drawing)
PLUG_EXIT = 'down'           # 'down': the loose wires turn straight down into the
                             # plug bay and riser right behind the relief (or use a
                             # right-angle pogo pair, Adafruit 5359); 'rear': the
                             # sleeved cable leaves the relief toward the user
                             # (needs room for the turn - fails verify by default)
PLUG_WIRE_BEND_R = 1.0       # 'down': the wires drop this far in front of the relief
PLUG_MIN_CLEARANCE = 0.5     # verify FAILs when the plug envelope comes closer to
                             # the rest than this
PLUG_BAY_W = 26.0            # plug bay cut into the back-top edge, centred on the
                             # notch: width (X) ...
PLUG_BAY_L = CABLE_NOTCH_LEN  # ... length from the back face (derived) ...
PLUG_BAY_DEPTH = 2.0         # ... depth below REST_HEIGHT (0 = no bay)
PLUG_BAY_R = 1.0             # bay plan corner radius
PLUG_BAY_CHAMFER = 0.4       # 45 deg chamfer on the bay's top edges (0 = none)

# ---------------------------------------------------------------------------
# Engraving
# ---------------------------------------------------------------------------
ENGRAVE_TEXT = 'ithalat'     # engraved text ('' = none)
ENGRAVE_FACE = 'bottom'      # 'bottom' (mirrored, reads right when flipped) | 'top'
ENGRAVE_DEPTH = 0.6          # 3 layers at 0.2 mm
ENGRAVE_HEIGHT = 12.0        # cap height
ENGRAVE_FONT = 'LiberationSans-Bold'  # font file stem (fonts-liberation) or a .ttf path
ENGRAVE_CENTER_Y = None      # text centre Y; None = auto (front half, clear of
                             # bumpers / push holes; in front of the pad on 'top')
ENGRAVE_MARGIN = 2.0         # 'bottom': min distance text <-> bed footprint edge
ENGRAVE_PAD_GAP = 3.0        # 'top' auto placement: gap text top <-> pocket opening

# ---------------------------------------------------------------------------
# Underside: bumpers and ballast
# ---------------------------------------------------------------------------
BUMPER_D = 10.0              # silicone bumper diameter (same type as the keyboard)
BUMPER_RECESS = 0.6          # locating recess depth
BUMPER_INSET = 11.0          # bumper centre inset from the bbox edges
BUMPER_POSITIONS = None      # None = auto: 4 corners + front/back middle

BALLAST_ENABLED = True       # steel ballast pockets in the two wrist wings (--no-ballast)
BALLAST_SIZE = (78.0, 20.0, 5.0)  # steel flat bar L (X) x W (Y) x T = the longest
                             # bar that keeps the rules below with the default rest
BALLAST_AUTO_SHORTEN = True  # True: a bar that does not fit is shortened / its
                             # pocket made shallower (logged, verify WARNs);
                             # False: that is a config error
BALLAST_CLEARANCE = 0.25     # pocket = bar + this per side (and on the depth)
BALLAST_MIN_DIST_FROM_TP = 20.0  # plan distance pocket <-> trackpad opening
BALLAST_MIN_TOP_SKIN = 3.0   # material above the pocket
BALLAST_WALL = 3.0           # min wall pocket <-> outside, measured at the bed
                             # (the footprint inside the bottom chamfer)
BALLAST_MIN_LEN = 20.0       # shorter pocket than this: omitted
BALLAST_MIN_DEPTH = 1.5      # shallower pocket than this: omitted
BALLAST_CENTER_Y = None      # None = auto (mid depth)
STEEL_DENSITY = 7.85         # g/cm3

# ---------------------------------------------------------------------------
# Material / mass estimate
# ---------------------------------------------------------------------------
PLA_DENSITY = 1.24           # g/cm3
MASS_SHELL_T = 1.2           # avg solid shell (perimeters + top/bottom) for the
                             # infill mass approximation
STL_MAX_MB = 12.0            # verify: max size of a rest STL

# ---------------------------------------------------------------------------
# TPU insert: optional second "Top" (geometry/tpu.py). A flat-bottomed soft TPU
# insert replaces the front of the rest - nose, front corners, ends and the front
# slope up to the ballast - where wrists and palms land. It is cut out of the
# rigid rest's own envelope (base + insert == the rigid rest, minus a hidden fit
# relief at the floor: TPU_BED_CHAMFER, TPU_PEG_HEADROOM), so the outside shape,
# the pocket and every fit stay as checked. One pair of STLs serves both routes:
# print the insert alone (flat side down, no supports) and press it onto the
# base's pegs, or print base + insert as one multi-material object.
# ---------------------------------------------------------------------------
TPU_ENABLED = True           # also write stl/ithalat-<variant>-tpu-base.stl + stl/ithalat-tpu-insert.stl.
                             # If another override leaves no room for a sound insert and no TPU_*
                             # constant was set, generate / verify skip the TPU top with a WARNING
                             # (rigid parts only); with any TPU_* override it is a config error
TPU_TOP_LABELS = {'rigid': 'Rigid', 'tpu': 'TPU insert', 'tpu-thin': 'Thin TPU insert'}
                             # preview "Top" switch / manifest labels (Top switch order)
TPU_FLOOR_Z = 3.0            # tray floor = the insert's flat underside (z above the bed). Must leave
                             # MIN_FLOOR over every underside recess below the insert (bumpers and
                             # bottom engraving, 0.6 deep -> >= 2.6) and keep the front edge at
                             # least TPU_MIN_EDGE_ANGLE (-> <= ~4.0). Lower = thicker, softer TPU
TPU_INSERT_DEPTH = None      # insert back edge, mm from the front; None = auto: TPU_BALLAST_GAP in
                             # front of the ballast pockets (30.25), REST_DEPTH / 2 without ballast
TPU_BALLAST_GAP = 2.0        # rigid wall between the insert and a ballast pocket (plan, >= 4 lines)
TPU_POCKET_COLLAR = 3.0      # rigid collar around the pocket opening: rim, walls and ledge stay
                             # PETG/PLA. <= TP_BEZEL keeps the seam on the flat island (flush at H)
TPU_TEXT_KEEPOUT = 1.0       # ENGRAVE_FACE='top': the text's bounding box + this stays rigid
TPU_MIN_T = 3.0              # config error / verify: min TPU thickness (vertical) inside the edge
                             # round-overs; thinner TPU gives no cushion
TPU_MIN_EDGE_ANGLE = 45.0    # config error: min angle (deg) between the insert's flat underside and
                             # the outer surface where the floor plane cuts the nose / ends
TPU_PEGS = None              # locating pegs on the tray floor [(x, y), ...]; None = auto: 2 per wing at
                             # 25 % / 75 % of the wing span, y = 0.8 x the insert depth (the peg edge
                             # >= TPU_PEG_EDGE + 0.5 from the insert's back edge): near the back of
                             # the insert, where the TPU over them is thickest; [] = none
TPU_PEG_D = 5.0              # peg diameter (the insert's hole: + 2 x TPU_PEG_CLEARANCE)
TPU_PEG_H = 2.5              # peg height above the floor (hole depth: + TPU_PEG_HEADROOM)
TPU_PEG_CHAMFER = 0.5        # 45 deg chamfer on the peg top (lead-in; the hole roof bridges D - 2 x this)
TPU_PEG_HEADROOM = 0.4       # hole deeper than the peg is tall: a sagging TPU roof bridge or a tall
                             # peg cannot lift the insert off the floor
TPU_PEG_CLEARANCE = 0.0      # radial peg -> hole clearance (printed TPU holes come out a little
                             # small: 0 = a snug press fit)
TPU_BED_CHAMFER = 0.4        # 45 deg chamfer on the insert's underside edges along the seams and
                             # round the peg-hole mouths: room for elephant foot and the base's
                             # inside corners, so the insert seats flush (0 = none)
TPU_PEG_MIN_COVER = 2.0      # config error: min TPU above a peg-hole roof
TPU_PEG_EDGE = 3.0           # config error: min plan distance peg edge -> insert edge
TPU_DENSITY = 1.21           # g/cm3, TPU 95A-98A (mass estimate only)
TPU_MASS_INFILLS = (5, 10, 15)  # % gyroid the insert mass is estimated at (10 = recommended)

# ---------------------------------------------------------------------------
# Thin TPU insert: optional third "Top" (geometry/tpu_thin.py). The same plan as
# the TPU insert (TPU_INSERT_DEPTH, TPU_POCKET_COLLAR, TPU_BALLAST_GAP,
# TPU_TEXT_KEEPOUT: the same covered area), but its underside is one plane
# tilted up toward the back, so the TPU is 2-5 mm thick (TPU_THIN_T at the
# thinnest spot) instead of 5-9: the same TPU touch with almost no cushion,
# about 20 % less TPU and a quicker print. The tilt is solved: the smallest one
# whose edge at the nose / ends is >= TPU_MIN_EDGE_ANGLE + TPU_THIN_EDGE_MARGIN.
# Walls and pegs stay vertical (it presses straight down); the STL is saved
# lying on its underside (print as it loads; the manifest matrix places it).
# Shares TPU_PEG_D, TPU_PEG_CHAMFER, TPU_PEG_CLEARANCE, TPU_BED_CHAMFER,
# TPU_PEG_EDGE, TPU_DENSITY and TPU_MASS_INFILLS with the TPU insert.
# ---------------------------------------------------------------------------
TPU_THIN_ENABLED = True      # also write stl/ithalat-<variant>-tpu-thin-base.stl +
                             # stl/ithalat-tpu-thin-insert.stl (needs TPU_ENABLED). A thin config
                             # problem is a config error once a TPU_THIN_* is set; otherwise
                             # (rest or TPU-insert-only overrides) the thin top is skipped with a WARNING
TPU_THIN_T = 2.0             # thinnest TPU (vertical) inside the edge round-overs and on the nose
                             # crest; with the default tilt that is the back seam (from ~3.6 the
                             # underside is flat and it is the nose crest). Sets the underside's
                             # height (1.0 .. 6.0; below ~1.6 the pegs lose their TPU cover)
TPU_THIN_EDGE_MARGIN = 0.5   # deg: the tilt is solved so the nose / ends edge is at least
                             # TPU_MIN_EDGE_ANGLE + this (0 .. 5)
TPU_THIN_PEGS = None         # pegs on the tilted tray floor [(x, y), ...]; None = auto: one row at
                             # y = REST_FRONT_NOSE_R + 3 (thickest wing TPU, just behind the nose):
                             # 2 per wing at 25 % / 75 % of the wing span + 2 in front of the
                             # trackpad at 25 % / 75 % of the pocket opening (left out where they do
                             # not fit, e.g. round a top engraving); [] = none
TPU_THIN_PEG_H = 1.5         # peg height above the tilted floor (TPU_PEG_D wide, TPU_PEG_CHAMFER top)
TPU_THIN_PEG_HEADROOM = 0.3  # hole deeper than the peg is tall (0 .. 1)
TPU_THIN_PEG_MIN_COVER = 0.8  # config error: min TPU above a thin insert's peg-hole roof (>= 0.4)

# ---------------------------------------------------------------------------
# Connector variants (the builder picks one; every listed variant is generated)
# ---------------------------------------------------------------------------
CONNECTORS = ('pogo5', 'usbc')  # connector variants to generate (--connector NAME,
                             # repeatable); the first one is the preview default.
                             # 'pogo5' = 5-pin magnetic pogo, 'usbc' = USB-C breakout
                             # pair (USBC_* below), 'jst_sh4' = Qwiic JST-SH header
CONNECTOR_IDS = {'pogo5': 'pogo', 'usbc': 'usbc', 'jst_sh4': 'jst'}   # file / manifest ids
CONNECTOR_LABELS = {'pogo5': 'Magnetic pogo', 'usbc': 'USB-C', 'jst_sh4': 'JST-SH 4-pin'}  # preview /
                             # manifest labels (the Connector control)

# ---------------------------------------------------------------------------
# Keyboard dock (read by geometry/dock.py; keyboard-local where noted)
# ---------------------------------------------------------------------------
DOCK_ENABLED = True          # build stl/ithalat-dock-<connector>.stl (--no-dock)
DOCK_SWITCH_CUTOUT = 14.0    # switchplate cut-out (square)
DOCK_PLUG_SIZE = 13.85       # plug that drops into the cut-out
DOCK_PLATE_T = 1.2           # switchplate thickness (derived: KEYBOARD_LAYERS[-1])
DOCK_PLUG_DEPTH = 3.4        # plug length below the plate top
DOCK_CLIP_LIP = 0.45         # snap lip under the plate
DOCK_KEYS = 2                # number of switch positions the dock replaces
DOCK_BODY_W = 36.6           # dock body above the plate: width (X, < 2U minus keycap clearance)
DOCK_BODY_D = 19.0           # dock body depth (Y); >= 18.9 so the body also covers
                             # the back edge of the 14 mm cut-outs (contract had 18.0)
DOCK_BODY_H = 7.0            # dock body height above the switchplate top
DOCK_BODY_R = 2.0            # dock body corner radius
DOCK_FRONT_SETBACK = 0.6     # dock front face behind the keyboard front face
DOCK_CENTER_X = 135.475      # midpoint of the removed switches (derived: REMOVED_KEYS)
DOCK_SWITCH_CENTER_Y = 11.93  # removed switch centre Y (derived: REMOVED_KEYS rows)
DOCK_CONN_TYPE = 'pogo5'     # legacy single-connector switch: derived = CONNECTORS[0];
                             # overriding it alone (--set DOCK_CONN_TYPE=jst_sh4)
                             # generates only that connector
DOCK_CONN_W = 20.1           # connector housing width (5-pin magnetic pogo)
DOCK_CONN_H = 4.2            # connector housing height
DOCK_CONN_D = 4.0            # connector housing depth (mating axis)
DOCK_CONN_CLEARANCE = 0.15   # press-fit clearance per side
DOCK_CONN_Z = 3.2            # connector centreline above the switchplate top
DOCK_WIRE_HOLE = 5.0         # wire entry hole into the dock
CONNECTOR_PINOUT = ['SDA', '3V3', 'GND', 'SCL', 'RDY']  # pins 1..5, both halves (GND centre)
KB_X0 = (REST_WIDTH - KEYBOARD_WIDTH) / 2   # keyboard origin X in the assembly (centred)

# ---------------------------------------------------------------------------
# Keyboard dock internals (geometry/dock.py; dock-local frame, see its docstring)
# ---------------------------------------------------------------------------
DOCK_PLUG_WALL = 1.2         # plug wall: 3 perimeters at 0.4 mm
DOCK_UNDERPLATE_GAP = 4.0    # switchplate underside -> main PCB top (upper-middle
                             # acrylic; derived: KEYBOARD_LAYERS[-2])
DOCK_KEY_CLEARANCE = 0.7     # min body inset from the 2-key cell edge, per side
DOCK_CLIP_T = 0.8            # snap blade thickness (2 perimeters)
DOCK_CLIP_W = 3.6            # snap blade width (shrunk automatically if it does not fit)
DOCK_CLIP_SLOT = 0.5         # slots on both sides of a blade
DOCK_CLIP_OUTER_GAP = 0.4    # gap between blade and body on the blade's outer side
DOCK_CLIP_RELIEF = 0.7       # free space behind a blade
DOCK_CLIP_ROOT_SKIN = 2.0    # solid body above the slot tops (blade root = BODY_H - this)
DOCK_CLIP_CATCH_DEG = 45.0   # catch face angle from horizontal (0 = flat MX-style catch, permanent)
DOCK_CLIP_BACK_WALL = 'inner'  # where the back-half blades sit: 'inner' = the walls
                             # facing each other (pogo / JST dock), 'back' = the
                             # plugs' back walls, outer half (the USB-C dock: its
                             # female board covers the web between the plugs)
DOCK_CLIP_LAND = 0.15        # vertical land at full lip height
DOCK_CLIP_LEADIN_DEG = 30.0  # lead-in ramp angle from vertical (insertion)
DOCK_CLIP_EMBED = 0.3        # lip prism overlap into the blade (boolean robustness)
DOCK_CONN_RIB_H = 0.25       # crush rib protrusion into the connector pocket (0 = no ribs)
DOCK_CONN_RIB_R = 0.6        # crush rib radius (half-round)
DOCK_CONN_STOP = 0.6         # stop ledge width at the pocket bottom (x ends)
DOCK_CONN_STOP_Z = 0.4       # stop ledge height at the pocket bottom (top/bottom)
DOCK_CONN_NECK_D = 1.0       # depth of the stop "neck" behind the pocket
DOCK_CONN_PROUD = 0.0        # connector face proud of the dock face (+) / recessed (-)
DOCK_CONN_MIN_WALL = 0.6     # min material below / above the connector pocket
DOCK_CAV_FLOOR = 1.0         # wire cavity floor z (floor over the plugs)
DOCK_CAV_ROOF = 1.6          # solid top skin over the wire cavity
DOCK_CAV_MIN_D = 4.0         # min wire-cavity depth behind the neck (solder tails + joints)
DOCK_CAV_MARGIN = 0.2        # wire hole -> cavity wall margin
DOCK_REAR_CH_W = 3.0         # rear wire channel width (5 x 30 AWG side by side)
DOCK_REAR_CH_H = 2.8         # rear wire channel height above the plate (open bottom)
DOCK_MARK_DEPTH = 0.4        # pin-1 marker depth on the top face (2 layers)
DOCK_MARK_SIZE = 1.6         # pin-1 triangle base width / height
DOCK_SEGMENTS = 48           # circle resolution of the dock's round features
POGO5_PITCH = 2.54           # 5-pin magnetic pogo pin pitch (Adafruit 5413 / MG005)
DOCK_JST_W = 6.0             # 'jst_sh4': SM04B-SRSS-TB body width
DOCK_JST_H = 2.95            # 'jst_sh4': body height (mounting height)
DOCK_JST_D = 4.25            # 'jst_sh4': body depth (mating axis)
DOCK_JST_TAB_W = 7.0         # 'jst_sh4': width across the SMD fitting nails (estimate)
DOCK_JST_TAB_H = 0.9         # 'jst_sh4': fitting nail height above the body bottom (estimate)
JST_SH4_PITCH = 1.0          # 'jst_sh4': pin pitch
JST_SH4_PINOUT = ['GND', '3V3', 'SDA', 'SCL']  # 'jst_sh4': Qwiic / STEMMA QT pins 1..4

# ---------------------------------------------------------------------------
# USB-C variant ('usbc' in CONNECTORS; geometry/usbc.py, dock-local frame).
# Female (blue) breakout in the dock, male (green) breakout in a printed grip
# on the rest's pigtail. Only the 4 big pads are used: G = GND, V = 3V3 through
# a series Schottky at the keyboard end, D+ = SDA, D- = SCL (no RDY).
# The breakout boards differ from seller to seller: MEASURE YOUR BOARDS with
# calipers and override every board / shell value below before printing.
# ---------------------------------------------------------------------------
USBC_F_BOARD = (13.0, 13.5, 1.0)  # female board W (X) x L (mating axis) x T - measure
USBC_F_SHELL = (8.94, 3.26, 7.35)  # receptacle shell W x H x L (mouth -> back) - measure
USBC_F_SHELL_PROUD = 1.5     # receptacle mouth ahead of the female board's front edge - measure
USBC_F_SHELL_SINK = 0.0      # shell bottom below the board top (0 = top mount; mid-mount
                             # receptacles sink into a board cut-out) - measure
USBC_F_SHELL_X = 0.0         # receptacle centre right of the board centre (X) - measure
USBC_F_LEG_RELIEF = 0.5      # recess under the board for shell-leg stubs / solder
USBC_F_RIM = 1.5             # the board rests on (and the retainer presses) this edge rim;
                             # the relief inside it is the dock's widest bridge (<= 10 mm)
USBC_F_DEPTH = 6.2           # receptacle mating depth: mouth -> tip of a fully seated plug
                             # (USB-IF reference 6.20)
USBC_F_PADS = ['G', 'D', 'D', 'V']  # female pads, left -> right in the dock (beep-test them)
USBC_F_PAD_L = 3.0           # female pad row length (Y) at the board's rear end - measure
USBC_F_LEGS_L = 1.0          # SMD signal-leg row behind the shell (kept free of the diode)
USBC_M_BOARD = (8.64, 16.5, 0.8)  # male board W x L (plug tip -> board rear end) x T - measure;
                             # sellers' boards run about 8.0-8.64 x 16.0-17.1: every length
                             # in that range builds and verifies; below ~16.4 the grip is too
                             # short for its alignment pegs (dropped, verify warns)
USBC_M_SHELL = (8.25, 2.40)  # plug shell W x H (USB-C spec) - measure
USBC_M_SHELL_R = 1.0         # plug shell corner radius (grip cavity corner chamfer)
USBC_M_PLUG_L = 9.0          # plug length from the tip; the PCB (straddle tails) starts behind it - measure
USBC_M_PADS = ['V', 'D-', 'D+', 'G']  # male pads, left -> right as assembled (beep-test them)
USBC_M_PAD_L = 3.0           # pad length (Y) at the male board's rear end - measure
USBC_M_TAIL_H = 0.4          # straddle tails / solder above and below the board (grip relief)
USBC_M_JOINT_H = 1.5         # solder joints + wires above the pads (grip cavity height)
USBC_M_RIM = 0.8             # the grip clamps the male board on edge strips this wide
USBC_M_TAB_L = 2.0           # plug shell side tabs + their solder on the board edges reach this
                             # far behind the board's front edge: no clamp strips there
                             # (relief USBC_M_TAIL_H above and below) - measure
USBC_SIGNALS = {'G': 'GND', 'V': '3V3', 'D+': 'SDA', 'D-': 'SCL'}  # breakout pad -> signal
USBC_DIODE = (5.2, 2.7)      # series Schottky body L x D: 1N5817/1N5819 DO-41 (BAT54 SOT-23:
                             # (3.0, 1.4)); anode -> Pico 3V3, cathode -> V pad
USBC_DIODE_CLEARANCE = 0.15  # cradle clearance around the diode body
USBC_DIODE_LIFT = 0.1        # diode body above the female board top (tape it, Kapton)
USBC_DIODE_ROOF = 1.0        # min retainer material over the diode cradle (else: inline diode)

USBC_CONN_Z = 4.25           # connector axis above the switchplate top (grip floats over the rest)
USBC_DOCK_H = 9.0            # USB-C dock body height above the plate (keycap tops ~13 above);
                             # the top stays under the OLED cover's underside (9.2 above the
                             # plate with a 3 mm cover), so a cover edge further forward than
                             # OLED_COVER cannot block the dock - measure the cover edge
USBC_DOCK_R = 0.6            # USB-C dock corner / top-edge radius (DOCK_BODY_R for this dock)
USBC_DOCK_D = 20.9           # USB-C dock depth (Y): back face 0.6 in front of the OLED cover
USBC_FACE_FLAT_MIN = 0.3     # flat dock face kept between the well's entry chamfer and the
                             # top-edge round
USBC_WELL_DEPTH = None       # chamfered well in the dock face; the receptacle mouth sits at its
                             # floor and the grip nose enters it (side loads -> printed walls);
                             # None = auto: as deep as the female board leaves rear stop
                             # (USBC_REAR_STOP_MIN), within USBC_WELL_DEPTH_RANGE (4.45 with the
                             # default board); deeper = longer nose engagement and the grip
                             # further from the trackpad edge
USBC_WELL_DEPTH_RANGE = (3.5, 4.45)  # auto well depth limits (a deeper well shortens the grip
                             # body: no room for its pegs / screws; shallower: grip nearer the pad)
USBC_WELL_CLEARANCE = 0.15   # grip nose -> well wall, per side (verify prints the tilt the nose
                             # takes before it bears on the wall, ~2.7 deg by default)
USBC_WELL_CHAMFER = 1.0      # 45 deg entry chamfer (capture range)
USBC_WELL_FLOOR_MIN = 0.6    # min material between the well / its entry chamfer and the plate
USBC_BRIDGE_SAG = 0.15       # sag allowance: the dock's bridged faces that face a fit (the
                             # well's bottom wall, the shoulder window floor) sit this much
                             # further away (they print as bridges and sag toward the fit)
USBC_SHOULDER_T = None       # front shoulder wall well floor -> board front edge; None = auto:
                             # max(USBC_SHOULDER_MIN_T, USBC_F_SHELL_PROUD) (flush mouth)
USBC_SHOULDER_MIN_T = 1.2    # verify: min shoulder wall (takes the 20 N pull)
USBC_MOUTH_TOL = 0.2         # verify: receptacle mouth vs well floor
USBC_WINDOW_CLEARANCE = 0.15  # shoulder window = receptacle shell + this per side
USBC_WINDOW_RIB = (0.25, 0.5)  # vertical crush ribs on the window's side walls: protrusion,
                             # radius (protrusion - USBC_WINDOW_CLEARANCE = grip on the shell)
USBC_BOARD_CLEARANCE = 0.15  # board pocket = female board + this per side (X)
USBC_BOARD_PLAY = 0.2        # board pocket length = board L + this (Y)
USBC_REAR_STOP_MIN = 1.2     # verify: min rear stop wall behind the board (takes the 20 N push)
USBC_REAR_CH_W = 4.0         # rear wire channel width (4 wires side by side)
USBC_REAR_CH_H = None        # rear channel height above the plate (open bottom); None =
                             # board top + USBC_REAR_CH_ABOVE_BOARD
USBC_REAR_CH_ABOVE_BOARD = 1.3  # ... (the wires leave the pads over the board's rear edge)
USBC_CLIP_CATCH_DEG = 30.0   # USB-C dock catch face angle from horizontal: flatter than the
                             # pogo dock's 45 deg, so its clips hold harder (20 N pulls)
USBC_CLIP_ROOT_Z = 5.0       # blade root height above the plate (as in the pogo dock: 6.35 mm
                             # free length, ~1.1 % strain; taller = softer clips)
USBC_CLIP_RELIEF = 1.2       # free space behind a blade (the lock prong fills it)
USBC_CLIP_BACK_WALL = 'back'  # DOCK_CLIP_BACK_WALL for the USB-C dock
USBC_BRACE_MIN_W = 8.0       # verify: flat dock face either side of the well (finger brace)
USBC_MAX_BRIDGE = 10.5       # verify: widest bridge of a USB-C part in print orientation
USBC_MAX_OVERHANG = 0.6      # verify: widest steeper-than-48.6 deg overhang (the 30 deg
                             # catch lips print as 0.45 mm overhangs)

USBC_RET_ENABLED = True      # print stl/ithalat-usbc-retainer.stl (holds the board down,
                             # closes the window, carries the clip lock prongs); without it
                             # nothing holds the female board down: epoxy it in
USBC_RET_CLEARANCE = 0.1     # retainer -> opening clearance per side
USBC_RET_PLATE_T = 2.4       # retainer top plate (arms) thickness = recess depth (holds the
                             # screw heads' counterbores)
USBC_RET_ARM_W = 2.4         # arm width (Y) from the central block to the prongs
USBC_RET_CAV_H = 1.6         # wire cavity height above the female board's pads
USBC_RET_BUMP = 0.25         # crush bumps on the prong sides (interference = this -
                             # USBC_LOCK_PRONG_X_CLR); they locate the retainer, screws hold it
USBC_RET_BUMP_W = 0.6        # crush bump width (Y)
USBC_RET_BUMP_Z = (0.4, 0.3)  # bump band: starts this far above the blade root, ends this far
                             # below the arm recess floor
USBC_RET_SHELL_PRESS = (0.1, 0.5, 3)  # half-round ribs under the retainer's shell channel that
                             # press the receptacle shell onto the board (one over the window):
                             # interference, radius, count; side loads then bear on plastic
USBC_RET_SCREW = (2.0, 1.6, 2.3, 3.9, 1.4, 4.0)  # 2 x M2x4 self-tapping pan head down through
                             # the arms into the dock (positive hold-down): nominal, pilot D
                             # (dock), clearance D (arm), head counterbore D, its depth, pilot depth
USBC_RET_SCREW_L = 4.0       # retainer screw length (M2x4, the same screw as the grip)
USBC_RET_SCREW_X = None      # screw centres +-X on the arms; None = midway between the board
                             # pocket and the back blade's side slot
USBC_SCREW_PULLOUT_N = 60.0  # verify: conservative pull-out of one M2 self-tapping screw with
                             # >= 2.5 mm of thread in PETG / PLA
USBC_LOCK = True             # 2 prongs behind the back clip blades: positive dock lock
USBC_LOCK_PRONG_T = 1.05     # prong thickness (Y) in the USBC_CLIP_RELIEF gap
USBC_LOCK_BACK_CLR = 0.05    # prong -> slot back wall (and backing rib); the rest of the relief
                             # is the prong -> blade gap
USBC_LOCK_PRONG_X_CLR = 0.2  # prong -> slot side walls (X), per side
USBC_LOCK_BACKING = 1.0      # backing rib (Y) in the plug hollow below the plate: backs the
                             # prong down past the lip, so the blade cannot push it away
USBC_LOCK_PRONG_BELOW = 2.4  # prong reaches this far below the switchplate top (past the lip)
USBC_PRY_NOTCH = (1.2, 3.0, 1.0)  # pry notches at the arm ends: width (X), length (Y), depth

USBC_GRIP_W = 18.0           # grip body width (pinch faces)
USBC_GRIP_BELOW = 3.0        # grip body (and nose) bottom below the axis
USBC_GRIP_ABOVE = 3.5        # grip body top above the axis
USBC_GRIP_FACE_GAP = 0.5     # grip body front -> dock face (mated)
USBC_GRIP_WALL = 1.6         # min grip wall
USBC_GRIP_NOSE_WALL = 1.2    # min nose wall (the part that enters the well)
USBC_GRIP_NOSE_CHAMFER = 1.0  # 45 deg chamfer on the nose's long edges (well bridge <= 10)
USBC_GRIP_NOSE_LEADIN = 0.4  # chamfer around the nose face
USBC_EMBED = 0.3             # overlap of merged solids (nose root in the body; boolean
                             # robustness only)
USBC_NUDGE = 0.00731         # odd offset on the plug-shell cavity's chamfer so its corners never
                             # sit exactly on a relief face (mesh robustness only)
USBC_GRIP_CAV_CLEARANCE = 0.1  # grip cavity around the plug shell / male board
USBC_GRIP_CAV_CHAMFER = 0.6  # 45 deg corner chamfer of the plug-shell cavity (clears the
                             # shell's USBC_M_SHELL_R corners, keeps the nose corner wall)
USBC_GRIP_EDGE = 0.6         # 45 deg chamfer on the body's top / bottom edges
USBC_GRIP_R = 2.0            # body plan corner radius
USBC_SHELL_EXPOSED = 6.5     # plug shell exposed in front of the grip nose; the nose stops
                             # (this - USBC_F_DEPTH) before the well floor when seated
USBC_GRIP_BOARD_SQUEEZE = 0.0  # flat board-pocket ceiling below the board top (+) or above it
                             # (-); the crush ribs below do the clamping
USBC_GRIP_CLAMP_RIB = (0.3, 2)  # half-round crush ribs across the bottom half's seat under the
                             # board's edge strips: height (= radius), count per side; the
                             # screws crush them, so the clamp survives layer rounding
USBC_PRINT_LAYER = 0.2       # verify: layer height the grip clamp is checked at
USBC_GRIP_COLLAR = (0.03, 0.6)  # shell collar at the male board's front edge: clearance per side
                             # around the plug shell, length; its rear face stops the board's
                             # front corners (boards wider than the shell)
USBC_GRIP_GLUE_GROOVE = (0.4, 1.2, 0.2)  # epoxy key groove around the plug shell (sides and
                             # bottom): depth (the sides keep USBC_GRIP_NOSE_WALL), length, gap
                             # after the collar; cured epoxy locks the shell to the grip
USBC_GRIP_BOARD_GAP = 0.1    # male board rear edge -> push rib
USBC_GRIP_PUSH_RIB = 0.8     # rib behind the board's rear edge (takes the insertion push)
USBC_GRIP_WIRE_SQUEEZE = 0.1  # wire clamp: slot = CABLE_WIRE_D - this (zig-zag pinch)
USBC_GRIP_WIRE_BAND = 4.2    # wire slot width (X) at the grip's underside (4 wires side by
                             # side); over the push rib the band is as wide as the pad row
                             # (male board W - 2 x USBC_M_RIM) and the slot tapers to this
USBC_GRIP_JOINT_MARGIN = 0.5  # solder-joint cavity reaches this far past the pad row
USBC_GRIP_SCREW = (2.0, 1.6, 2.3, 3.9, 1.4, 3.0)  # M2x4 self-tapping pan head: nominal,
                             # pilot D (top half), clearance D, head counterbore D, its
                             # depth (bottom face), pilot depth
USBC_GRIP_SCREW_L = 4.0      # grip screw length (M2x4)
USBC_GRIP_SCREW_X = 6.25     # screw / peg centres beside the male board (+-X); the screws sit
                             # beside the board's middle, kept inside the grip body
USBC_GRIP_PEG = (1.8, 1.5, 0.2)  # alignment pegs: D, height, hole oversize (printed holes shrink)
USBC_GRIP_PEG_WALL = 0.6     # min wall peg hole <-> screw hole; less (short boards): no pegs
USBC_GRIP_RIDGES = (0.4, 1.0, 2.0)  # finger ridges on the sides: depth, width, pitch
USBC_GRIP_RIDGE_MARGIN = 0.3  # ridges stop this far from the edge chamfers / counterbores
USBC_GRIP_MIN_FLOAT = 0.5    # verify: grip bottom above the rest top (mated and withdrawn)
USBC_GRIP_POCKET_CLEAR = 1.0  # verify: grip rear end -> trackpad pocket opening (plan)
USBC_WITHDRAW = 7.5          # travel that frees the plug (verify sweeps the grip back)
USBC_WIRE_SLACK = 12.0       # extra loose wire (S-loop in the plug bay) so the grip can be
                             # withdrawn; verify: >= plug tip -> dock face (plug clears the well)

# Dock retention (both docks): cantilever clip model, see geometry/usbc.py retention()
CLIP_E_MPA = 2000.0          # blade material modulus (PETG ~2.0 GPa; PLA ~3.5)
CLIP_MU = 0.3                # friction catch face <-> switchplate edge
CLIP_LIP_SHEAR_MPA = 15.0    # conservative lip shear strength (locked blade failure mode)
USBC_PULL_N = 20.0           # design pull: USB-C max extraction force
USBC_PULL_UP_DEG = 20.0      # design pull direction: this far above horizontal
USBC_RETENTION_MIN = 1.5     # verify: required margin on the dock tipping load

# ---------------------------------------------------------------------------
# Derived values: recomputed in this order after CLI overrides (unless the name
# itself was overridden). Keep each default above equal to its formula here.
# ---------------------------------------------------------------------------
DERIVED = {
    'REST_WIDTH': lambda c: c.KEYBOARD_WIDTH,
    'REST_HEIGHT': lambda c: c.KEYBOARD_HEIGHT,
    'REST_BACK_HEIGHT': lambda c: c.REST_HEIGHT,
    'TP_CENTER_X': lambda c: c.REST_WIDTH / 2,
    'VARIANTS': lambda c: {'glass': c.GLASS_T, 'bare': 0.0},
    'CABLE_TUNNEL_H': lambda c: c.CABLE_D + 0.5,
    'CABLE_NOTCH_LEN': lambda c: max(3.0, c.TP_BACK_MARGIN - 2.0),
    'PLUG_BAY_L': lambda c: c.CABLE_NOTCH_LEN,
    'DOCK_CENTER_X': lambda c: round(sum(c.FIRST_KEY_X + col * c.KEY_PITCH
                                         for _, col in c.REMOVED_KEYS) / max(1, len(c.REMOVED_KEYS)), 4),
    'DOCK_SWITCH_CENTER_Y': lambda c: round(sum(c.FRONT_ROW_Y + (c.KEY_ROWS - 1 - row) * c.KEY_PITCH
                                                for row, _ in c.REMOVED_KEYS) / max(1, len(c.REMOVED_KEYS)), 4),
    'DOCK_PLATE_T': lambda c: c.KEYBOARD_LAYERS[-1][1],
    'DOCK_UNDERPLATE_GAP': lambda c: c.KEYBOARD_LAYERS[-2][1],
    'KB_X0': lambda c: (c.REST_WIDTH - c.KEYBOARD_WIDTH) / 2,
    'CABLE_NOTCH_X': lambda c: c.KB_X0 + c.DOCK_CENTER_X,
    'PLUG_BODY': lambda c: ((c.DOCK_CONN_W, c.DOCK_CONN_D, c.DOCK_CONN_H) if c.DOCK_CONN_TYPE == 'pogo5'
                            else tuple(c.PLUG_BODY_JST)),
}
