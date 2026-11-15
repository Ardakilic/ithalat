"""Engraving text outlines (matplotlib TextPath -> shapely)."""

import glob
import os
import warnings

from shapely import affinity
from shapely.geometry import Polygon

FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts",
             os.path.expanduser("~/.fonts"), "/System/Library/Fonts",
             "/Library/Fonts"]


def find_font(name):
    """Resolve ENGRAVE_FONT: an existing path, or a font file stem searched in
    the usual font directories. Returns a path or None."""
    if name and os.path.isfile(name):
        return name
    for d in FONT_DIRS:
        for ext in ("ttf", "otf", "TTF", "OTF"):
            hits = glob.glob(os.path.join(d, "**", f"{name}.{ext}"), recursive=True)
            if hits:
                return sorted(hits)[0]
    return None


def _path_geometry(text, prop):
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), text, size=100, prop=prop)
    geom = None
    for ring in tp.to_polygons():
        if len(ring) < 3:
            continue
        p = Polygon(ring)
        if not p.is_valid:
            p = p.buffer(0)
        if p.is_empty:
            continue
        # XOR: glyph counters (a, e, o ...) become holes
        geom = p if geom is None else geom.symmetric_difference(p)
    return geom


def text_geometry(text, font, cap_height):
    """Outline of `text` scaled so the cap height (height of 'H') equals
    cap_height. Returned centred: x on the text bbox centre, y on the middle
    of the baseline..cap-height band. Returns (geometry, font_path_used)."""
    from matplotlib.font_manager import FontProperties
    path = find_font(font)
    if path:
        prop = FontProperties(fname=path)
    else:
        warnings.warn(f"font {font!r} not found, using the default sans-serif bold")
        prop = FontProperties(family=["sans-serif"], weight="bold")
    ref = _path_geometry("H", prop)
    cap = ref.bounds[3] - ref.bounds[1]
    geom = _path_geometry(text, prop)
    if geom is None or geom.is_empty:
        raise ValueError(f"engraving text {text!r} produced no outline")
    s = cap_height / cap
    geom = affinity.scale(geom, xfact=s, yfact=s, origin=(0, 0))
    minx, _, maxx, _ = geom.bounds
    geom = affinity.translate(geom, -(minx + maxx) / 2.0, -cap_height / 2.0)
    return geom.buffer(0), path
