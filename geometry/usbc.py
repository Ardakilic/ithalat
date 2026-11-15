"""USB-C connector variant ('usbc' in CONNECTORS).

A cheap female USB-C breakout (blue board, pads G D D V) sits in the keyboard
dock; a male breakout (green board, plug on its front edge, pads V D- D+ G)
sits in a printed grip on the rest's pigtail. USB-C needs 5-20 N to plug in
and 8-20 N to pull out. The wire solder joints never carry that force, and the
user holds the grip itself. The connectors' own mounting joints are kept out
of the load path as far as printed parts can:

* the receptacle mouth is flush with the floor of a chamfered WELL in the dock
  face; the grip's NOSE enters the well with USBC_WELL_CLEARANCE per side, so
  side loads go into printed walls after ~1.5 deg of tilt;
* the female board is CAPTURED: its front edge bears on a 1.5 mm shoulder (the
  shell passes through a window in it, centred by two vertical crush ribs) -
  that takes the pull; its rear edge bears on a rear stop wall - that takes the
  push; a printed RETAINER, screwed down with 2 x M2x4, holds it down, closes
  the window and presses the receptacle shell onto the board with half-round
  ribs, so pitch moments bear on plastic instead of the shell's legs;
* the retainer also carries two LOCK PRONGS that slide into the gaps behind the
  dock's two back clip blades (backed by a rib below the plate), so the clips
  cannot let go while it is fitted (the 30 degree catch alone already gives
  margin >= 1.5, see retention());
* the GRIP is a two-piece clamshell split at the male board's bottom face,
  closed by 2 M2x4 screws from below (2 alignment pegs where they fit). The
  plug shell is bonded into an epoxy key groove in the nose, so the pull goes
  grip -> epoxy -> shell; a push rib behind the board takes the insertion
  force, crush ribs under the board's edge strips clamp it whatever the layer
  rounding, a collar stops the board's front corners, and the wires are pinched
  over the rib and again in a slot behind it (zig-zag) before they leave the
  grip's underside straight above the rest's notch.

Frames: the dock and the retainer are built in the dock-local frame of
geometry/dock.py (origin between the removed switch centres on the plate top,
+X right, +Y toward the keyboard back, +Z up). The grip is built in the same
frame in its MATED position, so the dock placement translation puts every
part (and every hardware box) into the assembly frame.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import shapely
import shapely.affinity
import trimesh
from manifold3d import Manifold, OpType
from shapely.geometry import Polygon

from geometry import common as C
from geometry import connectors as CN
from geometry import dock as DK
from geometry import plug as PL

SQ2 = math.sqrt(2.0)


class _Over:
    """Config proxy: names in `over` win over the wrapped config."""

    def __init__(self, cfg, over):
        self._c, self._o = cfg, dict(over)

    def __getattr__(self, n):
        if n.startswith("__"):
            raise AttributeError(n)
        if n in self._o:
            return self._o[n]
        return getattr(self._c, n)


def chamfer_rect(cx, cz, w, h, c):
    """Rectangle (x, z) centred on (cx, cz) with 45 degree corner chamfers c."""
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2
    c = max(0.0, min(c, w / 2 - 1e-3, h / 2 - 1e-3))
    if c <= 0:
        return shapely.box(x0, z0, x1, z1)
    return Polygon([(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c),
                    (x1 - c, z1), (x0 + c, z1), (x0, z1 - c), (x0, z0 + c)])


def _box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def _prism_y(poly_xz, y0, y1):
    return DK._prism_y(C.to_cross_section(poly_xz), y0, y1)


def _hull_y(*sections):
    """Convex hull of (poly_xz, y) sections (one solid: no shared faces)."""
    pts = []
    for poly, y in zip(sections[0::2], sections[1::2]):
        xz = np.asarray(poly.exterior.coords)[:-1]
        pts.append(np.column_stack([xz[:, 0], np.full(len(xz), float(y)), xz[:, 1]]))
    return Manifold.hull_points(np.vstack(pts))


def _loft_y(*sections):
    """Closed solid through (poly_xz, y) sections of convex polygons that share
    a centre and a vertex count (e.g. mitre offsets of one polygon): rings
    joined by quads, end caps fanned. Unlike a hull it may be non-convex (a
    funnel), and unlike a union it has no internal / coincident faces."""
    rings = []
    cx, cz = sections[0].centroid.x, sections[0].centroid.y
    for poly, y in zip(sections[0::2], sections[1::2]):
        xz = np.asarray(poly.exterior.coords)[:-1]
        order = np.argsort(np.arctan2(xz[:, 1] - cz, xz[:, 0] - cx))
        xz = xz[order]
        rings.append(np.column_stack([xz[:, 0], np.full(len(xz), float(y)), xz[:, 1]]))
    n = len(rings[0])
    if any(len(r) != n for r in rings):
        raise ValueError("loft sections need the same vertex count")
    verts = np.vstack(rings + [r.mean(axis=0, keepdims=True) for r in (rings[0], rings[-1])])
    faces = []
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces += [(a + i, a + j, b + j), (a + i, b + j, b + i)]
    c0, c1 = len(rings) * n, len(rings) * n + 1
    last = (len(rings) - 1) * n
    for i in range(n):
        j = (i + 1) % n
        faces += [(c0, a_, b_) for a_, b_ in [(j, i)]]
        faces += [(c1, last + i, last + j)]
    faces = np.asarray(faces, dtype=np.int64)
    tm = trimesh.Trimesh(verts, faces, process=False)
    if tm.volume < 0:
        faces = faces[:, ::-1]
    return C.manifold_from_arrays(verts, faces)


def _cyl_x(x0, x1, y, z, r, segs=48):
    return Manifold.cylinder(x1 - x0, r, r, segs).rotate((0.0, 90.0, 0.0)).translate((x0, y, z))


def _cyl_z(x, y, z0, z1, r, segs=40):
    return Manifold.cylinder(z1 - z0, r, r, segs).translate((x, y, z0))


def _union(parts):
    parts = [p for p in parts if p is not None and not p.is_empty()]
    return Manifold.batch_boolean(parts, OpType.Add) if parts else Manifold()


def _mitre(poly, d):
    return poly.buffer(d, join_style="mitre", mitre_limit=10.0)


# ---------------------------------------------------------------------------
# parameters (every number derived once from config.py)
# ---------------------------------------------------------------------------

def params(cfg):
    g = lambda n: getattr(cfg, n)  # noqa: E731
    P = SimpleNamespace()
    P.embed = float(g("USBC_EMBED"))
    P.nudge = float(g("USBC_NUDGE"))
    # boards / hardware (measure your boards: config.py USBC_*)
    P.fW, P.fL, P.fT = (float(v) for v in g("USBC_F_BOARD"))
    P.sW, P.sH, P.sL = (float(v) for v in g("USBC_F_SHELL"))
    P.f_proud = float(g("USBC_F_SHELL_PROUD"))
    P.f_sink = float(g("USBC_F_SHELL_SINK"))
    P.f_shell_x = float(g("USBC_F_SHELL_X"))
    P.f_relief = float(g("USBC_F_LEG_RELIEF"))
    P.f_rim = float(g("USBC_F_RIM"))
    P.f_depth = float(g("USBC_F_DEPTH"))
    P.f_legs_l = float(g("USBC_F_LEGS_L"))
    P.f_pad_l = float(g("USBC_F_PAD_L"))
    P.mW, P.mL, P.mT = (float(v) for v in g("USBC_M_BOARD"))
    P.msW, P.msH = (float(v) for v in g("USBC_M_SHELL"))
    P.ms_r = float(g("USBC_M_SHELL_R"))
    P.m_plug_l = float(g("USBC_M_PLUG_L"))
    P.m_pad_l = float(g("USBC_M_PAD_L"))
    P.m_tail_h = float(g("USBC_M_TAIL_H"))
    P.m_joint_h = float(g("USBC_M_JOINT_H"))
    P.m_rim = float(g("USBC_M_RIM"))
    P.m_tab_l = max(0.0, float(g("USBC_M_TAB_L")))
    P.d_len, P.d_dia = (float(v) for v in g("USBC_DIODE"))
    P.d_clr = float(g("USBC_DIODE_CLEARANCE"))
    P.d_lift = float(g("USBC_DIODE_LIFT"))
    P.d_roof = float(g("USBC_DIODE_ROOF"))
    P.wire_d = float(g("CABLE_WIRE_D"))

    # dock frame
    P.conn_z = float(g("USBC_CONN_Z"))
    P.H = float(g("USBC_DOCK_H"))
    P.D = float(g("USBC_DOCK_D"))
    P.R = float(g("USBC_DOCK_R"))
    P.kb_front = -float(g("DOCK_SWITCH_CENTER_Y"))
    P.y_front = P.kb_front + float(g("DOCK_FRONT_SETBACK"))
    P.y_back = P.y_front + P.D
    P.plate_t = float(g("DOCK_PLATE_T"))
    P.sag = max(0.0, float(g("USBC_BRIDGE_SAG")))

    # grip nose and the matching well (sections in x, z)
    clr = float(g("USBC_GRIP_CAV_CLEARANCE"))
    P.cav_clr = clr
    P.bclr = float(g("USBC_BOARD_CLEARANCE"))          # board pockets (both boards)
    P.cav_w = max(P.msW + 2 * clr, P.mW + 2 * P.bclr)
    P.cav_h = max(P.msH, P.mT + 2 * P.m_tail_h) + 2 * clr
    P.cav_ch = float(g("USBC_GRIP_CAV_CHAMFER"))
    P.nose_wall = float(g("USBC_GRIP_NOSE_WALL"))
    P.nose_w = P.cav_w + 2 * P.nose_wall
    # grip body z range; the nose's bottom is flush with the body's bottom so
    # the lower half prints flat without an overhang (the nose is taller below)
    P.z_gb = P.conn_z - float(g("USBC_GRIP_BELOW"))
    P.z_gt = P.conn_z + float(g("USBC_GRIP_ABOVE"))
    P.nose_z0 = P.z_gb
    P.nose_z1 = P.conn_z + P.cav_h / 2.0 + P.nose_wall
    P.nose_h = P.nose_z1 - P.nose_z0
    P.nose_ch = float(g("USBC_GRIP_NOSE_CHAMFER"))
    P.nose_li = float(g("USBC_GRIP_NOSE_LEADIN"))
    P.nose_poly = chamfer_rect(0.0, (P.nose_z0 + P.nose_z1) / 2.0, P.nose_w, P.nose_h, P.nose_ch)
    P.well_clr = float(g("USBC_WELL_CLEARANCE"))
    # the well = the nose + clearance; its bottom wall prints as a bridge that
    # sags into the well, so it sits USBC_BRIDGE_SAG lower (hull keeps 8 corners)
    wp = _mitre(P.nose_poly, P.well_clr)
    P.well_poly = shapely.convex_hull(shapely.union(wp, shapely.affinity.translate(wp, 0.0, -P.sag))) \
        if P.sag > 0 else wp
    st = g("USBC_SHOULDER_T")
    P.shoulder = float(st) if st is not None else max(float(g("USBC_SHOULDER_MIN_T")), P.f_proud)
    P.play = float(g("USBC_BOARD_PLAY"))
    wd = g("USBC_WELL_DEPTH")
    if wd is None:
        # auto: as deep as the rear stop behind the female board allows (rounded
        # down to 0.01 mm), within USBC_WELL_DEPTH_RANGE
        lo, hi = (float(v) for v in g("USBC_WELL_DEPTH_RANGE"))
        room = P.D - P.shoulder - P.fL - P.play - float(g("USBC_REAR_STOP_MIN"))
        wd = min(hi, max(lo, math.floor((room - 1e-9) * 100.0) / 100.0))
    P.well_auto = g("USBC_WELL_DEPTH") is None
    P.well_depth = max(0.0, float(wd))
    P.well_floor_min = float(g("USBC_WELL_FLOOR_MIN"))
    P.face_flat = float(g("USBC_FACE_FLAT_MIN"))
    P.well_ch = max(0.0, min(float(g("USBC_WELL_CHAMFER")), P.well_depth - P.face_flat))
    P.entry_poly = _mitre(P.well_poly, P.well_ch) if P.well_ch > 0 else P.well_poly
    # the entry chamfer never cuts closer than USBC_WELL_FLOOR_MIN to the plate
    # and stays on the flat face below the dock's top-edge round
    P.entry_clip = shapely.box(-50.0, P.well_floor_min, 50.0,
                               max(P.H - P.R - P.face_flat, P.well_poly.bounds[3]))
    P.entry_poly = P.entry_poly.intersection(P.entry_clip)
    wx0, wz0, wx1, wz1 = P.well_poly.bounds
    P.well_w, P.well_h, P.well_z0, P.well_z1 = wx1 - wx0, wz1 - wz0, wz0, wz1
    ex0, _, ex1, ez1 = P.entry_poly.bounds
    P.entry_hw, P.entry_z1 = ex1, ez1

    # shoulder, window, female board, receptacle
    P.y_wf = P.y_front + P.well_depth                    # well floor
    P.y_bf = P.y_wf + P.shoulder                         # shoulder back face = board front edge
    P.mouth_y = P.y_bf - P.f_proud
    P.recess = P.mouth_y - P.y_wf                        # + = mouth behind the well floor
    P.shell_bot = P.conn_z - P.sH / 2.0
    P.shell_top = P.conn_z + P.sH / 2.0
    P.shell_rear = P.mouth_y + P.sL
    P.z_b1 = P.shell_bot + P.f_sink                      # female board top
    P.z_b0 = P.z_b1 - P.fT
    P.xb = -P.f_shell_x                                  # board centre (shell on the axis)
    P.play = float(g("USBC_BOARD_PLAY"))
    P.y_pr = P.y_bf + P.fL + P.play                      # pocket rear = rear stop face
    P.rear_stop = P.y_back - P.y_pr
    P.bp_x0, P.bp_x1 = P.xb - P.fW / 2 - P.bclr, P.xb + P.fW / 2 + P.bclr
    P.win_c = float(g("USBC_WINDOW_CLEARANCE"))
    P.win_hw = P.sW / 2.0 + P.win_c
    # window floor = a bridge in print: USBC_BRIDGE_SAG lower; the shell rests on
    # the board, the retainer's ribs press it down, the side ribs centre it
    P.win_z0, P.win_z1 = P.shell_bot - P.win_c - P.sag, P.shell_top + P.win_c
    P.wrib_h, P.wrib_r = (float(v) for v in g("USBC_WINDOW_RIB"))
    P.wrib_y = (P.y_wf + P.y_bf) / 2.0
    P.ch_w = float(g("USBC_REAR_CH_W"))
    ch = g("USBC_REAR_CH_H")
    P.ch_top = float(ch) if ch is not None else P.z_b1 + float(g("USBC_REAR_CH_ABOVE_BOARD"))
    P.floor_min = min(P.z_b0 - P.f_relief, P.win_z0)     # thinnest floor over the plugs

    # clip blades: the pogo dock's machinery with USB-C overrides
    over = {"DOCK_BODY_H": P.H, "DOCK_BODY_D": P.D, "DOCK_BODY_R": P.R,
            "DOCK_CONN_Z": P.conn_z,
            "DOCK_CONN_TYPE": "usbc", "DOCK_CONN_W": 2 * P.entry_hw, "DOCK_CONN_H": P.well_h,
            "DOCK_CONN_D": max(P.well_depth, 0.01), "DOCK_CONN_CLEARANCE": 0.0, "DOCK_CONN_PROUD": 0.0,
            "DOCK_CLIP_CATCH_DEG": float(g("USBC_CLIP_CATCH_DEG")),
            "DOCK_CLIP_ROOT_SKIN": P.H - float(g("USBC_CLIP_ROOT_Z")),
            "DOCK_CLIP_RELIEF": float(g("USBC_CLIP_RELIEF")),
            "DOCK_CLIP_BACK_WALL": str(g("USBC_CLIP_BACK_WALL"))}
    P.dp = DK._params(_Over(cfg, over))
    dp = P.dp
    P.back_blades = [b for b in dp.blades if b["wall"] in ("back", "inner")]
    P.front_blades = [b for b in dp.blades if b["wall"] == "front"]

    # retainer + lock prongs
    P.ret = bool(g("USBC_RET_ENABLED"))
    P.lock = bool(g("USBC_LOCK")) and P.ret and all(b["wall"] == "back" for b in P.back_blades)
    P.rc = float(g("USBC_RET_CLEARANCE"))
    P.ret_t = float(g("USBC_RET_PLATE_T"))
    P.z_arm = P.H - P.ret_t                              # arm recess floor
    P.arm_w = float(g("USBC_RET_ARM_W"))
    P.ret_cav_h = float(g("USBC_RET_CAV_H"))
    P.bump = float(g("USBC_RET_BUMP"))
    P.bump_w = float(g("USBC_RET_BUMP_W"))
    bz0, bz1 = (float(v) for v in g("USBC_RET_BUMP_Z"))
    P.bump_z0, P.bump_z1 = dp.z_root + bz0, P.z_arm - bz1
    P.press, P.press_r, P.press_n = (float(v) for v in g("USBC_RET_SHELL_PRESS"))
    P.press_n = int(P.press_n)
    P.prong_t = float(g("USBC_LOCK_PRONG_T"))
    P.prong_back_clr = float(g("USBC_LOCK_BACK_CLR"))
    P.prong_below = float(g("USBC_LOCK_PRONG_BELOW"))
    P.prong_x_clr = float(g("USBC_LOCK_PRONG_X_CLR"))
    P.backing = float(g("USBC_LOCK_BACKING"))
    P.prongs = []
    for b in P.back_blades:
        if b["wall"] != "back":
            continue
        # relief gap behind the blade (outward normal +Y): y = w_out + n
        ry0 = b["w_out"] - dp.clip_t - dp.clip_relief
        ry1 = b["w_out"] - dp.clip_t
        y0 = ry0 + P.prong_back_clr
        P.prongs.append(dict(x0=b["t0"] + P.prong_x_clr, x1=b["t1"] - P.prong_x_clr,
                             y0=y0, y1=y0 + P.prong_t, gap=ry1 - (y0 + P.prong_t),
                             slot=(b["t0"], b["t1"], ry0, ry1), blade_back=ry1, blade=b))
    if P.prongs:
        P.arm_yc = sum((p["y0"] + p["y1"]) / 2.0 for p in P.prongs) / len(P.prongs)
        P.arm_x1 = max(max(abs(p["x0"]), abs(p["x1"])) for p in P.prongs)
    else:
        P.arm_yc = min(P.y_pr - P.arm_w / 2.0 - P.rc, (P.y_bf + P.y_pr) / 2.0)
        P.arm_x1 = P.bp_x1 - P.rc
    P.arm_y0, P.arm_y1 = P.arm_yc - P.arm_w / 2.0, P.arm_yc + P.arm_w / 2.0
    P.pry_w, P.pry_l, P.pry_d = (float(v) for v in g("USBC_PRY_NOTCH"))
    # retainer screws (positive hold-down) through round pads on the arms
    (P.rs_d, P.rs_pilot, P.rs_clear, P.rs_head, P.rs_cb, P.rs_depth) = (
        float(v) for v in g("USBC_RET_SCREW"))
    P.rs_l = float(g("USBC_RET_SCREW_L"))
    P.rs_pad_r = P.rs_head / 2.0 + float(g("DOCK_CONN_MIN_WALL"))
    slot_in = min((b["t0"] for b in P.back_blades if b["t0"] > 0), default=P.bp_x1 + 4.0) - dp.clip_slot
    rsx = g("USBC_RET_SCREW_X")
    P.rs_x = float(rsx) if rsx is not None else (P.bp_x1 + slot_in) / 2.0
    P.rs_slot_in = slot_in
    P.rs = [(-P.rs_x, P.arm_yc), (P.rs_x, P.arm_yc)] if P.ret else []
    # receptacle shell press ribs (under the retainer's shell channel)
    P.press_ys = []
    if P.ret and P.press_n > 0:
        P.press_ys.append(P.wrib_y)                      # over the window (the tongue)
        k = P.press_n - 1
        if k > 0:
            a, b = P.y_bf + P.press_r + P.rc, P.shell_rear - P.press_r - P.rc
            P.press_ys += [a + (b - a) * i / max(1, k - 1) for i in range(k)] if k > 1 else [(a + b) / 2.0]
    # diode cradle (in the retainer, over the board between the legs and the pads)
    P.d_r = P.d_dia / 2.0
    P.d_y = P.shell_rear + P.f_legs_l + P.d_clr + P.d_r
    P.d_z = P.z_b1 + P.d_lift + P.d_r
    P.d_x = 0.0
    P.f_pads_y0 = P.y_bf + P.fL - P.f_pad_l
    P.diode_fits = (P.ret
                    and P.d_y + P.d_r + P.d_clr <= P.f_pads_y0 + 1e-6
                    and P.d_len / 2 + P.d_clr <= P.fW / 2 - P.f_rim + 1e-6
                    and P.d_z + P.d_r + P.d_clr <= P.H - P.d_roof)

    # grip (mated)
    P.exposed = float(g("USBC_SHELL_EXPOSED"))
    P.y_tip = P.mouth_y + P.f_depth                     # seated plug tip
    P.y_nf = P.y_tip - P.exposed                        # nose face
    P.nose_gap = P.y_wf - P.y_nf                        # nose face -> well floor
    P.y_mb1 = P.y_tip - P.m_plug_l                      # male board front edge (plug rear)
    P.y_mb0 = P.y_tip - P.mL                            # male board rear edge
    P.gw = float(g("USBC_GRIP_W"))
    P.g_wall = float(g("USBC_GRIP_WALL"))
    P.y_gf = P.y_front - float(g("USBC_GRIP_FACE_GAP"))  # body front face
    P.y_rib1 = P.y_mb0 - float(g("USBC_GRIP_BOARD_GAP"))  # push rib front face
    P.y_rib0 = P.y_rib1 - float(g("USBC_GRIP_PUSH_RIB"))
    P.slot = P.wire_d - float(g("USBC_GRIP_WIRE_SQUEEZE"))
    P.band = float(g("USBC_GRIP_WIRE_BAND"))
    P.band_rib = max(P.band, P.mW - 2 * P.m_rim)        # over the rib: as wide as the pad row
    P.y_slot1 = P.y_rib0
    P.y_slot0 = P.y_rib0 - P.slot
    P.y_g0 = P.y_slot0 - P.g_wall                       # grip rear end
    P.z_s = P.conn_z - P.mT / 2.0                       # split plane = male board bottom
    P.squeeze = float(g("USBC_GRIP_BOARD_SQUEEZE"))
    P.z_pc = P.z_s + P.mT - P.squeeze                   # board pocket ceiling = rib top
    P.bw = P.mW / 2 + P.bclr                            # board pocket half-width
    P.y_jc = P.y_mb0 + P.m_pad_l + float(g("USBC_GRIP_JOINT_MARGIN"))  # joint cavity front
    P.y_tab = P.y_mb1 - P.m_tab_l                       # shell side tabs start here
    # clamp: crush ribs across the bottom half's seat under the board's edge
    # strips, where the top half's flat ceiling covers the strips
    P.crib_h, P.crib_n = (float(v) for v in g("USBC_GRIP_CLAMP_RIB"))
    P.crib_n = int(P.crib_n)
    P.layer = float(g("USBC_PRINT_LAYER"))
    P.clamp_y0, P.clamp_y1 = P.y_jc, P.y_tab
    # rib centres >= 2 radii from the zone ends (no faces shared with the reliefs)
    span = P.clamp_y1 - P.clamp_y0 - 4 * P.crib_h
    P.crib_ys = ([P.clamp_y0 + 2 * P.crib_h + span * (i / max(1, P.crib_n - 1) if P.crib_n > 1 else 0.5)
                  for i in range(P.crib_n)] if P.crib_h > 0 and P.crib_n > 0 and span >= 0 else [])
    # shell collar (board corner stop) and the epoxy key groove in front of it
    P.col_c, P.col_l = (float(v) for v in g("USBC_GRIP_COLLAR"))
    if P.col_l <= 0:
        P.col_l = 0.0
    P.col_hw = P.msW / 2.0 + (min(P.col_c, P.cav_clr) if P.col_l > 0 else P.cav_clr)
    P.col_ledge = max(0.0, P.mW / 2.0 - P.col_hw)       # board corner bearing width per side
    gd, gl, gg = (float(v) for v in g("USBC_GRIP_GLUE_GROOVE"))
    side_wall = P.nose_w / 2.0 - (P.msW / 2.0 + P.cav_clr)
    bot_wall = (P.conn_z - P.msH / 2.0 - P.cav_clr) - P.nose_z0
    P.glue_side = max(0.0, min(gd, side_wall - P.nose_wall - 0.05))
    P.glue_bot = max(0.0, min(gd, bot_wall - P.nose_wall - 0.05))
    P.glue_y0 = P.y_mb1 + P.col_l + gg
    P.glue_y1 = min(P.glue_y0 + gl, P.y_nf - P.nose_li - P.embed)
    P.glue = gl > 0 and gd > 0 and P.glue_y1 - P.glue_y0 > 0.3
    P.g_edge = float(g("USBC_GRIP_EDGE"))
    P.g_r = float(g("USBC_GRIP_R"))
    P.scr_d, P.scr_pilot, P.scr_clear, P.scr_head, P.scr_cb, P.scr_depth = (
        float(v) for v in g("USBC_GRIP_SCREW"))
    P.scr_l = float(g("USBC_GRIP_SCREW_L"))
    P.scr_x = float(g("USBC_GRIP_SCREW_X"))
    # screws beside the board's middle, kept inside the body (not the nose)
    P.scr_y_lo = P.y_g0 + P.g_wall + P.scr_head / 2.0
    P.scr_y_hi = P.y_gf - P.g_wall - P.scr_head / 2.0
    P.scr_y = min(max((P.y_mb0 + P.y_mb1) / 2.0, P.scr_y_lo), P.scr_y_hi)
    P.peg_d, P.peg_h, P.peg_fit = (float(v) for v in g("USBC_GRIP_PEG"))
    P.peg_hole_r = (P.peg_d + P.peg_fit) / 2.0
    P.peg_wall_min = float(g("USBC_GRIP_PEG_WALL"))
    cands = [P.y_g0 + P.g_wall + P.peg_hole_r, P.y_gf - P.g_wall - P.peg_hole_r]
    P.peg_y = max(cands, key=lambda y: abs(y - P.scr_y))
    dy = abs(P.peg_y - P.scr_y)
    P.peg_wall = dy - P.peg_hole_r - P.scr_pilot / 2.0           # top half: peg hole <-> pilot
    peg_root = dy - P.peg_d / 2.0 - P.scr_clear / 2.0            # bottom half: peg <-> clearance hole
    P.pegs = ([(-P.scr_x, P.peg_y), (P.scr_x, P.peg_y)]
              if P.peg_d > 0 and P.peg_wall >= P.peg_wall_min - 1e-9 and peg_root >= 0.0 else [])
    P.rd, P.rw, P.rp = (float(v) for v in g("USBC_GRIP_RIDGES"))
    rm = float(g("USBC_GRIP_RIDGE_MARGIN"))
    P.z_ridge0 = P.z_gb + max(P.scr_cb, P.g_edge) + rm
    P.z_ridge1 = P.z_gt - P.g_edge - rm
    _validate(P)
    return P


def _validate(P):
    err = []
    if P.rear_stop < 0.3:
        err.append(f"female board (USBC_F_BOARD L {P.fL:g}) does not fit the {P.D:g} mm USB-C dock: "
                   f"rear stop {P.rear_stop:.2f} mm - shorten USBC_WELL_DEPTH / USBC_SHOULDER_T or "
                   f"raise USBC_DOCK_D (OLED cover permitting)")
    if P.bp_x1 > P.dp.hw - 1.0 or P.bp_x0 < -P.dp.hw + 1.0:
        err.append("female board too wide for the dock body (USBC_F_BOARD W)")
    if P.z_b0 - P.f_relief < 0.4:
        err.append("female board floor too thin over the plugs - raise USBC_CONN_Z")
    if P.entry_z1 > P.H - 0.4 or P.well_z0 < 0.2:
        err.append("well does not fit the dock height - USBC_DOCK_H / USBC_CONN_Z / USBC_BRIDGE_SAG")
    if P.mL <= P.m_plug_l + P.m_pad_l:
        err.append("USBC_M_BOARD L must exceed USBC_M_PLUG_L + USBC_M_PAD_L")
    if P.y_nf - P.y_gf < 0.05:
        err.append("grip nose has no length - check USBC_SHELL_EXPOSED / USBC_WELL_DEPTH")
    if P.y_mb1 >= P.y_nf:
        err.append("USBC_M_PLUG_L shorter than USBC_SHELL_EXPOSED: the PCB would stick out of the nose")
    if P.scr_x - P.scr_clear / 2 < P.bw + 0.4:
        err.append("grip screws too close to the male board (USBC_GRIP_SCREW_X)")
    if P.scr_x + P.scr_head / 2 > P.gw / 2 - 0.6:
        err.append("grip screw counterbores break through the sides (USBC_GRIP_W / USBC_GRIP_SCREW_X)")
    if P.scr_depth > P.z_gt - P.z_s - 0.6:
        err.append("grip screw pilot breaks through the top (USBC_GRIP_SCREW pilot depth / USBC_GRIP_ABOVE)")
    if P.scr_y_lo > P.scr_y_hi + 1e-9:
        err.append(f"grip body ({P.y_gf - P.y_g0:.2f} mm) too short for its screws: the male board "
                   f"(USBC_M_BOARD L {P.mL:g}) is short for USBC_WELL_DEPTH {P.well_depth:g} - lower "
                   f"USBC_WELL_DEPTH or USBC_GRIP_FACE_GAP, or use a smaller USBC_GRIP_SCREW head")
    if P.scr_x - P.scr_clear / 2 < P.band_rib / 2 + 0.6:
        err.append("grip screws too close to the wire slot (USBC_GRIP_SCREW_X / USBC_GRIP_WIRE_BAND)")
    if P.z_s - P.m_tail_h - P.z_gb < 1.0 or P.z_gt - (P.z_s + P.mT + P.m_joint_h) < 1.0:
        err.append("grip too low for the male board (USBC_GRIP_BELOW / ABOVE)")
    if P.nose_z1 > P.z_gt - 0.3 or P.nose_z0 < P.z_gb - 1e-9:
        err.append("grip nose taller than the grip body")
    if P.clamp_y1 - P.clamp_y0 < 4 * P.crib_h and P.crib_n > 0 and P.crib_h > 0:
        err.append(f"no room for the grip's clamp ribs: {P.clamp_y1 - P.clamp_y0:.2f} mm between the pad "
                   f"row and the shell tabs - lower USBC_M_TAB_L / USBC_M_PAD_L / USBC_GRIP_JOINT_MARGIN")
    if P.ret:
        if P.rs_x - P.rs_pilot / 2 < P.bp_x1 + 0.6 or P.rs_x + P.rs_pilot / 2 > P.rs_slot_in - 0.6:
            err.append("retainer screws do not fit between the board pocket and the clip slots "
                       "(USBC_RET_SCREW_X / USBC_RET_SCREW pilot D)")
        if P.z_arm - P.rs_depth < 0.8:
            err.append("retainer screw pilot reaches the plug hollow (USBC_RET_SCREW pilot depth / "
                       "USBC_RET_PLATE_T)")
        if P.rs_cb > P.ret_t - 0.6:
            err.append("retainer screw counterbore deeper than the arm allows (USBC_RET_PLATE_T)")
        if P.z_arm < P.dp.z_root + 0.8:
            err.append("retainer arm recess cuts into the clip blade roots (USBC_RET_PLATE_T / USBC_DOCK_H)")
    for pr in P.prongs:
        if pr["gap"] < 0.02:
            err.append("lock prong thicker than the blade relief (USBC_LOCK_PRONG_T + USBC_LOCK_BACK_CLR "
                       "> USBC_CLIP_RELIEF)")
            break
    if err:
        raise ValueError("USB-C config invalid:\n  - " + "\n  - ".join(err))


# ---------------------------------------------------------------------------
# dock
# ---------------------------------------------------------------------------

def _window_cutter(P):
    """Shoulder window: a U-slot open to the top (the retainer's tongue closes
    it), with vertical half-round crush ribs on both side walls over the shell
    height (a 45 deg lead-in cone on top guides the shell down past them)."""
    y_u0 = P.y_wf - 0.01 if P.well_depth > 0.05 else P.y_front - 1.0
    cut = _box(-P.win_hw, P.win_hw, y_u0, P.y_bf + 0.01, P.win_z0, P.H + 1.0)
    h, r = P.wrib_h, P.wrib_r
    if h > 0 and r > h:
        ribs = []
        z0, z1 = P.win_z0 - 0.5, P.win_z1
        for s in (-1.0, 1.0):
            cx = s * (P.win_hw + r - h)
            ribs.append(_cyl_z(cx, P.wrib_y, z0, z1 - h, r))
            ribs.append(Manifold.cylinder(h, r, r - h, 40).translate((cx, P.wrib_y, z1 - h)))
        cut = cut - _union(ribs)
    return cut


def _dock_cutters(P):
    cut = []
    yf = P.y_front
    if P.well_depth > 0.05:
        # straight well + a 45 deg entry funnel as ONE lofted solid (a funnel is
        # not convex), clipped to the flat face (entry_clip)
        cx0, cz0, cx1, cz1 = P.entry_clip.bounds
        if P.well_ch > 0:
            fun = _loft_y(_mitre(P.well_poly, P.well_ch + 0.5), yf - 0.5,
                          P.well_poly, yf + P.well_ch, P.well_poly, P.y_wf)
        else:
            fun = _prism_y(P.well_poly, yf - 1.0, P.y_wf)
        cut.append(fun ^ _box(cx0, cx1, yf - 1.0, P.y_wf + 1.0, min(cz0, P.well_z0 - 0.01),
                              max(cz1, P.well_z1 + 0.01)))
    cut.append(_window_cutter(P))
    # board pocket + the top opening the board drops in through
    cut.append(_box(P.bp_x0, P.bp_x1, P.y_bf, P.y_pr, P.z_b0, P.H + 1.0))
    # leg / solder relief under the board (the board rests on a USBC_F_RIM rim)
    r = P.f_rim
    if P.f_relief > 0:
        cut.append(_box(P.xb - P.fW / 2 + r, P.xb + P.fW / 2 - r, P.y_bf + r, P.y_bf + P.fL - r,
                        P.z_b0 - P.f_relief, P.z_b0 + 0.01))
    # rear wire channel: open bottom, through the rear stop, out of the back face
    cut.append(_box(-P.ch_w / 2, P.ch_w / 2, P.y_pr - 0.01, P.y_back + 1.0, -1.0, P.ch_top))
    if P.ret:
        # retainer arm recess in the top face (+ round screw pads) + pry notches
        cut.append(_box(-P.arm_x1 - P.rc, P.arm_x1 + P.rc, P.arm_y0 - P.rc, P.arm_y1 + P.rc,
                        P.z_arm, P.H + 1.0))
        for x, y in P.rs:
            cut.append(_cyl_z(x, y, P.z_arm, P.H + 1.0, P.rs_pad_r + P.rc))
            cut.append(_cyl_z(x, y, P.z_arm - P.rs_depth, P.z_arm + 0.01, P.rs_pilot / 2.0, 24))
        for s in (-1.0, 1.0):
            xa, xb_ = sorted((s * (P.arm_x1 + P.rc - 0.01), s * (P.arm_x1 + P.rc + P.pry_w)))
            cut.append(_box(xa, xb_, P.arm_yc - P.pry_l / 2, P.arm_yc + P.pry_l / 2,
                            P.H - P.pry_d, P.H + 1.0))
    if P.lock:
        # prong slots: the blades' relief gaps continued up to the top face
        for pr in P.prongs:
            t0, t1, ry0, ry1 = pr["slot"]
            cut.append(_box(t0, t1, ry0, ry1, P.dp.z_root - 0.01, P.H + 1.0))
    return cut


def _backing_ribs(P):
    """Inside the plug hollow, below the plate: a wall right in front of each
    lock prong (the relief gap is otherwise open into the hollow there), so
    the blade cannot push the prong away near its lip."""
    out = []
    if not P.lock or P.backing <= 0:
        return out
    for pr in P.prongs:
        t0, t1, ry0, _ = pr["slot"]
        out.append(_box(t0, t1, ry0 - P.backing, ry0, -P.prong_below, P.embed))
    return out


def build_dock(cfg, P=None):
    """(mesh_local, print_T) like geometry/dock.py: printed upside down."""
    P = P or params(cfg)
    dp = P.dp
    solid = DK._body(dp)
    plug_solids, plug_cutters = DK._plugs(dp)
    solid = Manifold.batch_boolean([solid] + plug_solids, OpType.Add)
    cutters = plug_cutters + _dock_cutters(P)
    for b in dp.blades:
        cutters += DK._blade_cutters(dp, b)
    solid = solid - Manifold.batch_boolean(cutters, OpType.Add)
    solid = Manifold.batch_boolean([solid] + [DK._lip(dp, b) for b in dp.blades] + _backing_ribs(P),
                                   OpType.Add)
    mesh = DK._to_trimesh(solid)
    return mesh, _print_flip(mesh, axis="x")


def _print_flip(mesh, axis="x"):
    """180 deg about X (or Y), then drop on z = 0, XY bbox centred."""
    R = np.diag([1.0, -1.0, -1.0, 1.0]) if axis == "x" else np.diag([-1.0, 1.0, -1.0, 1.0])
    v = trimesh.transform_points(mesh.vertices, R)
    lo, hi = v.min(axis=0), v.max(axis=0)
    T = np.eye(4)
    T[:3, 3] = [-(lo[0] + hi[0]) / 2.0, -(lo[1] + hi[1]) / 2.0, -lo[2]]
    return T @ R


def _print_upright(mesh):
    lo, hi = mesh.bounds
    T = np.eye(4)
    T[:3, 3] = [-(lo[0] + hi[0]) / 2.0, -(lo[1] + hi[1]) / 2.0, -lo[2]]
    return T


# ---------------------------------------------------------------------------
# retainer (+ clip lock prongs, shell press ribs, screws)
# ---------------------------------------------------------------------------

def build_retainer(cfg, P=None):
    P = P or params(cfg)
    rc = P.rc
    solid = [
        # block over the board: presses its rim, fills the opening to the top face
        _box(P.bp_x0 + rc, P.bp_x1 - rc, P.y_bf + rc, P.y_pr - rc, P.z_b1, P.H),
        # tongue: fills the U-slot above the shell (closes the window)
        _box(-P.win_hw + rc, P.win_hw - rc, P.y_wf + rc, P.y_bf + rc + 0.01, P.win_z1, P.H),
        # top plate arms (flush with the dock top) toward the lock prongs
        _box(-P.arm_x1, P.arm_x1, P.arm_y0, P.arm_y1, P.z_arm, P.H),
    ]
    solid += [_cyl_z(x, y, P.z_arm, P.H, P.rs_pad_r) for x, y in P.rs]
    if P.lock:
        z_top = P.z_arm + 0.01
        for pr in P.prongs:
            solid.append(_box(pr["x0"], pr["x1"], pr["y0"], pr["y1"], -P.prong_below, z_top))
            # crush bumps on both X faces, in the slot part above the blade root
            if P.bump > 0 and P.bump_z1 > P.bump_z0 + 0.5:
                yc, hw = (pr["y0"] + pr["y1"]) / 2.0, P.bump_w / 2.0
                solid.append(_box(pr["x0"] - P.bump, pr["x0"] + P.embed, yc - hw, yc + hw, P.bump_z0, P.bump_z1))
                solid.append(_box(pr["x1"] - P.embed, pr["x1"] + P.bump, yc - hw, yc + hw, P.bump_z0, P.bump_z1))
    body = _union(solid)
    cut = [
        # channel over the receptacle shell (window top clearance)
        _box(-P.win_hw, P.win_hw, P.y_wf - 1.0, P.shell_rear + P.win_c, P.z_b1 - 1.0, P.win_z1),
        # wire cavity over the pads, open to the rear channel
        _box(P.xb - P.fW / 2 + P.f_rim, P.xb + P.fW / 2 - P.f_rim, P.shell_rear + P.win_c - 0.01, P.y_pr + 1.0,
             P.z_b1 - 1.0, P.z_b1 + P.ret_cav_h),
    ]
    if P.diode_fits:
        cut.append(_cyl_x(P.d_x - P.d_len / 2 - P.d_clr, P.d_x + P.d_len / 2 + P.d_clr, P.d_y, P.d_z,
                          P.d_r + P.d_clr))
    for x, y in P.rs:
        cut.append(_cyl_z(x, y, P.z_arm - 1.0, P.H + 1.0, P.rs_clear / 2.0, 24))
        cut.append(_cyl_z(x, y, P.H - P.rs_cb, P.H + 1.0, P.rs_head / 2.0))
    m = body - _union(cut)
    # half-round ribs across the shell channel: bottom USBC_RET_SHELL_PRESS
    # below the shell top (in print they stand on an upward face)
    if P.press_ys and P.press_r > 0:
        dz = P.win_c + P.press
        zc = P.win_z1 + P.press_r - dz
        hw = P.win_hw - P.rc                             # as wide as the tongue
        ribs = [_cyl_x(-hw - 0.01, hw + 0.01, y, zc, P.press_r) ^
                _box(-hw, hw, y - P.press_r, y + P.press_r, P.win_z1 - dz, P.win_z1 + P.embed)
                for y in P.press_ys]
        m = _union([m] + ribs)
    mesh = DK._to_trimesh(m)
    return mesh, _print_flip(mesh, axis="x")


# ---------------------------------------------------------------------------
# grip (clamshell, built mated in the dock-local frame)
# ---------------------------------------------------------------------------

def _grip_solid(P):
    outline = C.rounded_rect(-P.gw / 2, P.y_g0, P.gw / 2, P.y_gf, P.g_r)
    e = P.g_edge
    pts = []
    for poly, z in ((outline.buffer(-e, quad_segs=C.QS), P.z_gb), (outline, P.z_gb + e),
                    (outline, P.z_gt - e), (outline.buffer(-e, quad_segs=C.QS), P.z_gt)):
        xy = np.asarray(poly.exterior.coords)[:-1]
        pts.append(np.column_stack([xy, np.full(len(xy), z)]))
    body = Manifold.hull_points(np.vstack(pts))
    li = P.nose_li
    nose = _hull_y(P.nose_poly, P.y_gf - P.g_edge - P.embed, P.nose_poly, P.y_nf - li,
                   P.nose_poly.buffer(-li, join_style="mitre"), P.y_nf)
    return _union([body, nose])


def _ridges(P):
    out = []
    if P.rd <= 0 or P.z_ridge1 - P.z_ridge0 < 1.0:
        return out
    # keep clear of the plan-corner rounds (a groove there leaves a sliver)
    y = P.y_g0 + P.g_r
    while y + P.rw <= P.y_gf - P.g_r + 1e-9:
        for s in (-1.0, 1.0):
            x0, x1 = sorted((s * (P.gw / 2 - P.rd), s * (P.gw / 2 + 1.0)))
            out.append(_box(x0, x1, y, y + P.rw, P.z_ridge0, P.z_ridge1))
        y += P.rp
    return out


def _shell_cavity(P):
    """Plug-shell cavity: the collar (tight, stops the board's front corners),
    the epoxy key groove (sides + bottom, its top flush with the cavity), then
    the plain cavity out through the nose face."""
    zc = P.conn_z
    w, h = P.msW + 2 * P.cav_clr, P.msH + 2 * P.cav_clr
    # the chamfer corners must never land exactly on a relief / pocket face
    # height (an edge-on-edge contact makes the mesh non-manifold there)
    ch = P.cav_ch + P.nudge
    plain = chamfer_rect(0.0, zc, w, h, ch)
    y0 = P.y_mb1 - 0.01
    parts = []
    yc = y0
    if P.col_l > 0 and P.col_hw < w / 2.0 - 1e-6:
        parts.append(_prism_y(chamfer_rect(0.0, zc, 2 * P.col_hw, h, ch), y0, P.y_mb1 + P.col_l))
        yc = P.y_mb1 + P.col_l
    parts.append(_prism_y(plain, yc - (0.01 if parts else 0.0), P.y_nf + 1.0))
    if P.glue:
        zt, zb = zc + h / 2.0, zc - h / 2.0 - P.glue_bot
        ring = chamfer_rect(0.0, (zt + zb) / 2.0, w + 2 * P.glue_side, zt - zb, ch)
        parts.append(_prism_y(ring, P.glue_y0, P.glue_y1))
    return _union(parts)


def _slot_lo(P):
    """Wire slot through the bottom half: pad-row wide at the split plane,
    tapering to USBC_GRIP_WIRE_BAND at the underside (the wires converge)."""
    a, b = P.band_rib / 2.0, P.band / 2.0
    zt, ext = P.z_s + 0.01, 1.0
    b_ext = b - (a - b) * ext / (zt - P.z_gb)          # same taper continued below the underside
    pts = []
    for x, z in ((a, zt), (b_ext, P.z_gb - ext)):
        for sx in (-1.0, 1.0):
            for y in (P.y_slot0, P.y_slot1):
                pts.append((sx * x, y, z))
    return Manifold.hull_points(pts)


def _clamp_ribs(P):
    """Half-round crush ribs across the bottom half's seat, under the board's
    edge strips (x from the tails relief to the pocket wall)."""
    out = []
    x0, x1 = P.mW / 2.0 - P.m_rim, P.bw - 0.05
    if x1 <= x0:
        return out
    for y in P.crib_ys:
        for s in (-1.0, 1.0):
            xa, xb = sorted((s * x0, s * x1))
            cyl = _cyl_x(xa, xb, y, P.z_s, P.crib_h, 32)
            out.append(cyl ^ _box(xa, xb, y - P.crib_h, y + P.crib_h, P.z_s - P.embed, P.z_s + P.crib_h))
    return out


def build_grip(cfg, P=None):
    """{'top': (mesh_mated, print_T), 'bottom': (mesh_mated, print_T)}."""
    P = P or params(cfg)
    grip = _grip_solid(P)
    big = 100.0
    lower_box = _box(-big, big, -big, big, P.z_gb - 1.0, P.z_s)
    upper_box = _box(-big, big, -big, big, P.z_s, P.z_gt + 1.0)
    bw, eps = P.bw, 0.05
    rib = _box(-bw, bw, P.y_rib0, P.y_rib1, P.z_s - eps, P.z_pc)
    shell_cav = _shell_cavity(P)
    rb = P.band_rib / 2.0
    slot_hi = _box(-rb, rb, P.y_slot0, P.y_slot1, P.z_s - eps, P.z_pc + P.slot)
    ridges = _ridges(P)
    tails_x = P.mW / 2 - P.m_rim
    # lower half
    lo_cut = [shell_cav, _slot_lo(P),
              _box(-tails_x, tails_x, P.y_mb0 + P.m_rim, P.y_mb1 + 0.01, P.z_s - P.m_tail_h, P.z_s + eps)] + ridges
    if P.m_tab_l > 0:                                    # shell side tabs: no seat under them
        lo_cut.append(_box(-bw, bw, P.y_tab, P.y_mb1 + 0.01, P.z_s - P.m_tail_h, P.z_s + eps))
    for s in (-1.0, 1.0):
        x = s * P.scr_x
        lo_cut.append(_cyl_z(x, P.scr_y, P.z_gb - 1.0, P.z_s + eps, P.scr_clear / 2))
        lo_cut.append(_cyl_z(x, P.scr_y, P.z_gb - 1.0, P.z_gb + P.scr_cb, P.scr_head / 2))
    pegs = [_cyl_z(x, y, P.z_s - 0.1, P.z_s + P.peg_h, P.peg_d / 2) for x, y in P.pegs]
    lower = _union([(grip ^ lower_box), rib])
    lower = _union([lower - _union(lo_cut)] + pegs + _clamp_ribs(P))
    # upper half (the cutters overlap by USBC_EMBED instead of sharing faces)
    up_cut = [rib, shell_cav, slot_hi,
              _box(-bw, bw, P.y_rib1, P.y_mb1 + 0.01, P.z_s - eps, P.z_pc),                  # board pocket
              _box(-bw, bw, P.y_rib1, P.y_jc, P.z_s - eps, P.z_s + P.mT + P.m_joint_h),        # joints / pads
              _box(-tails_x, tails_x, P.y_jc - P.embed, P.y_mb1 + 0.01, P.z_s - eps,
                   P.z_s + P.mT + P.m_tail_h),                                               # tails / parts
              _box(-rb, rb, P.y_rib0 - 0.01, P.y_rib1 + 0.01, P.z_s - eps, P.z_pc + P.slot)]  # pinch over the rib
    if P.m_tab_l > 0:
        up_cut.append(_box(-bw, bw, P.y_tab, P.y_mb1 + 0.01, P.z_s - eps, P.z_s + P.mT + P.m_tail_h))
    up_cut += ridges
    for s in (-1.0, 1.0):
        up_cut.append(_cyl_z(s * P.scr_x, P.scr_y, P.z_s - eps, P.z_s + P.scr_depth, P.scr_pilot / 2))
    for x, y in P.pegs:
        up_cut.append(_cyl_z(x, y, P.z_s - eps, P.z_s + P.peg_h + P.embed, P.peg_hole_r))
    upper = (grip ^ upper_box) - _union(up_cut)
    m_lo, m_up = DK._to_trimesh(lower), DK._to_trimesh(upper)
    # both halves print in the assembled orientation: the lower one on its
    # outer bottom face, the upper one on its flat split face (cavity roofs
    # are bridges <= the board width)
    return {"bottom": (m_lo, _print_upright(m_lo)), "top": (m_up, _print_upright(m_up))}


def clamp_slicing(P, layer=None):
    """Board clamp interference after slicing at `layer` (faces snap to the
    nearest layer boundary): the bottom half's crush-rib tops (above its bed)
    and the top half's flat pocket ceiling (above its bed = the split face)."""
    L = float(P.layer if layer is None else layer)
    q = lambda v: round(v / L) * L  # noqa: E731
    seat = P.z_s - P.z_gb
    rib_q = (q(seat + P.crib_h) - q(seat)) if P.crib_ys else 0.0
    ceil_q = q(P.mT - P.squeeze)
    return {"layer": L, "nominal": (P.crib_h if P.crib_ys else 0.0) + P.squeeze,
            "sliced": rib_q + P.mT - ceil_q,
            "worst": (P.crib_h if P.crib_ys else 0.0) + P.squeeze - L,
            "rib_q": rib_q, "ceiling_q": ceil_q}


# ---------------------------------------------------------------------------
# hardware envelopes, info, retention, cable
# ---------------------------------------------------------------------------

def hardware(cfg, P, T):
    """Non-printed USB-C parts, assembly frame (T = dock placement offset)."""
    tx, ty, tz = (float(v) for v in T)

    def bx(x0, x1, y0, y1, z0, z1):
        return [round(v, 4) for v in (x0 + tx, x1 + tx, y0 + ty, y1 + ty, z0 + tz, z1 + tz)]
    hw = [
        {"id": "usbc-female-board", "label": "USB-C female breakout (blue, pads G D D V)",
         "shape": "box", "box": bx(P.xb - P.fW / 2, P.xb + P.fW / 2, P.y_bf, P.y_bf + P.fL, P.z_b0, P.z_b1),
         "material": "pcb_blue", "moves_with": "dock"},
        {"id": "usbc-receptacle", "label": "USB-C receptacle shell", "shape": "rounded_box", "axis": "y",
         "r": round(P.sH / 2, 4),
         "box": bx(-P.sW / 2, P.sW / 2, P.mouth_y, P.mouth_y + P.sL, P.shell_bot, P.shell_top),
         "material": "metal", "moves_with": "dock"},
        {"id": "usbc-male-board", "label": "USB-C male breakout (green, pads V D- D+ G)",
         "shape": "box", "box": bx(-P.mW / 2, P.mW / 2, P.y_mb0, P.y_mb1, P.z_s, P.z_s + P.mT),
         "material": "pcb_green", "moves_with": "pad"},
        {"id": "usbc-plug", "label": "USB-C plug shell", "shape": "rounded_box", "axis": "y",
         "r": round(min(P.ms_r, P.msH / 2), 4),
         "box": bx(-P.msW / 2, P.msW / 2, P.y_mb1, P.y_tip, P.conn_z - P.msH / 2, P.conn_z + P.msH / 2),
         "material": "metal", "moves_with": "pad"},
    ]
    if P.diode_fits:
        hw.append({"id": "usbc-schottky", "label": "Series Schottky (1N5817, anode to Pico 3V3)",
                   "shape": "cylinder_x", "r": round(P.d_r, 4),
                   "box": bx(P.d_x - P.d_len / 2, P.d_x + P.d_len / 2, P.d_y - P.d_r, P.d_y + P.d_r,
                             P.d_z - P.d_r, P.d_z + P.d_r),
                   "material": "diode", "moves_with": "dock"})
    return hw


def retention(cfg, P=None):
    """Dock tipping under a USB-C pull vs the clip capacity (see module doc).

    Side view, pivot = the dock's front-bottom edge (y_front, plate top). A
    pull F at USBC_PULL_UP_DEG above horizontal enters the dock at the
    shoulder (y_bf) on the connector axis; the plug walls bear on the cut-out
    edges at mid-plate (0.6 below the plate top):
        M = F cos(t) (z_axis + t_plate / 2) + F sin(t) (y_bf - y_front)
    resisted by the back blades' lips at arm y_lip - y_front:
        demand per blade = M / (n_back * arm)
    Capacity per blade: CN.clip_capacity (cantilever + catch-face camming),
    or with the lock prongs fitted the lip must shear off.
    Retainer hold-down: the upward share F sin(t) lifts the receptacle's mouth;
    with the board's rear edge as the pivot the retainer's tongue rib takes
        F sin(t) (y_pr - mouth) / (y_pr - y_tongue)
    against 2 screws x USBC_SCREW_PULLOUT_N.
    """
    P = P or params(cfg)
    dp = P.dp
    Pb, cap = CN.clip_capacity(cfg, {"clips": _clips_info(P)})
    F, th = float(cfg.USBC_PULL_N), math.radians(float(cfg.USBC_PULL_UP_DEG))
    Fh, Fv = F * math.cos(th), F * math.sin(th)
    za = P.conn_z + P.plate_t / 2.0
    lever_v = P.y_bf - P.y_front
    M = Fh * za + Fv * lever_v

    def lip_y(b):
        return b["w_out"] + b["sg"] * dp.lip / 2.0 if b["axis"] == "y" else (b["t0"] + b["t1"]) / 2.0
    back = P.back_blades
    arm = sum(lip_y(b) for b in back) / len(back) - P.y_front
    demand = M / (len(back) * arm)
    lip_w = min(b["t1"] - b["t0"] for b in back) - 2 * P.prong_x_clr
    lip_h = dp.z_catch - dp.z_lip_bot
    cap_lock = float(cfg.CLIP_LIP_SHEAR_MPA) * lip_w * lip_h
    m_catch = cap / demand
    m_lock = cap_lock / demand
    # plugging in: horizontal push tips the dock about its back-bottom edge
    front = P.front_blades
    arm_f = P.y_back - sum(lip_y(b) for b in front) / len(front)
    dem_push = F * za / (len(front) * arm_f)
    eff = m_lock if P.lock else m_catch
    # retainer hold-down
    y_t = P.press_ys[0] if P.press_ys else (P.y_wf + P.y_bf) / 2.0
    hold_dem = Fv * (P.y_pr - P.mouth_y) / max(1e-6, P.y_pr - y_t)
    hold_cap = len(P.rs) * float(cfg.USBC_SCREW_PULLOUT_N)
    return {"pull_n": F, "pull_up_deg": float(cfg.USBC_PULL_UP_DEG), "moment_nmm": M,
            "arm_mm": arm, "n_back_blades": len(back), "demand_per_blade_n": demand,
            "blade_force_n": Pb, "capacity_per_blade_n": cap, "catch_deg": dp.catch_deg,
            "margin_catch": m_catch, "lock": P.lock, "lock_capacity_n": cap_lock, "margin_lock": m_lock,
            "margin": eff, "push_demand_per_blade_n": dem_push, "push_arm_mm": arm_f,
            "margin_push": cap / dem_push, "E_mpa": float(cfg.CLIP_E_MPA), "mu": float(cfg.CLIP_MU),
            "hold_down_demand_n": hold_dem, "hold_down_capacity_n": hold_cap,
            "margin_hold_down": (hold_cap / hold_dem) if hold_dem > 0 else None}


def _clips_info(P):
    dp = P.dp
    L_free = dp.z_root - (dp.z_catch + dp.z_lip_full) / 2.0
    back = P.back_blades
    return {"count": len(dp.blades), "lip": dp.lip, "thickness": dp.clip_t,
            "width_front": dp.clip_w_front, "width_inner": dp.clip_w,
            "width_back": min(b["t1"] - b["t0"] for b in back),
            "root_z": dp.z_root, "catch_deg": dp.catch_deg, "free_length": L_free,
            "deflection": dp.lip - dp.side_clr,
            "root_strain_pct": 100.0 * 1.5 * dp.clip_t * (dp.lip - dp.side_clr) / (L_free * L_free),
            "walls": sorted({b["wall"] for b in dp.blades})}


def dock_info(cfg, P=None):
    P = P or params(cfg)
    dp = P.dp
    r = lambda v: round(float(v), 4)  # noqa: E731
    return {
        "frame": ("dock-local: origin = midpoint of the removed switch centres on the "
                  "switchplate top; +X right, +Y toward keyboard back, +Z up"),
        "origin_keyboard_local": [r(dp.center_x), r(dp.center_y), r(dp.kb_h)],
        "connector_type": "usbc",
        "connector_face_center": [0.0, r(P.y_front), r(P.conn_z)],
        "connector_face_normal": [0.0, -1.0, 0.0],
        "mouth_center": [0.0, r(P.mouth_y), r(P.conn_z)],
        "well": {"w": r(P.well_w), "h": r(P.well_h), "depth": r(P.well_depth), "chamfer": r(P.well_ch),
                 "z0": r(P.well_z0), "z1": r(P.well_z1), "floor_y": r(P.y_wf), "clearance": r(P.well_clr),
                 "bridge_sag_allowance": r(P.sag)},
        "shoulder": {"t": r(P.shoulder), "y0": r(P.y_wf), "y1": r(P.y_bf),
                     "window": [r(2 * P.win_hw), r(P.win_z1 - P.win_z0)], "window_clearance": r(P.win_c),
                     "window_ribs": {"protrusion": r(P.wrib_h), "radius": r(P.wrib_r),
                                     "grip": r(P.wrib_h - P.win_c), "y": r(P.wrib_y)}},
        "mouth_recess": r(P.recess),
        "board_pocket": {"x0": r(P.bp_x0), "x1": r(P.bp_x1), "y0": r(P.y_bf), "y1": r(P.y_pr),
                         "z0": r(P.z_b0), "relief": r(P.f_relief), "rim": r(P.f_rim)},
        "rear_stop": r(P.rear_stop),
        "rear_channel": {"w": r(P.ch_w), "h": r(P.ch_top), "exit_y": r(P.y_back)},
        "body": {"w": r(dp.W), "d": r(P.D), "h": r(P.H), "r": r(dp.R), "x0": r(-dp.hw), "x1": r(dp.hw),
                 "y0": r(P.y_front), "y1": r(P.y_back), "z0": 0.0, "z1": r(P.H)},
        "keyboard_front_y": r(P.kb_front),
        "plug_size": r(dp.s), "plug_depth": r(dp.depth), "plug_wall": r(dp.wall),
        "plug_centers": [[r(cx), 0.0, 0.0] for cx in dp.plug_cx],
        "switch_cutout": r(dp.cut),
        "clips": {k: (r(v) if isinstance(v, float) else v) for k, v in _clips_info(P).items()},
        "lock_prongs": [{"x0": r(p["x0"]), "x1": r(p["x1"]), "y0": r(p["y0"]), "y1": r(p["y1"]),
                         "z0": r(-P.prong_below), "gap_to_blade": r(p["gap"]),
                         "back_clearance": r(P.prong_back_clr),
                         "lip_engagement": r(dp.lip - dp.side_clr - p["gap"] - P.prong_back_clr)}
                        for p in P.prongs] if P.lock else [],
        "retainer": {"enabled": P.ret, "arm": [r(-P.arm_x1), r(P.arm_x1), r(P.arm_y0), r(P.arm_y1)],
                     "plate_t": r(P.ret_t), "screws": [[r(x), r(y)] for x, y in P.rs],
                     "screw": f"M{P.rs_d:g}x{P.rs_l:g} self-tapping pan head",
                     "shell_press": {"interference": r(P.press), "ribs_y": [r(y) for y in P.press_ys]}},
        "diode": {"fits": P.diode_fits, "center": [r(P.d_x), r(P.d_y), r(P.d_z)], "l": r(P.d_len),
                  "d": r(P.d_dia)},
        "clearance_to_oled_cover_y": r(dp.cover_y0_local - P.y_back),
        "below_oled_cover_underside": r(dp.cover_clear_h - P.H),
        "clearance_to_neighbour_keycell": r(dp.keys * dp.pitch / 2.0 - dp.hw),
        "print_orientation": ("upside down: top face on the bed (180 deg about X); no supports; "
                              "PETG recommended for the snap blades"),
    }


def grip_info(cfg, P=None):
    P = P or params(cfg)
    r = lambda v: round(float(v), 4)  # noqa: E731
    cs = clamp_slicing(P)
    return {"w": r(P.gw), "l": r(P.y_gf - P.y_g0), "h": r(P.z_gt - P.z_gb),
            "nose": [r(P.nose_w), r(P.nose_h), r(P.y_nf - P.y_gf)],
            "nose_gap": r(P.nose_gap), "exposed": r(P.exposed),
            "inserted": r(P.y_tip - P.mouth_y), "split_z": r(P.z_s),
            "screws": f"2 x M{P.scr_d:g}x{P.scr_l:g} self-tapping pan head from below",
            "screw_y": r(P.scr_y), "pegs": len(P.pegs),
            "clamp": {"ribs_per_side": len(P.crib_ys), "rib_h": r(P.crib_h), "nominal": r(cs["nominal"]),
                      "sliced": r(cs["sliced"]), "worst": r(cs["worst"]), "layer": r(cs["layer"])},
            "collar_ledge": r(P.col_ledge),
            "glue_groove": ([r(P.glue_y0), r(P.glue_y1), r(P.glue_side), r(P.glue_bot)] if P.glue else None),
            "wire_band": [r(P.band_rib), r(P.band)],
            "wire_exit_y": [r(P.y_slot0), r(P.y_slot1)]}


def pad_signals(cfg):
    sig_of = dict(cfg.USBC_SIGNALS)
    return [sig_of.get(p, p) for p in cfg.USBC_M_PADS]


def cable_route(cfg, lay, P, T):
    """Pigtail for the USB-C grip, assembly frame: TPS65 pads -> well ->
    S-groove -> tunnel -> riser (the sleeve ends CABLE_PLUG_LOOSE_LEN of route
    before the male pads) -> loose wires up through the notch / bay -> grip wire exit ->
    up the clamp slot (fanning out to the pad pitch) -> over the push rib -> male pads."""
    tx, ty, tz = (float(v) for v in T)
    r = cfg.CABLE_D / 2.0
    wd = float(cfg.CABLE_WIRE_D)
    zg = lay.tunnel_floor + 0.1 + r
    zt = lay.tunnel_floor + r
    Xn = lay.notch_x
    sig = pad_signals(cfg)
    n = len(sig)
    line = list(lay.groove_line.coords)[::-1]
    P3 = line[0]
    xc = tx
    y_drop = ty + (P.y_slot0 + P.y_slot1) / 2.0
    z_exit = tz + P.z_gb
    z_wire = tz + P.z_pc + P.slot / 2.0
    y_pads = ty + P.y_mb0 + P.m_pad_l / 2.0
    pitch = P.mW / n
    pads_m = [(xc + (i - (n - 1) / 2.0) * pitch, y_pads, z_wire) for i in range(n)]
    p_rib = min(pitch, (P.band_rib - wd) / max(1, n - 1))   # spread over the rib

    pads = [(lay.pads_c[0], lay.pads_c[1], lay.ledge_z - 0.5), (lay.pads_c[0], P3[1] - 2.0, lay.well_z + 0.6)]
    groove = [(x, y, zg) for x, y in line]
    tunnel = [(Xn, line[-1][1] + 0.5, zt), (Xn, y_drop, zt)]
    up = [(Xn, y_drop, z_wire), (xc, y_pads, z_wire)]
    sleeve_f = PL.fillet(groove + tunnel + up, 2.0)
    total = PL.polyline_length(sleeve_f)
    s_end = max(0.0, total - float(cfg.CABLE_PLUG_LOOSE_LEN))
    sleeve, plug_side = PL.split_at_length(sleeve_f, s_end)
    centre = PL.fillet(pads, 1.0) + sleeve_f
    wires = PL.pad_wires(cfg, lay, sig)
    colors = dict(cfg.CABLE_WIRE_COLORS or {})
    bend = 0.8
    for k, s in enumerate(sig):
        o = (k - (n - 1) / 2.0) * wd
        o_rib = (k - (n - 1) / 2.0) * p_rib
        pts = [(p[0] + o, p[1], p[2]) for p in plug_side if p[1] <= y_drop + 1e-6 and p[2] <= z_exit + 1e-6]
        if not pts:
            pts = [(plug_side[0][0] + o, plug_side[0][1], plug_side[0][2])]
        pts += [(xc + o, y_drop, z_exit), (xc + o_rib, y_drop, z_wire - bend), (xc + o_rib, y_drop + bend, z_wire),
                (pads_m[k][0], pads_m[k][1] - 1.0, z_wire), pads_m[k]]
        wires.append({"signal": s, "color": colors.get(s, "#888888"), "part": "plug",
                      "points": [PL._r(p) for p in PL.fillet(pts, 0.6)]})
    lo, hi = lay.notch_y0 + wd, lay.riser_y1 - wd
    return {
        "centerline": [PL._r(p) for p in centre],
        "sleeve": [PL._r(p) for p in sleeve],
        "wires": wires,
        "sleeve_len": round(PL.polyline_length(sleeve), 2),
        "slack": float(cfg.USBC_WIRE_SLACK),
        "envelope": {"drop_y": y_drop, "drop_ok": bool(lo <= y_drop <= hi), "drop_range": (lo, hi),
                     "drop_what": "grip wires drop into the riser", "exit": "down",
                     "exit_z": z_exit, "pads": pads_m},
    }


def metal_distance(cfg, lay, P, T):
    """Plan distance plug shell / male board -> TPS65 outline (advisory)."""
    tx, ty, _ = (float(v) for v in T)
    mod = shapely.box(lay.mod_x0, lay.mod_y0, lay.mod_x1, lay.mod_y1)
    shell = shapely.box(tx - P.msW / 2, ty + P.y_mb1, tx + P.msW / 2, ty + P.y_tip)
    board = shapely.box(tx - P.mW / 2, ty + P.y_mb0, tx + P.mW / 2, ty + P.y_mb1)
    return {"plug_shell": float(mod.distance(shell)), "male_board": float(mod.distance(board))}


def grip_float(grip_meshes, rest_mesh, T, withdraw):
    """Min gap grip <-> rest (assembly), mated and pulled back `withdraw` mm."""
    rm = C.from_trimesh(rest_mesh)
    gm = [C.from_trimesh(m).translate(tuple(float(v) for v in T)) for m in grip_meshes]
    return {"mated": min(rm.min_gap(m, 5.0) for m in gm),
            "withdrawn": min(rm.min_gap(m.translate((0.0, -float(withdraw), 0.0)), 5.0) for m in gm),
            "withdraw": float(withdraw)}


def dims_notes(cfg, P, ret, metal, floats=None):
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")  # noqa: E731
    dp = P.dp
    cs = clamp_slicing(P)
    if floats:
        fl = (f"floats {f(floats['mated'])} mm over the rest ({f(floats['withdrawn'])} when pulled back "
              f"{f(floats['withdraw'])} mm)")
    else:
        fl = f"floats {f(cfg.KEYBOARD_HEIGHT + P.z_gb - cfg.REST_HEIGHT)} mm over the rest top"
    capture = (f"pull -> {f(P.shoulder)} mm shoulder, push -> {f(P.rear_stop)} mm rear stop; retainer on top "
               f"(2 x M{P.rs_d:g}x{P.rs_l:g} screws), its ribs press the shell onto the board, the window's "
               f"side ribs grip it {f(P.wrib_h - P.win_c)} mm"
               if P.ret else
               f"pull -> {f(P.shoulder)} mm shoulder, push -> {f(P.rear_stop)} mm rear stop; NO retainer "
               f"(USBC_RET_ENABLED=False): epoxy the board into its pocket, nothing else holds it down")
    dims = [
        ["Dock (USB-C)", f"{f(dp.W)} x {f(P.D)} x {f(P.H)} mm, axis {f(P.conn_z)} above the plate, "
                         f"{f(dp.cover_y0_local - P.y_back)} mm in front of the OLED cover and "
                         f"{f(dp.cover_clear_h - P.H)} mm below its underside"],
        ["Well", f"{f(P.well_w)} x {f(P.well_h)} x {f(P.well_depth)} mm deep, {f(P.well_ch)} x 45° entry "
                 f"chamfer, grip nose clearance {f(P.well_clr)}/side"],
        ["Female board", f"{f(P.fW)} x {f(P.fL)} x {f(P.fT)} mm; shell {f(P.sW)} x {f(P.sH)} x {f(P.sL)} through a "
                         f"{f(2 * P.win_hw)} x {f(P.win_z1 - P.win_z0)} window in a {f(P.shoulder)} mm shoulder; "
                         + ("mouth flush with the well floor" if abs(P.recess) < 0.005 else
                            f"mouth {f(abs(P.recess))} mm {'behind' if P.recess > 0 else 'proud of'} the well floor")],
        ["Board capture", capture],
        ["Clip retention", f"{f(dp.catch_deg)}° catch, blades on the plug {'/'.join(_clips_info(P)['walls'])} "
                           f"walls; {f(ret['pull_n'])} N at {f(ret['pull_up_deg'])}° up: "
                           f"{ret['demand_per_blade_n']:.2f} N per back blade vs {ret['capacity_per_blade_n']:.2f} N "
                           f"(margin {ret['margin_catch']:.2f})"
                           + (f"; lock prongs fitted: margin {ret['margin_lock']:.1f}" if P.lock else "")],
        ["Grip", f"clamshell {f(P.gw)} x {f(P.y_nf - P.y_g0)} x {f(P.z_gt - P.z_gb)} mm (body "
                 f"{f(P.y_gf - P.y_g0)} long + nose {f(P.nose_w)} x {f(P.nose_h)} x {f(P.y_nf - P.y_gf)}); "
                 f"2 x M{P.scr_d:g}x{P.scr_l:g}" + (f" + {len(P.pegs)} pegs" if P.pegs else " (no pegs: grip too short)")
                 + f"; {fl}"],
        ["Male board", f"{f(P.mW)} x {f(P.mL)} x {f(P.mT)} mm incl. plug; shell {f(P.msW)} x {f(P.msH)}, "
                       f"{f(P.exposed)} exposed, seats {f(P.f_depth)} deep, nose stops {f(P.nose_gap)} before "
                       f"the floor"],
        ["Male board hold", f"epoxy key groove around the plug shell + {len(P.crib_ys)} crush ribs per side "
                            f"under the board ({f(cs['nominal'])} mm squeeze, {f(cs['sliced'])} at "
                            f"{f(cs['layer'])} mm layers)"
                            + (f"; board corners stop on a {f(P.col_ledge)} mm collar" if P.col_ledge > 0.02 else "")],
        ["Schottky", (f"{f(P.d_len)} x Ø{f(P.d_dia)} mm in the retainer cradle (anode -> Pico 3V3)"
                      if P.diode_fits else "inline at the 3V3 tap (does not fit the retainer cradle)")],
        ["Wires", f"4 x 28 AWG GND / 3V3 / SDA / SCL, {f(cfg.USBC_WIRE_SLACK)} mm slack S-loop in the plug bay"],
        ["Metal near the pad", f"plug shell {metal['plug_shell']:.1f} mm, male board {metal['male_board']:.1f} mm "
                               f"from the TPS65 (advisory {f(cfg.TP_METAL_KEEPOUT)})"],
    ]
    notes = [
        "Never plug either half into a real USB port or charger: V carries the Pico's 3V3. Label both parts.",
        "Remove both 5.1k Rd resistors (CC to GND) from the female board, and any 56k / 5.1k CC resistor "
        "from the male.",
        "Keyboard end: Pico 3V3 -> Schottky (1N5817 / SS14, anode to the Pico) -> V pad; D+ = SDA (GP2), "
        "D- = SCL (GP3), G = GND. No RDY (the firmware polls).",
    ]
    if P.ret:
        notes.append(
            "Female board: check that every receptacle shell leg is soldered, solder the 4 wires (and the "
            "diode), route them out of the rear channel, press the board in from the top (the shell slides "
            "down between the window's crush ribs), snap the dock into the plate, then press the retainer "
            f"in and drive its 2 x M{P.rs_d:g}x{P.rs_l:g} screws: it holds the board down, presses the shell, "
            "closes the window and its two prongs lock the back clips.")
        notes.append("To take the dock out: undo the 2 retainer screws and lever the retainer up at the pry "
                     "notches first (it locks the clips).")
    else:
        notes.append("No retainer (USBC_RET_ENABLED=False): nothing holds the female board down. Bed it in "
                     "epoxy in its pocket (keep epoxy out of the receptacle) and let it cure before the "
                     "first plug-in.")
    notes += [
        "Deburr the dock's well bottom and window floor (printed bridges) and check the bare boards' fit "
        f"before soldering. Measure the OLED cover: the dock's back face is {f(dp.cover_y0_local - P.y_back)} mm "
        f"in front of its front edge and its top {f(dp.cover_clear_h - P.H)} mm below its underside (taken as "
        f"{f(dp.cover_clear_h)} mm above the plate), so the dock still seats if the edge sits further forward "
        "unless the underside is lower.",
        "Grip: solder each wire on the front half of its pad and fan the 4 wires toward the middle over the "
        "push rib. Mix 2-part epoxy, fill the key groove around the plug shell and run a bead where the shell "
        "meets the board (keep it off the exposed shell), lay the board in the bottom half (rear edge on the "
        "push rib), lead the wires over the rib and down the slot, add the top half"
        + (" on the pegs" if P.pegs else "") + f" and drive 2 x M{P.scr_d:g}x{P.scr_l:g} screws from below "
        "(they crush the clamp ribs). Let it cure before the first plug-in.",
        "Plugging in: hold the keyboard (USB-C needs 5-20 N). Unplugging: brace a fingertip on the dock face "
        "beside the well and pull the grip - never the wires, never the rest.",
        f"Leave the {f(cfg.USBC_WIRE_SLACK)} mm wire slack as an S-loop in the plug bay: the grip comes back "
        f"{f(P.y_tip - P.y_front)} mm before the plug clears the well.",
        "Retainer: print it upside down (top plate on the bed). Grip: the lower half on its bottom face, the "
        "upper half on its flat split face. PETG, no supports.",
    ]
    return dims, notes
