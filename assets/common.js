/* PACIDA ASAL Climate Watch — shared engine
   Live data: Open-Meteo API (no key). Need index aligned to NDMA / IPC / WHO frameworks. */

const PHASE_COLORS = { critical:"#C93A20", high:"#D96C2B", elevated:"#E0A21B", watch:"#7FA653" };
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
    bars+='<rect x="'+(i*bw+1).toFixed(1)+'" y="'+(H-h).toFixed(1)+'" width="'+(bw-2).toFixed(1)+'" height="'+h.toFixed(1)+'" rx="1.5" fill="'+(isFc?'#4E7C8A':'#E0A21B')+'" opacity="'+(isFc?0.85:0.9)+'"/>';
  });
  const sx=(splitIdx*bw).toFixed(1);
  return '<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" aria-hidden="true">'+bars
    +'<line x1="'+sx+'" y1="0" x2="'+sx+'" y2="'+H+'" stroke="#9C9077" stroke-width="1" stroke-dasharray="3 3"/></svg>';
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
