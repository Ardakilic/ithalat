"""Pigtail plug envelope and the cable route (assembly frame, mm).

The pigtail's plug (cable half of the connector) mates with the dock's front
face and therefore hangs over the rest's back edge. It is modelled as two
boxes - the housing (PLUG_BODY) and the strain relief behind it (solder tails,
joint heat-shrink, glue: PLUG_RELIEF_*) - so verify can measure their real
clearance to the rest instead of guessing.

PLUG_EXIT selects how the wires leave the relief:
  'down'  the loose last CABLE_PLUG_LOOSE_LEN of wire turns straight down,
          PLUG_WIRE_BEND_R in front of the relief, into the plug bay and the
          riser (feasible when that drop line lies inside the riser);
  'rear'  the sleeved cable leaves the relief toward the user and has to turn
          down into the riser with CABLE_BEND_R (feasible only when the relief
          ends at least CABLE_BEND_R behind the riser - not with the defaults).

cable_route() builds, for one variant's Layout, the cable centreline (pads ->
well -> S-groove -> tunnel -> riser -> plug -> dock face), the sleeved part
of it, and one polyline per core (pads -> sleeve start, sleeve end -> tails),
all with rounded bends. Used by generate.py (manifest / preview) and verify.
"""

import math

import numpy as np

PAD_ALIAS = {"3V3": "VDDHI", "VCC": "VDDHI", "VDD": "VDDHI"}


def connector_face(cfg):
    """Centre of the dock's connector mating face, assembly frame. Same value
    as geometry/dock.py dock_info()['connector_face_center'] placed with the
    dock matrix (verify cross-checks the two)."""
    return np.array([cfg.KB_X0 + cfg.DOCK_CENTER_X,
                     cfg.REST_DEPTH + cfg.REST_KEYBOARD_GAP + cfg.DOCK_FRONT_SETBACK - cfg.DOCK_CONN_PROUD,
                     cfg.KEYBOARD_HEIGHT + cfg.DOCK_CONN_Z], dtype=float)


def pinout(cfg):
    """(signals, pin x offsets from the connector centre), pin 1 at -X."""
    if cfg.DOCK_CONN_TYPE == "jst_sh4":
        sig, pitch = list(cfg.JST_SH4_PINOUT), float(cfg.JST_SH4_PITCH)
    else:
        sig, pitch = list(cfg.CONNECTOR_PINOUT), float(cfg.POGO5_PITCH)
    n = len(sig)
    return sig, [(i - (n - 1) / 2.0) * pitch for i in range(n)]


def plug_envelope(cfg, lay, face=None):
    """Housing + relief boxes (x0, x1, y0, y1, z0, z1) and the exit check."""
    face = connector_face(cfg) if face is None else np.asarray(face, dtype=float)
    fx, fy, fz = (float(v) for v in face)
    W, Dp, Hp = (float(v) for v in cfg.PLUG_BODY)
    RW = float(cfg.PLUG_RELIEF_W) if cfg.PLUG_RELIEF_W else W
    RL, RH = float(cfg.PLUG_RELIEF_L), float(cfg.PLUG_RELIEF_H)
    back_y = fy - Dp
    end_y = back_y - RL
    housing = (fx - W / 2, fx + W / 2, back_y, fy, fz - Hp / 2, fz + Hp / 2)
    relief = (fx - RW / 2, fx + RW / 2, end_y, back_y, fz - RH / 2, fz + RH / 2) if RL > 0 else None
    out = {"face": [fx, fy, fz], "housing": housing, "relief": relief, "exit": cfg.PLUG_EXIT,
           "back_y": back_y, "relief_end_y": end_y}
    if cfg.PLUG_EXIT == "down":
        # loose wires turn down PLUG_WIRE_BEND_R in front of the relief
        y = end_y - float(cfg.PLUG_WIRE_BEND_R)
        lo, hi = lay.notch_y0 + cfg.CABLE_WIRE_D, lay.riser_y1 - cfg.CABLE_WIRE_D
        out.update(drop_y=y, drop_ok=bool(lo <= y <= hi), drop_range=(lo, hi),
                   drop_what="loose wires drop into the riser")
    else:
        # the sleeved cable comes up the riser and bends (CABLE_BEND_R) into the relief
        r = cfg.CABLE_D / 2.0
        y = end_y - float(cfg.CABLE_BEND_R)
        lo, hi = lay.notch_y0 + r, lay.riser_y1 - r
        out.update(drop_y=y, drop_ok=bool(lo <= y <= hi), drop_range=(lo, hi),
                   drop_what="sleeved cable turns from the riser into the relief")
    # MG005 magnets: in the stadium ends of the housing
    if cfg.DOCK_CONN_TYPE == "pogo5":
        mx = W / 2 - Hp / 2
        out["magnets"] = [(fx - mx, back_y, fy, fz), (fx + mx, back_y, fy, fz)]
    else:
        out["magnets"] = []
    return out


