"""Ikoner och delningsbilder för CarDep. Kräver Pillow (pip install pillow). Körs när loggan, en modell eller ett foto
ändras, före python3 bygg.py:

    python3 verktyg/bilder.py

Skriver favicon.svg, favicon.ico, apple-touch-icon.png, icon-192.png, icon-512.png och icon-maskable-512.png i app/,
och delningsbilder (1200×630) i app/og/: cardep.png, cardep-en.png och en per bilmodell.
"""
import pathlib, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sajt import data as sdata  # noqa: E402

APP = ROOT / "app"
ACCENT, INK, BG_HI, BG_LO, WHITE = (15, 107, 82), (21, 32, 27), (245, 247, 244), (227, 232, 228), (255, 255, 255)
FONTS = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"]

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0f6b52"/>
<g fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"><path d="M6.4 21.5a9.6 9.6 0 1 1 19.2 0"/><path d="M16 21.5l5.2-5.9"/></g>
<circle cx="16" cy="21.5" r="1.9" fill="#fff"/></svg>
"""


def font(size, kind="display"):
    names = {"display": ["archivo.woff2"], "body": ["ibm-plex-sans.woff2"]}[kind]
    for n in names:
        try:
            f = ImageFont.truetype(str(APP / "assets" / "fonts" / n), size)
            if kind == "display":
                try: f.set_variation_by_axes([800])
                except Exception: pass
            return f
        except Exception:
            pass
    for p in FONTS:
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    return ImageFont.load_default()


def gauge(draw, cx, cy, r, w, color):
    """loggan: en halv mätare med visare, ritad runt (cx, cy) med radien r och linjebredden w"""
    draw.arc([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=color, width=w)
    for x in (cx - r + w / 2, cx + r - w / 2):
        draw.ellipse([x - w / 2, cy - w / 2, x + w / 2, cy + w / 2], fill=color)
    nx, ny = cx + r * 0.54, cy - r * 0.61
    draw.line([cx, cy, nx, ny], fill=color, width=w)
    draw.ellipse([nx - w / 2, ny - w / 2, nx + w / 2, ny + w / 2], fill=color)
    d = w * 0.85
    draw.ellipse([cx - d, cy - d, cx + d, cy + d], fill=color)


def icon(size, maskable=False, rounded=True):
    S = 1024
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if maskable or not rounded:
        dr.rectangle([0, 0, S, S], fill=ACCENT)
    else:
        dr.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=ACCENT)
    scale = 0.62 if maskable else 0.8          # maskerbara ikoner: allt viktigt inom de mittersta 80 %
    r, w = S * 0.3 * scale, S * 0.081 * scale
    gauge(dr, S / 2, S / 2 + r * 0.42, r, int(w), WHITE)
    return im.resize((size, size), Image.LANCZOS)


def tile(w, h):
    top, bot = Image.new("RGB", (w, h), BG_HI), Image.new("RGB", (w, h), BG_LO)
    mask = Image.linear_gradient("L").resize((w, h))
    return Image.composite(bot, top, mask)


def car(mid, box):
    """bilens foto med genomskinlig bakgrund (JPEG + PNG-mask) eller 3D-bilden, inpassad i box (b, h)"""
    f, m = APP / "img" / "foto" / f"{mid}.jpg", APP / "img" / "foto" / f"{mid}-m.png"
    if f.exists() and m.exists():
        im = Image.open(f).convert("RGB")
        a = Image.open(m)
        a = (a.split()[-1] if a.mode in ("RGBA", "LA") else a.convert("L")).resize(im.size)
        im.putalpha(a)
    elif (APP / "img" / "bilar" / f"{mid}.webp").exists():
        im = Image.open(APP / "img" / "bilar" / f"{mid}.webp").convert("RGBA")
    else:
        return None
    bb = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if bb: im = im.crop(bb)
    im.thumbnail(box, Image.LANCZOS)
    return im


def wordmark(dr, x, y, size):
    gauge(dr, x + size * 0.5, y + size * 0.72, size * 0.36, max(3, int(size * 0.09)), ACCENT)
    dr.text((x + size * 1.12, y + size * 0.1), "CarDep", font=font(int(size * 0.82)), fill=INK)


def og_site(lang, mids):
    W, H = 1200, 630
    im = tile(W, H)
    dr = ImageDraw.Draw(im)
    wordmark(dr, 64, 56, 64)
    head = {"sv": ["Vad kostar bilen", "egentligen per månad?"], "en": ["What does the car", "really cost per month?"]}[lang]
    sub = {"sv": "189 bilmodeller · värdeminskning, drivmedel, service, försäkring och skatt",
           "en": "189 car models · depreciation, fuel, servicing, insurance and tax"}[lang]
    f = font(66)
    for i, line in enumerate(head):
        dr.text((64, 190 + i * 78), line, font=f, fill=INK)
    dr.text((64, 372), sub, font=font(27, "body"), fill=(90, 103, 97))
    xs = [(560, 400), (860, 420)]
    for (x, y), mid in zip(xs, mids):
        c = car(mid, (360, 230))
        if c: im.paste(c, (x - c.width // 2 + 120, y + 230 - c.height - 20), c)
    im.save(APP / "og" / ("cardep.png" if lang == "sv" else "cardep-en.png"), optimize=True)


def og_model(m):
    W, H = 1200, 630
    im = tile(W, H)
    dr = ImageDraw.Draw(im)
    c = car(m["id"], (1000, 430))
    if c: im.paste(c, ((W - c.width) // 2, 560 - c.height), c)
    name = m["name"] if m["name"].startswith(m["brand"]) else f'{m["brand"]} {m["name"]}'
    wordmark(dr, 48, 40, 44)
    f = font(58)
    tw = dr.textlength(name, font=f)
    dr.text((W - 48 - tw, 44), name, font=f, fill=INK)
    im.convert("RGB").save(APP / "og" / f'{m["id"]}.jpg', quality=82, optimize=True, progressive=True)


def main():
    (APP / "og").mkdir(exist_ok=True)
    (APP / "favicon.svg").write_text(SVG)
    icon(64).save(APP / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    icon(180, rounded=False).save(APP / "apple-touch-icon.png", optimize=True)
    icon(192).save(APP / "icon-192.png", optimize=True)
    icon(512).save(APP / "icon-512.png", optimize=True)
    icon(512, maskable=True).save(APP / "icon-maskable-512.png", optimize=True)
    data = sdata.load()
    og_site("sv", ["volvo-xc60", "vw-golf"]); og_site("en", ["volvo-xc60", "vw-golf"])
    n = 0
    for m in (data or {}).get("models", []):
        og_model(m); n += 1
    print(f"ikoner och {n + 2} delningsbilder klara")


if __name__ == "__main__":
    main()
