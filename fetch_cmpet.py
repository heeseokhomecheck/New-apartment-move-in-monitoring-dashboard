# -*- coding: utf-8 -*-
"""
청약홈 경쟁률 API(36148) → 관리번호별 완판/미분양 판정 → cmpet_cache.json.
청약홈 id('관리번호-공고번호')에서 관리번호를 뽑아 조인. 병렬(워커6)·캐시·멱등.
판정: 총신청 ≥ 총공급 → 완판 / 미달 → 미분양의심 / 공급0 → 데이터없음.
"""
import os, io, sys, json, time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(HERE + "/_rebkey.txt").read().strip()
URL = "https://api.odcloud.kr/api/ApplyhomeInfoCmpetRtSvc/v1/getAPTLttotPblancCmpet"
WORKERS = 6
CACHE = HERE + "/cmpet_cache.json"


def fetch_one(mgmt):
    for attempt in range(3):
        try:
            r = requests.get(URL, params={"page": 1, "perPage": 200,
                             "cond[HOUSE_MANAGE_NO::EQ]": mgmt, "serviceKey": KEY}, timeout=25)
            rows = r.json().get("data", [])
            break
        except Exception:
            if attempt == 2:
                return mgmt, None
            time.sleep(2 * (attempt + 1))
    sup = {}
    req = 0
    rates = []
    for x in rows:
        ty = x.get("HOUSE_TY")
        try:
            sup[ty] = max(sup.get(ty, 0), int(x.get("SUPLY_HSHLDCO") or 0))
        except Exception:
            pass
        try:
            req += int(x.get("REQ_CNT") or 0)
        except Exception:
            pass
        cr = x.get("CMPET_RATE")
        if cr and cr not in ("-", "0"):
            try:
                rates.append(float(cr))
            except Exception:
                pass
    totsup = sum(sup.values())
    if totsup == 0:
        verdict = "데이터없음"
    elif req >= totsup:
        verdict = "완판"
    elif req >= totsup * 0.5:
        verdict = "경합"          # 절반이상 찼지만 미달
    else:
        verdict = "미분양의심"
    return mgmt, {"supply": totsup, "req": req,
                  "max_rate": round(max(rates), 1) if rates else 0,
                  "ratio": round(req / totsup, 2) if totsup else 0,
                  "verdict": verdict}


def main():
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    ch = json.load(open(HERE + "/data_cheongyak.json", encoding="utf-8"))["records"]
    mgmts = set()
    for r in ch:
        if (r.get("ipju_ym") or "") >= "2026-01":
            mn = (r.get("id") or "").split("-")[0]
            if mn:
                mgmts.add(mn)
    todo = [m for m in mgmts if m not in cache]
    print(f"관리번호 {len(mgmts)}개 (캐시 {len(mgmts)-len(todo)} / 신규 {len(todo)})", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_one, m): m for m in todo}
        for f in as_completed(futs):
            m, res = f.result()
            if res is not None:
                cache[m] = res
            done += 1
            if done % 50 == 0:
                json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
                print(f"  {done}/{len(todo)}", flush=True)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    from collections import Counter
    vc = Counter(v["verdict"] for v in cache.values())
    print(f"완료: 캐시 {len(cache)}개 | 판정분포 {dict(vc)}", flush=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
