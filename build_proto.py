# -*- coding: utf-8 -*-
"""
data.js → prototype.html (Artifact용) + 프로토타입_보기.html (로컬 더블클릭용).
에어비앤비 스타일. 사전점검월 '한 달 단위' 네비게이션 + 미분양/완판 배지 + 분양세대(임대 제외).
"""
import os, io, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    raw = open(HERE + "/data.js", encoding="utf-8").read()
    raw = raw[raw.index("{"):raw.rindex("}") + 1]
    payload = json.loads(raw)
    recs = payload["records"]
    slim = []
    for r in recs:
        al = [a for a in (r.get("aliases") or []) if a != r["name"]][:2]
        slim.append({
            "n": r["name"], "al": al, "rg": r.get("region", ""),
            "ht": r.get("house_type", ""), "lc": r.get("lease_class", ""),
            "th": r.get("total_hh", 0), "bh": r.get("bunyang_hh", 0),
            "ph": r.get("potential_hh", 0), "pt": r.get("potential_type", ""),
            "iy": r.get("ipju_ym", ""), "ia": r.get("ipju_alt", ""), "sy": r.get("sacheom_ym", ""),
            "ss": r.get("sale_status", ""), "cr": r.get("cmpet_ratio", 0),
            "cx": r.get("cmpet_rate", 0), "sc": r.get("source", ""),
        })
    data_json = json.dumps({"gen": payload.get("generated_at", ""), "recs": slim}, ensure_ascii=False)

    html = TEMPLATE.replace("/*__DATA__*/", data_json)
    open(HERE + "/prototype.html", "w", encoding="utf-8").write(html)
    local = ('<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="UTF-8">\n'
             '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
             '<title>홈체크 입주물량·미분양 모니터</title>\n</head>\n<body>\n'
             + html + '\n</body>\n</html>')
    open(HERE + "/프로토타입_보기.html", "w", encoding="utf-8").write(local)
    # GitHub 업로드용 index.html = 표준문서(charset 포함) 최신본
    open(HERE + "/index.html", "w", encoding="utf-8").write(local)
    print(f"prototype.html + 프로토타입_보기.html + index.html 생성: {len(slim)}단지", flush=True)


