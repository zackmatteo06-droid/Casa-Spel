# Drift av CarDep

Så uppdaterar och publicerar du webbplatsen, kopplar en egen domän, anmäler den till sökmotorer och sätter igång AI-chatten på den publicerade sidan.

## Uppdatera och publicera

Källkoden ligger i mappen `kallkod/` i repot Casa-Spel, och den färdiga sajten i `bilkollen/`. Ändra alltid i källkoden, aldrig direkt i `bilkollen/`, annars skrivs ändringen över nästa gång sajten byggs.

1. Ändra i `kallkod/app/bilkalkyl.html` (bildata, texter, kalkyl) eller i `kallkod/sajt/` (de statiska sidorna).
2. Bygg och lägg den färdiga sajten i `bilkollen/`:
   ```
   cd kallkod
   ./bygg_och_publicera.sh
   ```
   Det hämtar bilder, ikoner och typsnitt från `bilkollen/`, kör `bygg.py` (kalkylatorn, en sida per bilmodell på svenska och engelska, topplistor, info-sidor, `sitemap.xml`, service worker och chattens `katalog.txt`) och kopierar resultatet till `bilkollen/`. Modellsidorna räknas med kalkylatorns egen kod, via macOS inbyggda JavaScript eller Node.js, så siffrorna blir exakt desamma som i kalkylatorn.
3. Har du ändrat loggan, lagt till en modell eller bytt ett foto: skapa ikoner och delningsbilder (kräver Pillow, `pip install pillow`) med `python3 verktyg/bilder.py` och bygg igen.
4. Committa och pusha repot, till exempel med GitHub Desktop.

En schemalagd uppgift förbättrar CarDep varje natt på grenen `cardep-forbattringar` och samlar ändringarna i en pull request. Granska den och klicka **Merge** när du vill att ändringarna ska ut.

## Inställningar i sajt.json

| Nyckel | Vad den gör |
|---|---|
| `url` | Webbplatsens adress, med `/` på slutet. Används i sökmotortaggar, delningsbilder, sitemap och 404-sidan. |
| `chatt_url` | Chattserverns adress, t.ex. `https://cardep-chatt.onrender.com/api/chat`. Tom: chattknappen visas bara där `server.py` kör på samma adress som sidan. |
| `kontakt_url` | Kontaktlänken i sidfoten och på om- och integritetssidorna. |
| `kallkod_url` | Länken till koden på GitHub. |
| `google_verifiering` | (valfri) Koden från Google Search Console, se nedan. |

Bygg och publicera igen efter varje ändring.

## Egen domän

1. Köp en domän, till exempel `cardep.se`, hos en domänregistrar.
2. Lägg webbplatsen i roten av ett repo, antingen ett nytt repo eller Casa-Spel:
   ```
   python3 publicera.py ../../Casa-Spel --mapp .
   ```
3. På GitHub: repot → **Settings** → **Pages** → **Custom domain**, skriv domänen och spara. GitHub visar vilka DNS-poster du ska lägga in hos registraren. Kryssa i **Enforce HTTPS** när certifikatet är klart.
4. Ändra `url` i `sajt.json` till `https://cardep.se/`, bygg, publicera och pusha.

## Sökmotorer

1. Gå till [Google Search Console](https://search.google.com/search-console) och lägg till webbplatsen som **URL-prefix** (adressen i `url`).
2. Välj verifiering med **HTML-tagg**, kopiera koden i `content="..."` och lägg den i `sajt.json` som `"google_verifiering": "koden"`. Bygg, publicera, pusha och klicka **Verifiera**.
3. Under **Webbplatskartor**: skicka in `sitemap.xml`.
4. [Bing Webmaster Tools](https://www.bing.com/webmasters) kan hämta allt från Search Console.

Sidorna har titlar och beskrivningar, kanoniska adresser, språkversioner (hreflang), delningsbilder och strukturerade data (schema.org) för sökresultaten.

## AI-chatten på den publicerade sidan

GitHub Pages kan bara visa filer, inte köra `server.py`. Chatten behöver därför en server någon annanstans. Så här med Render:

1. Lägg projektmappen `bilkollen/bilkollen` i ett eget repo på GitHub: GitHub Desktop → **File** → **Add Local Repository** → välj mappen → **Publish repository**. Kryssa gärna i **Keep this code private**. API-nyckeln följer inte med, eftersom `.env` inte versionshanteras.
2. Skapa ett konto på [render.com](https://render.com) och välj **New** → **Blueprint**. Välj repot. Render läser `render.yaml` och frågar efter `ANTHROPIC_API_KEY`: klistra in nyckeln där. Render bygger servern från `Dockerfile`.
3. När servern är igång: kopiera adressen, till exempel `https://cardep-chatt.onrender.com`, och skriv den i `sajt.json` som `"chatt_url": "https://cardep-chatt.onrender.com/api/chat"`.
4. Bygg, publicera och pusha. Chattknappen visas på den publicerade sidan.

Bra att veta:
- **Vilka sidor som får använda chatten** styrs av `ALLOWED_ORIGINS` i `render.yaml`. Byt till din egen domän om du skaffar en.
- **Kostnaden** begränsas av `CHAT_PER_DAY` (frågor per dygn för hela sidan, standard 500) och `CHAT_PER_IP_HOUR` (frågor per besökare och timme, standard 20). Varje fråga kostar ungefär någon krona hos Anthropic. Sätt också en månadsgräns under **Billing** på console.anthropic.com.
- **Renders gratisnivå** somnar efter en stunds inaktivitet. Då tar första frågan ungefär en minut. En betald nivå håller servern vaken.
- **Läcker nyckeln**, skapa en ny på console.anthropic.com, ta bort den gamla och byt den i Render.

## Uppdatera bränslepriser och annonsdata

- **Bränslepriser** står i `FUEL_SNAPSHOT` i `app/bilkalkyl.html`.
- **Begagnatpriser och värdeminskning** står i `MKT` i `app/bilkalkyl.html`, per modell. De bygger på annonser som samlats in i oktober 2026. Inför en ny insamling: be Claude samla in nya annonser och räkna om `MKT`.
- **Nypriser** bygger på Skatteverkets nybilsprislista (öppna data) och annonser för nya bilar. `prisandringar.md` listar ändringarna.
- **Privatleasing** står i `LEASE` och `LEASE_TERMS` i `app/bilkalkyl.html`: märkenas egna erbjudanden, avlästa 26–27 oktober 2026. Kampanjerna byts ofta, och Volkswagens, Audis, Cupras, Hyundais och BMW:s gäller till och med 31 oktober 2026. Be Claude läsa av erbjudandena på nytt och uppdatera `LEASE`, bygg sedan och publicera. Sidan `leasing/` och avsnittet Leasa eller köpa på varje modellsida byggs om automatiskt.

Bygg och publicera efter varje uppdatering.
