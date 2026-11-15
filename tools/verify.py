#!/usr/bin/env python3
"""Geometry self-test for ithalat. Exits 1 on any failure.

    python3 tools/verify.py [--rebuild] [-v] [generate.py overrides]
    make verify GEN_ARGS="--glass-t 0.7"

By default it measures the STL files in stl/ (what you will print); a missing
STL - or every STL with --rebuild - is built in memory instead. Expected
values always come from config.py + the same overrides, so verifying with
different GEN_ARGS than the last `make generate` fails on purpose (stale STLs).

Measurements are made on the meshes only: vertical ray casts (depths, floors,
skins, engraving, rim height at the pocket wall), horizontal slices (pocket
opening and corner radius, notch / riser / plug bay widths, ballast walls and
distance), point-in-solid tests (cable path) and signed distances (a CABLE_D
cable swept along groove -> tunnel -> riser -> notch; the pigtail plug's
housing + strain relief docked at the dock face, which must clear the rest by
PLUG_MIN_CLEARANCE). Every connector in CONNECTORS is checked: each dock in
its own frame (plugs vs cut-outs, setback, open connector pocket) and, together
with build/manifest.json, in the assembly (placement matrix, connector face,
per-variant cable routes pads -> notch -> dock face / grip).

USB-C ('usbc'): rays and slices on the dock (well depth / section / entry
chamfer / bottom-wall sag allowance, shoulder wall, window vs receptacle and
its crush ribs, mouth vs well floor, board pocket, rear stop, floors, open wire
channel and lock-prong slots, finger-brace flats), the retainer (fit = crush
bumps only, tongue over the shell, shell press ribs, screw pilots and thread,
hold-down margin, prongs behind the back clip blades and backed at the lip),
the grip halves (walls, push rib, wire clamp and bands, screw thread, pegs,
board clamp incl. layer rounding at USBC_PRINT_LAYER, shell collar, epoxy key
groove, no overlap) and the mated assembly (nose clearance in the well and the
tilt before it bears, nose gap, seated depth, min gaps grip <-> dock /
retainer / rest, also withdrawn); hardware envelopes (boards, shells, diode)
must hold no printed material beyond the designed crush interference; the
clip retention calculation must keep USBC_RETENTION_MIN; every USB-C part is
checked for support-free printing (widest bridge / steep overhang in print
orientation). WARN rows are advisories and never fail the run.
"""

import argparse
import math
import os
import sys
import warnings

import numpy as np
import shapely
import trimesh
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from geometry import common as C  # noqa: E402
from geometry import plug  # noqa: E402
from geometry import rest  # noqa: E402
from geometry.cfg import add_cli_args, load_config, overrides_from_args  # noqa: E402

TOL = 0.01      # mm, for exact features (depths, ledges)
BBOX_TOL = 0.05  # mm, outer dimensions


# ---------------------------------------------------------------------------
# measuring helpers
# ---------------------------------------------------------------------------

def nudge(x, y):
    """Tiny offset so a vertical ray never runs exactly down a mesh edge."""
    return x + 0.00731, y + 0.00419


def hits(mesh, x, y, from_below=True):
    """Ascending z of every surface a vertical line through (x, y) crosses."""
    x, y = nudge(x, y)
    o = np.array([[x, y, -50.0]])
    loc, _, _ = mesh.ray.intersects_location(o, np.array([[0.0, 0.0, 1.0]]), multiple_hits=True)
    loc = np.asarray(loc).reshape(-1, 3)
    zs = sorted(float(z) for z in loc[:, 2])
    out = []
    for z in zs:
        if not out or z - out[-1] > 1e-4:
            out.append(z)
    return out


def first_down(mesh, x, y):
    h = hits(mesh, x, y)
    return h[-1] if h else None


def section(mesh, z):
    sec = mesh.section(plane_origin=[0.0, 0.0, float(z)], plane_normal=[0.0, 0.0, 1.0])
    if sec is None:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        planar, _ = sec.to_planar(to_2D=np.eye(4))
    polys = list(planar.polygons_full)
    return unary_union(polys) if polys else None


def holes_of(geom):
    out = []
    for p in C.poly_parts(geom):
        out += [Polygon(i) for i in p.interiors]
    return out


def top_facet_max_angle(mesh, lay, cfg):
    n = mesh.face_normals
    c = mesh.triangles_center
    adj = mesh.face_adjacency
    ang = np.degrees(mesh.face_adjacency_angles)
    top = (n[adj[:, 0], 2] > 0.05) & (n[adj[:, 1], 2] > 0.05)
    mid = (c[adj[:, 0]] + c[adj[:, 1]]) / 2
    keep = ~shapely.contains_xy(lay.opening.buffer(cfg.POCKET_RIM_CHAMFER + 1.0), mid[:, 0], mid[:, 1])
    keep &= ~((np.abs(mid[:, 0] - lay.notch_x) < cfg.CABLE_NOTCH_W / 2 + 1.5) & (mid[:, 1] > lay.notch_y0 - 1.5))
    if lay.bay is not None:
        keep &= ~shapely.contains_xy(lay.bay.buffer(cfg.PLUG_BAY_CHAMFER + 1.5), mid[:, 0], mid[:, 1])
    if cfg.ENGRAVE_FACE == "top" and cfg.ENGRAVE_TEXT:
        keep &= ~shapely.contains_xy(lay.engrave["geom"].buffer(1.0), mid[:, 0], mid[:, 1])
    sel = top & keep
    i = int(np.argmax(np.where(sel, ang, -1)))
    return float(ang[i]), mid[i]


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

class Report:
    def __init__(self, verbose):
        self.rows = []
        self.verbose = verbose

    def check(self, scope, name, ok, detail="", warn=False):
        """warn=True: a failed check prints WARN and does not fail the run
        (used for advisories that depend on parts outside this repo)."""
        self.rows.append((scope, name, bool(ok), detail, bool(warn)))

    def near(self, scope, name, value, want, tol=TOL, unit="mm"):
        ok = value is not None and abs(value - want) <= tol
        vtxt = "none" if value is None else f"{value:.3f}"
        self.check(scope, name, ok, f"{vtxt} {unit} (want {want:.3f} +-{tol:g})")

    def at_least(self, scope, name, value, want, unit="mm", warn=False):
        ok = value is not None and value >= want - 1e-6
        vtxt = "none" if value is None else f"{value:.3f}"
        self.check(scope, name, ok, f"{vtxt} {unit} (want >= {want:g})", warn=warn)

    def at_most(self, scope, name, value, want, unit="mm", warn=False):
        ok = value is not None and value <= want + 1e-6
        vtxt = "none" if value is None else f"{value:.3f}"
        self.check(scope, name, ok, f"{vtxt} {unit} (want <= {want:g})", warn=warn)

    def print(self):
        fails = [r for r in self.rows if not r[2] and not r[4]]
        warns = [r for r in self.rows if not r[2] and r[4]]
        w = max(len(r[0]) for r in self.rows)
        n = max(len(r[1]) for r in self.rows)
        scope = None
        for s, name, ok, detail, warn in self.rows:
            if s != scope:
                print(f"\n== {s}")
                scope = s
            tag = "PASS" if ok else ("WARN" if warn else "FAIL")
            print(f"  {tag}  {name:{n}s}  {detail}")
        checks = len(self.rows) - len(warns)
        print(f"\n{checks - len(fails)}/{checks} checks passed"
              + (f", {len(warns)} warning(s)" if warns else "")
              + (f", {len(fails)} FAILED:" if fails else " - all good."))
        for s, name, _, detail, _ in warns:
            print(f"  WARN [{s}] {name}: {detail}")
        for s, name, _, detail, _ in fails:
            print(f"  FAIL [{s}] {name}: {detail}")
        return not fails


# ---------------------------------------------------------------------------
# rest checks
# ---------------------------------------------------------------------------

