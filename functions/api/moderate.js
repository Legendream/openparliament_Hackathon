// /api/moderate  （你專用的審核 API，需 ADMIN_TOKEN）
//   GET  ?token=...           → 待審核主題清單
//   POST {token, id, action}  → action: approve | reject
import { json } from "./_shared.js";

function authed(env, token) {
  const a = env.ADMIN_TOKEN || "";
  // 長度不同直接擋；長度相同做逐字比較（避免時間旁路）
  if (!a || !token || a.length !== token.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ token.charCodeAt(i);
  return diff === 0;
}

export async function onRequestGet({ env, request }) {
  const token = new URL(request.url).searchParams.get("token") || "";
  if (!authed(env, token)) return json({ error: "未授權" }, 401);
  const { results } = await env.DB.prepare(
    `SELECT id, text, created_at FROM topics WHERE status = 'pending' ORDER BY created_at ASC`
  ).all();
  return json({ pending: results });
}

export async function onRequestPost({ env, request }) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "格式錯誤" }, 400); }
  if (!authed(env, body.token)) return json({ error: "未授權" }, 401);

  const id = parseInt(body.id, 10);
  const action = body.action;
  if (!id || !["approve", "reject"].includes(action)) return json({ error: "參數錯誤" }, 400);

  const status = action === "approve" ? "approved" : "rejected";
  await env.DB.prepare(`UPDATE topics SET status = ?1 WHERE id = ?2 AND status = 'pending'`)
    .bind(status, id).run();
  return json({ ok: true, id, status });
}
