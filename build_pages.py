#!/usr/bin/env python3
import json, html as H

REGIONS = {
"marsabit": {
  "title":"Marsabit County", "country":"Kenya", "center":[2.6,37.9], "zoom":7,
  "hq":{"name":"Marsabit town","lat":2.3346,"lon":37.9891},
  "households":77495,"population":459785,"area":"70,961 km²","density":"6.5 / km²","hhsize":5.8,
  "poverty":83.2,"staticVuln":88,"phase":"NDMA Alert (worsening)","gam":"18–26% (North Horr & Laisamis highest, recent SMART surveys)",
  "intro":"Kenya's second-largest county and PACIDA's home base. A vast basalt-and-desert landscape running from the shores of Lake Turkana across the Chalbi Desert — Kenya's only true desert — to the Ethiopian border at Moyale. Mt. Marsabit's forested volcanic massif (1,700&nbsp;m) is a green island whose mist-fed highlands support the county's only rain-fed agriculture; everything around it is camel, goat and small-stock country of the Gabra, Rendille, Borana, Burji, Turkana, Samburu, Dassanach and El Molo peoples. Annual rainfall spans 200&nbsp;mm on the Chalbi floor to 800+&nbsp;mm on the mountain. Poverty (83.2%) is among the highest in Kenya and 80% of livelihoods depend directly on livestock.",
  "subcounties":[
    ["Moyale","Moyale town",108949,17709,"Agro-pastoral / cross-border trade","Butiye, Somare, Odda, Uran, Golbo plains, Godoma"],
    ["Marsabit Central (Saku)","Marsabit town",79181,15849,"Highland agro-pastoral","Karare, Sagante, Jaldesa, Dirib Gombo, Songa, Badassa, Kituruni"],
    ["North Horr","North Horr",71447,9789,"Pure pastoral (camel) — Chalbi desert","Dukana, Balesa, El Gade, Darade, Illeret, Malabot"],
    ["Marsabit South (Laisamis)","Laisamis",65376,11615,"Rendille pastoral","Korr, Kargi, Ngurunit, Logologo, Merille, Ilaut"],
    ["Marsabit North","Maikona",54297,7521,"Gabra pastoral — Chalbi fringe","Maikona, Kalacha, Bubisa, Turbi, Hurri Hills, Forolle"],
    ["Sololo","Sololo",44822,7238,"Agro-pastoral escarpment","Sololo Makutano, Ambalo, Dambala Fachana, Uran, Walda"],
    ["Loiyangalani","Loiyangalani",35713,7774,"Fisher-pastoral — Lake Turkana shore","El Molo Bay, Moite, Gatab (Mt Kulal), Arapal, Sarima, South Horr road"]
  ],
  "sites":[
    ["Marsabit town",2.3346,37.9891,"Saku — county HQ, highland"],
    ["Moyale",3.5270,39.0560,"Border town — cross-border trade hub"],
    ["North Horr",3.3190,37.0680,"Chalbi — Gabra pastoral"],
    ["Kalacha",3.1300,37.4250,"Chalbi oasis settlement"],
    ["Maikona",2.9400,37.5450,"Marsabit North HQ"],
    ["Loiyangalani",2.7560,36.7220,"Lake Turkana — fisher-pastoral"],
    ["Laisamis",1.5980,37.8070,"Rendille country, A2 corridor"],
    ["Korr",2.0000,37.5000,"Rendille pastoral settlement"],
    ["Illeret",4.3100,36.2300,"Dassanach, far north-west"],
    ["Sololo",3.5560,38.6560,"Escarpment agro-pastoral"],
    ["Turbi",3.4500,38.2500,"Dida Galgalu plains"]
  ],
  "livelihoods":[["Pastoral (camel, goat, small stock)",81,"#D96C2B"],["Agro-pastoral (Saku highlands, Sololo)",10,"#7FA653"],["Fisheries (Lake Turkana)",4,"#4E7C8A"],["Trade, employment & other",5,"#E0A21B"]],
  "sectors":[
    ["Livestock economy","≈80% of household income is livestock-based. Camels are the drought-critical species (milk through dry seasons); Merille and Moyale are the key livestock markets. 2019 census recorded well over 2 million goats and sheep, ~420,000 cattle and ~240,000 camels in the county (indicative)."],
    ["Water & WASH","Household water is from boreholes, shallow wells (Chalbi springs at Kalacha/Maikona), pans and rock catchments. In drought, trekking distances exceed 15–25 km in North Horr and Laisamis; NDMA's Jan 2026 bulletin flagged Marsabit among counties with the longest grazing-to-water distances. Badassa dam and desalination pilots serve the highlands."],
    ["Nutrition & health","GAM has repeatedly breached the WHO 15% 'critical' emergency threshold in North Horr and Laisamis during droughts (SMART surveys 18–26%). PPR, CCPP and FMD livestock disease outbreaks were reported county-wide in early 2026, cutting milk availability for children."],
    ["Education","Low enrolment and high dropout track drought cycles as families migrate with herds; school-meals programmes and low-cost boarding ('lchekuti' model) are the main retention tools. PACIDA runs education access programmes across the county."],
    ["Conflict & peace","Resource-based and political flashpoints: Moyale corridor, Turbi–Forolle, and the Marsabit mountain belt (Borana–Gabra dynamics). Peace dividends directly determine access to dry-season grazing reserves. PACIDA facilitates inter-community resource-sharing dialogues and SMS Voices early warning."]
  ],
  "pacida":"County HQ of PACIDA. Programmes: emergency drought response (water trucking, relief food, cash transfers), mass livestock deworming & treatment (480,000+ animals reached), WASH infrastructure, Ward Climate Change Planning Committees & County Climate Change Fund support, women's climate-resilience projects (Caritas Austria), education access, and peace &amp; governance including the SMS Voices project with the County Government."
},
"samburu": {
  "title":"Samburu County","country":"Kenya","center":[1.25,36.95],"zoom":8,
  "hq":{"name":"Maralal","lat":1.0966,"lon":36.6980},
  "households":65910,"population":310327,"area":"21,065 km²","density":"15 / km²","hhsize":4.7,
  "poverty":71.0,"staticVuln":72,"phase":"NDMA Alert","gam":"13–20% in drought years (Samburu North highest)",
  "intro":"A transition county between the central highlands and the northern deserts — 92% classified ASAL. From the Lorroki plateau and Kirisia forests around Maralal (2,000&nbsp;m, agro-pastoral) the land falls north through Baragoi's Suguta corridor and east past the Mathews Range and Mt Ololokwe to the Ewaso Ng'iro lowlands at Archer's Post. The Samburu (Lokop) are cattle-culture pastoralists; drought forces herds into contested northern grazing where cattle rustling and armed conflict compound climate risk. Fewer than 15% of households have piped water.",
  "subcounties":[
    ["Samburu West (Central)","Maralal","≈134,000 *","≈29,000 *","Agro-pastoral — Lorroki plateau","Kisima, Suguta Marmar, Loosuk, Poro, Morijo, Lodokejek"],
    ["Samburu North","Baragoi","≈97,000 *","≈20,000 *","Pastoral — cattle & small stock","South Horr, Tuum, Marti, Nachola, Latakweny, Bendera"],
    ["Samburu East","Wamba","≈79,000 *","≈17,000 *","Pastoral + conservancies & tourism","Archer's Post, Sereolipi, Lodungokwe, Ngilai, Lerata, Lpus"]
  ],
  "subnote":"* 2019 census county totals are exact (310,327 people / 65,910 households); sub-county splits shown are indicative estimates pending ward-level tabulation.",
  "sites":[
    ["Maralal",1.0966,36.6980,"County HQ — Lorroki plateau"],
    ["Baragoi",1.7830,36.7860,"Samburu North HQ"],
    ["Wamba",0.9820,37.3200,"Samburu East HQ, Mathews Range"],
    ["Archer's Post",0.6400,37.6690,"Ewaso Ng'iro lowlands"],
    ["South Horr",2.0880,36.9210,"Nyiro valley, route to L. Turkana"],
    ["Suguta Marmar",0.8800,36.6800,"Agro-pastoral plateau"],
    ["Sereolipi",1.1200,37.6300,"Eastern pastoral rangelands"]
  ],
  "livelihoods":[["Pastoral (cattle, small stock)",68,"#D96C2B"],["Agro-pastoral (Lorroki plateau)",20,"#7FA653"],["Tourism, conservancies & trade",8,"#4E7C8A"],["Formal employment & other",4,"#E0A21B"]],
  "sectors":[
    ["Livestock economy","Cattle-dominant with rapid small-stock growth as a drought adaptation; camels are being adopted in the north. Key markets: Maralal, Baragoi, Archer's Post; trekking routes to Rumuruti/Nyahururu. Livestock body condition and milk yields collapse fastest in Samburu East lowlands."],
    ["Water & WASH","Only ~14% of households have piped water (2019 census). Sources: seasonal rivers (Ewaso Ng'iro), sand dams, boreholes, springs on the plateau. Dry-season water distances in Samburu East and North commonly exceed 10 km for households and 20 km for herds."],
    ["Nutrition & health","Acute malnutrition remains high in Samburu North (Tiaty-adjacent belt): NDMA lists Samburu among counties with significant numbers of children 6–59 months needing urgent treatment (Jan 2026). Milk deficit during dry seasons is the primary driver."],
    ["Education","Secondary attainment 6.4% — about a quarter of the national rate (2019 census). Morans' herding duties and early marriage suppress enrolment; conservancy bursaries and school feeding are key levers."],
    ["Conflict & peace","Cattle-rustling corridors: Baragoi–Suguta valley (Samburu–Turkana), and Samburu East–Isiolo boundary over Ewaso grazing. Disarmament cycles and peace committees shape whether drought reserves (Kirisia forest, Mathews Range) can be shared safely."]
  ],
  "pacida":"PACIDA implements resilience and emergency programming in Samburu: drought response (water, cash and fodder), WASH, livestock health campaigns, and cross-county peace dialogues linking Samburu, Marsabit and Isiolo grazing communities under the Humanitarian-Development-Peace nexus approach."
},
"isiolo": {
  "title":"Isiolo County","country":"Kenya","center":[0.75,38.4],"zoom":8,
  "hq":{"name":"Isiolo town","lat":0.3546,"lon":37.5822},
  "households":58072,"population":268002,"area":"25,336 km²","density":"11 / km²","hhsize":4.6,
  "poverty":65.0,"staticVuln":76,"phase":"NDMA Alert (worsening)","gam":"12–18%; severe acute malnutrition cases documented in 2026 drought reporting",
  "intro":"The gateway to northern Kenya and a melting pot of Borana, Turkana, Somali, Meru and Samburu communities. The county straddles the Ewaso Ng'iro river — the lifeline that carries highland water into the drylands and around which people, livestock and wildlife concentrate in every drought. Isiolo town is booming (A2 tarmac, abattoir, planned resort city under LAPSSET) while Merti and Garbatulla remain deep pastoral country. Isiolo was among the worst-hit counties in the 2023 floods and slid back into drought Alert through 2025–26 — the classic ASAL whiplash of failed rains and flash floods.",
  "subcounties":[
    ["Isiolo (Central)","Isiolo town",121066,29853,"Urban / peri-urban agro-pastoral","Kambi Garba, Kiwanjani, Checheles, Burat, Ngare Mara, Gambella, Oldonyiro, Kipsing"],
    ["Garbatulla","Garbatulla",99730,18661,"Borana pastoral + Kinna/Rapsu irrigation","Kinna, Rapsu, Kulamawe, Belgesh, Sericho, Boji, Duse"],
    ["Merti","Merti",47206,9558,"Riverine Ewaso pastoral","Korbesa, Bulesa, Biliqo, Malkadaka, Dadacha Basa, Mata Arba"]
  ],
  "sites":[
    ["Isiolo town",0.3546,37.5822,"County HQ, A2 corridor"],
    ["Merti",1.0500,38.6560,"Ewaso riverine — Merti-Korbesa pipeline"],
    ["Garbatulla",0.5300,38.5100,"Borana pastoral HQ"],
    ["Kinna",0.2900,38.2000,"Irrigation scheme, Meru NP border"],
    ["Oldonyiro",0.6200,36.9300,"Western pastoral, Samburu border"],
    ["Sericho",0.1100,39.1000,"Eastern rangelands, Garissa border"],
    ["Ngare Mara",0.4800,37.6300,"A2 corridor settlement"]
  ],
  "livelihoods":[["Pastoral (cattle, goats, camels)",70,"#D96C2B"],["Agro-pastoral & irrigation (Burat, Kinna, Rapsu, Merti)",15,"#7FA653"],["Urban trade, casual labour & employment",12,"#E0A21B"],["Other (firewood/charcoal, remittances)",3,"#4E7C8A"]],
  "sectors":[
    ["Livestock economy","Borana cattle heartland with growing camel herds. Isiolo livestock market and the export abattoir anchor offtake; in drought, herds converge on the Ewaso riverine strip and Meru NP border, driving disease transmission and human-wildlife conflict."],
    ["Water & WASH","The Ewaso Ng'iro's flow is falling from upstream highland abstraction — the county's central climate-security issue. Flagship response: Merti–Korbesa water supply project (NDMA/EU/NWWDA/County). Elsewhere: boreholes, pans; Sericho and Cherab wards face the longest dry-season distances."],
    ["Nutrition & health","2026 drought reporting documented severe acute malnutrition cases in Isiolo; NDMA lists the county in Alert with worsening food access. GAM typically 12–18% in bad years, concentrated in Merti and Sericho."],
    ["Floods & multi-hazard","Isiolo is the textbook twin-disaster county: among the worst affected by the 2023 El Niño floods (Ewaso burst its banks, displacing riverine villages) followed directly by failed rains. Preparedness must cover both extremes."],
    ["Conflict & peace","Grazing pressure funnels Borana, Somali, Samburu and Turkana herds into the same riverine reserves; flashpoints on the Isiolo–Samburu (Oldonyiro) and Isiolo–Garissa (Modogashe–Sericho) axes. Land speculation along LAPSSET adds a new conflict layer."]
  ],
  "pacida":"PACIDA scaled up in Isiolo after the 2023 floods put the organisation on the response frontline. Programmes: flood and drought emergency response, WASH, resilience building with Ward Climate Change Planning Committees, livestock health, and peace dialogues on shared Ewaso grazing."
},
"borena": {
  "title":"Borena Zone","country":"Southern Ethiopia (Oromia)","center":[4.6,38.4],"zoom":8,
  "hq":{"name":"Yabelo","lat":4.8850,"lon":38.0830},
  "households":232000,"population":1210000,"area":"≈45,000 km²","density":"≈27 / km²","hhsize":5.2,
  "poverty":78.0,"staticVuln":82,"phase":"IPC Phase 2–3 (Stressed–Crisis)","gam":"Persistently elevated; SAM admissions surged in 2022–23 drought and remain above pre-drought baselines",
  "intro":"The Ethiopian half of PACIDA's cross-border footprint and the cultural heartland of the Borana Oromo, whose Gadaa governance system (UNESCO-listed) and deep-well 'tula' system — the famous singing wells — have managed these rangelands for five centuries. The zone lost an estimated 60%+ of cattle in the catastrophic 2020–23 drought (five consecutive failed seasons), a livelihood shock from which herds have not recovered. Rainfall is bimodal: Ganna long rains (Mar–May) and Hagayya short rains (Oct–Nov). Cross-border movement with Marsabit County (Moyale, Dukana–Dillo, Forolle) is constant — grazing, trade, kinship and conflict all flow across the line, which is why single-country programming fails here.",
  "subcounties":[
    ["Yabelo","Yabelo town","≈120,000 †","≈23,000 †","Pastoral / zone capital","Dida Hara, Surupa, Dharito, Elwaye road"],
    ["Moyale (ET)","Moyale","≈95,000 †","≈18,000 †","Cross-border trade + pastoral","Bede, Lagasure, Chamuk, border kebeles"],
    ["Dire","Mega","≈100,000 †","≈19,000 †","Pastoral — tula deep wells","Mega, Dubluk road, Magado crater"],
    ["Teltele","Teltele","≈95,000 †","≈18,000 †","Pastoral / agro-pastoral west","Sarite, El Gof, Konso border kebeles"],
    ["Arero","Arero","≈90,000 †","≈17,000 †","Pastoral — forest fringe","Web, Melbana, Mata Gafarsa"],
    ["Dubluk","Dubluk","≈55,000 †","≈11,000 †","Pastoral — wells cluster","Dubluk town, Tula wells kebeles"],
    ["Miyo","Miyo (Hidi Lola)","≈60,000 †","≈12,000 †","Pastoral border woreda","Hidi Lola, Tuka, border kebeles"],
    ["Dillo","Dillo","≈50,000 †","≈10,000 †","Pastoral — Kenya border (Dukana axis)","Dillo town, Mado, border kebeles"],
    ["Dhas","Dhas","≈45,000 †","≈9,000 †","Pastoral","Dhas town, Gorile"],
    ["Gomole / Elwaye / Guchi / Wachile","various","≈220,000 †","≈42,000 †","Pastoral (newer woredas)","Elwaye, Wachile, Guchi, Gomole kebeles"]
  ],
  "subnote":"† Woreda figures are indicative projections from the 2007 CSA census pending a new national census; zone totals (~1.21 M people, ~232,000 households) are population-projection based. Boundary on the map is approximate.",
  "sites":[
    ["Yabelo",4.8850,38.0830,"Zone capital"],
    ["Moyale (ET)",3.5540,39.0520,"Border twin-town with Kenya"],
    ["Mega",4.0700,38.3000,"Dire woreda — tula wells"],
    ["Dubluk",4.3500,38.2400,"Deep-well cluster"],
    ["Teltele",4.8000,37.4000,"Western woreda"],
    ["Dillo",4.2000,37.7300,"Kenya border, Dukana axis"],
    ["Arero",4.7500,38.8000,"Eastern forest fringe"],
    ["Hidi Lola",3.8500,38.9500,"Miyo woreda, border trade"]
  ],
  "livelihoods":[["Pastoral (cattle-centred Borana system)",75,"#D96C2B"],["Agro-pastoral (maize, haricot, teff pockets)",20,"#7FA653"],["Trade & town economies (Moyale, Yabelo)",5,"#E0A21B"]],
  "sectors":[
    ["Livestock economy","Cattle are wealth, identity and food security; the 2020–23 drought killed an estimated 3.3+ million livestock across Borena and neighbouring zones, collapsing herd capital. Restocking, fodder value-chains and shifting toward camels/small stock are the recovery frontier. Moyale is the region's cross-border trade artery."],
    ["Water & the tula system","The nine tula deep-well clusters (Dubluk, Mega, Web among them) are communally governed and drought-proof but labour-intensive; motorised boreholes and ponds (haro) supplement them. Water governance through Gadaa institutions is a resilience asset most interventions should build on, not replace."],
    ["Nutrition & health","SAM admissions surged through 2022–23 and stabilisation-centre caseloads remain above pre-drought baselines; measles and cholera outbreaks tracked displacement into IDP sites around Dubluk and Yabelo during the drought peak."],
    ["Rangelands & bush encroachment","Decades of fire suppression drove acacia/commiphora bush encroachment over prime grasslands — a slow-onset crisis reducing carrying capacity independent of rainfall. Participatory rangeland management and controlled clearing are priority interventions."],
    ["Conflict & cross-border dynamics","Borana–Gabra and Borana–Garre dynamics span the Kenya line; Moyale town has repeatedly split along it. Peace here is a precondition for drought-cycle mobility — closed borders during conflict episodes have trapped herds away from reserve grazing with fatal results."]
  ],
  "pacida":"PACIDA's Ethiopian office anchors cross-border programming: drought emergency response, WASH around the tula clusters, livestock health, education support, and Borana-led peace and resource-sharing dialogues that keep the Marsabit–Borena grazing corridors open. Funded partners include Welthungerhilfe and BMZ programmes."
}
}

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
    cells = "".join('<div class="mo %s">%s<small>%s</small></div>' % (c,m,l) for m,l,c in mo)
    return ('<div class="season">%s</div><div class="season-note">Bimodal ASAL calendar: long rains Mar–May '
            '(Ganna in Borana), short rains Oct–Dec (Hagayya). Both seasons must perform for pasture recovery; '
            'a single failed season triggers Alert, consecutive failures cascade to Alarm/Emergency.</div>') % cells

