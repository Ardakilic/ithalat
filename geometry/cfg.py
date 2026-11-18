"""Config loading: config.py constants + CLI overrides, derived values
recomputed AFTER the overrides (lesson learned: a registry that captured
GLASS_T at import time never saw --glass-t)."""

import argparse
import ast
import importlib
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _base_module():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import config  # noqa: E402
    return importlib.reload(config)


def config_names(mod=None):
    mod = mod or _base_module()
    return [n for n in dir(mod) if n.isupper() and n != "DERIVED"]


def parse_value(text):
    """Python literal if it parses, else the raw string."""
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def load_config(overrides=None):
    """Return a SimpleNamespace of every UPPER_CASE config value with
    `overrides` (dict NAME -> value) applied and DERIVED values recomputed
    unless overridden themselves."""
    mod = _base_module()
    names = config_names(mod)
    overrides = dict(overrides or {})
    unknown = [k for k in overrides if k not in names]
    if unknown:
        raise SystemExit(f"unknown config name(s): {', '.join(unknown)} "
                         f"(see config.py for the full list)")
    ns = types.SimpleNamespace(**{n: getattr(mod, n) for n in names})
    for k, v in overrides.items():
        setattr(ns, k, v)
    # connector selection: CONNECTORS (or --connector) wins; the legacy
    # DOCK_CONN_TYPE overridden alone selects that single connector; otherwise
    # DOCK_CONN_TYPE follows CONNECTORS[0] (before DERIVED, so PLUG_BODY follows)
    if isinstance(ns.CONNECTORS, str):
        ns.CONNECTORS = (ns.CONNECTORS,)
    ns.CONNECTORS = tuple(normalize_connector(ns, c) for c in ns.CONNECTORS)
    ns.DOCK_CONN_TYPE = normalize_connector(ns, ns.DOCK_CONN_TYPE)
    if "DOCK_CONN_TYPE" in overrides and "CONNECTORS" not in overrides:
        ns.CONNECTORS = (normalize_connector(ns, ns.DOCK_CONN_TYPE),)
    elif "DOCK_CONN_TYPE" not in overrides and ns.CONNECTORS:
        ns.DOCK_CONN_TYPE = ns.CONNECTORS[0]
    for k, fn in mod.DERIVED.items():
        if k not in overrides:
            setattr(ns, k, fn(ns))
    ns._overrides = overrides
    validate(ns)
    return ns


CONNECTOR_TYPES = ("pogo5", "usbc", "jst_sh4")


def normalize_connector(c, name):
    """Connector type from a type ('pogo5') or an id ('pogo'); unknown names
    are returned unchanged (validate() reports them)."""
    name = str(name).strip()
    ids = {v: k for k, v in dict(getattr(c, "CONNECTOR_IDS", {}) or {}).items()}
    return ids.get(name, name)


