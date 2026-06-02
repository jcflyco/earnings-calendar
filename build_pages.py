#!/usr/bin/env python3
"""Regenerate index.html (list view) and calendar.html (month view) from
calendar_data.json, embedding the data inline so the pages work over file://.
Both pages are bilingual (zh/en) with a persisted top-right language toggle."""
import json

DATA = json.load(open('calendar_data.json'))
COMPACT = json.dumps(DATA, ensure_ascii=False, separators=(',', ':'))

# ---- shared CSS bits reused by both pages -------------------------------
SHARED_HEAD = '''  :root{
    --bg:#0b0e14; --panel:#141925; --panel2:#1b2230; --line:#262e3d;
    --text:#e6eaf2; --muted:#8a93a6; --accent:#3b82f6;
    --green:#22c55e; --red:#ef4444; --amber:#f59e0b; --hover:#39435a;
  }
  body.light{
    --bg:#f4f6fa; --panel:#ffffff; --panel2:#eef1f7; --line:#e3e8f0;
    --text:#1b212e; --muted:#697384; --accent:#2563eb;
    --green:#16a34a; --red:#dc2626; --amber:#d97706; --hover:#c7cedb;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    background:var(--bg); color:var(--text); line-height:1.5; padding:24px 16px 60px;
    transition:background .2s,color .2s;
  }
  .wrap{max-width:1080px;margin:0 auto}
  header{margin-bottom:22px}
  h1{font-size:24px;font-weight:700;letter-spacing:.3px}
  h1 .em{color:var(--accent)}
  .sub{color:var(--muted);font-size:13px;margin-top:6px}
  .nav{display:flex;gap:8px;margin-top:14px}
  .nav-link{
    text-decoration:none;color:var(--muted);background:var(--panel);
    border:1px solid var(--line);border-radius:10px;padding:8px 16px;
    font-size:13px;font-weight:600;transition:.15s;
  }
  .nav-link:hover{color:var(--text);border-color:var(--hover)}
  .nav-link.on{background:var(--accent);border-color:var(--accent);color:#fff}
  .topbar{position:fixed;top:16px;right:16px;z-index:20;display:flex;gap:8px}
  .lang-btn,.icon-btn{
    background:var(--panel);border:1px solid var(--line);color:var(--text);
    border-radius:20px;font-size:13px;font-weight:700;cursor:pointer;transition:.15s;
  }
  .lang-btn{padding:7px 16px}
  .icon-btn{width:36px;height:34px;border-radius:18px;font-size:15px;line-height:1}
  .lang-btn:hover,.icon-btn:hover{border-color:var(--accent);color:var(--accent)}
'''

# ============================ LIST VIEW (index.html) =====================
LIST_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>财报日历 · Earnings Calendar</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📅</text></svg>">
<style>
__SHARED__
  .controls{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 12px;align-items:center;min-height:40px}
  .search{
    flex:1;min-width:200px;background:var(--panel);border:1px solid var(--line);
    border-radius:10px;padding:10px 14px;color:var(--text);font-size:14px;outline:none;
  }
  .search:focus{border-color:var(--accent)}
  .filters{display:flex;gap:6px;flex-wrap:wrap}
  .chip{
    background:var(--panel);border:1px solid var(--line);color:var(--muted);
    padding:6px 12px;border-radius:18px;font-size:12px;cursor:pointer;
    transition:.15s;user-select:none;
  }
  .chip:hover{color:var(--text)}
  .chip.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
  .stats{color:var(--muted);font-size:12px;margin:4px 2px 16px}
  .day{margin-bottom:22px}
  .day-head{
    display:flex;align-items:baseline;gap:10px;padding:8px 4px;
    border-bottom:1px solid var(--line);margin-bottom:12px;position:sticky;top:0;
    background:var(--bg);z-index:2;
  }
  .day-date{font-size:16px;font-weight:700}
  .day-week{color:var(--muted);font-size:13px}
  .day-count{margin-left:auto;color:var(--muted);font-size:12px}
  .day-count.today{color:var(--accent);font-weight:600}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
  .card{
    background:var(--panel);border:1px solid var(--line);border-radius:12px;
    padding:14px;transition:.15s;position:relative;overflow:hidden;
  }
  .card:hover{border-color:var(--hover);transform:translateY(-1px)}
  .card-top{display:flex;align-items:center;gap:10px;margin-bottom:10px}
  .ico{width:34px;height:34px;border-radius:8px;background:var(--panel2);object-fit:cover;flex-shrink:0}
  .ico-fallback{
    width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;
    font-size:13px;font-weight:700;color:#fff;flex-shrink:0;
  }
  .name-box{min-width:0;flex:1}
  .name{display:block;font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
    color:var(--text);text-decoration:none}
  a.name:hover{color:var(--accent);text-decoration:underline}
  .sym{font-size:12px;color:var(--muted);margin-top:1px}
  .badges{display:flex;gap:5px;flex-shrink:0}
  .badge{font-size:10px;padding:2px 7px;border-radius:6px;font-weight:600;white-space:nowrap}
  .b-mkt{color:#fff}
  .b-star{background:transparent;padding:2px 2px;font-size:11px}
  .imp-chip{font-weight:600}
  .export-btn{
    background:var(--panel);border:1px solid var(--line);color:var(--text);
    border-radius:18px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;transition:.15s;
  }
  .export-btn:hover{border-color:var(--accent);color:var(--accent)}
  .b-when{background:var(--panel2);color:var(--muted)}
  .b-when.pre{color:var(--amber)}
  .b-when.post{color:var(--accent)}
  .content{font-size:12px;color:var(--muted);margin-bottom:10px;min-height:16px}
  .metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .metric{background:var(--panel2);border-radius:8px;padding:8px 10px}
  .m-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  .m-vals{display:flex;align-items:baseline;gap:6px;margin-top:3px}
  .m-est{font-size:12px;color:var(--muted)}
  .m-act{font-size:14px;font-weight:700}
  .m-act.beat{color:var(--green)}
  .m-act.miss{color:var(--red)}
  .live{margin-top:10px;font-size:11px;color:var(--accent);display:flex;align-items:center;gap:5px}
  .live .dot{width:6px;height:6px;border-radius:50%;background:var(--accent);
    box-shadow:0 0 0 0 var(--accent);animation:pulse 1.6s infinite}
  @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(59,130,246,.6)}70%{box-shadow:0 0 0 6px rgba(59,130,246,0)}100%{box-shadow:0 0 0 0 rgba(59,130,246,0)}}
  .empty{text-align:center;color:var(--muted);padding:60px 0;font-size:14px}
  footer{margin-top:40px;text-align:center;color:var(--muted);font-size:11px;line-height:1.7}
  @media(max-width:560px){.grid{grid-template-columns:1fr}h1{font-size:20px}}