def page(rid, r):
    sub_rows = ""
    for row in r["subcounties"]:
        name,hq,pop,hh,lz,vill = row
        pops = fmtnum(pop); hhs = fmtnum(hh)
        sub_rows += ("<tr><td><b>%s</b><br><small>HQ: %s</small></td><td class='mono'>%s</td>"
                     "<td class='mono'>%s</td><td>%s</td><td>%s</td></tr>") % (name,hq,pops,hhs,lz,vill)
    subnote = ('<p style="font-size:12px;color:var(--faint);margin-top:8px">%s</p>' % r["subnote"]) if r.get("subnote") else ""

    lz_rows = "".join(('<div class="lz-row"><div>%s</div><div class="lz-bar">'
                       '<div class="lz-fill" style="width:%d%%;background:%s"></div></div>'
                       '<div class="lz-pct">%d%%</div></div>') % (n,p,c,p) for n,p,c in r["livelihoods"])

    sect = "".join('<div class="src"><b>%s</b><span>%s</span></div>' % (t,x) for t,x in r["sectors"])

    tl = ""
    for item in DROUGHT_TIMELINE:
        yr, tx = item[0], item[1]
        cls = " now" if len(item)>2 else ""
        tl += '<div class="tl%s"><div class="yr">%s</div><div class="tx">%s</div></div>' % (cls,yr,tx)

    sites_json = json.dumps(r["sites"])
    nav = navbar(rid)

    return TEMPLATE % dict(
        rid=rid, title=r["title"], country=r["country"],
        nav=nav, intro=r["intro"],
        center=json.dumps(r["center"]), zoom=r["zoom"],
        hqname=r["hq"]["name"], hqlat=r["hq"]["lat"], hqlon=r["hq"]["lon"],
        households=fmtnum(r["households"]), population=fmtnum(r["population"]),
        area=r["area"], density=r["density"], hhsize=r["hhsize"],
        poverty=r["poverty"], staticVuln=r["staticVuln"], phase=r["phase"], gam=r["gam"],
        sub_rows=sub_rows, subnote=subnote, lz_rows=lz_rows, sectors=sect,
        seasoncal=seasoncal(), timeline=tl, pacida=r["pacida"], sites_json=sites_json
    )

