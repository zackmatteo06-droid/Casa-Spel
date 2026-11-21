"""Kopierar den byggda webbplatsen (app/) till en lokal kopia av GitHub-repot som publiceras med GitHub Pages.

    python3 bygg.py
    python3 publicera.py ../../Casa-Spel            # webbplatsen hamnar i Casa-Spel/bilkollen/
    python3 publicera.py ../../Casa-Spel --mapp .   # eller i repots rot (t.ex. med egen domän)

Filer som inte längre finns i app/ tas bort i målmappen, så borttagna sidor försvinner också från webbplatsen.
404.html och .nojekyll läggs i repots rot, där GitHub Pages letar efter dem. Sedan återstår bara att committa och
pusha repot, till exempel med GitHub Desktop.
"""
import argparse, filecmp, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent
APP = ROOT / "app"
SKIP = {"bilkalkyl.html"}                   # källfilen; de byggda sidorna räcker
SKIP_PREFIX = ("assets/_",)                 # tillfälliga testfiler


def files(base):
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.name != ".DS_Store":
            yield p.relative_to(base).as_posix()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="sökväg till den lokala kopian av GitHub-repot")
    ap.add_argument("--mapp", default="bilkollen", help="mapp i repot för webbplatsen (standard: bilkollen)")
    a = ap.parse_args()
    repo = pathlib.Path(a.repo).resolve()
    if not (repo / ".git").exists():
        sys.exit(f"{repo} är inte ett git-repo")
    dest = (repo / a.mapp).resolve()
    if repo not in dest.parents and dest != repo:
        sys.exit("målmappen måste ligga i repot")
    if not (APP / "index.html").exists():
        sys.exit("kör python3 bygg.py först")
    want = [f for f in files(APP) if f not in SKIP and not f.startswith(SKIP_PREFIX)]
    copied = 0
    for f in want:
        src, dst = APP / f, dest / f
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst); copied += 1
    removed = 0
    if dest != repo:                         # i repots rot rör vi bara filer som webbplatsen själv har lagt dit
        keep = set(want)
        for f in list(files(dest)):
            if f not in keep:
                (dest / f).unlink(); removed += 1
        for d in sorted((p for p in dest.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
            if not any(d.iterdir()): d.rmdir()
    shutil.copy2(APP / "404.html", repo / "404.html")
    (repo / ".nojekyll").write_text("")
    print(f"{len(want)} filer i {dest}: {copied} nya eller ändrade, {removed} borttagna. 404.html och .nojekyll i {repo}.")
    print("Committa och pusha repot, till exempel med GitHub Desktop.")


if __name__ == "__main__":
    main()
