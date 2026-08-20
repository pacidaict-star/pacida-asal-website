#!/usr/bin/env python3
"""Generates areas.html — a focused, map-only view of PACIDA's 4 operational
areas and their live intervention footprint, with no surrounding dashboard
chrome (no stat strip, cards, tables). Standalone script, same pattern as
build_impact.py: loads the JSON data directly rather than importing
build_pages.py (which has top-level file-writing side effects)."""
import json, math, os

SITE = os.path.dirname(os.path.abspath(__file__))
COUNTIES = json.load(open(os.path.join(SITE, "counties.json"), encoding="utf-8"))
BOUNDARIES = json.load(open(os.path.join(SITE, "assets", "boundaries.json"), encoding="utf-8"))
PACIDA_SLUGS = ["marsabit", "samburu", "isiolo", "borena"]


def combined_bbox_center_zoom(geoms, pad=1.15):
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


def raw_bounds(geoms, pad=0.28):
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


geoms = [BOUNDARIES[s] for s in PACIDA_SLUGS if s in BOUNDARIES]
CENTER, ZOOM = combined_bbox_center_zoom(geoms)
BOUNDS = raw_bounds(geoms)

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

areas = []
for slug in PACIDA_SLUGS:
    r = COUNTIES[slug]
    areas.append(dict(
        id=slug, name=r["title"], lat=r["hq"]["lat"], lon=r["hq"]["lon"],
        households=r["households"], population=r["population"],
        staticVuln=r["staticVuln"], phase=r["phase"],
    ))

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Operational Areas Map — PACIDA Climate Watch</title>
<meta name="description" content="A focused map of PACIDA's 4 operational areas — Marsabit, Samburu, Isiolo and the Borena Zone — with live intervention density and every project pinned.">
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

<div class="areas-shell">

<header class="glass header-overlay">
  <div class="brand">
    <a href="index.html"><img class="brand-logo" src="assets/pacida-logo.png" alt="PACIDA"></a>
    <h1><a href="index.html">PACIDA <span>&middot;</span> Climate Watch</a></h1>
    <div class="sub">Operational Areas Map &middot; live intervention footprint</div>
  </div>
  <button class="navToggle" id="navToggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="navCollapse">&#9776;</button>
  <div class="nav-collapse" id="navCollapse">
    <nav class="site">%(nav)s</nav>
    <div class="head-right">
      <div class="search-wrap">
        <input type="text" id="searchBox" placeholder="Jump to a county&hellip;" aria-label="Search counties">
        <div class="search-results" id="searchResults"></div>
      </div>
      <div class="livepill"><span class="dot" id="liveDot"></span><span id="liveState" role="status" aria-live="polite">Live &middot; Open-Meteo</span></div>
      <button class="iconbtn" id="unitToggle" type="button" title="Toggle °C/°F, mm/in">&deg;C &middot; mm</button>
      <button class="iconbtn" id="glossaryBtn" type="button" title="Open glossary of terms">Glossary</button>
      <button class="iconbtn" id="exportBtn" type="button" title="Download current live readings as CSV">Export CSV</button>
    </div>
  </div>
  <button class="kioskBtn" id="kioskBtn" type="button" title="Presentation mode — fullscreen, decluttered, auto-tour">&#9974;</button>
</header>

<div class="gl-panel" id="glossaryPanel" aria-label="Glossary of terms">
  <div class="gl-head"><h3>Glossary</h3><button class="gl-close" type="button" aria-label="Close glossary">&times;</button></div>
  <input class="gl-search" type="text" placeholder="Filter terms&hellip;" aria-label="Filter glossary terms">
  <div class="gl-body"></div>
</div>
<div class="gl-backdrop" id="glBackdrop"></div>

