#!/usr/bin/env python3
"""ithalat - parametric ergonomic wrist rest with an Azoteq TPS65 trackpad
pocket for the Yakamoz keyboard, plus the keyboard-side connector dock(s).

    python3 generate.py [overrides]          (normally: make generate GEN_ARGS=...)

Writes (paths relative to this folder):
    stl/ithalat-<variant>.stl       one rest per VARIANTS entry, shared by every
                                    connector (binary STL, assembly frame = print
                                    orientation, bottom on the bed)
    stl/ithalat-dock-<id>.stl       one keyboard dock per CONNECTORS entry
                                    (pogo / usbc / jst), print orientation
    stl/ithalat-usbc-grip-top.stl   USB-C only: grip clamshell halves and the
    stl/ithalat-usbc-grip-bottom.stl  board retainer + clip lock (print
    stl/ithalat-usbc-retainer.stl     orientation)
    build/manifest.json             everything the preview needs

Overrides: --height, --depth, --width, --glass-t, --tp-back-margin,
--engrave-face, --engrave-text, --no-ballast, --no-dock, --mesh-edge-len,
--connector NAME (repeatable: pogo5|usbc|jst_sh4 or pogo|usbc|jst), and
--set NAME=VALUE (python literal) for ANY constant in config.py. Derived values
(REST_HEIGHT from KEYBOARD_HEIGHT, VARIANTS from GLASS_T, ...) are recomputed
after the overrides.
"""

import glob
import json
import os
import sys
import time
import traceback

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from geometry import common as C  # noqa: E402
from geometry import connectors as CN  # noqa: E402
from geometry import plug  # noqa: E402
from geometry import rest  # noqa: E402
from geometry import usbc  # noqa: E402
from geometry.cfg import config_from_argv, config_names  # noqa: E402

STL_DIR = os.path.join(HERE, "stl")
BUILD_DIR = os.path.join(HERE, "build")
# generated connector STLs (stale ones from other CONNECTORS are removed)
CONNECTOR_STL_GLOBS = ("ithalat-dock*.stl", "ithalat-usbc-*.stl")


# ---------------------------------------------------------------------------
# docks
# ---------------------------------------------------------------------------

def dock_place_matrix(cfg):
    return CN.place_matrix(cfg)


def build_dock(cfg):
    """Pogo / JST dock (geometry/dock.py). Returns dict(mesh_print,
    mesh_local, print_T, info) or None."""
    try:
        from geometry import dock  # lazy: an optional module historically
    except Exception as e:  # noqa: BLE001
        print(f"WARNING: dock skipped - geometry/dock.py not importable ({e.__class__.__name__}: {e})")
        return None
    try:
        mesh_local, print_T = dock.build_dock(cfg)
        print_T = np.asarray(print_T, dtype=float)
        info = {}
        if hasattr(dock, "dock_info"):
            try:
                info = dock.dock_info(cfg) or {}
            except Exception as e:  # noqa: BLE001
                print(f"WARNING: dock_info failed ({e}); using DOCK_* fallbacks")
        m = mesh_local.copy()
        m.apply_transform(print_T)
        if not m.is_watertight:
            print("WARNING: dock mesh is not watertight")
        return {"mesh_print": m, "mesh_local": mesh_local, "print_T": print_T, "info": info}
    except Exception as e:  # noqa: BLE001
        print(f"WARNING: dock skipped - build_dock failed: {e.__class__.__name__}: {e}")
        traceback.print_exc()
        return None


def _placed_part(mesh_local, print_T, T_place, **kw):
    m = mesh_local.copy()
    m.apply_transform(print_T)
    if not m.is_watertight or m.volume <= 0:
        raise RuntimeError(f"{kw.get('stl')}: mesh not watertight / non-positive volume")
    return dict(mesh=m, matrix=T_place @ np.linalg.inv(print_T), variant=None, **kw)


