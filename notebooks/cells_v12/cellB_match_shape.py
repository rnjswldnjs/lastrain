# 셀 B. 구간마다 OSM 노선 고르기 -> 정차역 좌표 -> 선로 모양 잘라내기
# 셀 A의 SUB, OSM, overpass, P 를 그대로 씀
import json, os, re, math, time

def norm(n):
    n = re.sub(r"\(.*?\)", "", n or "").replace(" ", "")
    return n[:-1] if n.endswith("역") and len(n) > 2 else n

def stop_seq(rel, nodes):
    seq = []
    for m in rel["members"]:
        if m["type"] != "node" or not m["role"].startswith("stop"):
            continue
        nd = nodes.get(str(m["ref"]))
        if not nd or not nd["name"]:
            continue
        if seq and norm(seq[-1][0]) == norm(nd["name"]):
            continue
        seq.append((nd["name"], nd["lat"], nd["lon"]))
    return seq

def cut(seq, a, b):
    a, b = norm(a), norm(b)
    names = [norm(s[0]) for s in seq]
    if a not in names or b not in names:
        return None
    loop = len(seq) > 2 and names[0] == names[-1]
    ext = seq + seq[1:] if loop else seq
    en = [norm(s[0]) for s in ext]
    for i, n in enumerate(en):
        if n == a and b in en[i+1:]:
            j = en.index(b, i+1)
            return ext[i:j+1]
    return None

def dist(p, q):
    R = 6371000
    la1, lo1, la2, lo2 = map(math.radians, (p[0], p[1], q[0], q[1]))
    h = (math.sin((la2-la1)/2)**2
         + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2)
    return 2*R*math.asin(math.sqrt(h))

def plen(pts):
    return sum(dist(pts[i], pts[i+1]) for i in range(len(pts)-1))

# 1) 구간 맞추기
SEG = {}
for rid, line, a, b, expect in SUB:
    key = f"{rid}:{a}→{b}"
    cands = []
    for rel in OSM[line]["rels"]:
        p = cut(stop_seq(rel, OSM[line]["nodes"]), a, b)
        if p:
            cands.append((rel, p))
    if not cands:
        print(f"{key}: X 맞는 노선 없음")
        continue
    cands.sort(key=lambda c: (0 if expect is not None and len(c[1])-1 == expect else 1,
                              len(c[1])))
    rel, part = cands[0]
    n = len(part) - 1
    SEG[key] = {"line": line, "rel": rel["id"],
                "rel_name": rel["tags"].get("name", ""), "osm_count": n,
                "stops": [[s[0], round(s[1], 6), round(s[2], 6)] for s in part]}
    if expect is not None and n != expect:
        print(f"{key}: OSM {n}개역 / 조사 {expect}개역 : "
              + " > ".join(s[0] for s in part))
print(f"구간 맞춤 {len(SEG)}/{len(SUB)} (위에 찍힌 것만 역 수가 조사와 다름)")
print()

# 2) 선로 모양 받기 (드라이브에 저장, 재사용)
GP = P("osm_geom.json")
GEOM = json.load(open(GP)) if os.path.exists(GP) else {}
for rel_id in sorted({str(v["rel"]) for v in SEG.values()}):
    if rel_id in GEOM:
        continue
    try:
        d = overpass(f"[out:json][timeout:150];rel({rel_id});out geom;")
    except RuntimeError:
        print("선로 받기 실패. 이 셀만 다시 실행하면 이어서 받음")
        break
    ways = [m["geometry"] for m in d["elements"][0]["members"]
            if m["type"] == "way" and m["role"] in ("", "forward", "backward")
            and m.get("geometry")]
    pts_all = []
    for w in ways:
        pts = [(g["lat"], g["lon"]) for g in w]
        if pts_all and dist(pts_all[-1], pts[-1]) < dist(pts_all[-1], pts[0]):
            pts = pts[::-1]
        pts_all += pts
    GEOM[rel_id] = pts_all
    json.dump(GEOM, open(GP, "w"))
    print(f"  relation {rel_id}: way {len(ways)}개, 점 {len(pts_all)}개")
    time.sleep(2)

# 3) 구간만 잘라내기. 이상하면 정차역 잇는 선으로 대체
for key, v in SEG.items():
    stops = [(s[1], s[2]) for s in v["stops"]]
    v["shape"] = [list(p) for p in stops]
    v["shape_src"] = "정차역 연결"
    ratio = 0
    pts = GEOM.get(str(v["rel"]))
    if pts:
        def near(p):
            return min(range(len(pts)), key=lambda i: dist(pts[i], p))
        ia, ib = near(stops[0]), near(stops[-1])
        seg = pts[ia:ib+1] if ia <= ib else pts[ia:] + pts[:ib+1]
        ratio = plen(seg) / max(1, plen(stops))
        ok = (0.9 <= ratio <= 1.8 and dist(seg[0], stops[0]) < 400
              and dist(seg[-1], stops[-1]) < 400)
        if ok:
            slim = [seg[0]]
            for p in seg[1:]:
                if dist(slim[-1], p) >= 30:
                    slim.append(p)
            if slim[-1] != seg[-1]:
                slim.append(seg[-1])
            v["shape"] = [[round(p[0], 5), round(p[1], 5)] for p in slim]
            v["shape_src"] = "선로"
    print(f"{key:24} {v['shape_src']:6} 점 {len(v['shape']):4}개, 길이비 {ratio:.2f}")

json.dump(SEG, open(P("seg_subway.json"), "w"), ensure_ascii=False)
n_track = sum(v["shape_src"] == "선로" for v in SEG.values())
print()
print(f"저장: seg_subway.json, {len(SEG)}/{len(SUB)} 구간, 선로 모양 {n_track}개")