<main id="main-content" class="areas-body">
  <div id="map" role="application" aria-label="Map of PACIDA's 4 operational areas"></div>

  <div class="area-picker glass">
    <h4>Jump to an area</h4>
    <div id="areaButtons"></div>
  </div>

  <div class="map-legend map-overlay">
    <h4>Map layers</h4>
    <div class="lg-row"><span class="lg-swatch" style="background:#E8834A"></span> Intervention density (heat)</div>
    <div class="lg-row"><span class="lg-swatch" style="background:var(--alarm)"></span> High need</div>
    <div class="lg-row"><span class="lg-swatch" style="background:var(--normal)"></span> Watch</div>
    <div class="lg-note">Ground colour = density of PACIDA interventions (hot = many projects). Solid dots are project pins at a specific site; dashed hollow dots are regional programmes shown at an approximate point. Star = PACIDA office. Toggle layers (top-right) for drought-need shading. Map is locked to PACIDA's operational area. Borena boundary is approximate (dashed). Zoom in for village &amp; site labels.</div>
  </div>
</main>

</div><!-- /areas-shell -->

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script src="assets/boundaries.js"></script>
<script src="assets/villages.js"></script>
<script src="assets/interventions.js"></script>
<script src="assets/county_index.js"></script>
<script src="assets/supabase-config.js"></script>
<script src="assets/common.js"></script>
<script>
const AREAS = %(areas_json)s;
const PACIDA_AREA_SLUGS = ["marsabit","samburu","isiolo","borena"];

const {map, layersControl} = makeGlassMap(%(center)s, %(zoom)s, "map", %(bounds_json)s);

const shadeLayer = L.layerGroup();
const markerLayer = L.layerGroup().addTo(map);
const markers = {};

PACIDA_AREA_SLUGS.forEach(slug=>{
  const geom = BOUNDARIES[slug];
  if(!geom) return;
  const approx = slug==="borena";
  L.geoJSON({type:"Feature",geometry:geom},{
    style:{color:"#FFFFFF", weight:approx?1.3:1.6, opacity:.75, dashArray:approx?"6 5":null, fillOpacity:0}
  }).addTo(map);
});

function drawShading(){
  shadeLayer.clearLayers();
  AREAS.forEach(a=>{
    const geom = BOUNDARIES[a.id];
    if(!geom) return;
    const need = a.live ? a.live.need : null;
    const band = need!=null ? needBand(need) : "elevated";
    const color = PHASE_COLORS[band];
    const poly = L.geoJSON({type:"Feature",geometry:geom},{
      style:{color:"#FFFFFF", weight:1, opacity:.4, fillColor:color, fillOpacity:.28}
    });
    poly.bindTooltip(`<b>${a.name}</b><br>Need: ${need!=null?bandLabel(band)+" ("+need+"/100)":"loading…"}<br>Phase: ${a.phase}`, {sticky:true, className:"shade-tip"});
    poly.on("click",()=>{ if(markers[a.id]) markers[a.id].openPopup(); });
    shadeLayer.addLayer(poly);
  });
}
drawShading();

PACIDA_AREA_SLUGS.forEach(slug=> attachVillageLayer(map, slug));

/* waits on the live Supabase fetch (falls back to the static snapshot on failure) before
   drawing, since drawInterventionHeat/drawInterventionLayer read INTERVENTIONS synchronously
   at call time — see loadLiveProjects() in common.js. */
(async()=>{
  await loadLiveProjects();
  const heatLayer = drawInterventionHeat(PACIDA_AREA_SLUGS).addTo(map);
  PACIDA_AREA_SLUGS.forEach(slug=>{
    drawInterventionLayer(map, slug).eachLayer(l=>markerLayer.addLayer(l));
  });
  layersControl.addOverlay(heatLayer, "Intervention density (heat)");
  layersControl.addOverlay(markerLayer, "PACIDA interventions &amp; offices");
})();

layersControl.addOverlay(shadeLayer, "Drought-need shading");