def build_connector(cfg, ctype, with_dock=True):
    """Every printed part of one connector variant + what the manifest needs."""
    cc = CN.for_connector(cfg, ctype)
    cid = CN.cid(cfg, ctype)
    out = {"type": ctype, "id": cid, "label": CN.label(cfg, ctype), "cfg": cc, "parts": {}, "dock": None}
    T_place = dock_place_matrix(cc)
    out["T_place"] = T_place
    if ctype == "usbc":
        P = usbc.params(cc)          # ValueError = impossible config -> config error
        out["P"] = P
        out["info"] = usbc.dock_info(cc, P)
        out["info"]["retention"] = usbc.retention(cc, P)
        out["info"]["grip"] = usbc.grip_info(cc, P)
        if not (with_dock and cfg.DOCK_ENABLED):
            return out
        t0 = time.time()
        mesh_local, print_T = usbc.build_dock(cc, P)
        out["dock"] = {"mesh_local": mesh_local, "print_T": print_T, "info": out["info"]}
        out["parts"][f"dock-{cid}"] = _placed_part(
            mesh_local, print_T, T_place, role="dock", connector=cid, moves_with="dock",
            label=f"Dock ({out['label']})", stl=f"stl/ithalat-dock-{cid}.stl")
        if P.ret:
            rm, rT = usbc.build_retainer(cc, P)
            out["parts"]["usbc-retainer"] = _placed_part(
                rm, rT, T_place, role="retainer", connector=cid, moves_with="dock",
                label="USB-C board retainer + clip lock", stl="stl/ithalat-usbc-retainer.stl")
        grip = usbc.build_grip(cc, P)
        out["grip_local"] = {k: v[0] for k, v in grip.items()}
        for half in ("top", "bottom"):
            gm, gT = grip[half]
            out["parts"][f"usbc-grip-{half}"] = _placed_part(
                gm, gT, T_place, role="grip", connector=cid, moves_with="pad",
                label=f"USB-C grip, {half} half", stl=f"stl/ithalat-usbc-grip-{half}.stl")
        print(f"connector '{cid}' (USB-C): dock, retainer, grip in {time.time() - t0:.1f} s")
        return out
    if not (with_dock and cfg.DOCK_ENABLED):
        if not cfg.DOCK_ENABLED:
            print(f"dock-{cid}: disabled (DOCK_ENABLED=False)")
        return out
    d = build_dock(cc)
    if d is not None:
        out["dock"] = d
        out["info"] = d["info"]
        out["parts"][f"dock-{cid}"] = dict(
            mesh=d["mesh_print"], role="dock", variant=None, connector=cid, moves_with="dock",
            label=f"Dock ({out['label']})", stl=f"stl/ithalat-dock-{cid}.stl",
            matrix=T_place @ np.linalg.inv(d["print_T"]))
    return out


def _jsonable(v):
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, (np.floating,)):
        return round(float(v), 6)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, np.ndarray):
        return _jsonable(v.tolist())
    if isinstance(v, float):
        return round(v, 6) if np.isfinite(v) else None
    if v is None or isinstance(v, (bool, int, str)):
        return v
    return str(v)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build_all(cfg, with_dock=True):
    """Build every part in memory. Returns (parts, plans, conns)."""
    parts, plans = {}, {}
    rest.LOG.clear()
    for vid, glass_t in cfg.VARIANTS.items():
        t0 = time.time()
        print(f"rest '{vid}' (glass {glass_t:.2f} mm) ...")
        man, info = rest.build_rest(cfg, vid, glass_t)
        tm = C.to_trimesh(man)
        if not tm.is_watertight or tm.volume <= 0:
            raise RuntimeError(f"rest-{vid}: mesh not watertight / non-positive volume")
        parts[f"rest-{vid}"] = {"mesh": tm, "role": "rest", "variant": vid, "connector": None,
                                "moves_with": None, "label": f"Wrist rest ({cfg.VARIANT_LABELS.get(vid, vid)})",
                                "stl": f"stl/ithalat-{vid}.stl", "matrix": np.eye(4),
                                "seconds": time.time() - t0, "mesh_info": info["mesh"]}
        plans[vid] = info["layout"], info["surface"]
    conns = {}
    for ctype in cfg.CONNECTORS:
        c = build_connector(cfg, ctype, with_dock)
        conns[c["id"]] = c
        parts.update(c["parts"])
    return parts, plans, conns


def mass_estimates(cfg, tm):
    """Rough PLA mass at several infills: solid shell (MASS_SHELL_T x surface
    area) + infill fraction of the rest of the volume."""
    vol = float(tm.volume)
    shell = min(vol, float(tm.area) * cfg.MASS_SHELL_T)
    out = {}
    for pct in (15, 25, 100):
        f = pct / 100.0
        out[f"{pct}%"] = round((shell + f * (vol - shell)) / 1000.0 * cfg.PLA_DENSITY, 1)
    return out


