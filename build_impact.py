#!/usr/bin/env python3
"""Generates impact.html — PACIDA's visual impact dashboard — from assets/interventions.json."""
import json, os
from collections import Counter, defaultdict

SITE = os.path.dirname(os.path.abspath(__file__))
INTERVENTIONS = json.load(open(os.path.join(SITE, "assets", "interventions.json"), encoding="utf-8"))
BOUNDARIES = json.load(open(os.path.join(SITE, "assets", "boundaries.json"), encoding="utf-8"))
PACIDA_SLUGS_LIST = ["marsabit", "samburu", "isiolo", "borena"]


def raw_bounds(geoms, pad=0.28):
    """[[south,west],[north,east]] padded bounds for Leaflet's maxBounds — mirrors
    build_pages.py's helper so this map is locked to the same intervention area."""
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
    lon_pad = (max(lons) - min(lons)) * pad or 0.5
    lat_pad = (max(lats) - min(lats)) * pad or 0.5
    return [[round(min(lats) - lat_pad, 3), round(min(lons) - lon_pad, 3)],
            [round(max(lats) + lat_pad, 3), round(max(lons) + lon_pad, 3)]]


IMPACT_BOUNDS = raw_bounds([BOUNDARIES[s] for s in PACIDA_SLUGS_LIST if s in BOUNDARIES])

COUNTY_NAV_LINKS = [("marsabit", "Marsabit"), ("samburu", "Samburu"), ("isiolo", "Isiolo"), ("borena", "Borena Zone")]


def site_nav(active):
    """Shared, site-wide header nav — identical to build_pages.py's site_nav().
    Duplicated rather than imported (see that copy's docstring for why)."""
    def a(href, id_, label):
        return '<a href="%s"%s>%s</a>' % (href, ' class="active"' if active == id_ else '', label)
    in_dropdown = active in dict(COUNTY_NAV_LINKS)
    dd_items = "".join(
        '<a href="%s.html"%s>%s</a>' % (slug, ' class="active"' if active == slug else '', label)
        for slug, label in COUNTY_NAV_LINKS)
    return (
        a("index.html", "home", "Home")
        + a("areas.html", "areas", "Operational Areas")
        + a("impact.html", "impact", "Impact Dashboard")
        + '<div class="nav-dd">'
        + '<button type="button" class="nav-dd-btn%s" aria-haspopup="true" aria-expanded="false">Counties <span class="caret">&#9662;</span></button>' % (' active' if in_dropdown else '')
        + '<div class="nav-dd-menu">%s</div>' % dd_items
        + '</div>'
        + a("about.html", "about", "About")
    )

projects = INTERVENTIONS["projects"]
ongoing_now = [p for p in projects if p["status"] == "ongoing"]
mapped = [p for p in projects if p["locations"]]
precisely_sited = [p for p in projects if p["locations"] and p["locations"][0].get("kind") != "regional"]

theme_counts = Counter(p["theme"] for p in projects)
theme_color = {t["label"]: t["color"] for t in INTERVENTIONS["themes"]}
donut_data = [dict(label=t, value=c, color=theme_color[t]) for t, c in theme_counts.most_common()]

by_year = defaultdict(lambda: {"completed": 0, "ongoing": 0})
for p in projects:
    y = p["year"]
    if not y:
        continue
    by_year[int(y)]["completed" if p["status"] == "completed" else "ongoing"] += 1
years_sorted = sorted(by_year.keys())
year_data = [dict(year=y, completed=by_year[y]["completed"], ongoing=by_year[y]["ongoing"]) for y in years_sorted]

hero_stats = [
    (str(INTERVENTIONS["total_projects"]), "Real projects, FY2010\u2013FY2026"),
    (str(INTERVENTIONS["years_active"]), "Years of continuous operation"),
    (str(len(ongoing_now)), "Projects active right now"),
    (str(len(INTERVENTIONS["partners"])), "Donor &amp; implementing partners"),
]