def validate(c):
    errs = []
    conns = list(c.CONNECTORS or ())
    if not conns:
        errs.append("CONNECTORS must list at least one connector variant")
    bad = [x for x in conns if x not in CONNECTOR_TYPES]
    if bad:
        errs.append(f"unknown connector(s) {bad}: use {', '.join(CONNECTOR_TYPES)}")
    if len(set(conns)) != len(conns):
        errs.append("CONNECTORS lists a connector twice")
    for x in conns:
        if x in CONNECTOR_TYPES and x not in (c.CONNECTOR_IDS or {}):
            errs.append(f"CONNECTOR_IDS has no id for {x!r}")
    if c.DOCK_CLIP_BACK_WALL not in ("inner", "back") or c.USBC_CLIP_BACK_WALL not in ("inner", "back"):
        errs.append("DOCK_CLIP_BACK_WALL / USBC_CLIP_BACK_WALL must be 'inner' or 'back'")
    if c.ENGRAVE_FACE not in ("bottom", "top"):
        errs.append("ENGRAVE_FACE must be 'bottom' or 'top'")
    if not isinstance(c.VARIANTS, dict) or not c.VARIANTS:
        errs.append("VARIANTS must be a non-empty dict id -> glass thickness")
    for k, v in (c.VARIANTS or {}).items():
        if not isinstance(v, (int, float)) or v < 0:
            errs.append(f"VARIANTS[{k!r}] must be a glass thickness >= 0")
    for n in ("REST_WIDTH", "REST_DEPTH", "REST_HEIGHT", "MESH_EDGE_LEN", "TP_WIDTH", "TP_DEPTH"):
        if not (isinstance(getattr(c, n), (int, float)) and getattr(c, n) > 0):
            errs.append(f"{n} must be a positive number")
    if c.MESH_EDGE_LEN < 0.2 or c.MESH_EDGE_LEN > 3.0:
        errs.append("MESH_EDGE_LEN must be within 0.2 .. 3.0 mm")
    if c.DOCK_CONN_TYPE not in CONNECTOR_TYPES:
        errs.append(f"DOCK_CONN_TYPE must be one of {', '.join(CONNECTOR_TYPES)}")
    if c.PLUG_EXIT not in ("down", "rear"):
        errs.append("PLUG_EXIT must be 'down' or 'rear'")
    if not (isinstance(c.PLUG_BODY, (list, tuple)) and len(c.PLUG_BODY) == 3):
        errs.append("PLUG_BODY must be (width, depth, height)")
    if not c.REMOVED_KEYS:
        errs.append("REMOVED_KEYS must list the (row, col) positions the dock replaces")
    if c.PLUG_BAY_DEPTH < 0 or c.PLUG_BAY_CHAMFER < 0:
        errs.append("PLUG_BAY_DEPTH / PLUG_BAY_CHAMFER must be >= 0")
    errs += _validate_tpu(c)
    if errs:
        raise SystemExit("config error:\n  " + "\n  ".join(errs))


def _num(v):
    """A finite int or float, not a bool: inf / nan (e.g. --set X=1e999) fail here."""
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return False
    try:
        return math.isfinite(v)
    except OverflowError:            # an int too large for a float
        return False


def _validate_tpu(c):
    """Type-level checks of the TPU_* constants; the geometric limits (floor
    over the recesses, edge angle, thickness, pegs) live in geometry/tpu.params."""
    errs = []
    labels = c.TPU_TOP_LABELS
    if not (isinstance(labels, dict) and set(labels) == {"rigid", "tpu"}):
        errs.append("TPU_TOP_LABELS must be a dict with exactly the keys 'rigid' and 'tpu'")
    if not isinstance(c.TPU_ENABLED, bool):
        errs.append("TPU_ENABLED must be True or False")
    for n in ("TPU_FLOOR_Z", "TPU_POCKET_COLLAR", "TPU_BALLAST_GAP", "TPU_PEG_D", "TPU_PEG_H",
              "TPU_PEG_CHAMFER", "TPU_PEG_HEADROOM", "TPU_PEG_CLEARANCE", "TPU_BED_CHAMFER",
              "TPU_TEXT_KEEPOUT", "TPU_MIN_T", "TPU_MIN_EDGE_ANGLE", "TPU_PEG_MIN_COVER", "TPU_PEG_EDGE",
              "TPU_DENSITY"):
        if not _num(getattr(c, n)):
            errs.append(f"{n} must be a finite number")
    if errs:
        return errs
    for n in ("TPU_POCKET_COLLAR", "TPU_BALLAST_GAP", "TPU_PEG_D", "TPU_PEG_H", "TPU_DENSITY"):
        if getattr(c, n) <= 0:
            errs.append(f"{n} must be > 0")
    if not (0 < c.TPU_PEG_CHAMFER < c.TPU_PEG_D / 2):
        errs.append("TPU_PEG_CHAMFER must be > 0 and < TPU_PEG_D / 2")
    if not (0 <= c.TPU_PEG_HEADROOM <= 1.0):
        errs.append("TPU_PEG_HEADROOM must be within 0 .. 1 mm")
    if not (0 <= c.TPU_PEG_CLEARANCE <= 0.5):
        errs.append("TPU_PEG_CLEARANCE must be within 0 .. 0.5 mm")
    if not (0 <= c.TPU_BED_CHAMFER <= 1.0):
        errs.append("TPU_BED_CHAMFER must be within 0 .. 1 mm")
    if c.TPU_TEXT_KEEPOUT < 0.3:
        errs.append("TPU_TEXT_KEEPOUT must be >= 0.3 (no cutter wall next to a letter)")
    if c.TPU_INSERT_DEPTH is not None and not (_num(c.TPU_INSERT_DEPTH) and c.TPU_INSERT_DEPTH > 0):
        errs.append("TPU_INSERT_DEPTH must be None (auto) or a positive number")
    pegs = c.TPU_PEGS
    if pegs is not None and not (isinstance(pegs, (list, tuple))
                                 and all(isinstance(p, (list, tuple)) and len(p) == 2
                                         and all(_num(v) for v in p) for p in pegs)):
        errs.append("TPU_PEGS must be None (auto), [] (none) or a list of (x, y) pairs")
    infills = c.TPU_MASS_INFILLS
    if not (isinstance(infills, (list, tuple)) and infills and all(_num(v) and 0 < v < 100 for v in infills)):
        errs.append("TPU_MASS_INFILLS must list infill percentages between 0 and 100")
    return errs


