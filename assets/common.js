/* Kenya ASAL Climate Watch — shared engine
   Live data: Open-Meteo API (no key). Need index aligned to NDMA / IPC / WHO frameworks. */

const PHASE_COLORS = { critical:"#ED1C24", high:"#E8834A", elevated:"#F0B22E", watch:"#34B44B" };
function needBand(v){ return v>=75?"critical":v>=60?"high":v>=45?"elevated":"watch"; }
function bandLabel(b){ return {critical:"Critical",high:"High",elevated:"Elevated",watch:"Watch"}[b]; }
const fmt = n => n.toLocaleString("en-KE");
function clamp(v,a,b){ return Math.min(b,Math.max(a,v)); }

/* Need index: 45% structural vulnerability + 55% live climate (rain deficit 50%, soil 25%, heat 25%) */
function computeNeed(staticVuln, w){
  const rainDeficit = clamp(1 - (w.rain30/60), 0, 1) * 100;
  const soilDry     = clamp((0.20 - w.soil)/0.20, 0, 1) * 100;
  const heat        = clamp((w.tmax7 - 30)/10, 0, 1) * 100;
  const climate = 0.5*rainDeficit + 0.25*soilDry + 0.25*heat;
  return Math.round(0.45*staticVuln + 0.55*climate);
}

/* Fetch live weather for one point. Returns weather object. */
async function fetchPoint(lat, lon){
  const url = "https://api.open-meteo.com/v1/forecast"
    + "?latitude="+lat+"&longitude="+lon
    + "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
    + "&hourly=soil_moisture_0_to_7cm"
    + "&daily=precipitation_sum,temperature_2m_max"
    + "&past_days=30&forecast_days=7&timezone=Africa%2FNairobi";
  const res = await fetch(url);
  if(!res.ok) throw new Error("Open-Meteo "+res.status);
  const d = await res.json();
  const daily = d.daily.precipitation_sum.map(v=>v==null?0:v);
  const todayIdx = 30;
  const rain30 = daily.slice(0, todayIdx).reduce((a,b)=>a+b,0);
  const tmaxFuture = d.daily.temperature_2m_max.slice(todayIdx).filter(v=>v!=null);
  const tmax7 = tmaxFuture.length ? tmaxFuture.reduce((a,b)=>a+b,0)/tmaxFuture.length : 33;
  const soilArr = (d.hourly && d.hourly.soil_moisture_0_to_7cm) ? d.hourly.soil_moisture_0_to_7cm.filter(v=>v!=null) : [];
  const soil = soilArr.length ? soilArr[soilArr.length-1] : 0.08;
  const startIdx = Math.max(0, todayIdx-14);
  return {
    temp:d.current.temperature_2m, rh:d.current.relative_humidity_2m,
    wind:d.current.wind_speed_10m, rain30, tmax7, soil,
    dailyRain: daily.slice(startIdx), splitIdx: todayIdx-startIdx
  };
}

function sparkline(vals, splitIdx){
  if(!vals||!vals.length) return "";
  const W=320,H=46,max=Math.max(4,...vals);
  const bw=W/vals.length; let bars="";
  vals.forEach((v,i)=>{
    const h=Math.max(1,(v/max)*(H-6));
    const isFc=i>=splitIdx;
    bars+='<rect x="'+(i*bw+1).toFixed(1)+'" y="'+(H-h).toFixed(1)+'" width="'+(bw-2).toFixed(1)+'" height="'+h.toFixed(1)+'" rx="1.5" fill="'+(isFc?'#6FA3B4':'#F0B22E')+'" opacity="'+(isFc?0.9:0.95)+'"/>';
  });
  const sx=(splitIdx*bw).toFixed(1);
  return '<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" aria-hidden="true">'+bars
    +'<line x1="'+sx+'" y1="0" x2="'+sx+'" y2="'+H+'" stroke="#D8BD98" stroke-width="1" stroke-dasharray="3 3"/></svg>';
}

/* Clock (East Africa Time) */
function startClock(){
  const el=document.getElementById("clock"), ft=document.getElementById("footTime");
  function tick(){
    const now=new Date();
    if(el) el.textContent = now.toLocaleTimeString("en-GB",{timeZone:"Africa/Nairobi",hour12:false})+" EAT";
    if(ft) ft.textContent = now.toLocaleString("en-GB",{timeZone:"Africa/Nairobi"})+" EAT";
  }
  setInterval(tick,1000); tick();
}

/* ---------- units (metric / imperial), persisted ---------- */
const UNIT_KEY = "pacida_unit_system";
function getUnitSystem(){ return localStorage.getItem(UNIT_KEY) || "metric"; }
function setUnitSystem(v){ localStorage.setItem(UNIT_KEY, v); document.dispatchEvent(new CustomEvent("units-changed")); }
function fmtTemp(c){ return getUnitSystem()==="imperial" ? (c*9/5+32).toFixed(1)+"°F" : c.toFixed(1)+"°C"; }
function fmtRain(mm){ return getUnitSystem()==="imperial" ? (mm/25.4).toFixed(2)+" in" : mm.toFixed(0)+" mm"; }
/* ---------- header height var (drives content padding under a floating
   header — see header.header-overlay in style.css) ---------- */
