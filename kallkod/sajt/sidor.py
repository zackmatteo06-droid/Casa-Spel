"""De statiska sidorna runt kalkylatorn: en sida per bilmodell, bilregister, topplistor, leasa eller köpa, om, metod, integritet,
villkor, bildkällor och 404, på svenska och engelska. Plus sitemap.xml, robots.txt, manifest, service worker och
chattens katalog. Allt skrivs till app/ (webbplatsens rot) av bygg.py.

Länkar mellan sidorna är relativa, så webbplatsen fungerar både i en undermapp (GitHub Pages) och på en egen
domän. Absoluta adresser (canonical, delningsbilder, sitemap) bygger på "url" i sajt.json.
"""
import base64, datetime, hashlib, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "app"
CFG = json.loads((ROOT / "sajt.json").read_text(encoding="utf-8"))
SITE = CFG["url"].rstrip("/") + "/"
TODAY = datetime.date.today().isoformat()
LANGS = ("sv", "en")
NBSP = " "

# sidornas sökvägar från webbplatsens rot
P = {"home": {"sv": "", "en": "en/"}, "cars": {"sv": "bil/", "en": "en/cars/"}, "rank": {"sv": "topplistor/", "en": "en/rankings/"},
     "method": {"sv": "metod/", "en": "en/method/"}, "about": {"sv": "om/", "en": "en/about/"},
     "privacy": {"sv": "integritet/", "en": "en/privacy/"}, "terms": {"sv": "villkor/", "en": "en/terms/"},
     "credits": {"sv": "bildkallor/", "en": "en/image-credits/"}, "lease": {"sv": "leasing/", "en": "en/leasing/"}}


def car_path(mid, lang):
    return P["cars"][lang] + mid + "/"


def rel(frm, to):
    """relativ länk från sidan frm till sidan to (båda från roten, mappar slutar med /)"""
    up = "../" * frm.count("/")
    return (up + to) or "./"


def esc(s):
    return html.escape(str(s), quote=True)


# ---------- texter ----------
T = {
 "sv": {
  "home": "Kalkylatorn", "cars": "Alla bilar", "rank": "Topplistor", "lease": "Leasa eller köpa", "method": "Så räknar vi", "about": "Om CarDep",
  "privacy": "Integritet", "terms": "Villkor", "credits": "Bildkällor", "contact": "Kontakt", "source": "Källkod",
  "skip": "Hoppa till innehållet", "langBtn": "EN", "langName": "In English", "navAria": "Huvudmeny", "footAria": "Om webbplatsen",
  "crumbAria": "Du är här", "kr": lambda v: f"{nf(v, 'sv')}{NBSP}kr", "mo": "/mån", "perMo": "per månad",
  "footNote": "CarDep är en oberoende jämförelsetjänst. Priser och kostnader är beräkningar utifrån annonsdata och uppskattningar, inte offerter.",
  "updated": "Uppdaterad", "adData": "annonsdata okt 2026",
  "tagline": "Vad kostar bilen egentligen per månad?",
  "siteDesc": "Jämför vad 189 bilmodeller kostar per månad med värdeminskning, drivmedel, service, försäkring och skatt. Begagnat- och nypriser från svenska annonser, och ett prisvärdhetsbetyg från A till E.",
  "fuel": {"E": "El", "P": "Laddhybrid", "H": "Hybrid", "B": "Bensin", "D": "Diesel"},
  "type": {"SUV": "SUV", "Kombi": "Kombi", "Sedan": "Sedan", "Halvkombi": "Halvkombi", "Sportbil": "Sportbil"},
  "typePl": {"SUV": "SUV:ar", "Kombi": "kombibilar", "Sedan": "sedaner", "Halvkombi": "halvkombi", "Sportbil": "sportbilar"},
 },
 "en": {
  "home": "Calculator", "cars": "All cars", "rank": "Rankings", "lease": "Lease or buy", "method": "How we calculate", "about": "About CarDep",
  "privacy": "Privacy", "terms": "Terms", "credits": "Image credits", "contact": "Contact", "source": "Source code",
  "skip": "Skip to content", "langBtn": "SV", "langName": "På svenska", "navAria": "Main menu", "footAria": "About the site",
  "crumbAria": "You are here", "kr": lambda v: f"SEK{NBSP}{nf(v, 'en')}", "mo": "/mo", "perMo": "per month",
  "footNote": "CarDep is an independent comparison service. Prices and costs are calculations based on ad data and estimates, not quotes.",
  "updated": "Updated", "adData": "ad data Oct 2026",
  "tagline": "What does the car really cost per month?",
  "siteDesc": "Compare what 189 car models cost per month in Sweden: depreciation, fuel, servicing, insurance and tax. Used and new prices from Swedish ads, and a value grade from A to E.",
  "fuel": {"E": "Electric", "P": "Plug-in hybrid", "H": "Hybrid", "B": "Petrol", "D": "Diesel"},
  "type": {"SUV": "SUV", "Kombi": "Estate", "Sedan": "Sedan", "Halvkombi": "Hatchback", "Sportbil": "Sports car"},
  "typePl": {"SUV": "SUVs", "Kombi": "estates", "Sedan": "sedans", "Halvkombi": "hatchbacks", "Sportbil": "sports cars"},
 },
}


def thin_mark(lang):
    """varningstriangel för årsmodeller med för få annonser att räkna säkert på"""
    a = {"sv": "Osäkert pris: för få annonser", "en": "Uncertain price: too few ads"}[lang]
    return f'<span class="thin" role="img" aria-label="{a}" title="{a}">⚠&#xFE0E;</span>'


def nf(v, lang):
    s = f"{round(v):,}"
    return s.replace(",", NBSP) if lang == "sv" else s


def kr(v, lang):
    return T[lang]["kr"](v)


def full_name(m, lang):
    n = m["nameEn"] if lang == "en" else m["name"]
    return n if n.startswith(m["brand"]) else f'{m["brand"]} {n}'


LOGO = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true">'
        '<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="M12 17l4.6-5.2"/><circle cx="12" cy="17" r="1.6" fill="currentColor" stroke="none"/></svg>')


def head_common(path, lang, title, desc, alt_path, og_image, extra=""):
    """<head>-taggar som alla sidor delar: sökmotorer, delning, ikoner, manifest, typsnitt"""
    canon = SITE + path
    alt = {lang: path, ("en" if lang == "sv" else "sv"): alt_path}
    hreflang = "".join(f'<link rel="alternate" hreflang="{l}" href="{esc(SITE + alt[l])}">' for l in LANGS)
    hreflang += f'<link rel="alternate" hreflang="x-default" href="{esc(SITE + (alt["sv"]))}">'
    r = rel(path, "")
    og = SITE + og_image
    if path in (P["home"]["sv"], P["home"]["en"]) and CFG.get("google_verifiering"):
        extra = f'<meta name="google-site-verification" content="{esc(CFG["google_verifiering"])}">\n' + extra
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canon)}">
{hreflang}
<meta property="og:type" content="website"><meta property="og:site_name" content="CarDep"><meta property="og:locale" content="{'sv_SE' if lang == 'sv' else 'en_GB'}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canon)}">
<meta property="og:image" content="{esc(og)}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0f6b52" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#161d1a" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="icon" href="{r}favicon.ico" sizes="32x32"><link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{r}apple-touch-icon.png"><link rel="manifest" href="{rel(path, 'en/manifest.webmanifest' if lang == 'en' else 'manifest.webmanifest')}">
<link rel="preload" href="{r}assets/fonts/archivo.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/ibm-plex-sans.woff2" as="font" type="font/woff2" crossorigin>
{extra}"""


def csp(script_hashes=(), connect=()):
    src = " ".join(["'self'"] + [f"'sha256-{h}'" for h in script_hashes])
    conn = " ".join(["'self'"] + list(connect))
    return (f"default-src 'self'; script-src {src}; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
            f"connect-src {conn}; manifest-src 'self'; worker-src 'self'; base-uri 'self'; form-action 'self'; object-src 'none'")


def script_hashes(doc):
    """sha256 för varje inbäddat skript som körs (inte JSON-rutor), till sidans Content-Security-Policy"""
    out = []
    for attrs, body in re.findall(r"<script([^>]*)>(.*?)</script>", doc, re.S):
        if "src=" in attrs or "application/json" in attrs or "application/ld+json" in attrs:
            continue
        out.append(base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode())
    return out


def chat_origin():
    u = CFG.get("chatt_url") or ""
    m = re.match(r"(https?://[^/]+)", u)
    return [m.group(1)] if m else []


def topbar(path, lang, alt_path, current=None):
    t = T[lang]
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{rel(path, P[k][lang])}"{cur if current == k else ""}>{t[k]}</a>'
                    for k in ("home", "cars", "rank", "lease", "method"))
    return f"""<a class="skip" href="#innehall">{t["skip"]}</a>
<header class="topbar gut"><div class="shell">
  <a class="logo" href="{rel(path, P['home'][lang])}">{LOGO}CarDep</a>
  <nav class="nav" aria-label="{t['navAria']}">{links}<a class="lang" href="{rel(path, alt_path)}" hreflang="{'en' if lang == 'sv' else 'sv'}" lang="{'en' if lang == 'sv' else 'sv'}" aria-label="{t['langName']}">{t['langBtn']}</a></nav>
</div></header>"""


def footer(path, lang):
    t = T[lang]
    links = "".join(f'<a href="{rel(path, P[k][lang])}">{t[k]}</a>' for k in ("about", "method", "lease", "privacy", "terms", "credits"))
    links += f'<a href="{esc(CFG["kontakt_url"])}" rel="noopener">{t["contact"]}</a>'
    if CFG.get("telefon"):
        links += f'<a href="tel:{esc(CFG["telefon"])}">{esc(CFG["telefon_visning"])}</a>'
    return f"""<footer class="foot gut"><div class="shell">
  <div class="cols"><a class="logo" href="{rel(path, P['home'][lang])}">{LOGO}CarDep</a><nav aria-label="{t['footAria']}">{links}</nav></div>
  <p>{t["footNote"]} © {datetime.date.today().year} CarDep · {t["adData"]}.</p>
</div></footer>"""


def crumbs(path, lang, items):
    """items: [(namn, sökväg eller None)]"""
    t = T[lang]
    li = "".join(f'<li><a href="{rel(path, p)}">{esc(n)}</a></li>' if p is not None else f'<li aria-current="page">{esc(n)}</li>'
                 for n, p in items)
    return f'<nav class="crumbs" aria-label="{t["crumbAria"]}"><ol>{li}</ol></nav>'


def crumbs_ld(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": SITE + p} if p is not None else {})} for i, (n, p) in enumerate(items)]}


def page(path, lang, alt_path, title, desc, body, current=None, ld=None, og_image="og/cardep.png"):
    if og_image == "og/cardep.png" and lang == "en":
        og_image = "og/cardep-en.png"
    r = rel(path, "")
    ld_html = f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": ld}, ensure_ascii=False)}</script>' if ld else ""
    head = head_common(path, lang, title, desc, alt_path, og_image,
                       extra=f'<link rel="stylesheet" href="{r}assets/site.css">\n'
                             f'<meta http-equiv="Content-Security-Policy" content="{csp()}">\n{ld_html}\n'
                             f'<script src="{r}assets/site.js" defer></script>')
    doc = f"""<!doctype html>
