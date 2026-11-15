"""Connector variants: ids, per-connector config copies, pin tables and the
non-printed hardware envelopes of the pogo / JST connectors (assembly frame).

CONNECTORS (config.py) lists the variants to generate. Every variant shares
the rest; each has its own dock (and the USB-C variant its grip + retainer,
see geometry/usbc.py).
"""

import copy

import numpy as np

from geometry import common as C

# Pico / TPS65 side of every signal (Yakamoz netlist: OLED bus on RP2040 I2C1)
SIGNAL_REF = {
    "SDA": {"pico": "GP2 · pin 4", "tps65": "SDA (J1-6)", "note": "shared with the OLED"},
    "SCL": {"pico": "GP3 · pin 5", "tps65": "SCL (J1-5)", "note": "shared with the OLED"},
    "3V3": {"pico": "3V3(OUT) · pin 36", "tps65": "VDDHI (J1-4)", "note": "never 5 V"},
    "GND": {"pico": "GND · pin 38", "tps65": "GND (J1-3)", "note": "any Pico GND pin"},
    "RDY": {"pico": "GP15 · pin 20", "tps65": "RDY (J1-1)", "note": "optional, else NC"},
}


def cid(cfg, ctype):
    return dict(cfg.CONNECTOR_IDS).get(ctype, ctype)


def label(cfg, ctype):
    return dict(cfg.CONNECTOR_LABELS).get(ctype, ctype)


def for_connector(cfg, ctype):
    """Copy of cfg for one connector: DOCK_CONN_TYPE = ctype and the values
    derived from it (PLUG_BODY) recomputed unless overridden explicitly."""
    c = copy.copy(cfg)
    c.DOCK_CONN_TYPE = ctype
    ov = getattr(cfg, "_overrides", {}) or {}
    if "PLUG_BODY" not in ov:
        c.PLUG_BODY = ((c.DOCK_CONN_W, c.DOCK_CONN_D, c.DOCK_CONN_H) if ctype == "pogo5"
                       else tuple(c.PLUG_BODY_JST))
    return c


def place_matrix(cfg):
    """Dock-local -> assembly (pure translation)."""
    return C.translation(cfg.KB_X0 + cfg.DOCK_CENTER_X,
                         cfg.REST_DEPTH + cfg.REST_KEYBOARD_GAP + cfg.DOCK_SWITCH_CENTER_Y,
                         cfg.KEYBOARD_HEIGHT)


def pins(cfg, ctype):
    """Pin table rows {pin, signal, pico, tps65, note} for the manifest."""
    rows = []
    if ctype == "usbc":
        order = [("G", "GND"), ("V", "3V3"), ("D+", "SDA"), ("D-", "SCL")]
        sig_of = dict(cfg.USBC_SIGNALS)
        d_l, d_d = cfg.USBC_DIODE
        for pad, default in order:
            s = sig_of.get(pad, default)
            ref = dict(SIGNAL_REF.get(s, {"pico": "-", "tps65": "-", "note": ""}))
            if s == "3V3":
                ref["pico"] = "3V3(OUT) · pin 36, via the Schottky"
                ref["note"] = (f"series Schottky at the keyboard end (1N5817 / SS14, anode to the "
                               f"Pico): ~3.0-3.1 V at the pad; never real USB / 5 V")
            elif s == "GND":
                ref["note"] = "USB-C GND mates first"
            else:
                ref["note"] = "USB-C " + pad + ": " + ref["note"]
            rows.append({"pin": pad, "signal": s, **ref})
        rows.append({"pin": "-", "signal": "RDY", "pico": "GP15 · pin 20", "tps65": "RDY (J1-1)",
                     "note": "not connected (the firmware polls); SBU mod optional"})
        return rows
    sig = list(cfg.JST_SH4_PINOUT if ctype == "jst_sh4" else cfg.CONNECTOR_PINOUT)
    for i, s in enumerate(sig):
        ref = SIGNAL_REF.get(str(s).upper(), {"pico": "-", "tps65": "-", "note": "not connected"})
        rows.append({"pin": i + 1, "signal": s, **ref})
    return rows