achievements_html = "".join(
    '<div class="ach-row"><div class="an">%s</div><div class="al">%s</div></div>' % (a["n"], a["label"])
    for a in INTERVENTIONS["achievements"]
)
challenges_html = "".join(
    '<div class="chal-row"><div class="cc">%s</div><div class="cm">&rarr; %s</div></div>' % (c["challenge"], c["mitigation"])
    for c in INTERVENTIONS["challenges"]
)
hero_stats_html = "".join(
    '<div class="hs"><div class="hn">%s</div><div class="hl">%s</div></div>' % (n, l) for n, l in hero_stats
)
partner_pills_html = "".join('<span class="partner-pill">%s</span>' % p for p in INTERVENTIONS["partners"])
legend_html = "".join(
    '<div class="legend-item"><span class="legend-sw" style="background:%s"></span>%s (%d)</div>' % (t["color"], t["label"], theme_counts.get(t["label"], 0))
    for t in INTERVENTIONS["themes"]
)
theme_chip_html = '<button class="chip-filter active" data-theme="all">All themes</button>' + "".join(
    '<button class="chip-filter" data-theme="%s" style="border-color:%s">%s</button>' % (t["label"], t["color"], t["label"])
    for t in INTERVENTIONS["themes"]
)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PACIDA Impact Dashboard — Kenya ASAL Climate Watch</title>
<meta name="description" content="236 real PACIDA projects, FY2010–FY2026, across Marsabit, Samburu, Isiolo and the Borena Zone — drawn directly from PACIDA's own project register, not modelled or estimated.">
<meta name="theme-color" content="#34B44B">
<meta property="og:type" content="website">
<meta property="og:title" content="PACIDA Impact Dashboard — Kenya ASAL Climate Watch">
<meta property="og:description" content="236 real PACIDA projects, FY2010–FY2026, across Marsabit, Samburu, Isiolo and the Borena Zone — drawn directly from PACIDA's own project register, not modelled or estimated.">
<meta property="og:url" content="%(base_url)simpact.html">
<meta property="og:image" content="%(base_url)sassets/favicon-512.png">
<meta property="og:site_name" content="Kenya ASAL Climate Watch">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="PACIDA Impact Dashboard">
<meta name="twitter:description" content="236 real PACIDA projects, FY2010–FY2026, across Marsabit, Samburu, Isiolo and the Borena Zone.">
<meta name="twitter:image" content="%(base_url)sassets/favicon-512.png">
<link rel="canonical" href="%(base_url)simpact.html">
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

<div class="content-pane">
<div id="mapBg" class="content-bg-map" aria-hidden="true"></div>
<div class="content-inner">

<header class="glass">
  <div class="brand">
    <a href="index.html"><img class="brand-logo" src="assets/pacida-logo.png" alt="PACIDA"></a>
    <h1><a href="index.html">Kenya <span>&middot;</span> ASAL Climate Watch</a></h1>
    <div class="sub">PACIDA Impact Dashboard &middot; real project data, FY2010&ndash;FY2026</div>
  </div>
  <button class="navToggle" id="navToggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="navCollapse">&#9776;</button>
  <div class="nav-collapse" id="navCollapse">
    <nav class="site">%(nav)s</nav>
    <div class="head-right">
      <div class="search-wrap">
        <input type="text" id="searchBox" placeholder="Jump to a county&hellip;" aria-label="Search counties">
        <div class="search-results" id="searchResults"></div>
      </div>
      <button class="iconbtn" id="glossaryBtn" type="button" title="Open glossary of terms">Glossary</button>
      <button class="iconbtn" id="exportBtn" type="button" title="Download the full project list as CSV">Export CSV</button>
    </div>
  </div>
  <button class="kioskBtn" id="kioskBtn" type="button" title="Presentation mode — fullscreen, decluttered">&#9974;</button>
</header>

<div class="gl-panel" id="glossaryPanel" aria-label="Glossary of terms">
  <div class="gl-head"><h3>Glossary</h3><button class="gl-close" type="button" aria-label="Close glossary">&times;</button></div>
  <input class="gl-search" type="text" placeholder="Filter terms&hellip;" aria-label="Filter glossary terms">
  <div class="gl-body"></div>
</div>
<div class="gl-backdrop" id="glBackdrop"></div>

