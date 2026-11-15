"""Playwright helper: serves this folder under http://r.local/ so render.html can load its ES modules without a web server."""
import pathlib, mimetypes
ROOT=pathlib.Path(__file__).resolve().parent
def attach(page):
    def h(route):
        url=route.request.url
        path=url.split("http://r.local/",1)[1].split("?")[0]
        f=ROOT/path
        if not f.is_file(): return route.fulfill(status=404,body="nf")
        ct=mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if f.suffix in (".js",".mjs"): ct="text/javascript"
        route.fulfill(status=200,body=f.read_bytes(),headers={"content-type":ct,"access-control-allow-origin":"*"})
    page.route("http://r.local/**",h)