def verify_rest(R, cfg, vid, glass_t, mesh, source):
    sc = f"rest-{vid} ({source})"
    lay, surf = rest.plan(cfg, glass_t)
    W, D, H = cfg.REST_WIDTH, cfg.REST_DEPTH, cfg.REST_HEIGHT

    R.check(sc, "watertight", mesh.is_watertight)
    R.check(sc, "winding consistent", mesh.is_winding_consistent)
    R.check(sc, "positive volume", mesh.volume > 0, f"{mesh.volume / 1000:.2f} cm3")
    lo, hi = mesh.bounds
    R.near(sc, "bbox min x", lo[0], 0.0, BBOX_TOL)
    R.near(sc, "bbox min y", lo[1], 0.0, BBOX_TOL)
    R.near(sc, "bbox min z", lo[2], 0.0, BBOX_TOL)
    R.near(sc, "width (bbox x)", hi[0] - lo[0], W, BBOX_TOL)
    R.near(sc, "depth (bbox y)", hi[1] - lo[1], D, BBOX_TOL)
    R.near(sc, "height (bbox z)", hi[2] - lo[2], H, BBOX_TOL)
    R.near(sc, "max Z == REST_HEIGHT", float(mesh.vertices[:, 2].max()), H, 1e-3)

    ang, where = top_facet_max_angle(mesh, lay, cfg)
    R.at_most(sc, "top smoothness (max facet angle)", ang, 8.0, unit=f"deg at ({where[0]:.1f},{where[1]:.1f})")

    # pocket opening (slice just under the rim bevel, above every ledge)
    z_open = H - cfg.POCKET_RIM_CHAMFER_H - 0.3
    sec = section(mesh, z_open)
    hole = None
    for hp in holes_of(sec):
        if hp.contains(Point(lay.tp_cx, lay.tp_cy)):
            hole = hp
    if hole is None:
        R.check(sc, "pocket opening found", False, f"no hole at z={z_open:.2f}")
    else:
        x0, y0, x1, y1 = hole.bounds
        R.near(sc, "pocket opening width", x1 - x0, lay.open_w, BBOX_TOL)
        R.near(sc, "pocket opening depth", y1 - y0, lay.open_d, BBOX_TOL)
        R.near(sc, "pocket back margin", D - y1, cfg.TP_BACK_MARGIN, BBOX_TOL)
        R.near(sc, "pocket centre x", (x0 + x1) / 2, cfg.TP_CENTER_X, BBOX_TOL)
        # corner radius from the diagonal inset of the slice: inset = R (sqrt2 - 1)
        d = shapely.distance(Point(x1, y1), hole)
        R.near(sc, "pocket corner radius (diagonal inset)", d / (math.sqrt(2.0) - 1.0), lay.open_r, 0.05)
        # the parts themselves (module / glass outline with their corner radii)
        # placed in the measured opening: they must fit with a gap at the corners
        parts = [("module", cfg.TP_WIDTH, cfg.TP_DEPTH, cfg.TP_CORNER_R)]
        if glass_t > 0:
            parts.append(("glass", cfg.GLASS_WIDTH, cfg.GLASS_DEPTH, cfg.GLASS_CORNER_R))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for name, pw, pd, pr in parts:
            part = C.rounded_rect(cx - pw / 2, cy - pd / 2, cx + pw / 2, cy + pd / 2, pr)
            inside = hole.buffer(1e-6).contains(part)
            gap = hole.exterior.distance(part) if inside else -part.difference(hole).area
            diag = min(shapely.distance(Point(px, py), part) - shapely.distance(Point(px, py), hole)
                       for px in (x0, x1) for py in (y0, y1))
            R.check(sc, f"{name} (R{pr:g} corners) fits the opening", inside and gap >= 0.1 - 1e-6,
                    f"min gap {gap:.3f} mm, corner gap {diag:.3f} mm (want >= 0.1)")
    # rim bevel: the vertical pocket wall must rise above the glass / film top
    surf_top = H - cfg.TP_SURFACE_RECESS
    xw, yw = lay.open_x0 - 0.02, lay.tp_cy
    R.at_least(sc, "rim z at the pocket wall (surface top + 0.05)", first_down(mesh, xw, yw), surf_top + 0.05)

    # ledge all around (rays just inside the module edge, mid-edges + corners-ish)
    m2a = lay.m2a
    e = cfg.POCKET_LEDGE - 0.2
    ledge_pts = {"back": (cfg.TP_WIDTH * 0.25, e), "back-r": (cfg.TP_WIDTH * 0.8, e),
                 "front": (cfg.TP_WIDTH / 2, cfg.TP_DEPTH - e),
                 "left": (e, cfg.TP_DEPTH / 2), "right": (cfg.TP_WIDTH - e, cfg.TP_DEPTH / 2),
                 "front flat": (6.0, 42.0)}
    zs = []
    for name, (mx, my) in ledge_pts.items():
        z = first_down(mesh, *m2a(mx, my))
        zs.append(z)
        R.near(sc, f"ledge z ({name})", z, lay.ledge_z)
    z_ledge = float(np.median([z for z in zs if z is not None])) if any(zs) else None
    if z_ledge is not None:
        R.near(sc, "pocket depth (top -> ledge)", H - z_ledge, lay.pocket_depth)
        pcb_top = z_ledge + cfg.TP_PCB_T
        liner_top = pcb_top + cfg.TP_ADHESIVE_T
        if glass_t > 0:
            R.near(sc, "glass top z (rim - recess)", liner_top + glass_t, H - cfg.TP_SURFACE_RECESS)
        else:
            R.near(sc, "PCB/liner top z (rim - recess)", liner_top, H - cfg.TP_SURFACE_RECESS)
        R.check(sc, "PCB top z", True, f"{pcb_top:.3f} mm")

    # relief cavity covers component box + 1.0
    comp = lay.component_box
    ring = comp.buffer(0.95, quad_segs=8).exterior
    worst = max(first_down(mesh, *ring.interpolate(t, normalized=True).coords[0]) or 99
                for t in np.linspace(0, 1, 48, endpoint=False))
    R.at_most(sc, "relief covers comp. box + 1.0 (max floor z)", worst, lay.cavity_z + TOL)
    cz = first_down(mesh, comp.centroid.x + 3.0, comp.centroid.y - 3.0)
    R.near(sc, "relief depth below PCB", (z_ledge or 0) - (cz or 0), cfg.POCKET_CAVITY_DEPTH)

    # solder well under the 6 pads + ZIF
    px0, px1, py0, py1 = cfg.TP_PADS_BOX
    pitch = (px1 - px0) / 6.0
    pad_z = [first_down(mesh, *m2a(px0 + pitch * (i + 0.5), (py0 + py1) / 2)) for i in range(6)]
    R.at_most(sc, "solder well under all 6 pads (max z)", max(z or 99 for z in pad_z), lay.well_z + TOL)
    zx0, zx1, zy0, zy1 = cfg.TP_ZIF_BOX
    R.at_most(sc, "solder well under the ZIF", first_down(mesh, *m2a((zx0 + zx1) / 2, (zy0 + zy1) / 2)),
              lay.well_z + TOL)

    # push-out holes: open all the way through
    for i, (hx, hy) in enumerate(lay.push_holes):
        h = hits(mesh, hx, hy)
        R.check(sc, f"push hole {i + 1} through (D{cfg.PUSH_HOLE_D:g})", len(h) == 0,
                f"{len(h)} surfaces on the axis")
        h2 = hits(mesh, hx + cfg.PUSH_HOLE_D / 2 + 0.3, hy)
        R.check(sc, f"push hole {i + 1} diameter edge", len(h2) > 0, "material just outside")

    # floors >= MIN_FLOOR under the pocket, well, groove, tunnel, notch
    region = unary_union([lay.opening, shapely.box(lay.notch_x - cfg.CABLE_NOTCH_W / 2 - 0.5, lay.tunnel_y0,
                                                   lay.notch_x + cfg.CABLE_NOTCH_W / 2 + 0.5, D - 0.3)])
    x0, y0, x1, y1 = region.bounds
    gx, gy = np.meshgrid(np.arange(x0 + 0.25, x1, 1.0), np.arange(y0 + 0.25, y1, 1.0))
    gx, gy = gx.ravel(), gy.ravel()
    inside = shapely.contains_xy(region, gx, gy)
    fmin, fwhere = 1e9, None
    for x, y in zip(gx[inside], gy[inside]):
        h = hits(mesh, x, y)
        if len(h) >= 2:
            f = h[1] - h[0]
            if f < fmin:
                fmin, fwhere = f, (x, y, h[0], h[1])
    R.at_least(sc, "min floor under pocket/channels", fmin, cfg.MIN_FLOOR,
               unit=f"mm at ({fwhere[0]:.1f},{fwhere[1]:.1f})" if fwhere else "mm")

    # cable: tunnel, skin, riser, notch
    Xn = lay.notch_x
    zmid = (lay.tunnel_floor + lay.tunnel_ceiling) / 2
    path = [(Xn, (lay.mod_y1 - cfg.POCKET_LEDGE / 2), zmid),          # under the ledge
            (Xn, (lay.open_y1 + lay.notch_y0) / 2, zmid),              # under the rim
            (Xn, (lay.notch_y0 + lay.riser_y1) / 2, lay.notch_floor - 0.5),  # riser
            (Xn, D - 0.5, lay.notch_floor + 1.0)]                      # notch exit
    gl = list(lay.groove_line.coords)
    path += [(x, y, lay.tunnel_floor + 0.6) for x, y in gl[1:]]
    inside_solid = mesh.contains(np.array(path))
    R.check(sc, "cable path open (well -> tunnel -> riser -> notch)", not inside_solid.any(),
            f"{int(inside_solid.sum())}/{len(path)} path points inside material")
    h = hits(mesh, Xn, lay.mod_y1 - cfg.POCKET_LEDGE / 2)
    skin_ledge = (h[-1] - h[-2]) if len(h) >= 3 else None
    R.at_least(sc, "tunnel skin under the ledge", skin_ledge, cfg.CABLE_SKIN)
    if len(h) >= 3:
        R.at_least(sc, "tunnel height", h[-2] - h[-3], cfg.CABLE_D)
    h = hits(mesh, Xn, (lay.open_y1 + lay.notch_y0) / 2)
    R.at_least(sc, "tunnel skin under the rim", (h[-1] - h[-2]) if len(h) >= 3 else None, cfg.CABLE_SKIN)
    R.near(sc, "notch floor (back-top edge)", first_down(mesh, Xn, D - 1.0), lay.notch_floor, 0.05)

    def gap_width(z, y, near=5.0):
        s = section(mesh, z)
        if s is None:
            return None
        g = LineString([(Xn - 40, y), (Xn + 40, y)]).difference(s)
        w = [p.length for p in getattr(g, "geoms", [g]) if abs(p.centroid.x - Xn) < near]
        return max(w) if w else None
    # U-notch width: chord of its R(u) bottom below the bay floor, else full width
    ru = lay.notch_r_u
    zc = min(lay.notch_floor + ru + 0.3, lay.bay_floor - 0.2, H - 0.3)
    dz = zc - lay.notch_floor
    want = cfg.CABLE_NOTCH_W if dz >= ru else (cfg.CABLE_NOTCH_W - 2 * ru) + 2 * math.sqrt(ru * ru - (ru - dz) ** 2)
    R.near(sc, f"notch width on the back face (z {zc:.2f})", gap_width(zc, D - 0.3), want, 0.05)
    hb = hits(mesh, Xn, D - cfg.CABLE_RISER_BACK_WALL / 2)
    R.check(sc, "back face closed below the notch", len(hb) >= 2 and hb[0] < 0.01 and hb[1] > lay.notch_floor - 0.06,
            f"solid {hb[0]:.2f}..{hb[1]:.2f}" if len(hb) >= 2 else "no material")
    # riser -> notch passage never narrower than the channel (vertical through the riser)
    y_rc = (lay.notch_y0 + lay.riser_y1) / 2
    zs = np.arange(lay.tunnel_floor + 0.3, lay.notch_floor + ru + 0.3, 0.15)
    wmin = min((gap_width(z, y_rc) or 0.0) for z in zs)
    R.at_least(sc, "riser -> notch passage width (min over z)", wmin, cfg.CABLE_CHANNEL_W - 0.05)
    # plug bay
    if lay.bay is not None:
        bx = lay.notch_x + (cfg.CABLE_NOTCH_W / 2 + cfg.PLUG_BAY_W / 2) / 2      # between notch and bay wall
        R.near(sc, "plug bay floor", first_down(mesh, bx, D - cfg.PLUG_BAY_L / 2), lay.bay_floor, TOL)
        R.near(sc, "plug bay width on the back face", gap_width((lay.bay_floor + H - cfg.PLUG_BAY_CHAMFER) / 2,
                                                              D - 0.3, near=8.0), cfg.PLUG_BAY_W, 0.05)
        zb = (lay.bay_floor + H - cfg.PLUG_BAY_CHAMFER) / 2
        sb = section(mesh, zb)
        yb = None
        if sb is not None:
            g = LineString([(bx, D - 30), (bx, D + 1)]).difference(sb)
            seg = [p for p in getattr(g, "geoms", [g]) if p.bounds[3] >= D - 0.01]
            yb = (D - seg[0].bounds[1]) if seg else None
        R.near(sc, "plug bay length from the back face", yb, D - lay.bay_y0, 0.05)

    # a sleeved CABLE_D cable passes groove -> tunnel -> riser -> notch: sweep
    # its centreline (resting on the floors) and measure the distance to the
    # nearest surface (signed distance, positive inside material)
    route = plug.resample(plug.sleeve_passage(cfg, lay), 0.25)
    clear = -trimesh.proximity.signed_distance(mesh, route)
    i = int(np.argmin(clear))
    R.at_least(sc, f"sleeved cable D{cfg.CABLE_D:g} clearance along groove/tunnel/riser",
               float(clear[i]), cfg.CABLE_D / 2 - 0.05,
               unit=f"mm centre-to-surface at ({route[i][0]:.1f},{route[i][1]:.1f},{route[i][2]:.1f})")

    # bumpers
    for i, (bx, by) in enumerate(lay.bumpers):
        h = hits(mesh, bx, by)
        R.near(sc, f"bumper {i + 1} recess", h[0] if h else None, cfg.BUMPER_RECESS)

    # ballast pockets
    if cfg.BALLAST_ENABLED:
        R.check(sc, "ballast pockets present", len(lay.ballast) == 2, f"{len(lay.ballast)} placed")
        sec1 = section(mesh, 1.0)
        rect_holes = [hp for hp in holes_of(sec1) if hp.area > 300]
        sec0 = section(mesh, 0.02)
        bed_holes = [hp for hp in holes_of(sec0) if hp.area > 300]
        bed_outer = max(C.poly_parts(sec0), key=lambda p: p.area) if sec0 is not None else None
        for bp in lay.ballast:
            cx, cy = (bp["x0"] + bp["x1"]) / 2, (bp["y0"] + bp["y1"]) / 2
            h = hits(mesh, cx, cy)
            R.near(sc, f"ballast {bp['side']} depth", h[0] if h else None, bp["depth"])
            gx, gy = np.meshgrid(np.linspace(bp["x0"] + 0.3, bp["x1"] - 0.3, 12),
                                 np.linspace(bp["y0"] + 0.3, bp["y1"] - 0.3, 4))
            skin = min((hh[1] - hh[0]) for hh in (hits(mesh, x, y) for x, y in zip(gx.ravel(), gy.ravel()))
                       if len(hh) >= 2)
            R.at_least(sc, f"ballast {bp['side']} top skin", skin, cfg.BALLAST_MIN_TOP_SKIN)
            mine = [hp for hp in rect_holes if hp.contains(Point(cx, cy))]
            if hole is not None and mine:
                R.at_least(sc, f"ballast {bp['side']} plan distance to the pad", mine[0].distance(hole),
                           cfg.BALLAST_MIN_DIST_FROM_TP)
            else:
                R.check(sc, f"ballast {bp['side']} found in slice", False)
            # wall beside the pocket at the bed (footprint inside the bottom chamfer)
            mine0 = [hp for hp in bed_holes if hp.contains(Point(cx, cy))]
            if mine0 and bed_outer is not None:
                R.at_least(sc, f"ballast {bp['side']} wall at the bed (z 0.02)",
                           mine0[0].distance(bed_outer.exterior), cfg.BALLAST_WALL)
            want_bar = [float(v) for v in cfg.BALLAST_SIZE]
            same = all(abs(a - b) < 1e-6 for a, b in zip(bp["bar"], want_bar))
            R.check(sc, f"ballast {bp['side']} bar = BALLAST_SIZE", same,
                    f"placed {' x '.join(f'{v:g}' for v in bp['bar'])} mm, BALLAST_SIZE "
                    f"{' x '.join(f'{v:g}' for v in want_bar)}"
                    + ("" if same else " (shortened; buy the placed size)"),
                    warn=bool(cfg.BALLAST_AUTO_SHORTEN))
    # engraving
    if cfg.ENGRAVE_TEXT:
        geom = lay.engrave["geom"]
        parts = sorted(C.poly_parts(geom), key=lambda p: -p.area)
        dev = []
        for p in parts[:6]:
            q = p.buffer(-0.25)
            pt = (q if not q.is_empty else p).representative_point()
            h = hits(mesh, pt.x, pt.y)
            if cfg.ENGRAVE_FACE == "bottom":
                dev.append(abs((h[0] if h else 99) - cfg.ENGRAVE_DEPTH))
            else:
                want = float(surf.top_z([pt.x], [pt.y])[0]) - cfg.ENGRAVE_DEPTH
                dev.append(abs((h[-1] if h else 99) - want))
        R.at_most(sc, f"engraving depth {cfg.ENGRAVE_DEPTH:g} ({cfg.ENGRAVE_FACE}, max dev)", max(dev),
                  0.05 if cfg.ENGRAVE_FACE == "top" else TOL)
        R.check(sc, "engraving inside the rest", surf.outline.polygon.buffer(-1.0).contains(geom))


