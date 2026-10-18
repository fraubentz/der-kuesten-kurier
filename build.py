#!/usr/bin/env python3
"""Baut den Küsten-Kurier: holt echte Meldungen (Google News RSS), Wetter (Open-Meteo),
Kaffeepreis (Stooq), rendert docs/index.html und archiviert jede Ausgabe."""
import json, re, statistics, time, html, datetime as dt, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
NOW = dt.datetime.now(ZoneInfo("Europe/Berlin"))
SECTIONS = [  # (Titel, Suchanfrage)
    ("Deutschland", "Deutschland aktuell"), ("Welt", "Weltnachrichten"),
    ("Scharbeutz", "Scharbeutz"), ("Timmendorfer Strand", "Timmendorfer Strand"),
    ("Katzenfurt", "Katzenfurt OR Ehringshausen"), ("Wetzlar", "Wetzlar"), ("Berlin", "Berlin"),
    ("Portugal", "Portugal"), ("Kanada", "Kanada"),
]
def _i(body, fill=False):
    a = 'fill="currentColor"' if fill else 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false" {a}>{body}</svg>'
ICONS = [
    _i('<path d="M2 12c4-6 10-6 14 0-4 6-10 6-14 0zM16 12l6-5v10z"/><circle cx="7" cy="11" r="1" fill="#fff"/>', True),
    _i('<circle cx="12" cy="5" r="2"/><path d="M12 7v14M8 11h8M4 13c0 5 4 8 8 8s8-3 8-8"/>'),
    _i('<path d="M9 21l1.5-12h3L15 21zM10 9l2-5 2 5M6 21h12"/>'),
    _i('<path d="M2 12c3-4 5-4 8 0s5 4 8 0 3-2 4-1M2 18c3-4 5-4 8 0s5 4 8 0 3-2 4-1"/>'),
]
SECTIONS_FISCH = [  # (Titel, Suchanfrage) – Meldungen der letzten 14 Tage
    ("Sardinen & Konserven", "Sardinen Konserven OR Fischkonserven OR Dosenfisch"),
    ("Thunfisch, Lachs & Makrele", "Thunfisch OR Lachs OR Makrele OR Hering Fang Preise"),
    ("Fischerei weltweit", "Fischerei Fangquoten OR Fischbestände OR Fischereiflotte OR Fischer"),
]
UA = {"User-Agent": "Mozilla/5.0 (Kuesten-Kurier build)"}

def load(name, default):
    try:
        return json.loads((ROOT / "data" / name).read_text(encoding="utf-8") or "null") or default
    except Exception as e:
        print("Datenfehler", name, e)
        return default

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()

GN = "hl=de&gl=DE&ceid=DE:de"
TOP_URL = "https://news.google.com/rss?" + GN
TOPIC = {"Deutschland": "NATION", "Welt": "WORLD"}  # Google-News-Themen statt Stichwortsuche
LOKAL = {"Katzenfurt": 30, "Scharbeutz": 7, "Timmendorfer Strand": 7}  # kleine Orte: längerer Zeitraum (Tage)
JUNK = re.compile(r"livestream|mediathek|sendungen|alle videos|startseite|newsletter|podcast", re.I)

def gfeed(url, n=6):
    """Google-News-RSS-Feed (Überschrift, Link, Quelle, Datum); Navigations- und Videoseiten werden aussortiert."""
    try:
        items = ET.fromstring(get(url)).findall(".//item")
    except Exception as e:
        print("News-Fehler", url, e); return []
    out = []
    for i in items:
        title, src = i.findtext("title", ""), i.findtext("source", "")
        if src and title.endswith(" - " + src): title = title[:-len(src) - 3]
        if JUNK.search(title): continue
        out.append((title, i.findtext("link", ""), src, i.findtext("pubDate", "")[:16]))
    return out[:n]

def direct(section, n=3):
    """Direkte RSS-Feeds aus data/feeds.json (nur Einträge mit enabled=true); zeigt nur Überschrift, Link und Quelle."""
    out = []
    for f in load("feeds.json", {}).get(section, []):
        if not f.get("enabled") or not f.get("url"): continue
        try:
            for i in ET.fromstring(get(f["url"])).findall(".//item")[:n]:
                out.append((i.findtext("title", "").strip(), i.findtext("link", ""), f["name"], i.findtext("pubDate", "")[:16]))
        except Exception as e:
            print("Feed-Fehler", f["name"], e)
    return out

