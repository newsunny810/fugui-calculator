# 富貴大贏家 變額萬能壽險(戊型) 試算系統

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `index.html` | 主程式（試算網頁） |
| `fund_data.json` | 基金績效數據（每日自動更新） |
| `fetch_fund.py` | 每日自動抓取淨值的 Python 腳本 |
| `.github/workflows/update_fund_data.yml` | GitHub Actions 自動化設定 |

---

## 第一次設定步驟

### 步驟一：上傳到 GitHub

1. 登入 [github.com](https://github.com)，點右上角 **+** → **New repository**
2. Repository name 填：`fugui-calculator`
3. 設為 **Public**（GitHub Pages 免費版需要 Public）
4. 點 **Create repository**
5. 把這個資料夾的所有檔案上傳（拖拉到 GitHub 網頁即可）
   - `index.html`
   - `fund_data.json`
   - `fetch_fund.py`
   - `.github/workflows/update_fund_data.yml`

### 步驟二：開啟 GitHub Pages

1. 進入 repo → 點上方 **Settings**
2. 左側選 **Pages**
3. Source 選 **Deploy from a branch**
4. Branch 選 **main**，資料夾選 **/ (root)**
5. 按 **Save**
6. 等約 1 分鐘，網址會出現：`https://newsunny810.github.io/fugui-calculator/`

### 步驟三：確認 Actions 自動化

1. 進入 repo → 點上方 **Actions**
2. 應該會看到「每日更新基金淨值數據」這個 workflow
3. 點進去 → 點右上角 **Run workflow** 手動跑一次測試
4. 跑完後確認 `fund_data.json` 有被更新

---

## 自動化時間

- 每週一到週五，台灣時間 **下午 4:00** 自動執行
- 基金收盤後抓取，確保取到當日最新淨值

---

## 未來新增基金

在 `fetch_fund.py` 的 `FUNDS` 字典加入新基金：

```python
FUNDS = {
    "allianz_tech": { ... },           # 安聯台灣科技（已有）
    "uni_racing": {                     # 統一奔騰（範例）
        "name": "統一奔騰基金",
        "moneydj_code": "xxxxx",       # MoneyDJ 基金代碼
        "inception": "YYYY-MM-DD",
        "note": "單筆申購 / 台幣計價"
    }
}
```

同時在 `index.html` 的 `<select id="fundSelect">` 加入一行：
```html
<option value="uni_racing">統一奔騰基金</option>
```
