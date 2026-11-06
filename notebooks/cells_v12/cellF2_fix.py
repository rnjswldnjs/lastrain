# 셀 F2. 셀 F에서 덜 맞은 출발지 3곳 다시 찾기 + 출구 수집 (셀 F 결과 PL을 이어서 씀)
import json, time
FIX = [  # (경로, 찾는 조건, 기준점, 반경)
    ("R05", '["name"~"대학본부|본관"]', (37.58215, 127.00198), 700),
    ("R07", '["name"~"IFC|아이에프씨"]["highway"!~"."]', (37.52180, 126.92415), 800),
    ("R11", '["building"]["name"~"행정관|60동"]', (37.46882, 126.94531), 2000),
]
for rid, flt, c, r in FIX:
    q = f'[out:json][timeout:60];nwr{flt}(around:{r},{c[0]},{c[1]});out center tags;'
    try:
        els = overpass(q)["elements"]
    except RuntimeError:
        print(rid, "실패. 이 셀만 다시 실행"); break
    cands = []
    for e in els:
        lat = e.get("lat", e.get("center", {}).get("lat")); lon = e.get("lon", e.get("center", {}).get("lon"))
        if lat is None: continue
        t = e.get("tags", {})
        cands.append((round(dist(c, (lat, lon))), t.get("name", ""), round(lat, 6), round(lon, 6),
                      f"{e['type']}/{e['id']}", t.get("building", ""), t.get("operator", "")))
    cands.sort()
    print(f"{rid}: 후보 {len(cands)}개")
    for x in cands[:6]:
        print(f"    {x[0]:5}m  {x[1]}  ({x[2]}, {x[3]})  {x[4]}  building={x[5]} operator={x[6]}")
    PL["origin"][rid + "_fix"] = {"cands": cands[:6]}
    time.sleep(2)

print("\n== 출구 ==")
for rid, st in EXIT_ST.items():
    c = next(x[3] for x in ORIG if x[0] == rid)
    q = f'[out:json][timeout:60];node["railway"="subway_entrance"](around:450,{c[0]},{c[1]});out body;'
    try:
        els = overpass(q)["elements"]
    except RuntimeError:
        print(rid, "실패. 이 셀만 다시 실행"); break
    ex = [{"ref": e.get("tags", {}).get("ref", ""), "name": e.get("tags", {}).get("name", ""),
           "lat": round(e["lat"], 6), "lon": round(e["lon"], 6)} for e in els if "lat" in e]
    PL["exits"][rid] = {"station": st, "exits": ex}
    refs = sorted({x["ref"] for x in ex if x["ref"]}, key=lambda s: (len(s), s))
    print(f"{rid} {st}: 출구 {len(ex)}개 · 번호 있는 것 {sum(1 for x in ex if x['ref'])}개 · {refs[:20]}")
    time.sleep(2)

json.dump(PL, open(P("osm_places.json"), "w"), ensure_ascii=False)
from google.colab import files
json.dump(PL, open("osm_places.json", "w"), ensure_ascii=False)
files.download("osm_places.json")
print("\n저장 + 내려받기: osm_places.json")