def verify_plug_vs_rest(R, cfg, cid, vid, glass_t, mesh):
    """Pogo / JST: the pigtail plug (housing + strain relief) docked at the
    dock face must clear this rest, and its wires must drop into the riser."""
    sc = f"{cid} plug vs rest-{vid}"
    lay, _ = rest.plan(cfg, glass_t)
    D = cfg.REST_DEPTH
    env = plug.plug_envelope(cfg, lay)
    for name in ("housing", "relief"):
        b = env[name]
        if b is None:
            continue
        pts = plug.box_surface_points(b, 0.4)
        pts = pts[pts[:, 1] <= D + 5.0]
        cl = float((-trimesh.proximity.signed_distance(mesh, pts)).min()) if len(pts) else 99.0
        R.at_least(sc, f"plug {name} clearance to the rest", cl, cfg.PLUG_MIN_CLEARANCE,
                   unit=f"mm ({b[1] - b[0]:g} x {b[3] - b[2]:g} x {b[5] - b[4]:g} box, bottom z {b[4]:.2f})")
    lo, hi = env["drop_range"]
    R.check(sc, f"plug exit '{env['exit']}': {env['drop_what']}", env["drop_ok"],
            f"turn at y {env['drop_y']:.2f}, riser allows {lo:.2f}..{hi:.2f}")


def plugs_in_cutouts(R, sc, cfg, mesh_local, centers):
    """Inside the plate thickness every piece of a plug (walls, clip blades)
    must fit its cut-out: group the slice pieces per switch position."""
    sec = section(mesh_local, -cfg.DOCK_PLATE_T / 2)
    pieces = C.poly_parts(sec) if sec is not None else []
    plugs = []
    for cx, cy in centers:
        mine = [p for p in pieces if abs(p.centroid.x - cx) < cfg.KEY_PITCH / 2 and abs(p.centroid.y - cy) < cfg.KEY_PITCH / 2]
        if mine:
            plugs.append(unary_union(mine))
    stray = len(pieces) - sum(len(C.poly_parts(p)) for p in plugs)
    R.check(sc, "plug count", len(plugs) == cfg.DOCK_KEYS and stray == 0,
            f"{len(plugs)} plugs ({len(pieces)} slice pieces, {stray} outside the cut-outs) at z=-{cfg.DOCK_PLATE_T / 2:g}")
    for i, p in enumerate(sorted(plugs, key=lambda p: p.centroid.x)):
        x0, y0, x1, y1 = p.bounds
        size = max(x1 - x0, y1 - y0)
        R.check(sc, f"plug {i + 1} < switch cut-out", size < cfg.DOCK_SWITCH_CUTOUT,
                f"{x1 - x0:.2f} x {y1 - y0:.2f} mm (cut-out {cfg.DOCK_SWITCH_CUTOUT:g})")


def dock_frame_checks(R, sc, cfg, mesh_local, info, body_h):
    """Dock-local fit shared by every dock: plugs, height, setback, cut-out cover."""
    lo, hi = mesh_local.bounds
    R.near(sc, "plugs reach DOCK_PLUG_DEPTH below the plate top", -float(lo[2]), cfg.DOCK_PLUG_DEPTH, 0.01)
    R.near(sc, "body height above the plate", float(hi[2]), body_h, 0.01)
    removed = sorted(c for r, c in cfg.REMOVED_KEYS if r == 3)
    want_x = [cfg.FIRST_KEY_X + c * cfg.KEY_PITCH - cfg.DOCK_CENTER_X for c in removed]
    got_x = sorted(float(c[0]) for c in info["plug_centers"])
    R.check(sc, "plugs on the removed switch centres", len(got_x) == len(want_x)
            and all(abs(a - b) < 0.02 for a, b in zip(got_x, want_x))
            and abs(cfg.DOCK_SWITCH_CENTER_Y - cfg.FRONT_ROW_Y) < 0.02,
            f"x {', '.join(f'{v:+.3f}' for v in got_x)} (want {', '.join(f'{v:+.3f}' for v in want_x)})")
    sec_top = section(mesh_local, 0.3)
    if sec_top is not None:
        bx0, by0, bx1, by1 = sec_top.bounds
        R.near(sc, "front face behind the keyboard front edge (setback)", by0 + cfg.DOCK_SWITCH_CENTER_Y,
               cfg.DOCK_FRONT_SETBACK, 0.05)
        cut = cfg.DOCK_SWITCH_CUTOUT / 2.0
        R.at_least(sc, "body covers the cut-outs (back overlap)", by1 - cut, 0.0)
        R.at_least(sc, "body covers the cut-outs (front overlap)", -cut - by0, 0.0)
        cell = cfg.DOCK_KEYS * cfg.KEY_PITCH / 2.0
        R.at_least(sc, "clearance to the neighbouring key cells", cell - max(-bx0, bx1), 0.5)


