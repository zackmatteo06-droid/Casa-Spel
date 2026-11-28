"""Bildata för de statiska sidorna, räknad med appens egen kalkyl.

Appens skript i app/bilkalkyl.html körs i macOS inbyggda JavaScript (osascript -l JavaScript) med en tom
ersättning för webbläsarens dokument. Sedan räknas varje modell med samma funktioner som i appen (build, costs,
gradeOf), så att siffrorna på modellsidorna blir exakt desamma som i kalkylatorn.

Resultatet sparas i .cache/ och räknas bara om när bilkalkyl.html har ändrats.
"""
import hashlib, json, pathlib, shutil, subprocess, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "app" / "bilkalkyl.html"
CACHE = ROOT / ".cache"

# Webbläsarens objekt ersätts med en tom stub som tål allt (läsning, anrop, tilldelning).
STUB = r"""
var __stub=function(){var f=function(){};return new Proxy(f,{get:function(t,k){if(k===Symbol.toPrimitive)return function(){return ""};
 if(k==="value"||k==="textContent"||k==="innerHTML")return "";if(k==="length")return 0;if(k===Symbol.iterator)return function*(){};
 if(k==="then")return undefined;return __stub()},set:function(){return true},apply:function(){return __stub()},construct:function(){return __stub()}})};
var document=__stub(),window={},localStorage={getItem:function(){return null},setItem:function(){}},
 location={protocol:"file:",search:"",hostname:"",href:"",pathname:"/"},navigator={language:"sv-SE"},history={replaceState:function(){},pushState:function(){}};
var matchMedia=function(){return {matches:false,addEventListener:function(){}}},requestAnimationFrame=function(){},setTimeout=function(){},
 clearTimeout=function(){},MutationObserver=function(){this.observe=function(){}},fetch=function(){return new Promise(function(){})};
var URLSearchParams=function(){this.get=function(){return null}},URL=function(u){this.href=String(u);this.searchParams=new URLSearchParams()};
"""

