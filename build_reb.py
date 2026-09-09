# -*- coding: utf-8 -*-
"""
#0 뼈대 재구성 — 한국부동산원 입주예정물량(공식·지자체검증) = 뼈대,  청약홈 = 신규공고 델타.

REB 주소는 '지번', 청약홈 주소는 '도로명+(법정동)'이라 지번키로 직접 안 맞물린다.
그런데 REB 자체가 '입주자모집공고(청약홈)'를 이미 통합·검증한 데이터라서:
  - REB 675단지 = 뼈대(총세대·입주월·임대구분 확정)
  - 청약홈 units 중 REB 기준시점(2025-12) 이후 신규 공고분만 델타로 얹는다(지역+유사명 매칭).

입력: reb_ipju.csv, data_cheongyak.json
출력: units.json  (build_data.py가 렌더)
"""
import os, re, io, sys, csv, json
from collections import defaultdict
from build_units import norm_id, norm_search, block_of, parcel_key

HERE = os.path.dirname(os.path.abspath(__file__))
CUTOFF = "2026-01"   # REB 수록 범위 시작(그 이전 입주는 이미 지남)
SACHEOM_GAP = 1      # 사전점검 예상월 = 입주월 − N개월. 확률모델 peak(1달전 57.98%)

# REB 지번주소: "강릉시 견소동  244-2" / "천곡동  산 6번지" / "주문진읍 주문리 762-5"
RE_REB = re.compile(r"([가-힣0-9]+[동리])\s+(산\s*)?(\d+)(?:-(\d+))?\s*번?지?")


def reb_key(addr):
    """REB 지번주소 → (식별키, 법정동). 산 지번은 키에 'san' 표기해 충돌 방지."""
    toks = (addr or "").split()
    sido = toks[0] if toks else ""
    sgg = toks[1] if len(toks) > 1 else ""
    m = RE_REB.search(addr or "")
    if not m:
        return None, ""
    dong = m.group(1)
    san = "산" if m.group(2) else ""
    bun = int(m.group(3))
    ji = int(m.group(4) or 0)
    return f"{sido}|{sgg}|{dong}|{san}{bun}-{ji}", dong


def ym_minus(ym, n):
    """입주예정월 − n개월 = 사전점검월(임시 고정, 이후 확률모델로 교체)."""
    try:
        y, mo = int(ym[:4]), int(ym[5:7])
    except Exception:
        return ym
    mo -= n
    while mo <= 0:
        mo += 12
        y -= 1
    return f"{y:04d}-{mo:02d}"


def bigrams(s):
    return {s[i:i+2] for i in range(len(s) - 1)}


def name_match(a, b):
    na, nb = norm_search(a), norm_search(b)
    if not na or not nb:
        return False
    if na in nb or nb in na:
        return True
    A, B = bigrams(na), bigrams(nb)
    if not A or not B:
        return False
    return len(A & B) / min(len(A), len(B)) >= 0.62


def load_reb():
    p = HERE + "/reb_ipju.csv"
    rows = list(csv.reader(open(p, encoding="utf-8-sig")))
    data = rows[1:]
    units = []
    for i, r in enumerate(data):
        ym, reg, saup, addr, name, hh = (r + ["", "", "", "", "", ""])[:6]
        ym = (ym or "").strip()
        if ym.endswith("-00") or not ym[:4].isdigit():
            ym = ym[:4] + "-00" if ym[:4].isdigit() else ""      # 미정
        key, dong = reb_key(addr)
        if not key:
            key = f"REB|{i}"
        try:
            total = int(re.sub(r"[^\d]", "", hh) or 0)
        except Exception:
            total = 0
        saup = (saup or "").strip()
        is_rent = (saup == "임대")           # 순수 임대만 잠재 제외(행복/영구/국민)
        units.append({
            "key": key,
            "name": name.strip(),
            "aliases": [name.strip()],
            "region": reg.strip(),
            "addr": addr.strip(),
            "dong": dong,
            "total_hh": total,
            "reb_hh": total,
            "hub_hh": 0,
            "ch_hh": 0,
            "ipju_ym": ym or "0000-00",
            "sacheom_ym": ym_minus(ym, SACHEOM_GAP) if ym and not ym.endswith("-00") else "미정",
            "house_type": "",
            "supply_type": saup,
            "is_public_rent": is_rent,
            "confidence": "확정(부동산원·지자체검증)",
            "sources": ["부동산원"],
            "n_records": 1,
        })
    return units