def news(query, n=5, days=2):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query + f" when:{days}d", "hl": "de", "gl": "DE", "ceid": "DE:de"})
    try:
        items = ET.fromstring(get(url)).findall(".//item")[:n]
    except Exception as e:
        print("News-Fehler", query, e); return []
    out = []
    for i in items:
        title = i.findtext("title", "")
        src = i.findtext("source", "")
        if src and title.endswith(" - " + src): title = title[:-len(src) - 3]
        out.append((title, i.findtext("link", ""), src, i.findtext("pubDate", "")[:16]))
    return out

def weather():
    url = ("https://api.open-meteo.com/v1/forecast?latitude=54.01&longitude=10.75&current="
           "temperature_2m,weather_code,wind_gusts_10m,precipitation&timezone=Europe%2FBerlin")
    try:
        c = json.loads(get(url))["current"]
    except Exception as e:
        print("Wetter-Fehler", e); return None, [], []
    codes = {0: "klar", 1: "heiter", 2: "wolkig", 3: "bedeckt", 45: "Nebel", 48: "Reifnebel",
             51: "Nieselregen", 61: "Regen", 63: "Regen", 65: "Starkregen", 71: "Schnee",
             73: "Schnee", 75: "Starker Schneefall", 80: "Schauer", 81: "Schauer",
             82: "Heftige Schauer", 95: "Gewitter", 96: "Gewitter mit Hagel", 99: "Gewitter mit Hagel"}
    txt = f"Scharbeutz: {c['temperature_2m']:.0f} °C, {codes.get(c['weather_code'], 'wechselhaft')}, Böen bis {c['wind_gusts_10m']:.0f} km/h"
    alerts = []
    if c["weather_code"] in (45, 48): alerts.append("Nebel an der Küste – Vorsicht auf der Ostsee und auf der Promenade.")
    if c["weather_code"] in (65, 82): alerts.append("Starkregen – Keller und Unterführungen im Blick behalten.")
    if c["weather_code"] in (75,): alerts.append("Starker Schneefall an der Lübecker Bucht.")
    if c["weather_code"] >= 95: alerts.append("Gewitter über der Lübecker Bucht – Strand und Seebrücke meiden!")
    if c["wind_gusts_10m"] >= 60: alerts.append("Sturmböen – Boote bleiben im Hafen.")
    kinds = []
    if c["weather_code"] >= 95: kinds.append("gewitter")
    if c["wind_gusts_10m"] >= 60: kinds.append("sturm")
    if c["weather_code"] in (45, 48): kinds.append("nebel")
    if c["weather_code"] in (65, 82): kinds.append("regen")
    if c["weather_code"] == 75: kinds.append("schnee")
    return txt, alerts, kinds

def fred(sid):
    """Letzte zwei Monatswerte einer FRED-Reihe (IMF-Rohstoffpreise): (Wert, Jahr, Monat, Vormonatswert)."""
    rows = []
    try:
        for line in get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}").decode().strip().splitlines()[1:]:
            d, v = line.split(",")
            if v not in (".", ""): rows.append((d, float(v)))
    except Exception as e:
        print("FRED-Fehler (csv)", sid, e)
    if not rows:  # Ausweichadresse: Textdatei der Reihe
        try:
            for line in get(f"https://fred.stlouisfed.org/data/{sid}.txt").decode().splitlines():
                a = line.split()
                if len(a) == 2 and re.match(r"\d{4}-\d{2}-\d{2}$", a[0]) and a[1] != ".": rows.append((a[0], float(a[1])))
        except Exception as e:
            print("FRED-Fehler (txt)", sid, e)
    if not rows: return None
    (d, v), prev = rows[-1], (rows[-2][1] if len(rows) > 1 else None)
    return v, int(d[:4]), int(d[5:7]), prev

def de(x, nd=2): return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fx():
    """Euro-Referenzkurse der EZB (über Frankfurter), Basis US-Dollar."""
    for url in ("https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,GBP,BRL,JPY,CAD,CHF",
                "https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,BRL,JPY,CAD,CHF"):
        try: return json.loads(get(url))["rates"]
        except Exception as e: print("Kurs-Fehler", url, e)
    return {}

STAEDTE = [("Lissabon & Berlin", "EUR", "{} €", 2), ("London", "GBP", "£ {}", 2), ("São Paulo", "BRL", "R$ {}", 2),
           ("Tokio", "JPY", "¥ {}", 0), ("Vancouver", "CAD", "C$ {}", 2), ("Zürich", "CHF", "CHF {}", 2)]
