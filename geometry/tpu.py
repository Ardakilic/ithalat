"""TPU insert: the optional soft "Top" of the rest (config.py TPU_*).

A flat-bottomed TPU insert replaces the front of the rigid rest - the nose, the
front corners, the front of both ends and the crown back to just in front of
the ballast pockets - where wrists and palms land. It is cut out of the
finished rigid rest itself (rest.build_rest, every cutter already applied):

    plan     = box(-5, -5, W + 5, depth) - rigid_keep
    cutter   = prism(plan, TPU_FLOOR_Z, H + 2) - pegs
    base[v]  = rest[v] - cutter
    insert   = rest[first variant] & (prism - holes - bed chamfers)
                                                (the same for every variant)

so base + insert == the rigid rest minus a small designed relief: the outside
shape, the pocket and its recess, the cable path and every fit stay as
verified, and the rigid STLs cannot change (this module only reads the rest
manifolds). rigid_keep is a collar around the pocket opening (plus the text
box with ENGRAVE_FACE='top'). The pegs stand on the tray floor; the insert's
blind holes are TPU_PEG_HEADROOM deeper and TPU_PEG_CLEARANCE wider (their
roofs are D + 2 x clearance - 2 x chamfer bridges), and its underside edges
along every seam and round the hole mouths carry a 45 deg TPU_BED_CHAMFER, so
elephant foot, a sagging hole roof or a tall peg cannot lift it off the floor.
The relief lies only in that bed-edge strip and inside the holes.

No cutter face is coincident with a face of the rest (the rest.py rule): the
back wall keeps TPU_BALLAST_GAP from the ballast pockets, the collar is
>= 1 mm outside the rim bevel, the text keep-out >= TPU_TEXT_KEEPOUT from every
letter, and the floor >= MIN_FLOOR above every underside recess. The insert's
cutter is one lofted mesh (the plan inset by TPU_BED_CHAMFER at the floor, 45
deg up to the plan) and each countersunk hole one lathe mesh, so the chamfers
need no boolean that could run along an edge.

One pair of STLs serves both print routes: print the insert alone (it rests on
its flat underside, no supports) and press it onto the pegs, or load base +
insert as one object with two parts on a two-nozzle / toolchanger printer.
"""

import math
from dataclasses import dataclass, field

import manifold3d
import numpy as np
import shapely
from manifold3d import Manifold
from shapely.geometry import Point, Polygon

from . import common as C

SUFFIX = " (or --set TPU_ENABLED=False)"
PEG_SEGS = 48      # circle resolution of the pegs (= the insert's holes)


def _fail(msg):
    raise ValueError(msg + SUFFIX)


def overridden(cfg):
    """True when the build set any TPU_* constant: then a TPU config error stops
    the build; otherwise generate / verify skip the TPU top with a WARNING, so a
    rigid-only override that leaves no room for a sound insert still builds."""
    return any(str(k).startswith("TPU_") for k in (getattr(cfg, "_overrides", None) or {}))


@dataclass
class TpuPlan:
    floor_z: float           # tray floor = the insert's flat underside
    depth: float             # insert back edge (y)
    depth_auto: bool
    collar: float
    plan: Polygon            # cutter plan: box(-5, -5, W + 5, depth) - rigid_keep
    rigid_keep: object       # collar (+ top-text keep-out)
    inside: Polygon          # plan inside the rest outline (the insert footprint at the chamfer top)
    pegs: list               # [(x, y)]
    peg_d: float
    peg_h: float
    peg_ch: float
    hole_d: float            # insert hole diameter: TPU_PEG_D + 2 x TPU_PEG_CLEARANCE
    hole_h: float            # insert hole depth: TPU_PEG_H + TPU_PEG_HEADROOM
    bed_chamfer: float       # 45 deg chamfer on the insert's underside edges (seams, hole mouths)
    peg_cover: float         # min TPU over the hole roofs (analytic)
    z_top: float             # cutter top (above the rest)
    edge_angle_min: float    # deg, where the floor plane cuts the nose / ends
    floor_z_max: float       # highest TPU_FLOOR_Z that keeps TPU_MIN_EDGE_ANGLE
    thickness: dict          # analytic vertical TPU thickness (top_z - floor)
    wing_x: tuple            # (left, right) middle of the wing spans (probes)
    text_keepout: bool
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# analytic limits
# ---------------------------------------------------------------------------

