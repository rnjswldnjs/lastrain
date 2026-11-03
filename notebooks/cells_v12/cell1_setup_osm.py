# ── 셀 1. 준비 + OSM에서 지하철 노선(정차역 순서) 받아오기 ──
# 키 필요 없음. OpenStreetMap Overpass API(무료)를 쓴다.
import json, time, re, requests

# 지금 프로토타입의 지하철 구간 (index.html ROUTES 그대로) — (경로, 노선, 출발역, 도착역, 조사상 역 수)
SUB = [
 ("R01","신분당선","강남","정자",5), ("R01","수인분당선","정자","수원",15),
 ("R02","경의중앙선","홍대입구","대곡",8), ("R02","3호선","대곡","대화",5),
 ("R03","2호선","건대입구","잠실",4),
 ("R05","4호선","혜화","창동",8), ("R05","1호선","창동","의정부",6),
 ("R06","2호선","사당","강남",4), ("R06","신분당선","강남","수지구청",8),
 ("R07","9호선 급행","여의도","김포공항",5), ("R07","김포골드라인","김포공항","운양",5),
 ("R08","7호선","숭실대입구","고속터미널",4), ("R08","3호선","고속터미널","수서",None), ("R08","GTX-A","수서","동탄",3),
 ("R09","4호선","충무로","서울역",3), ("R09","GTX-A","서울역","운정중앙",4),
 ("R10","2호선","서울대입구","사당",2), ("R10","4호선","사당","한대앞",16),
 ("R11","신림선","관악산","신림",3), ("R11","2호선","신림","사당",4), ("R11","4호선","사당","범계",9),
]
# OSM 노선 이름에서 찾을 말
KW = {"신분당선":"신분당", "수인분당선":"수인|분당", "경의중앙선":"경의|중앙", "3호선":"3호선", "2호선":"2호선",
      "4호선":"4호선", "1호선":"1호선|경원", "9호선 급행":"9호선", "김포골드라인":"김포|골드", "7호선":"7호선",
      "GTX-A":"GTX|광역급행", "신림선":"신림"}
BBOX = "36.9,126.4,38.1,127.6"   # 수도권
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
HDR = {"User-Agent": "lastrain-capstone/1.0"}

def overpass(q):
    for url in OVERPASS:
        for _ in range(2):
            try:
                r = requests.post(url, data={"data": q}, headers=HDR, timeout=120)
                if r.status_code == 200: return r.json()
                print("  ", url.split('/')[2], r.status_code); time.sleep(5)
            except Exception as e:
                print("  ", url.split('/')[2], type(e).__name__); time.sleep(5)
    raise RuntimeError("Overpass 실패")

OSM = {}   # 노선 → {"rels":[...], "nodes":{id:{name,lat,lon}}}
for line, kw in KW.items():
    q = f'''[out:json][timeout:90];
    rel["type"="route"]["route"~"subway|train|light_rail|monorail"]["name"~"{kw}"]({BBOX})->.r;
    .r out body;
    node(r.r);
    out;'''
    d = overpass(q)
    rels  = [e for e in d["elements"] if e["type"]=="relation"]
    nodes = {e["id"]: {"name": e.get("tags",{}).get("name",""), "lat": e["lat"], "lon": e["lon"]}
             for e in d["elements"] if e["type"]=="node"}
    OSM[line] = {"rels": rels, "nodes": nodes}
    print(f"{line:8} 노선 relation {len(rels):2}개 · 정차 노드 {len(nodes)}개 ·",
          " / ".join(sorted({r['tags'].get('name','') for r in rels}))[:110])
    time.sleep(2)

json.dump(OSM, open("osm_lines.json","w"), ensure_ascii=False)
print("\n저장: osm_lines.json")
