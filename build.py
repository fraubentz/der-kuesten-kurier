#!/usr/bin/env python3
"""Baut den Küsten-Kurier: holt echte Meldungen (Google News RSS), Wetter (Open-Meteo),
Kaffeepreis (Stooq), rendert docs/index.html und archiviert jede Ausgabe."""
import json, statistics, time, html, datetime as dt, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
NOW = dt.datetime.now(ZoneInfo("Europe/Berlin"))
SECTIONS = [  # (Titel, Suchanfrage)
    ("Deutschland", "Deutschland aktuell"), ("Welt", "Weltnachrichten"),
    ("Scharbeutz", "Scharbeutz"), ("Timmendorfer Strand", "Timmendorfer Strand"),
    ("Katzenfurt", "Katzenfurt"), ("Wetzlar", "Wetzlar"), ("Berlin", "Berlin"),
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
UA = {"User-Agent": "Mozilla/5.0 (Kuesten-Kurier build)"}

def load(name, default):
    try:
        return json.loads((ROOT / "data" / name).read_text(encoding="utf-8") or "null") or default
    except Exception as e:
        print("Datenfehler", name, e)
        return default

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()

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

def news(query, n=5):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query + " when:2d", "hl": "de", "gl": "DE", "ceid": "DE:de"})
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
    """Letzter Monatswert einer FRED-Reihe (IMF-Rohstoffpreise), ohne API-Schlüssel."""
    try:
        for line in reversed(get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}").decode().strip().splitlines()[1:]):
            d, v = line.split(",")
            if v not in (".", ""):
                return float(v), int(d[:4]), int(d[5:7])
    except Exception as e:
        print("FRED-Fehler", sid, e)
    return None

def de(x, nd=2): return f"{x:.{nd}f}".replace(".", ",")

def coffee():
    r = fred("PCOFFOTMUSDM")
    return (f"{de(r[0], 1)} US-Cent/lb", f"IMF/FRED, Ø {MONTHS[r[2]-1]} {r[1]}") if r else None

def salmon():
    r = fred("PSALMUSDM")
    return (f"{de(r[0])} US-$/kg (Zuchtlachs, Norwegen)", f"IMF/FRED, Ø {MONTHS[r[2]-1]} {r[1]}") if r else None

def sardinen():
    """Neueste Dosenpreise (EUR) je Marke aus Open Food Facts Prices; Marken ohne Eintrag entfallen."""
    out = []
    for b in load("sardinen.json", []):
        best = None
        for tag in b["tags"]:
            try:
                q = {"brands_tags": tag, "categories_tags": "en:sardines", "fields": "code,product_name", "page_size": 5}
                prods = json.loads(get("https://world.openfoodfacts.org/api/v2/search?" + urllib.parse.urlencode(q))).get("products", [])
                for pr in prods:
                    time.sleep(0.5)
                    q = {"product_code": pr["code"], "currency": "EUR", "order_by": "-date", "size": 3}
                    for it in json.loads(get("https://prices.openfoodfacts.org/api/v1/prices?" + urllib.parse.urlencode(q))).get("items", []):
                        if it.get("price_per") in (None, "UNIT") and it.get("price") and (not best or it["date"] > best[3]):
                            best = (b["marke"], pr.get("product_name") or "Sardinen", float(it["price"]), it["date"])
            except Exception as e:
                print("Sardinen-Fehler", tag, e)
            if best: break
        if best: out.append(best)
    return out

def price_rows():
    p = json.loads((ROOT / "data/prices.json").read_text(encoding="utf-8"))
    c, s = coffee(), salmon()
    for r in p["items"]:
        if r["name"].startswith("Kaffee") and c: r["wert"], r["stand"] = c
        if r["name"] == "Lachs" and s: r["wert"], r["stand"] = s
    sar = sardinen()
    if sar:
        med = statistics.median(x[2] for x in sar)
        for i, r in enumerate(p["items"]):
            if r["name"].startswith("Sardinen"):
                r["wert"], r["stand"] = f"Ø {de(med)} € pro Dose ({len(sar)} Marken)", "Open Food Facts Prices"
                p["items"][i+1:i+1] = [dict(name=f"– {m}: {n}", wert=f"{de(pr)} €", stand=f"{d[8:]}.{d[5:7]}.{d[:4]}", marke=True) for m, n, pr, d in sar]
                break
    rows, tick = "", ""
    for r in p["items"]:
        if r.get("marke"): continue
        tick += f"<li>{ICONS[0]}<span><strong>{html.escape(r['name'].split(' (')[0])}</strong> {html.escape(r['wert']) if r.get('wert') else '–'}</span></li>"
    for r in p["items"]:
        w = html.escape(r["wert"]) if r.get("wert") else "<em>derzeit keine Daten</em>"
        rows += f"<tr><th scope='row'>{html.escape(r['name'])}</th><td>{w}</td><td>{html.escape(r.get('stand') or '–')}</td></tr>"
    return rows, p.get("hinweis", ""), tick

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
        out += (f"<section class='card klatsch' aria-labelledby='hk'><h2 id='hk' data-de='Hafenklatsch' data-en='Harbour gossip'>Hafenklatsch</h2>"
                f"<article><h3>{esc(k['titel'])}</h3><p>{esc(k['text'])}</p></article></section>")
    l = tagesauswahl("logbuch.json")
    if l and l.get("kutter") and l.get("text"):
        out += (f"<section class='card logbuch' aria-labelledby='lb'><h2 id='lb' data-de='Logbuch' data-en=\"Ship's log\">Logbuch</h2>"
                f"<p class='kutter'>{esc(l['kutter'])}</p><p>{esc(l['text'])}</p></section>")
    return f"<div class='duo'>{out}</div>" if out else ""