def edge_angles(surf, plan, z_f):
    """Angle (deg) between the insert's flat underside and the outer surface at
    every outline sample inside `plan`. The floor plane z_f cuts the elliptic
    round-over (d = a(1 - cos t), drop = b(1 - sin t)) at sin t = 1 - (h - z_f) / b,
    where its slope is b cos t / (a sin t); 90 deg where it meets the vertical
    wall (wall top above the floor)."""
    ol = surf.outline
    m = shapely.contains_xy(plan, ol.pts[:, 0], ol.pts[:, 1])
    if not m.any():
        return np.array([90.0])
    a, b = surf.edge_a[m], surf.edge_b[m]
    h = surf.h(ol.pts[m, 0], ol.pts[m, 1])
    st = np.clip(1.0 - (h - z_f) / b, 1e-9, 1.0)
    ang = np.degrees(np.arctan2(b * np.cos(np.arcsin(st)), a * st))
    return np.where(surf.wall_top[m] <= z_f, ang, 90.0)


def floor_limit(surf, plan, min_angle, lo, hi):
    """Highest floor z whose edge angle is still >= min_angle (the angle only
    falls as the floor rises: bisection)."""
    def f(z):
        return float(edge_angles(surf, plan, z).min())
    if f(lo) < min_angle:
        return lo
    if f(hi) >= min_angle:
        return hi
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if f(mid) >= min_angle:
            lo = mid
        else:
            hi = mid
    return lo


# ---------------------------------------------------------------------------
# plan + config errors
# ---------------------------------------------------------------------------

