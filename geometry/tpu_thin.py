"""Thin TPU insert: the optional third "Top" of the rest (config.py TPU_THIN_*).

Same plan as the TPU insert (geometry/tpu.py insert_plan: the nose, the front
corners, the front of both ends and the crown back to TPU_BALLAST_GAP in front
of the ballast pockets, around the rigid collar), so the TPU covers the same
area. Only the underside differs: one plane tilted up toward the back,

    z = z0 + s * y        (s = tan(tilt))

instead of the flat floor at TPU_FLOOR_Z. A flat floor cannot be thin: the top
rises from 6.5 mm at the nose to ~11.8 mm across the insert and the nose needs
the floor low (TPU_MIN_EDGE_ANGLE). The plane is set by two rules:

    z0(s)  = min over the inner footprint and the nose crest of
             (top_z - s * y) - TPU_THIN_T
             (TPU_THIN_T of TPU at the thinnest spot: the back seam with
             the default tilt, the nose crest when the plane is flat)
    s      = the smallest tilt whose edge, where the plane leaves the nose /
             ends, is >= TPU_MIN_EDGE_ANGLE + TPU_THIN_EDGE_MARGIN (true
             dihedral angle; bisection). A flatter plane would feather the
             nose, a steeper one only adds TPU.

The cutters are tpu.py's own (tpu.cutter / tpu.insert_cutter on this plan with
floor_z = z0: plan prism, pegs, blind holes, 45 deg bed chamfer), built flat
and sheared by z += s * y. The shear keeps vertical lines vertical (seam walls,
pegs, hole walls: the insert still presses straight down onto vertical pegs)
and every vertical distance (floor -> peg top, hole depth, TPU thickness), and
turns horizontal faces parallel to the plane (tray floor, peg tops, hole
roofs, the bed face). So, as for the TPU insert, base + insert == the rigid
rest minus the designed relief (bed-chamfer strip + peg holes), and the rigid
STLs cannot change (only reads the rest manifolds).

The insert's STL is saved in its print pose: rotated by -tilt about X so the
plane is the bed (z = 0); print it as it loads (no supports: the only
downward faces are the bed face, the hole roofs - bridges, as on the TPU
insert - and the 0.4 mm bed chamfers, which lean up to 45 deg + tilt). The
manifest matrix (print -> assembly) places it in the preview, like the docks.
"""

import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.geometry import Point, Polygon

from . import common as C
from . import tpu

SUFFIX = " (or --set TPU_THIN_ENABLED=False)"
MAX_TILT_DEG = 25.0      # steepest underside tried; beyond it the edge rule is a config error
# shared TPU_* knobs that also shape the thin insert (TPU_DENSITY / TPU_MASS_INFILLS
# only change the mass estimate, so they can never make it fail)
SHARED = ("TPU_INSERT_DEPTH", "TPU_BALLAST_GAP", "TPU_POCKET_COLLAR", "TPU_TEXT_KEEPOUT", "TPU_MIN_EDGE_ANGLE",
          "TPU_PEG_D", "TPU_PEG_CHAMFER", "TPU_PEG_CLEARANCE", "TPU_BED_CHAMFER", "TPU_PEG_EDGE")


def _fail(msg):
    raise ValueError(msg + SUFFIX)


def overridden(cfg):
    """True when the build set a TPU_THIN_* constant: then a thin-insert config
    error stops the build. Otherwise (a rest override, or only SHARED knobs set
    for the TPU insert, e.g. TPU_INSERT_DEPTH=20) the thin top is skipped with a
    WARNING (tag tpu-thin) and everything else builds as it did before the thin top."""
    return any(str(k).startswith("TPU_THIN_") for k in (getattr(cfg, "_overrides", None) or {}))


def shear(s):
    """3x4 affine z += s * y (Manifold.transform)."""
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, float(s), 1.0, 0.0]]


