#!/usr/bin/env python3
"""Generates impact.html — PACIDA's visual impact dashboard — from assets/interventions.json."""
import json, os
from collections import Counter, defaultdict

SITE = os.path.dirname(os.path.abspath(__file__))
INTERVENTIONS = json.load(open(os.path.join(SITE, "assets", "interventions.json"), encoding="utf-8"))

projects = INTERVENTIONS["projects"]
donors = sorted({p["donor"] for p in projects if p["donor"]})
ongoing_now = [p for p in projects if p["status"] == "ongoing"]
mapped = [p for p in projects if p["locations"]]

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
    (str(len(donors)), "Donor &amp; implementing partners"),
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%%3E%%3Ctext y='.9em' font-size='90'%%3E%%F0%%9F%%87%%B0%%F0%%9F%%87%%AA%%3C/text%%3E%%3C/svg%%3E">
</head>
<body>

<div class="overlay">

<header class="glass">
  <div class="brand">
    <h1><a href="index.html">Kenya <span>&middot;</span> ASAL Climate Watch</a></h1>
    <div class="sub">PACIDA Impact Dashboard &middot; real project data, FY2010&ndash;FY2026</div>
  </div>
  <nav class="site">
    <a href="index.html">&larr; All ASAL counties</a>
    <a href="marsabit.html">Marsabit</a>
    <a href="samburu.html">Samburu</a>
    <a href="isiolo.html">Isiolo</a>
    <a href="borena.html">Borena</a>
  </nav>
  <div class="head-right">
    <div class="search-wrap">
      <input type="text" id="searchBox" placeholder="Jump to a county&hellip;" aria-label="Search counties">
      <div class="search-results" id="searchResults"></div>
    </div>
    <button class="iconbtn" id="glossaryBtn" type="button" title="Open glossary of terms">Glossary</button>
    <button class="iconbtn" id="exportBtn" type="button" title="Download the full project list as CSV">Export CSV</button>
  </div>
</header>

<div class="gl-panel" id="glossaryPanel" aria-label="Glossary of terms">
  <div class="gl-head"><h3>Glossary</h3><button class="gl-close" type="button" aria-label="Close glossary">&times;</button></div>
  <input class="gl-search" type="text" placeholder="Filter terms&hellip;" aria-label="Filter glossary terms">
  <div class="gl-body"></div>
</div>
<div class="gl-backdrop" id="glBackdrop"></div>

<div class="wide" style="padding-top:22px">
  <div class="panel glass">
    <h2>PACIDA, at a glance</h2>
    <p>Sixteen years of continuous humanitarian and development work across Marsabit, Samburu, Isiolo and the
    cross-border Borena Zone of southern Ethiopia &mdash; drawn directly from PACIDA's own project register and its
    externally-shared "@ A Glance" briefing, not modelled or estimated.</p>
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
    <p class="hist-cap">%(mapped_count)s of %(total_count)s projects name a specific site in their title and are pinned here;
    the rest are regional or multi-county programmes (shown in the table below, not on the map, rather than guessing a location).</p>
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
        <th class="sortable" data-key="donor">Donor <span class="arrow">&#9662;</span></th>
        <th class="sortable" data-key="status">Status <span class="arrow">&#9662;</span></th>
      </tr></thead>
      <tbody id="projBody"></tbody>
    </table>
    </div>
  </div>

  <div class="panel glass">
    <h2>Sources &amp; methodology</h2>
    <div class="src-grid">
      <div class="src"><b>Project register</b><span>PACIDA's internal Project Summary (FY2010&ndash;FY2026): donor, thematic area, title, duration and dates for every grant. Individual grant amounts are intentionally not published here &mdash; they read as internal financial detail rather than material PACIDA already shares externally.</span></div>
      <div class="src"><b>Achievement figures</b><span>PACIDA's own "@ A Glance 2023-2026" partner briefing &mdash; the same headline numbers shared with donors and partners.</span></div>
      <div class="src"><b>Challenges &amp; gaps</b><span>PACIDA's own stated challenges and mitigation measures, from the same briefing &mdash; not this dashboard's assessment.</span></div>
      <div class="src"><b>Map locations</b><span>Only projects whose title names a specific settlement or ward are pinned, using this site's existing settlement coordinates. Regional/multi-county programmes are listed in the table but not placed on the map.</span></div>
    </div>
  </div>
