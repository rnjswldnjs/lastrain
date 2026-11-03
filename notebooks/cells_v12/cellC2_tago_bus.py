# 셀 C2. 인천 1400번 정류장 좌표 (국토부 TAGO 버스노선정보, 활용신청 필요 / 무료)
import json, requests
from google.colab import userdata
KEY = (userdata.get("DATA_GO_KR_KEY") or "").strip()
BASE = "https://apis.data.go.kr/1613000/BusRouteInfoInqireService/"
CITY = 23  # 인천

def tago(op, params):
    # 오퍼레이션 이름이 대문자로 바뀐 버전도 있어서 둘 다 시도
    for name in (op, op[0].upper() + op[1:]):
        try:
            r = requests.get(BASE + name, params={"serviceKey": KEY, "_type": "json",
                                                  "numOfRows": 300, **params}, timeout=20)
            j = r.json()
            items = j["response"]["body"]["items"]
            items = items.get("item", []) if isinstance(items, dict) else []
            return (items if isinstance(items, list) else [items]), name
        except Exception:
            last = r.text[:200] if "r" in dir() else "요청 실패"
    return None, last

routes, info = tago("getRouteNoList", {"cityCode": CITY, "routeNo": "1400"})
if routes is None:
    print("TAGO 응답 이상:", info)
    print("활용신청 직후면 1시간쯤 뒤에 다시 실행")
else:
    routes = [x for x in routes if str(x.get("routeno")) == "1400"]
    print("1400 노선 후보:", [(x.get("routeid"), x.get("startnodenm"), x.get("endnodenm")) for x in routes])
    done = False
    for rt in routes:
        st, _ = tago("getRouteAcctoThrghSttnList", {"cityCode": CITY, "routeId": rt["routeid"]})
        st = sorted(st or [], key=lambda s: int(s.get("nodeord", 0)))
        stops = [(s["nodenm"], float(s["gpslati"]), float(s["gpslong"])) for s in st]
        part = pick(stops, "홍대입구역", "부평역")
        if part:
            key = "R04:홍대입구역→부평역"
            BSEG[key] = {"line": "1400", "src": f"TAGO 인천 routeId {rt['routeid']}",
                         "stops": [[s[0], round(s[1], 6), round(s[2], 6)] for s in part],
                         "shape": [[round(s[1], 5), round(s[2], 5)] for s in part],
                         "shape_src": "정류장 연결"}
            print(f"{key}: {len(part) - 1}개 정류장")
            print("   " + " > ".join(s[0] for s in part))
            done = True
            break
        print("  이 노선에선 못 맞춤. 정류장 예시:", [s[0] for s in stops[:15]])
    if done:
        json.dump(BSEG, open(P("seg_bus.json"), "w"), ensure_ascii=False)
        print(f"저장: seg_bus.json, {len(BSEG)}/5 구간")