def params(cfg, lay, surf):
    """Insert plan, pegs and the analytic limits for one rest layout. Raises
    ValueError (the message names the knob) for configs that cannot give a sound
    insert; generate.py / verify.py turn that into `config error: ...`."""
    W, D, H = lay.W, lay.D, lay.H
    ol = surf.outline
    z_f = float(cfg.TPU_FLOOR_Z)
    gap = float(cfg.TPU_BALLAST_GAP)
    collar = float(cfg.TPU_POCKET_COLLAR)
    notes = []

    # insert depth: auto = TPU_BALLAST_GAP in front of the ballast pockets
    auto = cfg.TPU_INSERT_DEPTH is None
    if auto:
        depth = (min(b["y0"] for b in lay.ballast) - gap) if lay.ballast else D / 2.0
    else:
        depth = float(cfg.TPU_INSERT_DEPTH)
    min_depth = float(cfg.REST_FRONT_NOSE_R) + 3.0
    if depth < min_depth - 1e-9:
        what = ("the ballast pockets (BALLAST_CENTER_Y) leave" if auto and lay.ballast
                else "TPU_INSERT_DEPTH gives")
        _fail(f"{what} a TPU insert only {depth:.2f} mm deep (< REST_FRONT_NOSE_R + 3 = {min_depth:g}): "
              f"it would not reach past the nose")
    if depth > lay.open_y1 - 1.0 + 1e-9:
        _fail(f"TPU_INSERT_DEPTH {depth:g} reaches behind the trackpad pocket (keep <= "
              f"{lay.open_y1 - 1.0:.2f}): the back strip with the cable notch stays rigid")

    # rigid collar around the pocket: rim, bevel, walls, ledge stay PETG / PLA
    lo_c = float(cfg.POCKET_RIM_CHAMFER) + 1.0
    if not (lo_c - 1e-9 <= collar <= float(cfg.TP_BEZEL) + 1e-9):
        _fail(f"TPU_POCKET_COLLAR {collar:g} must be within POCKET_RIM_CHAMFER + 1 = {lo_c:g} .. TP_BEZEL "
              f"{cfg.TP_BEZEL:g}: the rim needs rigid material, and the seam must lie on the flat island "
              f"around the pocket (flush at REST_HEIGHT)")
    rigid_keep = lay.opening.buffer(collar, quad_segs=C.QS)
    text_keepout = False
    eng = lay.engrave or {}
    if cfg.ENGRAVE_TEXT and eng.get("face") == "top" and not eng["geom"].is_empty:
        # the auto-placed text top lands exactly on the collar seam otherwise
        # (coincident faces); keeping its box rigid also engraves it in PETG
        box = shapely.box(*eng["geom"].bounds).buffer(float(cfg.TPU_TEXT_KEEPOUT), join_style="mitre")
        rigid_keep = rigid_keep.union(box)
        text_keepout = True
        notes.append(f"NOTE: top engraving: the text area (+{cfg.TPU_TEXT_KEEPOUT:g} mm) stays rigid; "
                     f"the TPU insert goes around it")
    plan = shapely.box(-5.0, -5.0, W + 5.0, depth).difference(rigid_keep)
    inside = plan.intersection(ol.polygon)
    if plan.is_empty or plan.geom_type != "Polygon" or inside.geom_type != "Polygon":
        n = max(len(C.poly_parts(plan)), len(C.poly_parts(inside)))
        _fail(f"the TPU insert plan falls apart into {n} pieces (TPU_POCKET_COLLAR / TPU_INSERT_DEPTH / "
              f"top engraving)")

    # everything rigid behind / beside the insert keeps its wall
    for b in lay.ballast:
        d = shapely.box(b["x0"], b["y0"], b["x1"], b["y1"]).distance(plan)
        if d < gap - 1e-6:
            _fail(f"TPU_INSERT_DEPTH {depth:g} runs into the {b['side']} ballast pocket (keep <= "
                  f"{b['y0'] - gap:.2f}: TPU_BALLAST_GAP {gap:g} of rigid wall in front of it)")
    notch = shapely.box(lay.notch_x - cfg.CABLE_NOTCH_W / 2.0, lay.notch_y0,
                        lay.notch_x + cfg.CABLE_NOTCH_W / 2.0, D)
    for name, g in (("cable path", lay.cable_area), ("plug bay", lay.bay), ("cable notch", notch)):
        if g is not None and g.distance(plan) < 1.0 - 1e-9:
            _fail(f"the TPU insert reaches the {name} (keep it >= 1 mm away: TPU_INSERT_DEPTH / "
                  f"TPU_POCKET_COLLAR)")

    # 1. tray floor over every underside recess below the insert
    min_floor = float(cfg.MIN_FLOOR)
    for (bx, by) in lay.bumpers:
        if Point(bx, by).buffer(cfg.BUMPER_D / 2.0, quad_segs=16).intersects(inside):
            f = z_f - float(cfg.BUMPER_RECESS)
            if f < min_floor - 1e-9:
                _fail(f"TPU_FLOOR_Z {z_f:g} leaves {f:.2f} mm over the bumper recess at ({bx:.1f}, {by:.1f}) "
                      f"(< MIN_FLOOR {min_floor:g}): raise TPU_FLOOR_Z")
    if cfg.ENGRAVE_TEXT and eng.get("face") == "bottom" and eng["geom"].intersects(inside):
        f = z_f - float(cfg.ENGRAVE_DEPTH)
        if f < min_floor - 1e-9:
            _fail(f"TPU_FLOOR_Z {z_f:g} leaves {f:.2f} mm over the bottom engraving (< MIN_FLOOR "
                  f"{min_floor:g}): raise TPU_FLOOR_Z")

    # 2. front edge: no thin feather where the floor plane cuts the nose / ends
    amin = float(edge_angles(surf, plan, z_f).min())
    z_max = floor_limit(surf, plan, float(cfg.TPU_MIN_EDGE_ANGLE), float(cfg.REST_BOTTOM_CHAMFER) + 0.3, H)
    if amin < cfg.TPU_MIN_EDGE_ANGLE - 1e-9:
        _fail(f"TPU_FLOOR_Z {z_f:g} leaves a {amin:.1f} deg edge where the insert's flat underside meets the "
              f"nose / ends (< TPU_MIN_EDGE_ANGLE {cfg.TPU_MIN_EDGE_ANGLE:g} deg: a thin feather that lifts): "
              f"keep TPU_FLOOR_Z <= {math.floor(z_max * 10.0 + 1e-6) / 10.0:.1f}")

    # 5. TPU thickness inside the edge round-overs
    step = 0.5
    gx, gy = np.meshgrid(np.arange(step / 2, W, step), np.arange(step / 2, depth, step))
    gx, gy = gx.ravel(), gy.ravel()
    m = shapely.contains_xy(inside, gx, gy)
    gx, gy = gx[m], gy[m]
    thick = surf.top_z(gx, gy) - z_f
    dd = shapely.distance(shapely.points(gx, gy), ol.ring)
    inner = dd >= float(surf.edge_a.max()) + 0.5
    if not inner.any():
        _fail("the TPU insert has no area inside the edge round-overs (TPU_INSERT_DEPTH too small)")
    i_min = int(np.argmin(np.where(inner, thick, np.inf)))
    tmin = float(thick[i_min])
    if tmin < cfg.TPU_MIN_T - 1e-9:
        _fail(f"TPU_FLOOR_Z {z_f:g} leaves only {tmin:.2f} mm of TPU at ({gx[i_min]:.1f}, {gy[i_min]:.1f}) "
              f"inside the edge round-overs (< TPU_MIN_T {cfg.TPU_MIN_T:g}): lower TPU_FLOOR_Z")

    x_lo = float(cfg.REST_END_EDGE_R) + float(cfg.REST_END_BULGE) + 5.0
    spans = [(x_lo, lay.open_x0 - collar - 10.0), (lay.open_x1 + collar + 10.0, W - x_lo)]
    wing_x = tuple(0.5 * (a + b) for a, b in spans)
    nose_r = float(cfg.REST_FRONT_NOSE_R)

    def t_at(x, y):
        if not inside.contains(Point(x, y)):
            return None
        return round(float(surf.top_z([x], [y])[0]) - z_f, 3)
    thickness = {"min_inside": round(tmin, 3), "min_inside_at": [round(float(gx[i_min]), 2),
                                                                  round(float(gy[i_min]), 2)],
                 "max": round(float(thick.max()), 3),
                 "nose_wing": t_at(wing_x[0], nose_r), "nose_centre": t_at(lay.tp_cx, nose_r),
                 "nose_profile": [[y, t_at(wing_x[0], y)] for y in (2.0, 4.0, 6.0, nose_r)]}

    # 6. pegs: inside the insert with TPU_PEG_EDGE to spare, TPU over their tops
    r, h, ch = float(cfg.TPU_PEG_D) / 2.0, float(cfg.TPU_PEG_H), float(cfg.TPU_PEG_CHAMFER)
    head, clr, bch = float(cfg.TPU_PEG_HEADROOM), float(cfg.TPU_PEG_CLEARANCE), float(cfg.TPU_BED_CHAMFER)
    r_h = r + clr
    if cfg.TPU_PEGS is None:
        # near the back of the insert: the TPU over the pegs is thickest there,
        # and they sit behind the middle of the estimated palm band
        y_p = round(min(0.8 * depth, depth - r - float(cfg.TPU_PEG_EDGE) - 0.5), 1)
        pegs = [(round(a + f * (b - a), 2), y_p) for a, b in spans if b - a >= 2 * r for f in (0.25, 0.75)]
    else:
        pegs = [(float(x), float(y)) for x, y in cfg.TPU_PEGS]
    if pegs and bch > h - ch - 1e-9:
        _fail(f"TPU_BED_CHAMFER {bch:g} must stay below the straight part of the pegs (TPU_PEG_H - "
              f"TPU_PEG_CHAMFER = {h - ch:g})")
    allowed = inside.buffer(-float(cfg.TPU_PEG_EDGE), quad_segs=C.QS)
    covers = []
    for i, (px, py) in enumerate(pegs):
        if not allowed.contains(Point(px, py).buffer(r, quad_segs=16)):
            _fail(f"TPU peg {i + 1} at ({px:.1f}, {py:.1f}) is outside the insert or closer than TPU_PEG_EDGE "
                  f"{cfg.TPU_PEG_EDGE:g} mm to its edge: move it (TPU_PEGS)")
        ddx, ddy = np.meshgrid(np.linspace(px - r_h, px + r_h, 9), np.linspace(py - r_h, py + r_h, 9))
        k = np.hypot(ddx - px, ddy - py) <= r_h + 1e-9
        cover = float(surf.top_z(ddx[k], ddy[k]).min()) - (z_f + h + head)
        covers.append(cover)
        if cover < cfg.TPU_PEG_MIN_COVER - 1e-9:
            _fail(f"TPU peg {i + 1} at ({px:.1f}, {py:.1f}) leaves {cover:.2f} mm of TPU over its hole "
                  f"(< TPU_PEG_MIN_COVER {cfg.TPU_PEG_MIN_COVER:g}): lower TPU_PEG_H / TPU_PEG_HEADROOM "
                  f"or move the peg")
        for j in range(i):
            if math.hypot(px - pegs[j][0], py - pegs[j][1]) < 2 * r + 1.0:
                _fail(f"TPU pegs {j + 1} and {i + 1} overlap (keep their centres >= TPU_PEG_D + 1 apart)")

    return TpuPlan(floor_z=z_f, depth=depth, depth_auto=auto, collar=collar, plan=plan, rigid_keep=rigid_keep,
                   inside=inside, pegs=pegs, peg_d=2 * r, peg_h=h, peg_ch=ch, hole_d=2 * r_h, hole_h=h + head,
                   bed_chamfer=bch, peg_cover=min(covers) if covers else None,
                   z_top=H + 2.0,
                   edge_angle_min=amin, floor_z_max=z_max, thickness=thickness, wing_x=wing_x,
                   text_keepout=text_keepout, notes=notes)


