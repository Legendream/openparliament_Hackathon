// /api/vote   POST {topic_id, voter} → 切換投票（投/取消）。可投多個主題；同主題每人一次。
import { json, ipHash, nowSec, recentCount } from "./_shared.js";

export async function onRequestPost({ env, request }) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "格式錯誤" }, 400); }

  const topicId = parseInt(body.topic_id, 10);
  const voter = (body.voter || "").trim();
  if (!topicId || voter.length < 8) return json({ error: "參數錯誤" }, 400);

  // 主題必須存在且已核可
  const topic = await env.DB.prepare(
    `SELECT id FROM topics WHERE id = ?1 AND status = 'approved'`
  ).bind(topicId).first();
  if (!topic) return json({ error: "主題不存在" }, 404);

  const ipv = await ipHash(env, request);
  // 限流：同 IP 1 分鐘最多 30 次投票動作（擋洗票/機器人）
  if (await recentCount(env, "votes", ipv, 60) >= 30) {
    return json({ error: "操作太頻繁，請稍後再試" }, 429);
  }

  const existing = await env.DB.prepare(
    `SELECT id FROM votes WHERE topic_id = ?1 AND voter = ?2`
  ).bind(topicId, voter).first();

  let voted;
  if (existing) {
    await env.DB.prepare(`DELETE FROM votes WHERE id = ?1`).bind(existing.id).run();
    voted = false;
  } else {
    await env.DB.prepare(
      `INSERT OR IGNORE INTO votes (topic_id, voter, ip_hash, created_at)
       VALUES (?1, ?2, ?3, ?4)`
    ).bind(topicId, voter, ipv, nowSec()).run();
    voted = true;
  }

  const cnt = await env.DB.prepare(
    `SELECT COUNT(*) AS c FROM votes WHERE topic_id = ?1`
  ).bind(topicId).first();

  return json({ ok: true, topic_id: topicId, votes: cnt.c, voted });
}
