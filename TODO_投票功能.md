# 你的 To-Do：上線「現在就投票」功能

> 程式我都寫好了（前端投票區、後端 API、審核頁 admin.html、資料庫 schema）。
> 以下是**只有你能做**的部分（建帳號 / 金鑰 / 部署）。詳細指令在 [voting/DEPLOY.md](voting/DEPLOY.md)。

## A. 帳號與工具
- [ ] 註冊 Cloudflare 免費帳號
- [ ] 安裝 wrangler 並登入：`npm i -g wrangler && wrangler login`

## B. 資料庫（D1）
- [ ] 建立：`wrangler d1 create congressthon`
- [ ] 把回傳的 `database_id` 填進 [wrangler.toml](wrangler.toml)
- [ ] 建表+種子：`wrangler d1 execute congressthon --remote --file=voting/schema.sql`

## C. 人機驗證（Turnstile，防機器人）
- [ ] Cloudflare 後台 → Turnstile → 新增站台，拿 **Site Key** 與 **Secret Key**
- [ ] 把 Site Key 填進 [src/index.src.html](src/index.src.html) 裡 `id="vote-turnstile"` 的 `data-sitekey=""`
- [ ] 重新打包：`python3 scripts/build_index.py`（產生新的 index.html）

## D. 機密設定
- [ ] `wrangler pages secret put TURNSTILE_SECRET`（貼 Turnstile Secret Key）
- [ ] `wrangler pages secret put ADMIN_TOKEN`（自訂一組長密碼，審核頁要用）
- [ ] `wrangler pages secret put IP_HASH_SALT`（隨機長字串，IP 雜湊用）

## E. 部署（網站從 GitHub Pages 改到 Cloudflare Pages）
- [ ] Cloudflare 後台 → Pages → 連結這個 GitHub repo
      （build 指令留空、輸出目錄填 `.`、綁定 D1：binding 名 `DB`）
- [ ] 或手動：`wrangler pages deploy .`

## F. 驗收
- [ ] 開你的網站 → 投票區能按讚、可複選
- [ ] 送一個新主題 → 應顯示「待審核」
- [ ] 開 `你的網址/admin.html` → 貼 ADMIN_TOKEN → 看到待審、可通過/退回
- [ ] 通過後回網站，新主題出現在投票區

## 想本機先試（不部署也行）
```bash
wrangler d1 execute congressthon --local --file=voting/schema.sql
wrangler pages dev . --d1 DB=congressthon
# 開 http://localhost:8788
```

---
**備註**
- 投票（👍）不需要 Turnstile，部署後立刻可用；**只有「送出新主題」需要 Site Key**，所以 C 步驟沒做完前，新主題送出會失敗、但投票正常。
- 隱私：資料庫只存主題文字與票數，IP 只存加鹽雜湊，新主題一律先審後公開。
