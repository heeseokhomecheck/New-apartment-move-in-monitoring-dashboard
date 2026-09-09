# -*- coding: utf-8 -*-
"""
대시보드 데이터 생성 — 공공데이터(청약홈)만. (API 0)
대표님 영업 CSV는 일절 사용하지 않음. units.json(지번 기반 단지 마스터) → 단일파일 index.html.

세대:
  총세대 = 건축HUB totHhldCnt(있으면) / 없으면 청약홈 공급규모(일반분양분)
  일반분양 = 청약홈 공급규모,  조합+임대 = 총세대 − 일반분양(건축HUB 있을 때만)
사전점검월 = 입주예정월 − 2개월(고정). 착공(추정)은 제외.
"""
import os, io, sys, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    p = HERE + "/units.json"
    if not os.path.exists(p):
        sys.exit("units.json 없음 — 먼저 build_units.py 실행")
    units = json.load(open(p, encoding="utf-8"))["units"]

    # 경쟁률→완판/미분양 판정 캐시(관리번호 기준)
    cmpet = {}
    cp = HERE + "/cmpet_cache.json"
    if os.path.exists(cp):
        cmpet = json.load(open(cp, encoding="utf-8"))

    # 수동 보정표(보정.csv): 대표님이 부동산114 등으로 확인한 정확한 잠재세대를 직접 입력.
    #  자동으로 못 가리는 혼합단지(조합 vs 임대)를 사람이 확정. 단지명 부분일치로 적용.
    import csv as _csv, re as _re
    def _nk(s):
        return _re.sub(r"[^\w가-힣]", "", s or "").lower()
    overrides = []   # [(정규화이름, 잠재값)]
    op = HERE + "/보정.csv"
    if os.path.exists(op):
        for row in _csv.DictReader(open(op, encoding="utf-8-sig")):
            nm = (row.get("단지명") or "").strip()
            val = (row.get("잠재물량_직접입력") or "").strip()
            if nm and val.isdigit():
                overrides.append((_nk(nm), int(val)))

    # 확정만: 부동산원(지자체검증) 또는 청약홈(공식 입주예정월) 출처.
    units = [u for u in units if ("부동산원" in u.get("sources", []) or "청약홈" in u.get("sources", []))]
    maxy = datetime.date.today().year + 12
    units = [u for u in units if u["ipju_ym"][:4].isdigit() and int(u["ipju_ym"][:4]) <= maxy]

    # 제외 = 행복주택·공공임대성만. 민간임대·토지임대부·조합·분양은 전부 대상(실입주+매도 가능).
    # '공공임대'는 제외 — 대연 디아이엘(분양 3137, 이름만 '(공공임대)')처럼 혼합행을 통째로
    # 날려버림. REB 사업유형=='임대'가 진짜 공공임대 신호. 이름 KW는 순수 공공임대 유형만.
    PUBLIC_KW = ("행복주택", "영구임대", "국민임대", "통합공공임대", "장기전세",
                 "매입임대", "전세임대", "청년", "든든전세")
    INCLUDE_RENT_KW = ("민간임대", "토지임대", "공공지원민간", "뉴스테이", "기업형임대")
    recs = []
    for u in units:
        reb_hh, hub_hh, ch_hh = u.get("reb_hh", 0), u.get("hub_hh", 0), u.get("ch_hh", 0)
        total = reb_hh or hub_hh or ch_hh
        src = "부동산원 총세대" if reb_hh else ("건축HUB 총세대" if hub_hh else "청약홈 공급규모")
        etc = max(0, hub_hh - ch_hh) if hub_hh else 0
        nm, sup = u["name"], u.get("supply_type", "")
        include_rent = any(k in nm for k in INCLUDE_RENT_KW)         # 임대여도 포함(민간·토지임대부)
        public_rent = (not include_rent) and (sup == "임대" or any(k in nm for k in PUBLIC_KW))
        if public_rent:
            lease = "공공임대제외"       # 행복주택·영구·국민·공공임대·청년 = 사전점검 안 함
        elif "토지임대" in nm:
            lease = "토지임대부"         # 대상(건물 분양·문의·예약 있음)
        elif include_rent:
            lease = "민간임대"           # 대상
        elif "조합" in sup or "조합" in nm:
            lease = "조합"               # 대상(조합원도 실입주)
        elif "분양전환" in sup or "분양전환" in nm:
            lease = "분양전환"
        elif "공공분양" in sup or "공공분양" in nm:
            lease = "공공분양"
        else:
            lease = "분양"
        # 잠재물량 = 총세대(공공임대만 0). 일반분양+조합+민간임대+토지임대부 전부 포함.
        bunyang = u.get("bunyang_hh", 0) or u.get("ch_hh", 0)
        if lease == "공공임대제외":
            potential, ptype = 0, "공공임대"
        else:
            potential, ptype = total, ("총세대" if reb_hh or hub_hh else "공급규모")
        # 수동 보정 적용(단지명 부분일치) — 사람이 확정한 값이 최우선
        _nkn = _nk(u["name"])
        _ov = next((v for k, v in overrides if k and k in _nkn), None)
        if _ov is not None:
            potential, ptype = _ov, "보정"
            if lease == "공공임대제외" and _ov > 0:
                lease = "분양"          # 보정으로 사전점검 대상 편입
        # 경쟁률→완판/미분양(청약홈 관리번호 있는 단지만)
        cm = cmpet.get(u.get("mgmt", "")) or {}
        sale_status = cm.get("verdict", "")
        recs.append({
            "sale_status": sale_status,             # 완판/경합/미분양의심/데이터없음/''
            "cmpet_rate": cm.get("max_rate", 0),
            "cmpet_ratio": cm.get("ratio", 0),
            "bunyang_hh": bunyang,
            "potential_type": ptype,
            "lease_class": lease,
            "potential_hh": potential,
            "id": u["key"],
            "name": u["name"],
            "aliases": u.get("aliases", []),
            "region": u.get("region", ""),
            "addr": u.get("addr", ""),
            "ipju_ym": u["ipju_ym"],
            "ipju_alt": u.get("ipju_alt", ""),      # 소스간 입주월 상이시 다른 값(확인표시)
            "sacheom_ym": u["sacheom_ym"],
            "total_hh": total,
            "total_hh_src": src,
            "sale_hh": ch_hh,
            "etc_hh": etc,
            "house_type": u.get("house_type", ""),
            "supply_type": u.get("supply_type", ""),
            "is_public_rent": lease == "공공임대제외",
            "confidence": u.get("confidence", ""),
            "source": "+".join(u.get("sources", [])),
        })

    gen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    both = sum(1 for u in units if len(u.get("sources", [])) > 1)
    payload = {"generated_at": gen, "count": len(recs),
               "gap_note": "사전점검월 = 입주예정월 − 2개월",
               "sources": {"청약홈 확정": len(recs), "건축HUB 총세대 보정": both},
               "records": recs}

    js = "window.IPJU_DATA = " + json.dumps(payload, ensure_ascii=False) + ";"
    with open(HERE + "/data.js", "w", encoding="utf-8") as f:
        f.write("/* 공공데이터 전용 */\n" + js + "\n")
    tpl = HERE + "/_template.html"
    if os.path.exists(tpl):
        html = open(tpl, encoding="utf-8").read().replace("<!--IPJU_DATA_HERE-->", "<script>" + js + "</script>")
        open(HERE + "/index.html", "w", encoding="utf-8").write(html)
        print(f"index.html(단일파일) 생성: 청약홈 확정 {len(recs)}단지 (건축HUB 총세대 {both})", flush=True)
    else:
        print(f"data.js 생성: {len(recs)}단지 (_template.html 없음)", flush=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