def keyboard_keys(cfg):
    """Switch grid (KEY_ROWS x KEY_COLS minus KEY_ABSENT); REMOVED_KEYS flagged."""
    keys = []
    removed = {tuple(k) for k in cfg.REMOVED_KEYS}
    absent = {tuple(k) for k in cfg.KEY_ABSENT}
    last = int(cfg.KEY_ROWS) - 1
    for r in range(int(cfg.KEY_ROWS)):
        y = cfg.FRONT_ROW_Y + (last - r) * cfg.KEY_PITCH
        for i in range(int(cfg.KEY_COLS)):
            if (r, i) in absent:
                continue
            keys.append({"row": r, "col": i, "x": round(cfg.FIRST_KEY_X + i * cfg.KEY_PITCH, 3),
                         "y": round(y, 3), "removed": (r, i) in removed})
    return keys


def _plug_variant(cfg, conn, plans, vids):
    """Manifest object of a pogo / JST connector variant."""
    cc, ctype, cid = conn["cfg"], conn["type"], conn["id"]
    T_place = conn["T_place"]
    info = conn.get("info") or {}
    face = None
    if info.get("connector_face_center") is not None:
        p = np.append(np.asarray(info["connector_face_center"], dtype=float)[:3], 1.0)
        face = (T_place @ p)[:3]
    if face is None:
        face = plug.connector_face(cc)
    routes = {vid: plug.cable_route(cc, plans[vid][0], face) for vid in vids}
    env = routes[vids[0]]["envelope"]
    if not env["drop_ok"]:
        rest.log(f"WARNING: {cid} plug ({cc.PLUG_EXIT} exit): {env['drop_what']} is impossible - turn at "
                 f"y {env['drop_y']:.2f}, riser allows {env['drop_range'][0]:.2f}..{env['drop_range'][1]:.2f} "
                 f"(verify fails; see PLUG_* / TP_BACK_MARGIN)")
    lay0 = plans[vids[0]][0]
    cable = {"points": routes[vids[0]]["centerline"], "diameter": cc.CABLE_D, "pigtail_len": cc.CABLE_PIGTAIL_LEN,
             "wire_d": cc.CABLE_WIRE_D,
             "per_variant": {vid: {"centerline": r["centerline"], "sleeve": r["sleeve"],
                                   "wires": r["wires"], "sleeve_len": r["sleeve_len"]}
                             for vid, r in routes.items()},
             "plug": {"housing": [round(v, 4) for v in env["housing"]],
                      "relief": [round(v, 4) for v in env["relief"]] if env["relief"] else None,
                      "exit": env["exit"], "tail_l": cc.PLUG_TAIL_L,
                      "drop_y": round(env["drop_y"], 4), "drop_ok": env["drop_ok"],
                      "magnets": [[round(v, 4) for v in m] for m in env["magnets"]]}}
    hb, rl = env["housing"], env["relief"]
    plug_row = (f"housing {cc.PLUG_BODY[0]:g} x {cc.PLUG_BODY[1]:g} x {cc.PLUG_BODY[2]:g} mm"
                + (f" + relief {rl[1] - rl[0]:g} x {cc.PLUG_RELIEF_L:g} x {cc.PLUG_RELIEF_H:g} mm" if rl else "")
                + f", {cc.PLUG_EXIT} exit; bottom z {min(hb[4], rl[4] if rl else hb[4]):.2f} over "
                + (f"the bay floor {lay0.bay_floor:.2f}" if lay0.bay is not None else f"the rim {cc.REST_HEIGHT:.2f}"))
    dims = []
    if info.get("body"):
        b = info["body"]
        cl = info.get("clips") or {}
        dims.append([f"Dock ({conn['label']})", f"{b['w']:g} x {b['d']:g} x {b['h']:g} mm on the plate, "
                                               f"connector axis {cc.DOCK_CONN_Z:g} above it, "
                                               f"{info.get('clearance_to_oled_cover_y', 0):.1f} mm in front of the "
                                               f"OLED cover"])
        if cl:
            _, cap = CN.clip_capacity(cc, info)
            dims.append(["Clips", f"{cl['count']} blades ({'/'.join(cl['walls'])} walls), {cl['catch_deg']:g}° catch, "
                                  f"~{cap:.1f} N release each ({cc.CLIP_E_MPA / 1000:g} GPa, mu {cc.CLIP_MU:g})"])
    dims.append(["Plug", plug_row])
    if ctype == "pogo5":
        dims.append(["Connector", f"5-pin magnetic pogo (MG005 {cc.DOCK_CONN_W:g} x {cc.DOCK_CONN_H:g} x "
                                  f"{cc.DOCK_CONN_D:g} mm), press fit with {cc.DOCK_CONN_RIB_H:g} mm crush ribs"])
        notes = ["Magnetic: the rest can be slid away, the plug lets go at a few newtons.",
                 "Press the keyboard half into the dock pocket (pin 1 = SDA at the marked -X end).",
                 "The plug's two magnets sit closer to the pad than TP_METAL_KEEPOUT: check the cursor "
                 "for drift with the plug docked (the IQS550 recalibrates at power-up)."]
    else:
        dims.append(["Connector", f"JST SM04B-SRSS-TB {cc.DOCK_JST_W:g} x {cc.DOCK_JST_H:g} x {cc.DOCK_JST_D:g} mm, "
                                  f"Qwiic / STEMMA QT pinout"])
        notes = ["Glue the bare JST header into the dock pocket, its open face flush with the dock face.",
                 "Plug a Qwiic / STEMMA QT cable straight in."]
    return {
        "dock": {"available": conn["dock"] is not None, "connector_face_center": [round(float(v), 4) for v in face],
                 "place_matrix": C.mat4_to_list(T_place), "info": _jsonable(info)},
        "cable": cable,
        "connector": {"type": ctype, "pinout": CN.pinout(cc, ctype), "pins": CN.pins(cc, ctype)},
        "hardware": CN.hardware_plug(cc, ctype, env, face, info),
        "dims": dims, "notes": notes,
    }, routes