def verify_dock(R, cfg, cid, stl_path):
    sc = f"dock-{cid}"
    stl_name = "stl/" + os.path.basename(stl_path)
    try:
        from geometry import dock
    except Exception as e:  # noqa: BLE001
        R.check(sc, "geometry/dock.py importable", False, str(e))
        return
    mesh_local, print_T = dock.build_dock(cfg)
    R.check(sc, "watertight (built)", mesh_local.is_watertight)
    R.check(sc, "positive volume", mesh_local.volume > 0, f"{mesh_local.volume / 1000:.2f} cm3")
    # inside the plate thickness every piece of a plug (walls, clip blades)
    # must fit its cut-out: group the slice pieces per switch position
    sec = section(mesh_local, -cfg.DOCK_PLATE_T / 2)
    pieces = C.poly_parts(sec) if sec is not None else []
    try:
        centers = [tuple(c[:2]) for c in dock.dock_info(cfg)["plug_centers"]]
    except Exception:  # noqa: BLE001
        centers = [((i - (cfg.DOCK_KEYS - 1) / 2) * cfg.KEY_PITCH, 0.0) for i in range(cfg.DOCK_KEYS)]
    plugs = []
    for cx, cy in centers:
        mine = [p for p in pieces if abs(p.centroid.x - cx) < cfg.KEY_PITCH / 2 and abs(p.centroid.y - cy) < cfg.KEY_PITCH / 2]
        if mine:
            plugs.append(unary_union(mine))
    stray = len(pieces) - sum(len(C.poly_parts(p)) for p in plugs)
    R.check(sc, "plug count", len(plugs) == cfg.DOCK_KEYS and stray == 0,
            f"{len(plugs)} plugs ({len(pieces)} slice pieces, {stray} outside the cut-outs) at z=-{cfg.DOCK_PLATE_T / 2:g}")
    for i, p in enumerate(sorted(plugs, key=lambda p: p.centroid.x)):
        x0, y0, x1, y1 = p.bounds
        size = max(x1 - x0, y1 - y0)
        R.check(sc, f"plug {i + 1} < switch cut-out", size < cfg.DOCK_SWITCH_CUTOUT,
                f"{x1 - x0:.2f} x {y1 - y0:.2f} mm (cut-out {cfg.DOCK_SWITCH_CUTOUT:g})")
    pm = mesh_local.copy()
    pm.apply_transform(print_T)
    R.near(sc, "print orientation rests on z=0", float(pm.bounds[0][2]), 0.0, 1e-3)
    if os.path.exists(stl_path):
        m = trimesh.load(stl_path)
        R.check(sc, f"{stl_name} watertight", m.is_watertight)
        R.near(sc, "stl matches build (volume)", m.volume / 1000, pm.volume / 1000, 0.01, unit="cm3")
    else:
        R.check(sc, f"{stl_name} exists", False, "run `make generate`")

    # dock-local fit: body on the plate, plugs on the removed switch centres,
    # connector face flush with the front face and open
    info = dock.dock_info(cfg)
    body = info["body"]
    lo, hi = mesh_local.bounds
    R.near(sc, "plugs reach DOCK_PLUG_DEPTH below the plate top", -float(lo[2]), cfg.DOCK_PLUG_DEPTH, 0.01)
    R.near(sc, "body height above the plate", float(hi[2]), cfg.DOCK_BODY_H, 0.01)
    removed = sorted(c for r, c in cfg.REMOVED_KEYS if r == 3)
    want_x = [cfg.FIRST_KEY_X + c * cfg.KEY_PITCH - cfg.DOCK_CENTER_X for c in removed]
    got_x = sorted(float(c[0]) for c in info["plug_centers"])
    R.check(sc, "plugs on the removed switch centres", len(got_x) == len(want_x)
            and all(abs(a - b) < 0.02 for a, b in zip(got_x, want_x))
            and abs(cfg.DOCK_SWITCH_CENTER_Y - cfg.FRONT_ROW_Y) < 0.02,
            f"x {', '.join(f'{v:+.3f}' for v in got_x)} (want {', '.join(f'{v:+.3f}' for v in want_x)})")
    sec_top = section(mesh_local, 0.3)
    if sec_top is not None:
        bx0, by0, bx1, by1 = sec_top.bounds
        R.near(sc, "front face behind the keyboard front edge (setback)", by0 + cfg.DOCK_SWITCH_CENTER_Y,
               cfg.DOCK_FRONT_SETBACK, 0.05)
        cut = cfg.DOCK_SWITCH_CUTOUT / 2.0
        R.at_least(sc, "body covers the cut-outs (back overlap)", by1 - cut, 0.0)
        R.at_least(sc, "body covers the cut-outs (front overlap)", -cut - by0, 0.0)
        cell = cfg.DOCK_KEYS * cfg.KEY_PITCH / 2.0
        R.at_least(sc, "clearance to the neighbouring key cells", cell - max(-bx0, bx1), 0.5)
    face = np.asarray(info["connector_face_center"], dtype=float)
    R.near(sc, "connector face flush with the front face", float(face[1]), float(body["y0"]), 0.05)
    pk = info["connector_pocket"]
    ex, ez = pk["w"] / 2 - 0.5, pk["h"] / 2 - 0.4      # stay clear of the crush ribs
    probe = np.array([[face[0] + dx, face[1] + 0.5, face[2] + dz]
                      for dx in (-ex, 0.0, ex) for dz in (-ez, 0.0, ez)])
    inside = mesh_local.contains(probe)
    R.check(sc, "connector pocket open at the face", not inside.any(),
            f"{int(inside.sum())}/{len(probe)} probe points inside material")
    return mesh_local, print_T, info




# ---------------------------------------------------------------------------
# helpers for the USB-C checks
# ---------------------------------------------------------------------------

def axis_hits(mesh, origin, axis, sign=1.0):
    """Coordinates (along `axis`) where a ray from `origin` toward +/-axis
    crosses a surface, in ray order. The origin is nudged sideways only."""
    o = np.asarray(origin, dtype=float).copy()
    nud = np.array([0.00731, 0.00419, 0.00311])
    nud[axis] = 0.0
    o = o + nud
    d = np.zeros(3)
    d[axis] = sign
    loc, _, _ = mesh.ray.intersects_location(o.reshape(1, 3), d.reshape(1, 3), multiple_hits=True)
    loc = np.asarray(loc).reshape(-1, 3)
    ts = sorted(float((p[axis] - o[axis]) * sign) for p in loc)
    out = []
    for t in ts:
        if t > -1e-9 and (not out or t - out[-1] > 1e-4):
            out.append(t)
    return [float(origin[axis] + sign * t) for t in out]


def section_y(mesh, y):
    """Slice normal to Y -> shapely geometry in (x, z)."""
    sec = mesh.section(plane_origin=[0.0, float(y), 0.0], plane_normal=[0.0, 1.0, 0.0])
    if sec is None:
        return None
    M = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, -1.0, 0.0, float(y)], [0.0, 0.0, 0.0, 1.0]])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        planar, _ = sec.to_planar(to_2D=M, check=False)
    polys = list(planar.polygons_full)
    return unary_union(polys) if polys else None


def hole_at(geom, x, z):
    for hp in holes_of(geom):
        if hp.contains(Point(x, z)):
            return hp
    return None


def min_width(geom):
    """Shortest span of a region: 2 x its largest inscribed radius (bisection)."""
    best = 0.0
    for p in C.poly_parts(geom):
        if p.area < 1e-6:
            continue
        lo, hi = 0.0, max(p.bounds[2] - p.bounds[0], p.bounds[3] - p.bounds[1])
        for _ in range(26):
            mid = (lo + hi) / 2.0
            if p.buffer(-mid / 2.0).is_empty:
                hi = mid
            else:
                lo = mid
        best = max(best, lo)
    return best


def printability(mesh, bed=0.05):
    """(widest bridge, widest steep overhang) of a mesh in print orientation:
    downward horizontal faces off the bed (bridges) and downward faces steeper
    than 48.6 deg from vertical (overhangs), grouped into connected regions;
    the width of a region is its shortest span (min_width of its plan view)."""
    n = mesh.face_normals
    off = mesh.triangles_center[:, 2] > bed
    bridge = off & (n[:, 2] < -0.999)
    steep = off & (n[:, 2] < -0.75) & ~bridge

    def worst(mask):
        idx = np.nonzero(mask)[0]
        if not len(idx):
            return 0.0
        sub = mesh.submesh([idx], append=True)
        comps = trimesh.graph.connected_components(sub.face_adjacency, nodes=np.arange(len(sub.faces)))
        w = 0.0
        for comp in comps:
            polys = [Polygon(t[:, :2]) for t in sub.triangles[comp]]
            polys = [p for p in polys if p.is_valid and p.area > 1e-9]
            if polys:
                w = max(w, min_width(unary_union(polys)))
        return w
    return worst(bridge), worst(steep)


def box_points(b, shrink=0.03, step=0.4, shrink_z0=None, shrink_z1=None):
    """Surface points of a box shrunk by `shrink` (bottom / top faces by
    shrink_z0 / shrink_z1 when given: designed crush interference there)."""
    x0, x1, y0, y1, z0, z1 = b
    s0 = shrink if shrink_z0 is None else shrink_z0
    s1 = shrink if shrink_z1 is None else shrink_z1
    return plug.box_surface_points((x0 + shrink, x1 - shrink, y0 + shrink, y1 - shrink, z0 + s0, z1 - s1), step)


def stadium_points(b, r, shrink=0.03, step=0.3, axis=1):
    """Surface points of a box with its edges along `axis` rounded by r."""
    x0, x1, y0, y1, z0, z1 = b
    lo = np.array([x0, y0, z0]) + shrink
    hi = np.array([x1, y1, z1]) - shrink
    other = [a for a in range(3) if a != axis]
    a0, a1 = other
    rr = max(0.0, min(r - shrink, (hi[a0] - lo[a0]) / 2 - 0.01, (hi[a1] - lo[a1]) / 2 - 0.01))
    ring = C.rounded_rect(lo[a0], lo[a1], hi[a0], hi[a1], rr) if rr > 0 else shapely.box(lo[a0], lo[a1], hi[a0], hi[a1])
    ext = ring.exterior
    n = max(16, int(ext.length / step))
    uv = np.array([ext.interpolate(t, normalized=True).coords[0] for t in np.linspace(0, 1, n, endpoint=False)])
    ts = np.linspace(lo[axis], hi[axis], max(2, int((hi[axis] - lo[axis]) / step) + 1))
    pts = []
    for t in ts:
        p = np.zeros((len(uv), 3))
        p[:, axis] = t
        p[:, a0], p[:, a1] = uv[:, 0], uv[:, 1]
        pts.append(p)
    return np.vstack(pts)


def cylinder_points(b, axis=0, shrink=0.03, step=0.3):
    x0, x1, y0, y1, z0, z1 = b
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    other = [a for a in range(3) if a != axis]
    r = (b[2 * other[0] + 1] - b[2 * other[0]]) / 2 - shrink
    lo, hi = b[2 * axis] + shrink, b[2 * axis + 1] - shrink
    ang = np.linspace(0, 2 * np.pi, 40, endpoint=False)
    pts = []
    for t in np.linspace(lo, hi, max(2, int((hi - lo) / step) + 1)):
        p = np.zeros((len(ang), 3))
        p[:, axis] = t
        p[:, other[0]] = c[other[0]] + r * np.cos(ang)
        p[:, other[1]] = c[other[1]] + r * np.sin(ang)
        pts.append(p)
    return np.vstack(pts)


def hw_points(h, shrink=0.03):
    if h["shape"] == "rounded_box":
        return stadium_points(h["box"], float(h.get("r") or 0.0), shrink, axis="xyz".index(h.get("axis", "y")))
    if h["shape"] in ("cylinder_x", "cylinder_y"):
        return cylinder_points(h["box"], axis=0 if h["shape"] == "cylinder_x" else 1, shrink=shrink)
    return box_points(h["box"], shrink)


def _man(tm):
    return C.from_trimesh(tm)


# ---------------------------------------------------------------------------
# USB-C variant (dock, retainer + clip lock, grip, mated assembly)
# ---------------------------------------------------------------------------