<html lang="{lang}">
<head>
{head}
</head>
<body>
{topbar(path, lang, alt_path, current)}
<main id="innehall" class="gut"><div class="shell">
{body}
</div></main>
{footer(path, lang)}
</body>
</html>
"""
    out = APP / path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    return path


# ---------- bilder ----------
def car_img(path, m, lang, big=False, eager=False):
    """fotot (JPEG + PNG-mask som gör bakgrunden genomskinlig), annars 3D-bilden, annars ingen bild"""
    r = rel(path, "")
    alt = esc(full_name(m, lang))
    lazy = "" if eager else ' loading="lazy"'
    if m["photo"]:
        mid = m["id"]
        src, mask = (f"{r}img/foto/{mid}.jpg", f"{r}img/foto/{mid}-m.png") if big else (f"{r}img/foto/{mid}-s.jpg", f"{r}img/foto/{mid}-ms.png")
        return (f'<img src="{src}" width="1200" height="750" alt="{alt}"{lazy} decoding="async" '
                f'style="-webkit-mask-image:url({mask});mask-image:url({mask});-webkit-mask-size:100% 100%;mask-size:100% 100%">')
    if m["img3d"]:
        mid = m["id"]
        src = f"{r}img/bilar/{mid}.webp" if big else f"{r}img/bilar/{mid}-s.webp"
        return f'<img src="{src}" width="1200" height="600" alt="{alt}"{lazy} decoding="async">'
    return ""


LIC_URL = {"CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/", "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
           "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/", "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
           "CC BY-SA 3.0 de": "https://creativecommons.org/licenses/by-sa/3.0/de/deed.en", "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
           "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/", "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
           "CC BY-SA 2.5": "https://creativecommons.org/licenses/by-sa/2.5/", "CC BY 2.5": "https://creativecommons.org/licenses/by/2.5/"}


def commons(file):
    return "https://commons.wikimedia.org/wiki/File:" + file.replace(" ", "_")


def credit(m, lang):
    ph = m["photo"]
    if not ph:
        return ""
    t = {"sv": ("Foto", "bakgrund borttagen"), "en": ("Photo", "background removed")}[lang]
    lic = esc(ph["license"])
    lic = f'<a href="{LIC_URL[ph["license"]]}" rel="license noopener">{lic}</a>' if ph["license"] in LIC_URL else lic
    return (f'{t[0]}: <a href="{esc(commons(ph["file"]))}" rel="noopener">{esc(ph["artist"] or "Wikimedia Commons")}</a>, {lic}, '
            f'Wikimedia Commons, {t[1]}')


# ---------- data som delas av sidorna ----------
def typical(m):
    """raden som sammanfattar modellen: bilen som är 3 år (eller nyaste raden om den saknas)"""
    rows = m["rows"]
    return rows[1] if len(rows) > 1 else rows[0]


def years_txt(m, lang):
    if m["to"]:
        return f'{m["from"]}–{m["to"]}'
    return f'{m["from"]}–' if lang == "en" else f'sedan {m["from"]}'


def scenario_txt(data, lang):
    sc = data["scenario"]
    if lang == "sv":
        return (f'Räknat på {sc["years"]} års ägande och {nf(sc["mil"], "sv")} mil per år, med bränslepriser från {data["fuel"]["updated"]}. '
                f'Månadskostnaden innehåller värdeminskning, drivmedel, service och reparationer, försäkring och fordonsskatt.')
    return (f'Based on {sc["years"]} years of ownership and {nf(sc["mil"] * 10, "en")} km a year, with fuel prices from {data["fuel"]["updated"]}. '
            f'The monthly cost includes depreciation, fuel, servicing and repairs, insurance and road tax.')


SRC_NAME = {"bl": "Blocket", "au": "AutoUncle", "aum": "AutoUncle", "bk": "BilKoll", "dk": {"sv": "Danmark", "en": "Denmark"},
            "fi": {"sv": "Finland", "en": "Finland"}}


def src_txt(src, lang):
    names = []
    for s in (src or "").split("+"):
        n = SRC_NAME.get(s)
        if isinstance(n, dict): n = n[lang]
        if n and n not in names: names.append(n)
    return ", ".join(names)


def option_price(o, lang):
    p = o.get("p") or 0
    return "" if not p else (("+" if p > 0 else "−") + kr(abs(p), lang))


def cons_txt(o, lang):
    f, c, e = o.get("f"), o.get("c"), o.get("e")
    l100 = "l/100 km"
    if f == "E" and e: return f"{str(e).replace('.', ',') if lang == 'sv' else e} kWh/100 km"
    if f == "P" and c and e:
        cc = str(c).replace(".", ",") if lang == "sv" else str(c)
        ee = str(e).replace(".", ",") if lang == "sv" else str(e)
        return f"{cc} {l100} + {ee} kWh/100 km"
    if c: return f"{str(c).replace('.', ',') if lang == 'sv' else c} {l100}"
    return "–"


def year_span(o, m, lang):
    a, b = o.get("y") or m["from"], o.get("to") or m["to"]
    if b: return f"{a}–{b}"
    return f"{a}–" if lang == "en" else f"från {a}"


# ---------- modellsida ----------
L_MODEL = {
 "sv": {"h1": lambda n: f"Vad kostar en {n} per månad?", "title": lambda n: f"{n}: månadskostnad, begagnatpriser och vanliga fel | CarDep",
        "desc": lambda n, y, mo, p: f"Vad kostar en {n} per månad? En {n} från {y} kostar cirka {mo} i månaden allt inräknat, och kostar cirka {p} att köpa. Se begagnatpriser, motorer och vanliga fel.",
        "lead": lambda n, y, mo, sc: f"En {n} från {y} kostar cirka {mo} i månaden, allt inräknat. {sc}",
        "kMonth": lambda y: f"per månad, årsmodell {y}", "kPrice": lambda y: f"pris, årsmodell {y}", "kNew": "nypris från", "kLast": "senaste nypris",
        "kGrade": "prisvärdhetsbetyg", "cta": "Räkna på din egen situation", "ctaAll": lambda t: f"Alla {t}",
        "hCost": "Månadskostnad per årsmodell", "cYear": "Årsmodell", "cVer": "Version i beräkningen", "cPrice": "Pris", "cMonth": "Per månad", "cGrade": "Betyg",
        "hSplit": lambda y: f"Så fördelas kostnaden för en {y}:a", "dep": "Värdeminskning", "fuelc": "Drivmedel", "svc": "Service och reparationer", "ins": "Försäkring", "tax": "Fordonsskatt",
        "hUsed": "Begagnatpriser i annonser", "uYear": "Årsmodell", "uPrice": "Medianpris", "uAds": "Annonser", "uMil": "Typiskt miltal",
        "thinNote": "Årsmodeller med varningstriangel har färre än fem annonser att räkna på, så priset är osäkert.", "uNote": lambda src: f"Medianpriset i svenska annonser per årsmodell i oktober 2026 (källa: {src}). Annonspriser är utgångspriser, och slutpriset kan bli lägre.",
        "mil": lambda v: f"{nf(v, 'sv')} mil", "hEng": "Motorer och versioner", "eName": "Motor", "eFuel": "Drivmedel", "eHp": "Effekt", "eAcc": "0–100 km/h",
        "eCons": "Förbrukning (WLTP)", "eRange": "Räckvidd", "eYears": "Årsmodeller", "ePrice": "Pristillägg", "hp": lambda v: f"{v} hk", "s": lambda v: f"{str(v).replace('.', ',')} s",
        "km": lambda v: f"{nf(v, 'sv')} km", "other": "Övriga val", "hFacts": "Fakta", "fType": "Kaross", "fYears": "Årsmodeller", "fNew": "Nypris från",
        "fLast": "Senaste nypris", "fTrunk": "Bagage", "fNcap": "Euro NCAP", "fWar": "Nybilsgaranti", "fRel": "Driftsäkerhet", "fIns": "Helförsäkring, uppskattning",
        "fSvc": "Service, uppskattning", "perYear": "/år", "stars": lambda v: f"{v} av 5 stjärnor", "notTested": "inte testad", "years": lambda v: f"{v} år",
        "rel": lambda v: f"{str(v).replace('.', ',')} av 5", "l": lambda v: f"{v} liter",
        "hFaults": "Vanliga fel att ha koll på", "faultCost": lambda v: f"reparation cirka {v}",
        "faultNote": "Felen gäller vissa motorer och årsmodeller. I kalkylatorn räknas risken för just den version du väljer.",
        "hPc": "Fördelar och nackdelar", "pro": "Fördel", "con": "Nackdel", "hSim": "Liknande bilar",
        "simTxt": lambda mo, y: f"{mo}/mån som {y}:a", "hNone": "Bild saknas"},
 "en": {"h1": lambda n: f"What does a {n} cost per month?", "title": lambda n: f"{n}: monthly cost, used prices and common faults | CarDep",
        "desc": lambda n, y, mo, p: f"What does a {n} cost per month? A {y} {n} costs about {mo} a month all in, and about {p} to buy. See used prices, engines and common faults.",
        "lead": lambda n, y, mo, sc: f"A {y} {n} costs about {mo} a month, all in. {sc}",
        "kMonth": lambda y: f"per month, {y} model", "kPrice": lambda y: f"price, {y} model", "kNew": "new from", "kLast": "last new price",
        "kGrade": "value grade", "cta": "Calculate your own situation", "ctaAll": lambda t: f"All {t}",
        "hCost": "Monthly cost by model year", "cYear": "Model year", "cVer": "Version in the calculation", "cPrice": "Price", "cMonth": "Per month", "cGrade": "Grade",
        "hSplit": lambda y: f"How the cost splits for a {y} car", "dep": "Depreciation", "fuelc": "Fuel", "svc": "Servicing and repairs", "ins": "Insurance", "tax": "Road tax",
        "hUsed": "Used prices in ads", "uYear": "Model year", "uPrice": "Median price", "uAds": "Ads", "uMil": "Typical mileage",
        "thinNote": "Model years with a warning triangle have fewer than five ads to go on, so the price is uncertain.", "uNote": lambda src: f"The median price in Swedish ads by model year in October 2026 (source: {src}). Ad prices are asking prices, and the final price may be lower.",
        "mil": lambda v: f"{nf(v * 10, 'en')} km", "hEng": "Engines and versions", "eName": "Engine", "eFuel": "Fuel", "eHp": "Power", "eAcc": "0–100 km/h",
        "eCons": "Consumption (WLTP)", "eRange": "Range", "eYears": "Model years", "ePrice": "Extra cost", "hp": lambda v: f"{v} hp", "s": lambda v: f"{v} s",
        "km": lambda v: f"{nf(v, 'en')} km", "other": "Other options", "hFacts": "Facts", "fType": "Body", "fYears": "Model years", "fNew": "New from",
        "fLast": "Last new price", "fTrunk": "Boot", "fNcap": "Euro NCAP", "fWar": "New-car warranty", "fRel": "Reliability", "fIns": "Comprehensive insurance, estimate",
        "fSvc": "Servicing, estimate", "perYear": "/yr", "stars": lambda v: f"{v} of 5 stars", "notTested": "not tested", "years": lambda v: f"{v} years",
        "rel": lambda v: f"{v} of 5", "l": lambda v: f"{v} litres",
        "hFaults": "Common faults to watch for", "faultCost": lambda v: f"repair about {v}",
        "faultNote": "The faults apply to some engines and model years. The calculator works out the risk for the exact version you choose.",
        "hPc": "Pros and cons", "pro": "Pro", "con": "Con", "hSim": "Similar cars",
        "simTxt": lambda mo, y: f"{mo}/mo as a {y} model", "hNone": "No picture"},
}
GROUP_EN = {"Motor": "Engine", "Utrustning": "Trim", "Säten": "Seats", "Kaross": "Body", "Batteri": "Battery", "Hjul": "Wheels"}


def model_page(data, m, lang, similar):
    t, L = T[lang], L_MODEL[lang]
    mid, name = m["id"], full_name(m, lang)
    path, alt = car_path(mid, lang), car_path(mid, "en" if lang == "sv" else "sv")
    sc = scenario_txt(data, lang)
    row = typical(m)
    mo, pr = kr(row["month"], lang), kr(row["price"], lang)
    app_link = rel(path, P["home"][lang]) + "?bil=" + mid
    cars_link = rel(path, P["cars"][lang])
    typ = t["type"][m["type"]]
    new_kpi = (kr(m["newFrom"], lang), L["kNew"]) if m["newFrom"] else (kr(m["listPrice"], lang), L["kLast"])
    img = car_img(path, m, lang, big=True, eager=True)
    figure = (f'<figure class="photo">{img}<figcaption>{credit(m, lang)}</figcaption></figure>' if img
              else f'<figure class="photo" aria-hidden="true"></figure>')
    kpis = (f'<div class="kpis"><div class="kpi"><b>{mo}</b><span>{L["kMonth"](row["year"])}</span></div>'
            f'<div class="kpi"><b>{pr}</b><span>{L["kPrice"](row["year"])}{thin_mark(lang) if row.get("thin") else ""}</span></div>'
            f'<div class="kpi"><b>{new_kpi[0]}</b><span>{new_kpi[1]}</span></div>'
            f'<div class="kpi"><b><span class="grade {row["grade"]}">{row["grade"]}</span></b><span>{L["kGrade"]} ({row["year"]})</span></div></div>')
    rows = "".join(f'<tr><td>{r["year"]}{thin_mark(lang) if r.get("thin") else ""}</td><td>{esc(", ".join(r["version"]))}</td><td class="num">{kr(r["price"], lang)}</td>'
                   f'<td class="num"><b>{kr(r["month"], lang)}</b></td><td><span class="grade {r["grade"]}" aria-label="{L["cGrade"]} {r["grade"]}">{r["grade"]}</span></td></tr>'
                   for r in m["rows"])
    parts = [("dep", L["dep"], row["dep"]), ("fuel", L["fuelc"], row["fuel"]), ("svc", L["svc"], row["svc"]), ("ins", L["ins"], row["ins"]), ("tax", L["tax"], row["tax"])]
    tot = sum(v for _, _, v in parts) or 1
    split = "".join(f'<span style="width:{v / tot * 100:.1f}%;background:var(--c-{c})"></span>' for c, _, v in parts)
    legend = "".join(f'<li><i style="background:var(--c-{c})"></i>{n}: {kr(v, lang)}{t["mo"]}</li>' for c, n, v in parts)
    body = [crumbs(path, lang, [("CarDep", P["home"][lang]), (t["cars"], P["cars"][lang]), (name, None)]),
            f'<section class="hero"><div><h1>{esc(L["h1"](name))}</h1><p class="lead">{esc(L["lead"](name, row["year"], mo, ""))}</p>{kpis}'
            f'<div class="btns"><a class="btn" href="{app_link}">{L["cta"]}</a><a class="btn ghost" href="{cars_link}#{m["type"].lower()}">{esc(L["ctaAll"](t["typePl"][m["type"]]))}</a></div></div>{figure}</section>',
            f'<h2>{L["hCost"]}</h2><div class="tblwrap" tabindex="0" role="region" aria-label="{L["hCost"]}"><table class="tbl"><thead><tr><th>{L["cYear"]}</th><th>{L["cVer"]}</th><th class="num">{L["cPrice"]}</th>'
            f'<th class="num">{L["cMonth"]}</th><th>{L["cGrade"]}</th></tr></thead><tbody>{rows}</tbody></table></div><p class="small muted">{esc(sc)}</p>'
            + (f'<p class="small muted">{thin_mark(lang)} {esc(L["thinNote"])}</p>' if any(r.get("thin") for r in m["rows"]) else ""),
            f'<h3>{esc(L["hSplit"](row["year"]))}</h3><div class="split" aria-hidden="true">{split}</div><ul class="legend">{legend}</ul>']
    if m.get("lease"):
        body.append(lease_block(data, m, lang, path))
    mk = m.get("market")
    if mk and mk["obs"]:
        obs = sorted(mk["obs"], key=lambda o: -o[0])
        # typical mileage: the app's smoothed figure per model year (an older year never lower), the ads' median for this year's cars
        mils = [(mk.get("mil") or {}).get(str(o[0])) or o[3] for o in obs]
        trs = "".join(f'<tr><td>{o[0]}</td><td class="num">{kr(o[1], lang)}</td><td class="num">{o[2] or "–"}</td><td class="num">{L["mil"](v) if v else "–"}</td></tr>' for o, v in zip(obs, mils))
        body.append(f'<h2>{L["hUsed"]}</h2><div class="tblwrap" tabindex="0" role="region" aria-label="{L["hUsed"]}"><table class="tbl"><thead><tr><th>{L["uYear"]}</th><th class="num">{L["uPrice"]}</th>'
                    f'<th class="num">{L["uAds"]}</th><th class="num">{L["uMil"]}</th></tr></thead><tbody>{trs}</tbody></table></div>'
                    f'<p class="small muted">{esc(L["uNote"](src_txt(mk["src"], lang)))}</p>')
    eng = m["groups"][0]["o"]
    trs = "".join(f'<tr><td>{esc(o["n"])}</td><td>{t["fuel"].get(o.get("f"), "–")}</td><td class="num">{L["hp"](o["hp"]) if o.get("hp") else "–"}</td>'
                  f'<td class="num">{L["s"](o["acc"]) if o.get("acc") else "–"}</td><td>{cons_txt(o, lang)}</td><td class="num">{L["km"](o["r"]) if o.get("r") else "–"}</td>'
                  f'<td>{year_span(o, m, lang)}</td><td class="num">{option_price(o, lang) or "–"}</td></tr>' for o in eng)
    other = []
    for g in m["groups"][1:]:
        gname = g["k"] if lang == "sv" else GROUP_EN.get(g["k"], g["k"])
        opts = ", ".join(esc(o["n"]) + (f" ({option_price(o, lang)})" if o.get("p") else "") for o in g["o"])
        other.append(f"<li><b>{esc(gname)}:</b> {opts}</li>")
    body.append(f'<h2>{L["hEng"]}</h2><div class="tblwrap" tabindex="0" role="region" aria-label="{L["hEng"]}"><table class="tbl"><thead><tr><th>{L["eName"]}</th><th>{L["eFuel"]}</th><th class="num">{L["eHp"]}</th>'
                f'<th class="num">{L["eAcc"]}</th><th>{L["eCons"]}</th><th class="num">{L["eRange"]}</th><th>{L["eYears"]}</th><th class="num">{L["ePrice"]}</th></tr></thead>'
                f'<tbody>{trs}</tbody></table></div>' + (f'<ul>{"".join(other)}</ul>' if other else ""))
    facts = [(L["fType"], typ), (L["fYears"], years_txt(m, lang)),
             (L["fNew"], kr(m["newFrom"], lang)) if m["newFrom"] else (L["fLast"], kr(m["listPrice"], lang)),
             (L["fTrunk"], L["l"](m["trunk"]) if m.get("trunk") else "–"),
             (L["fNcap"], L["stars"](m["ncap"]) if m.get("ncap") else L["notTested"]), (L["fWar"], L["years"](m["war"]) if m.get("war") else "–"),
             (L["fRel"], L["rel"](m["rel"]) if m.get("rel") is not None else "–"),
             (L["fIns"], kr(m["ins"], lang) + L["perYear"]), (L["fSvc"], kr(m["svc"], lang) + L["perYear"])]
    body.append(f'<h2>{L["hFacts"]}</h2><dl class="facts">' + "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in facts) + "</dl>")
    if m["faults"]:
        li = "".join(f'<li><b>{esc(f[lang])}</b>, {L["faultCost"](kr(f["cost"], lang))}</li>' for f in m["faults"])
        body.append(f'<h2>{L["hFaults"]}</h2><ul>{li}</ul><p class="small muted">{L["faultNote"]}</p>')
    body.append(f'<h2>{L["hPc"]}</h2><div class="procon"><div><h3>{L["pro"]}</h3><p>{esc(m["pro"][lang])}</p></div>'
                f'<div><h3>{L["con"]}</h3><p>{esc(m["con"][lang])}</p></div></div>')
    if similar:
        cards = "".join(card(path, s, lang) for s in similar)
        body.append(f'<h2>{L["hSim"]}</h2><ul class="grid">{cards}</ul>')
    body.append(f'<p class="updated">{t["updated"]} {TODAY} · {t["adData"]}</p>')
    og = f"og/{mid}.jpg" if (APP / "og" / f"{mid}.jpg").exists() else "og/cardep.png"
    ld = [crumbs_ld([("CarDep", P["home"][lang]), (t["cars"], P["cars"][lang]), (name, None)]),
          {"@type": "Car", "name": name, "brand": {"@type": "Brand", "name": m["brand"]}, "model": m["nameEn"] if lang == "en" else m["name"],
           "bodyType": typ, "url": SITE + path, "image": SITE + og, "description": m["pro"][lang],
           **({"vehicleModelDate": str(m["from"])} if m.get("from") else {})}]
    return page(path, lang, alt, L["title"](name), L["desc"](name, row["year"], mo, pr), "\n".join(body), ld=ld, og_image=og)


def card(path, m, lang, note=None):
    L = L_MODEL[lang]
    row = typical(m)
    img = car_img(path, m, lang) or f'<span class="muted small">{L["hNone"]}</span>'
    sub = note if note is not None else L["simTxt"](kr(row["month"], lang), row["year"])
    return (f'<li><a class="car" href="{rel(path, car_path(m["id"], lang))}"><span class="pic">{img}</span>'
            f'<span class="t"><b>{esc(full_name(m, lang))}{thin_mark(lang) if m.get("thin") else ""}</b><span>{esc(sub)}</span></span></a></li>')


def similar_to(m, models, n=6):
    row = typical(m)
    same = [x for x in models if x["id"] != m["id"] and x["type"] == m["type"] and not x.get("thin")]
    same.sort(key=lambda x: abs(typical(x)["month"] - row["month"]))
    return same[:n]


# ---------- leasa eller köpa ----------
def date_txt(iso, lang):
    y, mo, d = (int(x) for x in iso.split("-"))
    names = {"sv": ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"],
             "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}[lang]
    return f"{d} {names[mo - 1]} {y}"


def dist(mil, lang):
    return f"{nf(mil, 'sv')}{NBSP}mil" if lang == "sv" else f"{nf(mil * 10, 'en')}{NBSP}km"


def pct(v, lang):
    s = f"{v:g}"
    return s.replace(".", ",") if lang == "sv" else s


def host(url):
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]


L_LEASE = {
 "sv": {"h": "Leasa eller köpa ny?", "col": "Per månad", "lease": "Leasa", "buy": "Köpa",
        "intro": lambda c, mil, rate: (f"{c['n']} erbjuder {c['v']} från {kr(c['fee'], 'sv')} i månaden i {c['mon']} månader och {dist(c['mil'], 'sv')} per år. "
                                       f"Så mycket kostar det jämfört med att köpa samma bil ny för {kr(c['price'], 'sv')} och sälja den efter {c['mon']} månader, "
                                       f"räknat på {dist(mil, 'sv')} per år och {rate} procents ränta."),
        "win": {"L": "Leasa är billigast", "B": "Köpa är billigast", "S": "Ungefär lika"},
        "diff": lambda a, b, n: f"{a} mindre per månad, {b} på {n} månader.", "same": "Skillnaden är under 100 kr i månaden.",
        "fee": lambda d: f"Leasingavgift, {d} per år", "fees": "Uppläggnings- och aviavgift", "feesFirst": "Avgifter och förhöjd första hyra",
        "dep": "Värdeminskning", "rent": lambda r: f"Ränta på pengarna, {r} %", "svc": "Service och reparationer", "incl": "ingår",
        "fuel": "Drivmedel", "ins": "Försäkring", "tax": "Fordonsskatt", "tot": "Totalt per månad", "totN": lambda n: f"Totalt på {n} månader",
        "offer": lambda c: (f"{c['n']}: {c['v']}, {c['mon']} månader, {dist(c['mil'], 'sv')} per år"
                            + (f", {kr(c['first'], 'sv')} i förhöjd första hyra" if c["first"] else "")
                            + (", service ingår" if c["svc"] else ", service ingår inte") + (", fast avgift." if c["fix"] else ", rörlig avgift som följer räntan.")),
        "feesTxt": lambda c: (f"Uppläggningsavgift {kr(c['setup'], 'sv')} och aviavgift {kr(c['adm'], 'sv')} i månaden"
                              + (" (uppskattat, beloppen står inte i erbjudandet)." if c["est"] else ".")),
        "src": lambda a, d, u: f"Källa: {a}, avläst {d}" + (f", gäller till och med {u}." if u else "."),
        "milUp": lambda d, x, own: f"Du kör {d} mer per år än erbjudandet räknar med. {'Märkets' if own else 'Uppskattat'} pris för fler mil: {x} i månaden.",
        "milDown": lambda d: f"Erbjudandet gäller {d} per år. Kör du mindre blir leasingavgiften densamma.",
        "buyTxt": lambda p, r, y, d, typ: (f"Köpa: {p} för en ny bil i samma version, och {r} tillbaka när du säljer den efter {y} år. Restvärdet bygger på "
                                           f"annonspriserna för {y} år gamla bilar, justerat för att du kör {d} på {y} år i stället för typiska {typ}. Räntan är "
                                           f"vad pengarna kostar: ränta på ett billån, eller räntan du går miste om på sparade pengar."),
        "sameTxt": "Drivmedel, försäkring och skatt är desamma. Övermil och onormalt slitage betalas när leasingbilen lämnas tillbaka, och byter du in en köpt bil hos en handlare får du oftast mindre än annonspriset.",
        "sameIns": lambda a: (f"Försäkringen måste tecknas genom leasingbolaget för {a} i månaden; köper du räknar vi med vår uppskattning för helförsäkring. "
                              "Drivmedel och skatt är desamma. Övermil och onormalt slitage betalas när leasingbilen lämnas tillbaka, och byter du in en köpt bil "
                              "hos en handlare får du oftast mindre än annonspriset."),
        "cta": "Räkna med din egen körsträcka och ränta", "all": "Alla leasingbilar jämförda"},
 "en": {"h": "Lease or buy new?", "col": "Per month", "lease": "Lease", "buy": "Buy",
        "intro": lambda c, mil, rate: (f"{c['n']} offers the {c['v']} from {kr(c['fee'], 'en')} a month for {c['mon']} months and {dist(c['mil'], 'en')} a year. "
                                       f"Here is what that costs compared with buying the same car new for {kr(c['price'], 'en')} and selling it after {c['mon']} months, "
                                       f"at {dist(mil, 'en')} a year and {rate} percent interest."),
        "win": {"L": "Leasing is cheaper", "B": "Buying is cheaper", "S": "About the same"},
        "diff": lambda a, b, n: f"{a} less a month, {b} over {n} months.", "same": "The difference is under SEK 100 a month.",
        "fee": lambda d: f"Lease payment, {d} a year", "fees": "Set-up and invoice fees", "feesFirst": "Fees and higher first payment",
        "dep": "Depreciation", "rent": lambda r: f"Interest on the money, {r}%", "svc": "Servicing and repairs", "incl": "included",
        "fuel": "Fuel", "ins": "Insurance", "tax": "Road tax", "tot": "Total per month", "totN": lambda n: f"Total over {n} months",
        "offer": lambda c: (f"{c['n']}: {c['v']}, {c['mon']} months, {dist(c['mil'], 'en')} a year"
                            + (f", {kr(c['first'], 'en')} higher first payment" if c["first"] else "")
                            + (", servicing included" if c["svc"] else ", servicing not included") + (", fixed payment." if c["fix"] else ", variable payment that follows interest rates.")),
        "feesTxt": lambda c: (f"Set-up fee {kr(c['setup'], 'en')} and invoice fee {kr(c['adm'], 'en')} a month"
                              + (" (estimated, the offer doesn't state them)." if c["est"] else ".")),
        "src": lambda a, d, u: f"Source: {a}, read on {d}" + (f", valid until {u}." if u else "."),
        "milUp": lambda d, x, own: f"You drive {d} more per year than the offer assumes. {'The brand' + chr(39) + 's' if own else 'Estimated'} price for the extra distance: {x} a month.",
        "milDown": lambda d: f"The offer is for {d} a year. Driving less doesn't lower the payment.",
        "buyTxt": lambda p, r, y, d, typ: (f"Buying: {p} for a new car in the same version, and {r} back when you sell it after {y} years. The residual value is based "
                                           f"on ad prices for {y}-year-old cars, adjusted because you drive {d} in {y} years instead of the typical {typ}. The interest "
                                           f"is what the money costs: interest on a car loan, or the interest you miss on savings."),
        "sameTxt": "Fuel, insurance and tax are the same either way. Excess mileage and abnormal wear are charged when you hand back a leased car, and trading in a car you own at a dealer usually gets you less than the ad price.",
        "sameIns": lambda a: (f"Insurance must be taken out through the leasing company for {a} a month; if you buy, we use our estimate for comprehensive insurance. "
                              "Fuel and tax are the same. Excess mileage and abnormal wear are charged when you hand back a leased car, and trading in a car you own "
                              "at a dealer usually gets you less than the ad price."),
        "cta": "Calculate with your own distance and interest", "all": "All lease cars compared"},
}


def lease_dates(ls, lang):
    """dagarna då erbjudandena lästes av, t.ex. 26–27 oktober 2026"""
    ds = sorted({x.get("date") or ls["date"] for x in ls["terms"].values()})
    if len(ds) == 1:
        return date_txt(ds[0], lang)
    a, b = ds[0], ds[-1]
    return f"{int(a[8:])}–{date_txt(b, lang)}" if a[:7] == b[:7] else f"{date_txt(a, lang)} – {date_txt(b, lang)}"


def and_list(xs, lang):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + (" och " if lang == "sv" else " and ") + xs[-1]


def lease_diff(c):
    """leasa minus köpa per månad, i hela kronor som i tabellerna"""
    return round(c["lease"]["month"]) - round(c["buy"]["month"])


def lease_verdict(c, lang):
    L, d = L_LEASE[lang], lease_diff(c)
    if abs(d) < 100:
        return f'<p class="lease-v"><strong>{L["win"]["S"]}</strong> <span>{L["same"]}</span></p>'
    return (f'<p class="lease-v win"><strong>{L["win"]["L" if d < 0 else "B"]}</strong> '
            f'<span>{esc(L["diff"](kr(abs(d), lang), kr(abs(d) * c["mon"], lang), c["mon"]))}</span></p>')


def lease_table(c, lang, mil, rate, label):
    L = L_LEASE[lang]
    k = lambda v: kr(v, lang)
    l, b = c["lease"], c["buy"]
    lm, bm = round(l["month"]), round(b["month"])
    rows = [(L["fee"](dist(mil, lang)), k(l["fee"]), "–"),
            (L["feesFirst"] if c["first"] else L["fees"], k(l["first"] + l["fees"]), "–"),
            (L["dep"], "–", k(b["dep"])), (L["rent"](pct(rate, lang)), "–", k(b["rent"])),
            (L["svc"], L["incl"] if c["svc"] and l["svc"] < 1 else k(l["svc"]), k(b["svc"])),
            (L["fuel"], k(l["fuel"]), k(b["fuel"])), (L["ins"], k(l["ins"]), k(b["ins"])), (L["tax"], k(l["tax"]), k(b["tax"]))]
    trs = "".join(f'<tr><td>{esc(a)}</td><td class="num">{x}</td><td class="num">{y}</td></tr>' for a, x, y in rows)
    trs += f'<tr class="sum"><td>{L["tot"]}</td><td class="num">{k(lm)}</td><td class="num">{k(bm)}</td></tr>'
    trs += f'<tr><td>{esc(L["totN"](c["mon"]))}</td><td class="num">{k(lm * c["mon"])}</td><td class="num">{k(bm * c["mon"])}</td></tr>'
    return (f'<div class="tblwrap" tabindex="0" role="region" aria-label="{esc(label)}"><table class="tbl lease"><thead><tr><th>{L["col"]}</th>'
            f'<th class="num">{L["lease"]}</th><th class="num">{L["buy"]}</th></tr></thead><tbody>{trs}</tbody></table></div>')


def lease_block(data, m, lang, path):
    """avsnittet Leasa eller köpa på en modellsida (bara modeller med ett privatleasingerbjudande)"""
    c, L, ls = m["lease"], L_LEASE[lang], data["lease"]
    mil, rate, y = ls["mil"], ls["rate"], c["mon"] // 12
    notes = []
    if mil > c["mil"]:
        notes.append(L["milUp"](dist(mil - c["mil"], lang), kr(c["lease"]["fee"] - c["fee"], lang), bool(c["km"])))
    elif mil < c["mil"]:
        notes.append(L["milDown"](dist(c["mil"], lang)))
    src = L["src"](f'<a href="{esc(c["url"])}" rel="noopener">{esc(host(c["url"]))}</a>', date_txt(c["date"], lang),
                   date_txt(c["until"], lang) if c["until"] else "")
    note1 = esc(" ".join(notes + [L["offer"](c), L["feesTxt"](c)])) + " " + src
    note2 = esc(L["buyTxt"](kr(c["price"], lang), kr(c["resid"], lang), y, dist(y * mil, lang), dist(c["typ"], lang)) + " " + (L["sameIns"](kr(c["ins"], lang)) if c.get("ins") else L["sameTxt"]))
    app_link = rel(path, P["home"][lang]) + "?bil=" + m["id"]
    return (f'<h2 id="leasa">{L["h"]}</h2><p>{esc(L["intro"](c, mil, pct(rate, lang)))}</p>{lease_verdict(c, lang)}'
            + lease_table(c, lang, mil, rate, L["h"]) + f'<p class="small muted">{note1}</p><p class="small muted">{note2}</p>'
            f'<p><a href="{app_link}">{L["cta"]}</a> · <a href="{rel(path, P["lease"][lang])}">{L["all"]}</a></p>')


def lease_page(data, lang):
    """översikten: alla modeller med ett privatleasingerbjudande, leasa mot köpa"""
    t, L = T[lang], L_LEASE[lang]
    path, alt = P["lease"][lang], P["lease"]["en" if lang == "sv" else "sv"]
    ls = data["lease"]
    mil, rate = ls["mil"], pct(ls["rate"], lang)
    ms = sorted((m for m in data["models"] if m.get("lease")), key=lambda m: lease_diff(m["lease"]))
    n = len(ms)
    n_l = sum(1 for m in ms if lease_diff(m["lease"]) <= -100)
    n_b = sum(1 for m in ms if lease_diff(m["lease"]) >= 100)
    n_s = n - n_l - n_b
    by_fuel = []
    for f in ("E", "P", "H", "B"):
        fs = [m for m in ms if m["lease"]["fuelType"] == f]
        if fs:
            by_fuel.append((t["fuel"][f], sum(1 for m in fs if lease_diff(m["lease"]) <= -100), len(fs)))

    def verdict_cell(c):
        d = lease_diff(c)
        if abs(d) < 100:
            return L["win"]["S"]
        return (f'{"Leasa" if d < 0 else "Köpa"}, {kr(abs(d), "sv")} billigare' if lang == "sv"
                else f'{"Lease" if d < 0 else "Buy"}, {kr(abs(d), "en")} cheaper')

    trs = []
    for m in ms:
        c = m["lease"]
        lo, bo = round(c["lease"]["month"]), round(c["buy"]["month"])
        lt = f"<b>{kr(lo, lang)}</b>" if lo < bo else kr(lo, lang)
        bt = f"<b>{kr(bo, lang)}</b>" if bo < lo else kr(bo, lang)
        trs.append(f'<tr><td><a href="{rel(path, car_path(m["id"], lang))}#leasa">{esc(full_name(m, lang))}</a></td><td>{esc(c["v"])}</td>'
                   f'<td class="num">{kr(c["fee"], lang)}</td><td class="num">{lt}</td><td class="num">{bt}</td><td>{verdict_cell(c)}</td></tr>')
    terms = sorted({(x["n"], x["url"], x.get("until")) for x in ls["terms"].values()})
    bname = {m["lease"]["brand"]: m["brand"] for m in ms}
    fixed = and_list((bname[k] for k, x in ls["terms"].items() if x.get("fix") and k in bname), lang)
    own_ins = [(bname[k], x["ins"]) for k, x in ls["terms"].items() if x.get("ins") and k in bname]
    dates = lease_dates(ls, lang)
    if lang == "sv":
        h1 = "Leasa eller köpa?"
        head = ("<tr><th>Bil</th><th>Erbjudande</th><th class=\"num\">Leasingavgift</th><th class=\"num\">Leasa, allt inräknat</th>"
                "<th class=\"num\">Köpa, allt inräknat</th><th>Billigast</th></tr>")
        fuel_li = "".join(f"<li>{esc(a)}: leasing billigast för {b} av {c}</li>" for a, b, c in by_fuel)
        src_li = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(nm)}</a> ({esc(host(u))}){f", gäller till och med {date_txt(un, lang)}" if un else ""}</li>'
                         for nm, u, un in terms)
        body = (f'<p class="lead">Är det billigare att privatleasa en ny bil eller att köpa den? Vi har jämfört märkenas egna privatleasingerbjudanden för {n} bilar '
                f'med att köpa samma version ny och sälja den när avtalet går ut, oftast efter 36 månader.</p>'
                f'<p class="lease-v win"><strong>Leasa är billigast för {n_l} av {n} bilar</strong> <span>Köpa är billigast för {n_b}, och för {n_s} är skillnaden under 100 kr i månaden. '
                f'Räknat på {dist(mil, "sv")} per år och {rate} procents ränta på pengarna när du köper.</span></p>'
                f'<ul>{fuel_li}</ul>'
                f'<p>Kampanjpriserna på privatleasing är ofta lägre än vad bilen tappar i värde, särskilt för elbilar och dyrare bilar som tappar mycket i värde de första åren. '
                f'Bilar som håller värdet bra, som många hybrider och småbilar, blir oftare billigare att köpa.</p>'
                f'<h2>Alla bilar med privatleasing</h2><p class="small muted">Kronor per månad. Leasa och köpa innehåller allt: avgifter eller värdeminskning och ränta, '
                f'service, drivmedel, försäkring och skatt. Sorterat från störst fördel för leasing till störst fördel för köp. Välj en bil för hela uträkningen.</p>'
                f'<div class="tblwrap" tabindex="0" role="region" aria-label="Leasa eller köpa, alla bilar"><table class="tbl"><thead>{head}</thead><tbody>{"".join(trs)}</tbody></table></div>'
                f'<h2>Så jämför vi</h2><ul>'
                f'<li><b>Leasa:</b> märkets privatleasingavgift vid din körsträcka, uppläggnings- och aviavgift och eventuell förhöjd första hyra utslagna per månad, '
                f'och service om den inte ingår. Kör du mer än erbjudandet räknar vi med märkets pris för fler mil, eller en uppskattning om märket inte anger det.</li>'
                f'<li><b>Köpa:</b> samma version ny, till listpriset eller vad nya bilar annonseras för om det är lägre, såld efter avtalstiden till annonspriset för en lika gammal bil. '
                f'Restvärdet justeras med 2 procent per 1 000 mil som du kör mer eller mindre än en typisk bil. Till det kommer ränta på pengarna och service.</li>'
                f'<li><b>Lika i båda fallen:</b> drivmedel och fordonsskatt, och försäkringen om inte leasingbolaget kräver en egen'
                + ("".join(f', som {b} för {kr(a, "sv")} i månaden' for b, a in own_ins)) + '.</li></ul>'
                f'<p>Mer om beräkningarna står under <a href="{rel(path, P["method"]["sv"])}">Så räknar vi</a>. I <a href="{rel(path, P["home"]["sv"])}">kalkylatorn</a> '
                f'kan du ändra körsträcka och ränta: öppna en bil och gå till Leasa eller köpa ny.</p>'
                f'<h2>Bra att veta om privatleasing</h2><ul>'
                f'<li>Avtalet gäller oftast i 36 månader, och att avsluta det i förtid kostar.</li>'
                f'<li>Kör du mer än avtalat betalar du övermil när bilen lämnas tillbaka, 8–12,50 kr per mil i de erbjudanden som anger det, och skador utöver normalt slitage.</li>'
                f'<li>Många avgifter är rörliga och följer räntan. {fixed} har fast avgift i sina erbjudanden.</li>'
                f'<li>Försäkring och fordonsskatt betalar du själv, och leasingbolaget kan kräva en viss försäkring.</li>'
                f'<li>Du äger aldrig bilen. En köpt bil bestämmer du själv över, och blir den värd mer än väntat är det din vinst.</li></ul>'
                f'<h2>Källor</h2><p>Erbjudandena lästes av på märkenas webbplatser den {dates} och kan ha ändrats sedan dess. Kampanjer gäller ofta ett begränsat antal bilar.</p>'
                f'<ul>{src_li}</ul>')
        title = "Leasa eller köpa? Privatleasing jämfört med att köpa ny bil | CarDep"
        desc = (f"Är det billigare att privatleasa eller köpa en ny bil? Vi jämför märkenas privatleasingerbjudanden för {n} bilar med att köpa samma bil ny "
                f"och sälja den efter tre år. Leasing är billigast för {n_l} av dem.")
    else:
        h1 = "Lease or buy?"
        head = ("<tr><th>Car</th><th>Offer</th><th class=\"num\">Lease payment</th><th class=\"num\">Lease, all in</th>"
                "<th class=\"num\">Buy, all in</th><th>Cheaper</th></tr>")
        fuel_li = "".join(f"<li>{esc(a)}: leasing is cheaper for {b} of {c}</li>" for a, b, c in by_fuel)
        src_li = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(nm)}</a> ({esc(host(u))}){f", valid until {date_txt(un, lang)}" if un else ""}</li>'
                         for nm, u, un in terms)
        body = (f'<p class="lead">Is it cheaper to lease a new car privately or to buy it? We compared the brands\' own private lease offers in Sweden for {n} cars '
                f'with buying the same version new and selling it when the lease ends, usually after 36 months.</p>'
                f'<p class="lease-v win"><strong>Leasing is cheaper for {n_l} of {n} cars</strong> <span>Buying is cheaper for {n_b}, and for {n_s} the difference is under SEK 100 a month. '
                f'At {dist(mil, "en")} a year and {rate} percent interest on the money when you buy.</span></p>'
                f'<ul>{fuel_li}</ul>'
                f'<p>Private lease campaign prices are often lower than what the car loses in value, especially for electric cars and pricier cars that lose a lot of value in the first years. '
                f'Cars that hold their value well, like many hybrids and small cars, are more often cheaper to buy.</p>'
                f'<h2>All cars with a private lease offer</h2><p class="small muted">Swedish kronor per month. Lease and buy include everything: fees or depreciation and interest, '
                f'servicing, fuel, insurance and tax. Sorted from the biggest advantage for leasing to the biggest advantage for buying. Choose a car for the full calculation.</p>'
                f'<div class="tblwrap" tabindex="0" role="region" aria-label="Lease or buy, all cars"><table class="tbl"><thead>{head}</thead><tbody>{"".join(trs)}</tbody></table></div>'
                f'<h2>How we compare</h2><ul>'
                f'<li><b>Lease:</b> the brand\'s private lease payment at your distance, set-up and invoice fees and any higher first payment spread per month, '
                f'and servicing if it isn\'t included. If you drive more than the offer assumes we use the brand\'s price for more distance, or an estimate where the brand doesn\'t give one.</li>'
                f'<li><b>Buy:</b> the same version new, at the list price or what new cars are advertised for if that is lower, sold when the lease would end at the ad price for a car of the same age. '
                f'The residual value is adjusted by 2 percent per 10,000 km you drive more or less than a typical car. On top of that come interest on the money and servicing.</li>'
                f'<li><b>The same either way:</b> fuel and road tax, and insurance unless the leasing company requires its own'
                + ("".join(f', like {b} for {kr(a, "en")} a month' for b, a in own_ins)) + '.</li></ul>'
                f'<p>More about the calculations under <a href="{rel(path, P["method"]["en"])}">How we calculate</a>. In the <a href="{rel(path, P["home"]["en"])}">calculator</a> '
                f'you can change the distance and the interest: open a car and go to Lease or buy new.</p>'
                f'<h2>Good to know about private leasing</h2><ul>'
                f'<li>The contract usually runs for 36 months, and ending it early costs money.</li>'
                f'<li>If you drive more than agreed you pay for the extra distance when you hand the car back, SEK 8–12.50 per 10 km in the offers that state it, plus damage beyond normal wear.</li>'
                f'<li>Many payments are variable and follow interest rates. {fixed} have fixed payments in their offers.</li>'
                f'<li>You pay insurance and road tax yourself, and the leasing company may require a certain insurance.</li>'
                f'<li>You never own the car. A car you buy is yours to decide over, and if it ends up worth more than expected, the gain is yours.</li></ul>'
                f'<h2>Sources</h2><p>The offers were read on the brands\' Swedish websites on {dates} and may have changed since. Campaigns often cover a limited number of cars.</p>'
                f'<ul>{src_li}</ul>')
        title = "Lease or buy? Private leasing compared with buying a new car | CarDep"
        desc = (f"Is it cheaper to lease or buy a new car in Sweden? We compare the brands' private lease offers for {n} cars with buying the same car new "
                f"and selling it after three years. Leasing is cheaper for {n_l} of them.")
    body = (crumbs(path, lang, [("CarDep", P["home"][lang]), (h1, None)]) + f"<h1>{h1}</h1>" + body
            + f'<p class="updated">{t["updated"]} {TODAY} · {t["adData"]}</p>')
    ld = [crumbs_ld([("CarDep", P["home"][lang]), (h1, None)]),
          {"@type": "WebPage", "name": h1, "url": SITE + path, "inLanguage": lang, "description": desc}]
    return page(path, lang, alt, title, desc, body, current="lease", ld=ld)


# ---------- bilregister ----------
def cars_index(data, lang):
    t = T[lang]
    path, alt = P["cars"][lang], P["cars"]["en" if lang == "sv" else "sv"]
    models = data["models"]
    order = ["SUV", "Kombi", "Sedan", "Halvkombi", "Sportbil"]
    intro = {"sv": f"CarDep räknar på {len(models)} bilmodeller som är vanliga i Sverige, nya och begagnade. Välj en bil för att se månadskostnad, begagnatpriser, motorer och vanliga fel.",
             "en": f"CarDep covers {len(models)} car models that are common in Sweden, new and used. Choose a car to see its monthly cost, used prices, engines and common faults."}[lang]
    h1 = {"sv": "Alla bilar", "en": "All cars"}[lang]
    jump = " · ".join(f'<a href="#{k.lower()}">{t["type"][k]}</a>' for k in order)
    secs = []
    for k in order:
        ms = sorted([m for m in models if m["type"] == k], key=lambda m: full_name(m, lang).lower())
        if not ms: continue
        secs.append(f'<h2 id="{k.lower()}">{t["type"][k]} <span class="muted small">({len(ms)})</span></h2><ul class="grid">{"".join(card(path, m, lang) for m in ms)}</ul>')
    body = (crumbs(path, lang, [("CarDep", P["home"][lang]), (h1, None)]) + f'<h1>{h1}</h1><p class="lead">{intro}</p>'
            f'<p>{jump}</p><p class="small muted">{esc(scenario_txt(data, lang))} {"Priset under varje bil gäller en bil som är tre år gammal, eller den nyaste årsmodellen om den saknas." if lang == "sv" else "The price under each car is for a three-year-old car, or the newest model year if there is none."}</p>'
            + "".join(secs))
    desc = {"sv": f"Alla {len(models)} bilmodeller i CarDep: SUV, kombi, sedan, halvkombi och sportbil, med månadskostnad, begagnatpriser och vanliga fel.",
            "en": f"All {len(models)} car models in CarDep: SUVs, estates, sedans, hatchbacks and sports cars, with monthly cost, used prices and common faults."}[lang]
    title = {"sv": "Alla bilar: månadskostnad och begagnatpriser | CarDep", "en": "All cars: monthly cost and used prices | CarDep"}[lang]
    ld = [crumbs_ld([("CarDep", P["home"][lang]), (h1, None)]),
          {"@type": "CollectionPage", "name": h1, "url": SITE + path, "inLanguage": lang}]
    return page(path, lang, alt, title, desc, body, current="cars", ld=ld)


# ---------- topplistor ----------
def rankings(data, lang):
    t = T[lang]
    path, alt = P["rank"][lang], P["rank"]["en" if lang == "sv" else "sv"]
    now = data["now"]
    used_year = now - 3
    L = {"sv": {"h1": "Topplistor", "lead": f"Bilarna som kostar minst per månad, och de som ger mest bil för pengarna. Listorna gäller bilar från {used_year}, alltså tre år gamla, och nya bilar.",
                "cheap": lambda k: f"Billigast att äga: {k}", "ev": f"Billigaste elbilarna från {used_year}", "value": f"Mest prisvärda bilarna från {used_year}",
                "new": "Billigaste nya bilarna", "rank": "Plats", "car": "Bil", "ver": "Version", "price": "Pris", "month": "Per månad", "grade": "Betyg",
                "valueNote": "Prisvärdhetsbetyget väger månadskostnaden mot kvalitet, säkerhet, komfort, utrymme och prestanda.",
                "title": "Topplistor: billigaste bilarna att äga per månad | CarDep",
                "desc": f"Vilka bilar kostar minst per månad? Topplistor över de billigaste SUV:arna, kombibilarna, elbilarna och nya bilarna att äga, och de mest prisvärda bilarna."},
         "en": {"h1": "Rankings", "lead": f"The cars that cost least per month, and the ones that give the most car for the money. The lists cover {used_year} cars, three years old, and new cars.",
                "cheap": lambda k: f"Cheapest to own: {k}", "ev": f"Cheapest electric cars from {used_year}", "value": f"Best value cars from {used_year}",
                "new": "Cheapest new cars", "rank": "Rank", "car": "Car", "ver": "Version", "price": "Price", "month": "Per month", "grade": "Grade",
                "valueNote": "The value grade weighs the monthly cost against quality, safety, comfort, space and performance.",
                "title": "Rankings: the cheapest cars to own per month | CarDep",
                "desc": "Which cars cost the least per month in Sweden? Rankings of the cheapest SUVs, estates, electric cars and new cars to own, and the best value cars."}}[lang]

    def table(rows, label):
        trs = "".join(f'<tr><td class="num">{i + 1}</td><td><a href="{rel(path, car_path(m["id"], lang))}">{esc(full_name(m, lang))}</a></td>'
                      f'<td>{esc(", ".join(r["version"]))}</td><td class="num">{kr(r["price"], lang)}</td><td class="num"><b>{kr(r["month"], lang)}</b></td>'
                      f'<td><span class="grade {r["grade"]}">{r["grade"]}</span></td></tr>' for i, (m, r) in enumerate(rows))
        return (f'<div class="tblwrap" tabindex="0" role="region" aria-label="{esc(label)}"><table class="tbl"><thead><tr><th class="num">{L["rank"]}</th><th>{L["car"]}</th><th>{L["ver"]}</th>'
                f'<th class="num">{L["price"]}</th><th class="num">{L["month"]}</th><th>{L["grade"]}</th></tr></thead><tbody>{trs}</tbody></table></div>')

    def rows_for(year, pred=lambda m, r: True):
        out = []
        for m in data["models"]:
            for r in m["rows"]:
                if r["year"] == year and not r.get("thin") and pred(m, r): out.append((m, r))
        return out

    secs = []
    for k in ["SUV", "Kombi", "Sedan", "Halvkombi"]:
        rs = sorted(rows_for(used_year, lambda m, r, k=k: m["type"] == k), key=lambda x: x[1]["month"])[:10]
        if rs: secs.append(f'<h2>{esc(L["cheap"](t["typePl"][k]))}</h2>' + table(rs, L["cheap"](t["typePl"][k])))
    ev = sorted(rows_for(used_year, lambda m, r: r["fuelType"] == "E"), key=lambda x: x[1]["month"])[:10]
    if ev: secs.append(f'<h2>{L["ev"]}</h2>' + table(ev, L["ev"]))
    val = sorted(rows_for(used_year), key=lambda x: (-x[1]["score"], x[1]["month"]))[:10]
    if val: secs.append(f'<h2>{L["value"]}</h2><p class="small muted">{L["valueNote"]}</p>' + table(val, L["value"]))
    new = sorted(rows_for(now), key=lambda x: x[1]["month"])[:10]
    if new: secs.append(f'<h2>{L["new"]}</h2>' + table(new, L["new"]))
    body = (crumbs(path, lang, [("CarDep", P["home"][lang]), (L["h1"], None)]) + f'<h1>{L["h1"]}</h1><p class="lead">{L["lead"]}</p>'
            f'<p class="small muted">{esc(scenario_txt(data, lang))}</p>' + "".join(secs) + f'<p class="updated">{t["updated"]} {TODAY} · {t["adData"]}</p>')
    ld = [crumbs_ld([("CarDep", P["home"][lang]), (L["h1"], None)])]
    return page(path, lang, alt, L["title"], L["desc"], body, current="rank", ld=ld)


# ---------- metod, om, integritet, villkor ----------
def prose_page(lang, key, title, desc, h1, html_body, current=None):
    t = T[lang]
    path, alt = P[key][lang], P[key]["en" if lang == "sv" else "sv"]
    body = (crumbs(path, lang, [("CarDep", P["home"][lang]), (h1, None)]) + f'<article class="prose"><h1>{h1}</h1>{html_body}'
            f'<p class="updated">{t["updated"]} {TODAY}</p></article>')
    return page(path, lang, alt, title, desc, body, current=current, ld=[crumbs_ld([("CarDep", P["home"][lang]), (h1, None)])])


def method(data, lang):
    path = P["method"][lang]
    how = data["how"][lang].replace('<div class="agecurve"></div>', f'<div class="agecurve">{data.get("age", {}).get(lang, "")}</div>')
    if lang == "sv":
        intro = (f'<p class="lead">Så räknar CarDep fram vad en bil kostar per månad, var siffrorna kommer ifrån och hur prisvärdhetsbetyget sätts.</p>'
                 f'<p>Månadskostnaden är allt du betalar för bilen under den tid du äger den, delat med antalet månader: värdeminskning, drivmedel eller el, '
                 f'service och reparationer, försäkring och fordonsskatt. Ränta på billån ingår inte. På modellsidorna räknar vi med {data["scenario"]["years"]} års ägande '
                 f'och {nf(data["scenario"]["mil"], "sv")} mil per år. I <a href="{rel(path, P["home"]["sv"])}">kalkylatorn</a> kan du ändra allt.</p>')
        return prose_page("sv", "method", "Så räknar vi: källor och beräkningar | CarDep",
                          "Så räknar CarDep ut månadskostnaden: värdeminskning ur annonspriser på Blocket, drivmedel, skatt, försäkring, service, vanliga fel och batteriåldring.",
                          "Så räknar vi", intro + how, current="method")
    intro = (f'<p class="lead">How CarDep works out what a car costs per month, where the numbers come from and how the value grade is set.</p>'
             f'<p>The monthly cost is everything you pay for the car while you own it, divided by the number of months: depreciation, fuel or electricity, '
             f'servicing and repairs, insurance and road tax. Loan interest is not included. The model pages assume {data["scenario"]["years"]} years of ownership '
             f'and {nf(data["scenario"]["mil"] * 10, "en")} km a year. In the <a href="{rel(path, P["home"]["en"])}">calculator</a> you can change everything.</p>')
    return prose_page("en", "method", "How we calculate: sources and methods | CarDep",
                      "How CarDep works out the monthly cost: depreciation from Blocket ad prices, fuel, tax, insurance, servicing, common faults and battery ageing.",
                      "How we calculate", intro + how, current="method")


def about(data, lang):
    path = P["about"][lang]
    n = len(data["models"]) if data else 189
    c, src = esc(CFG["kontakt_url"]), esc(CFG["kallkod_url"])
    if lang == "sv":
        body = (f'<p class="lead">CarDep visar vad en bil verkligen kostar per månad, inte bara vad den kostar att köpa.</p>'
                f'<p>Vi räknar ihop värdeminskning, drivmedel eller el, service och reparationer, försäkring och fordonsskatt för {n} bilmodeller som är vanliga i Sverige, '
                f'nya och begagnade från 2005 och framåt. Varje bil får också ett prisvärdhetsbetyg från A till E som väger kostnaden mot kvalitet, säkerhet, komfort, utrymme och prestanda.</p>'
                f'<p>Begagnatpriserna bygger på tiotusentals svenska annonser, i första hand på Blocket, och nypriserna på vad bilarna annonseras för hos svenska bilhandlare och på '
                f'Skatteverkets nybilsprislista. Exakt hur vi räknar står på sidan <a href="{rel(path, P["method"]["sv"])}">Så räknar vi</a>.</p>'
                f'<h2>Oberoende</h2><p>CarDep säljer inga bilar, försäkringar eller lån och tar inte betalt för placeringar. Det finns ingen reklam och inga affiliatelänkar, '
                f'och CarDep själv samlar inte in något om besökarna. Webbhotellet räknar besök, se <a href="{rel(path, P["privacy"]["sv"])}">integritetspolicyn</a>.</p>'
                f'<h2>Begränsningar</h2><p>Siffrorna är beräkningar och uppskattningar, inte offerter. Verkliga priser beror på miltal, skick, utrustning och var du köper bilen. '
                f'Kontrollera alltid bilen och priset innan du köper.</p>'
                f'<h2>Kontakt</h2><p>Hittar du ett fel eller saknar du en bil? Ring eller sms:a <a href="tel:{esc(CFG["telefon"])}">{esc(CFG["telefon_visning"])}</a>, eller <a href="{c}" rel="noopener">skriv till oss på GitHub</a>. '
                f'Koden till webbplatsen finns öppet på <a href="{src}" rel="noopener">GitHub</a>.</p>')
        return prose_page("sv", "about", "Om CarDep | CarDep", "CarDep är en oberoende tjänst som visar vad bilar kostar per månad i Sverige, utan reklam och utan affiliatelänkar.", "Om CarDep", body)
    body = (f'<p class="lead">CarDep shows what a car really costs per month, not just what it costs to buy.</p>'
            f'<p>We add up depreciation, fuel or electricity, servicing and repairs, insurance and road tax for {n} car models that are common in Sweden, '
            f'new and used from 2005 onwards. Every car also gets a value grade from A to E that weighs the cost against quality, safety, comfort, space and performance.</p>'
            f'<p>Used prices are based on tens of thousands of Swedish ads, mainly on Blocket, and new prices on what Swedish dealers advertise the cars for and on the '
            f'Swedish Tax Agency\'s new car price list. The page <a href="{rel(path, P["method"]["en"])}">How we calculate</a> explains the details.</p>'
            f'<h2>Independent</h2><p>CarDep does not sell cars, insurance or loans and does not take payment for placements. There are no ads and no affiliate links, '
            f'and CarDep itself collects nothing about visitors. The host counts visits, see the <a href="{rel(path, P["privacy"]["en"])}">privacy policy</a>.</p>'
            f'<h2>Limitations</h2><p>The numbers are calculations and estimates, not quotes. Real prices depend on mileage, condition, equipment and where you buy. '
            f'Always check the car and the price before you buy.</p>'
            f'<h2>Contact</h2><p>Found a mistake or missing a car? Call or text <a href="tel:{esc(CFG["telefon"])}">{esc(CFG["telefon_visning"])}</a>, or <a href="{c}" rel="noopener">write to us on GitHub</a>. '
            f'The code for the site is openly available on <a href="{src}" rel="noopener">GitHub</a>.</p>')
    return prose_page("en", "about", "About CarDep | CarDep", "CarDep is an independent service that shows what cars cost per month in Sweden, with no ads and no affiliate links.", "About CarDep", body)


def privacy(lang):
    path = P["privacy"][lang]
    c = esc(CFG["kontakt_url"])
    gh = "https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement"
    an = "https://www.anthropic.com/legal/privacy"
    chat_on = bool(CFG.get("chatt_url"))
    if lang == "sv":
        chat = (f'<h2>AI-chatten</h2><p>{"Chatten är påslagen." if chat_on else "När chatten är påslagen gäller följande."} Din fråga och det du ser i kalkylatorn just då '
                f'(dina inställningar och bilarna i listan) skickas till CarDeps server och vidare till Anthropic, som tillhandahåller AI-modellen Claude, för att ett svar ska kunna skrivas. '
                f'Anthropic behandlar uppgifterna enligt <a href="{an}" rel="noopener">sin integritetspolicy</a>. Vi sparar inte samtalen. Skriv inte personuppgifter i chatten. '
                f'För att förhindra missbruk räknar servern hur många frågor som kommer från varje IP-adress under en timme. Det hålls bara i minnet och sparas inte.</p>')
        body = (f'<p class="lead">Kort sagt: CarDep visar ingen reklam, säljer inga uppgifter och samlar själv inte in personuppgifter om dig. Webbhotellet Lovable räknar besök med en egen kaka som gäller i 30 minuter.</p>'
                f'<h2>Det här sparas på din enhet</h2><p>Om webbläsaren stöder det sparar sidan kopior av sidor, bilder och typsnitt i webbläsarens cache, så att CarDep laddar snabbare '
                f'och fungerar utan uppkoppling. Inget av det skickas till oss, och du tar bort det genom att rensa webbplatsdata i webbläsaren.</p>'
                f'<h2>Webbhotellet och besöksstatistik</h2><p>Webbplatsen cardep.se ligger hos <a href="https://lovable.dev" rel="noopener">Lovable</a>. Lovable lägger till ett eget skript på varje sida som räknar besök. Det sätter kakan <code>session-id</code> med ett slumpat id som gäller i 30 minuter, och skickar till Lovable vilka sidor du visar, vilken sida du kom ifrån, webbläsare och språk, och hur snabbt sidan laddades. Som alla webbservrar registrerar Lovable också tekniska uppgifter, till exempel IP-adress, för säkerhet och drift. Lovable behandlar uppgifterna enligt <a href="https://lovable.dev/privacy" rel="noopener">sin integritetspolicy</a>. Vi ser bara sammanställd statistik, till exempel antal besök, och kan inte koppla den till dig. Vill du slippa kakan kan du blockera kakor för cardep.se i webbläsaren; sidan fungerar ändå.</p><p>En kopia av webbplatsen finns också hos GitHub Pages, som drivs av GitHub, Inc. i USA. Där sätts inga kakor, men GitHub registrerar tekniska uppgifter enligt <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHubs integritetspolicy</a>.</p>'
                f'<h2>Typsnitt och länkar</h2><p>Typsnitten ligger på samma server som sidan, så inga uppgifter skickas till Google eller andra tredje parter när du visar CarDep. '
                f'Länkar till andra webbplatser, till exempel källor och fotografernas sidor, öppnas först när du klickar på dem.</p>'
                f'{chat}<h2>Dina rättigheter</h2><p>Eftersom vi själva inte sparar personuppgifter om dig finns det normalt inget hos oss att lämna ut eller radera. Frågor om besöksstatistiken kan du också ställa direkt till Lovable på <a href="mailto:privacy@lovable.dev">privacy@lovable.dev</a>. Har du frågor kan du ringa <a href="tel:{esc(CFG["telefon"])}">{esc(CFG["telefon_visning"])}</a> eller <a href="{c}" rel="noopener">kontakta oss på GitHub</a>. Du kan också vända dig till <a href="https://www.imy.se" rel="noopener">Integritetsskyddsmyndigheten (IMY)</a>.</p>')
        return prose_page("sv", "privacy", "Integritetspolicy | CarDep", "Vilka uppgifter som hanteras när du besöker CarDep: besöksstatistik hos webbhotellet, cache på din enhet och AI-chatten.", "Integritetspolicy", body)
    chat = (f'<h2>The AI chat</h2><p>{"The chat is switched on." if chat_on else "When the chat is switched on, the following applies."} Your question and what you see in the calculator at that moment '
            f'(your settings and the cars in the list) are sent to CarDep\'s server and on to Anthropic, which provides the AI model Claude, so that an answer can be written. '
            f'Anthropic processes the data under <a href="{an}" rel="noopener">its privacy policy</a>. We do not store the conversations. Do not write personal information in the chat. '
            f'To prevent abuse, the server counts how many questions come from each IP address within an hour. This is only kept in memory and is not stored.</p>')
    body = (f'<p class="lead">In short: CarDep shows no ads, sells no data and does not itself collect personal information about you. The host, Lovable, counts visits with its own cookie that lasts 30 minutes.</p>'
            f'<h2>What is stored on your device</h2><p>If your browser supports it, the site keeps copies of pages, pictures and fonts in the browser cache, so that CarDep loads faster '
            f'and works offline. None of it is sent to us, and you remove it by clearing the site data in your browser.</p>'
            f'<h2>Hosting and visitor statistics</h2><p>The site cardep.se is hosted by <a href="https://lovable.dev" rel="noopener">Lovable</a>. Lovable adds its own script to every page that counts visits. It sets the cookie <code>session-id</code> with a random id that lasts 30 minutes, and sends Lovable which pages you view, which page you came from, your browser and language, and how fast the page loaded. Like all web servers, Lovable also records technical data such as your IP address for security and operations. Lovable processes the data under <a href="https://lovable.dev/privacy" rel="noopener">its privacy policy</a>. We only see combined statistics, such as the number of visits, and cannot link them to you. To avoid the cookie, block cookies for cardep.se in your browser; the site still works.</p><p>A copy of the site is also on GitHub Pages, run by GitHub, Inc. in the USA. It sets no cookies, but GitHub records technical data under <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub\'s privacy statement</a>.</p>'
            f'<h2>Fonts and links</h2><p>The fonts are on the same server as the site, so nothing is sent to Google or other third parties when you view CarDep. '
            f'Links to other sites, such as sources and photographers\' pages, only open when you click them.</p>'
            f'{chat}<h2>Your rights</h2><p>As we do not ourselves store personal information about you, there is normally nothing for us to hand over or delete. Questions about the visitor statistics can also go straight to Lovable at <a href="mailto:privacy@lovable.dev">privacy@lovable.dev</a>. If you have questions, call <a href="tel:{esc(CFG["telefon"])}">{esc(CFG["telefon_visning"])}</a> or <a href="{c}" rel="noopener">contact us on GitHub</a>. You can also contact the Swedish Authority for Privacy Protection, <a href="https://www.imy.se/en/" rel="noopener">IMY</a>.</p>')
    return prose_page("en", "privacy", "Privacy policy | CarDep", "What data is handled when you visit CarDep: visitor statistics at the host, the cache on your device and the AI chat.", "Privacy policy", body)


def terms(lang):
    path = P["terms"][lang]
    if lang == "sv":
        body = (f'<p class="lead">CarDep ger allmän information om vad bilar kostar. Den är gratis att använda, men vi lämnar inga garantier.</p>'
                f'<h2>Uppskattningar, inte rådgivning</h2><p>Priser, månadskostnader, betyg, risker för fel och övriga siffror är beräkningar och uppskattningar utifrån annonsdata, '
                f'offentliga prislistor och våra egna antaganden. De är inte offerter och inte ekonomisk rådgivning. Kontrollera alltid bilen, priset, försäkringen och finansieringen '
                f'innan du köper. Vi ansvarar inte för beslut som fattas utifrån informationen på sidan.</p>'
                f'<h2>Annonsdata</h2><p>Begagnatpriserna är sammanställningar, till exempel medianpriser per årsmodell, av offentliga annonser. Vi visar inte enskilda annonser. '
                f'CarDep har ingen koppling till Blocket, AutoUncle, Skatteverket eller biltillverkarna.</p>'
                f'<h2>Varumärken och bilder</h2><p>Bilmärken och modellnamn tillhör sina ägare och används bara för att beskriva bilarna. Fotona tillhör fotograferna och används '
                f'enligt sina fria licenser, se <a href="{rel(path, P["credits"]["sv"])}">Bildkällor</a>. Typsnitten används enligt SIL Open Font License.</p>'
                f'<h2>Ändringar</h2><p>Innehållet och de här villkoren kan ändras. Den version som ligger på sidan gäller.</p>')
        return prose_page("sv", "terms", "Villkor och ansvarsfriskrivning | CarDep", "Villkor för att använda CarDep: siffrorna är uppskattningar, inte offerter eller ekonomisk rådgivning.", "Villkor och ansvarsfriskrivning", body)
    body = (f'<p class="lead">CarDep gives general information about what cars cost. It is free to use, but we give no guarantees.</p>'
            f'<h2>Estimates, not advice</h2><p>Prices, monthly costs, grades, fault risks and other figures are calculations and estimates based on ad data, public price lists '
            f'and our own assumptions. They are not quotes and not financial advice. Always check the car, the price, the insurance and the financing before you buy. '
            f'We are not responsible for decisions made on the basis of the information on the site.</p>'
            f'<h2>Ad data</h2><p>Used prices are summaries, such as median prices by model year, of public ads. We do not show individual ads. '
            f'CarDep has no connection with Blocket, AutoUncle, the Swedish Tax Agency or the car makers.</p>'
            f'<h2>Trademarks and pictures</h2><p>Car brands and model names belong to their owners and are only used to describe the cars. The photos belong to the photographers '
            f'and are used under their free licences, see <a href="{rel(path, P["credits"]["en"])}">Image credits</a>. The fonts are used under the SIL Open Font License.</p>'
            f'<h2>Changes</h2><p>The content and these terms may change. The version on the site applies.</p>')
    return prose_page("en", "terms", "Terms and disclaimer | CarDep", "Terms for using CarDep: the figures are estimates, not quotes or financial advice.", "Terms and disclaimer", body)


def credits_page(data, lang):
    path = P["credits"][lang]
    rows = []
    for m in sorted(data["models"], key=lambda m: full_name(m, lang).lower()):
        ph = m["photo"]
        if not ph: continue
        lic = f'<a href="{LIC_URL[ph["license"]]}" rel="license noopener">{esc(ph["license"])}</a>' if ph["license"] in LIC_URL else esc(ph["license"])
        change = {"sv": "bakgrund borttagen, beskuren", "en": "background removed, cropped"}[lang]
        rows.append(f'<tr><td><a href="{rel(path, car_path(m["id"], lang))}">{esc(full_name(m, lang))}</a></td><td>{esc(ph["artist"])}</td>'
                    f'<td>{lic}</td><td><a href="{esc(commons(ph["file"]))}" rel="noopener">{esc(ph["file"].replace("_", " "))}</a></td><td>{change}</td></tr>')
    n3 = sum(1 for m in data["models"] if not m["photo"] and m["img3d"])
    if lang == "sv":
        intro = (f'<p class="lead">Fotona på CarDep kommer från Wikimedia Commons och är fritt licensierade. Här står fotograf, licens och källa för varje foto.</p>'
                 f'<p>Vi har tagit bort bakgrunden och beskurit fotona så att alla bilar visas likadant. Ändrade foton under CC BY-SA delas under samma licens. '
                 f'{n3} modeller utan fritt foto visas med en datorgenererad bild som vi har gjort själva. Typsnitten Archivo, IBM Plex Sans och IBM Plex Mono används enligt SIL Open Font License.</p>')
        head = "<th>Bil</th><th>Fotograf</th><th>Licens</th><th>Källa</th><th>Ändring</th>"
        title, desc, h1 = "Bildkällor | CarDep", "Fotograf, licens och källa för fotona på CarDep. Alla foton kommer från Wikimedia Commons och är fritt licensierade.", "Bildkällor"
    else:
        intro = (f'<p class="lead">The photos on CarDep come from Wikimedia Commons and are freely licensed. This page lists the photographer, licence and source for each photo.</p>'
                 f'<p>We removed the background and cropped the photos so that all cars are shown the same way. Modified photos under CC BY-SA are shared under the same licence. '
                 f'{n3} models with no free photo are shown with a computer-generated picture we made ourselves. The fonts Archivo, IBM Plex Sans and IBM Plex Mono are used under the SIL Open Font License.</p>')
        head = "<th>Car</th><th>Photographer</th><th>Licence</th><th>Source</th><th>Change</th>"
        title, desc, h1 = "Image credits | CarDep", "Photographer, licence and source for the photos on CarDep. All photos come from Wikimedia Commons and are freely licensed.", "Image credits"
    body = intro + f'<div class="tblwrap" tabindex="0" role="region" aria-label="{esc(h1)}"><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    return prose_page(lang, "credits", title, desc, h1, body)


def not_found():
    """404-sidan visas för alla adresser som saknas, så den har absoluta länkar"""
    body = f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sidan finns inte | CarDep</title><meta name="robots" content="noindex">
<link rel="icon" href="{SITE}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{SITE}assets/site.css">
</head>
<body>
<header class="topbar gut"><div class="shell"><a class="logo" href="{SITE}">{LOGO}CarDep</a></div></header>
<main class="gut"><div class="shell prose">
<h1>Sidan finns inte</h1>
<p class="lead">Adressen kan vara fel, eller så har sidan flyttat.</p>
<div class="btns"><a class="btn" href="{SITE}">Till kalkylatorn</a><a class="btn ghost" href="{SITE}{P['cars']['sv']}">Alla bilar</a></div>
<p lang="en">Page not found. <a href="{SITE}en/">Go to the calculator in English</a>.</p>
</div></main>
</body>
</html>
"""
    (APP / "404.html").write_text(body, encoding="utf-8")