def add_cli_args(p):
    g = p.add_argument_group("config overrides (any constant: --set NAME=VALUE)")
    g.add_argument("--height", type=float, help="REST_HEIGHT: max rest height = trackpad surface (mm)")
    g.add_argument("--depth", type=float, help="REST_DEPTH (mm)")
    g.add_argument("--width", type=float, help="REST_WIDTH (mm)")
    g.add_argument("--glass-t", type=float, help="GLASS_T: glass overlay thickness (mm); 'glass' variant")
    g.add_argument("--tp-back-margin", type=float, help="TP_BACK_MARGIN (mm)")
    g.add_argument("--engrave-face", choices=["bottom", "top"], help="ENGRAVE_FACE")
    g.add_argument("--engrave-text", help="ENGRAVE_TEXT ('' = no engraving)")
    g.add_argument("--no-ballast", action="store_true", help="BALLAST_ENABLED=False")
    g.add_argument("--no-dock", action="store_true", help="DOCK_ENABLED=False")
    g.add_argument("--mesh-edge-len", type=float, help="MESH_EDGE_LEN (mm)")
    g.add_argument("--connector", action="append", default=[], metavar="NAME",
                   help="CONNECTORS: generate only these connector variants (repeatable; "
                        "pogo5|usbc|jst_sh4 or the ids pogo|usbc|jst)")
    g.add_argument("--set", action="append", default=[], metavar="NAME=VALUE",
                   help="override any config constant (python literal), repeatable")
    return p


def overrides_from_args(a):
    o = {}
    pairs = (("height", "REST_HEIGHT"), ("depth", "REST_DEPTH"), ("width", "REST_WIDTH"),
             ("glass_t", "GLASS_T"), ("tp_back_margin", "TP_BACK_MARGIN"),
             ("engrave_face", "ENGRAVE_FACE"), ("engrave_text", "ENGRAVE_TEXT"),
             ("mesh_edge_len", "MESH_EDGE_LEN"))
    for attr, name in pairs:
        v = getattr(a, attr)
        if v is not None:
            o[name] = v
    if a.no_ballast:
        o["BALLAST_ENABLED"] = False
    if a.no_dock:
        o["DOCK_ENABLED"] = False
    if getattr(a, "connector", None):
        o["CONNECTORS"] = tuple(a.connector)
    for item in a.set:
        if "=" not in item:
            raise SystemExit(f"--set expects NAME=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        o[k.strip()] = parse_value(v.strip())
    return o


def config_from_argv(argv=None, description=None):
    p = argparse.ArgumentParser(description=description)
    add_cli_args(p)
    a, rest = p.parse_known_args(argv)
    return load_config(overrides_from_args(a)), a, rest