def fmtnum(v):
    if isinstance(v,int): return "{:,}".format(v)
    return str(v)

def navbar(active):
    links = [("index.html","Home","home"),("marsabit.html","Marsabit","marsabit"),
             ("samburu.html","Samburu","samburu"),("isiolo.html","Isiolo","isiolo"),
             ("borena.html","Borena · S. Ethiopia","borena")]
    return "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if k==active else "", t) for h,t,k in links)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s — PACIDA ASAL Climate Watch</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>

<div id="map" role="application" aria-label="Aerial map of %(title)s"></div>

<div class="overlay">

<header class="glass">
  <div class="brand">
    <h1><a href="index.html">PACIDA <span>&middot;</span> ASAL Climate Watch</a></h1>
    <div class="sub">%(title)s &middot; %(country)s</div>
  </div>
  <nav class="site">%(nav)s</nav>
  <div class="head-right">
    <div class="livepill"><span class="dot" id="liveDot"></span><span id="liveState">Live &middot; Open-Meteo</span></div>
    <div class="clock mono" id="clock">--:--:-- EAT</div>
    <button class="refresh" id="refreshBtn" type="button">Refresh now</button>
  </div>
</header>

<div class="strip">
  <div class="cell glass"><div class="k">Need index (live)</div><div class="v" id="needV">&mdash;</div><div class="n" id="needN">recalculating from live weather</div></div>
  <div class="cell glass"><div class="k">Now at %(hqname)s</div><div class="v" id="tempV">&mdash;</div><div class="n" id="tempN">&mdash;</div></div>
  <div class="cell glass"><div class="k">Rain, past 30 days</div><div class="v" id="rainV">&mdash;</div><div class="n">vs ~60 mm ASAL expectation</div></div>
  <div class="cell glass"><div class="k">Topsoil moisture</div><div class="v" id="soilV">&mdash;</div><div class="n">0&ndash;7 cm &middot; VCI proxy</div></div>
  <div class="cell glass"><div class="k">Households</div><div class="v">%(households)s</div><div class="n">Population %(population)s</div></div>
  <div class="cell glass"><div class="k">Drought phase</div><div class="v" style="font-size:15px;font-family:'Archivo'">%(phase)s</div><div class="n">Poverty %(poverty)s%%</div></div>