</style>
</head>
<body>
<div class="topbar">
  <button class="icon-btn" id="themeBtn" title="theme">🌙</button>
  <button class="lang-btn" id="langBtn">EN</button>
</div>
<div class="wrap">
  <header>
    <h1>📅 <span id="h1main"></span> <span class="tag" id="h1tag" style="font-size:14px;color:var(--muted);font-weight:400"></span></h1>
    <div class="nav"><a class="nav-link" id="navCal" href="index.html"></a><a class="nav-link on" id="navList" href="list.html"></a><a class="nav-link" id="navAbout" href="about.html"></a></div>
  </header>

  <div class="controls">
    <input class="search" id="search" autocomplete="off">
    <div class="filters" id="filters"></div>
    <span class="chip imp-chip" id="impChip"></span>
    <button class="export-btn" id="exportBtn"></button>
  </div>
  <div class="stats" id="stats"></div>

  <div id="list"></div>

  <footer>
    <span id="sub"></span><br>
    <span id="foot"></span><br>
    <span id="gen"></span>
  </footer>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const TODAY = (()=>{const d=new Date(),p=n=>String(n).padStart(2,'0');return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;})();
const GENERATED = "2026-06-02";
const MKT = {US:'#3b82f6',HK:'#ef4444',CN:'#f59e0b',SG:'#10b981',JP:'#8b5cf6'};
const MON_EN = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const WHEN_EN = {'盘前':'Pre-market','盘后':'After-hours'};
__ICS__
const T = {
  zh:{ htmlLang:'zh-CN', title:'财报日历 · Earnings Calendar',
    h1main:'财报<span class="em">日历</span>', tag:'Earnings Calendar',
    navList:'📋 列表视图', navCal:'🗓️ 日历视图', navAbout:'🛠️ 如何制作',
    search:'搜索公司名 / 代码…', all:'全部', today:'今天',
    est:'预期', eps:'EPS', rev:'营收', tba:'待公布', empty:'没有匹配的财报记录 🔍',
    impLabel:'⭐ 重磅', impTip:'预期营收 ≥ 100 亿', exportLabel:'📥 导出日历',
    reportWord:'财报', icsName:'财报日历',
    foot:'数据来源：Longbridge Finance Calendar · 仅供参考，不构成投资建议', langBtn:'EN',
    week:['周日','周一','周二','周三','周四','周五','周六'],
    date:(m,d)=>`${m}月${d}日`,
    count:(n)=>`${n} 家`,
    stats:(c,d)=>`共 ${c} 家公司 · ${d} 个交易日`,
    sub:(s,e,mk,n)=>`${s} ～ ${e} · 覆盖 ${mk} 市场 · 共 ${n} 场财报`,
    gen:(d)=>`生成于 ${d}` },
  en:{ htmlLang:'en', title:'Earnings Calendar · 财报日历',
    h1main:'Earnings <span class="em">Calendar</span>', tag:'财报日历',
    navList:'📋 List', navCal:'🗓️ Calendar', navAbout:'🛠️ How it\\'s made',
    search:'Search name / symbol…', all:'All', today:'Today',
    est:'Est.', eps:'EPS', rev:'Revenue', tba:'TBA', empty:'No matching earnings 🔍',
    impLabel:'⭐ Notable', impTip:'Est. revenue ≥ 10B', exportLabel:'📥 Export .ics',
    reportWord:'Earnings', icsName:'Earnings Calendar',
    foot:'Source: Longbridge Finance Calendar · For reference only, not investment advice', langBtn:'中',
    week:['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
    date:(m,d)=>`${MON_EN[m-1]} ${d}`,
    count:(n)=>`${n}`,
    stats:(c,d)=>`${c} companies · ${d} trading days`,
    sub:(s,e,mk,n)=>`${s} – ${e} · ${mk} · ${n} earnings`,
    gen:(d)=>`Generated on ${d}` },
};
let lang = localStorage.getItem('fc_lang')||'zh';
let activeMkt='ALL', query='', impOnly=false;
const markets=[...new Set(DATA.flatMap(d=>d.infos.map(i=>i.market)))].sort();
const t=()=>T[lang];
const byImp=(a,b)=>(b.imp||0)-(a.imp||0);

function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function nameOf(i){return lang==='en'?(i.name_en||i.name):(i.name||i.name_en);}
function quoteUrl(i){return `https://longbridge.com/${lang==='en'?'en':'zh-CN'}/quote/${encodeURIComponent(i.symbol)}/topics`;}
function fmtDate(s){const[y,m,dd]=s.split('-').map(Number);const dt=new Date(Date.UTC(y,m-1,dd));
  return {label:t().date(m,dd), week:t().week[dt.getUTCDay()]};}
function whenClass(w){if(!w)return'';if(w.includes('盘前'))return'pre';if(w.includes('盘后'))return'post';return'';}
function whenText(w){return lang==='en'?(WHEN_EN[w]||w):w;}
function trVal(v){return (lang==='en'&&v==='待公布')?'TBA':v;}

function metricHtml(label, est, act){
  if(!est && !act) return '';
  let cls='';
  const ne=parseFloat(String(est).replace(/[^0-9.\\-]/g,''));
  const na=parseFloat(String(act).replace(/[^0-9.\\-]/g,''));
  if(act && est && !isNaN(ne)&&!isNaN(na)) cls = na>=ne?'beat':'miss';
  return `<div class="metric">
    <div class="m-label">${label}</div>
    <div class="m-vals">
      ${est?`<span class="m-est">${t().est} ${esc(trVal(est))}</span>`:''}
      ${act?`<span class="m-act ${cls}">${esc(trVal(act))}</span>`:''}
    </div></div>`;
}

function card(i){
  const color = MKT[i.market]||'#8b5cf6';
  const initials = (i.name||'?').slice(0,2).toUpperCase();
  const icoHtml = i.icon
    ? `<img class="ico" src="${esc(i.icon)}" loading="lazy" onerror="this.outerHTML='<div class=\\'ico-fallback\\' style=\\'background:${color}\\'>${initials}</div>'">`
    : `<div class="ico-fallback" style="background:${color}">${initials}</div>`;
  const wc = whenClass(i.when);
  const nm = nameOf(i);
  const content = lang==='en' ? (i.content_en||i.content) : i.content;
  const er = lang==='en' ? (i.est_rev_en||'') : i.est_rev;
  const ar = lang==='en' ? (i.act_rev_en||'') : i.act_rev;
  return `<div class="card">
    <div class="card-top">
      ${icoHtml}
      <div class="name-box">
        <a class="name" href="${quoteUrl(i)}" target="_blank" rel="noopener">${esc(nm)}</a>
        <div class="sym">${esc(i.symbol)}</div>
      </div>
      <div class="badges">
        ${i.imp>=IMP_STAR?`<span class="badge b-star" title="${t().impTip}">⭐</span>`:''}
        <span class="badge b-mkt" style="background:${color}">${i.market}</span>
        ${i.when?`<span class="badge b-when ${wc}">${esc(whenText(i.when))}</span>`:''}
      </div>
    </div>
    ${content?`<div class="content">${esc(content)}</div>`:''}
    <div class="metrics">
      ${metricHtml(t().eps, i.est_eps, i.act_eps)}
      ${metricHtml(t().rev, er, ar)}
    </div>
    ${i.live?`<div class="live"><span class="dot"></span>${esc(i.live)}</div>`:''}
  </div>`;
}

function filterInfos(infos){
  let r = infos;
  if(activeMkt!=='ALL') r = r.filter(i=>i.market===activeMkt);
  if(impOnly) r = r.filter(i=>(i.imp||0)>=IMP_STAR);
  if(query){
    const q=query.toLowerCase();
    r = r.filter(i=>(i.name||'').toLowerCase().includes(q)||(i.name_en||'').toLowerCase().includes(q)||(i.symbol||'').toLowerCase().includes(q));
  }
  return r;
}

function render(){
  const list = document.getElementById('list');
  let total=0, shownDays=0, html='';
  for(const day of DATA){
    const infos = filterInfos(day.infos).slice().sort(byImp);
    if(!infos.length) continue;
    shownDays++; total+=infos.length;
    const {label,week}=fmtDate(day.date);
    const isToday = day.date===TODAY;
    html += `<div class="day">
      <div class="day-head">
        <span class="day-date">${label}</span>
        <span class="day-week">${week}${isToday?' · '+t().today:''}</span>
        <span class="day-count ${isToday?'today':''}">${t().count(infos.length)}</span>
      </div>
      <div class="grid">${infos.map(card).join('')}</div>
    </div>`;
  }
  list.innerHTML = html || `<div class="empty">${t().empty}</div>`;
  document.getElementById('stats').textContent = t().stats(total, shownDays);
}

function exportICS(){
  const events=[];
  for(const day of DATA){
    for(const i of filterInfos(day.infos).slice().sort(byImp)){
      const when=i.when?' · '+whenText(i.when):'';
      const er=lang==='en'?(i.est_rev_en||''):i.est_rev;
      const parts=[];
      if(i.est_eps) parts.push(`${t().eps} ${t().est} ${trVal(i.est_eps)}`);
      if(er) parts.push(`${t().rev} ${t().est} ${trVal(er)}`);
      parts.push(quoteUrl(i));
      events.push({symbol:i.symbol, date:day.date,
        summary:`📅 ${nameOf(i)} (${i.symbol}) ${t().reportWord}${when}`,
        desc:parts.join('\\n'), url:quoteUrl(i)});
    }
  }
  downloadICS(events, t().icsName);
}

function buildFilters(){
  const fbox=document.getElementById('filters');
  fbox.innerHTML=['ALL',...markets].map(m=>`<span class="chip${m===activeMkt?' on':''}" data-m="${m}">${m==='ALL'?t().all:m}</span>`).join('');
}

function applyLang(){
  const x=t();
  document.documentElement.lang=x.htmlLang;
  document.title=x.title;
  document.getElementById('h1main').innerHTML=x.h1main;
  document.getElementById('h1tag').textContent=x.tag;
  document.getElementById('navList').textContent=x.navList;
  document.getElementById('navCal').textContent=x.navCal;
  document.getElementById('navAbout').textContent=x.navAbout;
  document.getElementById('search').placeholder=x.search;
  document.getElementById('foot').textContent=x.foot;
  document.getElementById('langBtn').textContent=x.langBtn;
  document.getElementById('impChip').textContent=x.impLabel;
  document.getElementById('impChip').classList.toggle('on',impOnly);
  document.getElementById('exportBtn').textContent=x.exportLabel;
  const totalAll=DATA.reduce((a,d)=>a+d.infos.length,0);
  document.getElementById('sub').textContent=x.sub(DATA[0].date,DATA[DATA.length-1].date,markets.join(' / '),totalAll);
  document.getElementById('gen').textContent=x.gen(GENERATED);
  buildFilters();
  render();
}

document.getElementById('filters').addEventListener('click',e=>{
  const c=e.target.closest('.chip'); if(!c) return;
  activeMkt=c.dataset.m;
  document.querySelectorAll('#filters .chip').forEach(z=>z.classList.toggle('on',z===c));
  render();
});
document.getElementById('search').addEventListener('input',e=>{query=e.target.value.trim();render();});
document.getElementById('impChip').addEventListener('click',e=>{
  impOnly=!impOnly; e.currentTarget.classList.toggle('on',impOnly); render();
});
document.getElementById('exportBtn').addEventListener('click',exportICS);
document.getElementById('langBtn').addEventListener('click',()=>{
  lang=lang==='zh'?'en':'zh'; localStorage.setItem('fc_lang',lang); applyLang();
});

let theme = localStorage.getItem('fc_theme')||'dark';
function applyTheme(){
  document.body.classList.toggle('light', theme==='light');
  document.getElementById('themeBtn').textContent = theme==='light'?'🌙':'☀️';
}
document.getElementById('themeBtn').addEventListener('click',()=>{
  theme=theme==='dark'?'light':'dark'; localStorage.setItem('fc_theme',theme); applyTheme();
});

applyTheme();
applyLang();
</script>
</body>
</html>'''

# ============================ MONTH VIEW (calendar.html) =================
CAL_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>财报日历 · 日历视图</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📅</text></svg>">
<style>
__SHARED__
  .cal-bar{display:flex;align-items:center;gap:10px;margin:18px 0 12px;flex-wrap:wrap;min-height:40px}
  .month-title{font-size:18px;font-weight:700;min-width:130px}
  .navbtn{
    background:var(--panel);border:1px solid var(--line);color:var(--text);
    width:34px;height:34px;border-radius:9px;cursor:pointer;font-size:16px;
    display:flex;align-items:center;justify-content:center;transition:.15s;
  }
  .navbtn:hover{border-color:var(--accent);color:var(--accent)}
  .navbtn:disabled{opacity:.3;cursor:not-allowed}
  .filters{display:flex;gap:6px;flex-wrap:wrap;margin-left:auto}
  .chip{
    background:var(--panel);border:1px solid var(--line);color:var(--muted);
    padding:6px 12px;border-radius:18px;font-size:12px;cursor:pointer;
    transition:.15s;user-select:none;
  }
  .chip:hover{color:var(--text)}
  .chip.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
  .imp-chip{font-weight:600}
  .export-btn{
    background:var(--panel);border:1px solid var(--line);color:var(--text);
    border-radius:18px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;transition:.15s;
  }
  .export-btn:hover{border-color:var(--accent);color:var(--accent)}
  .weekhead{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:8px}
  .weekhead div{text-align:center;color:var(--muted);font-size:12px;font-weight:600;padding:4px 0}
  .weekhead div.we{color:#6b7488}
  .cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}
  .cell{
    background:var(--panel);border:1px solid var(--line);border-radius:10px;
    min-height:104px;padding:8px;display:flex;flex-direction:column;gap:4px;
    transition:.15s;overflow:hidden;
  }
  .cell.empty{background:transparent;border-color:transparent}
  .cell.has{cursor:pointer}
  .cell.has:hover{border-color:var(--hover);transform:translateY(-1px)}
  .cell.today{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
  .cell-num{font-size:13px;font-weight:700;color:var(--muted)}
  .cell.today .cell-num{color:var(--accent)}
  .cell-num .cnt{float:right;font-size:10px;font-weight:600;color:var(--accent);
    background:rgba(59,130,246,.14);padding:1px 6px;border-radius:8px}
  .ev{font-size:11px;display:flex;align-items:center;gap:5px;white-space:nowrap;overflow:hidden}
  .ev .d{width:6px;height:6px;border-radius:50%;flex-shrink:0}
  .ev .t{overflow:hidden;text-overflow:ellipsis}
  .more{font-size:10px;color:var(--muted);margin-top:auto}
  .legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:16px;color:var(--muted);font-size:12px}
  .legend span{display:flex;align-items:center;gap:6px}
  .legend i{width:9px;height:9px;border-radius:50%;display:inline-block}
  footer{margin-top:40px;text-align:center;color:var(--muted);font-size:11px;line-height:1.7}
  .ov{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:flex-start;
    justify-content:center;padding:40px 16px;z-index:10;overflow:auto}
  .ov.open{display:flex}
  .modal{background:var(--panel);border:1px solid var(--line);border-radius:14px;
    max-width:560px;width:100%;padding:18px}
  .modal-head{display:flex;align-items:baseline;gap:10px;margin-bottom:14px;
    padding-bottom:10px;border-bottom:1px solid var(--line)}
  .modal-date{font-size:17px;font-weight:700}
  .modal-week{color:var(--muted);font-size:13px}
  .modal-close{margin-left:auto;background:none;border:none;color:var(--muted);
    font-size:22px;cursor:pointer;line-height:1}
  .modal-close:hover{color:var(--text)}
  .row{display:flex;align-items:center;gap:10px;padding:9px 4px;border-bottom:1px solid var(--line)}
  .row:last-child{border-bottom:none}
  .ico{width:30px;height:30px;border-radius:7px;object-fit:cover;flex-shrink:0}
  .ico-fb{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;
    justify-content:center;font-size:11px;font-weight:700;color:#fff;flex-shrink:0}
  .row-name{flex:1;min-width:0}
  .row-name .n{display:block;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
    color:var(--text);text-decoration:none}
  a.n:hover{color:var(--accent);text-decoration:underline}
  .row-name .s{font-size:11px;color:var(--muted)}
  .badge{font-size:10px;padding:2px 7px;border-radius:6px;font-weight:600;color:#fff;flex-shrink:0}
  .when{font-size:10px;color:var(--muted);flex-shrink:0}
  @media(max-width:640px){
    .cell{min-height:84px;padding:5px}
    .ev .t{display:none}
    .filters{width:100%;margin-left:0}
  }
</style>
</head>
<body>
<div class="topbar">
  <button class="icon-btn" id="themeBtn" title="theme">🌙</button>
  <button class="lang-btn" id="langBtn">EN</button>
</div>
<div class="wrap">
  <header>
    <h1>📅 <span id="h1main"></span> <span class="tag" id="h1tag" style="font-size:14px;color:var(--muted);font-weight:400"></span></h1>
    <div class="nav"><a class="nav-link on" id="navCal" href="index.html"></a><a class="nav-link" id="navList" href="list.html"></a><a class="nav-link" id="navAbout" href="about.html"></a></div>
  </header>

  <div class="cal-bar">
    <button class="navbtn" id="prev">‹</button>
    <div class="month-title" id="monthTitle"></div>
    <button class="navbtn" id="next">›</button>
    <div class="filters" id="filters"></div>
    <span class="chip imp-chip" id="impChip"></span>
    <button class="export-btn" id="exportBtn"></button>
  </div>

  <div class="weekhead" id="weekhead"></div>
  <div class="cal-grid" id="grid"></div>
  <div class="empty" id="emptyNote" style="text-align:center;color:var(--muted);padding:24px 0;font-size:14px"></div>
  <div class="legend" id="legend"></div>

  <footer>
    <span id="sub"></span><br>
    <span id="foot"></span><br>
    <span id="gen"></span>
  </footer>
</div>

<div class="ov" id="ov"><div class="modal" id="modal"></div></div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const TODAY = (()=>{const d=new Date(),p=n=>String(n).padStart(2,'0');return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;})();
const GENERATED = "2026-06-02";
const MKT = {US:'#3b82f6',HK:'#ef4444',CN:'#f59e0b',SG:'#10b981',JP:'#8b5cf6'};
const MON_EN = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const WHEN_EN = {'盘前':'Pre-market','盘后':'After-hours'};
__ICS__
const T = {
  zh:{ htmlLang:'zh-CN', title:'财报日历 · 日历视图',
    h1main:'财报<span class="em">日历</span>', tag:'日历视图',
    navList:'📋 列表视图', navCal:'🗓️ 日历视图', navAbout:'🛠️ 如何制作', all:'全部', today:'今天', langBtn:'EN',
    search:'搜索公司名 / 代码…', empty:'本月没有匹配的财报 🔍',
    est:'预期', eps:'EPS', rev:'营收',
    impLabel:'⭐ 重磅', impTip:'预期营收 ≥ 100 亿', exportLabel:'📥 导出日历',
    reportWord:'财报', icsName:'财报日历',
    foot:'数据来源：Longbridge Finance Calendar · 仅供参考，不构成投资建议',
    weekFull:['周日','周一','周二','周三','周四','周五','周六'],
    monthTitle:(y,m)=>`${y}年 ${m}月`,
    date:(m,d)=>`${m}月${d}日`,
    more:(n)=>`+${n} 家…`,
    cnt:(n)=>`${n}`,
    modalSub:(week,today,n)=>`${week}${today?' · '+'今天':''} · ${n} 家`,
    sub:(s,e,mk,n)=>`${s} ～ ${e} · 覆盖 ${mk} 市场 · 共 ${n} 场财报`,
    gen:(d)=>`生成于 ${d}` },
  en:{ htmlLang:'en', title:'Earnings Calendar · Calendar View',
    h1main:'Earnings <span class="em">Calendar</span>', tag:'Calendar View',
    navList:'📋 List', navCal:'🗓️ Calendar', navAbout:'🛠️ How it\\'s made', all:'All', today:'Today', langBtn:'中',
    search:'Search name / symbol…', empty:'No matching earnings this month 🔍',
    est:'Est.', eps:'EPS', rev:'Revenue',
    impLabel:'⭐ Notable', impTip:'Est. revenue ≥ 10B', exportLabel:'📥 Export .ics',
    reportWord:'Earnings', icsName:'Earnings Calendar',
    foot:'Source: Longbridge Finance Calendar · For reference only, not investment advice',
    weekFull:['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
    monthTitle:(y,m)=>`${MON_EN[m-1]} ${y}`,
    date:(m,d)=>`${MON_EN[m-1]} ${d}`,
    more:(n)=>`+${n} more…`,
    cnt:(n)=>`${n}`,
    modalSub:(week,today,n)=>`${week}${today?', Today':''} · ${n}`,
    sub:(s,e,mk,n)=>`${s} – ${e} · ${mk} · ${n} earnings`,
    gen:(d)=>`Generated on ${d}` },
};
let lang = localStorage.getItem('fc_lang')||'zh';
let activeMkt='ALL', impOnly=false;
const t=()=>T[lang];
const byImp=(a,b)=>(b.imp||0)-(a.imp||0);

const byDate={}; for(const d of DATA) byDate[d.date]=d.infos;
const markets=[...new Set(DATA.flatMap(d=>d.infos.map(i=>i.market)))].sort();
const months=[...new Set(DATA.map(d=>d.date.slice(0,7)))].sort();
let mi=Math.max(0, months.indexOf(TODAY.slice(0,7)));

const colorOf=(m)=>MKT[m]||'#8b5cf6';
const pad=(n)=>String(n).padStart(2,'0');
function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function whenText(w){return lang==='en'?(WHEN_EN[w]||w):w;}
function nameOf(i){return lang==='en'?(i.name_en||i.name):(i.name||i.name_en);}
function quoteUrl(i){return `https://longbridge.com/${lang==='en'?'en':'zh-CN'}/quote/${encodeURIComponent(i.symbol)}/topics`;}
function infosFor(date){
  let l=byDate[date]||[];
  if(activeMkt!=='ALL') l=l.filter(i=>i.market===activeMkt);
  if(impOnly) l=l.filter(i=>(i.imp||0)>=IMP_STAR);
  return l.slice().sort(byImp);
}

function renderMonth(){
  const ym=months[mi]; const[y,m]=ym.split('-').map(Number);
  document.getElementById('monthTitle').textContent=t().monthTitle(y,m);
  document.getElementById('prev').disabled=mi<=0;
  document.getElementById('next').disabled=mi>=months.length-1;
  const startDow=new Date(Date.UTC(y,m-1,1)).getUTCDay();
  const days=new Date(Date.UTC(y,m,0)).getUTCDate();
  let html='', monthTotal=0;
  for(let i=0;i<startDow;i++) html+=`<div class="cell empty"></div>`;
  for(let d=1;d<=days;d++){
    const date=`${y}-${pad(m)}-${pad(d)}`;
    const infos=infosFor(date);
    const isToday=date===TODAY;
    const cls=`cell${infos.length?' has':''}${isToday?' today':''}`;
    let body=`<div class="cell-num">${d}${infos.length?`<span class="cnt">${t().cnt(infos.length)}</span>`:''}</div>`;
    for(const i of infos.slice(0,3))
      body+=`<div class="ev"><span class="d" style="background:${colorOf(i.market)}"></span><span class="t">${i.imp>=IMP_STAR?'⭐':''}${esc(nameOf(i))}</span></div>`;
    if(infos.length>3) body+=`<div class="more">${t().more(infos.length-3)}</div>`;
    html+=`<div class="${cls}" ${infos.length?`data-date="${date}"`:''}>${body}</div>`;
    monthTotal+=infos.length;
  }
  document.getElementById('grid').innerHTML=html;
  const note=document.getElementById('emptyNote');
  if(note) note.textContent = monthTotal? '' : t().empty;
}

function openDay(date){
  const infos=infosFor(date); if(!infos.length) return;
  const[y,m,d]=date.split('-').map(Number);
  const dt=new Date(Date.UTC(y,m-1,d));
  let rows='';
  for(const i of infos){
    const color=colorOf(i.market);
    const initials=(i.name||'?').slice(0,2).toUpperCase();
    const ico=i.icon
      ? `<img class="ico" src="${esc(i.icon)}" loading="lazy" onerror="this.outerHTML='<div class=\\'ico-fb\\' style=\\'background:${color}\\'>${initials}</div>'">`
      : `<div class="ico-fb" style="background:${color}">${initials}</div>`;
    rows+=`<div class="row">
      ${ico}
      <div class="row-name"><a class="n" href="${quoteUrl(i)}" target="_blank" rel="noopener">${i.imp>=IMP_STAR?'⭐ ':''}${esc(nameOf(i))}</a><div class="s">${esc(i.symbol)}</div></div>
      ${i.when?`<span class="when">${esc(whenText(i.when))}</span>`:''}
      <span class="badge" style="background:${color}">${i.market}</span>
    </div>`;
  }
  document.getElementById('modal').innerHTML=`
    <div class="modal-head">
      <span class="modal-date">${t().date(m,d)}</span>
      <span class="modal-week">${t().modalSub(t().weekFull[dt.getUTCDay()], date===TODAY, infos.length)}</span>
      <button class="modal-close" id="mclose">×</button>
    </div>${rows}`;
  document.getElementById('ov').classList.add('open');
  document.getElementById('mclose').onclick=closeDay;
}
function closeDay(){document.getElementById('ov').classList.remove('open');}

function exportICS(){
  const events=[];
  for(const day of DATA){
    for(const i of infosFor(day.date)){
      const when=i.when?' · '+whenText(i.when):'';
      const er=lang==='en'?(i.est_rev_en||''):i.est_rev;
      const parts=[];
      if(i.est_eps) parts.push(`${t().eps} ${t().est} ${i.est_eps}`);
      if(er) parts.push(`${t().rev} ${t().est} ${er}`);
      parts.push(quoteUrl(i));
      events.push({symbol:i.symbol, date:day.date,
        summary:`📅 ${nameOf(i)} (${i.symbol}) ${t().reportWord}${when}`,
        desc:parts.join('\\n'), url:quoteUrl(i)});
    }
  }
  downloadICS(events, t().icsName);
}

function buildWeekhead(){
  const w=t().weekFull;
  document.getElementById('weekhead').innerHTML=
    w.map((x,idx)=>`<div class="${idx===0||idx===6?'we':''}">${x}</div>`).join('');
}
function buildFilters(){
  document.getElementById('filters').innerHTML=
    ['ALL',...markets].map(m=>`<span class="chip${m===activeMkt?' on':''}" data-m="${m}">${m==='ALL'?t().all:m}</span>`).join('');
}

function applyLang(){
  const x=t();
  document.documentElement.lang=x.htmlLang;
  document.title=x.title;
  document.getElementById('h1main').innerHTML=x.h1main;
  document.getElementById('h1tag').textContent=x.tag;
  document.getElementById('navList').textContent=x.navList;
  document.getElementById('navCal').textContent=x.navCal;
  document.getElementById('navAbout').textContent=x.navAbout;
  document.getElementById('foot').textContent=x.foot;
  document.getElementById('langBtn').textContent=x.langBtn;
  document.getElementById('impChip').textContent=x.impLabel;
  document.getElementById('impChip').classList.toggle('on',impOnly);
  document.getElementById('exportBtn').textContent=x.exportLabel;
  const totalAll=DATA.reduce((a,d)=>a+d.infos.length,0);
  document.getElementById('sub').textContent=x.sub(DATA[0].date,DATA[DATA.length-1].date,markets.join(' / '),totalAll);
  document.getElementById('gen').textContent=x.gen(GENERATED);
  document.getElementById('legend').innerHTML=markets.map(m=>`<span><i style="background:${colorOf(m)}"></i>${m}</span>`).join('');
  buildWeekhead(); buildFilters(); renderMonth();
}

document.getElementById('grid').addEventListener('click',e=>{
  const c=e.target.closest('.cell.has'); if(!c) return; openDay(c.dataset.date);
});
document.getElementById('ov').addEventListener('click',e=>{if(e.target.id==='ov')closeDay();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDay();});
document.getElementById('prev').onclick=()=>{if(mi>0){mi--;renderMonth();}};
document.getElementById('next').onclick=()=>{if(mi<months.length-1){mi++;renderMonth();}};
document.getElementById('impChip').addEventListener('click',e=>{
  impOnly=!impOnly; e.currentTarget.classList.toggle('on',impOnly); renderMonth();
});
document.getElementById('exportBtn').addEventListener('click',exportICS);
document.getElementById('filters').addEventListener('click',e=>{
  const c=e.target.closest('.chip'); if(!c) return;
  activeMkt=c.dataset.m;
  document.querySelectorAll('#filters .chip').forEach(z=>z.classList.toggle('on',z===c));
  renderMonth();
});
document.getElementById('langBtn').addEventListener('click',()=>{
  lang=lang==='zh'?'en':'zh'; localStorage.setItem('fc_lang',lang); applyLang();
});

let theme = localStorage.getItem('fc_theme')||'dark';
function applyTheme(){
  document.body.classList.toggle('light', theme==='light');
  document.getElementById('themeBtn').textContent = theme==='light'?'🌙':'☀️';
}
document.getElementById('themeBtn').addEventListener('click',()=>{
  theme=theme==='dark'?'light':'dark'; localStorage.setItem('fc_theme',theme); applyTheme();
});

applyTheme();
applyLang();
</script>
</body>
</html>'''

# ============================ ABOUT VIEW (about.html) ===================
ABOUT_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>财报日历 · 如何制作</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📅</text></svg>">
<style>
__SHARED__
  .card{
    background:var(--panel);border:1px solid var(--line);border-radius:14px;
    padding:26px 24px;margin-top:18px;max-width:620px;
  }
  .card h2{font-size:16px;font-weight:700;margin-bottom:10px}
  .card p{color:var(--muted);font-size:14px;line-height:1.8;margin-bottom:14px}
  .card p .hl{color:var(--text);font-weight:600}
  .codebox{
    position:relative;background:var(--panel2);border:1px solid var(--line);
    border-radius:10px;padding:14px 16px;margin-top:6px;
  }
  .codebox pre{
    white-space:pre-wrap;word-break:break-all;line-height:1.75;margin:0;padding-right:74px;
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:var(--text);
  }
  .copy-btn{
    position:absolute;top:10px;right:10px;background:var(--accent);color:#fff;border:none;
    border-radius:8px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;transition:.15s;
  }
  .copy-btn:hover{filter:brightness(1.08)}
</style>
</head>
<body>
<div class="topbar">
  <button class="icon-btn" id="themeBtn" title="theme">🌙</button>
  <button class="lang-btn" id="langBtn">EN</button>
</div>
<div class="wrap">
  <header>
    <h1>📅 <span id="h1main"></span> <span class="tag" id="h1tag" style="font-size:14px;color:var(--muted);font-weight:400"></span></h1>
    <div class="nav"><a class="nav-link" id="navCal" href="index.html"></a><a class="nav-link" id="navList" href="list.html"></a><a class="nav-link on" id="navAbout" href="about.html"></a></div>
  </header>

  <div class="card">
    <h2 id="aboutH2"></h2>
    <p id="aboutP1"></p>
    <h2 id="installH2"></h2>
    <p id="installDesc"></p>
    <div class="codebox">
      <button class="copy-btn" id="copyBtn"></button>
      <pre id="codeText"></pre>
    </div>
    <p id="usage" style="margin-top:18px"></p>
    <div class="codebox">
      <button class="copy-btn" id="copyBtn2"></button>
      <pre id="usageCode"></pre>
    </div>
    <h2 id="authorH2" style="margin-top:24px"></h2>
    <p id="authorInfo"></p>
  </div>

  <footer style="margin-top:40px;text-align:center;color:var(--muted);font-size:11px;line-height:1.7">
    <span id="foot"></span>
  </footer>
</div>

<script>
const T = {
  zh:{ htmlLang:'zh-CN', title:'财报日历 · 如何制作',
    h1main:'财报<span class="em">日历</span>', tag:'如何制作',
    navList:'📋 列表视图', navCal:'🗓️ 日历视图', navAbout:'🛠️ 如何制作', langBtn:'EN',
    aboutH2:'关于本项目',
    aboutP1:'本财报日历由 <span class="hl">长桥 (Longbridge) Skill</span> 制作。日历数据通过长桥 Skill 的财经日历接口自动获取，并生成中英文双语页面。',
    installH2:'如何安装 Longbridge Skill',
    installDesc:'复制下面的内容发送给任意 AI，一键安装：',
    codeText:'请按照以下指南安装 Longbridge AI toolkit：\\nhttps://open.longbridge.com/skill/install.md?invite-code=K3CL9B\\n安装完成后，完成登录授权，查询一支股票行情确认可用。',
    copy:'复制', copied:'已复制 ✓',
    usage:'安装后，发送以下指令生成财报日历：',
    usageCode:'调用 longbridge skill 生成财报日历。',
    authorH2:'关于作者',
    authorInfo:'Tony D · <a href="mailto:jcflyingco@outlook.com">jcflyingco@outlook.com</a> · 微信号：veryfly888',
    foot:'数据来源：Longbridge Finance Calendar · 仅供参考，不构成投资建议' },
  en:{ htmlLang:'en', title:'Earnings Calendar · How it\\'s made',
    h1main:'Earnings <span class="em">Calendar</span>', tag:'How it\\'s made',
    navList:'📋 List', navCal:'🗓️ Calendar', navAbout:'🛠️ How it\\'s made', langBtn:'中',
    aboutH2:'About this project',
    aboutP1:'This earnings calendar is built with the <span class="hl">Longbridge skill</span>. The calendar data is fetched automatically through the Longbridge skill\\'s finance-calendar API, and the bilingual pages are generated from it.',
    installH2:'How to install the Longbridge Skill',
    installDesc:'Copy and send this to any AI — it will guide you through the installation:',
    codeText:'Please install the Longbridge AI toolkit by following this guide:\\nhttps://open.longbridge.com/skill/install.md?invite-code=K3CL9B\\nAfter installing, complete the login authorization and query a stock quote to confirm it works.',
    copy:'Copy', copied:'Copied ✓',
    usage:'After installing, send the following to generate the earnings calendar:',
    usageCode:'Using the longbridge skill to generate the earnings calendar.',
    authorH2:'About the author',
    authorInfo:'Tony D · <a href="mailto:jcflyingco@outlook.com">jcflyingco@outlook.com</a> · WeChat veryfly888',
    foot:'Source: Longbridge Finance Calendar · For reference only, not investment advice' },
};
let lang = localStorage.getItem('fc_lang')||'zh';
const t=()=>T[lang];

function applyLang(){
  const x=t();
  document.documentElement.lang=x.htmlLang;
  document.title=x.title;
  document.getElementById('h1main').innerHTML=x.h1main;
  document.getElementById('h1tag').textContent=x.tag;
  document.getElementById('navList').textContent=x.navList;
  document.getElementById('navCal').textContent=x.navCal;
  document.getElementById('navAbout').textContent=x.navAbout;
  document.getElementById('aboutH2').textContent=x.aboutH2;
  document.getElementById('aboutP1').innerHTML=x.aboutP1;
  document.getElementById('installH2').textContent=x.installH2;
  document.getElementById('installDesc').textContent=x.installDesc;
  document.getElementById('codeText').textContent=x.codeText;
  document.getElementById('copyBtn').textContent=x.copy;
  document.getElementById('usage').textContent=x.usage;
  document.getElementById('usageCode').textContent=x.usageCode;
  document.getElementById('copyBtn2').textContent=x.copy;
  document.getElementById('authorH2').textContent=x.authorH2;
  document.getElementById('authorInfo').innerHTML=x.authorInfo;
  document.getElementById('foot').textContent=x.foot;
  document.getElementById('langBtn').textContent=x.langBtn;
}
document.getElementById('langBtn').addEventListener('click',()=>{
  lang=lang==='zh'?'en':'zh'; localStorage.setItem('fc_lang',lang); applyLang();
});

function wireCopy(btnId, getText){
  const btn=document.getElementById(btnId);
  btn.addEventListener('click',()=>{
    const txt=getText();
    const done=()=>{btn.textContent=t().copied; setTimeout(()=>{btn.textContent=t().copy;},1500);};
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(txt).then(done).catch(()=>fallbackCopy(txt,done));
    } else { fallbackCopy(txt,done); }
  });
}
wireCopy('copyBtn', ()=>t().codeText);
wireCopy('copyBtn2', ()=>t().usageCode);
function fallbackCopy(txt,done){
  const ta=document.createElement('textarea');
  ta.value=txt; ta.style.position='fixed'; ta.style.opacity='0';
  document.body.appendChild(ta); ta.select();
  try{document.execCommand('copy');}catch(e){}
  document.body.removeChild(ta); done();
}