def verify_usbc(R, cfg, cid):
    from geometry import usbc
    P = usbc.params(cfg)
    dp = P.dp
    info = usbc.dock_info(cfg, P)
    sc = f"dock-{cid}"

    def stl_part(scope, name, mesh_local, print_T):
        pm = mesh_local.copy()
        pm.apply_transform(print_T)
        R.check(scope, "watertight (built)", mesh_local.is_watertight)
        R.check(scope, "positive volume", mesh_local.volume > 0, f"{mesh_local.volume / 1000:.3f} cm3")
        R.near(scope, "print orientation rests on z=0", float(pm.bounds[0][2]), 0.0, 1e-3)
        path = os.path.join(ROOT, "stl", name)
        if os.path.exists(path):
            m = trimesh.load(path)
            R.check(scope, f"stl/{name} watertight", m.is_watertight)
            R.near(scope, "stl matches build (volume)", m.volume / 1000, pm.volume / 1000, 0.002, unit="cm3")
        else:
            R.check(scope, f"stl/{name} exists", False, "run `make generate`")
        bw, ow = printability(pm)
        R.at_most(scope, "print: widest bridge (no supports)", bw, cfg.USBC_MAX_BRIDGE, unit="mm shortest span")
        R.at_most(scope, "print: widest overhang steeper than 48.6 deg", ow, cfg.USBC_MAX_OVERHANG)
        return pm

    # ---- dock ---------------------------------------------------------------
    dock_m, dock_T = usbc.build_dock(cfg, P)
    stl_part(sc, f"ithalat-dock-{cid}.stl", dock_m, dock_T)
    plugs_in_cutouts(R, sc, cfg, dock_m, [tuple(c[:2]) for c in info["plug_centers"]])
    dock_frame_checks(R, sc, cfg, dock_m, info, P.H)
    R.near(sc, "clip catch angle", dp.catch_deg, cfg.USBC_CLIP_CATCH_DEG, 1e-6, unit="deg")
    R.check(sc, "back-half blades on the plugs' back walls (clear of the board)",
            sorted({b["wall"] for b in dp.blades}) == ["back", "front"] or cfg.USBC_CLIP_BACK_WALL != "back",
            ", ".join(sorted({b["wall"] for b in dp.blades})))
    # well floor and shoulder: ray along +Y at the axis, between window and well wall
    xs = (P.win_hw + P.well_w / 2.0) / 2.0
    hy = axis_hits(dock_m, (xs, P.y_front - 3.0, P.conn_z), 1)
    y_wf = hy[0] if len(hy) >= 2 else None
    y_bf = hy[1] if len(hy) >= 2 else None
    R.near(sc, "well depth (ray at the axis)" + (" (auto)" if P.well_auto else ""),
           None if y_wf is None else y_wf - P.y_front, P.well_depth, 0.01)
    R.at_least(sc, "shoulder wall (well floor -> board front edge)", None if y_bf is None else y_bf - y_wf,
               cfg.USBC_SHOULDER_MIN_T)
    if y_bf is not None:
        mouth = y_bf - P.f_proud
        R.at_most(sc, "receptacle mouth vs well floor (flush)", abs(mouth - y_wf), cfg.USBC_MOUTH_TOL,
                  unit=f"mm ({'behind' if mouth > y_wf + 1e-6 else 'proud of' if mouth < y_wf - 1e-6 else 'at'} the floor)")
    # well section + entry chamfer (slices normal to Y)
    y_in = P.y_front + (P.well_ch + P.well_depth) / 2.0
    well = hole_at(section_y(dock_m, y_in), 0.0, P.conn_z)
    if well is None:
        R.check(sc, "well found", False, f"no opening at y {y_in:.2f}")
    else:
        wx0, wz0, wx1, wz1 = well.bounds
        R.near(sc, "well width", wx1 - wx0, P.well_w, 0.02)
        R.near(sc, "well height", wz1 - wz0, P.well_h, 0.02)
        face = section_y(dock_m, P.y_front + 0.05)
        ent = hole_at(face, 0.0, P.conn_z) if face is not None else None
        if ent is None and face is not None:      # the entry may be open to the bottom edge
            ent = None
        if ent is not None:
            R.near(sc, "well entry chamfer (45 deg)", ((ent.bounds[2] - ent.bounds[0]) - (wx1 - wx0)) / 2.0 + 0.05,
                   P.well_ch, 0.06)
        else:
            R.check(sc, "well entry found on the face", False)
    # window in the shoulder (clearance in front of the crush ribs, grip at them)
    def window_w(y):
        sw = section_y(dock_m, y)
        gg = LineString([(-20.0, P.conn_z), (20.0, P.conn_z)]).difference(sw) if sw is not None else None
        seg = [p for p in getattr(gg, "geoms", [gg]) if gg is not None and p.bounds[0] <= 0.0 <= p.bounds[2]]
        return seg[0].length if seg else None
    if y_bf is not None:
        ym = (y_wf + y_bf) / 2.0
        win_w = window_w(y_wf + 0.1)
        R.near(sc, "window clearance around the receptacle (per side, off the ribs)",
               None if win_w is None else (win_w - P.sW) / 2.0, cfg.USBC_WINDOW_CLEARANCE, 0.03)
        if P.wrib_h > 0:
            rib_w = window_w(P.wrib_y)
            R.near(sc, "window crush ribs grip the receptacle (per side)",
                   None if rib_w is None else (P.sW - rib_w) / 2.0, P.wrib_h - P.win_c, 0.03)
        zb = axis_hits(dock_m, (0.0, ym, P.H + 2.0), 2, -1.0)
        R.at_least(sc, "window floor below the receptacle shell (incl. sag allowance)",
                   None if not zb else P.shell_bot - zb[0], P.win_c + P.sag - TOL)
        zw = axis_hits(dock_m, (0.0, P.y_front + P.well_ch + 0.5, P.conn_z), 2, -1.0)
        R.near(sc, "well bottom wall: nose clearance + sag allowance",
               None if not zw else P.nose_z0 - zw[0], P.well_clr + P.sag, 0.02)
    # board pocket: length, width, rear stop, floor
    zmid = (P.z_b0 + P.z_b1) / 2.0
    xr = P.bp_x1 - 0.5
    fwd = axis_hits(dock_m, (xr, P.y_bf + P.fL / 2, zmid), 1)
    back = axis_hits(dock_m, (xr, P.y_bf + P.fL / 2, zmid), 1, -1.0)
    if len(fwd) >= 2 and back:
        R.near(sc, "board pocket length (board L + play)", fwd[0] - back[0], P.fL + P.play, 0.02)
        R.at_least(sc, "rear stop wall behind the board (takes the push; USBC_F_BOARD L)", fwd[1] - fwd[0], cfg.USBC_REAR_STOP_MIN)
    else:
        R.check(sc, "board pocket found", False)
    yb = P.y_bf + P.fL / 2.0
    xp = axis_hits(dock_m, (P.xb, yb, zmid), 0)
    xm = axis_hits(dock_m, (P.xb, yb, zmid), 0, -1.0)
    R.near(sc, "board pocket width (board W + 2 x clearance)", (xp[0] - xm[0]) if xp and xm else None,
           P.fW + 2 * P.bclr, 0.02)
    R.near(sc, "board rests on its rim (pocket floor z)",
           first_down(dock_m, P.xb + P.fW / 2 - P.f_rim / 2, yb), P.z_b0, 0.01)
    h = hits(dock_m, P.xb + P.fW / 2 - P.f_rim - 0.5, yb)
    R.at_least(sc, "floor under the leg relief (over the plug hollow; USBC_CONN_Z)",
               (h[1] - h[0]) if len(h) >= 2 else None, cfg.DOCK_CAV_FLOOR)
    # rear channel and lock-prong slots open
    pts = np.array([(0.0, y, P.ch_top / 2.0) for y in np.linspace(P.y_pr + 0.2, P.y_back + 0.5, 6)])
    inside = dock_m.contains(pts)
    R.check(sc, "rear wire channel open (pocket -> back face)", not inside.any(), f"{int(inside.sum())}/{len(pts)} inside")
    for k, pr in enumerate(P.prongs if P.lock else []):
        xc, yc = (pr["x0"] + pr["x1"]) / 2.0, (pr["y0"] + pr["y1"]) / 2.0
        pts = np.array([(xc, yc, z) for z in np.linspace(-P.prong_below + 0.2, P.H - 0.2, 12)])
        inside = dock_m.contains(pts)
        R.check(sc, f"lock prong slot {k + 1} open (top face -> behind the blade)", not inside.any(),
                f"{int(inside.sum())}/{len(pts)} inside")
    # finger-brace flats either side of the well (rays along +Y at the axis)
    xs_ = np.arange(0.05, dp.hw, 0.1)
    flat_r = [x for x in xs_ if (lambda hh: bool(hh) and abs(hh[0] - P.y_front) < 0.02)(
        axis_hits(dock_m, (x, P.y_front - 2.0, P.conn_z), 1))]
    flat_l = [x for x in xs_ if (lambda hh: bool(hh) and abs(hh[0] - P.y_front) < 0.02)(
        axis_hits(dock_m, (-x, P.y_front - 2.0, P.conn_z), 1))]
    for side, fl in (("right", flat_r), ("left", flat_l)):
        w = (max(fl) - min(fl) + 0.1) if fl else 0.0
        R.at_least(sc, f"finger-brace flat on the dock face ({side} of the well)", w, cfg.USBC_BRACE_MIN_W)
    # retention
    ret = usbc.retention(cfg, P)
    R.at_least(sc, f"retention: {ret['pull_n']:g} N at {ret['pull_up_deg']:g} deg up "
                   f"({'clip lock fitted' if P.lock else 'catch only'})", ret["margin"], cfg.USBC_RETENTION_MIN,
               unit=(f"x margin (M {ret['moment_nmm']:.1f} N mm -> {ret['demand_per_blade_n']:.2f} N per back blade "
                     f"at {ret['arm_mm']:.2f} mm arm; capacity {ret['capacity_per_blade_n']:.2f} N catch"
                     + (f" / {ret['lock_capacity_n']:.1f} N locked" if P.lock else "") + ")"))
    if P.lock:
        R.at_least(sc, "retention: catch alone (retainer removed)", ret["margin_catch"], cfg.USBC_RETENTION_MIN,
                   unit=f"x margin ({ret['capacity_per_blade_n']:.2f} / {ret['demand_per_blade_n']:.2f} N)", warn=True)
    R.at_least(sc, f"retention: {ret['pull_n']:g} N push (front blades)", ret["margin_push"], cfg.USBC_RETENTION_MIN,
               unit=f"x margin ({ret['capacity_per_blade_n']:.2f} / {ret['push_demand_per_blade_n']:.2f} N)")

    # ---- retainer + clip lock -------------------------------------------------
    ret_m = None
    solids = [dock_m]
    if P.ret:
        sr = "usbc-retainer"
        ret_m, ret_T = usbc.build_retainer(cfg, P)
        stl_part(sr, "ithalat-usbc-retainer.stl", ret_m, ret_T)
        solids.append(ret_m)
        R.near(sr, "top flush with the dock top", float(ret_m.bounds[1][2]), P.H, 0.01)
        bump = (4 * max(0.0, P.bump - P.prong_x_clr) * P.bump_w * max(0.0, P.bump_z1 - P.bump_z0)
                if P.lock and P.bump_z1 > P.bump_z0 + 0.5 else 0.0)
        inter = (_man(dock_m) ^ _man(ret_m)).volume()
        R.at_most(sr, "fits the dock (overlap = crush bumps only)", inter, bump + 0.05,
                  unit=f"mm3 (bumps {bump:.2f})")
        if y_bf is not None:
            up = axis_hits(ret_m, (0.0, P.y_wf + P.rc + 0.05, P.conn_z), 2)
            R.at_least(sr, "tongue closes the window over the shell", (up[0] - P.shell_top) if up else None, 0.05)
        for k, yp in enumerate(P.press_ys):
            up = axis_hits(ret_m, (0.0, yp, P.conn_z), 2)
            R.near(sr, f"shell press rib {k + 1}: interference on the receptacle top",
                   (P.shell_top - up[0]) if up else None, P.press, 0.02)
        hr = hits(ret_m, P.xb + P.fW / 2 - P.f_rim / 2, (P.y_bf + P.y_pr) / 2)
        R.near(sr, "presses the board rim (bottom face z)", hr[0] if hr else None, P.z_b1, 0.01)
        # screws: pilot in the dock under each pad, thread engagement, hold-down
        for k, (x, y) in enumerate(P.rs):
            hd = hits(dock_m, x, y)
            below = [z for z in hd if z < P.z_arm - 0.01]
            R.near(sr, f"screw {k + 1}: pilot hole in the dock (depth below the recess)",
                   (P.z_arm - below[-1]) if below else None, P.rs_depth, 0.02)
        thread = P.rs_l - (P.ret_t - P.rs_cb)
        R.at_least(sr, f"screw thread in the dock (M{P.rs_d:g}x{P.rs_l:g})", thread, 2.5)
        R.at_most(sr, "screw shorter than its pilot hole", thread, P.rs_depth - 0.2)
        R.at_least(sr, f"hold-down: {ret['pull_n']:g} N at {ret['pull_up_deg']:g} deg up vs {len(P.rs)} screws",
                   ret["margin_hold_down"], cfg.USBC_RETENTION_MIN,
                   unit=f"x margin ({ret['hold_down_capacity_n']:.0f} / {ret['hold_down_demand_n']:.2f} N)")
        if P.lock:
            z_lip = (dp.z_catch + dp.z_lip_full) / 2.0
            for k, pr in enumerate(P.prongs):
                xc = (pr["x0"] + pr["x1"]) / 2.0
                yi = (pr["y0"] + pr["y1"]) / 2.0
                face = axis_hits(ret_m, (xc, yi, z_lip), 1)
                blade = axis_hits(dock_m, (xc, yi, z_lip), 1)
                gap = (blade[0] - face[0]) if face and blade else None
                R.at_least(sr, f"lock prong {k + 1}: slides in behind the blade (gap)", gap, 0.02)
                # what backs the prong at the lip (backing rib below the plate)
                bface = axis_hits(ret_m, (xc, yi, z_lip), 1, -1.0)
                bwall = axis_hits(dock_m, (xc, yi, z_lip), 1, -1.0)
                back = (bface[0] - bwall[0]) if bface and bwall else None
                R.at_most(sr, f"lock prong {k + 1}: backed at the lip (clearance to the backing rib)",
                          back, P.prong_back_clr + 0.02)
                eng = None if gap is None or back is None else (dp.lip - dp.side_clr) - gap - back
                R.at_least(sr, f"lock prong {k + 1}: lip engagement left (lip - side clr - gap - back clr)", eng, 0.15)
            R.at_most(sr, "lock prongs reach below the lips", float(ret_m.bounds[0][2]), dp.z_lip_full)
    else:
        R.check(sc, "female board held down", False,
                "USBC_RET_ENABLED=False: no retainer - epoxy the board into its pocket", warn=True)
    # hardware in the dock: no printed material inside it (the receptacle is
    # gripped by the window ribs and the retainer's press ribs by design)
    grip_f = max(P.wrib_h - P.win_c, P.press if P.press_ys else 0.0, 0.0)
    for h in usbc.hardware(cfg, P, (0.0, 0.0, 0.0)):
        if h["moves_with"] != "dock":
            continue
        pts = hw_points(h, 0.03 + (grip_f if h["id"] == "usbc-receptacle" else 0.0))
        inside = np.zeros(len(pts), dtype=bool)
        for s in solids:
            inside |= s.contains(pts)
        R.check(sc + " hardware", f"{h['id']} fits (no printed material inside it)", not inside.any(),
                f"{int(inside.sum())}/{len(pts)} surface points inside")
    if not P.diode_fits:
        R.check(sc, "Schottky cradle in the retainer", False,
                ("does not fit" if P.ret else "no retainer") + ": put the diode inline at the tap", warn=True)

    # ---- grip -----------------------------------------------------------------
    sg = "usbc-grip"
    g = usbc.build_grip(cfg, P)
    for half in ("top", "bottom"):
        stl_part(f"{sg} ({half} half)", f"ithalat-usbc-grip-{half}.stl", g[half][0], g[half][1])
    top_m, bot_m = g["top"][0], g["bottom"][0]
    R.at_most(sg, "halves do not overlap", (_man(top_m) ^ _man(bot_m)).volume(), 0.01, unit="mm3")
    yn = P.y_nf - P.nose_li - 0.6
    sx = axis_hits(top_m, (20.0, yn, P.conn_z), 0, -1.0)
    R.at_least(sg, "nose side wall", (sx[0] - sx[1]) if len(sx) >= 2 else None, cfg.USBC_GRIP_NOSE_WALL)
    st = axis_hits(top_m, (0.0, yn, 30.0), 2, -1.0)
    R.at_least(sg, "nose top wall", (st[0] - st[1]) if len(st) >= 2 else None, cfg.USBC_GRIP_NOSE_WALL)
    sb = axis_hits(bot_m, (0.0, yn, -30.0), 2)
    R.at_least(sg, "nose bottom wall", (sb[1] - sb[0]) if len(sb) >= 2 else None, cfg.USBC_GRIP_NOSE_WALL)
    # corner: distance between the outer and the inner 45 deg chamfer lines
    hw_, hh_ = P.nose_w / 2.0, P.nose_z1 - P.conn_z
    iw, ih = P.msW / 2.0 + P.cav_clr, P.msH / 2.0 + P.cav_clr
    corner = ((hw_ + hh_ - P.nose_ch) - (iw + ih - P.cav_ch)) / math.sqrt(2.0)
    R.at_least(sg, "nose corner wall (chamfer to chamfer)", corner, cfg.USBC_GRIP_NOSE_WALL)
    st = axis_hits(top_m, (0.0, P.y_mb0 + P.m_pad_l / 2.0, 30.0), 2, -1.0)
    R.at_least(sg, "top wall over the solder joints (USBC_GRIP_ABOVE)", (st[0] - st[1]) if len(st) >= 2 else None, cfg.USBC_GRIP_WALL)
    sb = axis_hits(bot_m, (0.0, (P.y_mb0 + P.y_mb1) / 2.0, -30.0), 2)
    R.at_least(sg, "bottom wall under the board (USBC_GRIP_BELOW)", (sb[1] - sb[0]) if len(sb) >= 2 else None, cfg.USBC_GRIP_WALL)
    y_side = P.y_gf - 0.8
    ss = axis_hits(top_m, (30.0, y_side, P.conn_z), 0, -1.0)
    R.at_least(sg, "side wall beside the male board", (ss[0] - ss[1]) if len(ss) >= 2 else None, cfg.USBC_GRIP_WALL)
    sr_ = axis_hits(bot_m, (0.0, P.y_g0 - 5.0, P.z_s - 1.0), 1)
    if len(sr_) >= 3:
        R.at_least(sg, "rear wall behind the wire clamp", sr_[1] - sr_[0], cfg.USBC_GRIP_WALL - TOL)
        R.near(sg, "wire clamp slot (pinches the wires)", sr_[2] - sr_[1], P.wire_d - cfg.USBC_GRIP_WIRE_SQUEEZE, 0.02)
        R.at_most(sg, "slot narrower than a wire (zig-zag pinch)", sr_[2] - sr_[1], P.wire_d - 0.05)
    else:
        R.check(sg, "wire clamp found", False)
    rib = axis_hits(bot_m, (0.0, (P.y_mb0 + P.y_mb1) / 2.0, P.z_s + 0.4), 1, -1.0)
    R.near(sg, "push rib behind the male board (gap)", (P.y_mb0 - rib[0]) if rib else None,
           cfg.USBC_GRIP_BOARD_GAP, 0.02)
    yr = (P.y_rib0 + P.y_rib1) / 2.0
    ceil = axis_hits(top_m, (0.0, yr, 30.0), 2, -1.0)
    ribt = axis_hits(bot_m, (0.0, yr, 30.0), 2, -1.0)
    R.near(sg, "wire pinch over the push rib", (ceil[1] - ribt[0]) if len(ceil) >= 2 and ribt else None,
           P.wire_d - cfg.USBC_GRIP_WIRE_SQUEEZE, 0.02)
    zw = P.z_pc + P.slot / 2.0
    bx_ = axis_hits(top_m, (0.0, yr, zw), 0)
    R.near(sg, "wire band over the push rib (as wide as the pad row)", (2 * bx_[0]) if bx_ else None, P.band_rib, 0.02)
    dz = 0.05                               # just above the underside (the slot tapers)
    bx_ = axis_hits(bot_m, (0.0, (P.y_slot0 + P.y_slot1) / 2.0, P.z_gb + dz), 0)
    R.near(sg, "wire slot at the grip's underside (USBC_GRIP_WIRE_BAND)",
           (2 * bx_[0] - (P.band_rib - P.band) * dz / (P.z_s + 0.01 - P.z_gb)) if bx_ else None, P.band, 0.02)
    thread = P.scr_l - (P.z_s - P.z_gb - P.scr_cb)
    R.at_least(sg, f"screw thread in the top half (M{P.scr_d:g}x{P.scr_l:g})", thread, 2.5)
    R.at_most(sg, "screw shorter than its pilot hole", thread, P.scr_depth)
    if P.pegs:
        R.at_least(sg, "peg hole <-> screw pilot wall", P.peg_wall, cfg.USBC_GRIP_PEG_WALL)
    else:
        R.check(sg, "alignment pegs", False, f"dropped: {P.peg_wall:.2f} mm wall to the screw < USBC_GRIP_PEG_WALL "
                                             "(short grip); the push rib keys the halves", warn=True)
    # board clamp: crush ribs under the edge strips vs the flat ceiling, also
    # after the slicer rounds both faces to USBC_PRINT_LAYER
    xs_c = P.mW / 2.0 - P.m_rim / 2.0
    for k, yc in enumerate(P.crib_ys):
        rt = axis_hits(bot_m, (xs_c, yc, 30.0), 2, -1.0)
        R.near(sg, f"clamp rib {k + 1}: top above the seat", (rt[0] - P.z_s) if rt else None, P.crib_h, 0.02)
    yc_mid = (P.clamp_y0 + P.clamp_y1) / 2.0
    cz = axis_hits(top_m, (xs_c, yc_mid, P.z_s + 0.01), 2)
    R.near(sg, "clamp ceiling over the board's edge strips", cz[0] if cz else None, P.z_pc, 0.01)
    cs = usbc.clamp_slicing(P)
    R.at_least(sg, f"board clamp interference sliced at {cs['layer']:g} mm layers", cs["sliced"], 0.02,
               unit=f"mm (rib {cs['rib_q']:.2f}, ceiling {cs['ceiling_q']:.2f}; nominal {cs['nominal']:.2f})")
    R.at_least(sg, f"board clamp interference, worst layer rounding (<= {cs['layer']:g} mm)", cs["worst"], 0.0,
               unit="mm (nominal - one layer)", warn=True)
    # pull path: collar ledge for the board's front corners, epoxy key groove
    has_collar = P.col_l > 0 and P.col_hw < P.msW / 2.0 + P.cav_clr - 1e-6
    if has_collar:
        cl = axis_hits(top_m, (0.0, P.y_mb1 + P.col_l / 2.0, P.conn_z), 0)
        R.near(sg, "shell collar (board front-corner stop): half-width", cl[0] if cl else None, P.col_hw, 0.02)
    R.check(sg, "board front-corner ledge on the collar", (has_collar and P.col_ledge > 0.02) or P.glue,
            f"{P.col_ledge:.3f} mm per side" + ("" if P.col_ledge > 0.02 else " (board not wider than the "
                                                 "shell: the pull relies on the epoxy key and the clamp)"),
            warn=P.col_ledge <= 0.02)
    if P.glue:
        gm = (P.glue_y0 + P.glue_y1) / 2.0
        gb = axis_hits(bot_m, (0.0, gm, P.conn_z), 2, -1.0)
        R.near(sg, "epoxy key groove below the plug shell (depth)",
               ((P.conn_z - P.msH / 2.0 - P.cav_clr) - gb[0]) if gb else None, P.glue_bot, 0.02)
        gs = axis_hits(top_m, (0.0, gm, P.conn_z + 0.2), 0)
        R.near(sg, "epoxy key groove beside the plug shell (depth)",
               (gs[0] - (P.msW / 2.0 + P.cav_clr)) if gs else None, P.glue_side, 0.02)
    else:
        R.check(sg, "epoxy key groove around the plug shell", False,
                "none: disabled (USBC_GRIP_GLUE_GROOVE) or no room between the collar and the nose face "
                "(USBC_M_PLUG_L - USBC_SHELL_EXPOSED); the pull relies on the clamp - bed the shell in epoxy",
                warn=True)
    for h in usbc.hardware(cfg, P, (0.0, 0.0, 0.0)):
        if h["moves_with"] != "pad":
            continue
        if h["id"] == "usbc-male-board":    # clamp ribs below and a squeezing ceiling above, by design
            pts = box_points(h["box"], 0.03, shrink_z0=0.03 + (P.crib_h if P.crib_ys else 0.0),
                             shrink_z1=0.03 + max(0.0, P.squeeze))
        else:
            pts = hw_points(h, 0.03)
        inside = top_m.contains(pts) | bot_m.contains(pts)
        R.check(sg, f"{h['id']} fits (no printed material inside it)", not inside.any(),
                f"{int(inside.sum())}/{len(pts)} surface points inside")

    # ---- mated assembly (dock-local) -------------------------------------------
    sa = f"{cid} mated (grip in the dock)"
    y_s = P.y_front + P.well_ch + 0.6
    gsec = [section_y(m, y_s) for m in (top_m, bot_m)]
    nose = unary_union([s for s in gsec if s is not None]).buffer(1e-4).buffer(-1e-4)
    well = hole_at(section_y(dock_m, y_s), 0.0, P.conn_z)
    if well is None or nose.is_empty:
        R.check(sa, "nose inside the well", False, "section not found")
    else:
        inside = Polygon(well.exterior).buffer(1e-6).contains(Polygon(max(C.poly_parts(nose), key=lambda p: p.area).exterior))
        clr = well.exterior.distance(nose)
        R.check(sa, "nose inside the well", inside)
        R.at_least(sa, "nose clearance in the well (min, positive)", clr if inside else -clr, 0.05)
        R.near(sa, "nose clearance = USBC_WELL_CLEARANCE", clr, cfg.USBC_WELL_CLEARANCE, 0.03)
        # tilt the nose may take before it meets the well wall (lever = straight engagement)
        y_eng = P.y_nf - (P.y_front + P.well_ch)
        R.check(sa, "nose meets the well wall after (tilt)", y_eng > 0,
                f"{math.degrees(math.atan2(clr, max(y_eng, 1e-6))):.2f} deg over {y_eng:.2f} mm of straight "
                f"engagement (receptacle gripped by ribs, so the walls take over early)")
    y_nose = max(float(top_m.bounds[1][1]), float(bot_m.bounds[1][1]))
    if y_wf is not None:
        R.at_least(sa, "nose stops before the well floor (gap)", y_wf - y_nose, 0.1)
    R.at_least(sa, "plug fully seated (inserted length)", P.y_tip - P.mouth_y, cfg.USBC_F_DEPTH)
    R.at_least(sa, "nose cannot bottom before the plug seats (exposed - seated)",
               P.exposed - (P.y_tip - P.mouth_y) - max(0.0, P.recess), 0.1)
    for name, other in (("dock", dock_m), ("retainer", ret_m)):
        if other is None:
            continue
        om = _man(other)
        gap = min(om.min_gap(_man(top_m), 2.0), om.min_gap(_man(bot_m), 2.0))
        R.at_least(sa, f"grip clear of the {name} (min gap)", gap, min(0.2, cfg.USBC_WELL_CLEARANCE) - 0.02)
    return {"P": P, "dock": (dock_m, dock_T, info), "retainer": ret_m, "grip": (top_m, bot_m)}