TEMPLATE = r"""<style>
:root{
  --bg:#fff; --panel:#fff; --panel2:#f4f4f4; --ink:#171a20; --sub:#5c5e62; --faint:#a2a4a8;
  --line:#e3e3e3; --line2:#efefef;
  --rausch:#e82127; --rausch-d:#c8171c; --rausch-soft:#fdeaea;
  --good:#1a7f37; --good-soft:#e7f3ec; --warn:#8a6100; --warn-soft:#f6efda;
  --crit:#e82127; --crit-soft:#fdeaea; --rent:#86888c; --rent-soft:#f0f0f0;
  --shadow:none; --shadow-lg:0 2px 10px rgba(0,0,0,.08); --r:8px;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#000; --panel:#141416; --panel2:#1e1e21; --ink:#fff; --sub:#a2a4a8; --faint:#6a6c70;
  --line:#2a2a2d; --line2:#202023;
  --rausch:#ff4b50; --rausch-d:#e82127; --rausch-soft:#2a1414;
  --good:#35c759; --good-soft:#132a1b; --warn:#e0a53a; --warn-soft:#2a2312;
  --crit:#ff4b50; --crit-soft:#2a1414; --rent:#8e9095; --rent-soft:#1e1e21;
  --shadow:none; --shadow-lg:0 2px 12px rgba(0,0,0,.6); --r:8px;
}}
:root[data-theme="light"]{
  --bg:#fff; --panel:#fff; --panel2:#f4f4f4; --ink:#171a20; --sub:#5c5e62; --faint:#a2a4a8;
  --line:#e3e3e3; --line2:#efefef; --rausch:#e82127; --rausch-d:#c8171c; --rausch-soft:#fdeaea;
  --good:#1a7f37; --good-soft:#e7f3ec; --warn:#8a6100; --warn-soft:#f6efda;
  --crit:#e82127; --crit-soft:#fdeaea; --rent:#86888c; --rent-soft:#f0f0f0;
  --shadow:none; --shadow-lg:0 2px 10px rgba(0,0,0,.08); --r:8px;
}
:root[data-theme="dark"]{
  --bg:#000; --panel:#141416; --panel2:#1e1e21; --ink:#fff; --sub:#a2a4a8; --faint:#6a6c70;
  --line:#2a2a2d; --line2:#202023; --rausch:#ff4b50; --rausch-d:#e82127; --rausch-soft:#2a1414;
  --good:#35c759; --good-soft:#132a1b; --warn:#e0a53a; --warn-soft:#2a2312;
  --crit:#ff4b50; --crit-soft:#2a1414; --rent:#8e9095; --rent-soft:#1e1e21;
  --shadow:none; --shadow-lg:0 2px 12px rgba(0,0,0,.6); --r:8px;
}
*{box-sizing:border-box}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}
.hc{font-family:"Pretendard","Inter",-apple-system,BlinkMacSystemFont,"Helvetica Neue","Malgun Gothic","맑은 고딕",sans-serif;
  background:var(--bg);color:var(--ink);font-size:14px;line-height:1.5;
  -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.hc .wrap{max-width:1120px;margin:0 auto;padding:30px 22px 90px}
.hc h1{font-size:28px;font-weight:600;letter-spacing:-.4px;margin:0;text-wrap:balance}
.hc .lead{color:var(--sub);font-size:13px;margin:8px 0 0;max-width:78ch}
.hc .lead b{color:var(--ink);font-weight:600}
.hc .updated{color:var(--faint);font-size:11.5px;margin-top:6px;text-transform:uppercase;letter-spacing:.06em}

/* 월 네비게이션 */
.hc .monthnav{display:flex;align-items:center;justify-content:center;gap:14px;margin:24px 0 18px}
.hc .navbtn{width:44px;height:44px;border-radius:50%;border:1px solid var(--line);background:var(--panel);
  color:var(--ink);font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;
  box-shadow:var(--shadow);transition:transform .12s,box-shadow .15s}
.hc .navbtn:hover:not(:disabled){box-shadow:var(--shadow-lg);transform:scale(1.05)}
.hc .navbtn:disabled{opacity:.3;cursor:default}
.hc .monthbox{min-width:280px;text-align:center}
.hc .monthbox .mo{font-size:22px;font-weight:600;letter-spacing:-.3px}
.hc .monthbox .mo small{display:block;font-size:12px;font-weight:600;color:var(--sub);letter-spacing:0;margin-top:2px}
.hc .monthsel{position:relative}
.hc .monthsel select{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%}

/* 요약 */
.hc .cards{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px}
.hc .card{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:18px 18px}
.hc .card .k{color:var(--sub);font-size:10.5px;font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:6px;
  text-transform:uppercase;letter-spacing:.07em}
.hc .card .v{font-size:30px;font-weight:600;letter-spacing:-1px;line-height:1}
.hc .card .v small{font-size:12px;font-weight:500;color:var(--sub);margin-left:4px;letter-spacing:0}
.hc .card.hero{background:var(--rausch);border-color:var(--rausch);color:#fff}
.hc .card.hero .k{color:#ffd7d8}.hc .card.hero .v small{color:#ffd7d8}
.hc .dot{width:8px;height:8px;border-radius:50%}.hc .dot.crit{background:var(--crit)}.hc .dot.good{background:var(--good)}

/* 필터 */
.hc .bar{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-bottom:16px}
.hc .chips{display:inline-flex;gap:7px}
.hc .chip{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;
  padding:8px 15px;font-size:13px;font-weight:600;cursor:pointer;transition:border-color .12s,box-shadow .12s}
.hc .chip:hover{border-color:var(--ink)}
.hc .chip.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.hc .chip.on.crit{background:var(--crit);border-color:var(--crit);color:#fff}
.hc .chip.on.good{background:var(--good);border-color:var(--good);color:#fff}
.hc select.sel,.hc input[type=search]{border:1px solid var(--line);border-radius:999px;padding:9px 15px;font-size:13px;
  background:var(--panel);color:var(--ink);font-family:inherit;outline:none}
.hc input[type=search]{flex:1;min-width:190px}
.hc input[type=search]:focus,.hc select.sel:focus{border-color:var(--ink);box-shadow:0 0 0 2px var(--line)}
.hc .chk{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:600;color:var(--sub);cursor:pointer;user-select:none;
  border:1px solid var(--line);border-radius:999px;padding:8px 14px}
.hc .chk input{accent-color:var(--rausch);width:15px;height:15px}
.hc .divider{width:1px;height:22px;background:var(--line);margin:0 3px}

/* 리스트(카드형 행) */
.hc .panel{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow);overflow:hidden}
.hc .thead{display:grid;grid-template-columns:2.5fr 1fr .8fr 1fr 1.3fr 1.2fr;gap:10px;padding:12px 20px;
  border-bottom:1px solid var(--line);font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);font-weight:700}
.hc .row{display:grid;grid-template-columns:2.5fr 1fr .8fr 1fr 1.3fr 1.2fr;gap:10px;padding:15px 20px;
  border-bottom:1px solid var(--line2);align-items:center;transition:background .1s}
.hc .row:last-child{border-bottom:none}
.hc .row:hover{background:var(--panel2)}
.hc .row.crit{box-shadow:inset 3px 0 0 var(--crit)}
.hc .nm{font-weight:600;font-size:15px;letter-spacing:-.2px}
.hc .al{color:var(--faint);font-size:12px;margin-top:3px}
.hc .num{text-align:right;font-variant-numeric:tabular-nums}
.hc .pot{font-weight:700;color:var(--ink);font-size:16px}
.hc .pot small{color:var(--faint);font-weight:500;font-size:10px;display:block;margin-top:1px;text-transform:uppercase;letter-spacing:.04em}
.hc .thin{color:var(--sub)}
.hc .warn-ico{color:var(--warn);font-size:11px;margin-left:4px;cursor:help}
.hc .tag{display:inline-block;padding:3px 9px;border-radius:8px;font-size:11.5px;font-weight:700;background:var(--panel2);color:var(--sub)}
.hc .tag.rent{background:var(--rent-soft);color:var(--rent)}
.hc .pill{display:inline-flex;align-items:center;gap:5px;padding:5px 11px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}
.hc .pill.good{background:var(--good-soft);color:var(--good)}
.hc .pill.warn{background:var(--warn-soft);color:var(--warn)}
.hc .pill.crit{background:var(--crit-soft);color:var(--crit)}
.hc .pill.mut{background:var(--panel2);color:var(--faint)}
.hc .rate{font-size:11px;color:var(--faint);margin-left:6px}
.hc .empty{padding:56px 20px;text-align:center;color:var(--faint);font-size:15px}
.hc .foot{margin-top:20px;color:var(--faint);font-size:12px;line-height:1.7}
.hc .foot b{color:var(--sub)}
@media (max-width:820px){
  .hc .cards{grid-template-columns:repeat(2,1fr)}
  .hc .thead{display:none}
  .hc .row{grid-template-columns:1fr auto;gap:6px 10px;row-gap:4px}
  .hc .row>.hide-sm{display:none}
  .hc .r-status{grid-column:2;grid-row:1}
  .hc .r-pot{grid-column:2;text-align:right}
}
</style>
<div class="hc">
<h2 class="sr-only">사전점검월 한 달 단위로 신축 분양물량·미분양 상태를 보는 영업 대시보드</h2>
<div class="wrap">
  <h1>신축 입주물량 · 미분양 모니터</h1>
  <p class="lead">출처 <b>한국부동산원 입주예정물량</b>(착공·입주자모집공고·정비사업·R114 통합, <b>전국 지자체 검증</b>) + <b>청약홈</b> 신규공고·경쟁률. 잠재물량 = <b>총세대 − 공공임대</b>(일반분양·조합·민간임대·토지임대부 포함, 행복주택·공공임대·청년 제외). 예상 사전점검월 = 입주월 <b>−1개월</b>(확률모델 최빈값 58%).</p>
  <div class="updated" id="updated"></div>

  <div class="monthnav">
    <button class="navbtn" id="prevM" aria-label="이전 달">‹</button>
    <div class="monthbox monthsel">
      <div class="mo" id="moLabel">—<small id="moSub"></small></div>
      <select id="monthSel" aria-label="사전점검월 선택"></select>
    </div>
    <button class="navbtn" id="nextM" aria-label="다음 달">›</button>
  </div>

  <div class="cards" id="cards"></div>

  <div class="bar">
    <div class="chips" id="kindChips">
      <button class="chip on" data-k="분양">분양</button>
      <button class="chip" data-k="임대">임대</button>
      <button class="chip" data-k="">분양+임대</button>
    </div>
    <span class="divider"></span>
    <div class="chips" id="statusChips">
      <button class="chip on" data-s="">전체</button>
      <button class="chip crit" data-s="미분양의심">미분양</button>
      <button class="chip good" data-s="완판">완판</button>
    </div>
    <select class="sel" id="regionSel"><option value="">전지역</option></select>
    <select class="sel" id="sortSel">
      <option value="pot">물량순</option>
      <option value="region">지역순</option>
    </select>
    <input type="search" id="q" placeholder="단지명·별칭 검색">
  </div>

  <div class="panel" id="panel"></div>
  <div class="foot" id="foot"></div>
</div>
</div>
<script>
const PAYLOAD = /*__DATA__*/;
const RECS = PAYLOAD.recs;
const fmt = n => (n||0).toLocaleString();
const esc = s => (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const fmtMon = k => { if(k==='미정')return '입주월 미정'; const[y,m]=k.split('-'); return y+'년 '+(+m)+'월'; };
document.getElementById('updated').textContent = '갱신 ' + (PAYLOAD.gen||'') + ' · 전국 ' + fmt(RECS.length) + '개 단지';

const state = {status:'', region:'', q:'', kind:'분양', sort:'pot', mi:0};

// 지역 표시 순서(대표님 지정)
const REGION_ORDER=['서울','경기','부산','대구','인천','대전','울산','세종','전남','광주',
                    '강원','충북','충남','전북','경북','경남','제주'];
const rIdx = rg => { const i=REGION_ORDER.indexOf(rg); return i<0?99:i; };

// 지역 옵션(지정 순서대로)
const REGIONS=[...new Set(RECS.map(r=>r.rg).filter(Boolean))].sort((a,b)=>rIdx(a)-rIdx(b)||a.localeCompare(b));
REGIONS.forEach(rg=>{
  const o=document.createElement('option');o.value=rg;o.textContent=rg;regionSel.appendChild(o);
});

// 사전점검월 목록(대상 기준, 정렬). 미정은 맨 뒤.
const MONTHS = (()=>{
  const s=new Set(RECS.map(r=>r.sy));
  const a=[...s].filter(x=>x!=='미정').sort();
  if(s.has('미정')) a.push('미정');
  return a;
})();
// 기본 선택 = 당월(2026-07) 이상 첫 달
state.mi = Math.max(0, MONTHS.findIndex(m=>m>='2026-07'));
if(state.mi<0) state.mi=0;

const norm = s => (s||'').replace(/\s|[()]/g,'').toLowerCase();
function passFilter(r){
  const isRent = r.lc==='공공임대제외';
  if(state.kind==='분양' && isRent) return false;      // 분양만
  if(state.kind==='임대' && !isRent) return false;      // 임대만
  if(state.status && r.ss!==state.status) return false;
  if(state.region && r.rg!==state.region) return false;
  if(state.q){ const q=norm(state.q); if(!(norm(r.n)+' '+r.al.map(norm).join(' ')).includes(q)) return false; }
  return true;
}
function pill(ss){
  if(ss==='완판') return '<span class="pill good">✓ 완판</span>';
  if(ss==='미분양의심') return '<span class="pill crit">● 미분양의심</span>';
  if(ss==='경합') return '<span class="pill warn">경합</span>';
  return '<span class="pill mut">—</span>';
}
function typeTag(r){
  const M={'공공임대제외':['공공임대','rent'],'민간임대':['민간임대',''],'토지임대부':['토지임대부',''],
           '조합':['조합',''],'공공분양':['공공분양',''],'분양전환':['분양전환','']};
  if(M[r.lc]){const[t,c]=M[r.lc];return '<span class="tag '+c+'">'+t+'</span>';}
  const ht=(r.ht||'').replace('아파트','').trim();
  return '<span class="tag">'+(ht||'분양')+'</span>';
}

function buildMonthSelect(){
  monthSel.innerHTML='';
  MONTHS.forEach((m,i)=>{
    const cnt=RECS.filter(r=>r.sy===m && r.lc!=='공공임대제외').length;
    const o=document.createElement('option');o.value=i;o.textContent=fmtMon(m)+' · '+cnt+'단지';
    monthSel.appendChild(o);
  });
}

function render(){
  const mon = MONTHS[state.mi];
  moLabel.childNodes[0].nodeValue = fmtMon(mon)+' ';
  moSub.textContent = '사전점검 예정 (입주 '+ (mon==='미정'?'미정': (()=>{let[y,m]=mon.split('-').map(Number);m+=1;if(m>12){m-=12;y++;}return y+'년 '+m+'월';})()) +')';
  monthSel.value = state.mi;
  prevM.disabled = state.mi<=0;
  nextM.disabled = state.mi>=MONTHS.length-1;

  const inMonth = RECS.filter(r=>r.sy===mon);
  const volOf = r => r.lc==='공공임대제외' ? r.th : r.ph;   // 임대는 세대수, 분양은 잠재물량
  const rows = inMonth.filter(passFilter).sort((a,b)=>
    state.sort==='region' ? (rIdx(a.rg)-rIdx(b.rg) || volOf(b)-volOf(a)) : (volOf(b)-volOf(a)));
  // '분양'만 볼 때 숨겨진 임대 세대(참고 표시)
  let rentTot=0;
  if(state.kind==='분양') inMonth.forEach(r=>{ if(r.lc==='공공임대제외' && (!state.region||r.rg===state.region)) rentTot+=r.th; });

  const isRentView = state.kind==='임대';
  const vol = rows.reduce((a,r)=>a+volOf(r),0);
  const mis = rows.filter(r=>r.ss==='미분양의심');
  const sold= rows.filter(r=>r.ss==='완판');
  // 이달 예정 입주 총물량 = 분양 + 임대 = 그 달 전체 입주세대(지역필터만 반영)
  const totalIpju=inMonth.filter(r=>!state.region||r.rg===state.region).reduce((a,r)=>a+(r.th||0),0);
  cards.innerHTML=`
    <div class="card hero"><div class="k">${isRentView?'이달 임대 세대':'🎯 이달 홈체크 잠재물량'}</div><div class="v">${fmt(vol)}<small>세대</small></div></div>
    <div class="card"><div class="k">${isRentView?'임대 단지':'사전점검 대상 단지'}</div><div class="v">${fmt(rows.length)}<small>단지</small></div></div>
    <div class="card"><div class="k"><span class="dot crit"></span>미분양의심</div><div class="v">${fmt(mis.length)}<small>단지</small></div></div>
    <div class="card"><div class="k"><span class="dot good"></span>완판</div><div class="v">${fmt(sold.length)}<small>단지</small></div></div>
    <div class="card"><div class="k">이달 예정 입주 총물량</div><div class="v">${fmt(totalIpju)}<small>세대</small></div></div>`;

  if(!rows.length){ panel.innerHTML='<div class="empty">이 달에 조건에 맞는 단지가 없습니다.</div>'; }
  else{
    const head='<div class="thead"><span>단지명 / 별칭</span><span>지역</span><span>유형</span><span class="num">총세대</span><span class="num">'+(isRentView?'임대세대':'🎯 잠재물량')+'</span><span>판매상태</span></div>';
    const body=rows.map(r=>{
      const cls=r.ss==='미분양의심'?'crit':'';
      const rate=r.ss==='완판'&&r.cx?'<span class="rate">'+r.cx+':1</span>':'';
      const al=r.al.length?'<div class="al">'+esc(r.al.join(' · '))+'</div>':'';
      const iw=r.ia?'<span class="warn-ico" title="출처별 입주월 상이(늦은쪽 표기). 다른값 '+esc(r.ia)+'">⚠</span>':'';
      const approx=r.pt==='공급규모'?'<small>공급규모</small>':'';
      return `<div class="row ${cls}">
        <div><div class="nm">${esc(r.n)}${iw}</div>${al}</div>
        <div class="thin hide-sm">${esc(r.rg)}</div>
        <div class="hide-sm">${typeTag(r)}</div>
        <div class="num thin hide-sm">${fmt(r.th)}</div>
        <div class="num r-pot"><span class="pot">${volOf(r)?fmt(volOf(r)):'—'}</span>${approx}</div>
        <div class="r-status">${pill(r.ss)}${rate}</div>
      </div>`;
    }).join('');
    panel.innerHTML=head+body;
  }
  foot.innerHTML=`이 달 표시 <b>${fmt(rows.length)}</b>단지${rentTot?` · 공공임대 <b>${fmt(rentTot)}</b>세대 별도(<b>임대</b> 탭에서 보기)`:''}.<br>`+
    `잠재물량 = <b>총세대 − 공공임대</b>. 일반분양·조합·민간임대·토지임대부 <b>전부 포함</b>, 행복주택·영구·국민·공공임대·청년만 제외. `+
    `배지: <b>완판</b>=신청≥공급 · <b>경합</b>=50%↑ · <b>미분양의심</b>=50%미만 · <b>—</b>=경쟁률없음. <b>⚠</b>=출처별 입주월 상이(늦은쪽·확인요).`;
}

function move(d){ const n=state.mi+d; if(n>=0&&n<MONTHS.length){state.mi=n;render();} }
prevM.onclick=()=>move(-1);
nextM.onclick=()=>move(1);
monthSel.onchange=e=>{state.mi=+e.target.value;render();};
statusChips.onclick=e=>{const b=e.target.closest('.chip');if(!b)return;state.status=b.dataset.s;
  [...statusChips.children].forEach(x=>x.classList.toggle('on',x===b));render();};
kindChips.onclick=e=>{const b=e.target.closest('.chip');if(!b)return;state.kind=b.dataset.k;
  [...kindChips.children].forEach(x=>x.classList.toggle('on',x===b));render();};
regionSel.onchange=e=>{state.region=e.target.value;render();};
sortSel.onchange=e=>{state.sort=e.target.value;render();};
q.oninput=e=>{state.q=e.target.value;render();};

buildMonthSelect();
render();
</script>
"""


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