def print_matrix(z0, s):
    """4x4 assembly -> print pose: rotate by -atan(s) about X (the plane z0 + s*y
    becomes horizontal at z0 cos), then down to z = 0. Its inverse is the
    manifest matrix (print -> assembly)."""
    th = math.atan(s)
    c, sn = math.cos(th), math.sin(th)
    return np.array([[1.0, 0.0, 0.0, 0.0],
                     [0.0, c, sn, 0.0],
                     [0.0, -sn, c, -z0 * c],
                     [0.0, 0.0, 0.0, 1.0]])


@dataclass
class ThinPlan:
    floor_z: float           # z0: the plane's height at y = 0 (flat-frame floor of the tpu.py cutters)
    s: float                 # dz/dy of the underside plane
    tilt_deg: float
    t_back: float            # TPU_THIN_T
    depth: float
    depth_auto: bool
    collar: float
    plan: Polygon
    rigid_keep: object
    inside: Polygon
    pegs: list
    peg_d: float
    peg_h: float
    peg_ch: float
    hole_d: float
    hole_h: float
    bed_chamfer: float
    peg_cover: float
    z_top: float             # flat-frame cutter top (above the rest after the shear)
    edge_angle_min: float    # deg, true dihedral where the plane leaves the nose / ends
    edge_angle_at: list
    thickness: dict
    wing_x: tuple
    text_keepout: bool
    print_matrix: np.ndarray
    notes: list = field(default_factory=list)

    def plane_z(self, y):
        return self.floor_z + self.s * np.asarray(y, dtype=float)


# ---------------------------------------------------------------------------
# analytic limits
# ---------------------------------------------------------------------------

def edge_angles(surf, plan, z0, s, nd=400):
    """True dihedral angle (deg) between the insert's underside (the plane
    z0 + s*y) and the outer surface where the plane leaves it, at every
    outline sample inside `plan`; and the crossing points (x, y, z). Marches
    inward along each outline normal through the elliptic round-over (as
    rest.Surface builds it) to the first point on or above the plane; the
    angle is 180 - angle(n_top, n_plane_down), n_top from the top_z gradient.
    On the vertical wall (plane below the round-over) n_top is the wall
    normal. 0 where the plane is above the whole round-over (no edge: fails)."""
    ol = surf.outline
    m = shapely.contains_xy(plan, ol.pts[:, 0], ol.pts[:, 1])
    if not m.any():
        return np.array([90.0]), np.zeros((1, 3))
    P, N = ol.pts[m], ol.nrm[m]
    a, b, wt = surf.edge_a[m], surf.edge_b[m], surf.wall_top[m]
    n2 = np.array([0.0, s, -1.0]) / math.hypot(1.0, s)
    u = np.linspace(0.0, 1.0, nd)
    d = a[:, None] * u[None, :]
    rx = P[:, 0, None] - N[:, 0, None] * d
    ry = P[:, 1, None] - N[:, 1, None] * d
    w = 1.0 - u
    zs = surf.h(rx.ravel(), ry.ravel()).reshape(rx.shape) - b[:, None] * (1.0 - np.sqrt(np.maximum(1.0 - w * w, 0.0)))
    f = zs - (z0 + s * ry)
    ge = f >= 0.0
    has = ge.any(axis=1)
    j = np.argmax(ge, axis=1)
    k = np.arange(len(P))
    j0 = np.maximum(j - 1, 0)
    f0, f1 = f[k, j0], f[k, j]
    d0, d1 = d[k, j0], d[k, j]
    t = np.where((j > 0) & (f1 != f0), -f0 / np.where(f1 != f0, f1 - f0, 1.0), 0.0)
    dd = np.where(j > 0, d0 + (d1 - d0) * t, 0.0)
    cx, cy = P[:, 0] - N[:, 0] * dd, P[:, 1] - N[:, 1] * dd
    e = 0.02
    gx = (surf.top_z(cx + e, cy) - surf.top_z(cx - e, cy)) / (2 * e)
    gy = (surf.top_z(cx, cy + e) - surf.top_z(cx, cy - e)) / (2 * e)
    n1 = np.column_stack([-gx, -gy, np.ones_like(gx)])
    n1 /= np.linalg.norm(n1, axis=1)[:, None]
    ang = np.degrees(np.pi - np.arccos(np.clip(n1 @ n2, -1.0, 1.0)))
    wall = (z0 + s * P[:, 1]) <= wt
    nw = np.column_stack([N, np.zeros(len(N))])
    ang_w = np.degrees(np.pi - np.arccos(np.clip(nw @ n2, -1.0, 1.0)))
    ang = np.where(wall, ang_w, np.where(has, ang, 0.0))
    cz = z0 + s * np.where(wall, P[:, 1], cy)
    pts = np.column_stack([np.where(wall, P[:, 0], cx), np.where(wall, P[:, 1], cy), cz])
    return ang, pts


