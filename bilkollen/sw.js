/* CarDep service worker: sidan laddar snabbare och fungerar utan uppkoppling.
   Sidor: nätet först, sparad kopia om nätet saknas. Bilder och typsnitt: sparad kopia först. Chatten (/api/) går aldrig via cachen. */
const V="cardep-41ba08c7f6",IMG="cardep-img-1",CORE=["./", "en/", "bil/", "en/cars/", "assets/site.css", "assets/fonts.css", "assets/site.js", "assets/fonts/archivo.woff2", "assets/fonts/ibm-plex-sans.woff2", "assets/fonts/ibm-plex-mono.woff2", "favicon.svg", "manifest.webmanifest"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V&&k!==IMG).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
async function trim(c,max){const ks=await c.keys();for(let i=0;i<ks.length-max;i++)await c.delete(ks[i])}
self.addEventListener("fetch",e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=="GET"||u.origin!==location.origin||u.pathname.includes("/api/"))return;
  if(r.mode==="navigate"){
    e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}return res})
      .catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match(new URL("./",location).href))));
    return;
  }
  if(u.pathname.includes("/img/")||u.pathname.includes("/og/")){
    e.respondWith(caches.open(IMG).then(c=>c.match(r).then(m=>m||fetch(r).then(res=>{if(res.ok){c.put(r,res.clone());trim(c,400)}return res}))));
    return;
  }
  e.respondWith(caches.match(r).then(m=>m||fetch(r)));
});
