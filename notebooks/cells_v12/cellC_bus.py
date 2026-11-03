# 셀 C. 버스 구간 정류장 좌표 + 도로 모양
# 키: 코랩 보안 비밀 DATA_GO_KR_KEY (일반 인증키 Decoding). 코드엔 키 값이 없음
# 셀 A의 P, dist 등은 셀 B에서 정의된 것을 씀
import json, re, requests
from google.colab import userdata

KEY = (userdata.get("DATA_GO_KR_KEY") or "").strip()
print("DATA_GO_KR_KEY:", "있음" if KEY else "없음 (보안 비밀 확인)")

BUS_LEGS = [  # (경로, 노선, 승차 정류장, 하차 정류장)
    ("R03", "M2323", "잠실광역환승센터", "호평상업지구"),
    ("R04", "7737", "연세대학교앞", "홍대입구역"),
    ("R04", "1400", "홍대입구역", "부평역"),
    ("R09", "074", "운정중앙역", "운정역"),
    ("R10", "5511", "농생대", "서울대입구역"),
]

def jget(url, params):
    try:
        r = requests.get(url, params={"serviceKey": KEY, **params}, timeout=20)
        return r.json(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:120]}"

def nm(s):
    return re.sub(r"[\s.·()]", "", str(s or ""))

def pick(stops, a, b):
    """stops: [(이름, lat, lon), ...] 순서대로. a 다음에 나오는 b 까지 자름 (순환 노선은 한 바퀴 이어 붙임)"""
    ext = stops + stops
    best = None
    for i, s in enumerate(stops):
        if nm(a) not in nm(s[0]):
            continue
        for j in range(i + 1, i + len(stops)):
            if nm(b) in nm(ext[j][0]):
                if best is None or j - i < best[1] - best[0]:
                    best = (i, j)
                break
    return ext[best[0]:best[1] + 1] if best else None

def seoul(line):
    j, err = jget("http://ws.bus.go.kr/api/rest/busRouteInfo/getBusRouteList",
                  {"strSrch": line, "resultType": "json"})
    items = ((j or {}).get("msgBody") or {}).get("itemList") or []
    route = next((x for x in items if str(x.get("busRouteNm")) == line), None)
    if not route:
        return None, None, err or "서울 API에 노선 없음"
    rid = route["busRouteId"]
    j2, _ = jget("http://ws.bus.go.kr/api/rest/busRouteInfo/getStaionByRoute",
                 {"busRouteId": rid, "resultType": "json"})
    st = ((j2 or {}).get("msgBody") or {}).get("itemList") or []
    stops = [(s["stationNm"], float(s["gpsY"]), float(s["gpsX"])) for s in st]
    j3, _ = jget("http://ws.bus.go.kr/api/rest/busRouteInfo/getRoutePath",
                 {"busRouteId": rid, "resultType": "json"})
    path = [(float(p["gpsY"]), float(p["gpsX"]))
            for p in ((j3 or {}).get("msgBody") or {}).get("itemList") or []]
    return stops, path, f"서울 busRouteId {rid}"

def gyeonggi(line):
    j, err = jget("https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteListv2",
                  {"keyword": line, "format": "json"})
    lst = ((j or {}).get("response", {}).get("msgBody", {}) or {}).get("busRouteList") or []
    lst = lst if isinstance(lst, list) else [lst]
    cands = [x for x in lst if str(x.get("routeName")) == line]
    if not cands:
        return None, None, err or "경기 API에 노선 없음"
    out = []
    for c in cands:
        j2, _ = jget("https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2",
                     {"routeId": c["routeId"], "format": "json"})
        st = ((j2 or {}).get("response", {}).get("msgBody", {}) or {}).get("busRouteStationList") or []
        st = st if isinstance(st, list) else [st]
        if st:
            out.append((c, [(s["stationName"], float(s["y"]), float(s["x"])) for s in st]))
    if not out:
        return None, None, "경기 API 정류장 목록 없음 (응답: " + str(j)[:150] + ")"
    return out, None, "경기"

def cut_path(path, a_pt, b_pt):
    if len(path) < 2:
        return None
    ia = min(range(len(path)), key=lambda i: dist(path[i], a_pt))
    ext = path + path
    ib = min(range(ia + 1, ia + len(path)), key=lambda i: dist(ext[i], b_pt))
    seg = ext[ia:ib + 1]
    if dist(seg[0], a_pt) > 300 or dist(seg[-1], b_pt) > 300:
        return None
    slim = [seg[0]]
    for p in seg[1:]:
        if dist(slim[-1], p) >= 25:
            slim.append(p)
    if slim[-1] != seg[-1]:
        slim.append(seg[-1])
    return [[round(p[0], 5), round(p[1], 5)] for p in slim]

BSEG = {}
for rid_, line, a, b in BUS_LEGS:
    key = f"{rid_}:{a}→{b}"
    stops, path, src = seoul(line)
    part = pick(stops, a, b) if stops else None
    if not part:
        g, _, gsrc = gyeonggi(line)
        for c, gst in (g or []):
            part = pick(gst, a, b)
            if part:
                src = f"경기 routeId {c['routeId']} ({c.get('regionName', '')})"
                path = None
                break
        if not part:
            print(f"{key}: X 못 찾음 · 서울: {src} · 경기: {gsrc}")
            if stops:
                print("   서울 정류장 이름 예시:", [s[0] for s in stops[:12]])
            continue
    shape = cut_path(path, part[0][1:], part[-1][1:]) if path else None
    BSEG[key] = {"line": line, "src": src,
                 "stops": [[s[0], round(s[1], 6), round(s[2], 6)] for s in part],
                 "shape": shape or [[round(s[1], 5), round(s[2], 5)] for s in part],
                 "shape_src": "도로" if shape else "정류장 연결"}
    print(f"{key}: {len(part) - 1}개 정류장 · {BSEG[key]['shape_src']} · {src}")
    print("   " + " > ".join(s[0] for s in part))

json.dump(BSEG, open(P("seg_bus.json"), "w"), ensure_ascii=False)
print()
print(f"저장: seg_bus.json, {len(BSEG)}/{len(BUS_LEGS)} 구간")