def probe_points(surf, inside, nose_r, step=0.5):
    """Points where the thickness rule applies: a step grid inside the footprint
    plus 0.25 mm samples of its boundary (the back seam), both >= the widest
    round-over + 0.5 inside the outline (the TPU insert's 'inner' rule); and
    the straight nose crest (y = REST_FRONT_NOSE_R, a full round-over depth
    from the outline), where the TPU is thinnest when the plane is flat (verify
    checks TPU at the nose crest, as for the TPU insert). Returns (px, py) of
    the inner points and (cx, cy) of the crest points."""
    x0, y0, x1, y1 = inside.bounds
    gx, gy = np.meshgrid(np.arange(x0 + step / 2, x1, step), np.arange(y0 + step / 2, y1, step))
    gx, gy = gx.ravel(), gy.ravel()
    m = shapely.contains_xy(inside, gx, gy)
    bxy = np.asarray(inside.exterior.segmentize(0.25).coords)
    px, py = np.concatenate([gx[m], bxy[:, 0]]), np.concatenate([gy[m], bxy[:, 1]])
    dd = shapely.distance(shapely.points(px, py), surf.outline.ring)
    inner = dd >= float(surf.edge_a.max()) + 0.5
    cx = np.arange(x0 + step / 2, x1, step)
    cy = np.full_like(cx, float(nose_r))
    k = shapely.contains_xy(inside, cx, cy)
    cx, cy = cx[k], cy[k]
    k = shapely.distance(shapely.points(cx, cy), surf.outline.ring) >= float(nose_r) - 1e-3
    return px[inner], py[inner], cx[k], cy[k]


def solve_plane(surf, plan, px, py, top, t_min, angle, max_tilt=MAX_TILT_DEG):
    """(z0, s, min edge angle, crossing point) of the thinnest legal plane:
    TPU >= t_min at every probe point, edge >= angle. None when no tilt up to
    max_tilt reaches the angle."""
    base = top.copy()

    def z0_of(s):
        return float((base - s * py).min()) - t_min

    def amin(s):
        ang, pts = edge_angles(surf, plan, z0_of(s), s)
        i = int(np.argmin(ang))
        return float(ang[i]), pts[i]
    s_max = math.tan(math.radians(max_tilt))
    if amin(0.0)[0] >= angle:
        lo = hi = 0.0
    else:
        grid = np.linspace(0.0, s_max, 26)
        hi = next((float(v) for v in grid[1:] if amin(v)[0] >= angle), None)
        if hi is None:
            return None
        lo = float(grid[np.searchsorted(grid, hi) - 1])
        while hi - lo > 1e-6:
            mid = 0.5 * (lo + hi)
            if amin(mid)[0] >= angle:
                hi = mid
            else:
                lo = mid
    a, at = amin(hi)
    return z0_of(hi), hi, a, at


# ---------------------------------------------------------------------------
# plan + config errors
# ---------------------------------------------------------------------------

