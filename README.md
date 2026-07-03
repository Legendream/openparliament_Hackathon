# g0v 國會松展示網站

展示 g0v 國會松的活動資訊、會後問卷，以及大家想聽的主題。

## 目標功能

- 歷次活動滿意度問卷分析（NPS、參與者組成）
- 大家許願想聽的主題 × 歷次國會松主題對照分析
- 歷次國會松活動資訊（共筆、回放影片）
- 下一期活動預告與報名入口
- 國會松電子報訂閱入口

## 參考資料

- 歷次活動：https://g0vcongressthon.oen.tw/
- 歷次共筆：https://g0v.hackmd.io/@SA7CD7VRSp6Fcqw9CaElcQ/SJ93ZW5XR/

## 資料隱私原則

- 問卷 **raw data 不進此資料夾、不上傳 GitHub**（放 `~/Downloads`）。
- 所有整理／分析輸出只留本機 `data/`（已被 `.gitignore` 排除）。
- `config/value_synonyms.csv` 含受訪者逐字答案，亦僅留本機；其餘 config 為純方法論可公開。

## 分析 pipeline（可持續擴充）

程式碼固定，人工判斷都在 `config/`，新月份資料進來重跑即可：

```
scripts/
  normalize_surveys.py  # raw xlsx（每分頁一場）→ data/responses_normalized.csv + events.csv
  build_analysis.py     # 正規化資料 + config → data/analysis/*
  run_pipeline.sh       # 一鍵重跑全流程
config/
  value_synonyms.csv    # 職業/管道同義詞歸一（本機）
  wish_taxonomy.csv     # 許願主題分類關鍵字
  event_themes.csv      # 每場主題與已涵蓋分類
```

**更新流程（每月新增一場後）**

1. 把該月回覆，在 `~/Downloads/歷次問卷＿去識別化後整合.xlsx` 新增一個分頁（沿用既有題目最省事）。
2. 在 `config/event_themes.csv` 補一列該場主題。
3. 執行 `bash scripts/run_pipeline.sh`。
4. 若 `data/analysis/unmapped_values.csv` 出現新的職業/管道寫法，補進 `config/value_synonyms.csv` 再跑一次。

表頭以關鍵字比對，欄位順序或題目文字微調都不影響整併。

### 主要分析產出（`data/analysis/`）

- `nps_by_event.csv`／整體 NPS、推薦/中立/貶損
- `composition_occupation.csv`、`composition_channel.csv`、`composition_first_time.csv`
- `wish_topics_tagged.csv`、`wish_demand_vs_held.csv`（功能②：主題需求強度 × 是否已辦）
- `summary.json`（首頁彙總數字）

## 授權

- 程式碼：[MIT](LICENSE)
- 網站內容（文字、聚合統計圖表）：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh-hant)
- 問卷 raw data 不在此 repo、不適用上述授權（見資料隱私原則）

## 狀態

籌備中（g0v 國會松籌備工作小組）