def box_surface_points(b, step=0.5):
    """Points on the 6 faces of an axis-aligned box (x0, x1, y0, y1, z0, z1)."""
    x0, x1, y0, y1, z0, z1 = b
    ax = [np.linspace(lo, hi, max(2, int(math.ceil((hi - lo) / step)) + 1)) for lo, hi in ((x0, x1), (y0, y1), (z0, z1))]
    pts = []
    for i in range(3):
        j, k = [a for a in range(3) if a != i]
        gj, gk = np.meshgrid(ax[j], ax[k], indexing="ij")
        for v in (ax[i][0], ax[i][-1]):
            p = np.zeros((gj.size, 3))
            p[:, i] = v
            p[:, j] = gj.ravel()
            p[:, k] = gk.ravel()
            pts.append(p)
    return np.vstack(pts)


# ---------------------------------------------------------------------------
# polylines
# ---------------------------------------------------------------------------

def fillet(points, radius, seg_deg=12.0):
    """Round every interior corner of a 3D polyline with a circular arc of
    `radius` (shrunk where the neighbouring segments are too short)."""
    P = [np.asarray(p, dtype=float) for p in points]
    P = [p for i, p in enumerate(P) if i == 0 or np.linalg.norm(p - P[i - 1]) > 1e-6]
    if len(P) < 3 or radius <= 0:
        return [p.tolist() for p in P]
    out = [P[0]]
    avail = [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)]
    for i in range(1, len(P) - 1):
        A, B, Cc = P[i - 1], P[i], P[i + 1]
        u, v = A - B, Cc - B
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        u, v = u / lu, v / lv
        cos_t = float(np.clip(np.dot(u, v), -1.0, 1.0))
        theta = math.acos(cos_t)       # angle between the two legs at B
        if theta > math.pi - 1e-3 or theta < 1e-3:
            out.append(B)
            continue
        # a segment shared by two corners gives each half of its length
        la = avail[i - 1] if i == 1 else 0.5 * avail[i - 1]
        lb = avail[i] if i == len(P) - 2 else 0.5 * avail[i]
        t = max(0.0, min(radius / math.tan(theta / 2), la, lb))
        r = t * math.tan(theta / 2)
        if r < 1e-4:
            out.append(B)
            continue
        T0, T1 = B + u * t, B + v * t
        bis = (u + v) / np.linalg.norm(u + v)
        Cn = B + bis * (r / math.sin(theta / 2))
        a0, a1 = T0 - Cn, T1 - Cn
        sweep = math.pi - theta
        n = max(2, int(math.ceil(math.degrees(sweep) / seg_deg)))
        sin_s = math.sin(sweep)
        for k in range(n + 1):
            f = k / n
            w0 = math.sin((1 - f) * sweep) / sin_s
            w1 = math.sin(f * sweep) / sin_s
            out.append(Cn + w0 * a0 + w1 * a1)
    out.append(P[-1])
    return [p.tolist() for p in out]


def polyline_length(pts):
    a = np.asarray(pts, dtype=float)
    return float(np.linalg.norm(np.diff(a, axis=0), axis=1).sum()) if len(a) > 1 else 0.0


