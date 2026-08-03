# 数据更新流程

刷新财报日历数据的操作手册。**重点是第 3 步的验收** —— 抓漏数据时脚本不会报错，页面照样正常生成，只是少了几天。

## 1. 确认时间范围

`fetch_calendar.py` 顶部：

```python
START_DATE = "2026-06-01"
END_DATE   = "2026-12-31"
```

这两个常量是**唯一**需要手动前移的地方。`build_pages.py` 的月份列表是从数据里推导的（`[...new Set(DATA.map(d=>d.date.slice(0,7)))]`），不用改。

习惯上留一点历史（往前 2 个月，页面上能回看已公布的实际值）+ 未来 6 个月。

## 2. 跑抓取

```bash
python3 fetch_calendar.py     # 抓数据 → 写 calendar_data.json → 自动调 build_pages.py 生成 3 个页面
```

耗时约 3–5 分钟，大头在第 2 步解析英文名（`static` 命令按 10 个一批，5000 个 symbol 要几百次调用）。

正常输出：

```
  US: 4502 events
  HK: 967 events
  resolved 5045/5045 English names
  wrote calendar_data.json: 137 days, 5469 events (2026-06-01 → 2026-12-17)
```

- `resolved` 的两个数字应该相等，差太多说明英文名没解析全（页面切英文时会显示空白）
- 事件总量跟上次比不该断崖式下跌

## 3. 验收（别跳过）

```bash
python3 - <<'EOF'
import json
d = json.load(open('calendar_data.json'))
print(f"{len(d)} days  {sum(len(x['infos']) for x in d)} events  {d[0]['date']} -> {d[-1]['date']}")
us = [(x['date'], sum(1 for i in x['infos'] if i['market'] == 'US')) for x in d]
cliffs = [(a, na, b) for (a, na), (b, nb) in zip(us, us[1:]) if na >= 80 and nb == 0]
print("cliffs:", cliffs or "none")
for sym in ('AAPL.US', 'MSFT.US', 'AMZN.US', 'NVDA.US', '700.HK'):
    print(f"  {sym}: {[x['date'] for x in d for i in x['infos'] if i['symbol'] == sym] or 'MISSING'}")
EOF
```

三条判断标准：

1. **日期范围** 覆盖到 `END_DATE` 附近。尾部自然收窄是正常的（远期财报日还没排出来），但不该在 `END_DATE` 前一两个月就整段消失。
2. **`cliffs: none`** —— 「某天美股 ≥80 条、紧接着下一天 0 条」是截断的典型指纹。财报季密集日之间不会突然空一天。
   - 不要用「US=0」单独当指标，周末和远期月份本来就是 0，误报很多。
3. **大盘股点名** 全部命中，不能有 `MISSING`。这几家都落在最密集的财报日上，是最灵敏的探针。

某家公司查不到时，先确认是上游没有还是自己抓漏了 —— 直查接口：

```bash
longbridge finance-calendar report --market HK --start 2026-08-01 --end 2026-12-31 \
  --count 1000 --format json --lang zh-CN | grep -o '.\{80\}9988.\{80\}'
```

比如 `9988.HK`（阿里巴巴）在 2026-06 → 2026-12 区间内上游本身就没有条目，不是抓取问题。

注意 **港股代码不带前导零**：腾讯是 `700.HK` 而不是 `0700.HK`（`symbol_of()` 直接取 `counter_id` 的第三段，`ST/HK/700` → `700.HK`）。用 `0700.HK` 去查会得到假的 MISSING。

## 4. 提交

```bash
git add -A && git commit -m "Refresh earnings calendar data" && git push origin main
```

`index.html` / `list.html` 把数据内联进去了，每次都是 ~2MB 的全量 diff，属正常。

---

## 接口的坑（2026-08 实测）

`longbridge finance-calendar report` 的行为跟参数名给人的印象不一样：

| 参数 | 实际行为 |
|---|---|
| `--end` | **被忽略**。返回的天数只由 `--start` 和服务端上限决定，可能超出 `end` |
| `--count 1000` | **不被尊重**。实测单次返回过 1301 / 1074 条 |
| `next_date` | 返回**空字符串**，没有可用的续拉游标 |

服务端在约 1000 条处**按天边界静默截断** —— 不报错、不标记，就是少几天。所以：

- **不能用固定窗口**（比如按月切）。财报季密集月一次调用装不下，尾部几天会被直接丢掉。
- 现在的做法是**按日期游标翻页**：每轮从「上一轮返回的最后一天 + 1 天」继续，直到走完 `END_DATE`。截断是干净的按天切分（已验证：宽窗口最后一天 07-29 返回 330 条，单独窄查也是 330 条），所以最后一天是完整的，不用回退重拉。
- 由于 `--end` 被忽略，返回结果里**必须**保留 `if d < START_DATE or d > END_DATE: continue` 的过滤。

### 这个坑造成过的实际后果

修复前用的是固定月窗口，7 月只拿到 07-01 → 07-29，8 月只拿到 08-03 → 08-06，之后的美股事件全为 0 条。**亚马逊 2026-07-30 的 Q2 财报整条缺失**，苹果同日、英伟达 08-27 也一样没有 —— 恰好丢掉的是财报季最重要的几天。

修复后：美股 437 → 4502 条，港股 426 → 967 条。

### 还没处理的边界

如果将来**单日**事件数本身超过服务端上限，那天仍会被截掉一部分且不报错，游标翻页救不了（游标最小步长是 1 天）。目前最密集的 2026-08-06 是 510 条，离上限还有一倍余量。真撞上了得改成按半天/分页参数拉。
