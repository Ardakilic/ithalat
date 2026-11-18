"""The ithalat wrist rest: plan outline, C1 top surface, stepped trackpad pocket,
cable tunnel/notch, underside features.

Body construction (why not extrude + refine + warp like the prototype): the top
surface is meshed directly so the edge round-overs are sampled evenly by angle
(an extruded cap refined to a uniform edge length puts only 1-2 vertices on a
steep round-over) and the flat bottom stays a single fan:

  * boundary ring  - the analytic, tangent-continuous outline (straight back,
                     small back corners, bulging ends, big front corners,
                     straight front) sampled with exact outward normals;
  * band rings     - offset rings that follow the elliptic round-over
                     d = a(1-cos t), drop = b(1-sin t), t = 0..90 deg, with a
                     (horizontal) and b (vertical) varying smoothly along the
                     outline (back edge / ends / front nose);
  * interior       - a hexagonal lattice (spacing MESH_EDGE_LEN) Delaunay-
                     triangulated against the innermost ring;
  * wall + chamfer - a vertical wall down to a 45 deg bottom chamfer.

Every vertex takes z = top_z(x, y) = h(x, y) - drop(d, s), where h is the
crowned profile with the flat trackpad island blended in (smoothstep) and the
drop is the round-over. All pieces are C1, so the top has no creases. The
pocket, tunnel, notch, holes and engraving are then manifold3d booleans.
"""

import math
import warnings

import numpy as np
import shapely
from manifold3d import Manifold, triangulate
from scipy.spatial import Delaunay
from shapely import affinity
from shapely.geometry import LineString, LinearRing, Point, Polygon

from . import common as C
from .text import text_geometry

LOG = []


def log(msg, tag="rest"):
    if msg in LOG:      # every variant re-plans the same layout: report once
        return
    LOG.append(msg)
    print(f"  [{tag}] {msg}")


# ---------------------------------------------------------------------------
# plan outline
# ---------------------------------------------------------------------------

class Outline:
    """Tangent-continuous closed outline, CCW, with exact outward normals and a
    per-sample zone weight (back / end / front) for the round-over radii."""

    def __init__(self, cfg, spacing):
        W, D = float(cfg.REST_WIDTH), float(cfg.REST_DEPTH)
        rb, rf = float(cfg.REST_PLAN_BACK_CORNER_R), float(cfg.REST_PLAN_FRONT_CORNER_R)
        bulge = float(cfg.REST_END_BULGE)
        taper = float(cfg.REST_END_TAPER)
        if bulge < 0:
            raise ValueError("REST_END_BULGE must be >= 0 (convex ends)")
        if rb + rf >= D - 1.0:
            raise ValueError("REST_PLAN_*_CORNER_R too large for REST_DEPTH")
        self.W, self.D = W, D
        yc = D / 2.0
        segs = []  # (kind, data, zone)
        if bulge > 1e-6:
            Re = (yc * yc + bulge * bulge) / (2.0 * bulge)
            CeL, CeR = np.array([Re, yc]), np.array([W - Re, yc])

            def corner(y_line, r, left):
                dy = (r if y_line == 0.0 else D - r) - yc
                cx = Re - math.sqrt((Re - r) ** 2 - dy ** 2)
                c = np.array([cx, y_line + (r if y_line == 0.0 else -r)])
                if not left:
                    c = np.array([W - cx, c[1]])
                Ce = CeL if left else CeR
                t_end = Ce + (c - Ce) * Re / (Re - r)
                return c, t_end
            cFL, tFL = corner(0.0, rf, True)
            cFR, tFR = corner(0.0, rf, False)
            cBL, tBL = corner(D, rb, True)
            cBR, tBR = corner(D, rb, False)
            ang = lambda p, c: math.atan2(p[1] - c[1], p[0] - c[0])
            segs.append(("line", (np.array([cFL[0], 0.0]), np.array([cFR[0], 0.0]), (0.0, -1.0)), "front"))
            segs.append(("arc", (cFR, rf, -math.pi / 2, ang(tFR, cFR)), "front-corner-r"))
            segs.append(("arc", (CeR, Re, ang(tFR, CeR), ang(tBR, CeR)), "end-r"))
            segs.append(("arc", (cBR, rb, ang(tBR, cBR), math.pi / 2), "back"))
            segs.append(("line", (np.array([cBR[0], D]), np.array([cBL[0], D]), (0.0, 1.0)), "back"))
            segs.append(("arc", (cBL, rb, math.pi / 2, ang(tBL, cBL)), "back"))
            a0, a1 = ang(tBL, CeL), ang(tFL, CeL)
            if a1 < a0:
                a1 += 2 * math.pi
            segs.append(("arc", (CeL, Re, a0, a1), "end-l"))
            a0 = ang(tFL, cFL) % (2 * math.pi)   # ~ pi + small
            a1 = 1.5 * math.pi
            segs.append(("arc", (cFL, rf, a0, a1), "front-corner-l"))
        else:
            segs.append(("line", (np.array([rf, 0.0]), np.array([W - rf, 0.0]), (0.0, -1.0)), "front"))
            segs.append(("arc", (np.array([W - rf, rf]), rf, -math.pi / 2, 0.0), "front-corner-r"))
            segs.append(("line", (np.array([W, rf]), np.array([W, D - rb]), (1.0, 0.0)), "end-r"))
            segs.append(("arc", (np.array([W - rb, D - rb]), rb, 0.0, math.pi / 2), "back"))
            segs.append(("line", (np.array([W - rb, D]), np.array([rb, D]), (0.0, 1.0)), "back"))
            segs.append(("arc", (np.array([rb, D - rb]), rb, math.pi / 2, math.pi), "back"))
            segs.append(("line", (np.array([0.0, D - rb]), np.array([0.0, rf]), (-1.0, 0.0)), "end-l"))
            segs.append(("arc", (np.array([rf, rf]), rf, math.pi, 1.5 * math.pi), "front-corner-l"))

        pts, nrm, wts = [], [], []
        for kind, data, zone in segs:
            if kind == "line":
                p0, p1, n = data
                length = float(np.linalg.norm(p1 - p0))
                k = max(1, int(math.ceil(length / spacing)))
                u = np.arange(k) / k
                P = p0[None, :] + (p1 - p0)[None, :] * u[:, None]
                N = np.tile(np.array(n), (k, 1))
                sl = u * length
            else:
                c, r, a0, a1 = data
                length = abs(a1 - a0) * r
                k = max(24 if r < 10 else (12 if r < 50 else 1), int(math.ceil(length / spacing)))
                u = np.arange(k) / k
                a = a0 + (a1 - a0) * u
                N = np.column_stack([np.cos(a), np.sin(a)])
                P = c[None, :] + r * N
                sl = u * length
            # zone weights (back, end, front)
            wb = np.zeros(len(u))
            we = np.zeros(len(u))
            wf = np.zeros(len(u))
            if zone == "front":
                wf[:] = 1
            elif zone == "back":
                wb[:] = 1
            elif zone == "front-corner-r":
                we[:] = C.smoothstep(u)
                wf[:] = 1 - we
            elif zone == "front-corner-l":
                wf[:] = C.smoothstep(u)
                we[:] = 1 - wf
            elif zone == "end-r":   # front -> back
                t = min(taper, length)
                wb[:] = C.smoothstep((sl - (length - t)) / t)
                we[:] = 1 - wb
            elif zone == "end-l":   # back -> front
                t = min(taper, length)
                wb[:] = 1 - C.smoothstep(sl / t)
                we[:] = 1 - wb
            pts.append(P)
            nrm.append(N)
            wts.append(np.column_stack([wb, we, wf]))
        self.pts = np.vstack(pts)
        self.nrm = np.vstack(nrm)
        self.wts = np.vstack(wts)
        self.n = len(self.pts)
        seg = np.linalg.norm(np.roll(self.pts, -1, axis=0) - self.pts, axis=1)
        self.s = np.concatenate([[0.0], np.cumsum(seg)[:-1]])
        self.length = float(seg.sum())
        self.polygon = Polygon(self.pts)
        if not self.polygon.is_valid or not self.polygon.exterior.is_ccw:
            raise RuntimeError("outline construction failed (invalid / not CCW)")
        self.ring = LineString(np.vstack([self.pts, self.pts[:1]]))

    def interp(self, values, s):
        """Interpolate a per-sample array at arc lengths s (periodic)."""
        xs = np.concatenate([self.s, [self.length]])
        vs = np.concatenate([values, values[:1]])
        return np.interp(np.mod(s, self.length), xs, vs)