</div>

<main>
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
</main>

<div class="wide">

  <div class="panel glass">
    <h2>Live conditions by settlement <span class="tag">every dot refreshes with the page</span></h2>
    <div class="sites" id="siteGrid"></div>
  </div>

  <div class="panel glass">
    <h2>Sub-units, households &amp; key settlements <span class="tag">KNBS 2019 census / CSA projections</span></h2>
    <div class="table-scroll">
    <table class="ptable">
      <thead><tr><th>Sub-county / woreda</th><th>Population</th><th>Households</th><th>Livelihood zone</th><th>Key settlements &amp; villages (indicative)</th></tr></thead>
      <tbody>%(sub_rows)s</tbody>
    </table>
    </div>
    %(subnote)s
  </div>

  <div class="panel glass">
    <h2>Livelihood zones <span class="tag">FEWS NET livelihood zoning, indicative shares</span></h2>
    <div class="lz">%(lz_rows)s</div>
  </div>

  <div class="panel glass">
    <h2>Seasonal calendar</h2>
    %(seasoncal)s
  </div>

  <div class="panel glass">
    <h2>Sector deep-dive</h2>
    <div class="src-grid">%(sectors)s</div>
  </div>

  <div class="panel glass">
    <h2>Drought history &mdash; the recurrence the index is built for</h2>
    <div class="timeline">%(timeline)s</div>
  </div>

  <div class="panel glass">
    <h2>PACIDA in %(title)s</h2>
    <p>%(pacida)s</p>
  </div>

  <div class="panel glass">
    <h2>Sources</h2>
    <div class="src-grid">
      <div class="src"><b>Live weather</b><span>Open-Meteo API per settlement point; auto-refresh every 10 minutes. </span><a href="https://open-meteo.com" target="_blank" rel="noopener">open-meteo.com</a></div>
      <div class="src"><b>Population &amp; households</b><span>Kenya 2019 Population &amp; Housing Census Vol. I &amp; II (KNBS); Ethiopia CSA projections for Borena. </span><a href="https://www.knbs.or.ke" target="_blank" rel="noopener">knbs.or.ke</a></div>
      <div class="src"><b>Drought &amp; food security</b><span>NDMA monthly bulletins &amp; county early-warning; IPC analyses; FEWS NET East Africa. </span><a href="https://ndma.go.ke" target="_blank" rel="noopener">ndma.go.ke</a></div>
      <div class="src"><b>Programmes</b><span>PACIDA annual reports and programme pages. </span><a href="https://pacida.org" target="_blank" rel="noopener">pacida.org</a></div>
    </div>
  </div>
