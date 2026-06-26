// /api/topics
//   GET  ?voter=<token>  → 已核可主題 + 票數 + 此人是否投過
//   POST {text, voter, turnstileToken} → 新增主題（進審核佇列 pending）
import { json, ipHash, nowSec, verifyTurnstile, recentCount } from "./_shared.js";

export async function onRequestGet({ env, request }) {
  const voter = new URL(request.url).searchParams.get("voter") || "";
  const { results } = await env.DB.prepare(
    `SELECT t.id, t.text, t.kind, t.source,
       (SELECT COUNT(*) FROM votes v WHERE v.topic_id = t.id) AS votes,
       (SELECT COUNT(*) FROM votes v WHERE v.topic_id = t.id AND v.voter = ?1) AS voted
     FROM topics t
     WHERE t.status = 'approved'
     ORDER BY votes DESC, t.id ASC`
  ).bind(voter).all();
  return json({ topics: results });
}

export async function onRequestPost({ env, request }) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "格式錯誤" }, 400); }

  const text = (body.text || "").trim().replace(/\s+/g, " ");
  if (text.length < 2 || text.length > 60) return json({ error: "主題長度需 2–60 字" }, 400);

  if (!(await verifyTurnstile(env, body.turnstileToken, request))) {
    return json({ error: "人機驗證失敗，請重試" }, 403);
  }

  const ipv = await ipHash(env, request);
  // 限流：同 IP 10 分鐘最多送 3 個新主題
  if (await recentCount(env, "topics", ipv, 600) >= 3) {
    return json({ error: "太頻繁了，請稍後再試" }, 429);
  }
  // 擋重複：已存在（任何狀態）的相同主題就不重收
  const dup = await env.DB.prepare(
    `SELECT id FROM topics WHERE lower(text) = lower(?1) LIMIT 1`
  ).bind(text).first();
  if (dup) return json({ error: "這個主題已經有人提過了" }, 409);

  await env.DB.prepare(
    `INSERT INTO topics (text, status, source, ip_hash, created_at)
     VALUES (?1, 'pending', 'user', ?2, ?3)`
  ).bind(text, ipv, nowSec()).run();

  return json({ ok: true, message: "已送出，待審核後會出現在投票區" });
}
