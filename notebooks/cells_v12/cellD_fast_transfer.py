# 셀 D. 빠른 환승 (국토교통부_철도역 빠른 환승 정보 CSV 업로드)
import io, json, re
import pandas as pd
from google.colab import files

up = files.upload()   # 다운받은 CSV 선택
raw = next(iter(up.values()))
for enc in ("utf-8-sig", "cp949", "euc-kr"):
    try:
        FT = pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str)
        break
    except Exception:
        continue
print("행", len(FT), "· 열", list(FT.columns))
print("노선명 종류:", sorted(FT["노선명"].dropna().unique())[:60])
print()

# 우리 경로의 환승 (환승역, 타고 온 노선, 갈아탈 노선, 타고 온 노선 진행 방향 다음 역)
XFER = [
    ("R01", "정자", "신분당", "분당", "미금"),
    ("R02", "대곡", "경의", "3", "백석"),
    ("R05", "창동", "4", "1", "방학"),
    ("R06", "강남", "2", "신분당", "역삼"),
    ("R07", "김포공항", "9", "골드", None),
    ("R08", "고속터미널", "7", "3", "반포"),
    ("R08", "수서", "3", "GTX", None),
    ("R09", "서울역", "4", "GTX", "숙대입구"),
    ("R10", "사당", "2", "4", "방배"),
    ("R11", "신림", "신림", "2", None),
    ("R11", "사당", "2", "4", "방배"),
]
def has(cell, kw):
    s = str(cell or "")
    return (kw + "호선") in s if kw.isdigit() else kw in s

FAST = {}
for rid, st, frm, to, nxt in XFER:
    m = FT[(FT["역명"].str.replace("역", "", regex=False) == st)
           & FT["노선명"].apply(lambda x: has(x, frm))
           & FT["환승선"].apply(lambda x: has(x, to))]
    key = f"{rid}:{st}:{frm}>{to}"
    FAST[key] = m.to_dict("records")
    print(f"{key}: {len(m)}행")
    if len(m):
        print(m[["노선명", "역명", "종착역명", "환승선", "환승이후역명", "환승기점역명",
                 "차량순서", "차량출입문번호"]].to_string(index=False))
    print()

json.dump(FAST, open(P("fast_transfer.json"), "w"), ensure_ascii=False)
print("저장: fast_transfer.json")
