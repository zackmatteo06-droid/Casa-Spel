"""Read the model list straight out of the app (../app/index.html) and save models.json for the generator.
Run it again after adding or changing models in app/bilkalkyl.html (and building index.html with ../bygg.py)."""
import json, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
APP = HERE.parent / "app" / "index.html"
JS = r'''()=>MODELS.map(m=>{
  const rims=new Set();
  m.g.forEach(g=>g.o.forEach(o=>{(o.d||"").split(", ").forEach(x=>{const r=/^(\d+)-tumsfälg$/i.exec(x);if(r)rims.add(+r[1])})}));
  const f=m.g[0].o.map(o=>o.f);
  return {id:m.id,b:m.b,n:m.n,t:m.t,from:m.from,to:m.to||null,col:m.col,cm:CM[m.id]||null,
    fuels:[...new Set(f)],rims:[...rims].sort((a,b)=>a-b),base:m.g[0].o[0].n,hp:m.g[0].o.map(o=>o.hp)};
})'''

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(APP.as_uri())
    pg.wait_for_timeout(500)
    ms = pg.evaluate(JS)
    b.close()
json.dump(ms, open(HERE / "models.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
dims = json.load(open(HERE / "dims.json"))
missing = [m["id"] for m in ms if m["id"] not in dims]
print(len(ms), "models exported")
if missing:
    print("add [length, width, height, wheelbase] in mm to dims.json for:", ", ".join(missing))