function attachHeaderHeightVar(){
  const header = document.querySelector("header.glass");
  if(!header) return;
  const set = ()=> document.documentElement.style.setProperty("--header-h", header.offsetHeight + "px");
  set();
  window.addEventListener("resize", set);
  // header height can change once web fonts finish loading (text reflows)
  if(document.fonts && document.fonts.ready) document.fonts.ready.then(set);
}

/* ---------- mobile hamburger menu (collapses nav + header controls into a
   dropdown panel below the compact header row) ---------- */
function attachNavToggle(){
  const btn = document.getElementById("navToggle");
  const panel = document.getElementById("navCollapse");
  if(!btn || !panel) return;
  const close = ()=>{ panel.classList.remove("open"); btn.setAttribute("aria-expanded","false"); };
  const open = ()=>{ panel.classList.add("open"); btn.setAttribute("aria-expanded","true"); };
  btn.addEventListener("click", e=>{
    e.stopPropagation();
    panel.classList.contains("open") ? close() : open();
  });
  panel.addEventListener("click", e=>{ if(e.target.tagName === "A") close(); });
  document.addEventListener("click", e=>{
    if(panel.classList.contains("open") && !panel.contains(e.target) && e.target !== btn) close();
  });
  document.addEventListener("keydown", e=>{ if(e.key === "Escape") close(); });
  window.addEventListener("resize", ()=>{ if(window.innerWidth > 1020) close(); });
}

/* ---------- header "Counties" dropdown (click-toggled, not hover-only, so
   it works the same with mouse, keyboard and touch) ---------- */
function attachNavDropdown(){
  document.querySelectorAll(".nav-dd").forEach(dd=>{
    const btn = dd.querySelector(".nav-dd-btn");
    if(!btn) return;
    const close = ()=>{ dd.classList.remove("open"); btn.setAttribute("aria-expanded","false"); };
    const open = ()=>{ dd.classList.add("open"); btn.setAttribute("aria-expanded","true"); };
    btn.addEventListener("click", e=>{
      e.stopPropagation();
      dd.classList.contains("open") ? close() : open();
    });
    document.addEventListener("click", e=>{
      if(dd.classList.contains("open") && !dd.contains(e.target)) close();
    });
    document.addEventListener("keydown", e=>{ if(e.key === "Escape") close(); });
  });
}

/* ---------- kiosk / presentation mode — fullscreen + decluttered chrome, for an unattended
   display (office lobby, donor meeting, conference booth). Always starts off on page load;
   never persisted, so staff can't accidentally leave a public visitor's browser in kiosk mode.
   onTourStart/onTourStop let map pages plug in their own auto-cycle (see startKioskTour). ---------- */
function attachKioskMode(onTourStart, onTourStop){
  const btn = document.getElementById("kioskBtn");
  if(!btn) return;
  let active = false;
  async function enter(){
    try{ await document.documentElement.requestFullscreen(); }catch(e){ console.warn("Fullscreen request failed:", e); }
    document.body.classList.add("kiosk-active");
    btn.textContent = "✕"; btn.title = "Exit presentation mode (Esc)";
    active = true;
    if(onTourStart) onTourStart();
  }
  function exit(){
    if(document.fullscreenElement) document.exitFullscreen().catch(()=>{});
    document.body.classList.remove("kiosk-active");
    btn.textContent = "⛶"; btn.title = "Presentation mode — fullscreen, decluttered, auto-tour";
    active = false;
    if(onTourStop) onTourStop();
  }
  btn.addEventListener("click", ()=> active ? exit() : enter());
  document.addEventListener("keydown", e=>{ if(e.key === "Escape" && active) exit(); });
  // covers exiting fullscreen via the browser's own UI (Esc, F11, swipe) not just our button
  document.addEventListener("fullscreenchange", ()=>{ if(!document.fullscreenElement && active) exit(); });
}

/* cycles through `stops` (an array of ids) every intervalMs, calling onStop(id) each time —
   the page decides what "showing" a stop means (flyTo + open a popup, in practice). Returns a
   function that stops the cycle, for attachKioskMode's onTourStop to call. */
function startKioskTour(stops, {intervalMs=9000, onStop}={}){
  if(!stops || !stops.length || !onStop) return ()=>{};
  let idx = 0;
  const showNext = ()=>{ onStop(stops[idx % stops.length]); idx++; };
  showNext();
  const timer = setInterval(showNext, intervalMs);
  return ()=> clearInterval(timer);
}