# Körs i samma räckvidd som appens skript. Standardfallet: 5 års ägande, 1 250 mil per år, dagens bränslepriser.
EXPORT = r"""
/* leasa eller köpa samma nya bil, kronor per månad (null om märket inte har ett privatleasingerbjudande för modellen) */
function __lease(m,I){
 var c=leaseCmp(m,I.mil,I.pr,LEASE_RATE);if(!c)return null;
 return {date:c.lt.date||LEASE_DATE,ins:c.lt.ins||null,v:c.L.v,brand:c.L.t,n:c.lt.n,fee:c.L.fee,mil:c.L.mil,km:c.L.km||null,mon:c.mon,first:c.lt.first||0,setup:c.setup,adm:c.adm,est:c.est,
  svc:!!c.lt.svc,fix:!!c.lt.fix,url:c.L.u||c.lt.url,until:c.lt.until||null,price:c.s.p,resid:c.resid,typ:c.typ,fuelType:c.s.f,
  version:c.s.opts.map(function(o){return o.n}),buy:c.buy,lease:c.lease};
}
function __export(){
 var I={years:5,mil:1250,pr:{B:FUEL_SNAPSHOT.pB,D:FUEL_SNAPSHOT.pD,E:FUEL_SNAPSHOT.pE},type:"Alla",cond:"alla",
        minYear:OLDEST,minGrade:"E",lux:1,sport:1,maxP:0,maxM:0};
 var out={now:NOW,oldest:OLDEST,fuel:FUEL_SNAPSHOT,scenario:{years:I.years,mil:I.mil},
          how:{sv:T.sv.howHtml,en:T.en.howHtml},foot:{sv:T.sv.foot1,en:T.en.foot1},types:TYPE_L,fuels:FUEL_L,models:[],
          lease:{date:LEASE_DATE,rate:LEASE_RATE,mil:I.mil,terms:LEASE_TERMS,def:LEASE_DEF}};
 MODELS.forEach(function(m){
  var ys=allYears(m),last=lastYear(m);
  var picks=[last,last-3,last-6].filter(function(y){return ys.indexOf(y)>=0});
  if(!picks.length)picks=[ys[0]];
  var rows=picks.map(function(y){
   var s=build(m,effSel(m),y),k=costs(s,I.years,I.mil,I.pr),g=gradeOf(s,k,I);
   return {year:y,price:s.p,month:k.month,dep:k.dep/k.mo,fuel:k.fuel/k.mo,svc:k.svc/k.mo,ins:k.ins/k.mo,tax:k.tax/k.mo,
           grade:g.letter,score:g.score,version:(s.opts||[]).map(function(o){return o&&o.n}).filter(Boolean),fuelType:s.f,
           hp:s.hp,acc:s.acc,cons:s.c,kwh:s.e,range:s.r,thin:thinYear(m,y)};
  });
  var faults=[];(MF[m.id]||[]).forEach(function(e){var key=e[0],f=FL[key];if(f&&!faults.some(function(x){return x.key===key}))
   faults.push({key:key,sv:f.n,en:f.ne||f.n,cost:f.c})});
  var mk=MKT[m.id]||null,ph=PHOTO[m.id]||null;
  out.models.push({id:m.id,brand:m.b,name:m.n,nameEn:m.ne||m.n,type:m.t,from:m.from,to:m.to||null,years:ys,
   newFrom:m.to?null:newFrom(m),listPrice:m.p,ins:m.ins,svc:m.svc,trunk:m.trunk,ncap:m.ncap,rel:m.rel,war:m.war,warMil:WAR_MIL[m.b]||null,
   pro:{sv:m.pro,en:m.pe},con:{sv:m.con,en:m.ce},groups:m.g.map(function(g){return {k:g.k,o:g.o}}),
   design:DESIGN[m.id]||null,comfort:COMF[m.id]||null,
   thin:allYears(m).every(function(y){return thinYear(m,y)}),
   market:mk?{obs:mk.obs||[],mil:milByYear(m),src:mk.src||"",ads:mk.ads||0,nk:mk.nk||null,nads:mk.nads||null}:null,
   photo:ph?{artist:ph[0],license:ph[1],file:ph[2],flip:!!ph[3]}:null,img3d:CAR_IMG.has(m.id),rows:rows,faults:faults,
   lease:__lease(m,I)});
 });
 /* "När slutar bilen bli billigare?" på metodsidan: samma text och diagram som i kalkylatorn */
 var L0=LANG;out.age={};["sv","en"].forEach(function(l){LANG=l;setFormats();out.age[l]=ageHtml()});LANG=L0;setFormats();
 /* fasta texter i kalkylatorns HTML (data-t), så att den engelska sidan kan skrivas på engelska redan i HTML-koden */
 out.i18n={};for(var k in T.en)if(typeof T.en[k]==="string")out.i18n[k]=T.en[k];
 return JSON.stringify(out);
}
"""


def main_script(html):
    a = html.index("<script>") + len("<script>")
    return html[a:html.index("</script>", a)]


def load(force=False):
    """Bildata som dict, eller None om osascript saknas (då byggs sidorna utan modellsidor)."""
    html = SRC.read_text(encoding="utf-8")
    key = hashlib.sha256((html + STUB + EXPORT).encode()).hexdigest()[:16]
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / f"data-{key}.json"
    if cached.exists() and not force:
        return json.loads(cached.read_text(encoding="utf-8"))
    runner = ["osascript", "-l", "JavaScript"] if shutil.which("osascript") else ["node"] if shutil.which("node") else None
    if not runner:
        print("varken osascript (macOS) eller Node.js finns: bygger utan modellsidor och topplistor")
        return None
    js = STUB + "var __OUT=(function(){\n" + main_script(html) + "\n;return __export();\n" + EXPORT + "})();\n" + ("console.log(__OUT);" if runner[0] == "node" else "__OUT;")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js)
    try:
        r = subprocess.run(runner + [f.name], capture_output=True, text=True, timeout=300)
    finally:
        pathlib.Path(f.name).unlink(missing_ok=True)
    if r.returncode != 0 or not r.stdout.strip().startswith("{"):
        raise RuntimeError("kunde inte räkna bildata med appens skript: " + (r.stderr or r.stdout)[:400])
    data = json.loads(r.stdout)
    for old in CACHE.glob("data-*.json"):
        old.unlink()
    cached.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
