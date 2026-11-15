"""Shared helpers: shapely <-> manifold3d <-> trimesh, small math utilities."""

import math

import numpy as np
import shapely
import trimesh
from manifold3d import CrossSection, FillRule, Manifold, Mesh64, OpType
from shapely.geometry import Polygon, box as shp_box
from shapely.geometry.polygon import orient

QS = 24  # shapely quad segments (arc smoothness of plan-view buffers)


# ---------------------------------------------------------------------------
# math
# ---------------------------------------------------------------------------

def smoothstep(t):
    """C1 cubic ease 0..1 (zero slope at both ends)."""
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def softmin(a, b, k=0.4):
    """Smooth minimum (log-sum-exp), never larger than min(a, b)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.minimum(a, b)
    return m - k * np.log(np.exp(-(a - m) / k) + np.exp(-(b - m) / k))


def pchip(xs, ys):
    """Monotone cubic (Fritsch-Carlson PCHIP) interpolant, C1, no overshoot.
    Returns f(x) vectorised; clamps outside [xs[0], xs[-1]]."""
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if len(xs) < 2 or np.any(np.diff(xs) <= 0):
        raise ValueError("REST_PROFILE distances must be strictly increasing (>= 2 points)")
    h = np.diff(xs)
    delta = np.diff(ys) / h
    n = len(xs)
    m = np.zeros(n)
    if n == 2:
        m[:] = delta[0]
    else:
        for k in range(1, n - 1):
            if delta[k - 1] * delta[k] <= 0:
                m[k] = 0.0
            else:
                w1 = 2 * h[k] + h[k - 1]
                w2 = h[k] + 2 * h[k - 1]
                m[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])

        def end_slope(h0, h1, d0, d1):
            s = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
            if np.sign(s) != np.sign(d0):
                return 0.0
            if np.sign(d0) != np.sign(d1) and abs(s) > abs(3 * d0):
                return 3 * d0
            return s
        m[0] = end_slope(h[0], h[1], delta[0], delta[1])
        m[-1] = end_slope(h[-1], h[-2], delta[-1], delta[-2])

    def f(x):
        x = np.clip(np.asarray(x, dtype=float), xs[0], xs[-1])
        k = np.clip(np.searchsorted(xs, x, side='right') - 1, 0, n - 2)
        t = (x - xs[k]) / h[k]
        t2, t3 = t * t, t * t * t
        h00 = 2 * t3 - 3 * t2 + 1
        h10 = t3 - 2 * t2 + t
        h01 = -2 * t3 + 3 * t2
        h11 = t3 - t2
        return h00 * ys[k] + h10 * h[k] * m[k] + h01 * ys[k + 1] + h11 * h[k] * m[k + 1]
    return f


def rounded_rect_sdf(px, py, cx, cy, w, d, r):
    """Signed distance to a rounded rectangle (negative inside), analytic."""
    qx = np.abs(px - cx) - (w / 2 - r)
    qy = np.abs(py - cy) - (d / 2 - r)
    outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
    inside = np.minimum(np.maximum(qx, qy), 0.0)
    return outside + inside - r


# ---------------------------------------------------------------------------
# 2D (shapely)
# ---------------------------------------------------------------------------

def rounded_rect(x0, y0, x1, y1, r):
    """Axis-aligned rectangle with corner radius r as a shapely Polygon."""
    b = shp_box(x0, y0, x1, y1)
    r = min(r, (x1 - x0) / 2 - 1e-6, (y1 - y0) / 2 - 1e-6)
    if r <= 0:
        return b
    return b.buffer(-r, quad_segs=QS).buffer(r, quad_segs=QS)


def poly_parts(geom):
    """Polygons of a (possibly Multi-) polygon / collection, skipping empties."""
    if geom is None or geom.is_empty:
        return []
    parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    out = []
    for p in parts:
        if p.geom_type == "Polygon" and not p.is_empty:
            out.append(p)
        elif hasattr(p, "geoms"):
            out += poly_parts(p)
    return out


def to_cross_section(geom):
    """shapely (Multi)Polygon -> manifold CrossSection (even-odd fill, so ring
    orientation does not matter - GEOS buffer() rings are clockwise)."""
    contours = []
    for p in poly_parts(geom):
        p = orient(p, 1.0)
        contours.append(np.asarray(p.exterior.coords)[:-1])
        contours += [np.asarray(i.coords)[:-1] for i in p.interiors]
    if not contours:
        return CrossSection()
    return CrossSection(contours, FillRule.EvenOdd)


# ---------------------------------------------------------------------------
# 3D (manifold3d)
# ---------------------------------------------------------------------------

def prism(geom, z0, z1):
    """Vertical prism of a shapely (Multi)Polygon between z0 and z1."""
    cs = to_cross_section(geom)
    if cs.is_empty():
        return Manifold()
    return Manifold.extrude(cs, float(z1 - z0)).translate((0.0, 0.0, float(z0)))


def frustum_hull(poly_low, z_low, poly_high, z_high):
    """Convex hull of two convex outlines at two heights (chamfers)."""
    pts = []
    for poly, z in ((poly_low, z_low), (poly_high, z_high)):
        xy = np.asarray(poly.exterior.coords)[:-1]
        pts.append(np.column_stack([xy, np.full(len(xy), float(z))]))
    return Manifold.hull_points(np.vstack(pts))


def cylinder(cx, cy, r, z0, z1, segs=64):
    return (Manifold.cylinder(float(z1 - z0), float(r), float(r), segs)
            .translate((float(cx), float(cy), float(z0))))


def subtract_all(body, cutters):
    cutters = [c for c in cutters if c is not None and not c.is_empty()]
    if not cutters:
        return body
    return Manifold.batch_boolean([body] + cutters, OpType.Subtract)


def union_all(parts):
    parts = [p for p in parts if p is not None and not p.is_empty()]
    if not parts:
        return Manifold()
    return Manifold.batch_boolean(parts, OpType.Add)


def manifold_from_arrays(verts, faces):
    mesh = Mesh64(vert_properties=np.ascontiguousarray(verts, dtype=np.float64),
                  tri_verts=np.ascontiguousarray(faces, dtype=np.uint64))
    m = Manifold(mesh)
    status = str(m.status())
    if not status.endswith("NoError"):
        raise RuntimeError(f"custom mesh is not a valid manifold: {status}")
    return m


def to_trimesh(man):
    mesh = man.to_mesh64()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return trimesh.Trimesh(vertices=v, faces=f, process=True)


def from_trimesh(tm):
    return manifold_from_arrays(np.asarray(tm.vertices), np.asarray(tm.faces))


def mat4_to_list(m):
    """numpy 4x4 -> three.js Matrix4.elements order (column-major), 16 floats."""
    return [float(round(v, 9)) for v in np.asarray(m, dtype=float).flatten(order="F")]


def translation(x, y, z):
    t = np.eye(4)
    t[:3, 3] = (x, y, z)
    return t


def mesh_stats(tm, density):
    b = tm.bounds
    vol = float(tm.volume)
    return {
        "triangles": int(len(tm.faces)),
        "bbox": [[round(float(v), 4) for v in b[0]], [round(float(v), 4) for v in b[1]]],
        "volume_cm3": round(vol / 1000.0, 3),
        "mass_g_solid_pla": round(vol / 1000.0 * density, 1),
        "area_cm2": round(float(tm.area) / 100.0, 2),
    }


def deg(a):
    return a * 180.0 / math.pi