def verify_usbc_vs_rest(R, cfg, cid, vid, glass_t, rest_mesh, usb):
    from geometry import connectors as CN
    from geometry import usbc
    P = usb["P"]
    t = CN.place_matrix(cfg)[:3, 3]
    lay, _ = rest.plan(cfg, glass_t)
    sc = f"{cid} grip vs rest-{vid}"
    grip = []
    for m in usb["grip"]:
        mm = m.copy()
        mm.apply_translation(t)
        grip.append(mm)
    rm = _man(rest_mesh)
    for label, dy in (("mated", 0.0), (f"withdrawn {cfg.USBC_WITHDRAW:g} mm", -float(cfg.USBC_WITHDRAW))):
        gap = min(rm.min_gap(_man(m).translate((0.0, dy, 0.0)), 5.0) for m in grip)
        R.at_least(sc, f"grip floats above the rest ({label})", gap, cfg.USBC_GRIP_MIN_FLOAT)
    foot = unary_union([shapely.MultiPoint(m.vertices[:, :2]).convex_hull for m in grip])
    R.at_least(sc, "grip rear clear of the trackpad pocket (plan)", foot.distance(lay.opening),
               cfg.USBC_GRIP_POCKET_CLEAR)
    wd = float(cfg.CABLE_WIRE_D)
    drop = t[1] + (P.y_slot0 + P.y_slot1) / 2.0
    lo, hi = lay.notch_y0 + wd, lay.riser_y1 - wd
    R.check(sc, "grip wire exit straight above the riser", lo <= drop <= hi,
            f"exit y {drop:.2f}, riser allows {lo:.2f}..{hi:.2f}")
    R.at_most(sc, "wire band inside the notch width", abs(t[0] - lay.notch_x) + P.band / 2.0,
              cfg.CABLE_NOTCH_W / 2.0)
    R.at_least(sc, "wire slack lets the plug clear the well", float(cfg.USBC_WIRE_SLACK),
               float(P.y_tip - P.y_front))
    md = usbc.metal_distance(cfg, lay, P, t)
    R.at_least(sc, "USB-C plug shell -> TPS65 outline (plan)", md["plug_shell"], cfg.TP_METAL_KEEPOUT,
               unit="mm (advisory, TP_METAL_KEEPOUT)", warn=True)
    R.at_least(sc, "USB-C male board -> TPS65 outline (plan)", md["male_board"], cfg.TP_METAL_KEEPOUT,
               unit="mm (advisory: copper pads, no steel)", warn=True)


