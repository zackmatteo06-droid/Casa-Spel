"""Render studio images of all models (or the ids given on the command line) to out/render/<id>.png (2400x1000, transparent).

    python3 render_all.py                 # all models, ~10 s per car with software WebGL
    python3 render_all.py volvo-xc60 vw-golf
"""
import sys, json, base64, time
from playwright.sync_api import sync_playwright
import serve, specs, sheet

OUT = specs.OUT / "render"
OUT.mkdir(exist_ok=True)


def run(ids, view=None):
    t0 = time.time()
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 1300, "height": 600})
        serve.attach(pg)
        errs = []
        pg.on("pageerror", lambda e: errs.append("ERR " + str(e)))
        pg.goto("http://r.local/render.html")
        pg.wait_for_function("window.ready", timeout=60000)
        if view:
            pg.evaluate("v=>setView(v)", view)
        for mid in ids:
            r = pg.evaluate("s=>renderCar(s)", specs.spec_for(mid))
            (OUT / f"{mid}.png").write_bytes(base64.b64decode(r["url"].split(",")[1]))
            print(mid, "build %.0f ms, render %.0f ms" % (r["build"], r["render"]))
            if errs:
                print(mid, errs[-1]); errs.clear()
        b.close()
    print("rendered", len(ids), "in %.0f s" % (time.time() - t0))


def sheets(ms):
    """Contact sheets per body type for a quick visual review (out/sheet_<type>_<n>.png)."""
    by = {}
    for m in ms:
        by.setdefault(m["t"], []).append(m)
    for t, lst in by.items():
        for k in range(0, len(lst), 24):
            part = lst[k:k + 24]
            sheet.sheet([OUT / f"{m['id']}.png" for m in part], specs.OUT / f"sheet_{t}_{k // 24}.png",
                        cols=4, w=560, labels=[f"{m['b']} {m['n']}" for m in part])


if __name__ == "__main__":
    ids = sys.argv[1:] or list(specs.MODELS)
    run(ids)
    sheets([specs.MODELS[i] for i in ids])
