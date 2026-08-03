#!/usr/bin/env python3
import json, math, os, re

SITE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://pacidaict-star.github.io/pacida-asal-website/"

PACIDA_SLUGS = {"marsabit", "samburu", "isiolo", "borena"}


def meta_desc(text, limit=155):
    text = re.sub(r"<[^>]+>", "", text).replace("&mdash;", "—").replace("&amp;", "&").replace("&nbsp;", " ")
    text = re.sub(r"&\w+;", "", text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "…"

COUNTIES = json.load(open(os.path.join(SITE, "counties.json"), encoding="utf-8"))
BOUNDARIES_ALL = json.load(open(os.path.join(SITE, "assets", "boundaries.json"), encoding="utf-8"))
VILLAGES_ALL = json.load(open(os.path.join(SITE, "assets", "villages.json"), encoding="utf-8"))

# boundaries.js / villages.js are generated artifacts — keep them in sync with the
# full source JSON archives, but trimmed to only the regions actually on the site
BOUNDARIES = {k: v for k, v in BOUNDARIES_ALL.items() if k in COUNTIES}
open(os.path.join(SITE, "assets", "boundaries.js"), "w", encoding="utf-8").write(
    "const BOUNDARIES = " + json.dumps(BOUNDARIES, separators=(",", ":")) + ";\n"
)
VILLAGES = {k: v for k, v in VILLAGES_ALL.items() if k in COUNTIES}
open(os.path.join(SITE, "assets", "villages.js"), "w", encoding="utf-8").write(
    "const VILLAGES = " + json.dumps(VILLAGES, separators=(",", ":")) + ";\n"
)

# county_index.js powers the cross-page "jump to a county" search on every page
county_index = []
for slug, r in COUNTIES.items():
    county_index.append({"slug": slug, "name": r["title"], "asal": bool(r.get("asal"))})
county_index.sort(key=lambda c: c["name"])
open(os.path.join(SITE, "assets", "county_index.js"), "w", encoding="utf-8").write(
    "const COUNTY_INDEX = " + json.dumps(county_index, separators=(",", ":")) + ";\n"
)


def bbox_center_zoom(geom):
    """Derive a sensible map center + zoom from a county's boundary geometry."""
    pts = []

    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)

    walk(geom["coordinates"])
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    cx = (min(lons) + max(lons)) / 2
    cy = (min(lats) + max(lats)) / 2
    span = max(max(lons) - min(lons), max(lats) - min(lats))
    zoom = round(9.2 - math.log2(max(span, 0.1)))
    zoom = max(6, min(11, zoom))
    return [round(cy, 3), round(cx, 3)], zoom


def combined_bbox_center_zoom(geoms, pad=1.15):
    """Center/zoom that fits several boundary geometries at once (used for the
    homepage/impact map so it opens framed on PACIDA's operational area)."""
    pts = []

    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    for g in geoms:
        walk(g["coordinates"])
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    cx, cy = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2
    span = max(max(lons) - min(lons), max(lats) - min(lats)) * pad
    zoom = max(5, min(11, round(9.2 - math.log2(max(span, 0.1)))))
    return [round(cy, 3), round(cx, 3)], zoom


PACIDA_CENTER, PACIDA_ZOOM = combined_bbox_center_zoom([BOUNDARIES[s] for s in PACIDA_SLUGS if s in BOUNDARIES])


DROUGHT_TIMELINE = [
 ["1999–2000","Severe Horn drought; emergency operations across northern Kenya and southern Ethiopia."],
 ["2005–06","Failed short rains; major livestock losses in Marsabit and Borena; catalyst period for founding of local NGOs including PACIDA (2008)."],
 ["2008–09","Back-to-back poor seasons; food-insecure caseload across ASALs peaks above 3.8 million."],
 ["2010–11","Horn of Africa famine — the region's worst crisis in 60 years; famine declared in Somalia, Emergency phases across the cross-border cluster."],
 ["2016–17","Drought emergency declared in Kenya; GAM breaches 30% in parts of the north; massive livestock deaths in Borena."],
 ["2020–23","Five consecutive failed rainy seasons — worst drought in 40 years. 3.3+ million livestock deaths in southern Ethiopia; 4.4 M people on relief in Kenya's ASALs; Borena cattle herds cut by over half."],
 ["2023–24","El Niño whiplash: catastrophic floods (Isiolo among worst-hit) immediately after drought — the twin-disaster pattern."],
 ["2025–26","Failed 2025 short rains; NDMA moved 12–13 counties to Alert and 4 to Alarm by Feb 2026; 3.3 M food insecure. March 2026 rains brought partial, uneven relief; long-term recovery deficit persists.","now"]
]


def seasoncal():
    mo = [("J","Jilaal dry","dry"),("F","dry","dry"),("M","Long rains / Ganna","rain"),("A","Long rains","rain"),("M","Long rains","rain"),
          ("J","Adolessa dry","dry"),("J","dry","dry"),("A","dry","dry"),("S","dry","dry"),
          ("O","Short rains / Hagayya","rain"),("N","Short rains","rain"),("D","Bona dry","dry")]
    note = ("Bimodal ASAL calendar: long rains Mar&ndash;May (Ganna in Borana), short rains Oct&ndash;Dec (Hagayya). Both seasons "
            "must perform for pasture recovery; a single failed season triggers Alert, consecutive failures cascade to Alarm/Emergency.")
    cells = "".join('<div class="mo %s">%s<small>%s</small></div>' % (c, m, l) for m, l, c in mo)
    return '<div class="season">%s</div><div class="season-note">%s</div>' % (cells, note)


def fmtnum(v):
    if isinstance(v, int):
        return "{:,}".format(v)
    return str(v)


def navbar(rid):
    home_active = ' class="active"' if rid == "home" else ""
    return ('<a href="index.html"%s>&larr; PACIDA\'s operational areas</a>'
            '<a href="impact.html">PACIDA Impact Dashboard</a>') % home_active


