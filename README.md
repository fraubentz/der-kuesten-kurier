# Der Küsten-Kurier

Die Schifffahrts-, Hafen- und Fischerei-Zeitung für Küste, Kutter & Kaffeetafel.
Elegantes Broadsheet-Zeitungskonzept im Holzstich- und Kupfertiefdruck-Stil des 19. Jahrhunderts, generiert mit einem Python-basierten Static-Site-Generator und optimiert für macOS, iOS und moderne Webbrowser.

## Gestaltungs- und Stilmerkmale (19. Jahrhundert)

- **Holzstich-Kopfzeile (Masthead)**: Handgezeichnete Gravur mit Segelkutter, Leuchtturm, Felsklippen und springendem Ostsee-Fisch in den Wellen sowie zarter Fisch-Titelvignette.
- **Historischer Zeitungssatz**: Klassische Broadsheet-Doppellinien, dekorative typografische Ornamente (`❧ ⚓ ☙`), Jahrgangs- und Nummerierungszeile (*Jahrgang XLVIII · No. 293*) und Fraktur-/Antiqua-Titelhierarchie.
- **Telegraphische Wetter-Depesche**: Scharbeutzer Küstenwetter als Eildepesche mit historischem Stempel.
- **Nautisches Journal & Seewetter**: Seewetterbericht für die Lübecker Bucht mit Beaufort-Windskala, Windrichtung, Wellengang, Wassertemperatur, Sonnenzeiten und astronomischer Mondphasenberechnung.
- **Fischerei-, Kutter- & Fang-Chronik**: Maritime Nachrichten aus aller Welt (*Sardinen & Konserven*, *Thunfisch, Lachs & Makrele*, *Fischerei weltweit*).
- **Die Kaffeebörse & Colonialwaren**: Rohstoffpreise mit EZB-Wechselkursen für 6 Weltstädte und Espressopreis.
- **Küstenschnack & Kutter-Logbuch**: Hafenklatsch und das Schiffstagebuch der *Sturmvogel II*.
- **Rezepte der Kombüse**: Täglich wechselnde Fisch- und bürgerliche Gemüsegerichte.
- **Anzeigen-Theil & Postalischer Leserbrief**: Historische Kleinanzeigen und Leserbriefe mit Kaiserlicher Postwertzeichen-Prägung.

## Optimierungen für macOS & iOS

- Apple-Schriftsystem: `-apple-system-ui-serif`, `"New York"`, `"Hoefler Text"`, `"Didot"`, `"Baskerville"`.
- Retina-optimiertes Rendering mit Subpixel-Antialiasing (`-webkit-font-smoothing: antialiased`).
- Safe-Area-Unterstützung (`viewport-fit=cover`, `env(safe-area-inset-*)`).
- Touch-Ziele nach Apple Human Interface Guidelines (Mindesthöhe 44px).
- Robustes Responsive Design: Kein Überlappen oder Abschneiden von Depeschen, Tabellen oder langen deutschen Komposita auf Mobilgeräten.
- Barrierefreiheit: Dynamische Schriftgrößen (`A+` / `A−`) und Hoher Kontrast (`.hc`).

## Architektur & Build

- **Static Site Generator**: `build.py` holt aktuelle RSS-Feeds, Wetterdaten (Open-Meteo), Börsenkurse, rotiert tägliche Rubriken und baut `docs/index.html`, `docs/archive/` und `docs/briefe.html`.
- **Lokale Ausführung**:

```bash
python3 build.py
```

Oder über npm:

```bash
npm run build   # Baut die statischen Seiten via Python
npm run dev     # Baut und startet den lokalen Server auf Port 3000
```