function attachUnitToggle(){
  const btn = document.getElementById("unitToggle");
  if(!btn) return;
  const paint = ()=>{ btn.textContent = getUnitSystem()==="imperial" ? "°F · in" : "°C · mm"; };
  paint();
  btn.addEventListener("click", ()=>{ setUnitSystem(getUnitSystem()==="imperial"?"metric":"imperial"); paint(); });
}

/* ---------- glossary panel (shared terms across all pages) ---------- */
const GLOSSARY = [
  ["ASAL","Arid and Semi-Arid Lands — the ~80% of Kenya's landmass (and much of southern Ethiopia) receiving under 600mm rain/year, where pastoralism is the dominant livelihood."],
  ["NDMA","National Drought Management Authority (Kenya) — publishes monthly county drought early-warning bulletins with four escalating phases: Normal, Alert, Alarm, Emergency."],
  ["IPC","Integrated Food Security Phase Classification — the international 5-phase famine early-warning standard (Minimal / Stressed / Crisis / Emergency / Famine) used by FAO, WFP, UNICEF, FEWS NET and partners."],
  ["FEWS NET","Famine Early Warning Systems Network — USAID-funded food-security monitoring and forecasting service covering East Africa."],
  ["GAM / SAM","Global / Severe Acute Malnutrition — WHO child-nutrition thresholds; GAM ≥15% of children under 5 is a nutrition emergency."],
  ["MUAC","Mid-Upper Arm Circumference — a quick tape-measure screening tool for acute malnutrition in children."],
  ["VCI","Vegetation Condition Index — NDMA's satellite greenness measure; ≤20 signals severe drought stress on pasture."],
  ["SPI","Standardised Precipitation Index — a WMO statistical measure of how far rainfall departs from the long-term average for a place and season."],
  ["Livelihood zone","A FEWS NET / NDMA classification of how households in an area typically get food and income (pastoral, agro-pastoral, riverine, fisheries, etc.)."],
  ["Need Index","This dashboard's own 0–100 blended score: 45% structural vulnerability (poverty, malnutrition, NDMA/IPC phase) + 55% live climate signal (rain deficit, soil dryness, heat), recalculated on every refresh."],
  ["Gadaa","The Borana Oromo's UNESCO-listed indigenous governance system — an age-grade structure electing leaders every 8 years that still regulates grazing, water and conflict resolution today."],
  ["Tula","Borana “singing wells” — hand-dug communal deep wells up to 30m, some centuries old, where cattle are watered in human chains passing buckets while singing to keep rhythm."],
  ["Ganna / Hagayya","The Borana names for the long rains (Mar–May) and short rains (Oct–Nov) — the two rainy seasons whose failure or success drives the drought cycle."],
  ["Jilaal / Bona","Names for the region's harshest dry season (Jan–Feb) and the second dry season (Jun–Sep)."],
  ["LAPSSET","Lamu Port–South Sudan–Ethiopia Transport corridor — the infrastructure mega-project cutting through Isiolo and Marsabit, reshaping land use and conflict dynamics."],
  ["WASH","Water, Sanitation and Hygiene — the humanitarian sector covering water trucking, boreholes, latrines and hygiene promotion."],
  ["Offtake / destocking","Emergency or planned early sale of livestock before drought kills them, converting a dying asset into cash — a core NDMA/PACIDA drought response."],
  ["Woreda","Ethiopia's third-level administrative unit — equivalent to a Kenyan sub-county."]
];
function attachGlossary(){
  const btn = document.getElementById("glossaryBtn"), panel = document.getElementById("glossaryPanel");
  if(!btn || !panel) return;
  const body = panel.querySelector(".gl-body");
  body.innerHTML = GLOSSARY.map(([t,d])=>`<div class="gl-item"><b>${t}</b><span>${d}</span></div>`).join("");
  const search = panel.querySelector(".gl-search");
  const closeBtn = panel.querySelector(".gl-close");
  const backdrop = document.getElementById("glBackdrop");
  btn.setAttribute("aria-expanded","false");
  panel.setAttribute("role","dialog");
  panel.setAttribute("aria-modal","false");
  panel.setAttribute("aria-label","Glossary of terms");
  function open(){
    panel.classList.add("open"); btn.setAttribute("aria-expanded","true");
    search.focus();
  }
  function close(){
    panel.classList.remove("open"); btn.setAttribute("aria-expanded","false");
    btn.focus();
  }
  btn.addEventListener("click", ()=>{ panel.classList.contains("open") ? close() : open(); });
  closeBtn.addEventListener("click", close);
  if(backdrop) backdrop.addEventListener("click", close);
  search.addEventListener("input", ()=>{
    const q = search.value.toLowerCase();
    body.querySelectorAll(".gl-item").forEach(el=>{ el.style.display = el.textContent.toLowerCase().includes(q) ? "" : "none"; });
  });
  panel.addEventListener("keydown", e=>{
    if(e.key==="Escape"){ close(); return; }
    if(e.key!=="Tab") return;
    const focusables = panel.querySelectorAll('button, input, [href]');
    const first = focusables[0], last = focusables[focusables.length-1];
    if(e.shiftKey && document.activeElement===first){ e.preventDefault(); last.focus(); }
    else if(!e.shiftKey && document.activeElement===last){ e.preventDefault(); first.focus(); }
  });
}