WAREN = [  # Name, FRED-Reihe, Kurs->US-$/kg, Anzeige, Portion in g, Portionstext, Yahoo-Symbol (oder None)
    ("Kaffee (Arabica)", "PCOFFOTMUSDM", lambda c: c / 100 / 0.45359237, lambda v: f"{de(v, 1)} US-Cent/lb", 18, "Die Bohnen in einem Espresso (18 g) kosten etwa", "KC=F"),
    ("Tee (Schwarztee)", "PTEAUSDM", lambda c: c / 100, lambda v: f"{de(v, 1)} US-Cent/kg", 2, "Der Tee in einer Tasse (2 g) kostet etwa", None),
]

def yahoo(symbol):
    """Letzter und vorletzter Tageskurs von Yahoo Finance (inoffizielle Schnittstelle, kann ausfallen): (Kurs, Datum, Vortageskurs)."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=10d&interval=1d"
        res = json.loads(get(url))["chart"]["result"][0]
        pts = [(t, c) for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c is not None]
        (t, v), prev = pts[-1], (pts[-2][1] if len(pts) > 1 else None)
        d = dt.datetime.fromtimestamp(t, ZoneInfo("America/New_York"))
        return v, f"{d.day:02d}.{d.month:02d}.{d.year}", prev
    except Exception as e:
        print("Yahoo-Fehler", symbol, e)
    return None

def boerse():
    """Kaffee- und Tee-Börse: Kurs mit Veränderung, Preis pro Kilogramm in sechs Städten, Preis pro Tasse."""
    rates, out, quellen = fx(), "", []
    for name, sid, usd_kg, show, gram, ptext, ysym in WAREN:
        v = prev = label = vergleich = None
        y = yahoo(ysym) if ysym else None
        if y:
            v, prev, label, vergleich = y[0], y[2], f"Letzter Kurs vom {y[1]}", "zum Vortag"
            quellen.append(f"{name.split(' (')[0]}: Terminbörse (Yahoo Finance)")
        else:
            r = fred(sid)
            if r:
                v, prev, label, vergleich = r[0], r[3], f"Monatsmittel {MONTHS[r[2]-1]} {r[1]}", "zum Vormonat"
                quellen.append(f"{name.split(' (')[0]}: Monatsmittel des Internationalen Währungsfonds (über FRED)")
        if v is None:
            out += f"<article class='ware'><h3>{html.escape(name)}</h3><p>Derzeit keine Daten.</p></article>"; continue
        usd = usd_kg(v)
        delta = ""
        if prev:
            pct = (v - prev) / prev * 100
            up = pct >= 0
            delta = (f" <span class='delta {'up' if up else 'down'}'><span aria-hidden='true'>{'▲' if up else '▼'}</span>"
                     f"<span class='sr-only'>{'gestiegen um' if up else 'gefallen um'}</span> {de(abs(pct))} %</span>")
        rows = "".join(f"<tr><th scope='row'>{c}</th><td>{fmt.format(de(usd * rates[cur], nd))}</td></tr>"
                       for c, cur, fmt, nd in STAEDTE if cur in rates) or f"<tr><th scope='row'>US-Dollar</th><td>$ {de(usd)}</td></tr>"
        cup = f"<p>{ptext} <strong>{de(usd * rates['EUR'] * gram / 1000)} €</strong>.</p>" if "EUR" in rates else ""
        out += (f"<article class='ware'><h3>{html.escape(name)}</h3><p class='kurs'><strong>{show(v)}</strong>{delta}</p>"
                f"<p class='small'>{label}, Veränderung {vergleich}</p>"
                f"<table><caption>Pro Kilogramm</caption><thead><tr><th scope='col'>Stadt</th><th scope='col'>Preis</th></tr></thead><tbody>{rows}</tbody></table>{cup}</article>")
    return (f"<section class='card boerse' aria-labelledby='bo'><h2 id='bo'>Die Kaffee- und Tee-Börse</h2><div class='boerse-grid'>{out}</div>"
            f"<p class='small'>Großhandelspreise für Rohware ({'; '.join(quellen) or 'Quellen derzeit nicht erreichbar'}), "
            "umgerechnet mit den Referenzkursen der EZB. Nicht, was Café oder Laden verlangen.</p></section>")

MONTHS = "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split()
DAYS_DE = "Montag Dienstag Mittwoch Donnerstag Freitag Samstag Sonntag".split()
LEDGER = OUT / "briefe-archiv.json"

def ledger():
    try: return json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception: return {}

def pick_letter(kinds):
    """Ein Brief pro Tag: der erste Build des Tages legt ihn fest; bei Wetterwarnung schreibt Herr Huber."""
    led, key = ledger(), NOW.date().isoformat()
    if key not in led:
        L = load("letters.json", [dict(titel="Heute kein Brief", autor="Die Redaktion", ort="Scharbeutz", text="Die Post hat uns heute leider nicht erreicht.")])
        l = L[(NOW.date() - dt.date(2026, 10, 17)).days % len(L)]
        W = load("wetterbriefe.json", {})
        for k in kinds:
            if k in W: l = dict(W[k], wetter=True); break
        led[key] = l
        OUT.mkdir(exist_ok=True)
        LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    return led[key]

def render_letter(l):
    if not l.get("antwort"):  # ältere Archiv-Einträge: Redaktionsantwort aus den aktuellen Briefdateien ergänzen
        for src in (load("letters.json", []), list(load("wetterbriefe.json", {}).values())):
            for x in src:
                if x.get("titel") == l.get("titel") and x.get("antwort"): l = dict(l, antwort=x["antwort"])
    F = load("figuren.json", {}).get(l["autor"], {})
    paras = "".join(f"<p>{html.escape(t)}</p>" for t in l["text"].split("\n"))
    badge = "<p class='badge'>Wetterbrief</p>" if l.get("wetter") else ""
    antw = f"<p class='antwort'><strong>Die Redaktion antwortet:</strong> {html.escape(l['antwort'])}</p>" if l.get("antwort") else ""
    stamp = f"<div class='stamp' aria-hidden='true'>{ICONS[F.get('icon', 0) % 4]}</div>"
    return (f"{badge}<article class='brief'><h3>{html.escape(l['titel'])}</h3>{paras}"
            f"<div class='absender'>{stamp}<p class='sig'>{html.escape(F.get('gruss', 'Mit freundlichen Grüßen'))}<br>"
            f"<strong>{html.escape(l['autor'])}</strong>, {html.escape(l['ort'])}<br><span class='small'>{html.escape(F.get('kurz', ''))}</span></p></div>"
            f"{antw}</article>")

def write_briefe():
    led, items = ledger(), ""
    for k in sorted(led, reverse=True):
        d = dt.date.fromisoformat(k)
        items += (f"<section class='card letter'><h2>{DAYS_DE[d.weekday()]}, {d.day}. {MONTHS[d.month-1]} {d.year}</h2>"
                  f"{render_letter(led[k])}</section>")
    pg = ("<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
          "<title>Leserbriefe-Archiv – Der Küsten-Kurier</title><link rel='stylesheet' href='style.css'></head><body><main class='wrap'>"
          "<p><a href='index.html'>← Zur aktuellen Ausgabe</a></p><h1>Leserbriefe-Archiv</h1>"
          + items + "</main></body></html>")
    (OUT / "briefe.html").write_text(pg, encoding="utf-8")

def tagesauswahl(name):
    items = load(name, [])
    if not isinstance(items, list) or not items: return None
    return items[(NOW.date() - dt.date(2026, 10, 17)).days % len(items)]

def duo():
    """Hafenklatsch und Logbuch: je ein Eintrag pro Tag; fehlt die Datei oder ist sie leer, entfällt der Kasten."""
    out, esc = "", html.escape
    k = tagesauswahl("hafenklatsch.json")
    if k and k.get("titel") and k.get("text"):
        out += (f"<section class='card klatsch' aria-labelledby='hk'><h2 id='hk'>Hafenklatsch</h2>"
                f"<article><h3>{esc(k['titel'])}</h3><p>{esc(k['text'])}</p></article></section>")
    l = tagesauswahl("logbuch.json")
    if l and l.get("kutter") and l.get("text"):
        out += (f"<section class='card logbuch' aria-labelledby='lb'><h2 id='lb'>Logbuch</h2>"
                f"<p class='kutter'>{esc(l['kutter'])}</p><p>{esc(l['text'])}</p></section>")
    return f"<div class='duo'>{out}</div>" if out else ""

def cams():
    C = json.loads((ROOT / "data/webcams.json").read_text(encoding="utf-8"))
    if not C: return "<p>Derzeit sind noch keine geprüften Webcam-Links hinterlegt.</p>"
    return "<ul>" + "".join(f"<li><a href='{html.escape(c['url'])}' rel='noopener'>{html.escape(c['name'])}</a></li>" for c in C) + "</ul>"

def build():
    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    def card(idx, title, items, icon):
        li = "".join(f"<li><a href='{html.escape(u)}' rel='noopener'>{html.escape(t)}</a> <span class='src'>{html.escape(s)}, {html.escape(d)}</span></li>"
                     for t, u, s, d in items) or "<li>Gerade keine Meldungen abrufbar.</li>"
        return f"<section aria-labelledby='s{idx}' class='card'><h2 id='s{idx}'>{icon}{html.escape(title)}</h2><ul class='news'>{li}</ul></section>"
    res = {}
    for i, (title, q) in enumerate(SECTIONS):
        cap = 6 if i == 0 else 5
        items = direct(title)
        if title in TOPIC:
            items += gfeed(f"https://news.google.com/rss/headlines/section/topic/{TOPIC[title]}?{GN}", cap)
        seen = {x[0] for x in items}
        res[title] = (items + [x for x in news(q, cap, LOKAL.get(title, 2)) if x[0] not in seen and not JUNK.search(x[0])])[:cap]
    lead = ""
    top = gfeed(TOP_URL, 5)  # Aufmacher: wichtigste Meldung des Tages (Google News Top-Meldungen)
    if top:
        for title in res: res[title] = [x for x in res[title] if x[0] != top[0][0]]
    for title, _ in SECTIONS:  # sonst: erste echte Meldung in der Reihenfolge Deutschland, Welt, ...
        if top or res[title]:
            t, u, s, d = top[0] if top else res[title].pop(0)
            lead = (f"<article class='lead' aria-labelledby='lead-h'><p class='kicker'>Aufmacher · {html.escape(s)}</p>"
                    f"<h2 id='lead-h'><a href='{html.escape(u)}' rel='noopener'>{html.escape(t)}</a></h2><p class='src'>{html.escape(d)}</p></article>")
            break
    sec = "".join(card(i, title, res[title], ICONS[i % 4]) for i, (title, _) in enumerate(SECTIONS))
    fisch = "".join(card(100 + j, title, news(q, 4, 14), ICONS[0]) for j, (title, q) in enumerate(SECTIONS_FISCH))
    fisch = f"<section class='fischblock' aria-labelledby='fh'><h2 id='fh'>{ICONS[0]}Fisch &amp; Fang aus aller Welt</h2><div class='grid'>{fisch}</div></section>"
    wtxt, alerts, kinds = weather()
    alert_html = "".join(f"<li>{html.escape(a)}</li>" for a in alerts)
    boerse_html = boerse()
    months = "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split()
    days = "Montag Dienstag Mittwoch Donnerstag Freitag Samstag Sonntag".split()
    datum = f"{days[NOW.weekday()]}, {NOW.day}. {months[NOW.month-1]} {NOW.year}, {NOW:%H:%M} Uhr"
    page = {"NEWS": sec, "DUO": duo(), "DATUM": datum, "WETTER": html.escape(wtxt or "Wetterdaten derzeit nicht verfügbar."),
            "ALERTS": f"<div class='alert' role='alert'><h2>Wetterwarnung</h2><ul>{alert_html}</ul></div>" if alerts else "",
            "BOERSE": boerse_html, "LEAD": lead, "FISCH": fisch, "BRIEF": render_letter(pick_letter(kinds)), "CAMS": cams(), "YEAR": str(NOW.year)}
    def render(root):
        s = tpl.replace("{{ROOT}}", root)
        for k, v in page.items(): s = s.replace("{{%s}}" % k, v)
        return s
    OUT.mkdir(exist_ok=True); (OUT / "archive").mkdir(exist_ok=True)
    (OUT / "index.html").write_text(render(""), encoding="utf-8")
    name = f"{NOW:%Y-%m-%d}.html"  # eine Archiv-Ausgabe pro Tag: der letzte Lauf des Tages ersetzt die vorige
    for old in (OUT / "archive").glob(f"{NOW:%Y-%m-%d}_*.html"): old.unlink()
    (OUT / "archive" / name).write_text(render("../"), encoding="utf-8")
    for f in ("style.css", "app.js"):
        (OUT / f).write_bytes((ROOT / f).read_bytes())
    files = sorted((OUT / "archive").glob("2*.html"), reverse=True)
    li = "".join(f"<li><a href='{f.name}'>Ausgabe vom {f.stem[8:10]}.{f.stem[5:7]}.{f.stem[:4]}{(', ' + f.stem[11:13] + ':' + f.stem[14:] + ' Uhr') if len(f.stem) > 10 else ''}</a></li>" for f in files)
    arch = ("<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Archiv – Der Küsten-Kurier</title><link rel='stylesheet' href='../style.css'></head><body><main class='wrap'>"
            f"<p><a href='../index.html'>← Zur aktuellen Ausgabe</a></p><h1>Archiv</h1><ul class='archive'>{li}</ul></main></body></html>")
    (OUT / "archive" / "index.html").write_text(arch, encoding="utf-8")
    write_briefe()

if __name__ == "__main__":
    build()
