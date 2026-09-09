# -*- coding: utf-8 -*-
"""
입주물량 수집기 (1차: 청약홈 분양정보 기반)

청약홈 OpenAPI(공공데이터포털, odcloud.kr)에서
  - 아파트 / 민간사전청약 / 신혼희망타운  (getAPTLttotPblancDetail)
  - 오피스텔 / 도시형생활주택 / 생활숙박시설 / 민간임대  (getUrbtyOfctlLttotPblancDetail)
공고를 긁어와 '입주예정월 · 총세대 · 주택유형 · 분양유형 · 임대구분'을 뽑고,
예상 사전점검월(= 입주예정월 - GAP개월)을 계산해 data.js / data.json 으로 저장한다.

준비:
  - 같은 폴더의 _apikey.txt 에 data.go.kr 서비스키를 한 줄로 저장 (또는 환경변수 DATA_GO_KR_KEY)

실행:
  python fetch_ipju.py
"""
import sys, os, io, json, urllib.parse, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1"
GAP_MONTHS = 2  # 예상 사전점검월 = 입주예정월 - GAP (통상 사전점검은 입주 1~2개월 전). 화면에서 개별 수정 가능.

# 공고 단위 상세 엔드포인트 (둘 다 MVN_PREARNGE_YM · TOT_SUPLY_HSHLDCO 제공 확인됨)
ENDPOINTS = [
    {"ep": "getAPTLttotPblancDetail",        "kind": "APT"},   # 아파트류
    {"ep": "getUrbtyOfctlLttotPblancDetail",  "kind": "OFF"},   # 오피스텔/도시형/생숙/민간임대
]


def get_key():
    p = os.path.join(HERE, "_apikey.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    return os.environ.get("DATA_GO_KR_KEY", "")


def call(ep, page, per=300):
    key = get_key()
    if not key:
        sys.exit("서비스키가 없습니다. _apikey.txt 또는 환경변수 DATA_GO_KR_KEY 를 설정하세요.")
    q = {"page": page, "perPage": per, "serviceKey": key}
    url = f"{BASE}/{ep}?" + urllib.parse.urlencode(q, safe="[]:=")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_all(ep, max_pages=30):
    out = []
    for pg in range(1, max_pages + 1):
        try:
            chunk = call(ep, pg).get("data", [])
        except Exception as e:
            print(f"  ({ep} page{pg} 실패: {e})", file=sys.stderr)
            break
        out += chunk
        if len(chunk) < 300:
            break
    return out


def ym_minus(ym, months):
    """YYYYMM(int) 에서 months 개월 뺀 'YYYY-MM' 반환."""
    y, m = ym // 100, ym % 100
    m -= months
    while m <= 0:
        y -= 1; m += 12
    return f"{y:04d}-{m:02d}"


def house_type_of(rec, kind):
    """가시성용 주택유형 라벨."""
    secd = (rec.get("HOUSE_SECD_NM") or "")   # APT / 민간사전청약 / 신혼희망타운
    dtl = (rec.get("HOUSE_DTL_SECD_NM") or "")  # (APT)민영/국민 · (OFF)오피스텔/도시형생활주택/생활숙박시설
    if kind == "APT":
        if "사전청약" in secd: return "아파트(사전청약)"
        if "신혼희망" in secd: return "아파트(신혼희망)"
        return "아파트"
    # OFF: 상세명이 곧 유형
    return dtl or "기타"


def supply_type_of(rec, kind):
    """분양유형(민간분양/공공분양/임대 등)."""
    dtl = (rec.get("HOUSE_DTL_SECD_NM") or "")
    rent = (rec.get("RENT_SECD_NM") or "")
    if kind == "APT":
        if "불가임대" in rent: return "공공임대류(순수임대)"
        if "가능임대" in rent: return "분양전환임대"
        if dtl == "국민": return "공공분양"
        return "민간분양"
    # 오피스텔·도시형·생숙은 대부분 민간공급
    return "민간공급"


def is_public_rent(rec, kind):
    """순수 임대(주문 안 나옴) = 유효세대에서 제외 대상."""
    rent = (rec.get("RENT_SECD_NM") or "")
    return "불가임대" in rent  # '분양전환 불가임대' = 순수 임대


def region_of(rec):
    return rec.get("SUBSCRPT_AREA_CODE_NM") or ""


def norm_date(s):
    if not s: return None
    s = str(s)
    if len(s) == 8 and s.isdigit(): return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s


def main():
    records = []
    seen = set()
    for cfg in ENDPOINTS:
        rows = fetch_all(cfg["ep"])
        print(f"  [{cfg['kind']}] {cfg['ep']}: {len(rows)}건")
        for rec in rows:
            ym_raw = rec.get("MVN_PREARNGE_YM")
            if not ym_raw or not str(ym_raw).strip().isdigit():
                continue
            ym = int(str(ym_raw).strip())
            if ym < 190001 or ym > 210012:  # 방어적 범위 체크
                continue
            mng = str(rec.get("HOUSE_MANAGE_NO") or "")
            pbno = str(rec.get("PBLANC_NO") or "")
            uid = f"{mng}-{pbno}"
            if uid in seen:
                continue
            seen.add(uid)
            try: hh = int(rec.get("TOT_SUPLY_HSHLDCO") or 0)
            except: hh = 0
            records.append({
                "id": uid,
                "name": rec.get("HOUSE_NM") or "?",
                "region": region_of(rec),
                "addr": rec.get("HSSPLY_ADRES") or "",
                "ipju_ym": f"{ym//100:04d}-{ym%100:02d}",       # 입주예정월
                "sacheom_ym": ym_minus(ym, GAP_MONTHS),          # 예상 사전점검월(기본 -2개월)
                "total_hh": hh,
                "house_type": house_type_of(rec, cfg["kind"]),
                "supply_type": supply_type_of(rec, cfg["kind"]),
                "rent_type": rec.get("RENT_SECD_NM") or "",
                "is_public_rent": is_public_rent(rec, cfg["kind"]),
                "builder": rec.get("CNSTRCT_ENTRPS_NM") or "",
                "pblanc_de": norm_date(rec.get("RCRIT_PBLANC_DE")),
                "url": rec.get("PBLANC_URL") or "",
                "source": "청약홈",
            })

    records.sort(key=lambda r: r["ipju_ym"])
    gen_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {
        "generated_at": gen_at,
        "gap_months": GAP_MONTHS,
        "count": len(records),
        "records": records,
    }
    # 청약홈 원본(data_cheongyak.json) + 대시보드용 data.js(청약홈 단독).
    # 착공까지 합치려면 build_data.py 실행 → data.js 를 통합본으로 갱신.
    with open(os.path.join(HERE, "data_cheongyak.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as f:
        f.write("/* 자동 생성 — fetch_ipju.py. 청약홈 입주물량 */\n")
        f.write("window.IPJU_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")

    # 요약 출력
    future = [r for r in records if r["ipju_ym"] >= gen_at[:7]]
    tot = sum(r["total_hh"] for r in future)
    eff = sum(r["total_hh"] for r in future if not r["is_public_rent"])
    print(f"\n총 {len(records)}개 단지 수집 (입주예정월 보유)")
    print(f"앞으로(이번달~) {len(future)}단지 / 총 {tot:,}세대 / 유효 {eff:,}세대(공공임대 제외)")
    print(f"→ data.js, data.json 생성 완료 (갱신 {gen_at})")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