# ---------------------------------------------------------------------------
# solids
# ---------------------------------------------------------------------------

def peg_solid(x, y, floor_z, d, h, ch, segs=PEG_SEGS):
    """One locating peg as a single convex hull (no coplanar cylinder / cone
    faces): its foot starts 1 mm below the floor so its side crosses the floor
    plane cleanly, a 45 deg chamfer of `ch` on top."""
    r = d / 2.0
    a = np.linspace(0.0, 2.0 * math.pi, segs, endpoint=False)
    rings = [np.column_stack([x + rr * np.cos(a), y + rr * np.sin(a), np.full(segs, z)])
             for z, rr in ((floor_z - 1.0, r), (floor_z + h - ch, r), (floor_z + h, r - ch))]
    return Manifold.hull_points(np.vstack(rings))


def cutter(tp):
    """prism(plan, floor, above the rest) minus the pegs: cut from the rest, it
    leaves the base."""
    body = C.prism(tp.plan, tp.floor_z, tp.z_top)
    return C.subtract_all(body, [peg_solid(px, py, tp.floor_z, tp.peg_d, tp.peg_h, tp.peg_ch)
                                 for px, py in tp.pegs])


HOLE_BELOW = 0.5     # the insert's holes start this far below the floor (no coplanar bottom face)