/* ---------- keyboard-accessible sortable table headers ---------- */
function wireSortableHeaders(selector, onActivate){
  document.querySelectorAll(selector).forEach(th=>{
    th.setAttribute("tabindex","0");
    th.setAttribute("aria-sort","none");
    th.addEventListener("click", ()=>onActivate(th));
    th.addEventListener("keydown", e=>{
      if(e.key==="Enter" || e.key===" "){ e.preventDefault(); onActivate(th); }
    });
  });
}

/* ---------- CSV export ---------- */
function downloadCSV(filename, rows){
  const csv = rows.map(row=>row.map(v=>{
    const s = String(v==null?"":v);
    return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
  }).join(",")).join("\n");
  const blob = new Blob([csv], {type:"text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* ---------- quick search / jump — accessible combobox/listbox pattern ---------- */
function attachSearch(getItems, onSelect){
  const input = document.getElementById("searchBox"), list = document.getElementById("searchResults");
  if(!input || !list) return;
  input.setAttribute("role","combobox");
  input.setAttribute("aria-autocomplete","list");
  input.setAttribute("aria-expanded","false");
  input.setAttribute("aria-controls","searchResults");
  list.setAttribute("role","listbox");
  let activeIndex = -1;

  function paintActive(){
    list.querySelectorAll(".sr-item").forEach((el,i)=>{
      const on = i===activeIndex;
      el.classList.toggle("active", on);
      el.setAttribute("aria-selected", on ? "true" : "false");
    });
    input.setAttribute("aria-activedescendant", activeIndex>=0 ? "sr-item-"+activeIndex : "");
  }
  function close(){
    list.style.display = "none";
    input.setAttribute("aria-expanded","false");
    activeIndex = -1;
  }
  function render(q){
    const ql = q.trim().toLowerCase();
    const matches = ql ? getItems().filter(it=>it.label.toLowerCase().includes(ql)).slice(0,8) : [];
    list.innerHTML = matches.map((m,i)=>
      `<div class="sr-item" id="sr-item-${i}" role="option" aria-selected="false" data-i="${i}">${m.label}</div>`
    ).join("");
    list._matches = matches;
    activeIndex = matches.length ? 0 : -1;
    paintActive();
    list.style.display = matches.length ? "block" : "none";
    input.setAttribute("aria-expanded", matches.length ? "true" : "false");
  }
  function select(i){
    const m = list._matches && list._matches[i];
    if(!m) return;
    onSelect(m); close(); input.value=""; input.blur();
  }
  input.addEventListener("input", ()=>render(input.value));
  input.addEventListener("focus", ()=>render(input.value));
  input.addEventListener("keydown", e=>{
    const n = (list._matches||[]).length;
    if(e.key==="ArrowDown"){ if(n){ e.preventDefault(); activeIndex=(activeIndex+1)%n; paintActive(); } }
    else if(e.key==="ArrowUp"){ if(n){ e.preventDefault(); activeIndex=(activeIndex-1+n)%n; paintActive(); } }
    else if(e.key==="Enter"){ if(activeIndex>=0){ e.preventDefault(); select(activeIndex); } }
    else if(e.key==="Escape"){ close(); input.blur(); }
  });
  list.addEventListener("click", e=>{
    const row = e.target.closest(".sr-item"); if(!row) return;
    select(+row.dataset.i);
  });
  document.addEventListener("click", e=>{ if(!e.target.closest(".search-wrap")) close(); });
}

/* ---------- 12-month rainfall history (Open-Meteo archive, no key) ---------- */
async function fetchMonthlyRain(lat, lon){
  const end = new Date(); end.setDate(end.getDate()-5);
  const start = new Date(end); start.setDate(start.getDate()-364);
  const iso = d => d.toISOString().slice(0,10);
  const url = "https://archive-api.open-meteo.com/v1/archive"
    + "?latitude="+lat+"&longitude="+lon
    + "&start_date="+iso(start)+"&end_date="+iso(end)
    + "&daily=precipitation_sum&timezone=Africa%2FNairobi";
  const res = await fetch(url);
  if(!res.ok) throw new Error("Archive "+res.status);
  const d = await res.json();
  const months = {};
  d.daily.time.forEach((ds,i)=>{
    const key = ds.slice(0,7);
    months[key] = (months[key]||0) + (d.daily.precipitation_sum[i]||0);
  });
  return Object.keys(months).sort().slice(-12).map(k=>({month:k, total:months[k]}));
}
/* Redesigned for self-explanatory reading at a glance, not just on hover:
   - a real mm y-axis (gridlines + labels) instead of bars floating with no scale
   - a dashed reference line at the ~60mm/month ASAL norm already quoted elsewhere on this
     site ("vs ~60mm ASAL expectation"), so it's visible which months actually fell short
   - shaded bands behind the long-rains (Mar-May) and short-rains (Oct-Nov) months, so a low
     bar during a "should be rainy" month reads very differently from a low bar in the dry
     season — this is the whole point of the "did the rains arrive on schedule" caption
   - the current month is visually marked as in-progress (dashed outline + "*") rather than
     looking like a genuine below-normal month when it's really just incomplete data
   - a legend spelling out what every colour/line means, since none of this is self-evident
     from bars alone */
function monthChart(data){
  if(!data || !data.length) return "";
  const W=560, H=280, names=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const NORM = 60; // ASAL monthly norm — matches the "~60mm ASAL expectation" figure used elsewhere
  const RAINY_MONTHS = new Set([3,4,5,10,11]); // long rains Mar-May, short rains Oct-Nov
  const plotLeft=40, plotRight=W-6, plotTop=16, plotBottom=H-42;
  const plotH = plotBottom-plotTop, plotW = plotRight-plotLeft;
  const bw = plotW/data.length;

  const dataMax = Math.max(...data.map(d=>d.total));
  const rawCeil = Math.max(dataMax, NORM) * 1.15;
  const step = rawCeil<=40?10 : rawCeil<=100?20 : rawCeil<=200?50:100;
  const axisMax = Math.ceil(rawCeil/step)*step;
  const yFor = v => plotBottom - (v/axisMax)*plotH;

  let seasonBands="", gridlines="", bars="", vals="", labels="";

  data.forEach((d,i)=>{
    const mIdx = parseInt(d.month.slice(5,7),10);
    if(RAINY_MONTHS.has(mIdx)){
      const x = plotLeft + i*bw;
      seasonBands += `<rect x="${x.toFixed(1)}" y="${plotTop}" width="${bw.toFixed(1)}" height="${plotH.toFixed(1)}" fill="#34B44B" opacity="0.08"/>`;
    }
  });

  for(let f=0; f<=1.001; f+=0.25){
    const v = axisMax*f, y=yFor(v);
    gridlines += `<line x1="${plotLeft}" y1="${y.toFixed(1)}" x2="${plotRight}" y2="${y.toFixed(1)}" stroke="#6B4E30" stroke-width="1" opacity="${f===0?0.6:0.25}"/>`;
    gridlines += `<text x="${plotLeft-6}" y="${(y+3).toFixed(1)}" font-size="10.5" fill="#B0906A" font-family="IBM Plex Mono" text-anchor="end">${Math.round(v)}</text>`;
  }
  gridlines += `<text x="${plotLeft-6}" y="8" font-size="9.5" fill="#B0906A" font-family="Barlow Condensed" text-anchor="end">mm</text>`;
  const normY = yFor(NORM);
  gridlines += `<line x1="${plotLeft}" y1="${normY.toFixed(1)}" x2="${plotRight}" y2="${normY.toFixed(1)}" stroke="#F0B22E" stroke-width="1.4" stroke-dasharray="5 4" opacity="0.9"/>`;

  data.forEach((d,i)=>{
    const isLast = i===data.length-1;
    const x = plotLeft + i*bw + 5, w = Math.max(1,bw-10);
    const barTop = yFor(d.total);
    const h = Math.max(1.5, plotBottom-barTop);
    const mIdx = parseInt(d.month.slice(5,7),10)-1;
    const fill = isLast ? "#F0B22E" : "#6FA3B4";
    const style = isLast
      ? `fill="${fill}" fill-opacity="0.32" stroke="${fill}" stroke-width="1.5" stroke-dasharray="3 3"`
      : `fill="${fill}" opacity="0.9"`;
    bars += `<rect x="${x.toFixed(1)}" y="${barTop.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="3" ${style}><title>${d.month}${isLast?" (month in progress)":""}: ${d.total.toFixed(0)} mm${RAINY_MONTHS.has(mIdx+1)?" — typical rainy-season month":""}</title></rect>`;
    vals += `<text x="${(x+w/2).toFixed(1)}" y="${(barTop-6).toFixed(1)}" font-size="11.5" fill="${isLast?'#F0B22E':'#9AB6C0'}" font-family="IBM Plex Mono" text-anchor="middle">${d.total.toFixed(0)}</text>`;
    labels += `<text x="${(x+w/2).toFixed(1)}" y="${H-14}" font-size="13" fill="#D8BD98" font-family="Barlow Condensed" font-weight="600" text-anchor="middle">${names[mIdx]}${isLast?"*":""}</text>`;
  });

  const svg = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" style="width:100%;height:280px;display:block" role="img" `
    + `aria-label="12 month rainfall history in millimetres, with typical rainy-season months and the ~${NORM}mm ASAL monthly norm marked for reference">`
    + `${seasonBands}${gridlines}${bars}${vals}${labels}</svg>`;

  const legend = `<div class="hist-legend">`
    + `<span><i class="hist-sw hist-sw-past"></i>Completed month</span>`
    + `<span><i class="hist-sw hist-sw-now"></i>This month (in progress)*</span>`
    + `<span><i class="hist-sw hist-sw-norm"></i>~${NORM}mm ASAL monthly norm</span>`
    + `<span><i class="hist-sw hist-sw-season"></i>Typical rainy season</span>`
    + `</div>`;

  return svg + legend;
}

/* ---------- village tags (OpenStreetMap-geocoded, see assets/villages.js), shown when zoomed in ---------- */
function attachVillageLayer(map, slug){
  if(typeof VILLAGES === "undefined" || !VILLAGES[slug] || !VILLAGES[slug].length) return null;
  const layer = L.layerGroup();
  VILLAGES[slug].forEach(([name, lat, lon])=>{
    const dot = L.circleMarker([lat,lon],{radius:3,color:"#F7EAD6",weight:1,fillColor:"#D8BD98",fillOpacity:.9});
    const label = L.marker([lat,lon],{interactive:false,
      icon:L.divIcon({className:"",html:'<div class="village-label">'+name+'</div>',iconAnchor:[-7,4]})});
    layer.addLayer(dot); layer.addLayer(label);
  });
  const VILLAGE_ZOOM = 11;
  const sync = ()=>{
    const show = map.getZoom() >= VILLAGE_ZOOM;
    if(show && !map.hasLayer(layer)) map.addLayer(layer);
    if(!show && map.hasLayer(layer)) map.removeLayer(layer);
  };
  map.on("zoomend", sync);
  sync();
  return layer;
}

/* ---------- PACIDA interventions (real project data, see assets/interventions.js) ---------- */

/* mirrors build_interventions.py's THEME_MAP — kept in sync by hand since the admin panel's
   theme <select> is hard-restricted to exactly these 9 values, so this can't drift silently. */
const THEME_COLORS = {
  "Emergency":"#ED1C24", "Disaster Risk Reduction":"#E8834A", "WASH":"#6FA3B4",
  "Health & Nutrition":"#D66FB0", "Education":"#F0B22E", "Climate Change":"#5FBF8F",
  "Peace & Governance":"#9C87D9", "Livelihood":"#34B44B", "Other":"#9A8F70"
};

function computeDuration(startISO, endISO){
  if(!startISO || !endISO) return "";
  const months = Math.round((new Date(endISO) - new Date(startISO)) / (1000*60*60*24*30.44));
  return Math.max(1, months) + " month" + (months===1 ? "" : "s");
}

/* Live project data from Supabase (staff-editable via admin/) — layered on top of the static
   assets/interventions.js snapshot that's already loaded as the INTERVENTIONS global by the
   time this runs. On any failure (network blip, misconfigured keys, a paused free-tier
   Supabase project) this quietly leaves INTERVENTIONS.projects exactly as the static snapshot
   already set it — the map keeps working, just without the latest staff edits, rather than
   going blank. Requires assets/supabase-config.js (SUPABASE_URL/SUPABASE_ANON_KEY) loaded
   before this script. */
async function loadLiveProjects(){
  if(typeof SUPABASE_URL === "undefined" || typeof INTERVENTIONS === "undefined") return;
  try{
    const res = await fetch(
      SUPABASE_URL + "/rest/v1/projects_live?select=*,project_locations(*)",
      {headers:{apikey:SUPABASE_ANON_KEY, Authorization:"Bearer "+SUPABASE_ANON_KEY}}
    );
    if(!res.ok) throw new Error("Supabase " + res.status);
    const rows = await res.json();
    INTERVENTIONS.projects = rows.map(r => ({
      id: r.id,
      year: r.start_date ? +r.start_date.slice(0,4) : null,
      donor: r.donor,
      theme: r.theme,
      theme_color: THEME_COLORS[r.theme] || THEME_COLORS.Other,
      title: r.title,
      status: r.status, // pre-derived by the projects_live view (end_date vs today)
      start: r.start_date,
      end: r.end_date,
      duration: computeDuration(r.start_date, r.end_date),
      population: r.population_note,
      locations: (r.project_locations || []).map(l => ({slug:l.slug, kind:l.kind, name:l.name, lat:l.lat, lon:l.lon}))
    }));
  }catch(e){
    console.warn("Live projects fetch failed, using static snapshot:", e);
  }
}

function projectsForSlug(slug){
  if(typeof INTERVENTIONS === "undefined") return [];
  return INTERVENTIONS.projects.filter(p => p.locations.some(l => l.slug === slug));
}
function officesForSlug(slug){
  if(typeof INTERVENTIONS === "undefined") return [];
  return INTERVENTIONS.offices.filter(o => o.slug === slug && o.lat != null);
}
function drawInterventionLayer(map, slug){
  const layer = L.layerGroup();
  projectsForSlug(slug).forEach(p=>{
    const loc = p.locations.find(l=>l.slug===slug);
    if(!loc) return;
    const regional = loc.kind === "regional";
    const m = L.circleMarker([loc.lat, loc.lon], regional
      ? {radius:6, color:p.theme_color, weight:1.5, fillColor:p.theme_color, fillOpacity:.25, dashArray:"2,2", className:"interv-dot interv-dot-regional"}
      : {radius:6, color:"#fff", weight:1, fillColor:p.theme_color, fillOpacity:.85, className:"interv-dot"}
    );
    m.bindPopup(
      `<h4>${p.title}</h4>`
      +`<div><span class="pop-k">Theme:</span> <span class="pop-v">${p.theme}</span></div>`
      +`<div><span class="pop-k">Donor:</span> <span class="pop-v">${p.donor||"—"}</span></div>`
      +`<div><span class="pop-k">Year:</span> <span class="pop-v">${p.year||"—"} &middot; ${p.status==="ongoing"?"Ongoing":"Completed"}</span></div>`
      +(p.duration?`<div><span class="pop-k">Duration:</span> <span class="pop-v">${p.duration}</span></div>`:"")
      +(p.population?`<div class="pop-reach"><span class="pop-k">Reach:</span> <span class="pop-v">${p.population}</span></div>`:"")
      +(regional
        ? `<div style="margin-top:6px"><span class="pop-k">Location:</span> Regional / multi-site programme &mdash; title names no specific place, shown at an approximate point within the operational area</div>`
        : `<div style="margin-top:6px"><span class="pop-k">Located at:</span> ${loc.name}</div>`),
      {maxWidth: 340}
    );
    layer.addLayer(m);
  });
  officesForSlug(slug).forEach(o=>{
    const m = L.marker([o.lat, o.lon], {
      icon: L.divIcon({className:"", html:'<div class="office-pin">&#9733;</div>', iconAnchor:[9,9]})
    });
    m.bindPopup(`<h4>${o.name}</h4><div class="pop-k">${o.note}</div>`);
    layer.addLayer(m);
  });
  return layer;
}
/* "ground surface" colour by intervention density — the ask: see the level of an
   area by colour, not just individual pins. Uses Leaflet.heat (L.heatLayer). */
function drawInterventionHeat(slugs){
  const pts = [];
  if(typeof INTERVENTIONS !== "undefined"){
    INTERVENTIONS.projects.forEach(p=>{
      p.locations.forEach(loc=>{
        if(slugs.includes(loc.slug)) pts.push([loc.lat, loc.lon, loc.kind==="regional"?0.5:1]);
      });
    });
    INTERVENTIONS.offices.forEach(o=>{
      if(slugs.includes(o.slug) && o.lat != null) pts.push([o.lat, o.lon, 0.6]);
    });
  }
  return L.heatLayer(pts, {
    radius: 70, blur: 55, max: 6, minOpacity: 0.42,
    gradient: {0.05:"#1F5E52", 0.25:"#2A6F63", 0.45:"#6FA3B4", 0.65:"#34B44B", 0.82:"#F0B22E", 1.0:"#ED1C24"}
  });
}
function renderInterventionList(containerId, slug){
  const el = document.getElementById(containerId);
  if(!el) return;
  const projects = projectsForSlug(slug).sort((a,b)=>(b.year||0)-(a.year||0));
  el.innerHTML = projects.map(p=>`<div class="interv-row">
    <span class="interv-dot-sw" style="background:${p.theme_color}"></span>
    <div class="interv-body">
      <div class="interv-title">${p.title}</div>
      <div class="interv-meta">${p.year||"—"} &middot; ${p.donor||"—"} &middot; ${p.theme} &middot; <span class="${p.status==='ongoing'?'status-ongoing':'status-done'}">${p.status==='ongoing'?'Ongoing':'Completed'}</span></div>
    </div>
  </div>`).join("") || '<div class="loading">No dated projects pinned to this specific area — see the full Impact Dashboard for regional programmes.</div>';
}

/* ---------- simple SVG charts (no external lib) ---------- */
function donutChart(data, size){
  size = size || 180;
  const total = data.reduce((a,d)=>a+d.value,0) || 1;
  const r = size/2, cx=size/2, cy=size/2, rInner = r*0.6;
  let angle = -Math.PI/2, paths = "";
  data.forEach(d=>{
    const frac = d.value/total;
    const a2 = angle + frac*Math.PI*2;
    const x1=cx+r*Math.cos(angle), y1=cy+r*Math.sin(angle);
    const x2=cx+r*Math.cos(a2), y2=cy+r*Math.sin(a2);
    const xi1=cx+rInner*Math.cos(a2), yi1=cy+rInner*Math.sin(a2);
    const xi2=cx+rInner*Math.cos(angle), yi2=cy+rInner*Math.sin(angle);
    const large = frac>0.5?1:0;
    paths += `<path d="M${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large} 1 ${x2.toFixed(2)},${y2.toFixed(2)} L${xi1.toFixed(2)},${yi1.toFixed(2)} A${rInner},${rInner} 0 ${large} 0 ${xi2.toFixed(2)},${yi2.toFixed(2)} Z" fill="${d.color}" opacity="0.92"><title>${d.label}: ${d.value}</title></path>`;
    angle = a2;
  });
  return `<svg viewBox="0 0 ${size} ${size}" style="width:100%;max-width:${size}px;height:auto;display:block;margin:0 auto">${paths}<text x="${cx}" y="${cy-4}" text-anchor="middle" font-size="20" font-weight="700" fill="#F7EAD6" font-family="IBM Plex Mono">${total}</text><text x="${cx}" y="${cy+14}" text-anchor="middle" font-size="9" fill="#D8BD98" font-family="Barlow Condensed" letter-spacing="1">PROJECTS</text></svg>`;
}
function yearBarChart(data){
  const W=760,H=160,pad=26;
  const max = Math.max(1, ...data.map(d=>d.completed+d.ongoing));
  const bw = W/data.length;
  let bars="", labels="";
  data.forEach((d,i)=>{
    const x = i*bw+3, w = Math.max(1,bw-6);
    const hc = (d.completed/max)*(H-pad), ho=(d.ongoing/max)*(H-pad);
    const yTop = H-pad-hc-ho;
    if(d.ongoing) bars += `<rect x="${x.toFixed(1)}" y="${yTop.toFixed(1)}" width="${w.toFixed(1)}" height="${ho.toFixed(1)}" fill="#F0B22E"><title>${d.year}: ${d.ongoing} ongoing</title></rect>`;
    if(d.completed) bars += `<rect x="${x.toFixed(1)}" y="${(yTop+ho).toFixed(1)}" width="${w.toFixed(1)}" height="${hc.toFixed(1)}" fill="#6FA3B4" opacity="0.85"><title>${d.year}: ${d.completed} completed</title></rect>`;
    if(i%2===0 || data.length<14) labels += `<text x="${(x+w/2).toFixed(1)}" y="${H-8}" font-size="9" fill="#9A8F70" text-anchor="middle">${String(d.year).slice(2)}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" style="width:100%;height:160px;display:block">${bars}${labels}</svg>`;
}

/* Standard glass map (satellite base + labels + dark alternative). Returns {map, layersControl}. */
/* Non-interactive decorative map — purely a textured backdrop behind the
   content column's glass panels. Same imagery as the real map on the same
   page, which already carries the Esri attribution, so this one omits its
   own. Fails silently (returns null) if the target element isn't present. */
function makeBackgroundMap(elId, center, zoom){
  const el = document.getElementById(elId);
  if(!el || typeof L === "undefined") return null;
  const map = L.map(elId, {
    zoomControl:false, attributionControl:false, dragging:false, touchZoom:false,
    scrollWheelZoom:false, doubleClickZoom:false, boxZoom:false, keyboard:false, tap:false
  }).setView(center, zoom);
  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",{maxZoom:17}).addTo(map);
  return map;
}

function makeGlassMap(center, zoom, elId, bounds){
  const opts = {zoomControl:false, scrollWheelZoom:true};
  if(bounds){
    opts.maxBounds = bounds;
    opts.maxBoundsViscosity = 1.0; // hard stop — can't drag past the intervention area
    opts.minZoom = zoom - 1;       // can't zoom out past ~the framing we chose
  }
  const map = L.map(elId||"map", opts).setView(center, zoom);
  if(bounds) map.setMaxBounds(bounds);
  L.control.zoom({position:"bottomright"}).addTo(map);
  const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",{
    attribution:'Imagery &copy; Esri, Maxar, Earthstar Geographics', maxZoom:17});
  const placeLabels = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",{
    attribution:'Labels &copy; Esri', maxZoom:17, pane:"shadowPane"});
  const darkBase = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{
    attribution:'&copy; OpenStreetMap contributors &copy; CARTO', subdomains:"abcd", maxZoom:12});
  satellite.addTo(map); placeLabels.addTo(map);
  const layersControl = L.control.layers(
    {"Aerial (satellite)":satellite,"Dark map":darkBase},
    {"Place names":placeLabels},
    {position:"bottomright",collapsed:true}).addTo(map);
  map.on("baselayerchange",()=>{ if(map.hasLayer(placeLabels)) placeLabels.bringToFront(); });
  return {map, layersControl};
}