# ---------------------------------------------------------------------------
# trackpad / pocket / cable layout (everything that is a position)
# ---------------------------------------------------------------------------

class Layout:
    def __init__(self, cfg, glass_t):
        self.cfg = cfg
        W, D, H = float(cfg.REST_WIDTH), float(cfg.REST_DEPTH), float(cfg.REST_HEIGHT)
        self.W, self.D, self.H = W, D, H
        self.glass_t = float(glass_t)
        if cfg.TP_CONNECTOR_EDGE != "back":
            raise ValueError("only TP_CONNECTOR_EDGE='back' is supported (pads face the keyboard)")
        clr = float(cfg.TP_CLEARANCE)
        self.mod_x0 = float(cfg.TP_CENTER_X) - cfg.TP_WIDTH / 2.0
        self.mod_x1 = self.mod_x0 + cfg.TP_WIDTH
        self.open_y1 = D - float(cfg.TP_BACK_MARGIN)
        self.mod_y1 = self.open_y1 - clr
        self.mod_y0 = self.mod_y1 - cfg.TP_DEPTH
        self.tp_cx = float(cfg.TP_CENTER_X)
        self.tp_cy = (self.mod_y0 + self.mod_y1) / 2.0
        self.open_w = cfg.TP_WIDTH + 2 * clr
        self.open_d = cfg.TP_DEPTH + 2 * clr
        self.open_r = float(cfg.POCKET_CORNER_R)
        self.open_x0 = self.tp_cx - self.open_w / 2
        self.open_x1 = self.tp_cx + self.open_w / 2
        self.open_y0 = self.open_y1 - self.open_d
        self.opening = C.rounded_rect(self.open_x0, self.open_y0, self.open_x1, self.open_y1, self.open_r)
        sm, fm = float(cfg.TP_MIN_SIDE_MARGIN), float(cfg.TP_MIN_FRONT_MARGIN)
        if self.open_x0 < sm or self.open_x1 > W - sm or self.open_y0 < fm:
            raise ValueError("trackpad pocket does not fit the rest (check TP_* / REST_* sizes, "
                             "TP_MIN_SIDE_MARGIN / TP_MIN_FRONT_MARGIN)")
        # pocket corner vs the parts' corners: a part of corner radius Rp fits a
        # pocket of radius Ro with side clearance c only if Ro - Rp <= c / (sqrt2 - 1)
        k = math.sqrt(2.0) / (math.sqrt(2.0) - 1.0)   # = 3.414
        parts = [("module", float(cfg.TP_CORNER_R), cfg.TP_WIDTH, cfg.TP_DEPTH)]
        if self.glass_t > 0:
            parts.append(("glass", float(cfg.GLASS_CORNER_R), cfg.GLASS_WIDTH, cfg.GLASS_DEPTH))
        r_min = min(p[1] for p in parts)
        if self.open_r > r_min + 3.4 * clr - 0.2 + 1e-9:
            raise ValueError(f"POCKET_CORNER_R {self.open_r:g} pinches an R{r_min:g} corner: keep it <= "
                             f"min(TP_CORNER_R, GLASS_CORNER_R) + 3.4 x TP_CLEARANCE - 0.2 = "
                             f"{r_min + 3.4 * clr - 0.2:.2f}")
        self.corner_gaps = {}
        for name, rp, pw, pd in parts:
            c_side = min(self.open_w - pw, self.open_d - pd) / 2.0
            self.corner_gaps[name] = math.sqrt(2.0) * c_side - (math.sqrt(2.0) - 1.0) * (self.open_r - rp)
        log(f"pocket corner R{self.open_r:g}: corner gap " + ", ".join(
            f"{n} (R{rp:g}) {self.corner_gaps[n]:.2f} mm" for n, rp, _, _ in parts)
            + f"; any part corner >= R{max(self.open_r - k * clr, 0.0):.2f} fits")
        # rim bevel must leave a vertical wall above the glass / film top edge
        ch_h, recess = float(cfg.POCKET_RIM_CHAMFER_H), float(cfg.TP_SURFACE_RECESS)
        if cfg.POCKET_RIM_CHAMFER > 0 and ch_h > recess - 0.05 + 1e-9:
            raise ValueError(f"POCKET_RIM_CHAMFER_H {ch_h:g} must be <= TP_SURFACE_RECESS - 0.05 = "
                             f"{recess - 0.05:.2f}, or the glass top edge stands above the pocket wall")

        # depths (Z)
        self.pocket_depth = (cfg.TP_SURFACE_RECESS + self.glass_t + cfg.TP_ADHESIVE_T + cfg.TP_PCB_T)
        self.ledge_z = H - self.pocket_depth
        self.pcb_top_z = self.ledge_z + cfg.TP_PCB_T
        self.adhesive_top_z = self.pcb_top_z + cfg.TP_ADHESIVE_T
        self.glass_top_z = self.adhesive_top_z + self.glass_t if self.glass_t > 0 else None
        self.cavity_z = self.ledge_z - cfg.POCKET_CAVITY_DEPTH
        self.well_z = self.ledge_z - cfg.POCKET_WELL_DEPTH
        self.tunnel_ceiling = self.ledge_z - cfg.CABLE_SKIN
        self.tunnel_floor = self.tunnel_ceiling - cfg.CABLE_TUNNEL_H
        self.notch_floor = H - cfg.CABLE_NOTCH_DEPTH
        self.notch_x = float(cfg.CABLE_NOTCH_X)
        self.notch_y0 = D - float(cfg.CABLE_NOTCH_LEN)
        self.notch_r_u = min(float(cfg.CABLE_NOTCH_W) / 2.0, float(cfg.CABLE_NOTCH_DEPTH))
        if self.notch_y0 < self.open_y1 + 1.2:
            raise ValueError("CABLE_NOTCH_LEN would break into the pocket (keep >= 1.2 mm wall)")
        riser_len = float(cfg.CABLE_NOTCH_LEN) - float(cfg.CABLE_RISER_BACK_WALL)
        if riser_len < cfg.CABLE_D + 1.0 - 1e-9:
            raise ValueError(f"cable riser is {riser_len:.2f} mm long (CABLE_NOTCH_LEN - CABLE_RISER_BACK_WALL); "
                             f"it needs >= CABLE_D + 1 = {cfg.CABLE_D + 1.0:.2f} mm (raise TP_BACK_MARGIN)")
        # riser top: where the U-notch is as wide as the channel (+0.3 mm), so the
        # riser -> notch passage never narrows below CABLE_CHANNEL_W
        if cfg.CABLE_RISER_TOP is not None:
            self.riser_top = float(cfg.CABLE_RISER_TOP)
        else:
            hw = cfg.CABLE_CHANNEL_W / 2.0
            ru = self.notch_r_u
            full = ru - math.sqrt(ru * ru - hw * hw) if hw < ru else ru
            self.riser_top = self.notch_floor + full + 0.3
        if self.riser_top <= self.notch_floor + 0.05:
            raise ValueError("CABLE_RISER_TOP must be above the notch floor")
        # plug bay: a shallow slot in the back-top edge the plug's strain relief
        # and the loose wires turn down into
        self.bay, self.bay_floor = None, H
        if cfg.PLUG_BAY_DEPTH > 0:
            bw, bl = float(cfg.PLUG_BAY_W), float(cfg.PLUG_BAY_L)
            self.bay_floor = H - float(cfg.PLUG_BAY_DEPTH)
            self.bay_x0, self.bay_x1 = self.notch_x - bw / 2.0, self.notch_x + bw / 2.0
            self.bay_y0 = D - bl
            if abs(self.bay_y0 - self.notch_y0) < 0.05:
                self.bay_y0 = self.notch_y0 - 0.05   # no wall coincident with the notch's
            if bw < cfg.CABLE_NOTCH_W + 2.0:
                raise ValueError("PLUG_BAY_W must exceed CABLE_NOTCH_W + 2")
            if self.bay_y0 < self.open_y1 + 1.2:
                raise ValueError("PLUG_BAY_L would break into the pocket (keep >= 1.2 mm wall)")
            if self.bay_floor < cfg.MIN_FLOOR + 2.0:
                raise ValueError("PLUG_BAY_DEPTH leaves too little material under the bay")
            self.bay = C.rounded_rect(self.bay_x0, self.bay_y0, self.bay_x1, D + 3.0, float(cfg.PLUG_BAY_R))
        for name, z in (("relief cavity", self.cavity_z), ("solder well", self.well_z),
                        ("cable tunnel", self.tunnel_floor)):
            if z < cfg.MIN_FLOOR - 1e-9:
                raise ValueError(f"{name} floor {z:.2f} mm < MIN_FLOOR {cfg.MIN_FLOOR} "
                                 f"(raise REST_HEIGHT or reduce the pocket stack / CABLE_D)")

        # module-local (front view) -> assembly
        self.m2a = lambda x, y: (self.mod_x0 + x, self.mod_y1 - y)
        L = cfg.POCKET_LEDGE
        self.module_inset = C.rounded_rect(self.mod_x0 + L, self.mod_y0 + L, self.mod_x1 - L,
                                           self.mod_y1 - L, max(cfg.TP_CORNER_R - L, 0.6))

        def box(b, m=0.0):
            x0, x1, y0, y1 = b
            return (self.mod_x0 + x0 - m, self.mod_y1 - y1 - m, self.mod_x0 + x1 + m, self.mod_y1 - y0 + m)
        self.box_asm = box
        # relief = every point within POCKET_CAVITY_MARGIN of the component box
        # (Minkowski buffer -> corner radius = margin), clipped by the ledge
        comp = shapely.box(*box(cfg.TP_COMPONENT_BOX))
        self.component_box = comp
        self.cavity = comp.buffer(cfg.POCKET_CAVITY_MARGIN, quad_segs=C.QS).intersection(self.module_inset)
        if not self.cavity.buffer(1e-6).contains(comp.buffer(1.0 - 1e-3, quad_segs=C.QS)):
            log("WARNING: relief cavity does not cover component box + 1.0 mm (ledge wins)")

        # cable: groove polyline in the well (S-bend strain relief) -> tunnel -> riser -> notch
        pads = box(cfg.TP_PADS_BOX)
        zif = box(cfg.TP_ZIF_BOX)
        self.pads_c = ((pads[0] + pads[2]) / 2, (pads[1] + pads[3]) / 2)
        wm = cfg.POCKET_WELL_MARGIN
        wb = (min(pads[0], zif[0]) - wm, min(pads[1], zif[1]) - wm,
              max(pads[2], zif[2]) + wm, max(pads[3], zif[3]) + wm)
        Xn = self.notch_x
        if not (self.mod_x0 + L + cfg.CABLE_CHANNEL_W / 2 + 1 < Xn < self.mod_x1 - L - cfg.CABLE_CHANNEL_W / 2 - 1):
            raise ValueError("cable notch (CABLE_NOTCH_X, under the dock connector) is not under the "
                             "module; adjust TP_CENTER_X")
        y_wb = min(wb[3], self.mod_y1 - L)
        sgn = -1.0 if self.pads_c[0] < Xn else 1.0
        S = float(cfg.CABLE_SBEND)
        P0 = (Xn, y_wb)
        P1 = (Xn, self.pads_c[1] - float(cfg.CABLE_GROOVE_PAD_SETBACK))
        P2 = (Xn + sgn * S, P1[1] - S)
        P3 = (Xn + sgn * S, P2[1] - float(cfg.CABLE_GROOVE_TAIL))
        self.groove_line = LineString([P0, P1, P2, P3])
        self.jacket_end = P3
        well = C.rounded_rect(*wb, cfg.POCKET_INNER_R).union(
            self.groove_line.buffer(cfg.CABLE_CHANNEL_W / 2 + 1.0, quad_segs=C.QS))
        well = well.buffer(1.0, quad_segs=C.QS).buffer(-1.0, quad_segs=C.QS)
        self.well = well.intersection(self.module_inset)
        self.groove = self.groove_line.buffer(cfg.CABLE_CHANNEL_W / 2, quad_segs=C.QS)
        if not self.well.buffer(1e-6).contains(self.groove.intersection(
                Polygon([(0, 0), (W, 0), (W, self.mod_y1 - L), (0, self.mod_y1 - L)]))):
            log("WARNING: strain-relief groove leaves the solder well")
        self.tunnel_y0 = y_wb - 1.0
        self.tunnel_y1 = self.notch_y0 + 0.5
        self.riser_y1 = D - float(cfg.CABLE_RISER_BACK_WALL)

        # push-out holes (module front view -> assembly)
        self.push_holes = [self.m2a(x, y) for x, y in cfg.PUSH_HOLE_POS]
        for (hx, hy) in self.push_holes:
            c = Point(hx, hy).buffer(cfg.PUSH_HOLE_D / 2, quad_segs=C.QS)
            if c.intersects(self.cavity) or c.intersects(self.well) or not self.module_inset.contains(c):
                raise ValueError("PUSH_HOLE_POS must lie under the flat, component-free module area")

        # cable footprint in plan (groove + tunnel + riser/notch) and its floor
        self.cable_area = shapely.union_all([
            self.groove, shapely.box(Xn - cfg.CABLE_CHANNEL_W / 2, self.tunnel_y0,
                                     Xn + cfg.CABLE_CHANNEL_W / 2, self.riser_y1)])

        # bumpers: 4 corners + front/back middle; the back-middle one steps
        # sideways (away from the S-bend) so its recess never thins the floor
        # under the cable tunnel
        if cfg.BUMPER_POSITIONS:
            self.bumpers = [tuple(map(float, p)) for p in cfg.BUMPER_POSITIONS]
        else:
            i = float(cfg.BUMPER_INSET)
            bm = (self.tp_cx, D - i)
            if Point(bm).buffer(cfg.BUMPER_D / 2 + 1.0).intersects(self.cable_area):
                off = cfg.CABLE_CHANNEL_W / 2 + cfg.BUMPER_D / 2 + 2.0
                bm = (Xn - sgn * off, D - i)
            self.bumpers = [(i, i), (W - i, i), (i, D - i), (W - i, D - i), (self.tp_cx, i), bm]
        for (bx, by) in self.bumpers:
            c = Point(bx, by).buffer(cfg.BUMPER_D / 2)
            above = [z for geom, z in ((self.cable_area, self.tunnel_floor), (self.well, self.well_z),
                                       (self.cavity, self.cavity_z), (self.opening, self.ledge_z))
                     if c.intersects(geom)]
            if above and min(above) - cfg.BUMPER_RECESS < cfg.MIN_FLOOR - 1e-9:
                log(f"WARNING: bumper at ({bx:.1f}, {by:.1f}) leaves {min(above) - cfg.BUMPER_RECESS:.2f} mm "
                    f"floor (< MIN_FLOOR) - move it (BUMPER_POSITIONS)")
            if any(c.intersects(Point(p).buffer(cfg.PUSH_HOLE_D / 2 + 1.0)) for p in self.push_holes):
                raise ValueError(f"bumper at ({bx:.1f}, {by:.1f}) overlaps a push-out hole")
        self.ballast = []        # filled by place_ballast()
        self.engrave = None      # filled by place_engraving()

    # -- needs the surface ----------------------------------------------------
    def place_ballast(self, cfg, surf):
        self.ballast = []
        if not cfg.BALLAST_ENABLED:
            return
        L, Wb, T = (float(v) for v in cfg.BALLAST_SIZE)
        c = float(cfg.BALLAST_CLEARANCE)
        Lp, Wp, Dp = L + 2 * c, Wb + 2 * c, T + c
        yc = float(cfg.BALLAST_CENTER_Y) if cfg.BALLAST_CENTER_Y is not None else self.D / 2.0
        y0, y1 = yc - Wp / 2, yc + Wp / 2
        dist = float(cfg.BALLAST_MIN_DIST_FROM_TP)
        # wall measured at the bed: the outline polygon is the chamfer top, the
        # footprint on the bed is REST_BOTTOM_CHAMFER inside it
        safe = surf.outline.polygon.buffer(-(float(cfg.REST_BOTTOM_CHAMFER) + float(cfg.BALLAST_WALL)),
                                           quad_segs=C.QS)
        bumper_keep = [Point(b).buffer(cfg.BUMPER_D / 2 + 1.5, quad_segs=16) for b in self.bumpers]
        min_len, min_depth = float(cfg.BALLAST_MIN_LEN), float(cfg.BALLAST_MIN_DEPTH)
        auto = bool(cfg.BALLAST_AUTO_SHORTEN)

        def fits(x0, x1):
            r = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
            return safe.contains(r) and not any(r.intersects(k) for k in bumper_keep)

        def top_min(x0, x1):
            gx, gy = np.meshgrid(np.linspace(x0, x1, 25), np.linspace(y0, y1, 7))
            return float(surf.top_z(gx.ravel(), gy.ravel()).min())

        for side in ("left", "right"):
            # start at the full bar length, BALLAST_MIN_DIST_FROM_TP from the
            # pad; shorten from the outer end until it clears outline + bumpers
            if side == "left":
                x1 = self.open_x0 - dist
                x0 = x1 - Lp
            else:
                x0 = self.open_x1 + dist
                x1 = x0 + Lp
            while (x1 - x0) >= min_len and not fits(x0, x1):
                if side == "left":
                    x0 += 0.5
                else:
                    x1 -= 0.5
            if (x1 - x0) < min_len:
                log(f"ballast {side}: no room (>= {min_len:g} mm long) - pocket omitted")
                continue
            depth = Dp
            tmin = top_min(x0, x1)
            if tmin - depth < cfg.BALLAST_MIN_TOP_SKIN:
                new = tmin - cfg.BALLAST_MIN_TOP_SKIN
                if new < min_depth:
                    log(f"ballast {side}: top too low for any pocket - omitted")
                    continue
                if not auto:
                    raise ValueError(f"ballast {side}: a {T:g} mm bar leaves < {cfg.BALLAST_MIN_TOP_SKIN} mm top "
                                     f"skin (BALLAST_AUTO_SHORTEN=False; use a thinner bar)")
                log(f"ballast {side}: depth reduced {depth:.2f} -> {new:.2f} mm to keep "
                    f"{cfg.BALLAST_MIN_TOP_SKIN} mm top skin")
                depth = new
            eff_len = (x1 - x0) - 2 * c
            if abs(eff_len - L) > 1e-6:
                if not auto:
                    raise ValueError(f"ballast {side}: a {L:g} mm bar does not fit - the longest is "
                                     f"{eff_len:g} mm (BALLAST_AUTO_SHORTEN=False; set BALLAST_SIZE)")
                log(f"ballast {side}: bar length {L:.1f} -> {eff_len:.1f} mm (keeps "
                    f"{dist:.0f} mm from the trackpad and {cfg.BALLAST_WALL} mm walls at the bed)")
            self.ballast.append({"side": side, "x0": x0, "x1": x1, "y0": y0, "y1": y1,
                                 "depth": depth, "bar": [round(eff_len, 2), Wb, round(min(T, depth - c), 2)],
                                 "top_min": tmin})

    def place_engraving(self, cfg, surf):
        if not cfg.ENGRAVE_TEXT:
            self.engrave = {"geom": Polygon(), "center": (0.0, 0.0), "size": (0.0, 0.0),
                            "font": None, "face": cfg.ENGRAVE_FACE}
            return
        geom, font_path = text_geometry(cfg.ENGRAVE_TEXT, cfg.ENGRAVE_FONT, float(cfg.ENGRAVE_HEIGHT))
        minx, miny, maxx, maxy = geom.bounds
        tw, th = maxx - minx, maxy - miny
        xc = self.tp_cx if cfg.ENGRAVE_FACE == "top" else self.W / 2.0
        if cfg.ENGRAVE_FACE == "bottom":
            geom = affinity.scale(geom, xfact=-1.0, yfact=1.0, origin=(0, 0))  # mirrored
            obstacles = ([Point(b).buffer(cfg.BUMPER_D / 2, quad_segs=16) for b in self.bumpers]
                         + [Point(p).buffer(cfg.PUSH_HOLE_D / 2, quad_segs=16) for p in self.push_holes]
                         + [Polygon([(b["x0"], b["y0"]), (b["x1"], b["y0"]), (b["x1"], b["y1"]),
                                     (b["x0"], b["y1"])]) for b in self.ballast])
            obst = shapely.union_all(obstacles)
            margin = float(cfg.ENGRAVE_MARGIN)
            keep = surf.outline.polygon.buffer(-(cfg.REST_BOTTOM_CHAMFER + margin), quad_segs=C.QS)
            if cfg.ENGRAVE_CENTER_Y is not None:
                yc = float(cfg.ENGRAVE_CENTER_Y)
            else:
                best, yc = -1e9, self.D / 4
                for y in np.arange(th / 2 + margin + 1.0, self.D / 2 + 1e-9, 0.25):
                    bb = shapely.box(xc - tw / 2, y + miny, xc + tw / 2, y + maxy)
                    if not keep.contains(bb):
                        continue
                    score = bb.distance(obst)
                    if score > best + 1e-9:
                        best, yc = score, y
            placed = affinity.translate(geom, xc, yc)
            if placed.intersects(obst.buffer(0.5)):
                log("WARNING: bottom engraving touches a bumper / push hole / ballast pocket")
        else:
            if cfg.ENGRAVE_CENTER_Y is not None:
                yc = float(cfg.ENGRAVE_CENTER_Y)
            else:
                yc = self.open_y0 - float(cfg.ENGRAVE_PAD_GAP) - maxy
            placed = affinity.translate(geom, xc, yc)
            if placed.intersects(self.opening.buffer(1.5)):
                log("WARNING: top engraving runs into the trackpad pocket")
        if not surf.outline.polygon.buffer(-1.0).contains(placed):
            log("WARNING: engraving runs off the rest")
        self.engrave = {"geom": placed, "center": (xc, yc), "size": (tw, th), "font": font_path,
                        "face": cfg.ENGRAVE_FACE}


