#!/usr/bin/env python3
"""Refresh calendar_data.json from the Longbridge `finance-calendar report`
endpoint (US + HK earnings), then run build_pages.py to regenerate the pages.

Data shape per entry mirrors what the bilingual pages expect:
  name / name_en, content / content_en, est_rev / est_rev_en, act_rev / act_rev_en,
  est_eps, act_eps, when, currency, icon, symbol, market, live, imp

zh fields come from `report --lang zh-CN`; name_en comes from `static --lang en`;
content_en and the *_en revenue strings are derived locally to match the existing format.
"""
import json
import re
import subprocess
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

MARKETS = ["US", "HK"]

# Earnings-call clock times come back as Unix seconds; render them in the
# event's own market timezone (DST-aware) plus a Beijing time for convenience.
MARKET_TZ = {"US": ZoneInfo("America/New_York"), "HK": ZoneInfo("Asia/Hong_Kong")}
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
# Monthly windows defeat the server-side per-call event cap (US returns ~240/call).
WINDOWS = [
    ("2026-06-01", "2026-06-30"),
    ("2026-07-01", "2026-07-31"),
    ("2026-08-01", "2026-08-31"),
    ("2026-09-01", "2026-09-30"),
    ("2026-10-01", "2026-10-31"),
    ("2026-11-01", "2026-11-30"),
    ("2026-12-01", "2026-12-31"),
    ("2027-01-01", "2027-01-31"),
    ("2027-02-01", "2027-02-28"),
    ("2027-03-01", "2027-03-31"),
]


def run(args, lang):
    """Invoke the longbridge CLI with a forced LANG so name localization is honored."""
    env_lang = "en_US.UTF-8" if lang == "en" else "zh_CN.UTF-8"
    out = subprocess.run(
        ["longbridge", *args, "--format", "json", "--lang", lang],
        capture_output=True, text=True,
        env={"LANG": env_lang, "PATH": "/opt/homebrew/bin:/usr/bin:/bin"},
    )
    if out.returncode != 0:
        sys.stderr.write(f"! {' '.join(args)} ({lang}) failed: {out.stderr.strip()}\n")
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        sys.stderr.write(f"! could not parse JSON for {' '.join(args)}\n")
        return None


def kv(info, t):
    """Return (value, value_raw) for a data_kv type, or ('', '')."""
    for e in info.get("data_kv", []):
        if e.get("type") == t:
            return e.get("value", ""), e.get("value_raw", "")
    return "", ""


def fmt_rev(raw):
    """Format a raw revenue float into the en short form: 13.18B / 79.45M / 52.00K."""
    if not raw:
        return ""
    v = float(raw)
    if v >= 1e9:
        return f"{v / 1e9:.2f}B"
    if v >= 1e6:
        return f"{v / 1e6:.2f}M"
    if v >= 1e3:
        return f"{v / 1e3:.2f}K"
    return f"{v:.2f}"


def content_en(zh):
    """Derive the English earnings label from the zh content string."""
    m = re.search(r"(\d{4}) 财年第 (\d) 季度", zh)
    if m:
        return f"FY{m.group(1)} Q{m.group(2)} earnings"
    m = re.search(r"(\d{4}) 财年年报", zh)
    if m:
        return f"FY{m.group(1)} Annual earnings"
    m = re.search(r"(\d{4}) 财年半年报", zh)
    if m:
        return f"FY{m.group(1)} Interim earnings"
    m = re.search(r"(\d{4}) 财年前三季度", zh)
    if m:
        return f"FY{m.group(1)} earnings"
    return zh


def call_times(started_at, market):
    """From a Unix-second earnings-call start, return (local, beijing) as
    'MM-DD HH:MM' strings — local in the market's own timezone. ('','') if absent."""
    tz = MARKET_TZ.get(market)
    if not started_at or tz is None:
        return "", ""
    local = datetime.fromtimestamp(int(started_at), tz=tz)
    return local.strftime("%m-%d %H:%M"), local.astimezone(BEIJING_TZ).strftime("%m-%d %H:%M")


def symbol_of(counter_id):
    p = counter_id.split("/")
    return f"{p[2]}.{p[1]}" if len(p) >= 3 else counter_id


# --- 1. fetch zh reports, grouped by day, US before HK, deduped by event id ----
days = {}            # date -> {"US": [info...], "HK": [info...]}
seen_ids = set()
for market in MARKETS:
    kept = 0
    for start, end in WINDOWS:
        data = run(["finance-calendar", "report", "--market", market,
                    "--start", start, "--end", end, "--count", "1000"], "zh-CN")
        if not data:
            continue
        for day in data.get("list", []):
            d = day["date"]
            for info in day.get("infos", []):
                if info.get("id") in seen_ids:
                    continue
                seen_ids.add(info.get("id"))
                days.setdefault(d, {"US": [], "HK": []})[market].append(info)
                kept += 1
    print(f"  {market}: {kept} events")

# --- 2. resolve English names via `static --lang en`, batched ------------------
symbols = sorted({symbol_of(i["counter_id"])
                  for d in days.values() for m in d.values() for i in m})
name_en = {}
for x in range(0, len(symbols), 10):
    batch = symbols[x:x + 10]
    res = run(["static", *batch], "en")
    for r in (res or []):
        name_en[r["symbol"]] = r.get("name", "")
print(f"  resolved {len(name_en)}/{len(symbols)} English names")

# --- 3. assemble records in the page's schema --------------------------------
def build(info):
    est_eps_v, _ = kv(info, "estimate_eps")
    act_eps_v, _ = kv(info, "actual_eps")
    est_rev_v, est_rev_raw = kv(info, "estimate_revenue")
    act_rev_v, act_rev_raw = kv(info, "actual_revenue")
    sym = symbol_of(info["counter_id"])
    live = info.get("live")
    started_at = live.get("started_at") if isinstance(live, dict) else None
    call_local, call_bj = call_times(started_at, info.get("market", ""))
    return {
        "name": info.get("counter_name", ""),
        "symbol": sym,
        "market": info.get("market", ""),
        "content": info.get("content", ""),
        "content_en": content_en(info.get("content", "")),
        "icon": info.get("icon", ""),
        "when": info.get("date_type", ""),
        "currency": info.get("currency", ""),
        "est_eps": est_eps_v,
        "act_eps": act_eps_v,
        "est_rev": est_rev_v,
        "act_rev": act_rev_v,
        "est_rev_en": fmt_rev(est_rev_raw) if est_rev_raw else ("--" if est_rev_v == "--" else "--"),
        "act_rev_en": fmt_rev(act_rev_raw),
        "live": live.get("name") if isinstance(live, dict) else live,
        "call_local": call_local,   # earnings-call time in the market's own tz (盘前/盘后 only when absent)
        "call_bj": call_bj,         # same instant in Beijing time
        "name_en": name_en.get(sym, ""),
        "imp": float(est_rev_raw) if est_rev_raw else 0.0,
    }

out = []
for d in sorted(days):
    infos = [build(i) for i in days[d]["US"]] + [build(i) for i in days[d]["HK"]]
    out.append({"date": d, "infos": infos})

json.dump(out, open("calendar_data.json", "w"), ensure_ascii=False, indent=1)
total = sum(len(x["infos"]) for x in out)
print(f"  wrote calendar_data.json: {len(out)} days, {total} events "
      f"({out[0]['date']} → {out[-1]['date']})")

# --- 4. regenerate the pages --------------------------------------------------
subprocess.run([sys.executable, "build_pages.py"], check=True)