def load_cheongyak_units():
    """청약홈 records → 지번/이름 기반 units(간이). REB 델타 후보용."""
    try:
        ch = json.load(open(HERE + "/data_cheongyak.json", encoding="utf-8"))["records"]
    except Exception:
        return []
    groups = defaultdict(list)
    for r in ch:
        k = parcel_key(r.get("addr"), r.get("name")) or ("NOKEY|" + r.get("id", ""))
        groups[k].append(r)
    units = []
    for k, rs in groups.items():
        base = sorted(rs, key=lambda r: (r.get("pblanc_de") or "", r.get("ipju_ym", "")))[-1]
        names = []
        for r in rs:
            n = (r.get("name") or "").strip()
            if n and n not in names:
                names.append(n)
        units.append({
            "key": k, "name": base["name"], "aliases": names,
            "region": base.get("region", ""), "addr": base.get("addr", ""),
            "ipju_ym": base.get("ipju_ym", ""),
            "pblanc_de": base.get("pblanc_de", ""),
            "mgmt": (base.get("id") or "").split("-")[0],   # 청약홈 관리번호(경쟁률 조인용)
            "ch_hh": base.get("total_hh", 0),   # 대표공고 세대(최대값 X — 엘로이 오피스텔 혼입 방지)
            "house_type": base.get("house_type", ""),
            "supply_type": base.get("supply_type", ""),
            "is_public_rent": base.get("is_public_rent", False),
        })
    return units