def split_at_length(pts, s):
    """(head, tail) of a polyline cut at arc length s (the cut point is in both)."""
    a = [np.asarray(p, dtype=float) for p in pts]
    acc = 0.0
    for i in range(len(a) - 1):
        L = float(np.linalg.norm(a[i + 1] - a[i]))
        if acc + L >= s - 1e-9:
            f = 0.0 if L < 1e-12 else (s - acc) / L
            c = a[i] + (a[i + 1] - a[i]) * min(max(f, 0.0), 1.0)
            return ([p.tolist() for p in a[:i + 1]] + [c.tolist()],
                    [c.tolist()] + [p.tolist() for p in a[i + 1:]])
        acc += L
    return [p.tolist() for p in a], [a[-1].tolist()]


def resample(pts, step):
    """Points every `step` mm along a polyline (both ends included)."""
    a = np.asarray(pts, dtype=float)
    seg = np.linalg.norm(np.diff(a, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.linspace(0.0, s[-1], max(2, int(math.ceil(s[-1] / step)) + 1))
    return np.column_stack([np.interp(t, s, a[:, k]) for k in range(3)])


def _r(p):
    return [round(float(v), 3) for v in p]


# ---------------------------------------------------------------------------
# route
# ---------------------------------------------------------------------------

def sleeve_passage(cfg, lay):
    """Centreline a sleeved cable would follow through the rest's channels:
    jacket end -> S-groove -> tunnel -> riser (centre) -> up to where the
    U-notch is full width. verify sweeps it with the cable radius."""
    r = cfg.CABLE_D / 2.0
    zg = lay.tunnel_floor + 0.1 + r            # on the groove floor
    zt = lay.tunnel_floor + r                  # on the tunnel floor
    Xn = lay.notch_x
    line = list(lay.groove_line.coords)[::-1]  # P3 -> P0
    pts = [(x, y, zg) for x, y in line]
    y_rc = (lay.notch_y0 + lay.riser_y1) / 2.0
    pts += [(Xn, line[-1][1] + 0.5, zt), (Xn, y_rc, zt), (Xn, y_rc, lay.notch_floor + lay.notch_r_u)]
    return pts


def pad_wires(cfg, lay, sig):
    """Loose cores from the TPS65 solder pads to the jacket end in the well (a
    U-turn into the sleeve mouth), one per signal in `sig` (bundle order)."""
    r = cfg.CABLE_D / 2.0
    wd = float(cfg.CABLE_WIRE_D)
    zg = lay.tunnel_floor + 0.1 + r
    n = len(sig)
    P3 = list(lay.groove_line.coords)[::-1][0]
    wires = []
    pitch = (cfg.TP_PADS_BOX[1] - cfg.TP_PADS_BOX[0]) / len(cfg.TP_PAD_NAMES)
    pads_y = lay.pads_c[1]
    colors = dict(cfg.CABLE_WIRE_COLORS or {})
    z_under = lay.ledge_z - wd / 2 - 0.05
    z_over = zg + r + wd / 2 + 0.05             # crossing over the sleeve in the well
    for k, s in enumerate(sig):
        name = PAD_ALIAS.get(str(s).upper(), str(s).upper())
        names = [str(p).upper() for p in cfg.TP_PAD_NAMES]
        if name not in names:
            continue
        i = names.index(name)
        x_pad = lay.mod_x0 + cfg.TP_PADS_BOX[0] + pitch * (i + 0.5)
        o = (k - (n - 1) / 2.0) * wd
        # the U-turn stays inside the well's round end around the jacket end
        pts = [(x_pad, pads_y, z_under), (x_pad, pads_y - 2.0, z_under - 0.4),
               (P3[0] + 0.8 * o + 0.3 * (x_pad - P3[0]), P3[1] + 1.8, z_over),
               (P3[0] + 0.6 * o, P3[1] - 1.6, zg + 0.3), (P3[0] + 0.45 * o, P3[1] + 0.8, zg)]
        wires.append({"signal": s, "color": colors.get(s, "#888888"), "part": "pad",
                      "points": [_r(p) for p in fillet(pts, 1.2)]})
    return wires


def cable_route(cfg, lay, face=None):
    face = connector_face(cfg) if face is None else np.asarray(face, dtype=float)
    env = plug_envelope(cfg, lay, face)
    fx, fy, fz = env["face"]
    r = cfg.CABLE_D / 2.0
    wd = float(cfg.CABLE_WIRE_D)
    zg = lay.tunnel_floor + 0.1 + r
    zt = lay.tunnel_floor + r
    Xn = lay.notch_x
    sig, pin_x = pinout(cfg)
    n = len(sig)
    line = list(lay.groove_line.coords)[::-1]  # P3 (jacket end) -> P0
    P3 = line[0]
    y_drop = env["drop_y"]
    end_y, back_y = env["relief_end_y"], env["back_y"]
    # the cable / wires turn from the riser toward the plug above this height
    bend = float(cfg.PLUG_WIRE_BEND_R) if env["exit"] == "down" else float(cfg.CABLE_BEND_R)

    # -- centreline (pads -> dock face) -------------------------------------
    pads = [(lay.pads_c[0], lay.pads_c[1], lay.ledge_z - 0.5),
            (lay.pads_c[0], P3[1] - 2.0, lay.well_z + 0.6)]
    groove = [(x, y, zg) for x, y in line]
    tunnel = [(Xn, line[-1][1] + 0.5, zt), (Xn, y_drop, zt)]
    up = [(Xn, y_drop, fz - bend), (fx, end_y, fz), (fx, back_y, fz)]
    sleeve_raw = groove + tunnel + up
    sleeve_f = fillet(sleeve_raw, float(cfg.CABLE_BEND_R) if env["exit"] == "rear" else 2.0)
    # 'down': the sleeve ends CABLE_PLUG_LOOSE_LEN (route length) before the
    # housing's back face; 'rear': it runs into the relief
    total = polyline_length(sleeve_f)
    if env["exit"] == "down":
        s_end = max(0.0, total - float(cfg.CABLE_PLUG_LOOSE_LEN))
    else:
        s_end = max(0.0, total - float(cfg.PLUG_RELIEF_L) / 2.0)
    sleeve, plug_side = split_at_length(sleeve_f, s_end)
    centre = fillet(pads, 1.0) + sleeve_f + [list(face)]

    # -- loose wires: pads -> jacket end (a U-turn into the sleeve mouth) --------
    wires = pad_wires(cfg, lay, sig)
    colors = dict(cfg.CABLE_WIRE_COLORS or {})
    # -- loose wires: sleeve end -> tails ('down'), or only inside the relief ---
    # the bundle fans out to the pin pitch above the notch's full-width height
    z_spread = min(max(lay.notch_floor + lay.notch_r_u, lay.bay_floor if lay.bay is not None else lay.H),
                   fz - bend - 0.5)
    tail_y = back_y - float(cfg.PLUG_TAIL_L)
    for k, s in enumerate(sig):
        o = (k - (n - 1) / 2.0) * wd
        xt = fx + pin_x[k]
        if env["exit"] == "down":
            # follow the centreline (bundle offset o) up the riser, then fan out
            pts = [(p[0] + o, p[1], p[2]) for p in plug_side
                   if p[1] <= y_drop + 1e-6 and p[2] <= z_spread + 1e-6]
            if not pts:                    # the sleeve already ends above the fan-out
                pts = [(plug_side[0][0] + o, plug_side[0][1], plug_side[0][2])]
            if pts[-1][2] < z_spread - 1e-6:
                pts.append((Xn + o, y_drop, z_spread))
            pts += [(xt, y_drop, fz - bend), (xt, end_y, fz), (xt, tail_y, fz)]
        else:
            pts = [(fx + o * 0.5, end_y + 0.5, fz), (xt, back_y - 0.5, fz), (xt, tail_y, fz)]
        wires.append({"signal": s, "color": colors.get(s, "#888888"), "part": "plug",
                      "points": [_r(p) for p in fillet(pts, max(0.6, bend))]})

    return {
        "centerline": [_r(p) for p in centre],
        "sleeve": [_r(p) for p in sleeve],
        "wires": wires,
        "sleeve_len": round(polyline_length(sleeve), 2),
        "envelope": env,
    }