</div>

<footer class="glass">
  <div>PACIDA ASAL Climate Watch &middot; %(title)s detail &middot; monitoring prototype &mdash; deployment decisions require ground-truthing</div>
  <div class="mono" id="footTime"></div>
</footer>

</div><!-- /overlay -->

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="assets/boundaries.js"></script>
<script src="assets/common.js"></script>
<script>
const RID = "%(rid)s";
const STATIC_VULN = %(staticVuln)s;
const SITES = %(sites_json)s;  /* [name, lat, lon, note] */
const HQ = {name:"%(hqname)s", lat:%(hqlat)s, lon:%(hqlon)s};

startClock();
const {map} = makeGlassMap(%(center)s, %(zoom)s);

/* region outline */
if (BOUNDARIES[RID]) {
  L.geoJSON({type:"Feature",geometry:BOUNDARIES[RID]},{
    style:{color:"#FFFFFF",weight:1.8,opacity:.9,fillColor:"#E0A21B",fillOpacity:.06,
           dashArray:RID==="borena"?"6 5":null}
  }).addTo(map);
}

const siteLayer = L.layerGroup().addTo(map);
const siteState = SITES.map(s=>({name:s[0],lat:s[1],lon:s[2],note:s[3],live:null}));

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
        +"<div><span class='pop-k'>Now:</span> <span class='pop-v'>"+s.live.temp.toFixed(1)+"&deg;C &middot; "+s.live.rh+"%% RH</span></div>"
        +"<div><span class='pop-k'>Rain 30 d:</span> <span class='pop-v'>"+s.live.rain30.toFixed(1)+" mm</span></div>"
        +"<div><span class='pop-k'>Soil:</span> <span class='pop-v'>"+(s.live.soil*100).toFixed(1)+"%%</span></div>"
        : "<div class='pop-k'>loading&hellip;</div>"));
    const label = L.marker([s.lat,s.lon],{interactive:false,
      icon:L.divIcon({className:"",html:'<div class="site-label">'+s.name+'</div>',iconAnchor:[-10,7]})});
    siteLayer.addLayer(m); siteLayer.addLayer(label);
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
        +'<div class="site-row"><span>Temp now</span><b>'+s.live.temp.toFixed(1)+'&deg;C</b></div>'
        +'<div class="site-row"><span>Rain 30 d</span><b>'+s.live.rain30.toFixed(0)+' mm</b></div>'
        +'<div class="site-row"><span>Soil 0&ndash;7 cm</span><b>'+(s.live.soil*100).toFixed(1)+'%%</b></div>'
        +'<div class="site-row"><span>7-d max avg</span><b>'+s.live.tmax7.toFixed(1)+'&deg;C</b></div>'
        : '<div class="loading">loading&hellip;</div>')
      +'</div>';
  }).join("");
}
renderSiteGrid();