def main():
    reb = load_reb()
    # 지역별 인덱스(델타 매칭 가속)
    by_region = defaultdict(list)
    for u in reb:
        by_region[u["region"]].append(u)

    # 지번 인덱스(REB·청약홈 주소에 지번이 있으면 강력 매칭 — 성동자이=청계리버뷰자이)
    RE_JIB = re.compile(r"([가-힣0-9]+[동리])\s+(?:산\s*)?(\d+)(?:-(\d+))?\s*번?지?")

    def jkey(addr):
        toks = (addr or "").split()
        m = RE_JIB.search(addr or "")
        if not toks or not m:
            return None
        return f"{toks[0]}|{m.group(1)}|{int(m.group(2))}"   # 시도|동|본번

    reb_by_jk = defaultdict(list)
    for u in reb:
        jk = jkey(u["addr"])
        if jk:
            reb_by_jk[jk].append(u)

    ch = load_cheongyak_units()
    ch = [u for u in ch if (u.get("ipju_ym") or "") >= CUTOFF]   # REB 창(2026+)만

    # 재공급 껍데기 제외: 이미 집계된 단지의 재공고(잔여/무순위/보류지/취소분/사전청약)
    DROP_KW = ("잔여세대", "무순위", "보류지", "취소분", "계약취소", "임의공급",
               "추가입주자", "추가모집", "잔여 세대")

    def is_reoffer(u):
        if "사전청약" in (u.get("house_type") or ""):
            return True
        return any(k in (u.get("name") or "") for k in DROP_KW)

    ch = [u for u in ch if not is_reoffer(u)]

    delta = 0
    enriched = 0
    seen_delta = set()
    for cu in ch:
        hit = None
        # 1순위: 지번 일치(가장 강력 — 이름 달라도 같은 땅이면 동일 단지)
        jk = jkey(cu.get("addr"))
        if jk and jk in reb_by_jk:
            cands = reb_by_jk[jk]
            hit = cands[0] if len(cands) == 1 else next(
                (r for r in cands if name_match(cu["name"], r["name"])), cands[0])
        # 2순위: 같은 법정동 + 유사명, 3순위: 지역 내 유사명
        if hit is None:
            cand = by_region.get(cu["region"], [])
            for ru in cand:
                if ru.get("dong") and ru["dong"] in (cu.get("addr") or ""):
                    if name_match(cu["name"], ru["name"]) or any(name_match(a, ru["name"]) for a in cu["aliases"]):
                        hit = ru
                        break
            if hit is None:
                for ru in cand:
                    if name_match(cu["name"], ru["name"]):
                        hit = ru
                        break
        if hit is not None:
            # 별칭 축적 + 청약홈 출처 표기(REB 세대·입주월은 유지: 지자체검증본이 우선)
            for a in cu["aliases"]:
                if a and a not in hit["aliases"]:
                    hit["aliases"].append(a)
            if "청약홈" not in hit["sources"]:
                hit["sources"].append("청약홈")
            hit["house_type"] = hit["house_type"] or cu.get("house_type", "")
            if cu.get("mgmt") and not hit.get("mgmt"):
                hit["mgmt"] = cu["mgmt"]        # 경쟁률 조인용 관리번호
            hit["bunyang_hh"] = cu.get("ch_hh", 0)   # 청약홈 일반분양 세대(임대 제외 타겟)
            # 최신 단지명: 청약홈 공고가 REB 스냅샷(2025-12)보다 최신이면 그 이름을 대표로
            if (cu.get("pblanc_de") or "") > "2025-12-31" and cu.get("name"):
                if hit["name"] not in hit["aliases"]:
                    hit["aliases"].insert(0, hit["name"])
                hit["name"] = cu["name"]
            # 입주월 조정: REB(반기 스냅샷)와 청약홈이 다르면 늦은 쪽 채택(지연 흔함) + 확인표시
            cy = cu.get("ipju_ym") or ""
            if cy and cy[:4].isdigit() and cy != hit["ipju_ym"]:
                later = max(hit["ipju_ym"], cy)
                hit["ipju_alt"] = min(hit["ipju_ym"], cy)   # 다른 소스값(참고표시)
                hit["ipju_ym"] = later
                hit["sacheom_ym"] = ym_minus(later, SACHEOM_GAP)
            enriched += 1
        else:
            # REB에 없는 신규 공고분 → 델타 추가 (지역+정규화이름 중복 제거)
            sig = (cu["region"], norm_search(cu["name"]))
            if sig in seen_delta:
                continue
            seen_delta.add(sig)
            ym = cu.get("ipju_ym") or "0000-00"
            reb.append({
                "key": cu["key"], "name": cu["name"], "aliases": cu["aliases"],
                "region": cu["region"], "addr": cu.get("addr", ""), "dong": "",
                "total_hh": cu.get("ch_hh", 0), "reb_hh": 0, "hub_hh": 0,
                "ch_hh": cu.get("ch_hh", 0), "bunyang_hh": cu.get("ch_hh", 0),
                "ipju_ym": ym, "sacheom_ym": ym_minus(ym, SACHEOM_GAP),
                "house_type": cu.get("house_type", ""),
                "supply_type": cu.get("supply_type", ""),
                "is_public_rent": cu.get("is_public_rent", False),
                "confidence": "신규공고(청약홈)",
                "mgmt": cu.get("mgmt", ""),
                "sources": ["청약홈"], "n_records": 1,
            })
            delta += 1

    for u in reb:
        u.pop("dong", None)
    reb.sort(key=lambda u: u["ipju_ym"])
    json.dump({"count": len(reb), "units": reb},
              open(HERE + "/units.json", "w", encoding="utf-8"), ensure_ascii=False)

    n_rent = sum(1 for u in reb if u["is_public_rent"])
    pot = sum(u["total_hh"] for u in reb if not u["is_public_rent"])
    print(f"REB 뼈대 {sum(1 for u in reb if '부동산원' in u['sources'])} + 청약홈 신규 {delta} = 총 {len(reb)}단지", flush=True)
    print(f"청약홈 별칭보강(매칭) {enriched}건 | 임대제외 {n_rent}단지 | 홈체크 잠재물량 합계 {pot:,}세대", flush=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
