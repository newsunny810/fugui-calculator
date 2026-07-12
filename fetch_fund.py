"""
fetch_fund.py
每日自動從 MoneyDJ 抓取安聯台灣科技基金歷史淨值，
計算各年期年化報酬率，輸出 fund_data.json 供 index.html 讀取。
"""

import json
import math
import datetime
import urllib.request
import urllib.error

# ── 設定區 ──────────────────────────────────────────────────────────
FUNDS = {
    "allianz_tech": {
        "name": "安聯台灣科技基金",
        "moneydj_code": "acdd04",
        "inception": "2001-04-03",
        "note": "單筆申購 / 台幣計價"
    }
    # 未來加基金：在這裡新增一筆就好
}

OUTPUT_FILE = "fund_data.json"
# ────────────────────────────────────────────────────────────────────


def fetch_nav_history(code: str) -> list[dict]:
    """
    從 MoneyDJ 抓取近 10 年每日淨值。
    回傳格式：[{"date": "2024-01-02", "nav": 123.45}, ...]
    """
    # MoneyDJ 提供一個可以直接 GET 的 CSV-like 端點
    url = f"https://www.moneydj.com/funddj/yp/yp011001.djhtm?a={code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; fund-data-fetcher/1.0)",
        "Referer": "https://www.moneydj.com/"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as e:
        print(f"  [錯誤] 無法連線 MoneyDJ: {e}")
        return []

    # 解析 <td> 裡的日期和淨值（MoneyDJ 的淨值表格格式）
    import re
    # 找出 "YYYY/MM/DD" 跟接著的數字
    pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2})\s*</td>\s*<td[^>]*>\s*([\d,]+\.\d+)'
    )
    records = []
    for m in pattern.finditer(html):
        date_str = m.group(1).replace("/", "-")
        nav = float(m.group(2).replace(",", ""))
        records.append({"date": date_str, "nav": nav})

    # 去重、排序
    seen = set()
    unique = []
    for r in records:
        if r["date"] not in seen:
            seen.add(r["date"])
            unique.append(r)
    unique.sort(key=lambda x: x["date"])
    return unique


def annualized_return(nav_start: float, nav_end: float, years: float) -> float:
    """計算年化報酬率（%），四捨五入到小數點後兩位。"""
    if nav_start <= 0 or years <= 0:
        return 0.0
    rate = (nav_end / nav_start) ** (1 / years) - 1
    return round(rate * 100, 2)


def find_nav_on_or_before(records: list[dict], target_date: str) -> dict | None:
    """找 target_date 當天或之前最近一筆淨值。"""
    result = None
    for r in records:
        if r["date"] <= target_date:
            result = r
        else:
            break
    return result


def calc_scenarios(records: list[dict], inception: str) -> list[dict]:
    """根據歷史淨值計算各年期年化報酬率。"""
    if not records:
        return []

    today = records[-1]["date"]
    latest_nav = records[-1]["nav"]
    today_dt = datetime.date.fromisoformat(today)

    scenarios = []

    # 定義要計算的年期
    periods = [
        ("3年年化",  3),
        ("5年年化",  5),
        ("10年年化", 10),
    ]

    for label, yrs in periods:
        target_dt = today_dt - datetime.timedelta(days=int(yrs * 365.25))
        target_str = target_dt.isoformat()
        old = find_nav_on_or_before(records, target_str)
        if old is None:
            continue
        actual_years = (today_dt - datetime.date.fromisoformat(old["date"])).days / 365.25
        rate = annualized_return(old["nav"], latest_nav, actual_years)
        scenarios.append({
            "label": label,
            "rate": rate,
            "from_date": old["date"],
            "to_date": today,
            "from_nav": old["nav"],
            "to_nav": latest_nav
        })

    # 成立日年化
    inc_nav = find_nav_on_or_before(records, inception)
    if inc_nav:
        inc_dt = datetime.date.fromisoformat(inc_nav["date"])
        actual_years = (today_dt - inc_dt).days / 365.25
        rate = annualized_return(inc_nav["nav"], latest_nav, actual_years)
        scenarios.append({
            "label": "成立日年化",
            "rate": rate,
            "from_date": inc_nav["date"],
            "to_date": today,
            "from_nav": inc_nav["nav"],
            "to_nav": latest_nav
        })

    return scenarios


def main():
    output = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "funds": {}
    }

    for fund_id, meta in FUNDS.items():
        print(f"\n處理：{meta['name']} ({fund_id})")
        records = fetch_nav_history(meta["moneydj_code"])

        if records:
            print(f"  取得 {len(records)} 筆淨值，最新：{records[-1]}")
            scenarios = calc_scenarios(records, meta["inception"])
        else:
            print("  無法取得淨值，使用備用靜態數據")
            # 備用靜態數據（上次人工確認的數字）
            scenarios = [
                {"label": "3年年化",  "rate": 81.37, "from_date": "", "to_date": "", "from_nav": 0, "to_nav": 0},
                {"label": "5年年化",  "rate": 50.94, "from_date": "", "to_date": "", "from_nav": 0, "to_nav": 0},
                {"label": "10年年化", "rate": 41.60, "from_date": "", "to_date": "", "from_nav": 0, "to_nav": 0},
                {"label": "成立日年化","rate": 19.32, "from_date": "", "to_date": "", "from_nav": 0, "to_nav": 0},
            ]

        output["funds"][fund_id] = {
            "name": meta["name"],
            "inception": meta["inception"],
            "note": meta["note"],
            "latest_nav": records[-1]["nav"] if records else None,
            "latest_date": records[-1]["date"] if records else None,
            "scenarios": scenarios
        }

        for s in scenarios:
            print(f"  {s['label']}: {s['rate']}%")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 已輸出 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