def _usbc_variant(cfg, conn, plans, vids, parts):
    cc, cid, P = conn["cfg"], conn["id"], conn["P"]
    T_place = conn["T_place"]
    T = T_place[:3, 3]
    info = conn["info"]
    face = T + np.array([0.0, P.y_front, P.conn_z])
    routes = {vid: usbc.cable_route(cc, plans[vid][0], P, T) for vid in vids}
    env = routes[vids[0]]["envelope"]
    if not env["drop_ok"]:
        rest.log(f"WARNING: usbc grip wires drop at y {env['drop_y']:.2f}, outside the riser "
                 f"{env['drop_range'][0]:.2f}..{env['drop_range'][1]:.2f} (verify fails)")
    lay0 = plans[vids[0]][0]
    gl = conn.get("grip_local")
    if gl:
        lo = np.minimum(gl["top"].bounds[0], gl["bottom"].bounds[0]) + T
        hi = np.maximum(gl["top"].bounds[1], gl["bottom"].bounds[1]) + T
    else:
        lo = T + np.array([-P.gw / 2, P.y_g0, P.z_gb])
        hi = T + np.array([P.gw / 2, P.y_nf, P.z_gt])
    housing = [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]]
    ret = info["retention"]
    metal = usbc.metal_distance(cc, lay0, P, T)
    if ret["margin"] < cc.USBC_RETENTION_MIN:
        rest.log(f"WARNING: usbc dock retention margin {ret['margin']:.2f} < {cc.USBC_RETENTION_MIN:g} (verify fails)")
    if not P.diode_fits:
        rest.log("NOTE: usbc Schottky does not fit the retainer cradle - put it inline at the 3V3 tap")
    if housing[2] < lay0.open_y1 + cc.USBC_GRIP_POCKET_CLEAR:
        rest.log(f"WARNING: usbc grip rear at y {housing[2]:.2f} reaches over the trackpad pocket "
                 f"(opening at {lay0.open_y1:.2f}; verify fails)")
    if not P.pegs:
        rest.log(f"NOTE: usbc grip too short for its alignment pegs ({P.peg_wall:.2f} mm wall to the screw "
                 f"< USBC_GRIP_PEG_WALL) - built without them; the push rib keys the halves")
    floats = None
    rest_part = parts.get(f"rest-{vids[0]}")
    if gl and rest_part is not None:       # measured like verify (min gap mesh <-> mesh)
        floats = usbc.grip_float([gl["top"], gl["bottom"]], rest_part["mesh"], T, cc.USBC_WITHDRAW)
    dims, notes = usbc.dims_notes(cc, P, ret, metal, floats)
    info = dict(info)
    info["metal_distance"] = metal
    if floats:
        info["grip"] = dict(info["grip"], float_mated=floats["mated"], float_withdrawn=floats["withdrawn"])
    cable = {"points": routes[vids[0]]["centerline"], "diameter": cc.CABLE_D, "pigtail_len": cc.CABLE_PIGTAIL_LEN,
             "wire_d": cc.CABLE_WIRE_D,
             "per_variant": {vid: {"centerline": r["centerline"], "sleeve": r["sleeve"], "wires": r["wires"],
                                   "sleeve_len": r["sleeve_len"], "slack": r["slack"]}
                             for vid, r in routes.items()},
             "plug": {"housing": [round(float(v), 4) for v in housing], "relief": None, "exit": "down",
                      "tail_l": 0.0, "drop_y": round(env["drop_y"], 4), "drop_ok": env["drop_ok"],
                      "magnets": [], "grip": _jsonable(info["grip"])}}
    return {
        "dock": {"available": conn["dock"] is not None, "connector_face_center": [round(float(v), 4) for v in face],
                 "place_matrix": C.mat4_to_list(T_place), "info": _jsonable(info)},
        "cable": cable,
        "connector": {"type": "usbc", "pinout": CN.pinout(cc, "usbc"), "pins": CN.pins(cc, "usbc")},
        "hardware": usbc.hardware(cc, P, T),
        "dims": dims, "notes": notes,
    }, routes


