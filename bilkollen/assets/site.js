/* CarDep: registrerar service workern (snabbare laddning och fungerar utan uppkoppling) på publicerade sidor */
(function(){
  if(!("serviceWorker" in navigator)||location.protocol!=="https:")return;
  var s=document.currentScript&&document.currentScript.src;if(!s)return;
  addEventListener("load",function(){navigator.serviceWorker.register(new URL("../cardep-sw.js",s).href).catch(function(){})});
})();