# ---------------------------------------------------------------------------
# assembly (build/manifest.json)
# ---------------------------------------------------------------------------

def _placed_dock_checks(R, sc, cfg, part, print_T, T_place, kb_y0, body_h):
    M = np.asarray(part["matrix"], dtype=float).reshape(4, 4, order="F")
    want = T_place @ np.linalg.inv(print_T)
    R.at_most(sc, "dock matrix = T_place @ inv(print_T)", float(np.abs(M - want).max()), 1e-4, unit="max |diff|")
    stl = os.path.join(ROOT, part["stl"])
    if not os.path.exists(stl):
        return
    placed = trimesh.load(stl)
    placed.apply_transform(M)
    lo, hi = placed.bounds
    R.near(sc, "placed dock: plug tips below the switchplate top", float(lo[2]),
           cfg.KEYBOARD_HEIGHT - cfg.DOCK_PLUG_DEPTH, 0.01)
    R.near(sc, "placed dock: top", float(hi[2]), cfg.KEYBOARD_HEIGHT + body_h, 0.01)
    R.at_least(sc, "placed dock: behind the keyboard front edge", float(lo[1]) - kb_y0, 0.0)
    R.at_least(sc, "placed dock: clear of the OLED cover", kb_y0 + cfg.OLED_COVER[1] - float(hi[1]), 0.5)
    R.at_least(sc, "placed dock: top below the OLED cover underside (cover edge position uncritical)",
               cfg.OLED_COVER_TOP_Z - cfg.OLED_COVER_T - float(hi[2]), 0.0,
               unit="mm (advisory: OLED_COVER_T is an estimate)", warn=True)
    R.at_most(sc, "placed dock: top below the keycap tops", float(hi[2]), cfg.KEYCAP_TOP_Z)


def _route_checks(R, sc, cfg, cv, end, end_name, slack=0.0, n_wires=None):
    pv = (cv.get("cable") or {}).get("per_variant") or {}
    for vid, gt in cfg.VARIANTS.items():
        lay_v, _ = rest.plan(cfg, gt)
        pts = np.asarray((pv.get(vid) or {}).get("centerline", []), dtype=float).reshape(-1, 3)
        R.check(sc, f"cable route ({vid})", len(pts) >= 4, f"{len(pts)} points")
        if len(pts) < 4:
            continue
        R.at_most(sc, f"cable starts at the TPS65 pads ({vid})",
                  float(np.hypot(pts[0][0] - lay_v.pads_c[0], pts[0][1] - lay_v.pads_c[1])), 0.5)
        in_notch = [(abs(x - lay_v.notch_x) <= cfg.CABLE_NOTCH_W / 2 and lay_v.notch_y0 <= y <= cfg.REST_DEPTH
                     and z >= lay_v.notch_floor) for x, y, z in pts]
        R.check(sc, f"cable leaves through the back-top notch ({vid})", any(in_notch),
                f"{sum(in_notch)} route points inside the notch")
        sl = np.asarray((pv.get(vid) or {}).get("sleeve", []), dtype=float).reshape(-1, 3)
        R.near(sc, f"sleeve starts at the groove's jacket end ({vid})",
               float(np.hypot(*(sl[0][:2] - np.asarray(lay_v.jacket_end)))) if len(sl) else None, 0.0, 0.01)
        length = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
        R.at_most(sc, f"route length{' + slack' if slack else ''} fits the pigtail ({vid})", length + slack,
                  cfg.CABLE_PIGTAIL_LEN, unit="mm route")
        R.at_most(sc, f"cable ends at the {end_name} ({vid})", float(np.linalg.norm(pts[-1] - end)), 1e-3)
        if n_wires:
            wires = (pv.get(vid) or {}).get("wires") or []
            for part in ("pad", "plug"):
                R.check(sc, f"{n_wires} wires on the {part} side ({vid})",
                        sum(1 for w in wires if w.get("part") == part) == n_wires)


def _hardware_shape_ok(hw):
    mats = {"pcb_green", "pcb_blue", "metal", "plastic_black", "magnet", "diode"}
    shapes = {"box", "rounded_box", "cylinder_y", "cylinder_x"}
    bad = [h.get("id") for h in hw if not (h.get("shape") in shapes and h.get("material") in mats
                                         and h.get("moves_with") in ("dock", "pad")
                                         and len(h.get("box") or []) == 6 and h.get("label"))]
    return not bad, bad