let theme = localStorage.getItem('fc_theme')||'dark';
function applyTheme(){
  document.body.classList.toggle('light', theme==='light');
  document.getElementById('themeBtn').textContent = theme==='light'?'🌙':'☀️';
}
document.getElementById('themeBtn').addEventListener('click',()=>{
  theme=theme==='dark'?'light':'dark'; localStorage.setItem('fc_theme',theme); applyTheme();
});

applyTheme();
applyLang();
</script>
</body>
</html>'''

# ---- shared .ics export helper (raw string: backslashes stay literal) ---
ICS_JS = r'''
const IMP_STAR = 1e10;  // 预期营收 >= 100亿 视为「重磅」
function icsEsc(s){
  return String(s==null?'':s).split('\\').join('\\\\').split(';').join('\\;').split(',').join('\\,').split('\n').join('\\n');
}
function icsDate(s){return s.split('-').join('');}
function icsNextDay(s){const a=s.split('-').map(Number);const dt=new Date(Date.UTC(a[0],a[1]-1,a[2]+1));const p=n=>String(n).padStart(2,'0');return ''+dt.getUTCFullYear()+p(dt.getUTCMonth()+1)+p(dt.getUTCDate());}
function downloadICS(events, calName){
  if(!events.length){return;}
  let s='BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Earnings Calendar//EN\r\nCALSCALE:GREGORIAN\r\nX-WR-CALNAME:'+icsEsc(calName)+'\r\n';
  for(const e of events){
    s+='BEGIN:VEVENT\r\nUID:'+icsEsc(e.symbol+'-'+e.date)+'@earnings-calendar\r\nDTSTAMP:'+icsDate(GENERATED)+'T000000Z\r\nDTSTART;VALUE=DATE:'+icsDate(e.date)+'\r\nDTEND;VALUE=DATE:'+icsNextDay(e.date)+'\r\nSUMMARY:'+icsEsc(e.summary)+'\r\nDESCRIPTION:'+icsEsc(e.desc)+'\r\nURL:'+icsEsc(e.url)+'\r\nEND:VEVENT\r\n';
  }
  s+='END:VCALENDAR\r\n';
  const blob=new Blob([s],{type:'text/calendar;charset=utf-8'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download='earnings-calendar.ics';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(function(){URL.revokeObjectURL(a.href);}, 1000);
}
'''

def build(tpl, fname):
    out = tpl.replace('__SHARED__', SHARED_HEAD).replace('__ICS__', ICS_JS).replace('__DATA__', COMPACT)
    open(fname, 'w').write(out)
    print('wrote', fname, len(out), 'bytes')

build(CAL_HTML, 'index.html')    # calendar view is the default landing page
build(LIST_HTML, 'list.html')
build(ABOUT_HTML, 'about.html')