def _inset_ring(xy, c):
    """Mitre offset of a closed ring (no repeated last point) by c to the left
    of its direction, i.e. into an oriented polygon: every edge moves by c and
    stays parallel, so the loft's chamfer faces are planar and exactly 45 deg.
    An edge too short to survive the offset (a 0.08 mm stub where the back seam
    meets the collar's arc) collapses, as in a straight skeleton: both its ends
    go to the point where its neighbours' offset lines meet. Returns one inset
    point per ring vertex (collapsed ends share a point)."""
    n = len(xy)
    d = np.roll(xy, -1, axis=0) - xy
    d /= np.linalg.norm(d, axis=1)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])      # left normal of edge i (i -> i + 1)
    base = xy + c * nrm                              # a point on each edge's offset line

    def meet(i, j):                                  # offset lines of edges i and j
        cr = d[i, 0] * d[j, 1] - d[i, 1] * d[j, 0]
        if abs(cr) < 1e-12:                          # collinear: no corner
            return base[j].copy()
        w = base[j] - base[i]
        t = (w[0] * d[j, 1] - w[1] * d[j, 0]) / cr
        return base[i] + t * d[i]

    active = list(range(n))
    while True:
        m = len(active)
        if m < 3:
            raise RuntimeError("TPU bed chamfer: the plan collapses under TPU_BED_CHAMFER")
        pts = [meet(active[k - 1], active[k]) for k in range(m)]   # pts[k] starts active edge k
        lens = [float(np.dot(pts[(k + 1) % m] - pts[k], d[active[k]])) for k in range(m)]
        k = int(np.argmin(lens))
        if lens[k] > 1e-9:
            break
        del active[k]                                # this edge vanishes: drop it and re-meet
    start = {e: pts[k] for k, e in enumerate(active)}
    out = np.empty_like(xy)
    for v in range(n):                               # vertex v -> start of the next surviving edge
        e = v
        while e not in start:
            e = (e + 1) % n
        out[v] = start[e]
    if float(np.linalg.norm(out - xy, axis=1).max()) > 10.0 * c:
        raise RuntimeError("TPU bed chamfer: a seam corner is too sharp for a mitre offset")
    return out