# ---------------------------------------------------------------------------
# top surface z = top_z(x, y)
# ---------------------------------------------------------------------------

class Surface:
    def __init__(self, cfg, layout):
        self.cfg = cfg
        self.lay = layout
        L = float(cfg.MESH_EDGE_LEN)
        self.outline = Outline(cfg, spacing=0.9 * L)
        H = float(cfg.REST_HEIGHT)
        D = float(cfg.REST_DEPTH)
        self.H, self.D = H, D
        if cfg.REST_PROFILE:
            pts = sorted((float(s), float(z)) for s, z in cfg.REST_PROFILE)
            zs = np.array([p[1] for p in pts])
            if abs(zs.max() - H) > 1e-9:
                log(f"REST_PROFILE max {zs.max():.3f} normalised to REST_HEIGHT {H:.3f}")
                zs = zs * (H / zs.max())
            self._prof = C.pchip([p[0] for p in pts], zs)
        else:
            Hb, Hf = float(cfg.REST_BACK_HEIGHT), float(cfg.REST_FRONT_HEIGHT)
            P = float(cfg.REST_PEAK_FROM_BACK)
            p = float(cfg.REST_FALL_POWER)
            if not (Hb <= H + 1e-9 and Hf <= H + 1e-9 and 0 <= P < D - 5 and p > 1.0):
                raise ValueError("profile needs REST_BACK/FRONT_HEIGHT <= REST_HEIGHT, "
                                 "0 <= REST_PEAK_FROM_BACK < REST_DEPTH-5, REST_FALL_POWER > 1")

            def prof(s):
                s = np.clip(np.asarray(s, dtype=float), 0.0, D)
                up = Hb + (H - Hb) * np.sin(0.5 * np.pi * np.clip(s / max(P, 1e-9), 0, 1))
                t = np.clip((s - P) / (D - P), 0.0, 1.0)
                down = H - (H - Hf) * t ** p
                return np.where(s <= P, up, down)
            self._prof = prof

        # round-over parameters along the outline (a = horizontal, b = vertical)
        ol = self.outline
        c = float(cfg.REST_BOTTOM_CHAMFER)
        nose_v = (cfg.REST_FRONT_NOSE_V if cfg.REST_FRONT_NOSE_V is not None
                  else cfg.REST_FRONT_NOSE_R / 2.0)
        A = np.array([cfg.REST_BACK_EDGE_R, cfg.REST_END_EDGE_R, cfg.REST_FRONT_NOSE_R], dtype=float)
        B = np.array([cfg.REST_BACK_EDGE_R, cfg.REST_END_EDGE_R, nose_v], dtype=float)
        self.edge_a = ol.wts @ A
        b = ol.wts @ B
        hb = self.h(ol.pts[:, 0], ol.pts[:, 1])
        budget = hb - c - float(cfg.REST_MIN_WALL)
        if budget.min() <= 0.3:
            raise ValueError("rest too low at its edge for the bottom chamfer + min wall")
        self.edge_b = np.minimum(C.softmin(b, budget, 0.3), budget)
        if np.any(self.edge_b < b - 0.05):
            log(f"edge round-over height limited by the wall budget (min wall "
                f"{cfg.REST_MIN_WALL} mm above the chamfer)")
        if self.edge_a.max() >= cfg.REST_PLAN_FRONT_CORNER_R:
            raise ValueError("REST_FRONT_NOSE_R / REST_END_EDGE_R must be < REST_PLAN_FRONT_CORNER_R")
        if cfg.REST_BACK_EDGE_R >= cfg.REST_PLAN_BACK_CORNER_R:
            raise ValueError("REST_BACK_EDGE_R must be < REST_PLAN_BACK_CORNER_R")
        self.wall_top = hb - self.edge_b

    # base surface: crowned profile + flat island around the pocket
    def profile(self, s):
        return self._prof(s)

    def island_weight(self, x, y):
        lay = self.lay
        sdf = C.rounded_rect_sdf(np.asarray(x, float), np.asarray(y, float), lay.tp_cx,
                                 (lay.open_y0 + lay.open_y1) / 2, lay.open_w, lay.open_d, lay.open_r)
        t = (sdf - float(self.cfg.TP_BEZEL)) / float(self.cfg.TP_BLEND)
        return 1.0 - C.smoothstep(t)

    def h(self, x, y):
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        p = self.profile(self.D - y)
        w = self.island_weight(x, y)
        return p + (self.H - p) * w

    def top_z(self, x, y):
        """Analytic top surface incl. the edge round-overs (for arbitrary points)."""
        x = np.atleast_1d(np.asarray(x, float))
        y = np.atleast_1d(np.asarray(y, float))
        ol = self.outline
        pts = shapely.points(x, y)
        d = shapely.distance(pts, ol.ring)
        inside = shapely.contains_xy(ol.polygon, x, y)
        d = np.where(inside, d, 0.0)
        s = shapely.line_locate_point(ol.ring, pts)
        a = ol.interp(self.edge_a, s)
        b = ol.interp(self.edge_b, s)
        u = np.clip((a - np.minimum(d, a)) / a, 0.0, 1.0)
        drop = b * (1.0 - np.sqrt(np.maximum(1.0 - u * u, 0.0)))
        return self.h(x, y) - drop


