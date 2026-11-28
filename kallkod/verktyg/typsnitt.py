"""Hämtar typsnitten (Archivo, IBM Plex Sans, IBM Plex Mono; SIL Open Font License) till app/assets/fonts,
så att sidan inte laddar något från Google när den visas. Körs en gång, eller om typsnitten ska bytas.

    python3 verktyg/typsnitt.py
"""
import pathlib, re, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "app" / "assets" / "fonts"
CSS_URL = ("https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800"
           "&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"}
LICENSES = {"Archivo": "https://raw.githubusercontent.com/google/fonts/main/ofl/archivo/OFL.txt",
            "IBM Plex Sans": "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsans/OFL.txt",
            "IBM Plex Mono": "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/OFL.txt"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    css = get(CSS_URL).decode()
    faces = {}
    for sub, block in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face\s*\{[^}]*\})", css):
        if sub != "latin":          # å, ä, ö och é ingår i latin
            continue
        fam = re.search(r"font-family: '([^']+)'", block).group(1)
        w = int(re.search(r"font-weight: (\d+)", block).group(1))
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        rng = re.search(r"unicode-range: ([^;]+);", block).group(1)
        f = faces.setdefault((fam, url), {"w": [], "range": rng})
        f["w"].append(w)
    rules = []
    for (fam, url), f in faces.items():
        name = fam.lower().replace(" ", "-") + ".woff2"
        (OUT / name).write_bytes(get(url))
        lo, hi = min(f["w"]), max(f["w"])
        weight = str(lo) if lo == hi else f"{lo} {hi}"     # variabla typsnitt: ett intervall
        rules.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{weight};font-display:swap;"
                     f"src:url(fonts/{name}) format('woff2');unicode-range:{f['range']}}}")
        print(f"{fam:14} {weight:8} -> {name}")
    (OUT.parent / "fonts.css").write_text("/* Typsnitt under SIL Open Font License 1.1, se fonts/OFL-*.txt */\n" + "\n".join(rules) + "\n")
    for fam, url in LICENSES.items():
        (OUT / ("OFL-" + fam.lower().replace(" ", "-") + ".txt")).write_bytes(get(url))


if __name__ == "__main__":
    main()