def _clean_ring(coords, tol=1e-7):
    xy = np.asarray(coords, dtype=float)[:-1]
    keep = np.linalg.norm(xy - np.roll(xy, 1, axis=0), axis=1) > tol
    return xy[keep]


def loft_prism(plan, z0, c, z1):
    """prism(plan, z0, z1) with a 45 deg chamfer of c on every bottom edge, as
    one mesh: the bottom face is the plan inset by c (mitre) at z0, the chamfer
    rises to the plan at z0 + c, the walls go straight up to z1. The plan's own
    edges outside the rest are chamfered too, harmlessly."""
    if c <= 0:
        return C.prism(plan, z0, z1)
    rings = []
    for poly in C.poly_parts(shapely.geometry.polygon.orient(plan, sign=1.0)):
        rings += [_clean_ring(poly.exterior.coords)] + [_clean_ring(r.coords) for r in poly.interiors]
    insets, lo_maps = [], []
    for r in rings:
        a = _inset_ring(r, c)
        same = np.all(np.isclose(a, np.roll(a, 1, axis=0), rtol=0.0, atol=1e-12), axis=1)
        lo_maps.append((np.cumsum(~same) - 1) % int((~same).sum()))   # ring vertex -> unique inset point
        insets.append(a[~same])
    want = plan.buffer(-c, join_style="mitre", mitre_limit=10.0).area
    got = sum(Polygon(a).area * (1 if shapely.LinearRing(a).is_ccw else -1) for a in insets)
    if not shapely.Polygon(insets[0], insets[1:]).is_valid or abs(got - want) > 1e-3 * max(want, 1.0):
        raise RuntimeError("TPU bed chamfer: the inset plan is not valid")
    verts, faces, bottom, top = [], [], [], []
    n0 = 0
    for ring, ins, lmap in zip(rings, insets, lo_maps):
        n, nl = len(ring), len(ins)
        verts += [np.column_stack([ins, np.full(nl, z0)]), np.column_stack([ring, np.full(n, z0 + c)]),
                  np.column_stack([ring, np.full(n, z1)])]
        lo = n0 + lmap
        mid = n0 + nl + np.arange(n)
        hi = mid + n
        lo1, mid1, hi1 = np.roll(lo, -1), np.roll(mid, -1), np.roll(mid, -1) + n
        quad = lo != lo1                              # a collapsed edge leaves a triangle
        faces += [np.column_stack([lo, lo1, mid1])[quad], np.column_stack([lo, mid1, mid]),
                  np.column_stack([mid, mid1, hi1]), np.column_stack([mid, hi1, hi])]
        bottom.append(n0 + np.arange(nl))
        top.append(hi)
        n0 += nl + 2 * n
    tri_b = np.asarray(manifold3d.triangulate(insets), dtype=np.int64)
    tri_t = np.asarray(manifold3d.triangulate(rings), dtype=np.int64)
    faces += [np.concatenate(bottom)[tri_b][:, ::-1], np.concatenate(top)[tri_t]]
    return C.manifold_from_arrays(np.vstack(verts), np.vstack(faces))


def _lathe(x, y, profile, segs=PEG_SEGS):
    """Solid of revolution about (x, y) from [(z, r), ...] (z ascending), as one
    mesh with flat caps; the rings are in phase with peg_solid's."""
    a = np.linspace(0.0, 2.0 * math.pi, segs, endpoint=False)
    verts = [np.column_stack([x + rr * np.cos(a), y + rr * np.sin(a), np.full(segs, z)]) for z, rr in profile]
    faces = []
    for j in range(len(profile) - 1):
        lo = j * segs + np.arange(segs)
        hi = lo + segs
        lo1, hi1 = np.roll(lo, -1), np.roll(hi, -1)
        faces += [np.column_stack([lo, lo1, hi1]), np.column_stack([lo, hi1, hi])]
    last = (len(profile) - 1) * segs
    fan = np.arange(1, segs - 1)
    faces += [np.column_stack([np.zeros_like(fan), fan + 1, fan]),
              np.column_stack([np.full_like(fan, last), last + fan, last + fan + 1])]
    return C.manifold_from_arrays(np.vstack(verts), np.vstack(faces))