function hqRadius(hh){ return Math.max(8, Math.min(22, Math.sqrt(hh)/20)); }
function drawAreaPins(){
  Object.values(markers).forEach(m=>map.removeLayer(m));
  AREAS.forEach(a=>{
    const need = a.live ? a.live.need : null;
    const band = need!=null ? needBand(need) : "elevated";
    const color = PHASE_COLORS[band];
    const m = L.circleMarker([a.lat,a.lon], {radius:hqRadius(a.households), color:"#FFFFFF", weight:1.5, fillColor:color, fillOpacity:.5});
    m.bindPopup(`<h4>${a.name}</h4>`
      +`<div><span class="pop-k">Need index:</span> <span class="pop-v">${need!=null?need+" / 100 · "+bandLabel(band):"loading…"}</span></div>`
      +`<div><span class="pop-k">Households:</span> <span class="pop-v">${fmt(a.households)}</span></div>`
      +`<div><span class="pop-k">Population:</span> <span class="pop-v">${fmt(a.population)}</span></div>`
      +`<div><span class="pop-k">Phase:</span> <span class="pop-v">${a.phase}</span></div>`
      +`<div style="margin-top:6px"><a href="${a.id}.html" style="color:var(--alert)">Open ${a.name.split(" County")[0]} detail page →</a></div>`);
    m.addTo(map);
    markers[a.id] = m;
  });
}
drawAreaPins();

document.getElementById("areaButtons").innerHTML = AREAS.map(a=>
  `<button type="button" class="area-btn" data-id="${a.id}">${a.name.replace(" County","").replace(" Zone"," Zone")}</button>`
).join("");
document.querySelectorAll(".area-btn").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    const a = AREAS.find(x=>x.id===btn.dataset.id);
    map.flyTo([a.lat,a.lon], 8, {duration:1});
    if(markers[a.id]) markers[a.id].openPopup();
  });
});

attachHeaderHeightVar();
attachNavToggle();
attachNavDropdown();
let stopKioskTour = null;
attachKioskMode(
  ()=>{
    stopKioskTour = startKioskTour(PACIDA_AREA_SLUGS, {onStop: id=>{
      const a = AREAS.find(x=>x.id===id);
      if(a) map.flyTo([a.lat, a.lon], 8, {duration:1.2});
      if(markers[id]) markers[id].openPopup();
    }});
  },
  ()=>{ if(stopKioskTour) stopKioskTour(); }
);
attachUnitToggle();
attachGlossary();
attachSearch(
  ()=>COUNTY_INDEX.map(c=>({id:c.slug, label:c.name})),
  m=>{ window.location.href = m.id + ".html"; }
);
document.getElementById("exportBtn").addEventListener("click", ()=>{
  const rows = [["Area","Need index","Band","Temp C","RH %%","Rain 30d mm","Soil 0-7cm %%","Households","Population","Phase"]];
  AREAS.forEach(a=>{
    const w = a.live;
    rows.push([a.name, w?w.need:"", w?bandLabel(needBand(w.need)):"",
      w?w.temp.toFixed(1):"", w?w.rh:"", w?w.rain30.toFixed(1):"", w?(w.soil*100).toFixed(1):"",
      a.households, a.population, a.phase]);
  });
  downloadCSV("pacida-operational-areas.csv", rows);
});

async function refreshAll(){
  const dotEl=document.getElementById("liveDot"), st=document.getElementById("liveState");
  st.textContent="Updating…";
  try{
    await Promise.all(AREAS.map(async a=>{
      try{
        const w = await fetchPoint(a.lat, a.lon);
        w.need = computeNeed(a.staticVuln, w);
        a.live = w;
      }catch(e){ console.error(a.id, e); }
    }));
    drawAreaPins(); drawShading();
    st.textContent="Live · Open-Meteo";
    dotEl.style.background="var(--normal)";
  }catch(e){
    console.error(e);
    st.textContent="Feed unavailable — check connection";
    dotEl.style.background="var(--emergency)";
  }
}
refreshAll();
setInterval(refreshAll, 10*60*1000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    out = HTML % dict(
        areas_json=json.dumps(areas, separators=(",", ":")),
        center=json.dumps(CENTER), zoom=ZOOM, bounds_json=json.dumps(BOUNDS),
        nav=site_nav("areas"),
    )
    open(os.path.join(SITE, "areas.html"), "w", encoding="utf-8").write(out)
    print("areas.html", len(out), "bytes")
