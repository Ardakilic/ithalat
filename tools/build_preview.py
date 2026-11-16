#!/usr/bin/env python3
"""Build the ithalat 3D preview from build/manifest.json and the STLs it lists.

Writes two outputs from one template (preview/template.html):

  preview/index.html   complete standalone page (local viewing, GitHub Pages),
                       with a "Source on GitHub" link in the header and a
                       "Download STLs" block that lists the files the picked
                       variant + connector need (one link each, plus "Download
                       all" as a .zip built in the browser with JSZip from
                       cdnjs).  Every STL link points at the committed file on
                       the main branch (REPO_URL/raw/main/stl/<file>); the page
                       script switches the links to the site's own stl/<file>
                       when it is served from *.github.io (the Pages site, also
                       forks), where `make site` puts the STLs next to it
  build/artifact.html  the same app as an HTML *fragment* for publishing as a
                       claude.ai Artifact: no <!doctype>/<html>/<head>/<body>,
                       starts with <title> + the viewport-fit meta, then
                       <style>, then content; STL paths and sizes are listed as
                       text because downloads are blocked there (a note points
                       to the stl/ folder of the GitHub repository).

Connector variants: the manifest lists "connectors" (e.g. magnetic pogo and
USB-C) and per-connector data in "connector_variants" (dock, cable, pinout,
non-printed hardware, dimension rows, notes).  The page gets a Connector
switch next to the glass/bare Variant switch; every part, table row and note
that belongs to one connector carries data-connector="<id>".  An older
single-connector manifest (top-level "dock"/"cable"/"connector" only) still
works: it becomes a one-entry connector list.

Meshes are embedded compactly: vertices are welded on a 16-bit grid spanning
each part's bounding box (~0.004 mm steps), re-ordered by first use, stored as
per-axis uint16 deltas split into low/high byte planes; triangle indices are
"high-watermark" codes (0 = next new vertex) written as LEB128 varints.  Both
streams are gzipped and base64'd, then decoded in the browser with
DecompressionStream('gzip').  three.js r170 loads from jsDelivr via an import
map (exact version pin).

Usage: `make preview` from the repository root, or inside the build image:
  docker run --rm -v "$PWD":/app -w /app ithalat-build python3 tools/build_preview.py
Options let tests point at other inputs/outputs:
  --manifest build/manifest.json  --root .  --template preview/template.html
  --out-html preview/index.html   --out-artifact build/artifact.html

Only the standard library and numpy are used.
"""
import argparse
import base64
import gzip
import html
import json
import os
import posixpath
import re
import struct
import sys
import urllib.parse

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)

# Public home of the project; the standalone page links its STLs to the files
# committed on the main branch there.
REPO_URL = "https://github.com/Ardakilic/ithalat"
RAW_URL = REPO_URL + "/raw/main/"
# the same files from GitHub's CORS-enabled raw host: "Download all" fetches them from
# here when the page is not on *.github.io (local copy, other hosts)
FETCH_URL = "https://raw.githubusercontent.com/Ardakilic/ithalat/main/"
STL_FOLDER_URL = REPO_URL + "/tree/main/stl"
# "Download all" zips the files in the browser; loaded only on click (exact pin + SRI)
JSZIP_URL = "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"
JSZIP_SRI = "sha512-XMVd28F1oH/O71fzwBnV7HucLxVwtxf26XV8P4wPk26EDxuGZ91N8bsOttmnomcCD3CS5ZMRL50H0GgOHvegtg=="

TARGET_MB = 8.0     # aim for this total page size
HARD_CAP_MB = 15.0  # refuse to write a page bigger than this

STL_DTYPE = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])

# Connector pin -> Pico -> TPS65 mapping, keyed by link signal name.  Facts
# from the Yakamoz KiCad netlist (OLED bus on RP2040 I2C1, GP2/GP3, 4.7k
# pull-ups R1/R2 on the main PCB) and the TPS65 datasheet (J1 / solder pads).
SIGNAL_MAP = {
    "SDA": {"pico": "GP2 · pin 4", "tps65": "SDA (J1-6)", "note": "shared with the OLED"},
    "SCL": {"pico": "GP3 · pin 5", "tps65": "SCL (J1-5)", "note": "shared with the OLED"},
    "3V3": {"pico": "3V3(OUT) · pin 36", "tps65": "VDDHI (J1-4)", "note": "never 5 V"},
    "GND": {"pico": "GND · pin 38", "tps65": "GND (J1-3)", "note": "any Pico GND pin"},
    "RDY": {"pico": "GP15 · pin 20", "tps65": "RDY (J1-1)", "note": "optional, else NC"},
    "NC": {"pico": "-", "tps65": "-", "note": "not connected"},
}

# connector type -> (id used in file names / the manifest, short label, pinout title)
CONNECTOR_INFO = {
    "pogo5": ("pogo", "Magnetic pogo", "5-pin magnetic pogo, 2.54 mm"),
    "usbc": ("usbc", "USB-C", "USB-C breakout pair, four pads (G, V, D+, D-)"),
    "jst_sh4": ("jst", "JST-SH 4-pin", "JST-SH 4-pin (Qwiic)"),
}
# pinout footnote per connector type
PINOUT_NOTE = {
    "pogo5": "Pin order is the same on both halves; GND is the centre pin.",
    "usbc": "Remove the female board's two 5.1k Rd resistors (CC to GND) and any CC resistor on the "
            "male. The grip fits the well one way up only; most female boards tie both D+ and both D- "
            "contacts together, so check both plug orientations with the bare male board before you "
            "close the grip. Never plug either half into a real USB port or charger.",
}
# what the download list's buy note adds per connector type (README "Screws and epoxy")
BUY_NOTE = {
    "pogo5": "Pogo needs no screws.",
    "usbc": "USB-C also needs 4 × M2x4 self-tapping screws and 2-part epoxy.",
}