<main id="main-content">
<div class="wide" style="padding-top:22px">
  <div class="panel glass">
    <div class="hero-logo-row">
      <img class="hero-logo" src="assets/pacida-logo.png" alt="PACIDA — Pastoralist Community Initiative and Development Assistance">
      <div>
        <h2 style="margin-bottom:6px">PACIDA, at a glance</h2>
        <p style="margin-bottom:0">Sixteen years of continuous humanitarian and development work across Marsabit, Samburu, Isiolo and the
        cross-border Borena Zone of southern Ethiopia &mdash; drawn directly from PACIDA's own project register and its
        externally-shared partner briefing, not modelled or estimated.</p>
      </div>
    </div>
    <div class="hero-stats">%(hero_stats)s</div>
  </div>

  <div class="panel glass">
    <h2>Achievements <span class="tag">selected headline results, 2023&ndash;2026</span></h2>
    <div class="stat-grid" id="achGrid"></div>
  </div>

  <div class="panel glass">
    <h2>Interventions by thematic area</h2>
    <div class="chart-row">
      <div id="donutHolder"></div>
      <div>
        <div id="yearChartHolder"></div>
        <div class="hist-cap">Projects started per year, FY2010&ndash;FY2026 &middot; amber = still ongoing, blue = completed.</div>
      </div>
    </div>
    <div class="legend-row" id="themeLegend"></div>
  </div>

  <div class="panel glass">
    <h2>Where the work is happening <span class="tag">click a theme to filter &middot; star = PACIDA office</span></h2>
    <div class="chip-row" id="themeChips"></div>
    <div class="map-window" style="min-height:56vh;border-radius:10px;overflow:hidden;position:relative">
      <div id="impactMap" style="position:absolute;inset:0"></div>
    </div>
    <p class="hist-cap">All %(total_count)s projects are shown &mdash; %(precise_count)s name a specific site in their title and
    are pinned exactly there (solid dots); the remaining %(regional_count)s are regional or multi-county programmes with no
    named site, shown as dashed hollow dots at an approximate point within the operational area rather than guessing a
    precise location.</p>
  </div>

  <div class="panel glass">
    <h2>Done, and what's still needed</h2>
    <div class="split">
      <div class="split done">
        <h3>&#10003; What PACIDA has delivered</h3>
        %(achievements_list)s
      </div>
      <div class="split needs">
        <h3>&#9888; What still needs more</h3>
        %(challenges_list)s
      </div>
    </div>
  </div>

  <div class="panel glass">
    <h2>Full project register <span class="tag">%(total_count)s projects &middot; click a column to sort</span></h2>
    <div class="table-scroll">
    <table class="ptable" id="projTable">
      <thead><tr>
        <th class="sortable" data-key="year">Year <span class="arrow">&#9662;</span></th>
        <th class="sortable" data-key="theme">Theme <span class="arrow">&#9662;</span></th>
        <th>Project</th>
        <th>Location</th>
        <th class="sortable" data-key="donor">Donor <span class="arrow">&#9662;</span></th>
        <th class="sortable" data-key="status">Status <span class="arrow">&#9662;</span></th>
      </tr></thead>
      <tbody id="projBody"></tbody>
    </table>
    </div>
  </div>

  <div class="panel glass">
    <h2>Partners &amp; donors <span class="tag">%(partner_count)s organisations, from PACIDA's own partnership records</span></h2>
    <p style="margin-bottom:12px">The donors and implementing partners PACIDA has worked with, past and present &mdash;
    names only, drawn from PACIDA's internal partnership records. No contract, budget or audit detail is used here.</p>
    <div class="partner-grid">%(partner_pills)s</div>
  </div>

  <div class="panel glass">
    <h2>Sources &amp; methodology</h2>
    <div class="src-grid">
      <div class="src"><b>Project register</b><span>PACIDA's internal Project Summary (FY2010&ndash;FY2026): donor, thematic area, title, duration and dates for every grant. Individual grant amounts are intentionally not published here &mdash; they read as internal financial detail rather than material PACIDA already shares externally.</span></div>
      <div class="src"><b>Achievement figures</b><span>PACIDA's own 2023&ndash;2026 partner briefing &mdash; the same headline numbers shared with donors and partners.</span></div>
      <div class="src"><b>Challenges &amp; gaps</b><span>PACIDA's own stated challenges and mitigation measures, from the same briefing &mdash; not this dashboard's assessment.</span></div>
      <div class="src"><b>Partners &amp; donors</b><span>Organisation names from PACIDA's internal partnership records (current and historical); no financial or contractual detail is used or published.</span></div>
      <div class="src"><b>Reach figures (map pins)</b><span>Where shown, "Reach" numbers on a project's map pin are condensed from PACIDA's own narrative/progress/final reports to that donor &mdash; not the financial register, which has no beneficiary field. Covers %(pop_count)s of %(total_count)s projects; the rest either have no report on file yet or only fragmented activity-level counts with no reliable total, so no figure is shown rather than an estimated one.</span></div>
      <div class="src"><b>Map locations</b><span>Projects whose title names a specific settlement are pinned exactly there. Regional/multi-county programmes (no named site) are shown as an approximate point within the operational area, weighted by each area's scale, rather than omitted from the map.</span></div>
    </div>
  </div>