def pinout(cfg, ctype):
    if ctype == "usbc":
        sig_of = dict(cfg.USBC_SIGNALS)
        return [sig_of.get(p, p) for p in cfg.USBC_M_PADS]
    return list(cfg.JST_SH4_PINOUT if ctype == "jst_sh4" else cfg.CONNECTOR_PINOUT)


def _r(v):
    return [round(float(x), 4) for x in v]


def hardware_plug(cfg, ctype, env, face, info):
    """Non-printed parts of the pogo / JST connector (assembly frame,
    assembled): the keyboard half in the dock pocket and the cable half."""
    fx, fy, fz = (float(v) for v in face)
    body = info.get("connector_body") or [cfg.DOCK_CONN_W, cfg.DOCK_CONN_H, cfg.DOCK_CONN_D]
    cw, ch, cd = (float(v) for v in body)
    hw = []
    name = "MG005 pogo" if ctype == "pogo5" else "JST SM04B-SRSS-TB"
    hw.append({"id": f"{cid(cfg, ctype)}-dock-half", "label": f"{name} keyboard half (in the dock)",
               "shape": "rounded_box" if ctype == "pogo5" else "box", "axis": "y",
               "r": round(ch / 2.0, 4) if ctype == "pogo5" else None,
               "box": _r([fx - cw / 2, fx + cw / 2, fy, fy + cd, fz - ch / 2, fz + ch / 2]),
               "material": "plastic_black", "moves_with": "dock"})
    hb = env["housing"]
    hw.append({"id": f"{cid(cfg, ctype)}-plug", "label": f"{name} cable half",
               "shape": "rounded_box" if ctype == "pogo5" else "box", "axis": "y",
               "r": round((hb[5] - hb[4]) / 2.0, 4) if ctype == "pogo5" else None,
               "box": _r(hb), "material": "plastic_black", "moves_with": "pad"})
    if env.get("relief"):
        hw.append({"id": f"{cid(cfg, ctype)}-relief", "label": "solder tails + heat-shrink / glue",
                   "shape": "box", "box": _r(env["relief"]), "material": "plastic_black",
                   "moves_with": "pad"})
    mr = min(1.6, ch / 2.0 - 0.3)
    for k, (mx, y0, y1, mz) in enumerate(env.get("magnets") or []):
        hw.append({"id": f"{cid(cfg, ctype)}-plug-magnet-{k + 1}", "label": "NdFeB magnet (cable half)",
                   "shape": "cylinder_y", "r": round(mr, 4),
                   "box": _r([mx - mr, mx + mr, y0, y1, mz - mr, mz + mr]),
                   "material": "magnet", "moves_with": "pad"})
        hw.append({"id": f"{cid(cfg, ctype)}-dock-magnet-{k + 1}", "label": "NdFeB magnet (keyboard half)",
                   "shape": "cylinder_y", "r": round(mr, 4),
                   "box": _r([mx - mr, mx + mr, fy, fy + cd, mz - mr, mz + mr]),
                   "material": "magnet", "moves_with": "dock"})
    return hw


def clip_capacity(cfg, info, catch_deg=None):
    """Release force of one snap blade (N): cantilever force at the lip
    deflection P = 3 E I d / L^3, camming over the catch face at alpha from
    horizontal with friction mu: F = P (1 + mu tan a) / (tan a - mu)
    (self-locking - infinite - when tan a <= mu)."""
    cl = info["clips"]
    E, mu = float(cfg.CLIP_E_MPA), float(cfg.CLIP_MU)
    t, L, d = float(cl["thickness"]), float(cl["free_length"]), float(cl["deflection"])
    w = float(cl.get("width_back") or cl["width_inner"])
    a = float(cl["catch_deg"] if catch_deg is None else catch_deg)
    I = w * t ** 3 / 12.0
    P = 3.0 * E * I * d / L ** 3
    ta = np.tan(np.radians(a))
    if ta <= mu + 1e-9:
        return P, float("inf")
    return P, P * (1.0 + mu * ta) / (ta - mu)
