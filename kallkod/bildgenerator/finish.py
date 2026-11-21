"""Crop each render around the car (same ground line for all) and write the app images:
../app/img/bilar/<id>.webp (1200x600) and <id>-s.webp (640x320).

    python3 finish.py                 # every PNG in out/render
    python3 finish.py volvo-xc60
"""
import json, pathlib, sys
from PIL import Image
import numpy as np

D = pathlib.Path(__file__).resolve().parent
SRC = D / "out" / "render"
DST = D.parent / "app" / "img" / "bilar"
DST.mkdir(parents=True, exist_ok=True)
dims = json.load(open(D / "dims.json"))
OW, OH = 1200, 600


def finish(mid, quality=82):
    im = Image.open(SRC / f"{mid}.png").convert("RGBA")
    a = np.asarray(im)[:, :, 3]
    ys, xs = np.where(a > 60)                       # car + core shadow
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    bw, bh = x1 - x0, y1 - y0
    L = dims[mid][0] / 1000
    f = 0.80 + 0.11 * min(1, max(0, (L - 3.6) / 1.45))   # longer cars fill a little more of the frame
    s = min(f * OW / bw, 0.86 * OH / bh)
    cw, ch = OW / s, OH / s
    cx = (x0 + x1) / 2
    bottom = y1 + (OH * 0.045) / s                  # 4.5 % below the lowest solid pixel
    box = (int(round(cx - cw / 2)), int(round(bottom - ch)), int(round(cx + cw / 2)), int(round(bottom)))
    out = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    out.paste(im.crop((max(0, box[0]), max(0, box[1]), min(im.width, box[2]), min(im.height, box[3]))),
              (max(0, -box[0]), max(0, -box[1])))
    out.resize((OW, OH), Image.LANCZOS).save(DST / f"{mid}.webp", "WEBP", quality=quality, method=6)
    out.resize((640, 320), Image.LANCZOS).save(DST / f"{mid}-s.webp", "WEBP", quality=quality, method=6)
    return (DST / f"{mid}.webp").stat().st_size, (DST / f"{mid}-s.webp").stat().st_size


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(p.stem for p in SRC.glob("*.png"))
    tb = ts = 0
    for mid in ids:
        b, sm = finish(mid)
        tb += b; ts += sm
    print(len(ids), "images, big %.1f MB, small %.1f MB" % (tb / 1e6, ts / 1e6))