# ---------------------------------------------------------------------------
# body mesh
# ---------------------------------------------------------------------------

def build_body(cfg, surf):
    ol = surf.outline
    L = float(cfg.MESH_EDGE_LEN)
    N = ol.n
    P, Nr = ol.pts, ol.nrm
    a, b = surf.edge_a, surf.edge_b
    c = float(cfg.REST_BOTTOM_CHAMFER)
    quarter = 0.25 * math.pi * (a + b)            # ~ elliptic quarter arc length
    K = int(max(18, math.ceil(quarter.max() / (0.75 * L))))
    # rings at equal steps of the round-over's tangent angle psi (0 = vertical
    # wall, 90 = horizontal): theta = atan(b/a * tan psi) per vertex, so every
    # facet turns by 90/K deg whatever the ellipse aspect (tight nose foot too)
    psi = np.linspace(0.0, 0.5 * math.pi, K + 1)

    verts = []
    bot = P - Nr * c                              # chamfer foot, z = 0
    verts.append(np.column_stack([bot, np.zeros(N)]))
    verts.append(np.column_stack([P, np.full(N, c)]))   # chamfer top
    rings = []
    for k in range(K + 1):
        th = np.arctan2(b * math.sin(psi[k]), a * math.cos(psi[k]))
        dk = a * (1.0 - np.cos(th))
        Rk = P - Nr * dk[:, None]
        zk = surf.h(Rk[:, 0], Rk[:, 1]) - b * (1.0 - np.sin(th))
        rings.append(Rk)
        verts.append(np.column_stack([Rk, zk]))
    if np.any(verts[2][:, 2] <= c + 0.05):
        raise RuntimeError("wall top below the bottom chamfer")

    inner = rings[-1]
    inner_poly = Polygon(inner)
    if not inner_poly.is_valid:
        raise RuntimeError("inner band ring self-intersects (round-over radii too large?)")
    # hexagonal lattice inside the inner ring, kept >= 0.6 L from it
    minx, miny, maxx, maxy = inner_poly.bounds
    dy = L * math.sqrt(3) / 2
    ys = np.arange(miny + dy / 2, maxy, dy)
    gx, gy = [], []
    for j, yy in enumerate(ys):
        xs = np.arange(minx + (L / 2 if j % 2 else 0.0), maxx, L)
        gx.append(xs)
        gy.append(np.full(len(xs), yy))
    gx = np.concatenate(gx)
    gy = np.concatenate(gy)
    keep = shapely.contains_xy(inner_poly, gx, gy)
    gx, gy = gx[keep], gy[keep]
    dd = shapely.distance(shapely.points(gx, gy), inner_poly.exterior)
    keep = dd >= 0.6 * L
    lat = np.column_stack([gx[keep], gy[keep]])
    zlat = surf.h(lat[:, 0], lat[:, 1])
    verts.append(np.column_stack([lat, zlat]))

    pts2 = np.vstack([inner, lat])
    tri = Delaunay(pts2).simplices
    cen = pts2[tri].mean(axis=1)
    tri = tri[shapely.contains_xy(inner_poly, cen[:, 0], cen[:, 1])]
    p0, p1, p2 = pts2[tri[:, 0]], pts2[tri[:, 1]], pts2[tri[:, 2]]
    area = (p1[:, 0] - p0[:, 0]) * (p2[:, 1] - p0[:, 1]) - (p1[:, 1] - p0[:, 1]) * (p2[:, 0] - p0[:, 0])
    tri[area < 0] = tri[area < 0][:, [0, 2, 1]]
    edges = set(map(tuple, np.sort(np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1)))
    ring_edges = [(i, (i + 1) % N) for i in range(N)]
    missing = [e for e in ring_edges if tuple(sorted(e)) not in edges]
    if missing:
        raise RuntimeError(f"interior triangulation misses {len(missing)} ring edges")

    V = np.vstack(verts)
    i_bot = np.arange(N)
    i_cha = N + np.arange(N)
    i_ring = lambda k: 2 * N + k * N + np.arange(N)
    i_lat0 = 2 * N + (K + 1) * N
    nxt = lambda idx: np.roll(idx, -1)
    faces = []

    def strip(lo, hi):   # lo ring -> hi ring, outward / upward facing
        faces.append(np.column_stack([lo, nxt(lo), nxt(hi)]))
        faces.append(np.column_stack([lo, nxt(hi), hi]))
    strip(i_bot, i_cha)                       # chamfer
    strip(i_cha, i_ring(0))                   # vertical wall
    for k in range(K):
        strip(i_ring(k), i_ring(k + 1))      # round-over band
    # interior (map Delaunay indices: [inner ring | lattice])
    remap = np.concatenate([i_ring(K), i_lat0 + np.arange(len(lat))])
    faces.append(remap[tri])
    # bottom (flat fan via manifold's triangulator), facing down
    bt = np.asarray(triangulate([bot]))
    faces.append(bt[:, [0, 2, 1]])
    F = np.vstack(faces)
    body = C.manifold_from_arrays(V, F)
    if body.volume() <= 0:
        raise RuntimeError("body has non-positive volume (orientation)")
    return body, {"rings": K, "boundary_samples": N, "lattice_points": int(len(lat))}


