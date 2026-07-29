#!/usr/bin/env python3
"""One-off batch geocoder for village names listed in each county's subcounty
'key settlements & villages' text, using OpenStreetMap Nominatim (free, no key).
Respects Nominatim's usage policy: 1 req/sec, descriptive User-Agent, results cached
so re-runs are cheap and resumable. Writes assets/villages.json: {slug: [[name,lat,lon], ...]}
Only keeps matches that fall within (a padded) bounding box of the county's real boundary,
so wrong-country/wrong-place matches are dropped rather than shown as fact.
"""
import json, os, time, urllib.request, urllib.parse

SITE = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(SITE, "villages_geocode_cache.json")
OUT_PATH = os.path.join(SITE, "assets", "villages.json")
UA = "kenya-asal-climate-watch/1.0 (village label lookup; contact: pacida.org)"

counties = json.load(open(os.path.join(SITE, "counties.json"), encoding="utf-8"))
boundaries = json.load(open(os.path.join(SITE, "assets", "boundaries.json"), encoding="utf-8"))

cache = {}
if os.path.exists(CACHE_PATH):
    cache = json.load(open(CACHE_PATH, encoding="utf-8"))


def bbox(geom):
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
    return min(lons), max(lons), min(lats), max(lats)


def geocode(query, viewbox):
    params = {
        "q": query, "format": "json", "limit": 1,
        "viewbox": ",".join(str(x) for x in viewbox), "bounded": 0,
    }
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


results = {}
if os.path.exists(OUT_PATH):
    results = json.load(open(OUT_PATH, encoding="utf-8"))

total_q = 0
for slug, r in counties.items():
    geom = boundaries.get(slug)
    if not geom:
        continue
    minlon, maxlon, minlat, maxlat = bbox(geom)
    padlon = (maxlon - minlon) * 0.2 + 0.05
    padlat = (maxlat - minlat) * 0.2 + 0.05
    country = "Ethiopia" if r["country"] != "Kenya" else "Kenya"
    countyname = r["title"].replace(" County", "").replace(" Zone", "")

    names = set()
    for sc in r["subcounties"]:
        for v in sc[5].split(","):
            v = v.strip()
            if v and len(v) > 2 and "plains" not in v.lower() and "road" not in v.lower() and "kebele" not in v.lower():
                names.add(v)

    slug_results = results.get(slug, [])
    have = {row[0] for row in slug_results}
    for name in sorted(names):
        if name in have:
            continue
        key = f"{name}|{slug}"
        if key in cache:
            hit = cache[key]
        else:
            query = f"{name}, {countyname}, {country}"
            try:
                hit = geocode(query, (minlon - padlon, minlat - padlat, maxlon + padlon, maxlat + padlat))
            except Exception as e:
                print("ERROR", key, e)
                hit = None
            cache[key] = hit
            total_q += 1
            time.sleep(1.1)
            if total_q % 20 == 0:
                json.dump(cache, open(CACHE_PATH, "w", encoding="utf-8"))
                print(f"...{total_q} queries so far")
        if hit:
            lat, lon = hit
            if (minlon - padlon) <= lon <= (maxlon + padlon) and (minlat - padlat) <= lat <= (maxlat + padlat):
                slug_results.append([name, round(lat, 4), round(lon, 4)])
    results[slug] = slug_results
    json.dump(cache, open(CACHE_PATH, "w", encoding="utf-8"))
    json.dump(results, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(slug, "->", len(slug_results), "villages geocoded")

print("DONE. total new queries:", total_q)
