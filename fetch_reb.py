# -*- coding: utf-8 -*-
"""
한국부동산원 입주예정물량 API(15111714) → reb_ipju.csv 자동 갱신.
CSV 수동 다운로드를 대체. 반기 갱신 데이터라 호출 1회로 675행 전부 수신.
키: _rebkey.txt (계정 B = 건축HUB와 동일). API: api.odcloud.kr/api/15111714/v1/uddi:...
"""
import os, io, sys, csv, json, requests

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(HERE + "/_rebkey.txt").read().strip()
URL = "https://api.odcloud.kr/api/15111714/v1/uddi:0b257760-ac19-4841-adb4-b38b4d153397"
COLS = ["입주예정월", "지역", "사업유형", "주소", "아파트명", "세대수"]


def main():
    r = requests.get(URL, params={"page": 1, "perPage": 2000, "serviceKey": KEY}, timeout=30)
    r.raise_for_status()
    j = r.json()
    data = j.get("data", [])
    if not data:
        sys.exit("입주예정물량 API 응답 비어있음")
    with open(HERE + "/reb_ipju.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for d in data:
            w.writerow([d.get(c, "") for c in COLS])
    print(f"입주예정물량 {len(data)}행 → reb_ipju.csv (totalCount={j.get('totalCount')})", flush=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
