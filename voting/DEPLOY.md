# 「現在就投票」部署指南（Cloudflare Pages + D1）

> 你要做的事；指令可直接複製。需要先有一個 Cloudflare 免費帳號。

## 0. 安裝工具（一次）
```bash
npm install -g wrangler   # 或每次用 npx wrangler
wrangler login            # 開瀏覽器登入你的 Cloudflare 帳號
```

## 1. 建立 D1 資料庫
```bash
wrangler d1 create congressthon
```
把輸出的 `database_id` 填進專案根目錄 `wrangler.toml` 的 `database_id`。

## 2. 建表 + 種子（7 個主題）
```bash
wrangler d1 execute congressthon --remote --file=voting/schema.sql   # 線上
wrangler d1 execute congressthon --local  --file=voting/schema.sql   # 本機測試用
```

## 3. 設定 Turnstile（人機驗證，免費）
1. Cloudflare 後台 → Turnstile → Add site，網域填你的 Pages 網址。
2. 拿到 **Site Key**（公開）和 **Secret Key**（機密）。
3. Site Key 填進前端 `assets/js/vote.js` 的 `TURNSTILE_SITE_KEY`（我會留位置）。

## 4. 設定機密
```bash
wrangler pages secret put TURNSTILE_SECRET   # 貼上 Turnstile Secret Key
wrangler pages secret put ADMIN_TOKEN        # 自訂一組長密碼，審核頁要用
wrangler pages secret put IP_HASH_SALT       # 隨便一串長亂碼（IP 雜湊用）
```

## 5. 本機測試
```bash
wrangler pages dev . --d1 DB=congressthon
# 開 http://localhost:8788 ，投票區會接本機 D1
```

## 6. 部署
**方式 A（推薦）**：Cloudflare 後台 → Pages → 連結這個 GitHub repo，build 指令留空、輸出目錄填 `.`，並在專案設定綁定 D1（binding 名 `DB`）。之後每次 push 自動部署。

**方式 B（手動）**：
```bash
wrangler pages deploy .
```

## 審核新主題
開 `你的網址/admin.html`，貼上你設定的 `ADMIN_TOKEN`，就能看到待審主題、按通過 / 退回。

## 隱私備註
- 不存原始 IP，只存加鹽後的雜湊（限流用）。
- 新主題一律「先審核後公開」；投票只是數字，即時生效。
- 資料庫只有主題文字與票數，無問卷個資。
