"""Bygger hela webbplatsen i app/ från källfilen app/bilkalkyl.html:

    app/index.html, app/en/index.html   kalkylatorn på svenska och engelska
    app/bil/<modell>/, app/en/cars/...  en sida per bilmodell (månadskostnad, begagnatpriser, motorer, vanliga fel)
    app/bil/, app/topplistor/, app/leasing/, app/metod/, app/om/, app/integritet/, app/villkor/, app/bildkallor/ (och engelska motsvarigheter)
    app/404.html, sitemap.xml, robots.txt, manifest.webmanifest, sw.js, assets/site.js
    katalog.txt                         chattens underlag om alla bilar (läses av server.py)

    python3 bygg.py

Modellsidorna räknas med appens egen kalkyl via macOS inbyggda JavaScript (osascript). Utan macOS byggs allt utom
modellsidorna och topplistorna. Adressen, chattens adress och kontaktlänken står i sajt.json.
"""
import json, re, shutil, subprocess, sys

from sajt import data as sdata, sidor
from sajt.sidor import APP, P, SITE, CFG, T, esc, rel, head_common, csp, script_hashes, chat_origin, crumbs_ld

src = (APP / "bilkalkyl.html").read_text(encoding="utf-8")
assert 'const LANG_DEFAULT="sv";' in src
cut = src.index("</style>") + len("</style>")        # första <style> i <head>, resten i <body>

BASE_STYLE = ('<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
              'body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style>')
NAV_STYLE = ('<style>.hnav{display:flex;align-items:center;gap:18px;margin:0 auto 0 28px;font-size:.9rem}'
             '.hnav a{color:var(--ink);text-decoration:none;font-weight:500}.hnav a:hover{color:var(--accent);text-decoration:underline}'
             '@media (max-width:900px){.hnav{display:none}}'
             '.fnav{display:flex;flex-wrap:wrap;gap:6px 18px;margin:0 0 14px;font-size:.88rem}.fnav a{color:var(--muted)}'
             '.nojs{max-width:640px;margin:24px auto;padding:0 16px}</style>')


def app_page(lang, i18n=None):
    path, alt = P["home"][lang], P["home"]["en" if lang == "sv" else "sv"]
    t = T[lang]
    title = {"sv": "CarDep – vad kostar bilen egentligen per månad?", "en": "CarDep – what does the car really cost per month?"}[lang]
    desc = t["siteDesc"]
    code = src if lang == "sv" else src.replace('const LANG_DEFAULT="sv";', 'const LANG_DEFAULT="en";')
    head_src, body_src = code[:cut], code[cut:]
    if lang == "en" and i18n:
        # fasta texter (data-t) på engelska redan i HTML-koden, för sökmotorer och innan skriptet har körts
        def tr(m):
            k = m.group(3)
            return m.group(1) + (esc(i18n[k]) if k in i18n and "<" not in i18n[k] else m.group(4)) + m.group(5)
        body_src = re.sub(r'(<(\w+)\b[^>]*\bdata-t="(\w+)"[^>]*>)([^<]*)(</\2>)', tr, body_src)
        body_src = body_src.replace('<output id="yearsOut" for="years">5 år</output>', '<output id="yearsOut" for="years">5 years</output>', 1)
    # typsnitten ligger lokalt (inga anrop till Google), titeln och artefaktens meta-tagg ersätts
    head_src = re.sub(r'<link rel="preconnect"[^>]*>\n?', "", head_src)
    head_src = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', "", head_src)
    head_src = re.sub(r"<title>.*?</title>\n?", "", head_src, count=1)
    head_src = re.sub(r'<meta name="claude:[^>]*>\n?', "", head_src)
    page_cfg = {"lang": lang, "alt": rel(path, alt), "img": rel(path, "img/bilar/"), "cars": rel(path, P["cars"][lang]),
                "chat": CFG.get("chatt_url") or None, "title": title}
    ld = [{"@type": "WebSite", "name": "CarDep", "url": SITE, "inLanguage": lang, "description": desc},
          {"@type": "WebApplication", "name": "CarDep", "url": SITE + path, "applicationCategory": "FinanceApplication",
           "operatingSystem": "Alla" if lang == "sv" else "Any", "inLanguage": lang, "description": desc,
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}},
          {"@type": "Organization", "name": "CarDep", "url": SITE, "logo": SITE + "icon-512.png"}]
    og = "og/cardep.png" if lang == "sv" else "og/cardep-en.png"
    head = head_common(path, lang, title, desc, alt, og,
                       extra=(f'<link rel="stylesheet" href="{rel(path, "assets/fonts.css")}">\n'
                              f'<meta http-equiv="Content-Security-Policy" content="__CSP__">\n'
                              f'<script type="application/json" id="bk-page">{json.dumps(page_cfg, ensure_ascii=False)}</script>\n'
                              f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": ld}, ensure_ascii=False)}</script>\n'
                              f'<script src="{rel(path, "assets/site.js")}" defer></script>\n{BASE_STYLE}\n{NAV_STYLE}'))
    # meny i toppen och länkar i sidfoten
    hnav = "".join(f'<a href="{rel(path, P[k][lang])}">{t[k]}</a>' for k in ("cars", "rank", "lease", "method"))
    body_src = body_src.replace('    <div class="tright">', f'    <nav class="hnav" aria-label="{t["navAria"]}">{hnav}</nav>\n    <div class="tright">', 1)
    fnav = "".join(f'<a href="{rel(path, P[k][lang])}">{t[k]}</a>' for k in ("cars", "rank", "lease", "method", "about", "privacy", "terms", "credits"))
    fnav += f'<a href="{esc(CFG["kontakt_url"])}" rel="noopener">{t["contact"]}</a>'
    if CFG.get("telefon"):
        fnav += f'<a href="tel:{esc(CFG["telefon"])}">{esc(CFG["telefon_visning"])}</a>'
    body_src = body_src.replace('<footer class="foot gut">\n  <div class="shell">', f'<footer class="foot gut">\n  <div class="shell">\n    <nav class="fnav" aria-label="{t["footAria"]}">{fnav}</nav>', 1)
    nojs = {"sv": f'Kalkylatorn behöver JavaScript. Du kan ändå läsa om varje bil under <a href="{rel(path, P["cars"]["sv"])}">Alla bilar</a>.',
            "en": f'The calculator needs JavaScript. You can still read about every car under <a href="{rel(path, P["cars"]["en"])}">All cars</a>.'}[lang]
    doc = (f'<!doctype html>\n<html lang="{lang}">\n<head>\n{head}\n' + head_src + "\n</head>\n<body>\n"
           f'<noscript><p class="nojs">{nojs}</p></noscript>\n' + body_src + "\n</body>\n</html>\n")
    doc = doc.replace("__CSP__", csp(script_hashes(doc), chat_origin()), 1)
    out = APP / path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")


def main():
    data = sdata.load()
    for lang in ("sv", "en"):
        app_page(lang, (data or {}).get("i18n"))
    pairs = sidor.build_all(data)
    n = sum(1 for _ in APP.rglob("index.html"))
    print(f"byggde {n} sidor i {APP} ({len(pairs)} sidpar i sitemap.xml)" + ("" if data else ", utan modellsidor"))
    # syntaxkontroll av appens skript om Node.js finns
    if shutil.which("node"):
        js = "\n".join(re.findall(r"<script>(.*?)</script>", src, re.S))
        tmp = APP.parent / ".check.js"
        tmp.write_text(js, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
        tmp.unlink()
        print("script syntax:", "OK" if r.returncode == 0 else r.stderr[:400])


if __name__ == "__main__":
    main()