def verify_assembly(R, cfg, conns):
    """Cross-part checks on build/manifest.json: connector variants, parts,
    placement matrices, connector faces, hardware, cable routes."""
    from geometry import connectors as CN
    from geometry import usbc
    sc = "assembly (manifest)"
    path = os.path.join(ROOT, "build", "manifest.json")
    if not os.path.exists(path):
        R.check(sc, "build/manifest.json exists", False, "run `make generate`")
        return
    import json
    with open(path) as f:
        man = json.load(f)
    mc = man.get("config", {})

    def same(n):
        v = getattr(cfg, n)
        if isinstance(v, (tuple, list)):
            return list(mc[n]) == list(v)
        return mc[n] == (round(v, 6) if isinstance(v, float) else v)
    stale = [n for n in ("REST_WIDTH", "REST_DEPTH", "REST_HEIGHT", "GLASS_T", "KEYBOARD_HEIGHT",
                         "TP_BACK_MARGIN", "DOCK_ENABLED", "DOCK_BODY_D", "CONNECTORS", "USBC_WELL_DEPTH",
                         "USBC_CONN_Z", "USBC_DOCK_D") if n in mc and not same(n)]
    R.check(sc, "manifest built with the same config", not stale,
            ("differs: " + ", ".join(f"{n}={mc[n]!r}" for n in stale)) if stale else "")
    want_c = [{"id": CN.cid(cfg, c), "type": c, "label": CN.label(cfg, c)} for c in cfg.CONNECTORS]
    R.check(sc, "connectors listed in CONNECTORS order", man.get("connectors") == want_c,
            ", ".join(c.get("id", "?") for c in man.get("connectors") or []))
    ids = {p["id"]: p for p in man.get("parts", [])}
    want = {f"rest-{v}": None for v in cfg.VARIANTS}
    if cfg.DOCK_ENABLED:
        for c in cfg.CONNECTORS:
            cid = CN.cid(cfg, c)
            want[f"dock-{cid}"] = cid
            if c == "usbc":
                want.update({"usbc-grip-top": cid, "usbc-grip-bottom": cid})
                if cfg.USBC_RET_ENABLED:
                    want["usbc-retainer"] = cid
    R.check(sc, "parts listed", all(i in ids for i in want), ", ".join(ids))
    R.check(sc, "every part tagged with its connector", all(ids[i].get("connector", "?") == c
                                                           for i, c in want.items() if i in ids))
    for pid in want:
        if pid in ids:
            R.check(sc, f"{ids[pid]['stl']} exists", os.path.exists(os.path.join(ROOT, ids[pid]["stl"])))
    cvs = man.get("connector_variants") or {}
    first = CN.cid(cfg, cfg.CONNECTORS[0])
    if first in cvs:
        R.check(sc, "legacy dock / cable / connector = the first connector variant",
                man.get("dock") == cvs[first]["dock"] and man.get("cable") == cvs[first]["cable"]
                and man.get("connector") == cvs[first]["connector"])
    kb_y0 = cfg.REST_DEPTH + cfg.REST_KEYBOARD_GAP
    org = man["keyboard"]["origin"]
    R.near(sc, "keyboard origin (centred, gap behind the rest)",
           float(np.hypot(org[0] - cfg.KB_X0, org[1] - kb_y0)), 0.0, 1e-3)
    T_place = CN.place_matrix(cfg)
    lay, _ = rest.plan(cfg, list(cfg.VARIANTS.values())[0])

    for cid, entry in conns.items():
        cc, ctype = entry["cfg"], entry["type"]
        scc = f"assembly ({cid})"
        cv = cvs.get(cid)
        R.check(scc, "connector variant in the manifest",
                cv is not None and all(k in cv for k in ("dock", "cable", "connector", "hardware", "dims", "notes")))
        if cv is None:
            continue
        ok, bad = _hardware_shape_ok(cv["hardware"])
        R.check(scc, "hardware entries well formed", ok and len(cv["hardware"]) >= 2, ", ".join(map(str, bad)))
        R.check(scc, "pin table", len(cv["connector"].get("pins") or []) >= 4)
        b = entry.get("build")
        if ctype == "usbc":
            try:
                P = usbc.params(cc)
            except ValueError as e:
                R.check(scc, "USB-C config valid", False, str(e).replace("\n", " "))
                continue
            t = T_place[:3, 3]
            face = t + np.array([0.0, P.y_front, P.conn_z])
            R.at_most(scc, "manifest connector face = placed dock well entry",
                      float(np.abs(np.asarray(cv["dock"]["connector_face_center"]) - face).max()), 1e-3, unit="max |diff|")
            want_hw = usbc.hardware(cc, P, t)
            got = {h["id"]: h for h in cv["hardware"]}
            diff = max((float(np.abs(np.asarray(got[h["id"]]["box"]) - np.asarray(h["box"])).max())
                        if h["id"] in got else 99.0) for h in want_hw)
            R.at_most(scc, "hardware boxes = usbc.hardware() (meshes checked in dock-local)", diff, 1e-3,
                      unit="max |diff|")
            pads = t + np.array([0.0, P.y_mb0 + P.m_pad_l / 2.0, P.z_pc + P.slot / 2.0])
            _route_checks(R, scc, cc, cv, pads, "male pads in the grip", slack=float(cc.USBC_WIRE_SLACK), n_wires=4)
            ret = cv["dock"]["info"].get("retention") or {}
            R.at_least(scc, "manifest retention margin", ret.get("margin"), cc.USBC_RETENTION_MIN, unit="x")
            if b is None:
                continue
            dock_m, dock_T, _ = b["dock"]
            if f"dock-{cid}" in ids:
                _placed_dock_checks(R, scc, cc, ids[f"dock-{cid}"], dock_T, T_place, kb_y0, P.H)
            extras = [("usbc-retainer", b["retainer"]), ("usbc-grip-top", b["grip"][0]),
                      ("usbc-grip-bottom", b["grip"][1])]
            for pid, local in extras:
                if local is None or pid not in ids:
                    continue
                stl = os.path.join(ROOT, ids[pid]["stl"])
                if not os.path.exists(stl):
                    continue
                M = np.asarray(ids[pid]["matrix"], dtype=float).reshape(4, 4, order="F")
                placed = trimesh.load(stl)
                placed.apply_transform(M)
                d = float(np.abs(placed.bounds - (local.bounds + t)).max())
                R.at_most(scc, f"{pid}: matrix puts the print STL at its assembled place", d, 0.01, unit="max |diff|")
            continue
        # pogo / JST
        if b is not None:
            mesh_local, print_T, info = b
            if f"dock-{cid}" in ids:
                _placed_dock_checks(R, scc, cc, ids[f"dock-{cid}"], print_T, T_place, kb_y0, cc.DOCK_BODY_H)
            face_local = np.append(np.asarray(info["connector_face_center"], dtype=float)[:3], 1.0)
            face = (T_place @ face_local)[:3]
        else:
            face = plug.connector_face(cc)
        mface = np.asarray(cv["dock"]["connector_face_center"], dtype=float)
        R.at_most(scc, "manifest connector face = placed dock face", float(np.abs(mface - face).max()), 1e-3,
                  unit="max |diff|")
        R.at_most(scc, "plug.connector_face = placed dock face", float(np.abs(plug.connector_face(cc) - face).max()),
                  1e-3, unit="max |diff|")
        _route_checks(R, scc, cc, cv, face, "dock connector face")
        # advisory: the MG005 plug's two NdFeB magnets sit closer to the pad than
        # TP_METAL_KEEPOUT - acceptable (static while powered, ATI at power-up)
        env = plug.plug_envelope(cc, lay, face)
        if env["magnets"]:
            mod = shapely.box(lay.mod_x0, lay.mod_y0, lay.mod_x1, lay.mod_y1)
            dmin = min(mod.distance(shapely.box(mx - 1.6, y0, mx + 1.6, y1)) for mx, y0, y1, _ in env["magnets"])
            R.at_least(scc, "plug magnets -> TPS65 outline (plan)", dmin, cfg.TP_METAL_KEEPOUT,
                       unit="mm (advisory: static while powered, ATI at power-up)", warn=True)
    R.at_most(sc, "rest back edge level with the switchplate", abs(cfg.REST_BACK_HEIGHT - cfg.KEYBOARD_HEIGHT),
              0.5, unit="mm (advisory)", warn=True)


def main(argv=None):
    from geometry import connectors as CN
    from geometry import usbc
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--rebuild", action="store_true", help="build every STL in memory instead of loading stl/")
    p.add_argument("-v", "--verbose", action="store_true")
    add_cli_args(p)
    a = p.parse_args(argv)
    cfg = load_config(overrides_from_args(a))
    try:
        rest.plan(cfg, list(cfg.VARIANTS.values())[0])
    except ValueError as e:          # same config errors generate.py refuses
        raise SystemExit(f"config error: {e}")
    R = Report(a.verbose)
    print("ithalat verify" + (f" (overrides: {cfg._overrides})" if cfg._overrides else "")
          + f" - connectors: {', '.join(cfg.CONNECTORS)}")
    rests = {}
    for vid, glass_t in cfg.VARIANTS.items():
        path = os.path.join(ROOT, "stl", f"ithalat-{vid}.stl")
        if os.path.exists(path) and not a.rebuild:
            mesh, source = trimesh.load(path), "stl/" + os.path.basename(path)
            mb = os.path.getsize(path) / 1e6
            R.at_most(f"rest-{vid} ({source})", "STL size", mb, cfg.STL_MAX_MB, unit="MB")
        else:
            man, _ = rest.build_rest(cfg, vid, glass_t)
            mesh, source = C.to_trimesh(man), "in-memory build"
        verify_rest(R, cfg, vid, glass_t, mesh, source)
        rests[vid] = mesh
    conns = {}
    for ctype in cfg.CONNECTORS:
        cc = CN.for_connector(cfg, ctype)
        cid = CN.cid(cfg, ctype)
        entry = {"type": ctype, "cfg": cc, "build": None}
        conns[cid] = entry
        if ctype == "usbc":
            try:
                usbc.params(cc)
            except ValueError as e:
                R.check(f"dock-{cid}", "USB-C config valid", False, str(e).replace("\n", " "))
                continue
            if cfg.DOCK_ENABLED:
                entry["build"] = verify_usbc(R, cc, cid)
                for vid, glass_t in cfg.VARIANTS.items():
                    verify_usbc_vs_rest(R, cc, cid, vid, glass_t, rests[vid], entry["build"])
            continue
        for vid, glass_t in cfg.VARIANTS.items():
            verify_plug_vs_rest(R, cc, cid, vid, glass_t, rests[vid])
        if cfg.DOCK_ENABLED:
            entry["build"] = verify_dock(R, cc, cid, os.path.join(ROOT, "stl", f"ithalat-dock-{cid}.stl"))
    if not a.rebuild:   # --rebuild checks the in-memory geometry only
        verify_assembly(R, cfg, conns)
    ok = R.print()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