def hole_solid(tp, x, y):
    """One blind hole of the insert: TPU_PEG_CLEARANCE wider and TPU_PEG_HEADROOM
    deeper than the peg, same top chamfer (the roof bridge), a 45 deg
    TPU_BED_CHAMFER countersink round its mouth."""
    z_f, r_h, h_h, ch, c = tp.floor_z, tp.hole_d / 2.0, tp.hole_h, tp.peg_ch, tp.bed_chamfer
    e = HOLE_BELOW
    prof = ([(z_f - e, r_h + c + e), (z_f + c, r_h)] if c > 0 else [(z_f - e, r_h)])
    prof += [(z_f + h_h - ch, r_h), (z_f + h_h, r_h - ch)]
    return _lathe(x, y, prof)


def insert_cutter(tp):
    """The loft over the plan (bed chamfer along every seam) minus the holes:
    cut from the rest, it leaves the insert."""
    return C.subtract_all(loft_prism(tp.plan, tp.floor_z, tp.bed_chamfer, tp.z_top),
                          [hole_solid(tp, px, py) for px, py in tp.pegs])


def split(cfg, rests, tp):
    """rests: {variant: finished rigid rest Manifold}. Returns {"insert": Manifold
    (cut from the first variant; the pocket is rigid, so it is the same for every
    variant), "bases": {variant: Manifold}, "info": dict for the manifest}."""
    vids = list(rests)
    cut = cutter(tp)
    insert = rests[vids[0]] ^ insert_cutter(tp)
    bases = {v: rests[v] - cut for v in vids}
    for name, m in [("TPU insert", insert)] + [(f"rest-{v}-tpu base", b) for v, b in bases.items()]:
        status = str(m.status())
        if not status.endswith("NoError"):
            raise RuntimeError(f"{name}: boolean failed: {status}")
        if m.is_empty() or m.volume() <= 0:
            raise RuntimeError(f"{name}: empty / non-positive volume")
    n = len(insert.decompose())
    if n != 1:
        raise RuntimeError(f"TPU insert has {n} bodies, want 1 (a bug, not a config error)")
    vol, area = float(insert.volume()), float(insert.surface_area())
    shell = min(vol, area * float(cfg.MASS_SHELL_T))
    dens = float(cfg.TPU_DENSITY)
    grams = {f"{p:g}%": round((shell + p / 100.0 * (vol - shell)) / 1000.0 * dens, 1)
             for p in cfg.TPU_MASS_INFILLS}
    grams["100%"] = round(vol / 1000.0 * dens, 1)
    info = {
        "floor_z": tp.floor_z, "insert_depth": round(tp.depth, 4), "depth_auto": tp.depth_auto,
        "collar": tp.collar, "ballast_gap": float(cfg.TPU_BALLAST_GAP),
        "pegs": [[round(x, 4), round(y, 4)] for x, y in tp.pegs],
        "peg_d": tp.peg_d, "peg_h": tp.peg_h, "peg_chamfer": tp.peg_ch,
        "hole_d": round(tp.hole_d, 4), "hole_depth": round(tp.hole_h, 4), "bed_chamfer": tp.bed_chamfer,
        "peg_cover_min": None if tp.peg_cover is None else round(tp.peg_cover, 3),
        "edge_angle_min_deg": round(tp.edge_angle_min, 2), "floor_z_max": round(tp.floor_z_max, 3),
        "thickness": tp.thickness,
        "insert_plan_cm2": round(tp.inside.area / 100.0, 2),
        "insert_volume_cm3": round(vol / 1000.0, 3), "insert_area_cm2": round(area / 100.0, 2),
        "insert_tpu_g": grams, "text_keepout": tp.text_keepout,
        "routes": ["separate", "multi-material"],
    }
    return {"insert": insert, "bases": bases, "info": info}
