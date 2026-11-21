"""Turn the app's model list (models.json) and real dimensions (dims.json) into specs for the 3D generator (gen.js)."""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
MODELS = {m["id"]: m for m in json.load(open(HERE / "models.json", encoding="utf-8"))}
DIMS = json.load(open(HERE / "dims.json", encoding="utf-8"))   # id -> [length, width, height, wheelbase] in mm

# A few models look better with another body template than the app's drawing style.
STYLE_FIX = {"fiat-500e": "hatch3"}


def spec_for(mid, extra=None):
    """Spec for buildCar() in gen.js. The style string comes from the app's CM table, e.g. "suv D lux noclad"."""
    m = MODELS[mid]
    parts = (m["cm"] or "hatch C").split(" ")
    style = STYLE_FIX.get(mid, parts[0])
    flags = set(parts[2:])
    L, W, H, WB = DIMS.get(mid, [4300, 1800, 1450, 2640])
    s = {
        "id": mid, "brand": m["b"], "style": style,
        "L": L, "W": W, "H": H, "WB": WB,
        "color": m["col"],
        "lux": "lux" in flags,
        "sp": "sp" in flags or m["t"] == "Sportbil",
        "tt": "tt" in flags,                                   # two-tone (black) roof
        "ev": m["fuels"] == ["E"],
        "old": bool(m["to"] and m["to"] <= 2013) or m["from"] <= 2009,
    }
    s["rails"] = (style in ("wagon", "suv", "cross", "box") and "norails" not in flags) or "rails" in flags
    if "clad" in flags: s["clad"] = True
    if "noclad" in flags: s["clad"] = False
    for f in flags:                                            # g+N / g-N: ground clearance tweak
        if f.startswith("g") and f[1:2] in "+-":
            s["gcAdj"] = int(f[1:]) * 0.012
    if m["rims"]: s["rim"] = max(m["rims"])                    # largest rim option in inches
    if extra: s.update(extra)
    return s