</div>

<footer class="glass">
  <div>Kenya ASAL Climate Watch &middot; PACIDA Impact Dashboard &middot; built from PACIDA's own project data &mdash; not an audited financial report</div>
  <div class="mono" id="footTime"></div>
</footer>

</div><!-- /overlay -->

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
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
const {map} = makeGlassMap([2.3, 38.2], 7, "impactMap");
setTimeout(()=>map.invalidateSize(), 300);
PACIDA_SLUGS.forEach(slug=>{
  const geom = BOUNDARIES[slug];
  if(!geom) return;
  L.geoJSON({type:"Feature",geometry:geom},{
    style:{color:"#FFFFFF",weight:1.4,opacity:.6,fillColor:"#8FBB5F",fillOpacity:.05,
           dashArray:slug==="borena"?"6 5":null}
  }).addTo(map);
});
let currentTheme = "all";
let markerLayer = L.layerGroup().addTo(map);
function drawImpactMarkers(){
  markerLayer.clearLayers();
  PACIDA_SLUGS.forEach(slug=>{
    projectsForSlug(slug).forEach(p=>{
      if(currentTheme!=="all" && p.theme!==currentTheme) return;
      const loc = p.locations.find(l=>l.slug===slug);
      if(!loc) return;
      const m = L.circleMarker([loc.lat, loc.lon], {radius:6,color:"#fff",weight:1,fillColor:p.theme_color,fillOpacity:.88});
      m.bindPopup(`<h4>${p.title}</h4>`
        +`<div><span class="pop-k">Theme:</span> <span class="pop-v">${p.theme}</span></div>`
        +`<div><span class="pop-k">Donor:</span> <span class="pop-v">${p.donor||"—"}</span></div>`
        +`<div><span class="pop-k">Year:</span> <span class="pop-v">${p.year||"—"} &middot; ${p.status==="ongoing"?"Ongoing":"Completed"}</span></div>`
        +`<div style="margin-top:6px"><span class="pop-k">Located at:</span> ${loc.name}</div>`);
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
    <td>${p.donor||"—"}</td>
    <td><span class="${p.status==='ongoing'?'status-ongoing':'status-done'}">${p.status==='ongoing'?'Ongoing':'Completed'}</span></td>
  </tr>`).join("");
  document.querySelectorAll("#projTable th.sortable").forEach(th=>{
    th.classList.toggle("active", th.dataset.key===sortKey);
    th.querySelector(".arrow").textContent = th.dataset.key===sortKey ? (sortDir===1?"▴":"▾") : "▾";
  });
}
document.querySelectorAll("#projTable th.sortable").forEach(th=>{
  th.addEventListener("click",()=>{
    const key = th.dataset.key;
    if(sortKey===key) sortDir*=-1; else { sortKey=key; sortDir=-1; }
    renderProjTable();
  });
});
renderProjTable();

/* glossary, search, export */
attachGlossary();
attachSearch(
  ()=>COUNTY_INDEX.map(c=>({id:c.slug, label:c.name, kind:"county"})),
  m=>{ window.location.href = m.id + ".html"; }
);
document.getElementById("exportBtn").addEventListener("click", ()=>{
  const rows = [["Year","Theme","Project","Donor","Duration","Start","End","Status"]];
  INTERVENTIONS.projects.forEach(p=>{
    rows.push([p.year, p.theme, p.title, p.donor, p.duration, p.start, p.end, p.status]);
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
    donut_json=json.dumps(donut_data, separators=(",", ":")),
    year_json=json.dumps(year_data, separators=(",", ":")),
    theme_chips=theme_chip_html,
)
open(os.path.join(SITE, "impact.html"), "w", encoding="utf-8").write(out)
print("impact.html", len(out), "bytes")