def params(cfg, lay, surf):
    """Plan (shared with the TPU insert), the solved underside plane, pegs and
    the analytic limits. Raises ValueError naming the knob."""
    W, H = lay.W, lay.H
    ip = tpu.insert_plan(cfg, lay, surf, fail=_fail)
    depth, plan, inside = ip.depth, ip.plan, ip.inside
    T = float(cfg.TPU_THIN_T)
    target = float(cfg.TPU_MIN_EDGE_ANGLE) + float(cfg.TPU_THIN_EDGE_MARGIN)

    # 1. the plane: thinnest TPU = TPU_THIN_T, edge >= TPU_MIN_EDGE_ANGLE + margin
    px, py, cx, cy = probe_points(surf, inside, cfg.REST_FRONT_NOSE_R)
    if not len(px):
        _fail("the thin TPU insert has no area inside the edge round-overs (TPU_INSERT_DEPTH too small)")
    px, py = np.concatenate([px, cx]), np.concatenate([py, cy])
    top = surf.top_z(px, py)
    sol = solve_plane(surf, plan, px, py, top, T, target)
    if sol is None:
        _fail(f"TPU_THIN_T {T:g}: no underside tilt up to {MAX_TILT_DEG:g} deg keeps the edge at the nose / ends "
              f">= TPU_MIN_EDGE_ANGLE {cfg.TPU_MIN_EDGE_ANGLE:g} + TPU_THIN_EDGE_MARGIN "
              f"{cfg.TPU_THIN_EDGE_MARGIN:g} deg: raise TPU_THIN_T")
    z0, s, amin, at = sol
    plane = lambda y: z0 + s * np.asarray(y, dtype=float)  # noqa: E731
    # a low underside: tilted (s > 0), the edge rule set the tilt and a thicker back
    # needs less of it; flat, the thickness rule set the height
    lower = ("raise TPU_THIN_T (less tilt), or lower TPU_THIN_EDGE_MARGIN / TPU_MIN_EDGE_ANGLE" if s > 1e-9
             else "lower TPU_THIN_T")

    # 2. the plane above the bottom chamfer and over every underside recess below the insert
    lo_z = float(cfg.REST_BOTTOM_CHAMFER) + 0.3
    y_front = float(inside.bounds[1])
    if float(plane(y_front)) <= lo_z + 1e-9:
        _fail(f"TPU_THIN_T {T:g} puts the thin insert's underside at z {float(plane(y_front)):.2f} at its front "
              f"(<= REST_BOTTOM_CHAMFER + 0.3 = {lo_z:g}): {lower}")
    min_floor = float(cfg.MIN_FLOOR)
    for (bx, by) in lay.bumpers:
        disk = Point(bx, by).buffer(cfg.BUMPER_D / 2.0, quad_segs=16)
        if disk.intersects(inside):
            f = float(plane(disk.bounds[1])) - float(cfg.BUMPER_RECESS)
            if f < min_floor - 1e-9:
                _fail(f"the thin insert's underside leaves {f:.2f} mm over the bumper recess at ({bx:.1f}, "
                      f"{by:.1f}) (< MIN_FLOOR {min_floor:g}): {lower}")
    eng = lay.engrave or {}
    if cfg.ENGRAVE_TEXT and eng.get("face") == "bottom" and eng["geom"].intersects(inside):
        f = float(plane(eng["geom"].intersection(inside).bounds[1])) - float(cfg.ENGRAVE_DEPTH)
        if f < min_floor - 1e-9:
            _fail(f"the thin insert's underside leaves {f:.2f} mm over the bottom engraving (< MIN_FLOOR "
                  f"{min_floor:g}): {lower}")

    # 3. thickness (vertical) over the footprint
    step = 0.5
    gx, gy = np.meshgrid(np.arange(step / 2, W, step), np.arange(step / 2, depth, step))
    gx, gy = gx.ravel(), gy.ravel()
    m = shapely.contains_xy(inside, gx, gy)
    gx, gy = gx[m], gy[m]
    thick = surf.top_z(gx, gy) - plane(gy)
    ti = top - plane(py)
    i_min = int(np.argmin(ti))
    spans, wing_x = tpu.wing_spans(cfg, lay, ip.collar)
    nose_r = float(cfg.REST_FRONT_NOSE_R)

    def t_at(x, y):
        if not inside.contains(Point(x, y)):
            return None
        return round(float(surf.top_z([x], [y])[0] - plane(y)), 3)
    thickness = {"min_inside": round(float(ti[i_min]), 3),
                 "min_inside_at": [round(float(px[i_min]), 2), round(float(py[i_min]), 2)],
                 "max": round(float(thick.max()), 3), "max_inside": round(float(ti.max()), 3),
                 "nose_wing": t_at(wing_x[0], nose_r), "nose_centre": t_at(lay.tp_cx, nose_r),
                 "nose_profile": [[y, t_at(wing_x[0], y)] for y in (2.0, 4.0, 6.0, nose_r)],
                 "wing_profile": [[y, t_at(wing_x[0], y)] for y in (12.0, 15.0, 20.0, 25.0, round(depth - 0.5, 2))],
                 "centre_profile": [[y, t_at(lay.tp_cx, y)] for y in (12.0, 15.0, 18.0, 20.0, 23.0)]}

    # 4. pegs on the tilted floor: inside with TPU_PEG_EDGE to spare, TPU over the hole roofs
    r, h, ch = float(cfg.TPU_PEG_D) / 2.0, float(cfg.TPU_THIN_PEG_H), float(cfg.TPU_PEG_CHAMFER)
    head, clr, bch = float(cfg.TPU_THIN_PEG_HEADROOM), float(cfg.TPU_PEG_CLEARANCE), float(cfg.TPU_BED_CHAMFER)
    r_h = r + clr
    allowed = inside.buffer(-float(cfg.TPU_PEG_EDGE), quad_segs=C.QS)
    fits = lambda q: allowed.contains(Point(q).buffer(r, quad_segs=16))  # noqa: E731
    if cfg.TPU_THIN_PEGS is None:
        # auto: one row at y_p, 2 per wing at 25 % / 75 % of the wing span, plus 2 in front
        # of the trackpad at 25 % / 75 % of the pocket opening, which pin the middle of the
        # long strip (that pair is left out where it does not fit, e.g. round a top engraving)
        y_p = round(nose_r + 3.0, 1)
        pegs = [(round(a + f * (b - a), 2), y_p) for a, b in spans if b - a >= 2 * r for f in (0.25, 0.75)]
        mid = [(round(lay.open_x0 + f * (lay.open_x1 - lay.open_x0), 2), y_p) for f in (0.25, 0.75)]
        if all(fits(q) for q in mid):
            pegs = sorted(pegs + mid)
    else:
        pegs = [(float(x), float(y)) for x, y in cfg.TPU_THIN_PEGS]
    if pegs and not h > ch:
        _fail(f"TPU_THIN_PEG_H {h:g} must be > TPU_PEG_CHAMFER {ch:g}")
    if pegs and bch > h - ch - 1e-9:
        _fail(f"TPU_BED_CHAMFER {bch:g} must stay below the straight part of the thin insert's pegs "
              f"(TPU_THIN_PEG_H - TPU_PEG_CHAMFER = {h - ch:g})")
    covers = []
    for i, (qx, qy) in enumerate(pegs):
        if not fits((qx, qy)):
            _fail(f"thin TPU peg {i + 1} at ({qx:.1f}, {qy:.1f}) is outside the insert or closer than TPU_PEG_EDGE "
                  f"{cfg.TPU_PEG_EDGE:g} mm to its edge: move it (TPU_THIN_PEGS)")
        ddx, ddy = np.meshgrid(np.linspace(qx - r_h, qx + r_h, 9), np.linspace(qy - r_h, qy + r_h, 9))
        k = np.hypot(ddx - qx, ddy - qy) <= r_h + 1e-9
        cover = float((surf.top_z(ddx[k], ddy[k]) - plane(ddy[k])).min()) - (h + head)
        covers.append(cover)
        if cover < cfg.TPU_THIN_PEG_MIN_COVER - 1e-9:
            _fail(f"thin TPU peg {i + 1} at ({qx:.1f}, {qy:.1f}) leaves {cover:.2f} mm of TPU over its hole "
                  f"(< TPU_THIN_PEG_MIN_COVER {cfg.TPU_THIN_PEG_MIN_COVER:g}): lower TPU_THIN_PEG_H / "
                  f"TPU_THIN_PEG_HEADROOM, raise TPU_THIN_T or move the peg (TPU_THIN_PEGS)")
        for j in range(i):
            if math.hypot(qx - pegs[j][0], qy - pegs[j][1]) < 2 * r + 1.0:
                _fail(f"thin TPU pegs {j + 1} and {i + 1} overlap (keep their centres >= TPU_PEG_D + 1 apart)")

    return ThinPlan(floor_z=z0, s=s, tilt_deg=math.degrees(math.atan(s)), t_back=T, depth=depth,
                    depth_auto=ip.auto, collar=ip.collar, plan=plan, rigid_keep=ip.rigid_keep, inside=inside,
                    pegs=pegs, peg_d=2 * r, peg_h=h, peg_ch=ch, hole_d=2 * r_h, hole_h=h + head, bed_chamfer=bch,
                    peg_cover=min(covers) if covers else None, z_top=H + 2.0 + 5.0 * s,
                    edge_angle_min=amin, edge_angle_at=[round(float(v), 3) for v in at],
                    thickness=thickness, wing_x=wing_x, text_keepout=ip.text_keepout,
                    print_matrix=print_matrix(z0, s), notes=list(ip.notes))


