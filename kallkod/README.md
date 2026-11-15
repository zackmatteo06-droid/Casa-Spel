# CarDep

This folder (`kallkod/` in the Casa-Spel repo) is the source. The published site in `../bilkollen/` is built from it: never edit `bilkollen/` by hand.

CarDep compares what a car really costs per month: depreciation, fuel or electricity, service and repairs (including the risk of each model's common faults), insurance and tax. It ranks cars by monthly cost against quality, looks, comfort and luxury, in Swedish and English.

For 61 cars that are commonly leased privately in Sweden it also compares the brand's own private lease offer with buying the same car new and selling it when the lease ends.

CarDep is a static website: the calculator plus one page per car model, rankings, a lease-or-buy page, a method page, about, privacy, terms and image credits, in Swedish and English. Everything is built from one source file and published as plain files, for example on GitHub Pages. The optional AI chat runs on a small Python server. How to update, publish, connect a domain, register with search engines and put the chat online is in [DRIFT.md](DRIFT.md) (Swedish).

Live: https://zackmatteo06-droid.github.io/Casa-Spel/bilkollen/

## What's in the folder

```
bilkollen/
├── app/                   the website as published (built by bygg.py)
│   ├── bilkalkyl.html     the source: the calculator, all car data and the cost model in one file
│   ├── index.html         the calculator in Swedish (en/index.html: English)
│   ├── bil/<model>/       one page per car model: monthly cost by model year, used prices, engines, faults (en/cars/<model>/)
│   ├── bil/, topplistor/, leasing/, metod/, om/, integritet/, villkor/, bildkallor/   car index, rankings, lease or buy and info pages (English under en/)
│   ├── 404.html, sitemap.xml, robots.txt, manifest.webmanifest, sw.js
│   ├── assets/            site.css (static pages), site.js, self-hosted fonts (SIL Open Font License)
│   ├── og/                share images (1200×630) for every page
│   ├── img/foto/          cut-out photos of the real cars from Wikimedia Commons: colour as JPEG, transparency as PNG mask
│   └── img/bilar/         computer-generated 3D images, used where there is no photo
├── sajt/                  builds the static pages: data.py (car data via the app's own cost model), sidor.py (pages)
├── sajt.json              site address, chat address, contact link
├── bygg.py                builds the whole site in app/
├── publicera.py           copies the site to the local copy of the GitHub repo
├── verktyg/               bilder.py (icons and share images, needs Pillow), typsnitt.py (downloads the fonts)
├── server.py              serves the site and answers the AI chat with Claude
├── katalog.txt            every car with prices and costs, for the chat (written by bygg.py)
├── Dockerfile, render.yaml  run the chat server on Render or another container host
├── DRIFT.md               operations guide (Swedish)
└── bildgenerator/         the 3D generator that made the car images (see below)
```

## Build and preview

```
python3 bygg.py                       # builds app/ (the model pages need macOS: they use its built-in JavaScript)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python server.py            # http://localhost:8123, only reachable from this computer (HOST=0.0.0.0 to share it)
```

## Publish

```
./bygg_och_publicera.sh              # from kallkod/: builds and copies the site to ../bilkollen; then commit and push
```

## AI chat

The button at the bottom right opens a chat where visitors can ask about cars and costs. The page sends the question and what the visitor sees right now (settings, the top of the list, the open model) to `server.py`. The server adds every car from `katalog.txt` as a cached system prompt, asks Claude (`claude-opus-5-5`) and streams the answer back. It limits questions per visitor and per day, so the cost has a ceiling, and only answers the sites listed in `ALLOWED_ORIGINS`. The button only shows where a chat server answers. To run it locally, put `ANTHROPIC_API_KEY=your-key` in `.env`. To put it online, see DRIFT.md.

## Change the app

All changes to the calculator go in `app/bilkalkyl.html`; the static pages are made by `sajt/sidor.py`. Rebuild afterwards with `python3 bygg.py`.

- **Car data** is in the `MODELS` list inside the script: price, depreciation, insurance, service, reliability, engines and trims.
- **New prices** come from the Swedish Tax Agency's new car price list (open data, June 2026), list prices including VAT. An engine or trim with `to` is no longer sold new after that model year. `prisandringar.md` lists every price that changed in October 2026.
- **Private lease offers** are in `LEASE` (one offer per model: payment, distance per year, prices for more distance, the version it covers) and `LEASE_TERMS` (term, fees, servicing, source per brand). `leaseCmp` compares leasing with buying the same version new and selling it when the lease ends; the car view, the model pages and the lease-or-buy page all use it.
- **Default language** is set by `LANG_DEFAULT`. The page also has a language button.
- **Car images:** the app shows a photo of the right model and generation when its id is listed in `PHOTO` (photographer, licence and file name on Wikimedia Commons). All photos show the car from the front at the same angle, with the front pointing right, and none is mirrored. The background is removed (macOS Vision subject lifting) and every car stands on the same ground line at the same scale with a soft shadow, so all cars sit on the same background as the 3D images. Each photo is `<id>.jpg` / `<id>-s.jpg` for the colour and `<id>-m.png` / `<id>-ms.png` for the transparency, which the page applies as a CSS mask. The photos are freely licensed (CC BY, CC BY-SA, CC0 or public domain), so the photographer, the licence and the note that the background was removed must stay visible: the app shows them on the photo in the model view. Without a photo the app shows the 3D image when the id is in `CAR_IMG`. Any other model, including those users add themselves, gets the simple drawn side view (`carSvg`). If a photo fails to load, the 3D image or the drawing takes its place.

## Make the car images again

You need Python 3.10 or newer and Playwright with Chromium:

```
pip install playwright pillow numpy
python -m playwright install chromium
```

```
cd bildgenerator
python3 render_all.py                 # all models -> out/render/*.png (about 10 s per car)
python3 finish.py                     # -> ../app/img/bilar/<id>.webp and <id>-s.webp
python3 render_all.py volvo-xc60      # a single model
python3 preview.py persp,side vw-golf # test views while you tweak gen.js
```

To add a new model:

1. Add the model to `app/bilkalkyl.html` and run `python3 bygg.py`.
2. In `bildgenerator`, run `python3 export_models.py`.
3. Add the model's measurements to `dims.json`.
4. Render the model, then run `finish.py`.
5. Add the model's id to `CAR_IMG` in `app/bilkalkyl.html` and run `bygg.py` again.

## How the 3D images are made

1. **Body.** `gen.js` builds the body from about 340 cross-sections along the car. Each body style (hatchback, sedan, fastback, wagon, crossover, SUV, SUV coupe, box, van, coupe, roadster) has its own side profile: nose, hood, windshield, roof and rear. The profile is scaled to the model's real length, height and wheelbase. The sections add rounded corners seen from above, side windows that lean inwards, a shoulder line, wheel arches and wheel wells.
2. **Details.** Windows, pillars, lamps, grilles, air intakes, door lines, handles and trim are drawn as flat pictures of the car from the side, top, front and rear. A shader projects them onto the body, together with maps that control shine and metal. That is why paint, glass, chrome, rubber and plastic each look different.
3. **Wheels and extras.** Wheels are separate 3D parts: tyre, spoked rim, brake disc and caliper. Mirrors and roof rails are separate parts too.
4. **Variety.** A table of makes in `gen.js` gives each brand its own generic lamp, grille and rim styles. Every model also gets small, fixed variations based on its id. The shapes are generic, with no logos and no copies of real brand designs.
5. **Studio.** All cars share the same studio: soft-box lighting, a soft ground shadow and one fixed camera angle, slightly from the front. Paint has a clear-coat finish. Each car is rendered in headless Chromium with software WebGL at 2400×1000 on a transparent background. `finish.py` crops the render so every car sits on the same ground line and saves it as WebP in 1200×600 and 640×320.

The images are computer-generated illustrations based on each model's measurements and body style, not photos of the real cars.
