/* PACIDA ASAL Climate Watch — shared engine
   Live data: Open-Meteo API (no key). Need index aligned to NDMA / IPC / WHO frameworks. */

const PHASE_COLORS = { critical:"#E64A2E", high:"#E8834A", elevated:"#F0B22E", watch:"#8FBB5F" };
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
    +'<line x1="'+sx+'" y1="0" x2="'+sx+'" y2="'+H+'" stroke="#C6BB9A" stroke-width="1" stroke-dasharray="3 3"/></svg>';
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
  btn.addEventListener("click", ()=>{ panel.classList.toggle("open"); if(panel.classList.contains("open")) search.focus(); });
  closeBtn.addEventListener("click", ()=>panel.classList.remove("open"));
  if(backdrop) backdrop.addEventListener("click", ()=>panel.classList.remove("open"));
  search.addEventListener("input", ()=>{
    const q = search.value.toLowerCase();
    body.querySelectorAll(".gl-item").forEach(el=>{ el.style.display = el.textContent.toLowerCase().includes(q) ? "" : "none"; });
  });
  document.addEventListener("keydown", e=>{ if(e.key==="Escape") panel.classList.remove("open"); });
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

/* ---------- quick search / jump ---------- */
function attachSearch(getItems, onSelect){
  const input = document.getElementById("searchBox"), list = document.getElementById("searchResults");
  if(!input || !list) return;
  function render(q){
    const ql = q.trim().toLowerCase();
    const matches = ql ? getItems().filter(it=>it.label.toLowerCase().includes(ql)).slice(0,8) : [];
    list.innerHTML = matches.map((m,i)=>`<div class="sr-item" data-i="${i}">${m.label}</div>`).join("");
    list._matches = matches;
    list.style.display = matches.length ? "block" : "none";
  }
  input.addEventListener("input", ()=>render(input.value));
  input.addEventListener("focus", ()=>render(input.value));
  input.addEventListener("keydown", e=>{
    if(e.key==="Enter"){
      const m = list._matches && list._matches[0];
      if(m){ onSelect(m); list.style.display="none"; input.value=""; input.blur(); }
    } else if(e.key==="Escape"){ list.style.display="none"; input.blur(); }
  });
  list.addEventListener("click", e=>{
    const row = e.target.closest(".sr-item"); if(!row) return;
    const m = list._matches[+row.dataset.i];
    onSelect(m); list.style.display="none"; input.value="";
  });
  document.addEventListener("click", e=>{ if(!e.target.closest(".search-wrap")) list.style.display="none"; });
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
function monthChart(data){
  if(!data || !data.length) return "";
  const W=560,H=112,names=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const max = Math.max(20, ...data.map(d=>d.total));
  const bw = W/data.length;
  let bars="", labels="";
  data.forEach((d,i)=>{
    const h = Math.max(1,(d.total/max)*(H-30));
    const x = i*bw+4, w = Math.max(1,bw-8);
    const isLast = i===data.length-1;
    const mIdx = parseInt(d.month.slice(5,7),10)-1;
    bars += `<rect x="${x.toFixed(1)}" y="${(H-20-h).toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="2" fill="${isLast?'#F0B22E':'#6FA3B4'}" opacity="${isLast?1:0.9}"><title>${d.month}: ${d.total.toFixed(0)} mm</title></rect>`;
    labels += `<text x="${(x+w/2).toFixed(1)}" y="${H-6}" font-size="9" fill="#C6BB9A" text-anchor="middle">${names[mIdx]}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" style="width:100%;height:112px;display:block" role="img" aria-label="12 month rainfall history">${bars}${labels}</svg>`;
}

/* Standard glass map (satellite base + labels + dark alternative). Returns {map, layersControl}. */
function makeGlassMap(center, zoom){
  const map = L.map("map",{zoomControl:false, scrollWheelZoom:true}).setView(center, zoom);
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