def write_manifest(cfg, parts, plans, conns, path):
    vids = list(cfg.VARIANTS)
    lay0, surf0 = plans[vids[0]]
    D, H = cfg.REST_DEPTH, cfg.REST_HEIGHT

    variants_c, routes_c = {}, {}
    for cid, conn in conns.items():
        if conn["type"] == "usbc":
            variants_c[cid], routes_c[cid] = _usbc_variant(cfg, conn, plans, vids, parts)
        else:
            variants_c[cid], routes_c[cid] = _plug_variant(cfg, conn, plans, vids)
    first = next(iter(conns))

    per_variant = {}
    for vid in vids:
        lay, _ = plans[vid]
        pv = {"pcb_top_z": round(lay.pcb_top_z, 4), "adhesive_top_z": round(lay.adhesive_top_z, 4),
              "ledge_z": round(lay.ledge_z, 4), "pocket_depth": round(lay.pocket_depth, 4),
              "cavity_z": round(lay.cavity_z, 4), "well_z": round(lay.well_z, 4),
              "glass_t": cfg.VARIANTS[vid]}
        if lay.glass_top_z is not None:
            pv["glass_top_z"] = round(lay.glass_top_z, 4)
        per_variant[vid] = pv

    stats, masses = {}, {}
    for pid, p in parts.items():
        stats[pid] = C.mesh_stats(p["mesh"], cfg.PLA_DENSITY)
        if p["role"] == "rest":
            masses[pid] = mass_estimates(cfg, p["mesh"])
            stats[pid]["mass_g_estimate"] = masses[pid]
        stats[pid]["stl_bytes"] = 84 + 50 * len(p["mesh"].faces)

    ballast = [{"side": b["side"], "pocket": [round(b["x0"], 3), round(b["y0"], 3), round(b["x1"], 3),
                                             round(b["y1"], 3), 0.0, round(b["depth"], 3)],
                "bar": b["bar"]} for b in lay0.ballast]
    steel_g = sum(b["bar"][0] * b["bar"][1] * b["bar"][2] for b in lay0.ballast) / 1000.0 * cfg.STEEL_DENSITY
    module_g = cfg.TP_WIDTH * cfg.TP_DEPTH * cfg.TP_PCB_T / 1000.0 * cfg.TP_PCB_DENSITY + cfg.TP_PARTS_MASS
    glass_g = cfg.GLASS_WIDTH * cfg.GLASS_DEPTH * cfg.VARIANTS.get("glass", 0.0) / 1000.0 * cfg.GLASS_DENSITY

    dims = []
    add = lambda label, value: dims.append({"label": label, "value": value})  # noqa: E731
    add("Width", f"{cfg.REST_WIDTH:.2f} mm")
    add("Depth", f"{cfg.REST_DEPTH:.2f} mm (+{cfg.REST_KEYBOARD_GAP:.1f} mm gap to the keyboard)")
    add("Max height", f"{H:.2f} mm (trackpad island = keyboard {cfg.KEYBOARD_HEIGHT:.2f} mm)")
    if cfg.REST_PROFILE:
        add("Top profile", "custom spline: " + ", ".join(f"{s:g}->{z:g}" for s, z in cfg.REST_PROFILE))
    else:
        add("Top profile", f"back {cfg.REST_BACK_HEIGHT:.2f} -> peak {H:.2f} at {cfg.REST_PEAK_FROM_BACK:.0f} mm "
                           f"-> front {cfg.REST_FRONT_HEIGHT:.2f} mm (convex, C1)")
    nose_v = float(surf0.edge_b[np.argmax(surf0.outline.wts[:, 2])])
    add("Edge rounds", f"back R{cfg.REST_BACK_EDGE_R:g}, ends R{cfg.REST_END_EDGE_R:g}, "
                       f"front nose {cfg.REST_FRONT_NOSE_R:g} x {nose_v:.1f} mm")
    add("Plan corners", f"front R{cfg.REST_PLAN_FRONT_CORNER_R:g}, back R{cfg.REST_PLAN_BACK_CORNER_R:g}, "
                        f"ends bulge {cfg.REST_END_BULGE:g} mm; bottom chamfer {cfg.REST_BOTTOM_CHAMFER:g} mm")
    add("Trackpad pocket", f"{lay0.open_w:.2f} x {lay0.open_d:.2f} mm, R{lay0.open_r:.2f}, centre "
                           f"({lay0.tp_cx:.2f}, {lay0.tp_cy:.2f}), {cfg.TP_BACK_MARGIN:g} mm from the back")
    gaps = {}
    for vid in vids:
        gaps.update(plans[vid][0].corner_gaps)
    add("Pocket corners", f"R{lay0.open_r:g} vs module R{cfg.TP_CORNER_R:g}"
                          + (f" / glass R{cfg.GLASS_CORNER_R:g}" if "glass" in gaps else "")
                          + ": corner gap " + " / ".join(f"{v:.2f}" for v in gaps.values())
                          + f" mm; rim bevel {cfg.POCKET_RIM_CHAMFER:g} x {cfg.POCKET_RIM_CHAMFER_H:g} mm "
                            f"(wall {cfg.TP_SURFACE_RECESS - cfg.POCKET_RIM_CHAMFER_H:.2f} above the surface)")
    for vid in vids:
        lay, _ = plans[vid]
        top = (f"glass top {lay.glass_top_z:.2f}" if lay.glass_top_z is not None
               else f"PCB top {lay.pcb_top_z:.2f} / liner {lay.adhesive_top_z:.2f}")
        add(f"Pocket depth ({vid})", f"{lay.pocket_depth:.2f} mm -> ledge z {lay.ledge_z:.2f}, {top} mm "
                                     f"({cfg.TP_SURFACE_RECESS:g} below the rim)")
    add("Pocket steps", f"ledge >= {cfg.POCKET_LEDGE:g} mm, relief {cfg.POCKET_CAVITY_DEPTH:g} mm, "
                        f"solder well {cfg.POCKET_WELL_DEPTH:g} mm, {len(cfg.PUSH_HOLE_POS)} push holes "
                        f"D{cfg.PUSH_HOLE_D:g}")
    add("Island", f"flat {cfg.TP_BEZEL:g} mm around the pocket, {cfg.TP_BLEND:g} mm smoothstep blend")
    add("Cable", f"tunnel {cfg.CABLE_CHANNEL_W:g} x {cfg.CABLE_TUNNEL_H:g} mm (S-bend strain relief), notch "
                 f"{cfg.CABLE_NOTCH_W:g} x {cfg.CABLE_NOTCH_DEPTH:g} x {cfg.CABLE_NOTCH_LEN:g} mm, riser "
                 f"{cfg.CABLE_NOTCH_LEN - cfg.CABLE_RISER_BACK_WALL:g} mm long to z {lay0.riser_top:.2f}, "
                 f"pigtail {cfg.CABLE_PIGTAIL_LEN} mm, D{cfg.CABLE_D:g} (last {cfg.CABLE_PLUG_LOOSE_LEN:g} mm "
                 f"unsleeved)")
    if lay0.bay is not None:
        add("Plug bay", f"{cfg.PLUG_BAY_W:g} x {cfg.PLUG_BAY_L:g} x {cfg.PLUG_BAY_DEPTH:g} mm in the back-top "
                        f"edge at x {lay0.notch_x:.2f}, R{cfg.PLUG_BAY_R:g} corners, {cfg.PLUG_BAY_CHAMFER:g} mm chamfer")
    if ballast:
        add("Ballast", " + ".join(f"{b['bar'][0]:g} x {b['bar'][1]:g} x {b['bar'][2]:g}" for b in ballast)
            + f" mm steel (+{steel_g:.0f} g), >= {cfg.BALLAST_MIN_DIST_FROM_TP:g} mm from the pad")
    else:
        add("Ballast", "none")
    if cfg.KEYBOARD_BUMPER_H:
        bh = (f"use {cfg.KEYBOARD_BUMPER_H + cfg.BUMPER_RECESS:g} mm tall ones (keyboard's "
              f"{cfg.KEYBOARD_BUMPER_H:g} + {cfg.BUMPER_RECESS:g})")
    else:
        bh = f"use bumpers {cfg.BUMPER_RECESS:g} mm taller than the keyboard's"
    add("Bumpers", f"{len(lay0.bumpers)} x D{cfg.BUMPER_D:g} mm in {cfg.BUMPER_RECESS:g} mm recesses: {bh}")
    if cfg.ENGRAVE_TEXT:
        add("Engraving", f"'{cfg.ENGRAVE_TEXT}' on the {cfg.ENGRAVE_FACE}"
                         f"{' (mirrored)' if cfg.ENGRAVE_FACE == 'bottom' else ''}, {cfg.ENGRAVE_DEPTH:g} mm deep, "
                         f"cap height {cfg.ENGRAVE_HEIGHT:g} mm")
    pid0 = f"rest-{vids[0]}"
    m0 = masses.get(pid0, {})
    if m0:
        add("Mass (PLA)", f"{m0['15%']:.0f} g @15% / {m0['25%']:.0f} g @25% / {m0['100%']:.0f} g solid "
                          f"({vids[0]}, approx.)")
        add("Total on the desk", f"~{m0['25%'] + steel_g + module_g + glass_g:.0f} g @25% incl. steel, "
                                 f"trackpad{' and glass' if glass_g else ''}")

    kb_y0 = D + cfg.REST_KEYBOARD_GAP
    v0 = variants_c[first]
    manifest = {
        "name": "ithalat", "units": "mm",
        "frame": "origin rest front-left-bottom; +X right; +Y toward keyboard; +Z up",
        "config": {n: _jsonable(getattr(cfg, n)) for n in config_names()},
        "variants": [{"id": v, "label": cfg.VARIANT_LABELS.get(v, v), "glass_t": cfg.VARIANTS[v]} for v in vids],
        "connectors": [{"id": c["id"], "type": c["type"], "label": c["label"]} for c in conns.values()],
        "parts": [{"id": pid, "variant": p["variant"], "role": p["role"], "connector": p.get("connector"),
                   "moves_with": p.get("moves_with"), "label": p.get("label", pid), "stl": p["stl"],
                   "matrix": C.mat4_to_list(p["matrix"])} for pid, p in parts.items()],
        "trackpad": {
            "center": [round(lay0.tp_cx, 4), round(lay0.tp_cy, 4)],
            "width": cfg.TP_WIDTH, "depth": cfg.TP_DEPTH, "corner_r": cfg.TP_CORNER_R,
            "pcb_t": cfg.TP_PCB_T, "adhesive_t": cfg.TP_ADHESIVE_T, "component_h": cfg.TP_COMPONENT_H,
            "component_box": list(cfg.TP_COMPONENT_BOX), "connector_edge": cfg.TP_CONNECTOR_EDGE,
            "pads_box": list(cfg.TP_PADS_BOX), "zif_box": list(cfg.TP_ZIF_BOX), "pad_names": cfg.TP_PAD_NAMES,
            "pads_center": [round(v, 3) for v in lay0.pads_c],
            "opening": {"w": lay0.open_w, "d": lay0.open_d, "r": lay0.open_r},
            "glass": {"width": cfg.GLASS_WIDTH, "depth": cfg.GLASS_DEPTH, "corner_r": cfg.GLASS_CORNER_R},
            "per_variant": per_variant,
        },
        "keyboard": {
            "origin": [round(cfg.KB_X0, 4), round(kb_y0, 4), 0.0],
            "width": cfg.KEYBOARD_WIDTH, "depth": cfg.KEYBOARD_DEPTH, "height": cfg.KEYBOARD_HEIGHT,
            "corner_r": cfg.KEYBOARD_CORNER_R,
            "layers": [{"name": n, "t": t, "material": m} for n, t, m in cfg.KEYBOARD_LAYERS],
            "keys": keyboard_keys(cfg),
            "oled_cover": {"x0": cfg.OLED_COVER[0], "y0": cfg.OLED_COVER[1], "x1": cfg.OLED_COVER[2],
                           "y1": cfg.OLED_COVER[3], "top_z": cfg.OLED_COVER_TOP_Z},
            "pico": {"cx": cfg.PICO_CENTER[0], "cy": cfg.PICO_CENTER[1], "w": cfg.PICO_SIZE[0], "l": cfg.PICO_SIZE[1]},
            "keycap_top_z": cfg.KEYCAP_TOP_Z,
        },
        # legacy single-connector keys = the first (default) connector variant
        "dock": v0["dock"],
        "cable": v0["cable"],
        "connector": v0["connector"],
        "connector_variants": _jsonable(variants_c),
        "ballast": {"enabled": bool(ballast), "pockets": ballast, "steel_g": round(steel_g, 1)},
        "bumpers": {"d": cfg.BUMPER_D, "recess": cfg.BUMPER_RECESS,
                    "positions": [[round(x, 3), round(y, 3)] for x, y in lay0.bumpers]},
        "engraving": {"text": cfg.ENGRAVE_TEXT, "face": cfg.ENGRAVE_FACE,
                      "center": [round(float(v), 3) for v in lay0.engrave["center"]],
                      "size": [round(float(v), 3) for v in lay0.engrave["size"]]},
        "stats": stats,
        "masses": {"rest_pla_g": masses, "steel_g": round(steel_g, 1), "trackpad_g": round(module_g, 1),
                   "glass_g": round(glass_g, 1)},
        "dimensions": dims,
        "log": list(rest.LOG),
    }
    manifest = _jsonable(manifest)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def remove_stale_stls(parts):
    keep = {os.path.normpath(os.path.join(HERE, p["stl"])) for p in parts.values()}
    for pat in CONNECTOR_STL_GLOBS:
        for f in glob.glob(os.path.join(STL_DIR, pat)):
            if os.path.normpath(f) not in keep:
                os.remove(f)
                print(f"  removed stale {os.path.relpath(f, HERE)}")