# hardware material -> CSS token (preview/template.html :root) for the parts-list swatch
MATERIAL_TOKEN = {
    "pcb_green": "--mat-pcb-green", "pcb_blue": "--mat-pcb-blue", "metal": "--mat-metal",
    "plastic_black": "--mat-plastic", "magnet": "--mat-magnet", "diode": "--mat-diode",
}
HW_SHAPES = ("box", "rounded_box", "cylinder_x", "cylinder_y", "cylinder_z")


# ----------------------------------------------------------------- STL in --
def read_stl(path):
    """Return an (n, 3, 3) float64 array of triangle corners (binary or ASCII)."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) >= 84:
        n = struct.unpack_from("<I", data, 80)[0]
        if 84 + 50 * n == len(data):
            rec = np.frombuffer(data, dtype=STL_DTYPE, count=n, offset=84)
            return rec["v"].astype(np.float64)
    text = data.decode("ascii", "replace")
    nums = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text)
    if not nums or len(nums) % 3:
        raise ValueError(f"{path}: not a readable STL")
    return np.array(nums, dtype=np.float64).reshape(-1, 3, 3)


def mesh_stats(tris, density):
    """Triangles, bbox, volume (divergence theorem) and solid mass."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    vol = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
    pts = tris.reshape(-1, 3)
    return {
        "triangles": int(len(tris)),
        "bbox": [pts.min(0).round(3).tolist(), pts.max(0).round(3).tolist()],
        "volume_cm3": round(abs(vol) / 1000.0, 2),
        "mass_g_solid_pla": round(abs(vol) / 1000.0 * density, 1),
    }


# ------------------------------------------------------------- encoding --
def _varint(values):
    """LEB128-encode a non-negative int array (vectorised)."""
    a = values.astype(np.uint64)
    nb = np.ones(len(a), np.int64)
    for k in (7, 14, 21, 28):
        nb += a >= (1 << k)
    buf = np.zeros(int(nb.sum()), np.uint8)
    starts = np.concatenate([[0], np.cumsum(nb)[:-1]])
    for b in range(5):
        m = nb > b
        if not m.any():
            break
        byte = ((a[m] >> np.uint64(7 * b)) & np.uint64(0x7F)).astype(np.uint8)
        cont = (nb[m] > b + 1).astype(np.uint8) << 7
        buf[starts[m] + b] = byte | cont
    return buf.tobytes()


