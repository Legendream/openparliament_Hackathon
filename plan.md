# 專案架構 · g0v 國會松展示網站

## 目的
單頁式網站，向(潛在)參與者與籌備工作小組呈現：歷次活動回饋(NPS/組成)、
大家想聽的主題(可即時投票)、歷次活動紀錄、下一場預告報名、電子報訂閱。

## 🔒 資料隱私原則（最高優先）
- 問卷 **raw data 不進 repo、不上傳**（放 `~/Downloads`，不複製進專案）。
- 衍生**分析結果只留本機 `data/`**；**含逐字答案的設定檔也只留本機**。
- 網站只呈現**聚合統計**(人數/百分比/NPS)，不可回推個人。
- `.gitignore` 已排除：`data/`、所有 `*.csv`、`*.xlsx`；其中 config 內**只放行**兩支
  純方法論檔(見下)。`config/value_synonyms.csv`、`config/wish_labels.csv` 含逐字原文 → 留本機。

## 目錄結構
```
index.html                  打包後的自包含網站（CSS/JS/Chart.js/資料全內嵌，可離線開）
admin.html                  投票新主題的審核頁（需 ADMIN_TOKEN）
src/index.src.html          網站原始樣板（含內嵌 CSS）→ 由 build_index.py 打包成 index.html
assets/
  css/style.css             早期外部樣式（現以 src 內嵌為主）
  js/main.js                NPS/組成等圖表（Chart.js）
  js/vote.js                「想聽什麼」互動投票前端
  js/chart.umd.min.js       本機化的 Chart.js（不依賴 CDN）
  data/site_data.{json,js}  網站用聚合資料（由 build_site_data.py 產生，僅聚合值）
config/                     人工判斷設定檔（pipeline 讀取）
  wish_taxonomy.csv         ✅可上傳：主題分類維度+關鍵字+白話說明（主題/活動形式/工具建議）
  event_themes.csv          ✅可上傳：各場真實標題/連結/主題分類（公開資訊）
  value_synonyms.csv        ⛔本機：職業/管道同義詞（含逐字原文）
  wish_labels.csv           ⛔本機：許願逐筆人工分類（含逐字原文）
scripts/
  normalize_surveys.py      raw xlsx（每分頁一場）→ data/responses_normalized.csv + events.csv
  build_analysis.py         正規化資料 + config → data/analysis/*（NPS、組成、許願需求）
  build_site_data.py        分析結果 → assets/data/site_data.{json,js}（僅聚合）
  build_index.py            src/index.src.html + 各 JS → 自包含 index.html
  run_pipeline.sh           一鍵跑完上面四步
functions/api/              Cloudflare Pages Functions（投票後端）
  topics.js  vote.js  moderate.js  _shared.js
voting/
  schema.sql                D1 資料庫結構 + 種子（主題/形式，不含個資）
  DEPLOY.md                 部署逐步指令
wrangler.toml               Cloudflare Pages/D1 設定
TODO_投票功能.md            上線投票功能你要做的事
data/                       ⛔本機：正規化逐筆、分析輸出（gitignored）
```

## 資料分析 pipeline（可持續擴充）
程式固定、人工判斷在 `config/`。每月新增一場：
1. 在 `~/Downloads/歷次問卷＿去識別化後整合.xlsx` 新增一個分頁。
2. 在 `config/event_themes.csv` 補該場一列（屆次/標題/連結/主題分類）。
3. 跑 `bash scripts/run_pipeline.sh`。
4. `data/analysis/unmapped_values.csv` 若有新職業/管道寫法 → 補 `config/value_synonyms.csv`。
5. 新增的許願 → 在 `config/wish_labels.csv` 人工校訂分類（未校訂者自動用關鍵字暫歸）。

- 表頭以關鍵字比對，欄位順序/題目微調不影響整併。
- 許願分類採**逐筆人工語意判讀**（存 wish_labels.csv），優先於關鍵字自動標。

## 網站區塊（單頁 + 錨點導覽）
1 Hero 預告報名 → 2 關於+統計卡 → 3 參與者輪廓(NPS/職業/管道/新舊) →
4 想聽什麼(**互動投票**：主題/形式可按讚、許願新主題；問卷人次作灰字參考) →
5 歷次活動(15 場真實標題卡，連活動頁/共筆) → 6 Footer 電子報訂閱。

- 配色：g0v 綠 `#00a37a`（單一 accent 變數，全站含圖表共用）。
- Chart.js 本機化、CSS/JS 內嵌 → `index.html` 任何開啟方式都能呈現靜態內容。

## 投票功能（互動，需部署）
- 架構：**Cloudflare Pages**（同網域跑靜態站 + `functions/api/*` + D1 資料庫）。
- 模型：主題與形式皆可投，**可複選**，同項目每人一次（再點取消）。
- 防濫用：新主題**先審後顯示**、Turnstile 人機驗證、同 IP 限流、IP 只存加鹽雜湊。
- 未部署時前端優雅降級為唯讀（仍顯示清單與問卷參考）。
- 上線步驟見 `TODO_投票功能.md` / `voting/DEPLOY.md`（建帳號/金鑰/部署由專案擁有者執行）。

## 部署
- **正式站**：`congressthon.claire-cheng.com`（Cloudflare Pages 自訂網域，2026-06 完成）
- Pages 專案：`openparliament-hackathon`，帳號 `claire18412@gmail.com`
- D1：`congressthon`，Turnstile invisible widget 已上線

## 最近完成（2026-06）
- Turnstile invisible mode 修正（`5be3772`）：改用 `turnstile.execute()` 觸發，許願送出正常。
- 自訂網域：`congressthon.claire-cheng.com` 綁定完成。
- 投票區 UX 強化（PR #1，已 merge）：
  - 說明投票意義（工作小組會參考）、加分享呼籲
  - 投票項目加背景進度條（相對票數比例）、票數數字放大、依票數排序
  - 加入 g0v 國會松 Slack channel 入口（含未有帳號的申請連結）

## 最近完成（2026-07）
- 上次 PR 的 UX 改動（排序/進度條/Slack 入口）補回 `src/index.src.html` + `vote.js`
  來源層，避免下次跑 pipeline 重新打包時被覆蓋消失。
- 投票區可讀性修正（依會後收集到的問題清單逐項處理）：
  - 區分「👍 即時投票」與「📋 問卷 N 人提過」兩種數字的來源說明
  - NPS 卡片加白話公式（推薦者%－批評者%，範圍/門檻說明）
  - `wish_taxonomy.csv` 新增 `description` 欄：依 raw data 為每個許願分類寫白話說明
    （例如「開放國會與透明」→「國會資訊怎麼更公開？g0v 推動開放國會的經驗與挑戰」），
    顯示在投票項目副標；`build_site_data.py` 一併 join 進 site_data
  - 工具/平台類許願改成訪客與工作小組都看得懂的說法：講清楚「這是什麼、為何不列入投票、
    誰會處理」，而非單純同語反覆的分類名稱
  - 許願表單加審核提示（送出後由工作小組確認才會顯示）
- 新增 `LICENSE`（程式碼 MIT + 網站內容 CC BY 4.0 雙授權），footer 加原始碼連結與授權標示。
