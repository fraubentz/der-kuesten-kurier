#!/usr/bin/env python3
"""Baut den Küsten-Kurier: holt echte Meldungen (Google News RSS), Wetter (Open-Meteo),
Kaffeepreis (Stooq), rendert docs/index.html und archiviert jede Ausgabe."""
import json, html, datetime as dt, urllib.request, urllib.parse, xml.etree.ElementTree as ET
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
UA = {"User-Agent": "Mozilla/5.0 (Kuesten-Kurier build)"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()

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
        print("Wetter-Fehler", e); return None, []
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
    return txt, alerts

def coffee():
    try:
        row = get("https://stooq.com/q/l/?s=kc.f&f=sd2c&h&e=csv").decode().splitlines()[1].split(",")
        return f"{float(row[2]):.2f} US-Cent/lb (Stand {row[1]})"
    except Exception as e:
        print("Kaffee-Fehler", e); return None

def price_rows():
    p = json.loads((ROOT / "data/prices.json").read_text(encoding="utf-8"))
    c = coffee()
    for r in p["items"]:
        if r["name"] == "Kaffee (Arabica, Terminmarkt)" and c: r["wert"], r["stand"] = c, "live (Stooq)"
    rows = ""
    for r in p["items"]:
        w = html.escape(r["wert"]) if r.get("wert") else "<em>derzeit keine Daten</em>"
        rows += f"<tr><th scope='row'>{html.escape(r['name'])}</th><td>{w}</td><td>{html.escape(r.get('stand') or '–')}</td></tr>"
    return rows, p.get("hinweis", "")

def letter():
    L = json.loads((ROOT / "data/letters.json").read_text(encoding="utf-8"))
    l = L[(NOW.date() - dt.date(2026, 10, 17)).days % len(L)]
    paras = "".join(f"<p>{html.escape(t)}</p>" for t in l["text"].split("\n"))
    return f"<h3>{html.escape(l['titel'])}</h3>{paras}<p class='sig'>– {html.escape(l['autor'])}, {html.escape(l['ort'])}</p>"

def cams():
    try:
        C = json.loads((ROOT / "data/webcams.json").read_text(encoding="utf-8") or "[]")
    except Exception as e:
        print("Webcam-Fehler", e); C = []
    if not C: return "<p>Derzeit sind noch keine geprüften Webcam-Links hinterlegt.</p>"
    return "<ul>" + "".join(f"<li><a href='{html.escape(c['url'])}' rel='noopener'>{html.escape(c['name'])}</a></li>" for c in C) + "</ul>"

def build():
    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    sec = ""
    for i, (title, q) in enumerate(SECTIONS):
        items = news(q)
        li = "".join(f"<li><a href='{html.escape(u)}' rel='noopener'>{html.escape(t)}</a> <span class='src'>{html.escape(s)}, {html.escape(d)}</span></li>"
                     for t, u, s, d in items) or "<li>Gerade keine Meldungen abrufbar.</li>"
        sec += f"<section aria-labelledby='s{i}' class='card'><h2 id='s{i}'>{html.escape(title)}</h2><ul class='news'>{li}</ul></section>"
    wtxt, alerts = weather()
    alert_html = "".join(f"<li>{html.escape(a)}</li>" for a in alerts)
    rows, hint = price_rows()
    months = "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split()
    days = "Montag Dienstag Mittwoch Donnerstag Freitag Samstag Sonntag".split()
    datum = f"{days[NOW.weekday()]}, {NOW.day}. {months[NOW.month-1]} {NOW.year}, {NOW:%H:%M} Uhr"
    page = {"NEWS": sec, "DATUM": datum, "WETTER": html.escape(wtxt or "Wetterdaten derzeit nicht verfügbar."),
            "ALERTS": f"<div class='alert' role='alert'><h2>Wetterwarnung</h2><ul>{alert_html}</ul></div>" if alerts else "",
            "PREISE": rows, "HINWEIS": html.escape(hint), "BRIEF": letter(), "CAMS": cams(), "YEAR": str(NOW.year)}
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

if __name__ == "__main__":
    build()
