# 셀 F. 출발지·도착지 좌표를 OSM으로 + 역 출구(번호) 수집
# 카카오 응답은 저장하면 안 되므로, 저장해서 쓰는 좌표는 전부 OpenStreetMap(ODbL)으로 바꾼다
# 셀 A(overpass, P, HDR)를 먼저 실행해 둘 것
import json, math, time

def dist(p, q):
    R = 6371000
    la1, lo1, la2, lo2 = map(math.radians, (p[0], p[1], q[0], q[1]))
    h = (math.sin((la2-la1)/2)**2
         + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2)
    return 2*R*math.asin(math.sqrt(h))

# (경로, 출발지 이름, 찾을 말, 기준점=첫 승차 지점, 반경 m)
ORIG = [
    ("R01", "스타벅스 몬테소리점", "몬테소리", (37.49712, 127.02799), 800),
    ("R02", "스타벅스 홍대공항철도역점", "공항철도", (37.55805, 126.92602), 500),
    ("R03", "건국대 상허기념도서관", "상허", (37.54006, 127.07026), 1200),
    ("R04", "연세대 중앙도서관", "중앙도서관|학술문화", (37.55999, 126.93502), 900),
    ("R05", "방송통신대 대학본부", "방송통신", (37.58215, 127.00198), 700),
    ("R06", "KB국민은행 사당동센터", "국민은행|KB", (37.47648, 126.98255), 600),
    ("R07", "IFC서울", "IFC|국제금융", (37.52180, 126.92415), 800),
    ("R09", "동국대 중앙도서관", "중앙도서관", (37.56107, 126.99260), 900),
    ("R10", "서울대 관정도서관", "관정", (37.45752, 126.94912), 1200),
    ("R11", "서울대 행정관", "행정관", (37.46882, 126.94531), 2000),
]
# 마지막에 걸어서 도착하는 경로만: (경로, 도착 역, 찾을 말, 기준점=마지막 하차 지점)
DEST = [
    ("R01", "수원역", "^수원$|^수원역", (37.26581, 126.99931)),
    ("R03", "평내호평역", "평내호평", (37.65493, 127.24388)),
    ("R04", "부평역", "^부평$|^부평역", (37.49322, 126.72272)),
    ("R08", "동탄역", "^동탄$|^동탄역", (37.19848, 127.09598)),
    ("R09", "운정역", "^운정$|^운정역", (37.72603, 126.76633)),
]
# 출발지에서 걸어가는 지하철역 (출구를 찾을 역)
EXIT_ST = {"R01": "강남", "R02": "홍대입구", "R03": "건대입구", "R05": "혜화",
           "R06": "사당", "R07": "여의도", "R09": "충무로", "R11": "관악산"}

def q_name(kw, c, r, extra=""):
    q = f'''[out:json][timeout:60];
    (nwr["name"~"{kw}"]{extra}(around:{r},{c[0]},{c[1]});
     nwr["branch"~"{kw}"]{extra}(around:{r},{c[0]},{c[1]}););
    out center tags;'''
    els = overpass(q)["elements"]
    out = []
    for e in els:
        lat = e.get("lat", e.get("center", {}).get("lat"))
        lon = e.get("lon", e.get("center", {}).get("lon"))
        if lat is None:
            continue
        t = e.get("tags", {})
        nm = (t.get("name", "") + " " + t.get("branch", "")).strip()
        out.append((round(dist(c, (lat, lon))), nm, round(lat, 6), round(lon, 6), f"{e['type']}/{e['id']}"))
    return sorted(out)

PL = {"origin": {}, "dest": {}, "exits": {}}
print("== 출발지 ==")
for rid, label, kw, c, r in ORIG:
    try:
        cands = q_name(kw, c, r)
    except RuntimeError:
        print(rid, "실패. 이 셀만 다시 실행"); break
    print(f"{rid} {label}: 후보 {len(cands)}개")
    for d, nm, la, lo, oid in cands[:5]:
        print(f"    {d:5}m  {nm}  ({la}, {lo})  {oid}")
    PL["origin"][rid] = {"label": label, "cands": cands[:5]}
    time.sleep(2)

print("\n== 도착 역 ==")
for rid, label, kw, c in DEST:
    try:
        cands = q_name(kw, c, 1500, '["railway"="station"]')
    except RuntimeError:
        print(rid, "실패"); break
    print(f"{rid} {label}: " + (" / ".join(f"{d}m {nm} {oid}" for d, nm, la, lo, oid in cands[:3]) or "없음"))
    PL["dest"][rid] = {"label": label, "cands": cands[:3]}
    time.sleep(2)

print("\n== 출구 ==")
for rid, st in EXIT_ST.items():
    c = next(x[3] for x in ORIG if x[0] == rid)
    q = f'''[out:json][timeout:60];
    node["railway"="subway_entrance"](around:450,{c[0]},{c[1]});
    out tags;'''
    try:
        els = overpass(q)["elements"]
    except RuntimeError:
        print(rid, "실패"); break
    ex = [{"ref": e.get("tags", {}).get("ref", ""), "name": e.get("tags", {}).get("name", ""),
           "lat": round(e["lat"], 6), "lon": round(e["lon"], 6)} for e in els]
    PL["exits"][rid] = {"station": st, "exits": ex}
    refs = sorted({x["ref"] for x in ex if x["ref"]}, key=lambda s: (len(s), s))
    print(f"{rid} {st}: 출구 {len(ex)}개 · 번호 있는 것 {sum(1 for x in ex if x['ref'])}개 · {refs[:20]}")
    time.sleep(2)

json.dump(PL, open(P("osm_places.json"), "w"), ensure_ascii=False)
print("\n저장: osm_places.json")
