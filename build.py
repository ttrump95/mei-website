#!/usr/bin/env python3
"""
Miller Engineering website generator.
Reads content/ (JSON data files, editable via Decap CMS) + templates/,
writes a complete static site to _site/. Standard library only.

  content/projects/*.json  -> cards, map markers, project pages
  content/team/*.json       -> team grid
Run:  python3 build.py
"""
import json, os, re, math, html, shutil
from collections import OrderedDict

ROOT = os.path.dirname(os.path.abspath(__file__))
T    = os.path.join(ROOT, "templates")
CONTENT = os.path.join(ROOT, "content")
STATIC  = os.path.join(ROOT, "static")
ADMIN   = os.path.join(ROOT, "admin")
OUT  = os.path.join(ROOT, "_site")

def tmpl(name):
    with open(os.path.join(T, name), encoding="utf-8") as f: return f.read()

def esc(s): return html.escape(str(s), quote=False)

# ---------------------------------------------------------------- shell
CSS = tmpl("site.css")
# real-photo support: dark gradient over an uploaded image so text stays legible
CSS += "\n.logo-img{height:44px;width:auto;display:block}"
CSS += ("\n.ph.has-photo{background-size:cover;background-position:center}"
        "\n.ph.has-photo::before{background:linear-gradient(180deg,rgba(12,39,64,.10),rgba(12,39,64,.72))}")
# project photo gallery
CSS += ("\n.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}"
        "\n.gitem{display:block;text-decoration:none;color:inherit}"
        "\n.gitem .gimg{display:block;width:100%;aspect-ratio:4/3;background-size:cover;background-position:center;border-radius:10px;box-shadow:0 2px 10px rgba(12,39,64,.12);transition:transform .2s,box-shadow .2s}"
        "\n.gitem:hover .gimg{transform:translateY(-3px);box-shadow:0 10px 24px rgba(12,39,64,.22)}"
        "\n.gitem .gcap{display:block;margin-top:8px;font-size:14px;color:#5a6b7a;line-height:1.4}")
NAV    = tmpl("nav.html")
FOOTER = tmpl("footer.html")
REVEAL = tmpl("reveal.html")

