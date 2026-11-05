# 셀 D2. 빠른 환승 CSV에 김포골드·GTX·신림선이 다른 이름으로 있는지 확인
for st in ["김포공항", "수서", "서울역", "신림"]:
    m = FT[FT["역명"].str.contains(st, na=False)]
    print(st, "·", len(m), "행")
    if len(m):
        print("   노선명:", sorted(m["노선명"].dropna().unique()))
        print("   환승선:", sorted(m["환승선"].dropna().unique()))