# ---------------------------------------------------------------------------
# cutters
# ---------------------------------------------------------------------------

def _notch_cutter(cfg, lay):
    nw, H = float(cfg.CABLE_NOTCH_W), lay.H
    r_u = min(nw / 2, float(cfg.CABLE_NOTCH_DEPTH))
    prof = C.rounded_rect(lay.notch_x - nw / 2, lay.notch_floor, lay.notch_x + nw / 2,
                          H + 2.0 + r_u, r_u)
    length = (lay.D + 1.0) - lay.notch_y0
    m = Manifold.extrude(C.to_cross_section(prof), length)
    m = m.rotate((90.0, 0.0, 0.0))            # (x, y, e) -> (x, -e, y)
    return m.translate((0.0, lay.D + 1.0, 0.0))


def _text_cutter_top(cfg, lay, surf, geom):
    depth = float(cfg.ENGRAVE_DEPTH)
    cs = C.to_cross_section(geom)
    m = Manifold.extrude(cs, 1.0).refine_to_length(0.6)

    def warp(v):
        v = np.array(v, dtype=float, copy=True)
        t = surf.top_z(v[:, 0], v[:, 1])
        v[:, 2] = t - depth + v[:, 2] * (depth + 1.0)
        return v
    return m.warp_batch(warp)