def page(title, body):
    return (f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title><style>{CSS}</style></head><body>
{NAV}{body}{FOOTER}
{REVEAL}
</body></html>""")

def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f: f.write(content)

# ---------------------------------------------------------------- content
def load(folder):
    items=[]
    d=os.path.join(CONTENT, folder)
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                items.append(json.load(f))
    return items

projects = load("projects")
team     = load("team")

def market_key(m):
    ml=m.lower()
    if "healthcare" in ml: return "healthcare"
    if "education"  in ml: return "education"
    return "government"

def ph(p, label="PHOTO"):
    key=market_key(p.get("market",""))
    if p.get("image"):
        return f'<div class="ph {key} has-photo" style="background-image:url(\'{p["image"]}\')"></div>'
    return f'<div class="ph {key}"><span class="tag">{label}</span></div>'

def card(p):
    return (f'<a class="card" href="project-{p["slug"]}.html">'
            f'{ph(p)}<div class="grad"></div>'
            f'<div class="meta"><span class="mk">{esc(p["market"])}</span>'
            f'<h3>{esc(p["title"])}</h3><div class="loc">{esc(p["location"])}</div></div></a>')

# ---------------------------------------------------------------- map projection (verified)
minlon,maxlon,minlat,maxlat = -82.621743,-77.719881,37.20291,40.636951
meanlat=(minlat+maxlat)/2; k=math.cos(math.radians(meanlat))
PAD=40.0; W=1000.0
scale=(W-2*PAD)/((maxlon-minlon)*k)
H=(maxlat-minlat)*scale+2*PAD
def pct(lon,lat):
    x=(lon-minlon)*k*scale+PAD; y=(maxlat-lat)*scale+PAD
    return round(x/W*100,2), round(y/H*100,2)

def build_markers():
    cities=OrderedDict()
    for p in projects:
        cities.setdefault(p.get("city") or p["location"], []).append(p)
    out=""
    for city, ps in cities.items():
        xp,yp = pct(ps[0]["lng"], ps[0]["lat"])
        items="".join(
            f'<a class="pj" href="project-{p["slug"]}.html" onclick="event.stopPropagation()">'
            f'{esc(p["title"])}<span>{esc(p["market"])} · {esc(p["location"])}</span></a>'
            for p in ps)
        label=f'{len(ps)} project'+('s' if len(ps)>1 else '')
        out += (f'<div class="marker" data-city="{esc(city)}" style="left:{xp}%;top:{yp}%" onclick="mapPick(event,this)">'
                f'<div class="dot"></div><div class="city">{esc(city)}</div>'
                f'<div class="pop"><div class="pl">{esc(city)} · {label}</div>{items}'
                f'<div class="arr"></div></div></div>\n        ')
    return out

def build_list():
    out=""
    for p in sorted(projects, key=lambda x: x["title"].lower()):
        city=p.get("city") or p["location"]
        out += (f'<li class="pl-item" data-slug="{p["slug"]}" data-city="{esc(city)}" onclick="pickProject(this)">'
                f'<b>{esc(p["title"])}</b><span>{esc(p["market"])} · {esc(p["location"])}</span></li>')
    return out

# ---------------------------------------------------------------- build
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)

# HOME
featured = sorted([p for p in projects if p.get("featured")], key=lambda x: x.get("year",0), reverse=True)[:6]
feat_cards = "".join(card(p) for p in featured)
home_featured = (f'<section class="block" id="projects"><div class="wrap">\n'
    f'    <div class="sec-head"><span class="eyebrow">Featured Work</span>\n'
    f'      <h2 class="sect-title">Projects across the Mid-Atlantic</h2>\n'
    f'      <p class="lead">A selection of recent MEP work for state agencies, universities, school systems, and the military.</p></div>\n'
    f'    <div class="proj-grid">{feat_cards}</div>\n'
    f'    <div class="proj-foot"><a href="projects.html" class="btn btn-dark">See All Projects</a></div></div></section>')
home_body = (tmpl("home_hero.html")+tmpl("home_stats.html")+tmpl("home_services.html")
            +tmpl("home_markets.html")+home_featured+tmpl("home_about.html")+tmpl("home_cta.html"))
write("index.html", page("Miller Engineering, Inc. — MEP Consulting Engineers", home_body))

# PROJECTS (map + grid)
mapsec = (tmpl("projpage_map.html")
          .replace("{{MAP_SVG}}", tmpl("map_base.html"))
          .replace("{{MARKERS}}", build_markers())
          .replace("{{LIST_ITEMS}}", build_list()))
all_cards = "".join(card(p) for p in sorted(projects, key=lambda x: x.get("year",0), reverse=True))
gridsec = tmpl("projpage_grid.html").replace("{{CARDS}}", all_cards)
write("projects.html", page("Projects — Miller Engineering", mapsec+gridsec))

# STATIC PAGES
write("services.html", page("Services — Miller Engineering", tmpl("page_services.html")))
write("markets.html",  page("Markets — Miller Engineering",  tmpl("page_markets.html")))
write("contact.html",  page("Contact — Miller Engineering",  tmpl("page_contact.html")))
ty_body = ('\n  <section class="block navy" style="min-height:58vh;display:flex;align-items:center">'
    '<div class="wrap" style="max-width:720px;text-align:center">'
    '<span class="eyebrow dk">Message Sent</span>'
    '<h2 class="sect-title" style="color:#fff">Thank you — we\'ll be in touch</h2>'
    '<p class="lead" style="color:#cdd9e5">Your message has been sent to Miller Engineering. '
    'We\'ll get back to you shortly.</p>'
    '<div style="margin-top:24px"><a href="index.html" class="btn btn-gold">Back to Home</a> '
    '&nbsp;<a href="projects.html" class="btn btn-dark">See Our Work</a></div>'
    '</div></section>')
write("thank-you.html", page("Thank You — Miller Engineering", ty_body))

# TEAM
active = sorted([t for t in team if t.get("active", True)], key=lambda x: x.get("sort_order",99))
def person(t):
    img = (f'<div class="ph has-photo" style="background-image:url(\'{t["image"]}\')"><i></i></div>'
           if t.get("image") else '<div class="ph"><i></i></div>')
    return (f'<div class="person">{img}<b>{esc(t["name"])}</b>'
            f'<span class="r">{esc(t["role"])}</span><p>{esc(t["bio"])}</p></div>')
persons = "".join(person(t) for t in active)
team_grid = (f'<section class="block"><div class="wrap">\n'
    f'    <div class="sec-head"><span class="eyebrow">Our People</span>\n'
    f'      <h2 class="sect-title">The team</h2>\n'
    f'      <p class="lead">New staff are added here as the firm grows.</p></div>\n'
    f'    <div class="team-grid">{persons}</div></div></section>')
team_body = tmpl("team_intro.html")+team_grid+tmpl("team_cta.html")
write("team.html", page("About & Team — Miller Engineering", team_body))

# PROJECT DETAIL PAGES
def gallery_html(p):
    out=[]
    for g in (p.get("gallery") or []):
        src = g.get("image") if isinstance(g, dict) else g
        if not src: continue
        cap = (g.get("caption") if isinstance(g, dict) else "") or ""
        gcap = f'<span class="gcap">{esc(cap.strip())}</span>' if cap.strip() else ''
        out.append(f'<a class="gitem" href="{src}" target="_blank" rel="noopener">'
                   f'<span class="gimg" style="background-image:url(\'{src}\')"></span>{gcap}</a>')
    if not out: return ''
    return ('\n  <section class="block"><div class="wrap">\n'
            '    <div class="sec-head"><span class="eyebrow">Gallery</span>\n'
            '      <h2 class="sect-title">Project photos</h2></div>\n'
            f'    <div class="gallery">{"".join(out)}</div></div></section>')

def detail(p):
    related=[q for q in projects if q["slug"]!=p["slug"]][:3]
    rel="".join(card(q) for q in related)
    key=market_key(p["market"])
    hero_ph=(f'<div class="ph {key} has-photo" style="background-image:url(\'{p["image"]}\')"></div>'
             if p.get("image") else f'<div class="ph {key}"><span class="tag">PROJECT PHOTO</span></div>')
    paras="".join(f"<p>{esc(x.strip())}</p>" for x in str(p["overview"]).split("\n\n") if x.strip())
    body=(f'\n  <section class="detail-hero">{hero_ph}\n'
    f'    <div class="grad"></div><div class="wrap"><span class="eyebrow dk">{esc(p["market"])}</span>\n'
    f'      <h1>{esc(p["title"])}</h1></div></section>\n'
    f'  <div class="wrap"><div class="detail-body">\n'
    f'    <div class="copy"><h2>Project Overview</h2>\n      {paras}\n'
    f'      <p>Miller Engineering provided full MEP design and coordination, working within an occupied, in-service facility to minimize disruption while bringing systems up to current code.</p>\n'
    f'      <h2 style="margin-top:30px">Scope of Work</h2>\n'
    f'      <p>Mechanical and ventilation design, electrical power and distribution, plumbing coordination, and construction-phase administration including submittal review and site observation.</p></div>\n'
    f'    <aside class="factbox">\n'
    f'      <div class="row"><div class="k">Client</div><div class="v">{esc(p["client"])}</div></div>\n'
    f'      <div class="row"><div class="k">Location</div><div class="v">{esc(p["location"])}</div></div>\n'
    f'      <div class="row"><div class="k">Market</div><div class="v">{esc(p["market"])}</div></div>\n'
    f'      <div class="row"><div class="k">Year</div><div class="v">{esc(p["year"])}</div></div>\n'
    f'      <div class="row"><div class="k">Services</div><div class="v">{esc(p["services"])}</div></div>\n'
    f'    </aside></div>\n'
    f'    <div style="padding-bottom:20px"><a href="projects.html" class="btn btn-dark">← Back to Projects</a></div>\n'
    f'  </div>\n'
    f'{gallery_html(p)}'
    f'  <section class="block mist"><div class="wrap">\n'
    f'    <div class="sec-head"><span class="eyebrow">More Work</span>\n'
    f'      <h2 class="sect-title">Related projects</h2></div>\n'
    f'    <div class="proj-grid">{rel}</div></div></section>')
    write(f"project-{p['slug']}.html", page(f'{esc(p["title"])} — Miller Engineering', body))

for p in projects: detail(p)

# STATIC ASSETS + ADMIN
for src in (STATIC, ADMIN):
    if os.path.isdir(src):
        dest = OUT if src==STATIC else os.path.join(OUT, "admin")
        shutil.copytree(src, dest, dirs_exist_ok=True)

pages = [f for f in os.listdir(OUT) if f.endswith(".html")]
print(f"Built {len(pages)} pages into _site/  ({len(projects)} projects, {len(active)} people)")
for f in sorted(pages): print("  ", f)
