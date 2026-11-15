"""Keyboard-side connector dock ("2U dock") for ithalat.

The dock replaces the two front-row centre switches of the Yakamoz (SW44 /
SW43, keyboard-local X 125.95 and 145.00, Y 11.93). It is a low rounded block
that sits ON the switchplate. Two hollow square plugs drop into the two empty
14 mm switch cut-outs and snap under the 1.2 mm switchplate, like MX switches.
The keyboard half of the 5-pin magnetic pogo connector is press-fitted into a
pocket on the front face (-Y, toward the wrist rest).

Public API (see the shared contract)
-----------------------------------
    build_dock(cfg) -> (trimesh.Trimesh mesh_local, numpy 4x4 print_T)
    dock_info(cfg)  -> dict (JSON-serialisable)

`cfg` is the config module (or any namespace). Every DOCK_* value is read with
getattr() and falls back to the contract default, so this module works even
when the config lacks a name.

Dock-local frame (mesh_local)
-----------------------------
Origin = the midpoint between the two removed switch centres, ON the
switchplate top surface. +X right (as the typist sees it), +Y toward the back
of the keyboard, +Z up. The plugs hang below z = 0. The keyboard front edge is
at y = -DOCK_SWITCH_CENTER_Y. Placement in the assembly frame:
translate(KB_X0 + DOCK_CENTER_X, REST_DEPTH + REST_KEYBOARD_GAP +
DOCK_SWITCH_CENTER_Y, KEYBOARD_HEIGHT).

Layout (default values, dock-local mm)
--------------------------------------
* Body: x +/-18.3, y -11.33 (front face, 0.6 behind the keyboard front edge)
  to +7.67, z 0 to 7.0. The vertical corners have radius DOCK_BODY_R. The top
  edges use a "printable round": a quarter round that turns into a 45 degree
  chamfer where it meets the top face (see print orientation below).
* Plugs: 13.85 mm square, centred at x = +/-9.525, y = 0, hanging to z = -3.4.
  They are hollow and open at the bottom (1.2 mm walls). The wire holes open
  into them, and a small adapter board in the 4 mm gap under the plate can
  poke its parts up into them.
* Snap blades: there are 4, each 0.8 mm thick and about 3.6 mm wide. Each plug
  has one in the outer half of its front wall and one in the back half of the
  wall that faces the other plug (the web).
  - A blade is cut free by 0.5 mm slots and a 0.7 mm relief behind it. The
    slots run up INTO the body, so the blade is rooted 2 mm below the body top.
  - That gives a free length of about 6.4 mm. The 0.45 mm lip then needs only
    about 0.375 mm of deflection, which is about 1.1 % strain at the root.
  - Lips sit only where there is free space under the plate. The upper-middle
    acrylic cavity under the two cut-outs measures 34.1 x 16.0 x 4.0 mm. It is
    flush with the OUTER cut-out edges, so the outer walls carry no lips.
  - The catch face is 45 degrees, not flat, so a firm pull (about 20 N) takes
    the dock out without opening the case.
* Connector pocket: (W + 2c) x (H + 2c), depth DOCK_CONN_D, so the connector
  face is flush with the dock front face. It is centred at x = 0 and
  z = DOCK_CONN_Z.
  - Two 0.25 mm crush ribs on the end walls make the fit a press fit.
  - A 0.6 mm stop ledge (the "neck") holds the connector at the right depth.
  - Behind it is the wire cavity for the solder tails and joints.
* Wire paths out of the cavity:
  (a) A DOCK_WIRE_HOLE (5 mm) hole drops through the floor into EACH plug, and
      so into the 4 mm gap below the switchplate, for a small protection /
      adapter board.
  (b) A 3.0 x 2.8 mm open-bottom channel runs over the web between the plugs
      and out of the back face at plate level. This is the route for the 4-5
      wires coming from the OLED header (keyboard-local Y 24.2), lying flat on
      the switchplate under the OLED cover's front edge.
  NOTE: the research (connector.md 1.5) found a 2.9 mm acrylic bar at
  keyboard-local Y 20.0-22.9 between the under-plate cavity and the OLED header
  slot. So wires cannot run from the OLED header to the dock UNDER the
  switchplate without cutting acrylic. Route (b) is the real wire path.
* Pin-1 marker: a small triangle, 0.4 mm deep, on the top face above pin 1.
  Pin 1 (SDA) is at the -X end of the connector.

Print orientation (print_T)
---------------------------
The dock prints UPSIDE DOWN: a 180 degree rotation about X, with the flat top
face on the bed. This needs no supports:
* The plugs and snap blades grow straight up as vertical walls.
* The lips' 45 degree catch faces and the top-edge 45 degree chamfer are
  ordinary 45 degree overhangs.
* The pocket, cavity and plug floors are short flat bridges: 20.4 mm max,
  anchored at both ends.
* The rear wire channel opens upward.
* The pin-1 marker lies against the bed, so it comes out crisp.
Printed on its back face instead, a free blade would always have one face
hanging over a slot. Printed the right way up, the plugs would need support.
The cost of upside-down printing is that the blades bend across their layer
lines. That is why the strain is kept at about 1 %. PETG (or a well-tuned PLA)
is recommended.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

# ---------------------------------------------------------------------------
# Contract defaults: used only when cfg lacks the attribute.
# ---------------------------------------------------------------------------
_DEFAULTS = {
    'KEY_PITCH': 19.05,
    'KEYBOARD_HEIGHT': 11.8,
    'OLED_COVER': (117.1, 22.1, 153.9, 81.0),  # keyboard-local x0, y0, x1, y1
    'OLED_COVER_TOP_Z': 24.0,                   # absolute (keyboard bottom = 0)
    'OLED_COVER_T': 3.0,                        # cover thickness (2-3 mm; 3 = conservative)
    'DOCK_SWITCH_CUTOUT': 14.0,
    'DOCK_PLUG_SIZE': 13.85,
    'DOCK_PLATE_T': 1.2,
    'DOCK_PLUG_DEPTH': 3.4,
    'DOCK_CLIP_LIP': 0.45,
    'DOCK_KEYS': 2,
    'DOCK_BODY_W': 36.6,
    'DOCK_BODY_D': 19.0,
    'DOCK_BODY_H': 7.0,
    'DOCK_BODY_R': 2.0,
    'DOCK_FRONT_SETBACK': 0.6,
    'DOCK_CENTER_X': 135.475,
    'DOCK_SWITCH_CENTER_Y': 11.93,
    'DOCK_CONN_TYPE': 'pogo5',
    'DOCK_CONN_W': 20.1,
    'DOCK_CONN_H': 4.2,
    'DOCK_CONN_D': 4.0,
    'DOCK_CONN_CLEARANCE': 0.15,
    'DOCK_CONN_Z': 3.2,
    'DOCK_WIRE_HOLE': 5.0,
    'CONNECTOR_PINOUT': ['SDA', '3V3', 'GND', 'SCL', 'RDY'],
    'PLA_DENSITY': 1.24,
}

# ---------------------------------------------------------------------------
# Dock-internal design constants (mm / degrees): fallbacks only. config.py
# carries the same names (single source of truth) and its values win, so
# e.g. `--set DOCK_CLIP_CATCH_DEG=0` gives a flat, permanent catch.
# ---------------------------------------------------------------------------
DOCK_PLUG_WALL = 1.2          # plug wall: 3 perimeters at 0.4 mm
DOCK_UNDERPLATE_GAP = 4.0     # switchplate underside -> main PCB top (upper-middle acrylic)
DOCK_KEY_CLEARANCE = 0.7      # min body inset from the 2-key cell edge, per side
DOCK_CLIP_T = 0.8             # snap blade thickness (2 perimeters)
DOCK_CLIP_W = 3.6             # snap blade width (shrunk automatically if it does not fit)
DOCK_CLIP_SLOT = 0.5          # slots on both sides of a blade
DOCK_CLIP_OUTER_GAP = 0.4     # gap between blade and body on the blade's outer side (z > 0)
DOCK_CLIP_RELIEF = 0.7        # free space behind a blade (>= lip - side clearance + margin)
DOCK_CLIP_ROOT_SKIN = 2.0     # solid body above the slot tops -> blade root z = H - this
DOCK_CLIP_CATCH_DEG = 45.0    # catch face angle from horizontal (0 = flat MX catch, permanent)
DOCK_CLIP_LAND = 0.15         # vertical land at full lip height
DOCK_CLIP_LEADIN_DEG = 30.0   # lead-in ramp angle from vertical (insertion)
DOCK_CLIP_EMBED = 0.3         # lip prism overlap into the blade (boolean robustness)

DOCK_CONN_RIB_H = 0.25        # crush rib protrusion into the pocket (0 = no ribs);
                              # interference = rib - clearance = 0.10 mm per side
DOCK_CONN_RIB_R = 0.6         # crush rib radius (half-round)
DOCK_CONN_STOP = 0.6          # stop ledge width at the pocket bottom (x ends)
DOCK_CONN_STOP_Z = 0.4        # stop ledge height at the pocket bottom (top/bottom)
DOCK_CONN_NECK_D = 1.0        # depth of the stop "neck" behind the pocket
DOCK_CONN_PROUD = 0.0         # connector face proud of the dock face (+) / recessed (-)
DOCK_CONN_MIN_WALL = 0.6      # min material below / above the pocket

DOCK_CAV_FLOOR = 1.0          # wire cavity floor z (floor over the plugs = this thick)
DOCK_CAV_ROOF = 1.6           # solid top skin over the wire cavity
DOCK_CAV_MIN_D = 4.0          # min wire-cavity depth behind the neck (solder tails + joints)
DOCK_CAV_MARGIN = 0.2         # wire hole -> cavity wall margin

DOCK_REAR_CH_W = 3.0          # rear wire channel width (5 x 30 AWG Kynar side by side)
DOCK_REAR_CH_H = 2.8          # rear wire channel height above the plate (open bottom)

DOCK_MARK_DEPTH = 0.4         # pin-1 marker depth (2 layers)
DOCK_MARK_SIZE = 1.6          # pin-1 triangle base width / height
DOCK_SEGMENTS = 48            # circle resolution

# Connector bodies (keyboard half). pogo5 dims come from cfg DOCK_CONN_W/H/D.
POGO5_PITCH = 2.54            # Adafruit 5413/5359 (MG005): 20.08 x 4.20 x 4.00 mm housing
# JST SM04B-SRSS-TB: side-entry (right angle) SH header, 4 pins at 1.0 mm pitch.
# The body is n + 2 = 6.0 mm wide (JST "A" dimension), 4.25 mm deep and 2.95 mm
# tall (mounting height, verified by a distributor listing). The two SMD
# fitting nails stick out sideways at the bottom to about 7.0 mm across [I].
# The header is used bare: solder 4 wires to its tails, then glue it into the
# pocket. Its open (mating) face is flush with the dock front face. A Qwiic /
# STEMMA QT cable plugs straight in.
DOCK_JST_W = 6.0
DOCK_JST_H = 2.95
DOCK_JST_D = 4.25
DOCK_JST_TAB_W = 7.0          # across the fitting nails [I]
DOCK_JST_TAB_H = 0.9          # nail height above the header bottom [I]
JST_SH4_PITCH = 1.0
JST_SH4_PINOUT = ['GND', '3V3', 'SDA', 'SCL']   # Qwiic / STEMMA QT convention


# ---------------------------------------------------------------------------
# parameters
# ---------------------------------------------------------------------------

def _get(cfg, name, default=None):
    if hasattr(cfg, name):
        return getattr(cfg, name)
    if name in _DEFAULTS:
        return _DEFAULTS[name]
    if name in globals():
        return globals()[name]
    return default


def _params(cfg):
    """Resolve every dimension once (validated) for build_dock and dock_info."""
    g = lambda n: _get(cfg, n)  # noqa: E731
    p = SimpleNamespace()
    p.pitch = float(_get(cfg, 'DOCK_KEY_PITCH', None) or g('KEY_PITCH'))
    p.keys = int(g('DOCK_KEYS'))
    p.cut = float(g('DOCK_SWITCH_CUTOUT'))
    p.s = float(g('DOCK_PLUG_SIZE'))
    p.plate_t = float(g('DOCK_PLATE_T'))
    p.depth = float(g('DOCK_PLUG_DEPTH'))
    p.lip = float(g('DOCK_CLIP_LIP'))
    p.W = float(g('DOCK_BODY_W'))
    p.D = float(g('DOCK_BODY_D'))
    p.H = float(g('DOCK_BODY_H'))
    p.R = float(g('DOCK_BODY_R'))
    p.setback = float(g('DOCK_FRONT_SETBACK'))
    p.center_x = float(g('DOCK_CENTER_X'))
    p.center_y = float(g('DOCK_SWITCH_CENTER_Y'))
    p.kb_h = float(g('KEYBOARD_HEIGHT'))
    p.conn_type = str(g('DOCK_CONN_TYPE'))
    p.clr = float(g('DOCK_CONN_CLEARANCE'))
    p.conn_z = float(g('DOCK_CONN_Z'))
    p.hole_d = float(g('DOCK_WIRE_HOLE'))
    p.wall = float(g('DOCK_PLUG_WALL'))
    p.gap_under = float(g('DOCK_UNDERPLATE_GAP'))
    p.key_clear = float(g('DOCK_KEY_CLEARANCE'))
    p.density = float(g('PLA_DENSITY'))

    # clips
    p.clip_t = float(g('DOCK_CLIP_T'))
    p.clip_w = float(g('DOCK_CLIP_W'))
    p.clip_slot = float(g('DOCK_CLIP_SLOT'))
    p.clip_gap = float(g('DOCK_CLIP_OUTER_GAP'))
    p.clip_relief = float(g('DOCK_CLIP_RELIEF'))
    p.clip_root_skin = float(g('DOCK_CLIP_ROOT_SKIN'))
    p.catch_deg = float(g('DOCK_CLIP_CATCH_DEG'))
    p.land = float(g('DOCK_CLIP_LAND'))
    p.leadin_deg = float(g('DOCK_CLIP_LEADIN_DEG'))
    p.embed = float(g('DOCK_CLIP_EMBED'))
    p.back_wall = str(_get(cfg, 'DOCK_CLIP_BACK_WALL', 'inner') or 'inner')

    # connector body
    if p.conn_type == 'pogo5':
        p.cw = float(g('DOCK_CONN_W'))
        p.ch = float(g('DOCK_CONN_H'))
        p.cd = float(g('DOCK_CONN_D'))
        p.pin_pitch = float(g('POGO5_PITCH'))
        pinout = list(g('CONNECTOR_PINOUT'))
        p.tab_w, p.tab_h = 0.0, 0.0
    elif p.conn_type == 'jst_sh4':
        p.cw = float(g('DOCK_JST_W'))
        p.ch = float(g('DOCK_JST_H'))
        p.cd = float(g('DOCK_JST_D'))
        p.pin_pitch = float(g('JST_SH4_PITCH'))
        pinout = list(g('JST_SH4_PINOUT'))
        p.tab_w = float(g('DOCK_JST_TAB_W'))
        p.tab_h = float(g('DOCK_JST_TAB_H'))
    elif p.conn_type == 'usbc':
        # geometry/usbc.py passes the well (incl. its entry chamfer) as the
        # "connector" envelope; it cuts and validates its own features
        p.cw = float(g('DOCK_CONN_W'))
        p.ch = float(g('DOCK_CONN_H'))
        p.cd = float(g('DOCK_CONN_D'))
        p.pin_pitch = 1.0
        pinout = list(_get(cfg, 'USBC_M_PADS', None) or ['V', 'D-', 'D+', 'G'])
        p.tab_w, p.tab_h = 0.0, 0.0
    else:
        raise ValueError(f"DOCK_CONN_TYPE must be 'pogo5', 'jst_sh4' or 'usbc', got {p.conn_type!r}")
    p.pinout = pinout
    n = len(pinout)
    # pin 1 at the -X end (typist's left), pins along +X
    p.pin_x = [(i - (n - 1) / 2.0) * p.pin_pitch for i in range(n)]

    # body
    p.y_front = -p.center_y + p.setback
    p.y_back = p.y_front + p.D
    p.hw = p.W / 2.0
    p.plug_cx = [(i - (p.keys - 1) / 2.0) * p.pitch for i in range(p.keys)]

    # connector pocket (cross-section W+2c x H+2c, face flush + PROUD)
    p.proud = float(g('DOCK_CONN_PROUD'))
    p.pw = p.cw + 2 * p.clr
    p.ph = p.ch + 2 * p.clr
    p.pz0 = p.conn_z - p.ph / 2.0
    p.pz1 = p.conn_z + p.ph / 2.0
    p.y_face = p.y_front - p.proud                  # connector mating face
    p.y_pb = p.y_front + p.cd - p.proud             # pocket bottom (stop)
    p.rib_h = float(g('DOCK_CONN_RIB_H'))
    p.rib_r = float(g('DOCK_CONN_RIB_R'))
    stop = float(g('DOCK_CONN_STOP'))
    stop_z = float(g('DOCK_CONN_STOP_Z'))
    p.neck_hw = p.pw / 2.0 - stop
    p.neck_z0 = p.pz0 + stop_z
    p.neck_z1 = p.pz1 - stop_z
    p.neck_d = float(g('DOCK_CONN_NECK_D'))
    p.conn_min_wall = float(g('DOCK_CONN_MIN_WALL'))
    # crush ribs: centred on the part of the end wall above the JST nail relief
    p.rib_zc = (p.pz0 + p.pz1) / 2.0 if p.tab_w <= 0 else (p.pz0 + p.tab_h + p.clr + p.pz1) / 2.0

    # snap-lip vertical profile (z of catch top, lip bottom); side clearance
    p.side_clr = (p.cut - p.s) / 2.0
    tc = math.tan(math.radians(p.catch_deg))
    if p.catch_deg > 0.5:
        # the catch face touches the plate's lower edge (side_clr outside the
        # plug wall) exactly when the body sits on the plate
        p.z_catch = -p.plate_t + p.side_clr * tc
    else:
        p.z_catch = -p.plate_t - 0.05
    p.z_lip_full = p.z_catch - p.lip * tc
    p.z_land = p.z_lip_full - p.land
    p.z_lip_bot = p.z_land - p.lip / math.tan(math.radians(p.leadin_deg))
    p.z_root = p.H - p.clip_root_skin

    # wire cavity + holes (one hole per plug, on the side toward x = 0, front half)
    p.hole_r = p.hole_d / 2.0
    p.holes = []
    for cx in p.plug_cx:
        sg = -1.0 if cx > 1e-9 else 1.0          # toward the centre (+X for a centred plug)
        hx = cx + sg * (p.s / 2.0 - p.wall - p.hole_r - 0.1)
        hy = -p.s / 2.0 + p.wall + p.hole_r + 0.2
        p.holes.append((hx, hy))
    p.cav_floor = float(g('DOCK_CAV_FLOOR'))
    p.cav_roof_z = p.H - float(g('DOCK_CAV_ROOF'))
    margin = float(g('DOCK_CAV_MARGIN'))
    p.cav_y0 = p.y_pb + p.neck_d - 0.01
    hole_reach_x = max((abs(hx) + p.hole_r + margin for hx, _ in p.holes), default=0.0)
    hole_reach_y = max((hy + p.hole_r + margin for _, hy in p.holes), default=p.cav_y0)
    pin_reach = max(abs(x) for x in p.pin_x) + 3.0
    p.cav_hw = max(hole_reach_x, pin_reach)
    p.cav_y1 = max(hole_reach_y, p.cav_y0 + float(g('DOCK_CAV_MIN_D')))

    # rear wire channel
    p.ch_w = float(g('DOCK_REAR_CH_W'))
    p.ch_h = float(g('DOCK_REAR_CH_H'))

    # pin-1 marker
    p.mark_depth = float(g('DOCK_MARK_DEPTH'))
    p.mark_size = float(g('DOCK_MARK_SIZE'))
    p.seg = int(g('DOCK_SEGMENTS'))

    # OLED cover clearance (cover underside = top - OLED_COVER_T)
    cover = _get(cfg, 'OLED_COVER')
    p.cover_y0_local = float(cover[1]) - p.center_y
    p.cover_clear_h = float(g('OLED_COVER_TOP_Z')) - float(g('OLED_COVER_T')) - p.kb_h

    _layout_clips(p)
    _validate(p)
    return p


def _layout_clips(p):
    """Place the snap blades.

    Each blade is a dict with:
      axis     'y' (front wall, normal along y) or 'x' (inner wall)
      w_out    outer-face coordinate along the normal
      sg       outward sign (+1 / -1) along the normal
      t0, t1   tangential range
    """
    p.blades = []
    hs = p.s / 2.0
    for cx in p.plug_cx:
        side = 1.0 if cx >= 0 else -1.0          # which half of the dock
        # (1) front wall, outer half: blade ends one slot before the outer
        #     wall's inner face, and must stay clear of the connector pocket
        t_out = cx + side * (hs - p.wall - p.clip_slot)
        w = p.clip_w
        pocket_edge = p.pw / 2.0
        while True:
            t_in = t_out - side * w
            slot_in = t_in - side * p.clip_slot
            if side * slot_in - pocket_edge >= 0.45 or w < 2.0:
                break
            w -= 0.1
        if w < 2.0:
            raise ValueError("front snap blade does not fit between the connector pocket "
                             "and the plug's outer wall - narrow DOCK_CONN_W or DOCK_CLIP_W")
        t0, t1 = sorted((t_in, t_out))
        p.blades.append(dict(axis='y', w_out=-hs, sg=-1.0, t0=t0, t1=t1, plug=cx, wall='front'))
        # (2b) back wall, outer half (DOCK_CLIP_BACK_WALL='back': the USB-C
        #      dock's female board covers the web between the plugs). The
        #      under-plate cavity reaches ~1.1 mm behind the cut-outs, more
        #      than the lip needs (lip - side clearance = 0.375)
        if p.back_wall == 'back':
            t_in = t_out - side * p.clip_w
            t0, t1 = sorted((t_in, t_out))
            p.blades.append(dict(axis='y', w_out=hs, sg=1.0, t0=t0, t1=t1, plug=cx, wall='back'))
            continue
        # (2) wall facing x = 0 (the web), back half
        if abs(cx) > 1e-9:
            w_out = cx - side * hs
            sg = -side
            t1 = hs - p.wall - p.clip_slot
            t0 = t1 - p.clip_w
            p.blades.append(dict(axis='x', w_out=w_out, sg=sg, t0=t0, t1=t1, plug=cx, wall='inner'))
    p.clip_w_front = min(b['t1'] - b['t0'] for b in p.blades if b['wall'] == 'front')


def _validate(p):
    err = []
    if not p.s < p.cut:
        err.append(f"DOCK_PLUG_SIZE {p.s} must be smaller than DOCK_SWITCH_CUTOUT {p.cut}")
    if p.side_clr > p.lip - 0.1:
        err.append("DOCK_CLIP_LIP must exceed the plug side clearance by >= 0.1 mm")
    cell = p.keys * p.pitch
    if p.W > cell - 2 * p.key_clear + 1e-9:
        err.append(f"DOCK_BODY_W {p.W} touches the neighbouring keycaps "
                   f"(max {cell - 2 * p.key_clear:.2f} = {p.keys} x {p.pitch} - 2 x {p.key_clear})")
    for cx in p.plug_cx:
        if abs(cx) + p.s / 2.0 > p.hw - 0.5:
            err.append(f"plug at x={cx:.3f} sticks out of the body sides")
    if -p.s / 2.0 < p.y_front + 1.0:
        err.append("plugs reach the body front face - DOCK_FRONT_SETBACK / DOCK_SWITCH_CENTER_Y")
    if p.y_front < -p.center_y - 1e-9:
        err.append("dock front face would overhang the keyboard front edge")
    if p.depth - p.plate_t > p.gap_under - 0.5:
        err.append(f"DOCK_PLUG_DEPTH {p.depth} leaves < 0.5 mm above the main PCB")
    if p.z_lip_bot < -p.depth + 0.3:
        err.append("snap lip does not fit on the plug - increase DOCK_PLUG_DEPTH or reduce the lip")
    if p.conn_type == 'usbc':          # geometry/usbc.py checks its own features
        if p.y_back > p.cover_y0_local and p.H > p.cover_clear_h - 1.0:
            err.append("dock body reaches under the OLED cover and is too tall for it")
        if err:
            raise ValueError("dock config invalid:\n  - " + "\n  - ".join(err))
        return
    if p.pz0 < p.conn_min_wall - 1e-9 or p.pz1 > p.H - p.conn_min_wall - 0.4:
        err.append(f"connector pocket z {p.pz0:.2f}..{p.pz1:.2f} does not fit in the "
                   f"{p.H} mm body - DOCK_CONN_Z / DOCK_BODY_H")
    if p.pw / 2.0 + max(p.tab_w / 2.0 - p.cw / 2.0, 0.0) > p.hw - 2.0:
        err.append("connector pocket too wide for the body")
    if p.y_pb + p.neck_d + 1.0 > p.y_back:
        err.append("connector deeper than the body")
    if p.cav_roof_z - p.cav_floor < 2.0:
        err.append("wire cavity lower than 2 mm - DOCK_BODY_H too small")
    if p.cav_hw > p.neck_hw and p.conn_type == 'pogo5' and p.cav_hw > p.pw / 2.0 - 0.3:
        err.append("wire cavity wider than the connector stop")
    if p.cav_y1 > p.y_back - 1.0:
        err.append("wire cavity reaches the back face")
    if p.y_back > p.cover_y0_local and p.H > p.cover_clear_h - 1.0:
        err.append("dock body reaches under the OLED cover and is too tall for it")
    for hx, hy in p.holes:
        cx = min(p.plug_cx, key=lambda c: abs(c - hx))
        if not (abs(hx - cx) + p.hole_r <= p.s / 2.0 - p.wall + 1e-9
                and abs(hy) + p.hole_r <= p.s / 2.0 - p.wall + 1e-9):
            err.append(f"DOCK_WIRE_HOLE {p.hole_d} does not fit inside the hollow plug")
    if err:
        raise ValueError("dock config invalid:\n  - " + "\n  - ".join(err))


# ---------------------------------------------------------------------------
# primitives (manifold3d)
# ---------------------------------------------------------------------------

def _box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def _cs(points):
    """CrossSection from one ring; fixes orientation (manifold wants CCW)."""
    pts = [(float(a), float(b)) for a, b in points]
    area = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        area += x0 * y1 - x1 * y0
    if area < 0:
        pts = pts[::-1]
    return CrossSection([pts])


def _prism_y(cs_xz, y0, y1):
    """Extrude a profile drawn in (x, z) along +Y from y0 to y1 (proper rotation)."""
    m = Manifold.extrude(cs_xz, y1 - y0)
    return m.transform([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0]])


def _prism_x(cs_yz, x0, x1):
    """Extrude a profile drawn in (y, z) along +X from x0 to x1 (proper rotation)."""
    m = Manifold.extrude(cs_yz, x1 - x0)
    return m.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def _rounded_rect_ring(cx, cy, hw, hd, r, n=10):
    pts = []
    corners = [(cx + hw - r, cy + hd - r, 0.0), (cx - hw + r, cy + hd - r, 90.0),
               (cx - hw + r, cy - hd + r, 180.0), (cx + hw - r, cy - hd + r, 270.0)]
    for ox, oy, a0 in corners:
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def _edge_inset(h, R):
    """'Printable round' profile: inset from the side face at distance h below
    the top. A quarter round from the side face up to 45 degrees, then a 45
    degree chamfer into the top face (a safe overhang when printed top-down)."""
    h45 = R * (1.0 - math.sqrt(0.5))
    if h >= R:
        return 0.0
    if h >= h45:
        return R - math.sqrt(max(R * R - (R - h) ** 2, 0.0))
    return 2.0 * h45 - h


def _body(p):
    """Convex rounded block = hull of plan rings stacked along the edge profile."""
    cy = (p.y_front + p.y_back) / 2.0
    hd = p.D / 2.0
    R = min(p.R, p.H - 0.5, p.hw - 0.5, hd - 0.5)
    rp = R                                              # plan corner radius
    h45 = R * (1.0 - math.sqrt(0.5))
    hs = [R] + [R - (R - h45) * k / 8.0 for k in range(1, 9)] + [0.0]
    pts = []
    for z, d in [(0.0, 0.0)] + [(p.H - h, _edge_inset(h, R)) for h in hs]:
        for x, y in _rounded_rect_ring(0.0, cy, p.hw - d, hd - d, rp - d):
            pts.append((x, y, z))
    return Manifold.hull_points(pts)


# ---------------------------------------------------------------------------
# features
# ---------------------------------------------------------------------------

def _plugs(p):
    hs = p.s / 2.0
    solids, cutters = [], []
    for cx in p.plug_cx:
        plug = _box(cx - hs, cx + hs, -hs, hs, -p.depth, 0.5)
        # never poke out of the body above the plate (back face is flat for
        # aesthetics; with DOCK_BODY_D < 18.9 the plug back would sit behind it)
        if hs > p.y_back:
            plug = plug - _box(cx - hs - 1, cx + hs + 1, p.y_back, hs + 1, 0.0, 1.0)
        if -hs < p.y_front:
            plug = plug - _box(cx - hs - 1, cx + hs + 1, -hs - 1, p.y_front, 0.0, 1.0)
        solids.append(plug)
        iw = hs - p.wall
        cutters.append(_box(cx - iw, cx + iw, -iw, iw, -p.depth - 1.0, 0.0))
    return solids, cutters


def _nt_box(b, n0, n1, t0, t1, z0, z1):
    """Box given in blade coordinates (n = outward normal distance from the
    plug outline, t = tangential)."""
    c0, c1 = sorted((b['w_out'] + b['sg'] * n0, b['w_out'] + b['sg'] * n1))
    if b['axis'] == 'y':
        return _box(t0, t1, c0, c1, z0, z1)
    return _box(c0, c1, t0, t1, z0, z1)


def _blade_cutters(p, b):
    T, G, RL, S = p.clip_t, p.clip_gap, p.clip_relief, p.clip_slot
    z0, z1 = -p.depth - 1.0, p.z_root
    return [
        _nt_box(b, -T - RL, G, b['t0'] - S, b['t0'], z0, z1),   # side slot
        _nt_box(b, -T - RL, G, b['t1'], b['t1'] + S, z0, z1),   # side slot
        _nt_box(b, 0.0, G, b['t0'], b['t1'], z0, z1),           # outer gap (z > 0 matters)
        _nt_box(b, -T - RL, -T, b['t0'], b['t1'], z0, z1),      # relief behind the blade
    ]


def _lip(p, b):
    L = p.lip
    prof_nz = [(-p.embed, p.z_catch), (0.0, p.z_catch), (L, p.z_lip_full),
               (L, p.z_land), (0.0, p.z_lip_bot), (-p.embed, p.z_lip_bot)]
    prof = [(b['w_out'] + b['sg'] * n, z) for n, z in prof_nz]
    t0, t1 = b['t0'] + 0.1, b['t1'] - 0.1
    if b['axis'] == 'y':
        return _prism_x(_cs(prof), t0, t1)
    return _prism_y(_cs(prof), t0, t1)


def _connector_cutters(p):
    cut = []
    hw = p.pw / 2.0
    # pocket profile in (x, z) with half-round crush ribs on the end walls
    pocket = CrossSection.square((p.pw, p.ph)).translate((-hw, p.pz0))
    if p.tab_w > 0:      # JST fitting-nail relief along the pocket bottom
        tw = p.tab_w / 2.0 + p.clr
        pocket = pocket + CrossSection.square((2 * tw, p.tab_h + p.clr)).translate((-tw, p.pz0))
    if p.rib_h > 0:
        zc = p.rib_zc
        for sx in (-1.0, 1.0):
            # rib centre outside the end wall so it protrudes rib_h into the pocket
            rib = CrossSection.circle(p.rib_r, 24).translate((sx * (hw + p.rib_r - p.rib_h), zc))
            pocket = pocket - rib
    # pocket runs from 1 mm in front of the face to the stop
    cut.append(_prism_y(pocket, p.y_front - 1.0, p.y_pb))
    # neck: stop ledge window into the wire cavity
    cut.append(_box(-p.neck_hw, p.neck_hw, p.y_pb - 0.01, p.y_pb + p.neck_d,
                    p.neck_z0, p.neck_z1))
    # wire cavity
    cut.append(_box(-p.cav_hw, p.cav_hw, p.cav_y0, p.cav_y1, p.cav_floor, p.cav_roof_z))
    # wire holes into the plugs (and the gap under the switchplate)
    for hx, hy in p.holes:
        cyl = Manifold.cylinder(p.cav_floor + 0.8, p.hole_r, p.hole_r, p.seg)
        cut.append(cyl.translate((hx, hy, -0.5)))
    # rear channel: open bottom, over the web between the plugs, out of the back
    cut.append(_box(-p.ch_w / 2.0, p.ch_w / 2.0, p.cav_y1 - 1.0, p.y_back + 1.0,
                    -1.0, p.ch_h))
    return cut


def _marker(p):
    """Pin-1 triangle on the top face, pointing at the front (connector) face."""
    x1 = p.pin_x[0]
    a = p.mark_size
    y_tip = p.y_front + 1.9
    tri = _cs([(x1, y_tip), (x1 + a / 2.0, y_tip + a), (x1 - a / 2.0, y_tip + a)])
    return Manifold.extrude(tri, p.mark_depth + 1.0).translate((0.0, 0.0, p.H - p.mark_depth))


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def _to_trimesh(m):
    status = str(m.status())
    if not status.endswith('NoError'):
        raise RuntimeError(f"manifold3d error while building the dock: {status}")
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    f = np.asarray(mesh.tri_verts, dtype=np.int64)
    tm = trimesh.Trimesh(vertices=v, faces=f, process=True)
    return tm


def build_dock(cfg):
    """Build the dock.

    Returns (mesh_local, print_T):
      mesh_local  trimesh.Trimesh in the dock-local assembled frame (module doc)
      print_T     4x4 float64; mesh_local.apply_transform(print_T) gives the
                  support-free print orientation (top face on the bed, z >= 0,
                  bbox centred on x = y = 0)
    """
    p = _params(cfg)
    solid = _body(p)
    plug_solids, plug_cutters = _plugs(p)
    solid = Manifold.batch_boolean([solid] + plug_solids, _optype('Add'))
    cutters = plug_cutters + _connector_cutters(p) + [_marker(p)]
    for b in p.blades:
        cutters += _blade_cutters(p, b)
    solid = solid - Manifold.batch_boolean(cutters, _optype('Add'))
    solid = Manifold.batch_boolean([solid] + [_lip(p, b) for b in p.blades], _optype('Add'))
    mesh = _to_trimesh(solid)

    # print orientation: 180 deg about X (top face down), then drop on z = 0
    # and centre the XY bounding box on the origin
    R = np.diag([1.0, -1.0, -1.0, 1.0])
    v = trimesh.transform_points(mesh.vertices, R)
    lo, hi = v.min(axis=0), v.max(axis=0)
    T = np.eye(4)
    T[:3, 3] = [-(lo[0] + hi[0]) / 2.0, -(lo[1] + hi[1]) / 2.0, -lo[2]]
    print_T = T @ R
    return mesh, print_T


def _optype(name):
    from manifold3d import OpType
    return getattr(OpType, name)


def dock_info(cfg):
    """Key dimensions for the manifest / preview / cable endpoint (dock-local,
    mm, JSON-serialisable)."""
    p = _params(cfg)
    r = lambda v: round(float(v), 4)  # noqa: E731
    L_free = p.z_root - (p.z_catch + p.z_lip_full) / 2.0
    defl = p.lip - p.side_clr
    strain = 1.5 * p.clip_t * defl / (L_free * L_free)
    return {
        'frame': ("dock-local: origin = midpoint of the removed switch centres on the "
                  "switchplate top; +X right, +Y toward keyboard back, +Z up"),
        'origin_keyboard_local': [r(p.center_x), r(p.center_y), r(p.kb_h)],
        'connector_type': p.conn_type,
        'connector_face_center': [0.0, r(p.y_face), r(p.conn_z)],
        'connector_face_normal': [0.0, -1.0, 0.0],
        'connector_body': [r(p.cw), r(p.ch), r(p.cd)],
        'connector_pocket': {'w': r(p.pw), 'h': r(p.ph), 'depth': r(p.cd - p.proud),
                             'z0': r(p.pz0), 'z1': r(p.pz1),
                             'crush_rib': r(p.rib_h), 'clearance': r(p.clr)},
        'connector_pins': [{'pin': i + 1, 'signal': s, 'x': r(x)}
                           for i, (s, x) in enumerate(zip(p.pinout, p.pin_x))],
        'pin1_side': '-X (typist left)',
        'body': {'w': r(p.W), 'd': r(p.D), 'h': r(p.H), 'r': r(p.R),
                 'x0': r(-p.hw), 'x1': r(p.hw), 'y0': r(p.y_front), 'y1': r(p.y_back),
                 'z0': 0.0, 'z1': r(p.H)},
        'keyboard_front_y': r(-p.center_y),
        'plug_size': r(p.s),
        'plug_depth': r(p.depth),
        'plug_wall': r(p.wall),
        'plug_centers': [[r(cx), 0.0, 0.0] for cx in p.plug_cx],
        'switch_cutout': r(p.cut),
        'clips': {'count': len(p.blades), 'lip': r(p.lip), 'thickness': r(p.clip_t),
                  'width_front': r(p.clip_w_front), 'width_inner': r(p.clip_w),
                  'root_z': r(p.z_root), 'catch_deg': r(p.catch_deg),
                  'free_length': r(L_free), 'deflection': r(defl),
                  'root_strain_pct': r(100.0 * strain),
                  'walls': sorted({b['wall'] for b in p.blades})},
        'wire_holes': [[r(hx), r(hy)] for hx, hy in p.holes],
        'wire_hole_d': r(p.hole_d),
        'wire_cavity': {'x0': r(-p.cav_hw), 'x1': r(p.cav_hw), 'y0': r(p.cav_y0),
                        'y1': r(p.cav_y1), 'z0': r(p.cav_floor), 'z1': r(p.cav_roof_z)},
        'rear_channel': {'w': r(p.ch_w), 'h': r(p.ch_h), 'exit_y': r(p.y_back)},
        'clearance_to_oled_cover_y': r(p.cover_y0_local - p.y_back),
        'clearance_to_neighbour_keycell': r(p.keys * p.pitch / 2.0 - p.hw),
        'print_orientation': ("upside down: top face on the bed (180 deg about X); "
                              "no supports; PETG recommended for the snap blades"),
    }