function renderHQ(w){
  const need = w.need, band = needBand(need);
  document.getElementById("hqBadge").textContent = bandLabel(band)+" &middot; "+need;
  document.getElementById("hqBadge").innerHTML = bandLabel(band)+" &middot; "+need;
  document.getElementById("hqBadge").style.background = PHASE_COLORS[band];
  document.getElementById("hqMarker").style.left = need+"%%";
  document.getElementById("hqMetrics").innerHTML =
     '<div class="m"><div class="mk">Now</div><div class="mv">'+w.temp.toFixed(1)+'<small>&deg;C</small></div></div>'
    +'<div class="m"><div class="mk">Rain 30 d</div><div class="mv">'+w.rain30.toFixed(0)+'<small> mm</small></div></div>'
    +'<div class="m"><div class="mk">Soil 0&ndash;7 cm</div><div class="mv">'+(w.soil*100).toFixed(1)+'<small>%%</small></div></div>'
    +'<div class="m"><div class="mk">7-d max avg</div><div class="mv">'+w.tmax7.toFixed(1)+'<small>&deg;C</small></div></div>';
  document.getElementById("hqSpark").innerHTML = sparkline(w.dailyRain, w.splitIdx);
  document.getElementById("needV").textContent = need;
  document.getElementById("needN").textContent = bandLabel(band)+" &mdash; blended NDMA/IPC-aligned score";
  document.getElementById("tempV").textContent = w.temp.toFixed(1)+"\u00b0C";
  document.getElementById("tempN").textContent = w.rh+"%% RH \u00b7 wind "+w.wind.toFixed(0)+" km/h";
  document.getElementById("rainV").textContent = w.rain30.toFixed(0)+" mm";
  document.getElementById("soilV").textContent = (w.soil*100).toFixed(1)+"%%";
}

async function refreshAll(){
  const st=document.getElementById("liveState"), dotEl=document.getElementById("liveDot");
  st.textContent="Updating\u2026";
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
    st.textContent="Live \u00b7 Open-Meteo";
    dotEl.style.background="var(--normal)";
  }catch(e){
    console.error(e);
    st.textContent="Feed unavailable \u2014 check connection";
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
    import io, os
    for rid, r in REGIONS.items():
        out = page(rid, r)
        open(rid + ".html","w").write(out)
        print(rid+".html", len(out), "bytes")
