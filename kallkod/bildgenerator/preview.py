"""Quick look while tweaking gen.js: renders the studio view plus orthographic side/front/top views.

    python3 preview.py persp,side volvo-xc60 vw-golf
Images land in out/preview/<id>_<view>.png and out/preview/sheet.png.
"""
import sys, base64
from playwright.sync_api import sync_playwright
import serve, specs, sheet

OUT = specs.OUT / "preview"
OUT.mkdir(exist_ok=True)


def run(ids, views=("persp",), extra=None):
    files = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 1300, "height": 600})
        serve.attach(pg)
        pg.goto("http://r.local/render.html")
        pg.wait_for_function("window.ready", timeout=60000)
        for mid in ids:
            sp = specs.spec_for(mid, extra)
            for v in views:
                r = pg.evaluate("s=>renderCar(s)", sp) if v == "persp" else pg.evaluate("([s,m])=>renderOrtho(s,m)", [sp, v])
                f = OUT / f"{mid}_{v}.png"
                f.write_bytes(base64.b64decode(r["url"].split(",")[1]))
                files.append(f)
        b.close()
    sheet.sheet(files, OUT / "sheet.png", cols=3, w=640)
    print("wrote", len(files), "images and", OUT / "sheet.png")


if __name__ == "__main__":
    views = tuple(sys.argv[1].split(",")) if len(sys.argv) > 1 else ("persp",)
    run(sys.argv[2:] or ["volvo-xc60"], views)