def weld(tris, cell=None):
    """Weld corners onto a 16-bit grid over the bbox (optionally coarser:
    `cell` mm = vertex clustering, used only as a last-resort decimation).
    Returns (lo, step, qverts uint16 (n,3) in first-use order, faces (m,3))."""
    v = tris.reshape(-1, 3)
    lo = v.min(0)
    ext = np.maximum(v.max(0) - lo, 1e-6)
    step = ext / 65535.0
    q = np.rint((v - lo) / step).astype(np.int64)
    if cell:
        k = np.maximum(np.rint(cell / step).astype(np.int64), 1)
        q = np.minimum((q // k) * k + k // 2, 65535)
    key = q[:, 0] | (q[:, 1] << 16) | (q[:, 2] << 32)
    uniq, inv = np.unique(key, return_inverse=True)
    f = inv.reshape(-1, 3)
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    if cell:  # clustering can fold two triangles onto each other
        srt = np.sort(f, axis=1)
        _, keep = np.unique(srt, axis=0, return_index=True)
        f = f[np.sort(keep)]
    flat = f.ravel()
    used, first = np.unique(flat, return_index=True)
    order = used[np.argsort(first)]
    remap = np.full(len(uniq), -1, np.int64)
    remap[order] = np.arange(len(order))
    faces = remap[f]
    u = uniq[order]
    qv = np.stack([u & 0xFFFF, (u >> 16) & 0xFFFF, (u >> 32) & 0xFFFF], 1)
    return lo, step, qv, faces


def encode(lo, step, qv, faces):
    """Pack welded mesh -> (meta dict, base64 str)."""
    n = len(qv)
    d = np.diff(qv, axis=0, prepend=np.zeros((1, 3), np.int64)) & 0xFFFF
    planes = d.T.astype("<u2").copy().view(np.uint8).reshape(3, n, 2)
    pos = np.concatenate([planes[:, :, 0].ravel(), planes[:, :, 1].ravel()]).tobytes()
    flat = faces.ravel()
    hw = np.concatenate([[0], np.maximum.accumulate(flat)[:-1] + 1])
    code = hw - flat
    assert (code >= 0).all(), "vertex order is not first-use"
    idx = _varint(code)
    blob = gzip.compress(pos + idx, 9, mtime=0)
    meta = {"nv": int(n), "nt": int(len(faces)), "lo": [round(float(x), 6) for x in lo],
            "step": [float(x) for x in step], "pos_bytes": len(pos), "idx_bytes": len(idx),
            "gz_bytes": len(blob)}
    return meta, base64.b64encode(blob).decode("ascii")


# ----------------------------------------------------------- formatting --
def esc(s):
    """HTML-escape s; an ASCII "->" becomes a real arrow (the mono font draws "->" as a
    ligature that splits when a cell wraps at the hyphen)."""
    return html.escape(str(s).replace("->", "\u2192"), quote=True)


def fmt_bytes(n):
    if n >= 1e6:
        return f"{n / 1e6:.1f} MB"
    if n >= 1e3:
        return f"{n / 1e3:.0f} kB"
    return f"{n} B"


def fmt_int(n):
    return f"{int(n):,}".replace(",", " ")  # narrow no-break space


def safe_id(s):
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(s))


def bbox_txt(bb):
    if not bb:
        return ""
    lo, hi = bb
    return " × ".join(f"{hi[i] - lo[i]:.1f}" for i in range(3)) + " mm"


# ------------------------------------------------------------ connectors --
def pinout_rows(conn, cfg):
    """Pinout table rows from one connector object ({"type", "pins"|"pinout"})."""
    conn = conn or {}
    pins = conn.get("pins")
    if isinstance(pins, list) and pins and isinstance(pins[0], dict):
        rows = []
        for i, p in enumerate(pins):
            sig = str(p.get("signal", "NC"))
            ref = SIGNAL_MAP.get(sig.upper(), SIGNAL_MAP["NC"])
            rows.append({"pin": p.get("pin", i + 1), "signal": sig,
                         "pico": p.get("pico", ref["pico"]), "tps65": p.get("tps65", ref["tps65"]),
                         "note": p.get("note", ref["note"])})
        return rows
    pinout = conn.get("pinout") or cfg.get("CONNECTOR_PINOUT") or ["SDA", "3V3", "GND", "SCL", "RDY"]
    rows = []
    for i, sig in enumerate(pinout):
        ref = SIGNAL_MAP.get(str(sig).upper(), SIGNAL_MAP["NC"])
        rows.append({"pin": i + 1, "signal": sig, **ref})
    return rows


def legacy_hardware(dock, cable, cfg):
    """Non-printed parts to draw for a manifest that has no "hardware" list:
    the pigtail plug from cable.plug (housing, strain relief, magnets), or a
    plain connector box at the dock face."""
    plug = (cable or {}).get("plug") or {}
    out = []
    hb = plug.get("housing")
    if hb and len(hb) >= 6:
        out.append({"id": "plug-housing", "label": "Connector plug, cable half", "shape": "rounded_box",
                    "box": hb[:6], "r": min(hb[5] - hb[4], hb[1] - hb[0]) / 2 - 0.01,
                    "material": "plastic_black", "moves_with": "dock"})
        rl = plug.get("relief")
        if rl and len(rl) >= 6:
            out.append({"id": "plug-relief", "label": "Strain relief (heat-shrink, glue)",
                        "shape": "rounded_box", "box": rl[:6], "r": min(1.4, (rl[5] - rl[4]) / 2 - 0.01),
                        "material": "plastic_black", "moves_with": "dock"})
        md = float(cfg.get("PLUG_MAGNET_D") or 0.7 * (hb[5] - hb[4]))
        for i, m in enumerate(plug.get("magnets") or []):
            if len(m) >= 4:
                x, y0, y1, z = m[:4]
                out.append({"id": f"plug-magnet-{i + 1}", "label": "Plug magnet", "shape": "cylinder_y",
                            "box": [x - md / 2, x + md / 2, y0, y1, z - md / 2, z + md / 2],
                            "material": "magnet", "moves_with": "dock"})
        return out
    face = (dock or {}).get("connector_face_center")
    if face and len(face) >= 3:
        body = ((dock or {}).get("info") or {}).get("connector_body") or []
        cw = body[0] if len(body) > 0 else cfg.get("DOCK_CONN_W", 20.1)
        ch = body[1] if len(body) > 1 else cfg.get("DOCK_CONN_H", 4.2)
        cd = body[2] if len(body) > 2 else cfg.get("DOCK_CONN_D", 4.0)
        out.append({"id": "plug", "label": "Connector plug", "shape": "box",
                    "box": [face[0] - cw / 2, face[0] + cw / 2, face[1] - cd, face[1],
                            face[2] - ch / 2, face[2] + ch / 2],
                    "material": "plastic_black", "moves_with": "dock"})
    return out


def clean_hardware(items):
    out = []
    for i, h in enumerate(items or []):
        if not isinstance(h, dict):
            continue
        b = h.get("box")
        try:
            b = [float(v) for v in b][:6]
        except (TypeError, ValueError):
            continue
        if len(b) < 6 or not (b[1] > b[0] and b[3] > b[2] and b[5] > b[4]):
            continue
        e = {"id": str(h.get("id") or f"hw{i}"), "label": str(h.get("label") or h.get("id") or "part"),
             "shape": h.get("shape") if h.get("shape") in HW_SHAPES else "box", "box": b,
             "material": str(h.get("material") or "plastic_black"),
             "moves_with": "pad" if h.get("moves_with") == "pad" else "dock"}
        for k in ("r", "axis", "band_end", "explode_offset"):
            if h.get(k) is not None:
                e[k] = h[k]
        out.append(e)
    return out


def connectors_of(man, cfg):
    """-> (connectors [{id, type, label, title}], {id: variant dict}).  Falls back to
    the legacy single-connector manifest (top-level dock / cable / connector)."""
    raw = man.get("connectors")
    cvs = man.get("connector_variants") or {}
    conns = []
    if isinstance(raw, list) and raw:
        for c in raw:
            if isinstance(c, str):
                c = {"type": c}
            ctype = c.get("type") or c.get("id")
            info = CONNECTOR_INFO.get(ctype, (ctype, ctype, ctype))
            conns.append({"id": str(c.get("id") or info[0]), "type": ctype,
                          "label": c.get("label") or info[1]})
    else:
        ctype = (man.get("connector") or {}).get("type") or cfg.get("DOCK_CONN_TYPE", "pogo5")
        info = CONNECTOR_INFO.get(ctype, (ctype, ctype, ctype))
        conns.append({"id": info[0], "type": ctype, "label": info[1]})
    variants = {}
    for i, c in enumerate(conns):
        v = cvs.get(c["id"])
        if not isinstance(v, dict):
            v = ({"dock": man.get("dock"), "cable": man.get("cable"), "connector": man.get("connector")}
                 if i == 0 else {})
        dock, cable = v.get("dock") or {}, v.get("cable") or {}
        conn = dict(v.get("connector") or {})
        conn.setdefault("type", c["type"])
        hw = v.get("hardware")
        hw = clean_hardware(hw if isinstance(hw, list) else legacy_hardware(dock, cable, cfg))
        dims = []
        for r in v.get("dims") or []:
            if isinstance(r, dict):
                dims.append((str(r.get("label", "")), str(r.get("value", ""))))
            elif isinstance(r, (list, tuple)) and r:
                dims.append((str(r[0]), str(r[1]) if len(r) > 1 else ""))
        notes = v.get("notes")
        c["title"] = CONNECTOR_INFO.get(conn["type"], (None, None, c["label"]))[2]
        variants[c["id"]] = {
            "dock": dock, "cable": cable,
            "connector": {"type": conn["type"], "pins": pinout_rows(conn, cfg)},
            "hardware": hw, "dims": dims,
            "notes": [str(n) for n in notes] if isinstance(notes, list) else None,
        }
    return conns, variants


def part_label(part, variants, conns):
    if part.get("label"):
        return str(part["label"])
    role = part.get("role")
    var = part.get("variant")
    vlab = next((v.get("label") for v in variants if v.get("id") == var), var)
    clab = next((c["label"] for c in conns if c["id"] == part.get("connector")), None)
    pid = str(part.get("id", ""))
    if role == "rest":
        lab = f"Wrist rest, {vlab.lower()}" if vlab else "Wrist rest"
        return lab + (f" ({clab})" if clab else "")
    if role == "dock":
        return f"Keyboard dock, {clab}" if clab and len(conns) > 1 else "Keyboard dock"
    if role == "grip":
        half = " top half" if "top" in pid else " bottom half" if "bottom" in pid else ""
        return f"{clab or 'Plug'} grip{',' + half if half else ''}"
    if role == "retainer":
        return f"{clab or 'Connector'} board retainer"
    if role == "lock":
        return f"Dock lock{', ' + clab if clab else ''}"
    return pid or "part"


# ------------------------------------------------------------- print notes --
def plug_notes(cable):
    """Pigtail-plug notes derived from cable.plug (used when a connector has no notes)."""
    plug = (cable or {}).get("plug") or {}
    notes = []
    if plug.get("magnets"):
        notes.append("The docked plug's two small magnets sit closer to the pad than the ballast rule "
                     "allows. They are acceptable because the plug only powers the pad while it is docked "
                     "(fixed in place) and the controller calibrates at power-up. If the cursor drifts, "
                     "check it docked.")
    if plug.get("housing"):
        rl = plug.get("relief")
        notes.append("Pigtail plug: keep the soldered tails and their heat-shrink or glue within "
                     + (f"{rl[3] - rl[2]:g} mm behind the housing and {rl[5] - rl[4]:g} mm tall, "
                        if rl else "the housing outline, ")
                     + ("then turn the loose wires straight down into the bay at the back edge."
                        if plug.get("exit") == "down" else "with the cable leaving toward you."))
    return notes


def connector_notes(cv, label):
    po = ((cv.get("dock") or {}).get("info") or {}).get("print_orientation")
    notes = [f"{label} dock: print it {po.rstrip('.')}."] if po else []
    notes += cv["notes"] if cv.get("notes") is not None else plug_notes(cv.get("cable"))
    return notes


def print_notes(cfg, man=None):
    """General (connector-independent) notes; connector notes come from connector_notes()."""
    man = man or {}
    g = cfg.get
    bw, bd, bh = (g("BALLAST_SIZE") or (0.0, 0.0, 0.0))[:3]
    pockets = ((man.get("ballast") or {}).get("pockets") or [])
    if pockets and pockets[0].get("bar"):
        bw, bd, bh = pockets[0]["bar"][:3]
    nbump = len((man.get("bumpers") or {}).get("positions") or []) or None
    head = [
        "Print each rest bottom-down, exactly as it sits on the desk: the pocket opens "
        "upward and the channel and pockets bridge, so no supports are needed.",
        "Every dock and grip STL loads in its print orientation; print it as it loads.",
    ]
    tail = [
        "PLA or PETG. Never use carbon- or metal-filled (conductive) filament: it "
        "detunes the capacitive pad.",
    ]
    if any(isinstance((st or {}).get("mass_g_estimate"), dict)
           for st in (man.get("stats") or {}).values()):
        tail.append("Part masses list the generator's infill estimates and the 100 % solid figure.")
    else:
        tail.append("Masses are for 100 % solid PLA; a print with normal walls and infill weighs less.")
    if g("BALLAST_ENABLED", True) and pockets:
        tail.append(f"Ballast bars ({bw:g} × {bd:g} × {bh:g} mm steel) sit at least "
                    f"{g('BALLAST_MIN_DIST_FROM_TP', 20.0):g} mm from the trackpad. Keep loose steel, "
                    "magnets and coins away from the pad.")
    tail.append(f"Glass variant: the {g('GLASS_T', 1.1):g} mm glass bonds to the module's own "
                "adhesive. Seat the module from the top and never press on the glass edges; "
                f"push it out from below through the Ø{g('PUSH_HOLE_D', 6.0):g} mm hole.")
    rec = g('BUMPER_RECESS', 0.6)
    kbh = g('KEYBOARD_BUMPER_H')
    height = (f"{kbh + rec:g} mm tall (the keyboard's {kbh:g} mm + {rec:g})" if kbh
              else f"{rec:g} mm taller than the keyboard's")
    tail.append(f"Stick {str(nbump) + ' ' if nbump else ''}Ø{g('BUMPER_D', 10.0):g} mm silicone bumpers into the "
                f"{rec:g} mm recesses. Make them {height}, so the rest's top sits level with the switchplate.")
    tail.append("The TPS65 runs on 3.3 V only (VDDHI 1.65–3.6 V). Never feed it 5 V.")
    return head, tail


# ------------------------------------------------------------ panel HTML --
def conn_attr(cid, default, multi):
    """data-connector attribute (+ hidden when it is not the default connector)."""
    if not cid or not multi:
        return ""
    return f' data-connector="{esc(cid)}"' + ("" if cid == default else " hidden")


def html_dimensions(man, conns, cvars):
    rows = man.get("dimensions") or []
    multi = len(conns) > 1
    default = conns[0]["id"] if conns else None
    out = ['<table class="kv" id="dims-table"><tbody>']
    for r in rows:  # every row, no whitelist
        if isinstance(r, dict):
            label, value = r.get("label", ""), r.get("value", "")
        else:
            label, value = (list(r) + ["", ""])[:2]
        # a connector row with the same label replaces this one while that connector is shown
        over = [c["id"] for c in conns if any(l == str(label) for l, _ in cvars[c["id"]]["dims"])]
        attr = ""
        if over and multi:
            attr = f' data-hide-for="{esc(" ".join(over))}"' + (" hidden" if default in over else "")
        elif over:
            continue
        out.append(f"<tr{attr}><th scope=\"row\">{esc(label)}</th><td>{esc(value)}</td></tr>")
    for c in conns:
        for label, value in cvars[c["id"]]["dims"]:
            out.append(f'<tr class="conn-row"{conn_attr(c["id"], default, multi)}><th scope="row">{esc(label)}</th>'
                       f'<td>{esc(value)}</td></tr>')
    if not rows and not any(cvars[c["id"]]["dims"] for c in conns):
        out.append('<tr><td colspan="2">No dimension rows in the manifest.</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def grams(g):
    g = float(g)
    return f"{g:.0f}" if g >= 9.95 else f"{g:.1f}"  # small printed parts keep a decimal


def mass_txt(st):
    """'PLA 266 g solid', plus the manifest's infill estimates when it has them."""
    bits = []
    est = st.get("mass_g_estimate")
    if isinstance(est, dict):
        for k, v in est.items():
            if str(k).rstrip("%") != "100":
                bits.append(f"{grams(v)} g at {str(k).rstrip('%')} % infill")
    bits.append(f'{grams(st.get("mass_g_solid_pla", 0))} g solid')
    return "PLA " + " · ".join(bits)


def html_hardware(conns, cvars):
    """Per connector: the bought (non-printed) parts drawn in the viewer."""
    multi = len(conns) > 1
    default = conns[0]["id"] if conns else None
    out = []
    for c in conns:
        items, seen = [], {}
        for h in cvars[c["id"]]["hardware"]:
            key = h["label"]
            if key in seen:
                items[seen[key]][1] += 1
            else:
                seen[key] = len(items)
                items.append([h, 1])
        if not items:
            continue
        out.append(f'<div class="hw"{conn_attr(c["id"], default, multi)}>'
                   f'<p class="label">Not printed{(" · " + esc(c["label"])) if multi else ""}</p><ul class="hw-list">')
        for h, n in items:
            tokn = MATERIAL_TOKEN.get(h["material"])
            sw = f' style="--chip: var({tokn})"' if tokn else ""
            out.append(f'<li><span class="hw-chip"{sw} aria-hidden="true"></span>'
                       f'<span>{esc(h["label"])}{f" <b>× {n}</b>" if n > 1 else ""}</span></li>')
        out.append("</ul></div>")
    return "".join(out)


def html_parts(parts, mode, conns, cvars):
    multi = len(conns) > 1
    default = conns[0]["id"] if conns else None
    out = ['<ul class="parts" id="parts-list">']
    for p in parts:
        st = p["stats"]
        cls = "part" + (f" v-{p['variant']}" if p.get("variant") else "")
        if mode == "standalone":
            file_html = (f'<a class="file" href="{esc(p["href"])}"{stl_link_attrs(p)} '
                         f'title="Download {esc(p["stl"])}">{esc(p["stl"])}</a>'
                         f' <span class="size">{esc(fmt_bytes(p["file_bytes"]))}</span>')
        else:
            file_html = (f'<code class="file">{esc(p["stl"])}</code>'
                         f' <span class="size">{esc(fmt_bytes(p["file_bytes"]))}</span>')
        dv = f' data-variant="{esc(p["variant"])}"' if p.get("variant") else ""
        out.append(
            f'<li class="{cls}" data-part="{esc(p["id"])}"{dv}{conn_attr(p.get("connector"), default, multi)}>'
            f'<div class="part-head"><span class="part-name">{esc(p["label"])}</span></div>'
            f'<div class="part-file">{file_html}</div>'
            f'<div class="part-meta"><span>{esc(fmt_int(st.get("triangles", 0)))} triangles</span>'
            f'<span>{esc(bbox_txt(st.get("bbox")))}</span>'
            f'<span>{st.get("volume_cm3", 0):.1f} cm³</span></div>'
            f'<div class="part-mass">{esc(mass_txt(st))}</div></li>')
    out.append("</ul>")
    out.append(html_hardware(conns, cvars))
    if mode == "artifact":
        out.append(f'<p class="fine">The STL files are in the <code>stl/</code> folder of the '
                   f'{repo_link(mode, "GitHub repository")}. Download them there; this page can’t '
                   'offer files. Masses are PLA at the configured density.</p>')
    else:
        out.append('<p class="fine"><a href="#h-download">Download STLs</a> above has just the files your '
                   'pick needs; each file name here downloads one STL. Masses are PLA at the configured '
                   'density.</p>')
    return "".join(out)


def files_for(parts, v, c):
    """The STLs one build needs: the rest for variant v (its connector-c copy if the
    rests differ per connector), plus every other part that belongs to connector c (or
    to none) and to variant v (or to none).  The page script mirrors this (filesFor)."""
    rests = [p for p in parts if p.get("role") == "rest"]
    rest = (next((p for p in rests if p.get("variant") == v and p.get("connector") == c), None)
            or next((p for p in rests if p.get("variant") == v and not p.get("connector")), None)
            or next((p for p in rests if p.get("variant") == v), None)
            or (rests[0] if rests else None))
    return ([rest] if rest else []) + [
        p for p in parts if p.get("role") != "rest"
        and (not p.get("connector") or p.get("connector") == c)
        and (not p.get("variant") or p.get("variant") == v)]


def stl_link_attrs(p):
    """Download attributes of an STL link: data-site = the path on the Pages site (make
    site copies stl/*.stl next to index.html), data-fetch = the CORS-enabled raw copy."""
    name = posixpath.basename(str(p["stl"]).replace(os.sep, "/"))
    return (f' download="{esc(name)}" data-site="stl/{esc(urllib.parse.quote(name))}"'
            f' data-fetch="{esc(p["fetch"])}"')


def html_downloads(parts, mode, variants, conns):
    """The "Download STLs" block: one row per part, only the default pick's rows shown; the
    page script re-filters the rows (filesFor) and the totals when the radios change."""
    v0 = variants[0].get("id") if variants else None
    c0 = conns[0]["id"] if conns else None
    pick = files_for(parts, v0, c0)
    keep = {p["id"] for p in pick}
    order = [p for p in parts if p.get("role") == "rest"] + [p for p in parts if p.get("role") != "rest"]
    total = sum(p["file_bytes"] for p in pick)
    sel = " · ".join(esc(x) for x in ((variants[0].get("label") or v0) if variants else None,
                                      conns[0]["label"] if len(conns) > 1 else None) if x)
    count = (f'<span id="dl-count">{len(pick)} file{"" if len(pick) == 1 else "s"}, '
             f'{esc(fmt_bytes(total))}</span>')
    if mode == "standalone":
        out = [f'<p class="fine dl-for">For <b id="dl-sel">{sel}</b></p>',
               f'<button type="button" class="dl-all" id="dl-all" data-lib="{esc(JSZIP_URL)}" '
               f'data-sri="{esc(JSZIP_SRI)}" aria-describedby="dl-status">'
               f'Download all <span class="dl-sum">({count})</span></button>'
               '<progress class="dl-progress" id="dl-progress" max="1" value="0" '
               'aria-label="Zip progress" hidden></progress>'
               '<p class="fine dl-status" id="dl-status" role="status" aria-live="polite"></p>']
    else:
        out = [f'<p class="fine dl-for">For <b id="dl-sel">{sel}</b> · {count}</p>']
    out.append('<ul class="dl-list" id="dl-list" aria-label="STL files for this pick">')
    for p in order:
        name = posixpath.basename(str(p["stl"]).replace(os.sep, "/"))
        size = fmt_bytes(p["file_bytes"])
        get = ""
        if mode == "standalone":
            get = (f'<a class="dl-get" href="{esc(p["href"])}"{stl_link_attrs(p)} '
                   f'aria-label="Download {esc(name)}, {esc(size)}">Download</a>')
        out.append(f'<li class="dl-row" data-dl="{esc(p["id"])}"{"" if p["id"] in keep else " hidden"}>'
                   f'<div class="dl-what"><span class="dl-name">{esc(p["label"])}</span>'
                   f'<span class="dl-file"><code>{esc(name)}</code> <span class="size">{esc(size)}</span></span></div>'
                   f'{get}</li>')
    out.append("</ul>")
    if mode == "artifact":
        out.append('<p class="fine">Get these from the <a href="' + esc(STL_FOLDER_URL)
                   + '" target="_blank" rel="noopener noreferrer"><code>stl/</code> folder on GitHub</a>; '
                   'this page can’t offer downloads.</p>')
    multi = len(conns) > 1
    buy = "".join(f'<span{conn_attr(c["id"], c0, multi)}>{esc(BUY_NOTE[c["type"]])} </span>'
                  for c in conns if c.get("type") in BUY_NOTE)
    out.append(f'<p class="fine" id="dl-buy">{buy}Everything else to buy: '
               f'{repo_link(mode, "What you need", anchor="what-you-need")}.</p>')
    return "".join(out)


def repo_link(mode, text, cls=None, path=None, anchor=None):
    """Link to the GitHub repository (or to `path` on its main branch, or to a README
    `anchor`); the artifact opens it in a new tab (the claude.ai frame can't show github.com)."""
    attrs = f' class="{cls}"' if cls else ""
    if mode == "artifact":
        attrs += ' target="_blank" rel="noopener noreferrer"'
    href = REPO_URL + (f"/blob/main/{path}" if path else "") + (f"#{anchor}" if anchor else "")
    return f'<a{attrs} href="{esc(href)}">{text}</a>'


def html_wiring_link(mode):
    """Pointer from the pinout to the full wiring guide (wiring.md in the repository)."""
    return ('<p class="fine">Tap points, soldering steps and test procedures for both '
            f'connectors: {repo_link(mode, "wiring guide (wiring.md)", path="wiring.md")}.</p>')


def nobreak(s):
    """Escape s; at phone width the cell may wrap only before ' · ' and before '(' (never at
    the hyphen of 'J1-3'); the dot stays with the text after it, so no line ends in '·'."""
    segs = []
    for k, seg in enumerate(str(s).split(" · ")):
        parts = re.split(r" (?=\()", seg)
        if k:
            parts[0] = "· " + parts[0]
        segs.append(" ".join(f'<span class="nb">{esc(x)}</span>' for x in parts))
    return " ".join(segs)


def html_pinout(conns, cvars):
    multi = len(conns) > 1
    default = conns[0]["id"] if conns else None
    out = []
    for c in conns:
        cv = cvars[c["id"]]
        ctype = cv["connector"]["type"]
        title = c.get("title") or c["label"]
        note = PINOUT_NOTE.get(ctype)
        sid = safe_id(c["id"])
        out.append(f'<div class="pinout"{conn_attr(c["id"], default, multi)}>'
                   f'<p class="fine" id="pinout-type-{esc(sid)}">{esc(title)}.' + (f" {esc(note)}" if note else "")
                   + '</p><div class="scroll-x"><table class="grid" id="pinout-table-' + esc(sid) + '"><thead><tr>'
                   '<th scope="col">Pin</th><th scope="col">Signal</th><th scope="col">Pico</th>'
                   '<th scope="col">TPS65 pad</th></tr></thead><tbody>')
        for r in cv["connector"]["pins"]:
            out.append(f'<tr><td class="num">{esc(r["pin"])}</td><td><b>{esc(r["signal"])}</b>'
                       f'<span class="sub">{esc(r["note"])}</span></td>'
                       f'<td>{nobreak(r["pico"])}</td><td>{nobreak(r["tps65"])}</td></tr>')
        out.append("</tbody></table></div></div>")
    return "".join(out)


def html_radios(name, items):
    """One radio per item ({"id", "label"}); the first starts checked."""
    out = []
    for i, v in enumerate(items):
        vid = str(v.get("id", ""))
        hid = f"{name}-" + safe_id(vid)
        out.append(f'<input type="radio" name="{name}" id="{esc(hid)}" value="{esc(vid)}"'
                   f'{" checked" if i == 0 else ""}><label for="{esc(hid)}">{esc(v.get("label") or vid)}</label>')
    return "\n            ".join(out)


def html_notes(head, tail, conns, cvars):
    multi = len(conns) > 1
    default = conns[0]["id"] if conns else None
    items = [f"<li>{esc(n)}</li>" for n in head]
    for c in conns:
        items += [f'<li{conn_attr(c["id"], default, multi)}>{esc(n)}</li>'
                  for n in connector_notes(cvars[c["id"]], c["label"])]
    items += [f"<li>{esc(n)}</li>" for n in tail]
    return '<ol class="notes" id="print-notes">' + "".join(items) + "</ol>"


# ------------------------------------------------------------------ main --
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--manifest", default=os.path.join(REPO_ROOT, "build", "manifest.json"))
    ap.add_argument("--root", default=None,
                    help="folder the manifest's STL paths are relative to (default: the "
                         "manifest's parent's parent, i.e. the repository root)")
    ap.add_argument("--template", default=os.path.join(REPO_ROOT, "preview", "template.html"))
    ap.add_argument("--out-html", default=os.path.join(REPO_ROOT, "preview", "index.html"))
    ap.add_argument("--out-artifact", default=os.path.join(REPO_ROOT, "build", "artifact.html"))
    ap.add_argument("--target-mb", type=float, default=TARGET_MB)
    args = ap.parse_args(argv)

    with open(args.manifest, encoding="utf-8") as f:
        man = json.load(f)
    root = args.root or os.path.dirname(os.path.dirname(os.path.abspath(args.manifest)))
    cfg = man.get("config") or {}
    density = float(cfg.get("PLA_DENSITY", 1.24))
    variants = man.get("variants") or []
    conns, cvars = connectors_of(man, cfg)
    conn_ids = [c["id"] for c in conns]

    # ---- meshes ------------------------------------------------------------
    parts, tris_by_id = [], {}
    for p in man.get("parts") or []:
        path = os.path.join(root, p["stl"])
        tris = read_stl(path)
        tris_by_id[p["id"]] = tris
        st = dict(mesh_stats(tris, density))
        st.update({k: v for k, v in ((man.get("stats") or {}).get(p["id"]) or {}).items()
                   if v is not None})
        role = p.get("role")
        if "connector" in p:
            conn = p["connector"]
        elif role == "rest":
            conn = None
        else:  # older manifests: a connector id inside the part id ("dock-usbc"), else the first for a dock
            words = re.split(r"[-_.]", str(p["id"]))
            conn = next((cid for cid in conn_ids if cid in words), conn_ids[0] if role == "dock" else None)
        if conn is not None and conn not in conn_ids:
            print(f"  ! part {p['id']}: connector {conn!r} is not in the connector list", file=sys.stderr)
        mw = p.get("moves_with") or ("pad" if role == "grip" else "dock")
        q = {
            "id": p["id"], "variant": p.get("variant"), "role": role, "connector": conn,
            "moves_with": mw if role != "rest" else None,
            "stl": p["stl"], "matrix": p.get("matrix") or [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            "stats": st, "file_bytes": os.path.getsize(path),
        }
        if p.get("explode_offset"):
            q["explode_offset"] = p["explode_offset"]
        q["label"] = part_label(dict(p, connector=conn), variants, conns)
        parts.append(q)

    def encode_all(cell):
        out = {}
        for p in parts:
            tris = tris_by_id[p["id"]]
            c = cell if (cell and p.get("role") == "rest") else None
            out[p["id"]] = encode(*weld(tris, c))
        return out

    enc = encode_all(None)
    payload = sum(len(b) for _, b in enc.values())
    cell = 0.0
    while payload > (args.target_mb - 0.4) * 1e6 and cell < 3.0:
        # Last resort: cluster rest vertices on a coarser grid (warns loudly).
        cell = 0.35 if cell == 0 else cell * 1.4
        enc = encode_all(cell)
        payload = sum(len(b) for _, b in enc.values())
        print(f"  ! meshes too big for the {args.target_mb} MB target; clustered rest "
              f"vertices at {cell:.2f} mm -> {payload / 1e6:.2f} MB", file=sys.stderr)

    for p in parts:
        meta, _ = enc[p["id"]]
        p["mesh"] = meta

    # ---- data blob shared by both outputs ------------------------------------
    keep_cfg = {k: cfg[k] for k in cfg if k.startswith(("ENGRAVE_", "REST_", "TP_", "GLASS_",
                                                        "DOCK_", "CABLE_", "POCKET_", "KEY", "PLUG_",
                                                        "OLED_", "BALLAST_", "FIRST_KEY", "FRONT_ROW",
                                                        "USBC_", "CONNECTORS"))}
    part_keys = ("id", "variant", "role", "connector", "moves_with", "explode_offset", "stl", "matrix",
                 "label", "stats", "file_bytes", "mesh")
    data = {
        "name": man.get("name", "ithalat"), "units": man.get("units", "mm"),
        "frame": man.get("frame", ""), "variants": variants,
        "connectors": [{k: c[k] for k in ("id", "type", "label")} for c in conns],
        "connector_variants": {cid: {k: cv[k] for k in ("dock", "cable", "connector", "hardware")}
                               for cid, cv in cvars.items()},
        "parts": [{k: p[k] for k in part_keys if k in p} for p in parts],
        "trackpad": man.get("trackpad"), "keyboard": man.get("keyboard"),
        "engraving": man.get("engraving"),
        "config": keep_cfg,
    }

    with open(args.template, encoding="utf-8") as f:
        tpl = f.read()

    meshes_html = "\n".join(
        f'<script type="application/octet-stream" id="mesh-{esc(pid)}">{b64}</script>'
        for pid, (_, b64) in enc.items())
    head_notes, tail_notes = print_notes(cfg, man)

    for p in parts:  # the committed copy on GitHub (the page swaps in stl/<file> on *.github.io)
        rel = urllib.parse.quote(posixpath.normpath(str(p["stl"]).replace(os.sep, "/")))
        p["href"], p["fetch"] = RAW_URL + rel, FETCH_URL + rel

    def render(mode, out_path):
        out_dir = os.path.dirname(os.path.abspath(out_path))
        d = dict(data, mode=mode)
        js = json.dumps(d, ensure_ascii=True, separators=(",", ":"))
        js = js.replace("</", "<\\/").replace("<!--", "<\\!--")
        doc = tpl
        subs = {
            "/*@DATA@*/null": js,
            "<!--@MESHES@-->": meshes_html,
            "<!--@DIMENSIONS@-->": html_dimensions(man, conns, cvars),
            "<!--@PARTS@-->": html_parts(parts, mode, conns, cvars),
            "<!--@DOWNLOADS@-->": html_downloads(parts, mode, variants, conns),
            "<!--@PINOUT@-->": html_pinout(conns, cvars),
            "<!--@WIRING-LINK@-->": html_wiring_link(mode),
            "<!--@NOTES@-->": html_notes(head_notes, tail_notes, conns, cvars),
            "<!--@VARIANTS@-->": html_radios("variant", variants),
            "<!--@VARIANT-LABEL@-->": esc((variants[0].get("label") or variants[0].get("id")) if variants else ""),
            "<!--@CONNECTORS@-->": html_radios("connector", conns),
            "<!--@CONNECTOR-LABEL@-->": esc(conns[0]["label"] if conns else ""),
            "<!--@SOURCE-LINK@-->": repo_link(mode, 'Source on GitHub <span aria-hidden="true">↗</span>',
                                              "src-link"),
        }
        for k, v in subs.items():
            if k not in doc:
                raise SystemExit(f"template is missing the {k} placeholder")
            doc = doc.replace(k, v)
        # the "Download all" zip code (JSZip) runs on the standalone page only
        zip_re = r"/\*@ZIP-START@\*/.*?/\*@ZIP-END@\*/\n?"
        if not re.search(zip_re, doc, flags=re.S):
            raise SystemExit("template is missing the /*@ZIP-START@*/ ... /*@ZIP-END@*/ markers")
        if mode == "artifact":
            doc = re.sub(zip_re, "", doc, flags=re.S)
            def cut(a, b):
                i, j = doc.index(a), doc.index(b)
                return doc[i + len(a):j].strip("\n")
            doc = (cut("<!--@FRAGMENT-START@-->", "<!--@HEAD-END@-->") + "\n"
                   + cut("<!--@BODY-START@-->", "<!--@BODY-END@-->") + "\n")
            bad = re.search(r"<!doctype|</?(html|head|body)[\s>]", doc, flags=re.I)
            assert not bad, f"artifact fragment contains {bad.group(0) if bad else ''}"
            assert doc.startswith("<title>"), "artifact must begin with <title>"
        else:
            doc = re.sub(r"/\*@ZIP-(START|END)@\*/ ?\n?", "", doc)
            doc = re.sub(r"<!--@[A-Z-]+@-->\n?", "", doc)
        doc = re.sub(r"<!--@NOTE.*?-->\n?", "", doc, flags=re.S)
        size = len(doc.encode("utf-8"))
        if size > HARD_CAP_MB * 1e6:
            raise SystemExit(f"{out_path}: {size / 1e6:.1f} MB exceeds the {HARD_CAP_MB} MB cap")
        os.makedirs(out_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(doc)
        flag = "" if size <= args.target_mb * 1e6 else f"  (over the {args.target_mb} MB target)"
        print(f"  {os.path.relpath(out_path)}: {size / 1e6:.2f} MB{flag}")

    print("  connectors: " + ", ".join(f"{c['id']} ({c['type']}, {len(cvars[c['id']]['hardware'])} hardware)"
                                       for c in conns))
    for p in parts:
        m = p["mesh"]
        print(f"  {p['id']:18s} {m['nt']:8d} tris {m['nv']:8d} verts -> {m['gz_bytes'] / 1e6:.2f} MB gz")
    render("standalone", args.out_html)
    render("artifact", args.out_artifact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