def page(rid, r):
    sub_rows = ""
    for row in r["subcounties"]:
        name, hq, pop, hh, lz, vill = row
        pops = fmtnum(pop)
        hhs = fmtnum(hh)
        sub_rows += ("<tr><td><b>%s</b><br><small>HQ: %s</small></td><td class='mono'>%s</td>"
                     "<td class='mono'>%s</td><td>%s</td><td>%s</td></tr>") % (name, hq, pops, hhs, lz, vill)
    subnote = ('<p style="font-size:12px;color:var(--faint);margin-top:8px">%s</p>' % r["subnote"]) if r.get("subnote") else ""

    lz_rows = "".join(('<div class="lz-row"><div>%s</div><div class="lz-bar">'
                       '<div class="lz-fill" style="width:%d%%;background:%s"></div></div>'
                       '<div class="lz-pct">%d%%</div></div>') % (n, p, c, p) for n, p, c in r["livelihoods"])

    sect = "".join('<details class="acc"><summary>%s</summary><div class="acc-body">%s</div></details>' % (t, x) for t, x in r["sectors"])

    tl_items = "".join(
        '<div class="tl%s"><div class="yr">%s</div><div class="tx">%s</div></div>' % ((" now" if len(item) > 2 else ""), item[0], item[1])
        for item in DROUGHT_TIMELINE
    )
    timeline_panel = ('<div class="panel glass"><h2>Drought history &mdash; the recurrence the index is built for</h2>'
                       '<div class="timeline">%s</div></div>') % tl_items

    if r.get("pacida"):
        pacida_panel = '<div class="panel glass"><h2>PACIDA in %(title)s</h2><p>%(pacida)s</p></div>' % r
        sources_pacida = ('<div class="src"><b>Programmes</b><span>PACIDA annual reports and programme pages. </span>'
                           '<a href="https://pacida.org" target="_blank" rel="noopener">pacida.org</a></div>')
        interv_panel = ('<div class="panel glass"><h2>PACIDA interventions here <span class="tag">'
                         '<a href="impact.html" style="color:var(--alert)">full impact dashboard &rarr;</a></span></h2>'
                         '<p>Real projects from PACIDA\'s own project register, pinned where their title names a specific '
                         'site in %(title)s. Star markers on the map are PACIDA field presence/offices.</p>'
                         '<div class="interv-list" id="intervList"></div></div>') % r
        interventions_js = ('const intervLayer = drawInterventionLayer(map, RID);\n'
                             'intervLayer.addTo(map);\n'
                             'const heatLayer = drawInterventionHeat([RID]).addTo(map);\n'
                             'layersControl.addOverlay(heatLayer, "Intervention density (heat)");\n'
                             'layersControl.addOverlay(intervLayer, "PACIDA interventions");\n'
                             'renderInterventionList("intervList", RID);')
    else:
        pacida_panel = ""
        sources_pacida = ""
        interv_panel = ""
        interventions_js = ""

    sites_json = json.dumps(r["sites"])
    nav = navbar(rid)
    center, zoom = bbox_center_zoom(BOUNDARIES[rid]) if rid in BOUNDARIES else ([r["hq"]["lat"], r["hq"]["lon"]], 8)

    return TEMPLATE % dict(
        rid=rid, title=r["title"], country=r["country"],
        nav=nav, intro=r["intro"],
        center=json.dumps(center), zoom=zoom,
        hqname=r["hq"]["name"], hqlat=r["hq"]["lat"], hqlon=r["hq"]["lon"],
        households=fmtnum(r["households"]), population=fmtnum(r["population"]),
        area=r["area"], density=r["density"], hhsize=r["hhsize"],
        poverty=r["poverty"], staticVuln=r["staticVuln"], phase=r["phase"], gam=r["gam"],
        sub_rows=sub_rows, subnote=subnote, lz_rows=lz_rows, sectors=sect,
        seasoncal=seasoncal(), timeline_panel=timeline_panel, pacida_panel=pacida_panel,
        sources_pacida=sources_pacida, sites_json=sites_json,
        interv_panel=interv_panel, interventions_js=interventions_js,
        meta_desc=meta_desc(r["intro"]), canonical_url=BASE_URL + rid + ".html", base_url=BASE_URL
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s — Kenya ASAL Climate Watch</title>
<meta name="description" content="%(meta_desc)s">
<meta name="theme-color" content="#34B44B">
<meta property="og:type" content="website">
<meta property="og:title" content="%(title)s — Kenya ASAL Climate Watch">
<meta property="og:description" content="%(meta_desc)s">
<meta property="og:url" content="%(canonical_url)s">
<meta property="og:image" content="%(base_url)sassets/favicon-512.png">
<meta property="og:site_name" content="Kenya ASAL Climate Watch">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="%(title)s — Kenya ASAL Climate Watch">
<meta name="twitter:description" content="%(meta_desc)s">
<meta name="twitter:image" content="%(base_url)sassets/favicon-512.png">
<link rel="canonical" href="%(canonical_url)s">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" type="image/png" sizes="512x512" href="assets/favicon-512.png">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to main content</a>

<div id="map" role="application" aria-label="Aerial map of %(title)s"></div>

<div class="overlay">

<header class="glass">
  <div class="brand">
    <a href="index.html"><img class="brand-logo" src="assets/pacida-logo.png" alt="PACIDA"></a>
    <h1><a href="index.html">Kenya <span>&middot;</span> ASAL Climate Watch</a></h1>
    <div class="sub">%(title)s &middot; %(country)s</div>
  </div>
  <nav class="site">%(nav)s</nav>
  <div class="head-right">
    <div class="search-wrap">
      <input type="text" id="searchBox" placeholder="Jump to a county or site&hellip;" aria-label="Search counties and monitoring sites">
      <div class="search-results" id="searchResults"></div>
    </div>
    <div class="livepill"><span class="dot" id="liveDot"></span><span id="liveState" role="status" aria-live="polite">Live &middot; Open-Meteo</span></div>
    <div class="clock mono" id="clock">--:--:-- EAT</div>
    <button class="iconbtn" id="unitToggle" type="button" title="Toggle °C/°F, mm/in">&deg;C &middot; mm</button>
    <button class="iconbtn" id="glossaryBtn" type="button" title="Open glossary of terms">Glossary</button>
    <button class="iconbtn" id="exportBtn" type="button" title="Download current live readings as CSV">Export CSV</button>
    <button class="refresh" id="refreshBtn" type="button">Refresh now</button>
  </div>
</header>

<div class="gl-panel" id="glossaryPanel" aria-label="Glossary of terms">
  <div class="gl-head"><h3>Glossary</h3><button class="gl-close" type="button" aria-label="Close glossary">&times;</button></div>
  <input class="gl-search" type="text" placeholder="Filter terms&hellip;" aria-label="Filter glossary terms">
  <div class="gl-body"></div>
</div>
<div class="gl-backdrop" id="glBackdrop"></div>

<div class="strip">
  <div class="cell glass"><div class="k">Need index (live)</div><div class="v" id="needV">&mdash;</div><div class="n" id="needN">recalculating from live weather</div></div>
  <div class="cell glass"><div class="k">Now at %(hqname)s</div><div class="v" id="tempV">&mdash;</div><div class="n" id="tempN">&mdash;</div></div>
  <div class="cell glass"><div class="k">Rain, past 30 days</div><div class="v" id="rainV">&mdash;</div><div class="n">vs ~60 mm ASAL expectation</div></div>
  <div class="cell glass"><div class="k">Topsoil moisture</div><div class="v" id="soilV">&mdash;</div><div class="n">0&ndash;7 cm &middot; VCI proxy</div></div>
  <div class="cell glass"><div class="k">Households</div><div class="v">%(households)s</div><div class="n">Population %(population)s</div></div>
  <div class="cell glass"><div class="k">Drought phase</div><div class="v" style="font-size:15px;font-family:'Archivo'">%(phase)s</div><div class="n">Poverty %(poverty)s%%</div></div>
</div>

<main id="main-content">
<div class="hero-grid">
  <div class="map-window">
    <div class="map-legend glass">
      <h4>Monitoring sites</h4>
      <div class="lg-row"><span class="lg-swatch" style="background:var(--emergency)"></span> Critical (75&ndash;100)</div>
      <div class="lg-row"><span class="lg-swatch" style="background:var(--alarm)"></span> High (60&ndash;74)</div>
      <div class="lg-row"><span class="lg-swatch" style="background:var(--alert)"></span> Elevated (45&ndash;59)</div>
      <div class="lg-row"><span class="lg-swatch" style="background:var(--normal)"></span> Watch (0&ndash;44)</div>
      <div class="lg-note">Each dot is a settlement-level monitoring point with its own live weather feed. Shaded outline = %(title)s. Pan &amp; zoom anywhere outside the glass panels. Site coordinates are indicative (&plusmn;2&ndash;5 km; weather grid resolution ~11 km).</div>
    </div>
  </div>

  <div class="cards">
    <div class="card glass">
      <div class="card-top"><div><h3>%(title)s briefing</h3><div class="zone">%(country)s &middot; area %(area)s &middot; density %(density)s &middot; avg household %(hhsize)s persons</div></div></div>
      <p style="font-size:13.5px;color:var(--muted);margin-top:10px">%(intro)s</p>
      <div class="hh-line"><span>GAM (acute malnutrition): <b style="font-family:'Archivo'">%(gam)s</b></span></div>
    </div>
    <div class="card glass" id="hqCard">
      <div class="card-top"><div><h3>Live conditions &mdash; %(hqname)s</h3><div class="zone">County/zone reference station</div></div><span class="badge" id="hqBadge" style="background:var(--alert)">&hellip;</span></div>
      <div class="gauge"><div class="gauge-track"><div class="gauge-marker" id="hqMarker" style="left:0%%"></div></div>
      <div class="gauge-labels"><span>Watch</span><span>Elevated</span><span>High</span><span>Critical</span></div></div>
      <div class="metrics" id="hqMetrics"><div class="loading">Fetching live weather&hellip;</div></div>
      <div class="spark"><div class="mk">Rainfall &mdash; past 14 d &amp; next 7 d forecast (mm/day)</div><div id="hqSpark"></div></div>
    </div>
  </div>
</div>

<div class="wide">

  <div class="panel glass">
    <h2>Live conditions by settlement <span class="tag">every dot refreshes with the page</span></h2>
    <div class="sites" id="siteGrid"></div>
  </div>

  <div class="panel glass">
    <h2>Sub-units, households &amp; key settlements <span class="tag">KNBS 2019 census / indicative estimates</span></h2>
    <div class="table-scroll">
    <table class="ptable">
      <thead><tr><th>Sub-county / woreda</th><th>Population</th><th>Households</th><th>Livelihood zone</th><th>Key settlements &amp; villages (indicative)</th></tr></thead>
      <tbody>%(sub_rows)s</tbody>
    </table>
    </div>
    %(subnote)s
  </div>

  <div class="panel glass">
    <h2>Livelihood zones <span class="tag">FEWS NET-style livelihood zoning, indicative shares</span></h2>
    <div class="lz">%(lz_rows)s</div>
  </div>

  <div class="panel glass">
    <h2>Seasonal calendar</h2>
    %(seasoncal)s
  </div>

  <div class="panel glass">
    <h2>12-month rainfall history <span class="tag">at %(hqname)s &middot; loaded once per visit</span></h2>
    <div id="histChart"><div class="loading">Loading 12-month rainfall history&hellip;</div></div>
    <p class="hist-cap">Monthly totals from Open-Meteo's historical archive &mdash; shows whether this year's rains actually arrived on schedule.</p>
  </div>

  <div class="panel glass">
    <h2>Sector deep-dive <span class="tag">click a heading to expand</span></h2>
    <div class="acc-list">%(sectors)s</div>
  </div>

  %(timeline_panel)s

  %(interv_panel)s

  %(pacida_panel)s

  <div class="panel glass">
    <h2>Sources</h2>
    <div class="src-grid">
      <div class="src"><b>Live weather</b><span>Open-Meteo API per settlement point; auto-refresh every 10 minutes. </span><a href="https://open-meteo.com" target="_blank" rel="noopener">open-meteo.com</a></div>
      <div class="src"><b>Boundaries</b><span>geoBoundaries open geodata project (RCMRD / Africa GeoPortal source). </span><a href="https://www.geoboundaries.org" target="_blank" rel="noopener">geoboundaries.org</a></div>
      <div class="src"><b>Population &amp; households</b><span>Kenya 2019 Population &amp; Housing Census (KNBS). </span><a href="https://www.knbs.or.ke" target="_blank" rel="noopener">knbs.or.ke</a></div>
      <div class="src"><b>Drought &amp; food security</b><span>NDMA monthly bulletins &amp; county early-warning (23 ASAL counties); IPC analyses; FEWS NET East Africa. </span><a href="https://ndma.go.ke" target="_blank" rel="noopener">ndma.go.ke</a></div>
      %(sources_pacida)s
    </div>
  </div>
</div>
</main>

<footer class="glass">
  <div class="foot-brand"><img class="brand-logo" src="assets/pacida-logo.png" alt="PACIDA"><span>Kenya ASAL Climate Watch &middot; %(title)s detail &middot; monitoring prototype, in partnership with PACIDA &mdash; deployment decisions require ground-truthing</span></div>
  <div class="mono" id="footTime"></div>
</footer>

</div><!-- /overlay -->

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script src="assets/boundaries.js"></script>
<script src="assets/county_index.js"></script>
<script src="assets/villages.js"></script>
<script src="assets/interventions.js"></script>
<script src="assets/common.js"></script>
<script>
const RID = "%(rid)s";
const STATIC_VULN = %(staticVuln)s;
const SITES = %(sites_json)s;  /* [name, lat, lon, note] */
const HQ = {name:"%(hqname)s", lat:%(hqlat)s, lon:%(hqlon)s};

startClock();
const {map, layersControl} = makeGlassMap(%(center)s, %(zoom)s);

/* region outline */
if (BOUNDARIES[RID]) {
  L.geoJSON({type:"Feature",geometry:BOUNDARIES[RID]},{
    style:{color:"#FFFFFF",weight:1.8,opacity:.9,fillColor:"#F0B22E",fillOpacity:.06,
           dashArray:RID==="borena"?"6 5":null}
  }).addTo(map);
}
attachVillageLayer(map, RID);
%(interventions_js)s

const siteLayer = L.layerGroup().addTo(map);
const siteState = SITES.map(s=>({name:s[0],lat:s[1],lon:s[2],note:s[3],live:null}));
const siteMarkers = {};
let lastHQW = null;

function drawSites(){
  siteLayer.clearLayers();
  siteState.forEach(s=>{
    const need = s.live? s.live.need : null;
    const band = need!=null? needBand(need):"elevated";
    const color = PHASE_COLORS[band];
    const m = L.circleMarker([s.lat,s.lon],{radius:9,color:"#fff",weight:1.5,fillColor:color,fillOpacity:.85});
    m.bindPopup("<h4>"+s.name+"</h4>"
      +"<div class='pop-k'>"+s.note+"</div>"
      +(s.live? "<div><span class='pop-k'>Need:</span> <span class='pop-v'>"+need+" / 100 &middot; "+bandLabel(band)+"</span></div>"
        +"<div><span class='pop-k'>Now:</span> <span class='pop-v'>"+fmtTemp(s.live.temp)+" &middot; "+s.live.rh+"%% RH</span></div>"
        +"<div><span class='pop-k'>Rain 30 d:</span> <span class='pop-v'>"+fmtRain(s.live.rain30)+"</span></div>"
        +"<div><span class='pop-k'>Soil:</span> <span class='pop-v'>"+(s.live.soil*100).toFixed(1)+"%%</span></div>"
        : "<div class='pop-k'>loading&hellip;</div>"));
    const label = L.marker([s.lat,s.lon],{interactive:false,
      icon:L.divIcon({className:"",html:'<div class="site-label">'+s.name+'</div>',iconAnchor:[-10,7]})});
    siteLayer.addLayer(m); siteLayer.addLayer(label);
    siteMarkers[s.name] = m;
  });
}
drawSites();

function renderSiteGrid(){
  const g = document.getElementById("siteGrid");
  const order=[...siteState].sort((a,b)=>((b.live?b.live.need:-1)-(a.live?a.live.need:-1)));
  g.innerHTML = order.map(s=>{
    const need = s.live? s.live.need:null;
    const band = need!=null? needBand(need):"elevated";
    return '<div class="site-card">'
      +'<h4><span class="site-dot" style="background:'+PHASE_COLORS[band]+'"></span>'+s.name+'</h4>'
      +'<div class="sc-sub">'+s.note+'</div>'
      +(s.live?
         '<div class="site-row"><span>Need index</span><b>'+need+' &middot; '+bandLabel(band)+'</b></div>'
        +'<div class="site-row"><span>Temp now</span><b>'+fmtTemp(s.live.temp)+'</b></div>'
        +'<div class="site-row"><span>Rain 30 d</span><b>'+fmtRain(s.live.rain30)+'</b></div>'
        +'<div class="site-row"><span>Soil 0&ndash;7 cm</span><b>'+(s.live.soil*100).toFixed(1)+'%%</b></div>'
        +'<div class="site-row"><span>7-d max avg</span><b>'+fmtTemp(s.live.tmax7)+'</b></div>'
        : '<div class="loading">loading&hellip;</div>')
      +'</div>';
  }).join("");
}
renderSiteGrid();

function renderHQ(w){
  lastHQW = w;
  const need = w.need, band = needBand(need);
  document.getElementById("hqBadge").innerHTML = bandLabel(band)+" &middot; "+need;
  document.getElementById("hqBadge").style.background = PHASE_COLORS[band];
  document.getElementById("hqMarker").style.left = need+"%%";
  document.getElementById("hqMetrics").innerHTML =
     '<div class="m"><div class="mk">Now</div><div class="mv">'+fmtTemp(w.temp)+'</div></div>'
    +'<div class="m"><div class="mk">Rain 30 d</div><div class="mv">'+fmtRain(w.rain30)+'</div></div>'
    +'<div class="m"><div class="mk">Soil 0&ndash;7 cm</div><div class="mv">'+(w.soil*100).toFixed(1)+'<small>%%</small></div></div>'
    +'<div class="m"><div class="mk">7-d max avg</div><div class="mv">'+fmtTemp(w.tmax7)+'</div></div>';
  document.getElementById("hqSpark").innerHTML = sparkline(w.dailyRain, w.splitIdx);
  document.getElementById("needV").textContent = need;
  document.getElementById("needN").textContent = bandLabel(band)+" &mdash; blended NDMA/IPC-aligned score";
  document.getElementById("tempV").textContent = fmtTemp(w.temp);
  document.getElementById("tempN").textContent = w.rh+"%% RH · wind "+w.wind.toFixed(0)+" km/h";
  document.getElementById("rainV").textContent = fmtRain(w.rain30);
  document.getElementById("soilV").textContent = (w.soil*100).toFixed(1)+"%%";
}

document.addEventListener("units-changed", ()=>{
  if(lastHQW) renderHQ(lastHQW);
  drawSites(); renderSiteGrid();
});

attachUnitToggle();
attachGlossary();
attachSearch(
  ()=>[
    ...COUNTY_INDEX.filter(c=>c.slug!==RID).map(c=>({id:c.slug, label:c.name, kind:"county"})),
    ...siteState.map(s=>({id:s.name, label:s.name+" — "+s.note, kind:"site"}))
  ],
  m=>{
    if(m.kind==="county"){ window.location.href = m.id + ".html"; return; }
    const s = siteState.find(x=>x.name===m.id);
    if(!s) return;
    map.flyTo([s.lat,s.lon],10,{duration:1});
    const mk = siteMarkers[s.name]; if(mk) mk.openPopup();
  }
);

document.getElementById("exportBtn").addEventListener("click", ()=>{
  const rows = [["Site","Lat","Lon","Note","Need index","Band","Temp C","RH %%","Rain 30d mm","Soil 0-7cm %%","7d max avg C"]];
  siteState.forEach(s=>{
    const w = s.live;
    rows.push([s.name, s.lat, s.lon, s.note,
      w?w.need:"", w?bandLabel(needBand(w.need)):"",
      w?w.temp.toFixed(1):"", w?w.rh:"", w?w.rain30.toFixed(1):"", w?(w.soil*100).toFixed(1):"", w?w.tmax7.toFixed(1):""]);
  });
  downloadCSV("%(rid)s-live-readings.csv", rows);
});

fetchMonthlyRain(HQ.lat, HQ.lon).then(data=>{
  document.getElementById("histChart").innerHTML = monthChart(data);
}).catch(e=>{
  console.error("history",e);
  document.getElementById("histChart").innerHTML = '<div class="loading">History unavailable &mdash; check connection</div>';
});

async function refreshAll(){
  const st=document.getElementById("liveState"), dotEl=document.getElementById("liveDot");
  st.textContent="Updating…";
  try{
    const hqW = await fetchPoint(HQ.lat, HQ.lon);
    hqW.need = computeNeed(STATIC_VULN, hqW);
    renderHQ(hqW);
    await Promise.all(siteState.map(async s=>{
      try{
        const w = await fetchPoint(s.lat, s.lon);
        w.need = computeNeed(STATIC_VULN, w);
        s.live = w;
      }catch(e){ console.error(s.name, e); }
    }));
    drawSites(); renderSiteGrid();
    st.textContent="Live · Open-Meteo";
    dotEl.style.background="var(--normal)";
  }catch(e){
    console.error(e);
    st.textContent="Feed unavailable — check connection";
    dotEl.style.background="var(--emergency)";
  }
}

document.getElementById("refreshBtn").addEventListener("click",refreshAll);
refreshAll();
setInterval(refreshAll, 10*60*1000);
</script>
</body>
</html>
"""

def build_index():
    lean = []
    for slug, r in COUNTIES.items():
        site_names = [s[0] for s in r["sites"][:4]]
        lean.append(dict(
            id=slug, name=r["title"], country=r["country"],
            zone=r["country"] + " · " + ", ".join(site_names),
            lat=r["hq"]["lat"], lon=r["hq"]["lon"],
            households=r["households"], population=r["population"],
            povertyRate=r["poverty"], droughtPhase=r["phase"], staticVuln=r["staticVuln"],
            asal=bool(r.get("asal")), pacida=slug in PACIDA_SLUGS,
            sites=[s[0] for s in r["sites"]]
        ))
    lean.sort(key=lambda r: r["name"])
    updates = [[yr, tx, len(item) > 2] for item in DROUGHT_TIMELINE for yr, tx in [item[:2]]]
    out = INDEX_TEMPLATE % dict(
        regions_json=json.dumps(lean, separators=(",", ":")),
        updates_json=json.dumps(updates, separators=(",", ":")),
        center=json.dumps(PACIDA_CENTER), zoom=PACIDA_ZOOM, base_url=BASE_URL
    )
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(out)
    print("index.html", len(out), "bytes")


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kenya ASAL Climate Watch — Live County Dashboard</title>
<meta name="description" content="Live drought and climate intervention dashboard for PACIDA's operational area — Marsabit, Samburu and Isiolo counties in Kenya, and the cross-border Borena Zone of southern Ethiopia.">
<meta name="theme-color" content="#34B44B">
<meta property="og:type" content="website">
<meta property="og:title" content="Kenya ASAL Climate Watch — Live County Dashboard">
<meta property="og:description" content="Live drought and climate intervention dashboard for PACIDA's operational area — Marsabit, Samburu and Isiolo counties in Kenya, and the cross-border Borena Zone of southern Ethiopia.">
<meta property="og:url" content="%(base_url)s">
<meta property="og:image" content="%(base_url)sassets/favicon-512.png">
<meta property="og:site_name" content="Kenya ASAL Climate Watch">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Kenya ASAL Climate Watch — Live County Dashboard">
<meta name="twitter:description" content="Live drought and climate intervention dashboard for PACIDA's operational area in northern Kenya and southern Ethiopia.">
<meta name="twitter:image" content="%(base_url)sassets/favicon-512.png">
<link rel="canonical" href="%(base_url)s">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" type="image/png" sizes="512x512" href="assets/favicon-512.png">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to main content</a>

<div id="map" role="application" aria-label="Map of PACIDA's operational area"></div>

<div class="overlay">

<header class="glass">
  <div class="brand">
    <img class="brand-logo" src="assets/pacida-logo.png" alt="PACIDA">
    <h1>Kenya <span>·</span> ASAL Climate Watch</h1>
    <div class="sub">PACIDA's operational area &middot; Marsabit, Samburu, Isiolo &amp; the Borena Zone (S. Ethiopia) &middot; live intervention monitor</div>
  </div>
  <nav class="site">
    <a href="#pacida-section">Operational areas</a>
    <a href="impact.html">PACIDA Impact Dashboard</a>
    <a href="#about-section">About</a>
  </nav>
  <div class="head-right">
    <div class="search-wrap">
      <input type="text" id="searchBox" placeholder="Jump to a county…" aria-label="Search counties">
      <div class="search-results" id="searchResults"></div>
    </div>
    <div class="livepill"><span class="dot" id="liveDot"></span><span id="liveState" role="status" aria-live="polite">Live · Open-Meteo feed</span></div>
    <div class="clock mono" id="clock">--:--:-- EAT</div>
    <button class="iconbtn" id="unitToggle" type="button" title="Toggle °C/°F, mm/in">°C · mm</button>
    <button class="iconbtn" id="glossaryBtn" type="button" title="Open glossary of terms">Glossary</button>
    <button class="iconbtn" id="exportBtn" type="button" title="Download current live readings as CSV">Export CSV</button>
    <button class="refresh" id="refreshBtn" type="button">Refresh now</button>
  </div>
</header>

<div class="gl-panel" id="glossaryPanel" aria-label="Glossary of terms">
  <div class="gl-head"><h3>Glossary</h3><button class="gl-close" type="button" aria-label="Close glossary">&times;</button></div>
  <input class="gl-search" type="text" placeholder="Filter terms…" aria-label="Filter glossary terms">
  <div class="gl-body"></div>
</div>
<div class="gl-backdrop" id="glBackdrop"></div>

<div class="strip" id="strip">
  <div class="cell glass"><div class="k">PACIDA operational areas</div><div class="v">3<span style="font-size:14px;color:var(--muted)"> + Borena</span></div><div class="n">Marsabit, Samburu, Isiolo counties &amp; the Borena cross-border zone</div></div>
  <div class="cell glass"><div class="k">Kenya households</div><div class="v" id="totHH">—</div><div class="n">KNBS 2019 census, 3 counties</div></div>
  <div class="cell glass"><div class="k">Kenya population</div><div class="v" id="totPop">—</div><div class="n">KNBS 2019 census, 3 counties</div></div>
  <div class="cell glass"><div class="k">Zones at Alert+</div><div class="v" id="zonesAlert">—</div><div class="n">Of NDMA/IPC-monitored zones</div></div>
  <div class="cell glass"><div class="k">Avg. need index (live)</div><div class="v" id="avgNeed">—</div><div class="n">0–100 · recalculated from live weather</div></div>
  <div class="cell glass"><div class="k">Last data refresh</div><div class="v mono" id="lastRef" style="font-size:16px">—</div><div class="n">Auto-refreshes every 10 min</div></div>
</div>

<main id="main-content">

<div class="entry-grid" style="padding-top:22px">
  <div class="entry-card glass current">
    <span class="entry-eyebrow">01 &middot; You are here</span>
    <h3>Live Intervention Map</h3>
    <p>Real-time weather, drought-need scoring and PACIDA's intervention footprint across all four operational areas.</p>
  </div>
  <a class="entry-card glass" href="impact.html">
    <span class="entry-eyebrow">02</span>
    <h3>PACIDA Impact Dashboard<span class="arrow-mark">&rarr;</span></h3>
    <p>236 real projects, FY2010&ndash;FY2026 &mdash; donors, themes, achievements and where the work has actually happened.</p>
  </a>
  <a class="entry-card glass" href="#about-section">
    <span class="entry-eyebrow">03</span>
    <h3>About &amp; Methodology<span class="arrow-mark">&rarr;</span></h3>
    <p>How the Need Index is calculated, where the data comes from, and PACIDA's role in this project.</p>
  </a>
</div>

<div class="wide" style="padding-top:0">
  <div class="panel glass">
    <h2>Latest updates <span class="tag">drought &amp; recovery timeline</span></h2>
    <div class="updates-carousel" id="updatesCarousel" role="region" aria-roledescription="carousel" aria-label="Latest updates" tabindex="0">
      <button class="uc-nav uc-prev" type="button" aria-label="Previous update">&larr;</button>
      <div class="uc-slide" id="ucSlide">
        <div class="uc-year"></div>
        <div class="uc-text"></div>
      </div>
      <button class="uc-nav uc-next" type="button" aria-label="Next update">&rarr;</button>
    </div>
    <div class="uc-foot">
      <div class="uc-dots" id="ucDots"></div>
      <button class="uc-pause" id="ucPause" type="button" aria-pressed="false">Pause auto-advance</button>
    </div>
  </div>
</div>

<div class="wide" style="padding-top:0">
  <div class="map-window" style="min-height:64vh;border-radius:14px;overflow:hidden">
    <div class="map-legend glass">
      <h4>Map layers</h4>
      <div class="lg-row"><span class="lg-swatch" style="background:#E8834A"></span> Intervention density (heat)</div>
      <div class="lg-row"><span class="lg-swatch" style="background:var(--alarm)"></span> High need</div>
      <div class="lg-row"><span class="lg-swatch" style="background:var(--normal)"></span> Watch</div>
      <div class="lg-note">Ground colour = density of PACIDA interventions (hot = many projects). Circle size = households. Toggle layers (top-right) for drought-need shading. Borena boundary is approximate (dashed). Zoom in for village &amp; site labels.</div>
    </div>
  </div>
</div>

<div class="wide">
  <div class="panel glass" id="pacida-section">
    <h2>PACIDA's operational areas <span class="tag">Marsabit, Samburu, Isiolo &amp; the Borena Zone (S. Ethiopia)</span></h2>
    <p>This dashboard is scoped to where PACIDA actually works. The map above centers on these four areas and shades the
    ground surface by intervention density &mdash; where PACIDA has done the most, and where the gaps still are.</p>
    <div class="cards-grid" id="pacidaCards"></div>
  </div>

  <div class="panel glass">
    <h2>Compare the four areas <span class="tag">click to open its full profile · live</span></h2>
    <div class="table-scroll">
    <table class="ptable" id="allTable">
      <thead><tr>
        <th class="sortable" data-key="name">Area <span class="arrow">▾</span></th>
        <th class="sortable" data-key="need">Need index <span class="arrow">▾</span></th>
        <th class="sortable" data-key="band">Band <span class="arrow">▾</span></th>
        <th class="sortable" data-key="temp">Temp <span class="arrow">▾</span></th>
        <th class="sortable" data-key="rain">Rain 30d <span class="arrow">▾</span></th>
        <th class="sortable" data-key="hh">Households <span class="arrow">▾</span></th>
        <th class="sortable" data-key="pop">Population <span class="arrow">▾</span></th>
        <th class="sortable" data-key="poverty">Poverty <span class="arrow">▾</span></th>
        <th>Drought phase</th>
      </tr></thead>
      <tbody id="allBody"><tr><td colspan="9" class="loading">Fetching live weather for 4 zones…</td></tr></tbody>
    </table>
    </div>
  </div>

  <div class="panel glass">
    <h2>Rating framework — how intervention level is decided</h2>
    <p style="margin-bottom:14px">
      The Intervention Need Index (0–100) is aligned with the frameworks used by the world's main drought and
      food-security institutions: Kenya's <b>NDMA</b> drought early-warning phases (Marsabit, Samburu and Isiolo), the
      <b>IPC</b> (Integrated Food Security Phase Classification) used by <b>FAO, WFP, UNICEF, OCHA and FEWS&nbsp;NET</b>, and
      <b>WHO/UNICEF</b> acute-malnutrition thresholds. Live climate signals are re-scored on every refresh; structural
      indicators come from the latest published NDMA/IPC assessments.
      Unfamiliar term? Open the <b>Glossary</b> in the header.
    </p>
    <h2 style="font-size:15px;margin-top:6px">Index bands mapped to official phases</h2>
    <div class="table-scroll">
    <table class="ptable">
      <thead><tr><th>Dashboard band</th><th>Index</th><th>NDMA drought phase</th><th>IPC phase (FAO/WFP/FEWS NET)</th><th>Typical response</th></tr></thead>
      <tbody>
        <tr><td><span class="chip" style="background:var(--normal)"></span>Watch</td><td class="mono">0–44</td><td>Normal</td><td>Phase 1 · Minimal</td><td>Monitoring, preparedness, resilience building</td></tr>
        <tr><td><span class="chip" style="background:var(--alert)"></span>Elevated</td><td class="mono">45–59</td><td>Alert</td><td>Phase 2 · Stressed</td><td>Early action: water trucking standby, livestock offtake planning, cash-transfer scale-up</td></tr>
        <tr><td><span class="chip" style="background:var(--alarm)"></span>High</td><td class="mono">60–74</td><td>Alarm</td><td>Phase 3 · Crisis</td><td>Emergency WASH, supplementary feeding, food/cash assistance, fodder distribution</td></tr>
        <tr><td><span class="chip" style="background:var(--emergency)"></span>Critical</td><td class="mono">75–100</td><td>Emergency</td><td>Phase 4 · Emergency</td><td>Full humanitarian response: relief food, therapeutic nutrition (SAM), emergency water, destocking</td></tr>
      </tbody>
    </table>
    </div>
  </div>

  <div class="panel glass">
    <h2>Key resources</h2>
    <div class="resource-grid">
      <a class="resource-card" href="impact.html"><b>PACIDA Impact Dashboard</b><span>236 real projects, FY2010&ndash;FY2026 &mdash; donors, themes, achievements.</span></a>
      <button class="resource-card" type="button" id="resGlossaryBtn"><b>Glossary of terms</b><span>Plain-language decoder for NDMA, IPC, ASAL and local terms.</span></button>
      <a class="resource-card" href="#about-section"><b>Rating framework &amp; methodology</b><span>How the 0&ndash;100 Need Index is calculated and where the data comes from.</span></a>
      <a class="resource-card" href="https://pacida.org" target="_blank" rel="noopener"><b>PACIDA official site<span class="ext-mark">&#8599;</span></b><span>Programme pages, annual reports and contact information.</span></a>
    </div>
  </div>

  <div class="panel glass" id="about-section">
    <h2>About this project &amp; PACIDA</h2>
    <p>This dashboard is a monitoring tool for <b>PACIDA</b> (Pastoralist Community Initiative and Development Assistance), a
    Northern-Kenya/Southern-Ethiopia NGO working across Marsabit, Samburu and Isiolo counties and the Borena Zone of southern
    Ethiopia — drought emergency response, WASH, livestock health, education access, and cross-border peace &amp; governance.
    Every area shown here is somewhere PACIDA actually operates; nothing on this map is national context or a county PACIDA
    doesn't work in. See the <a href="impact.html" style="color:var(--alert)">Impact Dashboard</a> for what's been delivered
    on the ground, project by project.</p>
    <div class="src-grid">
      <div class="src"><b>Live weather &amp; soil</b><span>Open-Meteo API — temperature, humidity, wind, rainfall (past 30 d + 7-d forecast), soil moisture. Refreshed every 10 minutes. </span><a href="https://open-meteo.com" target="_blank" rel="noopener">open-meteo.com</a></div>
      <div class="src"><b>County boundaries</b><span>geoBoundaries open geodata project (RCMRD / Africa GeoPortal source, 2023 release). </span><a href="https://www.geoboundaries.org" target="_blank" rel="noopener">geoboundaries.org</a></div>
      <div class="src"><b>Households &amp; population</b><span>Kenya 2019 Population &amp; Housing Census (KNBS). Borena Zone figures are CSA-based projections. </span><a href="https://www.knbs.or.ke" target="_blank" rel="noopener">knbs.or.ke</a></div>
      <div class="src"><b>Drought phase</b><span>NDMA national drought early-warning bulletins for Marsabit, Samburu and Isiolo, and FEWS NET East Africa outlooks for southern Ethiopia. </span><a href="https://ndma.go.ke" target="_blank" rel="noopener">ndma.go.ke</a></div>
      <div class="src"><b>PACIDA interventions</b><span>PACIDA's own project register and "@ A Glance" briefing — see the Impact Dashboard for the full picture. </span><a href="https://pacida.org" target="_blank" rel="noopener">pacida.org</a></div>
    </div>
  </div>
</div>
</main>

<footer class="glass">
  <div class="foot-brand"><img class="brand-logo" src="assets/pacida-logo.png" alt="PACIDA"><span>Kenya ASAL Climate Watch · unofficial monitoring prototype, in partnership with PACIDA · census figures are the latest published, weather is live</span></div>
  <div class="mono" id="footTime"></div>
</footer>

</div><!-- /overlay -->

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script src="assets/boundaries.js"></script>
<script src="assets/villages.js"></script>
<script src="assets/interventions.js"></script>
<script src="assets/common.js"></script>
<script>
const REGIONS = %(regions_json)s;
const PACIDA_AREA_SLUGS = ["marsabit","samburu","isiolo","borena"];

startClock();

/* ================= MAP — framed on PACIDA's operational area ================= */
const {map, layersControl} = makeGlassMap(%(center)s, %(zoom)s);
const markerLayer = L.layerGroup().addTo(map);
const labelLayer  = L.layerGroup().addTo(map);
const shadeLayer  = L.layerGroup();
const outlineLayer = L.layerGroup().addTo(map);
const markers = {};

/* county/zone outlines always shown for orientation; fill shading is opt-in via the layers control */
PACIDA_AREA_SLUGS.forEach(slug=>{
  const geom = BOUNDARIES[slug];
  if(!geom) return;
  const approx = slug==="borena";
  L.geoJSON({type:"Feature",geometry:geom},{
    style:{color:"#FFFFFF", weight:approx?1.3:1.6, opacity:.75, dashArray:approx?"6 5":null, fillOpacity:0}
  }).addTo(outlineLayer);
});

function drawShading(){
  shadeLayer.clearLayers();
  REGIONS.forEach(r=>{
    const geom = BOUNDARIES[r.id];
    if(!geom) return;
    const need = r.live ? r.live.need : null;
    const band = need!=null ? needBand(need) : "elevated";
    const color = PHASE_COLORS[band];
    const approx = r.id==="borena";
    const poly = L.geoJSON({type:"Feature",geometry:geom},{
      style:{color:"#FFFFFF", weight:approx?1.2:1, opacity:.6, dashArray:approx?"6 5":null, fillColor:color, fillOpacity:.32}
    });
    poly.bindTooltip(
      `<b>${r.name}</b><br>Intervention level: ${need!=null?bandLabel(band)+" ("+need+"/100)":"loading…"}`+
      `<br>Phase: ${r.droughtPhase}`+(approx?"<br><i>Boundary approximate</i>":""),
      {sticky:true, className:"shade-tip"}
    );
    poly.on("click",()=>{ if(markers[r.id]) markers[r.id].openPopup(); });
    shadeLayer.addLayer(poly);
  });
}
drawShading();

/* intervention-density heat: the "ground surface" colour the dashboard leads with */
const heatLayer = drawInterventionHeat(PACIDA_AREA_SLUGS).addTo(map);
const interventionLayer = L.layerGroup().addTo(map);
PACIDA_AREA_SLUGS.forEach(slug=>{
  drawInterventionLayer(map, slug).eachLayer(l=>interventionLayer.addLayer(l));
  attachVillageLayer(map, slug);
});

layersControl.addOverlay(heatLayer,"Intervention density (heat)");
layersControl.addOverlay(shadeLayer,"Drought-need shading");
layersControl.addOverlay(markerLayer,"Household markers");
layersControl.addOverlay(interventionLayer,"PACIDA interventions &amp; offices");
layersControl.addOverlay(labelLayer,"County labels");

function hhRadius(hh){ return Math.max(5, Math.min(20, Math.sqrt(hh)/22)); }

function drawMarkers(){
  markerLayer.clearLayers(); labelLayer.clearLayers();
  REGIONS.forEach(r=>{
    const need = r.live ? r.live.need : null;
    const band = need!=null ? needBand(need) : "elevated";
    const color = PHASE_COLORS[band];
    const core = L.circleMarker([r.lat,r.lon],{radius:hhRadius(r.households), color:"#FFFFFF", weight:1.3, fillColor:color, fillOpacity:.65});
    const w = r.live;
    core.bindPopup(`
      <h4>${r.name}${r.pacida?' <span class="pacida-tag">PACIDA</span>':''}</h4>
      <div><span class="pop-k">Need index:</span> <span class="pop-v">${need!=null?need+" / 100 · "+bandLabel(band):"loading…"}</span></div>
      <div><span class="pop-k">Households:</span> <span class="pop-v">${fmt(r.households)}</span></div>
      <div><span class="pop-k">Population:</span> <span class="pop-v">${fmt(r.population)}</span></div>
      <div><span class="pop-k">Phase:</span> <span class="pop-v">${r.droughtPhase}</span></div>
      ${w?`
      <div><span class="pop-k">Now:</span> <span class="pop-v">${fmtTemp(w.temp)} · ${w.rh}%% RH · wind ${w.wind.toFixed(0)} km/h</span></div>
      <div><span class="pop-k">Rain, past 30 d:</span> <span class="pop-v">${fmtRain(w.rain30)}</span></div>
      <div><span class="pop-k">Topsoil moisture:</span> <span class="pop-v">${(w.soil*100).toFixed(1)}%%</span></div>`:""}
      <div style="margin-top:6px"><span class="pop-k">Key sites:</span> ${r.sites.slice(0,4).join(", ")}</div>
      <div style="margin-top:6px"><a href="${r.id}.html" style="color:var(--alert)">Open detail page →</a></div>
    `);
    const label = L.marker([r.lat,r.lon],{interactive:false,
      icon:L.divIcon({className:"", html:`<div class="region-label">${r.name.split(" County")[0]}</div>`, iconAnchor:[-hhRadius(r.households)-6, 8]})});
    markerLayer.addLayer(core); labelLayer.addLayer(label);
    markers[r.id]=core;
  });
  toggleLabels();
}
function toggleLabels(){
  const show = map.getZoom() >= 7;
  if(show && !map.hasLayer(labelLayer)) map.addLayer(labelLayer);
  if(!show && map.hasLayer(labelLayer)) map.removeLayer(labelLayer);
}
map.on("zoomend", toggleLabels);
drawMarkers();

/* ================= PACIDA CARDS ================= */
function renderPacidaCards(){
  const el = document.getElementById("pacidaCards");
  const order = REGIONS.filter(r=>r.pacida).sort((a,b)=>((b.live?b.live.need:-1)-(a.live?a.live.need:-1)));
  el.innerHTML = order.map(r=>{
    const w=r.live, need=w?w.need:null;
    const band = need!=null?needBand(need):"elevated";
    const color = PHASE_COLORS[band];
    return `<div class="card glass clickable" tabindex="0" role="button" aria-label="Zoom map to ${r.name}" data-id="${r.id}">
      <div class="card-top">
        <div><h3>${r.name}</h3><div class="zone">${r.zone}</div></div>
        <span class="badge" style="background:${color}">${need!=null?bandLabel(band)+" · "+need:"…"}</span>
      </div>
      <div class="gauge"><div class="gauge-track"><div class="gauge-marker" style="left:${need!=null?need:0}%%"></div></div>
      <div class="gauge-labels"><span>Watch</span><span>Elevated</span><span>High</span><span>Critical</span></div></div>
      ${w?`<div class="metrics">
        <div class="m"><div class="mk">Now</div><div class="mv">${fmtTemp(w.temp)}</div></div>
        <div class="m"><div class="mk">Rain 30 d</div><div class="mv">${fmtRain(w.rain30)}</div></div>
        <div class="m"><div class="mk">Soil 0–7 cm</div><div class="mv">${(w.soil*100).toFixed(1)}<small>%%</small></div></div>
        <div class="m"><div class="mk">7-d max avg</div><div class="mv">${fmtTemp(w.tmax7)}</div></div>
      </div>`:`<div class="loading">Fetching live weather…</div>`}
      <div class="hh-line">
        <span>Households <b>${fmt(r.households)}</b></span><span>Population <b>${fmt(r.population)}</b></span><span>Poverty <b>${r.povertyRate}%%</b></span>
      </div>
      <div class="hh-line" style="border:0;padding-top:4px;margin-top:0"><span>Phase: <b style="font-family:'Archivo'">${r.droughtPhase}</b></span></div>
      <a class="detail-link" href="${r.id}.html">Open ${r.name.split(" County")[0]} detail page →</a>
    </div>`;
  }).join("");
  el.querySelectorAll(".card").forEach(card=>{
    card.addEventListener("click",e=>{
      if(e.target.closest("a")) return;
      const r = REGIONS.find(x=>x.id===card.dataset.id);
      map.flyTo([r.lat,r.lon],8,{duration:1}); if(markers[r.id]) markers[r.id].openPopup();
    });
    card.addEventListener("keydown",e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();card.click();} });
  });
}

/* ================= AREA COMPARISON TABLE ================= */
let sortKey="need", sortDir=-1;
function renderTable(){
  const tbody = document.getElementById("allBody");
  let rows = REGIONS.map(r=>({
    id:r.id, name:r.name,
    need: r.live? r.live.need : -1,
    band: r.live? bandLabel(needBand(r.live.need)) : "…",
    temp: r.live? r.live.temp : null, rain: r.live? r.live.rain30 : null,
    hh:r.households, pop:r.population, poverty:r.povertyRate, phase:r.droughtPhase, pacida:r.pacida
  }));
  rows.sort((a,b)=>{
    const av=a[sortKey], bv=b[sortKey];
    if(typeof av === "string") return sortDir*av.localeCompare(bv);
    return sortDir*((av??-1)-(bv??-1));
  });
  tbody.innerHTML = rows.map(r=>`<tr class="row-link" data-id="${r.id}">
    <td><a class="row-name-link" href="${r.id}.html"><b>${r.name}</b></a>${r.pacida?'<span class="pacida-tag">PACIDA</span>':''}</td>
    <td class="mono">${r.need>=0?r.need:"…"}</td>
    <td>${r.band}</td>
    <td class="mono">${r.temp!=null?fmtTemp(r.temp):"…"}</td>
    <td class="mono">${r.rain!=null?fmtRain(r.rain):"…"}</td>
    <td class="mono">${fmt(r.hh)}</td>
    <td class="mono">${fmt(r.pop)}</td>
    <td class="mono">${r.poverty}%%</td>
    <td>${r.phase}</td>
  </tr>`).join("");
  tbody.querySelectorAll("tr.row-link").forEach(tr=>{
    tr.addEventListener("click", e=>{ if(e.target.closest("a")) return; window.location.href = tr.dataset.id + ".html"; });
  });
  document.querySelectorAll("#allTable th.sortable").forEach(th=>{
    const active = th.dataset.key===sortKey;
    th.classList.toggle("active", active);
    th.querySelector(".arrow").textContent = active ? (sortDir===1?"▴":"▾") : "▾";
    th.setAttribute("aria-sort", active ? (sortDir===1?"ascending":"descending") : "none");
  });
}
wireSortableHeaders("#allTable th.sortable", th=>{
  const key = th.dataset.key;
  if(sortKey===key) sortDir*=-1; else { sortKey=key; sortDir=-1; }
  renderTable();
});

/* ================= UNITS, GLOSSARY, SEARCH, EXPORT ================= */
document.addEventListener("units-changed", ()=>{ renderPacidaCards(); drawMarkers(); renderTable(); });
attachUnitToggle();
attachGlossary();
attachSearch(
  ()=>REGIONS.map(r=>({id:r.id, label:r.name+" — "+r.zone})),
  m=>{
    const r = REGIONS.find(x=>x.id===m.id);
    if(!r) return;
    map.flyTo([r.lat,r.lon],8,{duration:1});
    if(markers[r.id]) markers[r.id].openPopup();
  }
);
document.getElementById("exportBtn").addEventListener("click", ()=>{
  const rows = [["County","ASAL","Need index","Band","Temp C","RH %%","Rain 30d mm","Soil 0-7cm %%","7d max avg C","Households","Population","Poverty %%","Phase"]];
  REGIONS.forEach(r=>{
    const w = r.live;
    rows.push([r.name, r.asal?"yes":"no", w?w.need:"", w?bandLabel(needBand(w.need)):"",
      w?w.temp.toFixed(1):"", w?w.rh:"", w?w.rain30.toFixed(1):"", w?(w.soil*100).toFixed(1):"", w?w.tmax7.toFixed(1):"",
      r.households, r.population, r.povertyRate, r.droughtPhase]);
  });
  downloadCSV("kenya-climate-watch-live-readings.csv", rows);
});
document.getElementById("resGlossaryBtn").addEventListener("click", ()=>document.getElementById("glossaryBtn").click());

/* ================= LATEST UPDATES CAROUSEL ================= */
(function(){
  const UPDATES = %(updates_json)s; /* [year, text, isNow] */
  const slide = document.getElementById("ucSlide");
  const dotsWrap = document.getElementById("ucDots");
  const carousel = document.getElementById("updatesCarousel");
  const pauseBtn = document.getElementById("ucPause");
  let idx = UPDATES.findIndex(u=>u[2]); if(idx<0) idx = UPDATES.length-1;
  let timer = null;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function render(){
    const [yr, tx, isNow] = UPDATES[idx];
    slide.querySelector(".uc-year").innerHTML = yr + (isNow ? ' <span class="now-badge">Now</span>' : "");
    slide.querySelector(".uc-text").innerHTML = tx;
    dotsWrap.querySelectorAll(".uc-dot").forEach((d,i)=>{
      d.classList.toggle("active", i===idx);
      d.setAttribute("aria-current", i===idx ? "true" : "false");
    });
  }
  dotsWrap.innerHTML = UPDATES.map((_,i)=>`<button class="uc-dot" type="button" aria-label="Update ${i+1} of ${UPDATES.length}"></button>`).join("");
  dotsWrap.querySelectorAll(".uc-dot").forEach((d,i)=>d.addEventListener("click",()=>{ idx=i; render(); restart(); }));
  document.querySelector(".uc-prev").addEventListener("click", ()=>{ idx=(idx-1+UPDATES.length)%%UPDATES.length; render(); restart(); });
  document.querySelector(".uc-next").addEventListener("click", ()=>{ idx=(idx+1)%%UPDATES.length; render(); restart(); });
  carousel.addEventListener("keydown", e=>{
    if(e.key==="ArrowLeft"){ idx=(idx-1+UPDATES.length)%%UPDATES.length; render(); restart(); }
    else if(e.key==="ArrowRight"){ idx=(idx+1)%%UPDATES.length; render(); restart(); }
  });
  function start(){ if(reduceMotion || paused) return; timer = setInterval(()=>{ idx=(idx+1)%%UPDATES.length; render(); }, 7000); }
  function stop(){ clearInterval(timer); }
  function restart(){ stop(); start(); }
  let paused = reduceMotion;
  if(reduceMotion){ pauseBtn.textContent = "Auto-advance off"; pauseBtn.setAttribute("aria-pressed","true"); }
  pauseBtn.addEventListener("click", ()=>{
    paused = !paused;
    pauseBtn.textContent = paused ? "Resume auto-advance" : "Pause auto-advance";
    pauseBtn.setAttribute("aria-pressed", paused ? "true" : "false");
    if(paused) stop(); else start();
  });
  carousel.addEventListener("mouseenter", stop);
  carousel.addEventListener("mouseleave", ()=>{ if(!paused) start(); });
  render();
  start();
})();

/* ================= LIVE WEATHER ================= */
async function fetchRegion(r){
  const w = await fetchPoint(r.lat, r.lon);
  w.need = computeNeed(r.staticVuln, w);
  r.live = w;
}

async function refreshAll(){
  const dotEl=document.getElementById("liveDot"), st=document.getElementById("liveState");
  st.textContent="Updating…";
  try{
    await Promise.all(REGIONS.map(r=>fetchRegion(r).catch(e=>{console.error(r.id,e); r.error=String(e);})));
    const ok = REGIONS.filter(r=>r.live);
    if(!ok.length) throw new Error("No data returned");
    const kenyaOnly = REGIONS.filter(r=>r.country==="Kenya");
    document.getElementById("totHH").textContent = fmt(kenyaOnly.reduce((a,r)=>a+r.households,0));
    document.getElementById("totPop").textContent = fmt(kenyaOnly.reduce((a,r)=>a+r.population,0));
    const asalZones = REGIONS.filter(r=>r.asal);
    document.getElementById("zonesAlert").textContent = asalZones.filter(r=>/alert|alarm|crisis|emergency/i.test(r.droughtPhase)).length + " / " + asalZones.length;
    const avg = Math.round(ok.reduce((a,r)=>a+r.live.need,0)/ok.length);
    document.getElementById("avgNeed").textContent = avg;
    document.getElementById("lastRef").textContent = new Date().toLocaleTimeString("en-GB",{timeZone:"Africa/Nairobi",hour12:false})+" EAT";
    st.textContent="Live · Open-Meteo feed";
    dotEl.style.background="var(--normal)";
    renderPacidaCards(); drawMarkers(); drawShading(); renderTable();
  }catch(e){
    console.error(e);
    st.textContent="Feed unavailable — check connection";
    dotEl.style.background="var(--emergency)";
  }
}

document.getElementById("refreshBtn").addEventListener("click",refreshAll);
refreshAll();
setInterval(refreshAll, 10*60*1000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    for rid, r in COUNTIES.items():
        out = page(rid, r)
        open(os.path.join(SITE, rid + ".html"), "w", encoding="utf-8").write(out)
        print(rid + ".html", len(out), "bytes")
    build_index()