def plan(cfg, glass_t):
    """Positions only (no mesh): Layout + Surface with ballast/engraving placed."""
    lay = Layout(cfg, glass_t)
    surf = Surface(cfg, lay)
    lay.place_ballast(cfg, surf)
    lay.place_engraving(cfg, surf)
    return lay, surf


def build_rest(cfg, variant, glass_t):
    """Returns (manifold, info) for one variant."""
    lay, surf = plan(cfg, glass_t)
    body, mesh_info = build_body(cfg, surf)
    H, D = lay.H, lay.D
    ch_w, ch_h = float(cfg.POCKET_RIM_CHAMFER), float(cfg.POCKET_RIM_CHAMFER_H)
    W_ch = float(cfg.CABLE_CHANNEL_W)
    Xn = lay.notch_x
    cut = []
    # NOTE: cutters never share a coplanar / coincident face (tops, floors and
    # walls are offset by >= 0.05 mm): coincident faces leave sub-nm slivers
    # that turn non-manifold as soon as an STL reader merges vertices.
    # stepped pocket
    cut.append(C.prism(lay.opening, lay.ledge_z, H + 2.0))
    if ch_w > 0 and ch_h > 0:
        # rim bevel ch_w wide x ch_h high: the vertical wall ends at H - ch_h,
        # above the glass / film top. The cone starts 0.05 inside the opening
        # (so it cuts the wall transversally) and ends above the rest top.
        k = ch_w / ch_h                          # horizontal run per mm of rise
        z_lo = H - ch_h - 0.05 / k
        z_hi = H + 0.3
        cut.append(C.frustum_hull(lay.opening.buffer(-0.05, quad_segs=C.QS), z_lo,
                                  lay.opening.buffer((z_hi - (H - ch_h)) * k, quad_segs=C.QS), z_hi))
    if lay.bay is not None:
        # plug bay (plan corners PLUG_BAY_R) + 45 deg chamfer on its top edges
        cut.append(C.prism(lay.bay, lay.bay_floor, H + 2.0))
        bc = float(cfg.PLUG_BAY_CHAMFER)
        if bc > 0:
            cut.append(C.frustum_hull(lay.bay.buffer(-0.05, quad_segs=C.QS), H - bc - 0.05,
                                      lay.bay.buffer(bc + 1.0, quad_segs=C.QS), H + 1.0))
    cut.append(C.prism(lay.cavity, lay.cavity_z, lay.ledge_z + 0.5))
    cut.append(C.prism(lay.well, lay.well_z, lay.ledge_z + 0.6))
    groove = lay.groove_line.buffer(W_ch / 2 - 0.05, quad_segs=C.QS)
    cut.append(C.prism(groove, lay.tunnel_floor + 0.1, lay.well_z + 0.3))
    # cable tunnel + riser as one side-view (Y, Z) profile extruded along X
    side = shapely.union_all([
        shapely.box(lay.tunnel_y0, lay.tunnel_floor, lay.tunnel_y1, lay.tunnel_ceiling),
        shapely.box(lay.notch_y0, lay.tunnel_floor, lay.riser_y1, lay.riser_top)])
    tun = Manifold.extrude(C.to_cross_section(side), W_ch)       # (y, z, e)
    tun = tun.transform(np.array([[0.0, 0.0, 1.0, Xn - W_ch / 2],   # x = e
                                  [1.0, 0.0, 0.0, 0.0],              # y = u
                                  [0.0, 1.0, 0.0, 0.0]]))            # z = v
    cut.append(tun)
    cut.append(_notch_cutter(cfg, lay))
    # push-out holes
    for (hx, hy) in lay.push_holes:
        cut.append(C.cylinder(hx, hy, cfg.PUSH_HOLE_D / 2, -1.0, lay.ledge_z + 0.7))
    # underside
    for (bx, by) in lay.bumpers:
        cut.append(C.cylinder(bx, by, cfg.BUMPER_D / 2, -1.0, cfg.BUMPER_RECESS))
    for bp in lay.ballast:
        cut.append(C.prism(shapely.box(bp["x0"], bp["y0"], bp["x1"], bp["y1"]), -1.0, bp["depth"]))
    eng = lay.engrave
    if cfg.ENGRAVE_TEXT:
        if eng["face"] == "bottom":
            cut.append(C.prism(eng["geom"], -1.0, cfg.ENGRAVE_DEPTH))
        else:
            cut.append(_text_cutter_top(cfg, lay, surf, eng["geom"]))
    rest = C.subtract_all(body, cut)
    status = str(rest.status())
    if not status.endswith("NoError"):
        raise RuntimeError(f"boolean failed: {status}")
    info = {"layout": lay, "surface": surf, "mesh": mesh_info, "variant": variant}
    return rest, info
