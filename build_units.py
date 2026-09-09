# -*- coding: utf-8 -*-
"""
#1 지번 기반 단지 식별 + 별칭 사전  (API 호출 0)

이름은 바뀌어도 땅(지번)은 안 바뀐다 → 주소에서 뽑은 '지번 키'로 단지를 식별하고,
그 단지에 등장한 모든 이름을 별칭(alias)으로 축적한다.

입력: data_cheongyak.json, data_chakgong.json
출력: units.json  (단지 마스터: 키, 대표명, 별칭[], 세대, 입주월, 출처[])
"""
import os, re, io, sys, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

# "신정동 1136-3번지", "1266-6번지 일원", "638-1번지 외 21필지"
RE_JIBUN = re.compile(r"([가-힣0-9]+[동읍면리])\s*(\d+)(?:-(\d+))?\s*번지")
# 도로명주소의 괄호 법정동: "(신정동, 건물명)"
RE_PAREN_DONG = re.compile(r"\(([가-힣0-9]+[동읍면리])[,)]")


def norm_id(s):
    """식별용: 괄호(모집구분 등)만 제거, 단지·블록 번호는 살린다 (1단지≠2단지)."""
    s = re.sub(r"\([^)]*\)", "", s or "")
    return re.sub(r"[^\w가-힣]", "", s).lower()


def norm_search(s):
    """검색·별칭 매칭용: 단지/차/블록 번호까지 지워 느슨하게."""
    s = re.sub(r"\([^)]*\)", "", s or "")
    s = re.sub(r"\d+\s*(단지|차|BL|블록|공구|BLK)", "", s)
    return re.sub(r"[^\w가-힣]", "", s).lower()


RE_BLOCK = re.compile(r"([A-Za-z]{0,2})[-\s]?(\d{1,2})\s*(?:블록|블럭|BL|BLK)", re.I)


def block_of(name, addr):
    """단지명/주소에서 블록코드 추출(예: 'A-3블록'→'A3'). 사전청약↔본청약 등 지번없는 단지 매칭용."""
    m = RE_BLOCK.search((name or "") + " " + (addr or ""))
    return (m.group(1).upper() + m.group(2)) if m else ""


def parcel_key(addr, name):
    """지번>블록>이름 순으로 단지 식별키. 지번없는 사전/본청약은 (법정동+블록)으로 묶임."""
    if not addr:
        return None
    toks = addr.split()
    sido = toks[0] if toks else ""
    sgg = toks[1] if len(toks) > 1 else ""
    m = RE_JIBUN.search(addr)
    if m:
        dong, bun, ji = m.group(1), m.group(2), (m.group(3) or "0")
        return f"{sido}|{sgg}|{dong}|{int(bun)}-{int(ji)}"
    p = RE_PAREN_DONG.search(addr)
    dong = p.group(1) if p else ""
    if not dong:
        for t in toks:
            if t.endswith(("동", "읍", "면", "리")):
                dong = t
                break
    if not dong:
        return None
    blk = block_of(name, addr)
    if blk:
        return f"{sido}|{sgg}|{dong}|blk:{blk}"
    return f"{sido}|{sgg}|{dong}|~{norm_id(name)}"


def load(fn):
    try:
        return json.load(open(HERE + "/" + fn, encoding="utf-8")).get("records", [])
    except Exception:
        return []


def main():
    ch, cg = load("data_cheongyak.json"), load("data_chakgong.json")
    for r in ch:
        r.setdefault("confidence", "확정(입주예정월)")

    # 이전 units.json의 총세대 보정(match_tothh 결과)을 주소 기준으로 보존 — 재수집 방지
    prev_hub = {}
    try:
        for u in json.load(open(HERE + "/units.json", encoding="utf-8"))["units"]:
            if u.get("hub_hh", 0) > 0 and u.get("addr"):
                prev_hub[u["addr"]] = max(prev_hub.get(u["addr"], 0), u["hub_hh"])
    except Exception:
        pass

    groups = defaultdict(list)
    nokey = 0
    for r in ch + cg:
        k = parcel_key(r.get("addr"), r.get("name"))
        if not k:
            nokey += 1
            k = "NOKEY|" + r["id"]
        groups[k].append(r)

    units = []
    for k, rs in groups.items():
        names = []
        for r in rs:
            n = (r.get("name") or "").strip()
            if n and n not in names:
                names.append(n)
        # 최신 공고 우선(본청약 > 사전청약): 입주예정월·대표명은 가장 최근 공고 기준
        ch_rs = [r for r in rs if r.get("source") == "청약홈"]
        ch_sorted = sorted(ch_rs, key=lambda r: (r.get("pblanc_de") or "", r["ipju_ym"]))
        base = ch_sorted[-1] if ch_sorted else sorted(rs, key=lambda r: r["ipju_ym"])[0]
        display = base["name"]
        # 세대 분해: 청약홈=일반분양분, 건축HUB=단지 전체(총세대)
        cg_rs = [r for r in rs if r.get("source") == "건축HUB"]
        hub_hh = max([r["total_hh"] for r in cg_rs], default=0)      # 총세대(단지 전체)
        # 이전 총세대 보정값 보존(이 단지의 어느 공고 주소든 매칭되면 채택)
        for r in rs:
            hub_hh = max(hub_hh, prev_hub.get(r.get("addr", ""), 0))
        ch_hh = max([r["total_hh"] for r in ch_rs], default=0)       # 일반분양 세대
        hh = hub_hh or ch_hh
        units.append({
            "key": k,
            "name": display,
            "aliases": names,
            "region": base.get("region", ""),
            "addr": base.get("addr", ""),
            "total_hh": hh,
            "hub_hh": hub_hh,     # 건축HUB 총세대(단지 전체)
            "ch_hh": ch_hh,       # 청약홈 일반분양 세대
            "ipju_ym": base["ipju_ym"],
            "sacheom_ym": base["sacheom_ym"],
            "house_type": base.get("house_type", ""),
            "supply_type": base.get("supply_type", ""),
            "is_public_rent": base.get("is_public_rent", False),
            "confidence": base.get("confidence", ""),
            "sources": sorted({r.get("source", "") for r in rs}),
            "n_records": len(rs),
        })

    units.sort(key=lambda u: u["ipju_ym"])
    json.dump({"count": len(units), "units": units}, open(HERE + "/units.json", "w", encoding="utf-8"), ensure_ascii=False)

    merged = sum(u["n_records"] - 1 for u in units)
    multi = [u for u in units if len(u["aliases"]) > 1]
    both = [u for u in units if len(u["sources"]) > 1]
    print(f"입력 {len(ch)+len(cg)}건 → 단지 {len(units)}개 (통합 {merged}건, 주소없음 {nokey})", flush=True)
    print(f"별칭 2개+ 보유 단지: {len(multi)} / 청약홈+착공 양쪽에 잡힌 단지: {len(both)}", flush=True)
    print("\n[별칭 예시]", flush=True)
    for u in multi[:6]:
        print(f"  {u['key']}\n    → {u['aliases']}", flush=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
