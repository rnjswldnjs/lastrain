# 셀 E. 지하철·버스 구간 + 빠른 환승을 하나로 합쳐 내려받기
import json, os
from google.colab import files

def load(f):
    return json.load(open(P(f))) if os.path.exists(P(f)) else {}

sub, bus, fast = load("seg_subway.json"), load("seg_bus.json"), load("fast_transfer.json")
OUT = {"subway": sub, "bus": bus, "fast_transfer": fast,
       "source": {"subway": "OpenStreetMap (ODbL) 노선 relation",
                  "bus": "서울 버스 노선정보 / 경기 버스노선 / 국토부 TAGO 버스노선정보",
                  "fast_transfer": "국토교통부_철도역 빠른 환승 정보_20250923"}}
json.dump(OUT, open("lastrain_map.json", "w"), ensure_ascii=False)
print(f"지하철 {len(sub)} · 버스 {len(bus)} · 빠른 환승 {len(fast)}")
print("크기", round(os.path.getsize("lastrain_map.json") / 1024), "KB")
files.download("lastrain_map.json")