def cams():
    C = json.loads((ROOT / "data/webcams.json").read_text(encoding="utf-8"))
    if not C: return "<p>Derzeit sind noch keine geprüften Webcam-Links hinterlegt.</p>"
    return "<ul>" + "".join(f"<li><a href='{html.escape(c['url'])}' rel='noopener'>{html.escape(c['name'])}</a></li>" for c in C) + "</ul>"

def build():
    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    sec, lead = "", ""
    for i, (title, q) in enumerate(SECTIONS):
        cap = 6 if i == 0 else 5
        items = direct(title)
        seen = {x[0] for x in items}
        items = (items + [x for x in news(q, cap) if x[0] not in seen])[:cap]
        if i == 0 and items:
            t, u, s, d = items.pop(0)
            lead = (f"<article class='lead' aria-labelledby='lead-h'><p class='kicker'>Aufmacher · {html.escape(s)}</p>"
                    f"<h2 id='lead-h'><a href='{html.escape(u)}' rel='noopener'>{html.escape(t)}</a></h2><p class='src'>{html.escape(d)}</p></article>")
        li = "".join(f"<li><a href='{html.escape(u)}' rel='noopener'>{html.escape(t)}</a> <span class='src'>{html.escape(s)}, {html.escape(d)}</span></li>"
                     for t, u, s, d in items) or "<li>Gerade keine Meldungen abrufbar.</li>"
        sec += f"<section aria-labelledby='s{i}' class='card'><h2 id='s{i}'>{ICONS[i % 4]}{html.escape(title)}</h2><ul class='news'>{li}</ul></section>"
    wtxt, alerts, kinds = weather()
    alert_html = "".join(f"<li>{html.escape(a)}</li>" for a in alerts)
    rows, hint, tick = price_rows()
    months = "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split()
    days = "Montag Dienstag Mittwoch Donnerstag Freitag Samstag Sonntag".split()
    datum = f"{days[NOW.weekday()]}, {NOW.day}. {months[NOW.month-1]} {NOW.year}, {NOW:%H:%M} Uhr"
    page = {"NEWS": sec, "DUO": duo(), "DATUM": datum, "WETTER": html.escape(wtxt or "Wetterdaten derzeit nicht verfügbar."),
            "ALERTS": f"<div class='alert' role='alert'><h2>Wetterwarnung</h2><ul>{alert_html}</ul></div>" if alerts else "",
            "PREISE": rows, "TICKER": tick, "LEAD": lead or "<article class='lead'><h2>Heute keine Meldungen abrufbar</h2></article>", "HINWEIS": html.escape(hint), "BRIEF": render_letter(pick_letter(kinds)), "CAMS": cams(), "YEAR": str(NOW.year)}
    def render(root):
        s = tpl.replace("{{ROOT}}", root)
        for k, v in page.items(): s = s.replace("{{%s}}" % k, v)
        return s
    OUT.mkdir(exist_ok=True); (OUT / "archive").mkdir(exist_ok=True)
    (OUT / "index.html").write_text(render(""), encoding="utf-8")
    name = f"{NOW:%Y-%m-%d_%H-%M}.html"
    (OUT / "archive" / name).write_text(render("../"), encoding="utf-8")
    for f in ("style.css", "app.js"):
        (OUT / f).write_bytes((ROOT / f).read_bytes())
    files = sorted((OUT / "archive").glob("2*.html"), reverse=True)
    li = "".join(f"<li><a href='{f.name}'>Ausgabe vom {f.stem[8:10]}.{f.stem[5:7]}.{f.stem[:4]}, {f.stem[11:13]}:{f.stem[14:]} Uhr</a></li>" for f in files)
    arch = ("<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Archiv – Der Küsten-Kurier</title><link rel='stylesheet' href='../style.css'></head><body><main class='wrap'>"
            f"<p><a href='../index.html'>← Zur aktuellen Ausgabe</a></p><h1>Archiv</h1><ul class='archive'>{li}</ul></main></body></html>")
    (OUT / "archive" / "index.html").write_text(arch, encoding="utf-8")
    write_briefe()

if __name__ == "__main__":
    build()