def main(argv=None):
    cfg, args, extra = config_from_argv(argv, description=__doc__.split("\n")[1])
    if extra:
        raise SystemExit(f"unknown arguments: {' '.join(extra)}")
    if cfg._overrides:
        print("overrides: " + ", ".join(f"{k}={v!r}" for k, v in cfg._overrides.items()))
    print("connectors: " + ", ".join(f"{CN.cid(cfg, c)} ({c})" for c in cfg.CONNECTORS))
    t0 = time.time()
    try:
        parts, plans, conns = build_all(cfg)
    except ValueError as e:          # config that cannot produce a valid rest / dock
        raise SystemExit(f"config error: {e}")
    os.makedirs(STL_DIR, exist_ok=True)
    print()
    for pid, p in parts.items():
        out = os.path.join(HERE, p["stl"])
        p["mesh"].export(out)
        b = p["mesh"].bounds
        ext = b[1] - b[0]
        mb = os.path.getsize(out) / 1e6
        print(f"  {p['stl']:34s} {ext[0]:7.2f} x {ext[1]:6.2f} x {ext[2]:6.2f} mm  "
              f"bbox [{b[0][0]:.2f},{b[0][1]:.2f},{b[0][2]:.2f}]..[{b[1][0]:.2f},{b[1][1]:.2f},{b[1][2]:.2f}]  "
              f"{p['mesh'].volume / 1000:7.2f} cm3  {len(p['mesh'].faces):7d} tris  {mb:5.2f} MB")
        if p["role"] == "rest" and mb > cfg.STL_MAX_MB:
            print(f"WARNING: {p['stl']} is {mb:.1f} MB (> {cfg.STL_MAX_MB} MB) - raise MESH_EDGE_LEN")
    remove_stale_stls(parts)
    man = write_manifest(cfg, parts, plans, conns, os.path.join(BUILD_DIR, "manifest.json"))
    print("\n  " + "\n  ".join(f"{d['label']:18s} {d['value']}" for d in man["dimensions"]))
    for c in man["connectors"]:
        print(f"\n  [{c['label']}]")
        for label, text in man["connector_variants"][c["id"]]["dims"]:
            print(f"  {label:18s} {text}")
    for line in man["log"]:
        if line.startswith(("WARNING", "NOTE")):
            print(f"  {line}")
    print(f"\n  build/manifest.json written; {len(parts)} parts in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