</div>
</main>

<footer class="glass">
  <div class="foot-brand"><img class="brand-logo" src="assets/pacida-logo.png" alt="PACIDA"><span>Kenya ASAL Climate Watch &middot; PACIDA Impact Dashboard &middot; built from PACIDA's own project data &mdash; not an audited financial report</span></div>
  <div class="mono" id="footTime"></div>
</footer>

</div><!-- /content-inner -->
</div><!-- /content-pane -->

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script src="assets/boundaries.js"></script>
<script src="assets/county_index.js"></script>
<script src="assets/interventions.js"></script>
<script src="assets/common.js"></script>
<script>
const DONUT_DATA = %(donut_json)s;
const YEAR_DATA = %(year_json)s;
const PACIDA_SLUGS = ["marsabit","samburu","isiolo","borena"];

function tickFoot(){
  const now = new Date();
  document.getElementById("footTime").textContent = now.toLocaleString("en-GB",{timeZone:"Africa/Nairobi"}) + " EAT";
}
tickFoot(); setInterval(tickFoot, 1000);
makeBackgroundMap("mapBg", [2.3, 38.2], 7);

/* achievements grid */
document.getElementById("achGrid").innerHTML = INTERVENTIONS.achievements.map(a =>
  `<div class="stat-tile"><div class="sn">${a.n}</div><div class="sl">${a.label}</div></div>`
).join("");

/* charts */
document.getElementById("donutHolder").innerHTML = donutChart(DONUT_DATA, 190);
document.getElementById("yearChartHolder").innerHTML = yearBarChart(YEAR_DATA);
document.getElementById("themeLegend").innerHTML = INTERVENTIONS.themes.map(t =>
  `<div class="legend-item"><span class="legend-sw" style="background:${t.color}"></span>${t.label}</div>`
).join("");

/* map (embedded in the panel below, not the page-wide fixed background) */
const {map} = makeGlassMap([2.3, 38.2], 7, "impactMap", %(impact_bounds_json)s);
setTimeout(()=>map.invalidateSize(), 300);
PACIDA_SLUGS.forEach(slug=>{
  const geom = BOUNDARIES[slug];
  if(!geom) return;
  L.geoJSON({type:"Feature",geometry:geom},{
    style:{color:"#FFFFFF",weight:1.4,opacity:.6,fillColor:"#34B44B",fillOpacity:.05,
           dashArray:slug==="borena"?"6 5":null}
  }).addTo(map);
});
drawInterventionHeat(PACIDA_SLUGS).addTo(map);
let currentTheme = "all";
let markerLayer = L.layerGroup().addTo(map);
function drawImpactMarkers(){
  markerLayer.clearLayers();
  PACIDA_SLUGS.forEach(slug=>{
    projectsForSlug(slug).forEach(p=>{
      if(currentTheme!=="all" && p.theme!==currentTheme) return;
      const loc = p.locations.find(l=>l.slug===slug);
      if(!loc) return;
      const regional = loc.kind === "regional";
      const m = L.circleMarker([loc.lat, loc.lon], regional
        ? {radius:6,color:p.theme_color,weight:1.5,fillColor:p.theme_color,fillOpacity:.25,dashArray:"2,2"}
        : {radius:6,color:"#fff",weight:1,fillColor:p.theme_color,fillOpacity:.88});
      m.bindPopup(`<h4>${p.title}</h4>`
        +`<div><span class="pop-k">Theme:</span> <span class="pop-v">${p.theme}</span></div>`
        +`<div><span class="pop-k">Donor:</span> <span class="pop-v">${p.donor||"—"}</span></div>`
        +`<div><span class="pop-k">Year:</span> <span class="pop-v">${p.year||"—"} &middot; ${p.status==="ongoing"?"Ongoing":"Completed"}</span></div>`
        +(p.population?`<div class="pop-reach"><span class="pop-k">Reach:</span> <span class="pop-v">${p.population}</span></div>`:"")
        +(regional
          ? `<div style="margin-top:6px"><span class="pop-k">Location:</span> Regional / multi-site programme &mdash; approximate point within the operational area</div>`
          : `<div style="margin-top:6px"><span class="pop-k">Located at:</span> ${loc.name}</div>`),
        {maxWidth: 340});
      markerLayer.addLayer(m);
    });
    officesForSlug(slug).forEach(o=>{
      const m = L.marker([o.lat, o.lon], {icon: L.divIcon({className:"", html:'<div class="office-pin">&#9733;</div>', iconAnchor:[9,9]})});
      m.bindPopup(`<h4>${o.name}</h4><div class="pop-k">${o.note}</div>`);
      markerLayer.addLayer(m);
    });
  });
}
drawImpactMarkers();
document.getElementById("themeChips").innerHTML = `%(theme_chips)s`;
document.querySelectorAll("#themeChips .chip-filter").forEach(btn=>{
  btn.addEventListener("click",()=>{
    document.querySelectorAll("#themeChips .chip-filter").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    currentTheme = btn.dataset.theme;
    drawImpactMarkers();
  });
});