# ---------------------------------------------------------------------------
# solids
# ---------------------------------------------------------------------------

def split(cfg, rests, tp):
    """rests: {variant: finished rigid rest Manifold}. Returns {"insert": Manifold
    (assembly frame, cut from the first variant), "insert_print": the same in
    its print pose, "bases": {variant: Manifold}, "info": dict for the manifest}."""
    vids = list(rests)
    S = shear(tp.s)
    cut = tpu.cutter(tp).transform(S)
    insert = rests[vids[0]] ^ tpu.insert_cutter(tp).transform(S)
    bases = {v: rests[v] - cut for v in vids}
    for name, m in [("thin TPU insert", insert)] + [(f"rest-{v}-tpu-thin base", b) for v, b in bases.items()]:
        status = str(m.status())
        if not status.endswith("NoError"):
            raise RuntimeError(f"{name}: boolean failed: {status}")
        if m.is_empty() or m.volume() <= 0:
            raise RuntimeError(f"{name}: empty / non-positive volume")
    n = len(insert.decompose())
    if n != 1:
        raise RuntimeError(f"thin TPU insert has {n} bodies, want 1 (a bug, not a config error)")
    insert_print = insert.transform(tp.print_matrix[:3].tolist())
    vol, area = float(insert.volume()), float(insert.surface_area())
    info = {
        "t_back": tp.t_back, "plane_z0": round(tp.floor_z, 4), "plane_slope": round(tp.s, 6),
        "tilt_deg": round(tp.tilt_deg, 3),
        "insert_depth": round(tp.depth, 4), "depth_auto": tp.depth_auto, "collar": tp.collar,
        "ballast_gap": float(cfg.TPU_BALLAST_GAP),
        "pegs": [[round(x, 4), round(y, 4)] for x, y in tp.pegs],
        "peg_d": tp.peg_d, "peg_h": tp.peg_h, "peg_chamfer": tp.peg_ch,
        "hole_d": round(tp.hole_d, 4), "hole_depth": round(tp.hole_h, 4), "bed_chamfer": tp.bed_chamfer,
        "peg_cover_min": None if tp.peg_cover is None else round(tp.peg_cover, 3),
        "edge_angle_min_deg": round(tp.edge_angle_min, 2), "edge_angle_at": tp.edge_angle_at,
        "thickness": tp.thickness,
        "insert_plan_cm2": round(tp.inside.area / 100.0, 2),
        "insert_volume_cm3": round(vol / 1000.0, 3), "insert_area_cm2": round(area / 100.0, 2),
        "insert_tpu_g": tpu.insert_grams(cfg, vol, area), "text_keepout": tp.text_keepout,
        "print_matrix": [[round(float(v), 9) for v in row] for row in tp.print_matrix],
        "routes": ["separate"],
    }
    return {"insert": insert, "insert_print": insert_print, "bases": bases, "info": info}
