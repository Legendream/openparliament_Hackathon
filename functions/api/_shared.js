// 共用工具（檔名底線開頭 → 不會被當成路由）

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export function clientIp(request) {
  return request.headers.get("CF-Connecting-IP") || "0.0.0.0";
}

// 不存原始 IP，存加鹽雜湊（隱私）
export async function ipHash(env, request) {
  const data = new TextEncoder().encode(clientIp(request) + "|" + (env.IP_HASH_SALT || "salt"));
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function nowSec() {
  return Math.floor(Date.now() / 1000);
}

// Cloudflare Turnstile 後端驗證
export async function verifyTurnstile(env, token, request) {
  if (!env.TURNSTILE_SECRET) return true; // 未設定金鑰時放行（本機開發）
  if (!token) return false;
  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET);
  form.append("response", token);
  form.append("remoteip", clientIp(request));
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: form,
  });
  const out = await r.json();
  return !!out.success;
}

// 簡單 IP 限流：回傳該 ip_hash 在 windowSec 內、某資料表的筆數
export async function recentCount(env, table, ipHashVal, windowSec) {
  const since = nowSec() - windowSec;
  const row = await env.DB.prepare(
    `SELECT COUNT(*) AS c FROM ${table} WHERE ip_hash = ?1 AND created_at > ?2`
  ).bind(ipHashVal, since).first();
  return row ? row.c : 0;
}