# ---------- sitemap, robots, manifest, service worker, chattkatalog ----------
def sitemap(paths_by_key):
    """paths_by_key: [(sv-sökväg, en-sökväg)] — varje sida med sin motsvarighet på det andra språket"""
    urls = []
    for sv, en in paths_by_key:
        alt = f'<xhtml:link rel="alternate" hreflang="sv" href="{esc(SITE + sv)}"/><xhtml:link rel="alternate" hreflang="en" href="{esc(SITE + en)}"/>'
        for p in (sv, en):
            urls.append(f"<url><loc>{esc(SITE + p)}</loc><lastmod>{TODAY}</lastmod>{alt}</url>")
    (APP / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                     'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
    (APP / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")


def manifests():
    for lang, folder, up in (("sv", "", ""), ("en", "en/", "../")):
        man = {"name": "CarDep – " + T[lang]["tagline"], "short_name": "CarDep", "description": T[lang]["siteDesc"], "lang": lang,
               "start_url": "./", "scope": up or "./", "display": "standalone", "background_color": "#f1f3f0", "theme_color": "#0f6b52",
               "icons": [{"src": f"{up}icon-192.png", "sizes": "192x192", "type": "image/png"},
                         {"src": f"{up}icon-512.png", "sizes": "512x512", "type": "image/png"},
                         {"src": f"{up}icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
        (APP / folder / "manifest.webmanifest").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")


def service_worker(version):
    core = ["./", "en/", "bil/", "en/cars/", "assets/site.css", "assets/fonts.css", "assets/site.js", "assets/fonts/archivo.woff2",
            "assets/fonts/ibm-plex-sans.woff2", "assets/fonts/ibm-plex-mono.woff2", "favicon.svg", "manifest.webmanifest"]
    js = f"""/* CarDep service worker: sidan laddar snabbare och fungerar utan uppkoppling.
   Sidor: nätet först, sparad kopia om nätet saknas. Bilder och typsnitt: sparad kopia först. Chatten (/api/) går aldrig via cachen. */
const V="cardep-{version}",IMG="cardep-img-1",CORE={json.dumps(core)};
self.addEventListener("install",e=>{{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))}});
self.addEventListener("activate",e=>{{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V&&k!==IMG).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))}});
async function trim(c,max){{const ks=await c.keys();for(let i=0;i<ks.length-max;i++)await c.delete(ks[i])}}
self.addEventListener("fetch",e=>{{
  const r=e.request,u=new URL(r.url);
  if(r.method!=="GET"||u.origin!==location.origin||u.pathname.includes("/api/"))return;
  if(r.mode==="navigate"){{
    e.respondWith(fetch(r).then(res=>{{if(res.ok){{const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}}return res}})
      .catch(()=>caches.match(r,{{ignoreSearch:true}}).then(m=>m||caches.match(new URL("./",location).href))));
    return;
  }}
  if(u.pathname.includes("/img/")||u.pathname.includes("/og/")){{
    e.respondWith(caches.open(IMG).then(c=>c.match(r).then(m=>m||fetch(r).then(res=>{{if(res.ok){{c.put(r,res.clone());trim(c,400)}}return res}}))));
    return;
  }}
  e.respondWith(caches.match(r).then(m=>m||fetch(r)));
}});
"""
    (APP / "sw.js").write_text(js, encoding="utf-8")
    (APP / "cardep-sw.js").write_text(js, encoding="utf-8")   # sajten registrerar cardep-sw.js; sw.js finns kvar för äldre besökare


def site_js():
    js = """/* CarDep: registrerar service workern (snabbare laddning och fungerar utan uppkoppling) på publicerade sidor */
(function(){
  if(!("serviceWorker" in navigator)||location.protocol!=="https:")return;
  var s=document.currentScript&&document.currentScript.src;if(!s)return;
  addEventListener("load",function(){navigator.serviceWorker.register(new URL("../cardep-sw.js",s).href).catch(function(){})});
})();
"""
    (APP / "assets" / "site.js").write_text(js, encoding="utf-8")


def lease_cat(data, m):
    c = m.get("lease")
    if not c:
        return ""
    return (f'; privatleasing: {c["n"]}, {c["v"]}, {kr(c["fee"], "sv")}/mån i {c["mon"]} mån och {c["mil"]} mil/år'
            f'{", service ingår" if c["svc"] else ", service ingår inte"}{", förhöjd första hyra " + kr(c["first"], "sv") if c["first"] else ""}'
            f'{", obligatorisk försäkring genom leasingbolaget " + kr(c["ins"], "sv") + "/mån" if c.get("ins") else ""}; '
            f'leasa allt inräknat {kr(c["lease"]["month"], "sv")}/mån, köpa ny för {kr(c["price"], "sv")} och sälja efter {c["mon"] // 12} år '
            f'{kr(c["buy"]["month"], "sv")}/mån')


def catalogue(data):
    """Chattens underlag: alla modeller med priser, månadskostnad, begagnatpriser och vanliga fel (server.py läser katalog.txt)"""
    lines = [f"Standardfall för månadskostnaden: {data['scenario']['years']} års ägande, {data['scenario']['mil']} mil per år, "
             f"bensin {data['fuel']['pB']} kr/l, diesel {data['fuel']['pD']} kr/l, el {data['fuel']['pE']} kr/kWh ({data['fuel']['updated']}).",
             f"Privatleasing: märkenas egna erbjudanden, avlästa {lease_dates(data['lease'], 'sv')}. Jämförelsen leasa eller köpa gäller samma version ny under "
             f"avtalstiden, vid {data['lease']['mil']} mil per år och {data['lease']['rate']} % ränta på pengarna vid köp; köpet sker till listpriset (eller annonspriset om det är lägre) "
             f"och säljs efter avtalstiden till annonspriset."]
    for m in data["models"]:
        eng = "; ".join(f'{o["n"]} ({T["sv"]["fuel"].get(o.get("f"), "")}{", " + str(o["hp"]) + " hk" if o.get("hp") else ""}'
                        f'{", från " + str(o["y"]) if o.get("y") else ""}{", till " + str(o["to"]) if o.get("to") else ""})' for o in m["groups"][0]["o"])
        rows = "; ".join(f'{r["year"]} ({", ".join(r["version"])}): pris {kr(r["price"], "sv")}, {kr(r["month"], "sv")}/mån, betyg {r["grade"]}' for r in m["rows"])
        used = ", ".join(f"{o[0]}: {kr(o[1], 'sv')}" for o in sorted((m.get("market") or {}).get("obs", []), key=lambda o: -o[0])[:8])
        faults = ", ".join(f'{f["sv"]} (ca {kr(f["cost"], "sv")})' for f in m["faults"])
        newp = f'nypris från {kr(m["newFrom"], "sv")}' if m["newFrom"] else f'senaste nypris {kr(m["listPrice"], "sv")}'
        lines.append(f'{full_name(m, "sv")} [{m["type"]}, årsmodell {years_txt(m, "sv")}]: {newp}; motorer: {eng}; månadskostnad: {rows}; '
                     f'försäkring ca {kr(m["ins"], "sv")}/år; service ca {kr(m["svc"], "sv")}/år; driftsäkerhet {m["rel"]}/5; Euro NCAP {m["ncap"] or "–"}; '
                     f'garanti {m["war"]} år; bagage {m["trunk"]} l' + (f"; begagnatpriser i annonser (median): {used}" if used else "")
                     + (f"; vanliga fel: {faults}" if faults else "") + lease_cat(data, m) + f'. Fördel: {m["pro"]["sv"]} Nackdel: {m["con"]["sv"]}')
    (ROOT / "katalog.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_all(data):
    """alla statiska sidor; returnerar [(sv, en)] för sitemap"""
    pairs = [(P["home"]["sv"], P["home"]["en"])]
    if data:
        for m in data["models"]:
            sim = similar_to(m, data["models"])
            for lang in LANGS:
                model_page(data, m, lang, sim)
            pairs.append((car_path(m["id"], "sv"), car_path(m["id"], "en")))
        for lang in LANGS:
            cars_index(data, lang); rankings(data, lang); lease_page(data, lang); method(data, lang); credits_page(data, lang)
        pairs += [(P[k]["sv"], P[k]["en"]) for k in ("cars", "rank", "lease", "method", "credits")]
        catalogue(data)
    for lang in LANGS:
        about(data, lang); privacy(lang); terms(lang)
    pairs += [(P[k]["sv"], P[k]["en"]) for k in ("about", "privacy", "terms")]
    not_found(); manifests(); site_js(); sitemap(pairs)
    version = hashlib.sha256(json.dumps(pairs).encode() + (data and json.dumps(data["fuel"]).encode() or b"") + TODAY.encode()).hexdigest()[:10]
    service_worker(version)
    return pairs