/* project table */
const COUNTY_LABELS = {marsabit:"Marsabit", samburu:"Samburu", isiolo:"Isiolo", borena:"Borena Zone"};
function locationLabel(p){
  if(!p.locations || !p.locations.length) return "—";
  return p.locations.map(l=>
    l.kind === "regional" ? `${COUNTY_LABELS[l.slug]||l.slug} (regional)` : l.name
  ).join(", ");
}

let sortKey="year", sortDir=-1;
function renderProjTable(){
  const rows = INTERVENTIONS.projects.slice().sort((a,b)=>{
    const av=a[sortKey]||"", bv=b[sortKey]||"";
    if(typeof av === "string") return sortDir*av.localeCompare(bv);
    return sortDir*((av||0)-(bv||0));
  });
  document.getElementById("projBody").innerHTML = rows.map(p=>`<tr>
    <td class="mono">${p.year||"—"}</td>
    <td><span class="chip" style="background:${p.theme_color}"></span>${p.theme}</td>
    <td>${p.title}</td>
    <td>${locationLabel(p)}</td>
    <td>${p.donor||"—"}</td>
    <td><span class="${p.status==='ongoing'?'status-ongoing':'status-done'}">${p.status==='ongoing'?'Ongoing':'Completed'}</span></td>
  </tr>`).join("");
  document.querySelectorAll("#projTable th.sortable").forEach(th=>{
    const active = th.dataset.key===sortKey;
    th.classList.toggle("active", active);
    th.querySelector(".arrow").textContent = active ? (sortDir===1?"▴":"▾") : "▾";
    th.setAttribute("aria-sort", active ? (sortDir===1?"ascending":"descending") : "none");
  });
}
wireSortableHeaders("#projTable th.sortable", th=>{
  const key = th.dataset.key;
  if(sortKey===key) sortDir*=-1; else { sortKey=key; sortDir=-1; }
  renderProjTable();
});
renderProjTable();

/* glossary, search, export */
attachHeaderHeightVar();
attachNavToggle();
attachNavDropdown();
attachKioskMode();
attachGlossary();
attachSearch(
  ()=>COUNTY_INDEX.map(c=>({id:c.slug, label:c.name, kind:"county"})),
  m=>{ window.location.href = m.id + ".html"; }
);
document.getElementById("exportBtn").addEventListener("click", ()=>{
  const rows = [["Year","Theme","Project","Location","Donor","Duration","Start","End","Status"]];
  INTERVENTIONS.projects.forEach(p=>{
    rows.push([p.year, p.theme, p.title, locationLabel(p), p.donor, p.duration, p.start, p.end, p.status]);
  });
  downloadCSV("pacida-project-register.csv", rows);
});
</script>
</body>
</html>
"""

out = HTML % dict(
    hero_stats=hero_stats_html, achievements_list=achievements_html, challenges_list=challenges_html,
    mapped_count=len(mapped), total_count=len(projects),
    precise_count=len(precisely_sited), regional_count=len(projects) - len(precisely_sited),
    partner_pills=partner_pills_html, partner_count=len(INTERVENTIONS["partners"]),
    pop_count=len([p for p in projects if p.get("population")]),
    donut_json=json.dumps(donut_data, separators=(",", ":")),
    year_json=json.dumps(year_data, separators=(",", ":")),
    theme_chips=theme_chip_html,
    base_url="https://pacidaict-star.github.io/pacida-asal-website/",
    impact_bounds_json=json.dumps(IMPACT_BOUNDS),
    nav=site_nav("impact"),
)
open(os.path.join(SITE, "impact.html"), "w", encoding="utf-8").write(out)
print("impact.html", len(out), "bytes")
