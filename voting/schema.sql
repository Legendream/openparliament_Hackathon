-- 國會松「現在就投票」資料庫（Cloudflare D1 / SQLite）
-- 不含任何問卷個資；seed 為現有主題分類與活動形式。

CREATE TABLE IF NOT EXISTS topics (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  text       TEXT    NOT NULL,
  kind       TEXT    NOT NULL DEFAULT 'topic',     -- topic（主題）| format（活動形式）
  status     TEXT    NOT NULL DEFAULT 'pending',    -- pending | approved | rejected
  source     TEXT    NOT NULL DEFAULT 'user',       -- seed | user
  ip_hash    TEXT,                                   -- 送出者 IP 雜湊（限流用，不存原始 IP）
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS votes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id   INTEGER NOT NULL,
  voter      TEXT    NOT NULL,                       -- 前端 localStorage 隨機 token
  ip_hash    TEXT,
  created_at INTEGER NOT NULL,
  UNIQUE(topic_id, voter)                            -- 同一人同一項目只算一次
);

CREATE INDEX IF NOT EXISTS idx_votes_topic ON votes(topic_id);
CREATE INDEX IF NOT EXISTS idx_votes_ip    ON votes(ip_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_topics_ip   ON topics(ip_hash, created_at);

-- 種子：主題（text 與網站問卷分類完全一致，方便對照問卷人次）
INSERT INTO topics (text, kind, status, source, created_at) VALUES
 ('立委與助理實務',     'topic', 'approved', 'seed', unixepoch()),
 ('議事與立法流程',     'topic', 'approved', 'seed', unixepoch()),
 ('AI與資料工具',       'topic', 'approved', 'seed', unixepoch()),
 ('預算決算',           'topic', 'approved', 'seed', unixepoch()),
 ('特定政策議題',       'topic', 'approved', 'seed', unixepoch()),
 ('資料解讀與媒體識讀', 'topic', 'approved', 'seed', unixepoch()),
 ('開放國會與透明',     'topic', 'approved', 'seed', unixepoch());

-- 種子：活動形式
INSERT INTO topics (text, kind, status, source, created_at) VALUES
 ('講座/邀請來賓',  'format', 'approved', 'seed', unixepoch()),
 ('交流/聊聊',      'format', 'approved', 'seed', unixepoch()),
 ('工作坊/動手做',  'format', 'approved', 'seed', unixepoch()),
 ('針對特定受眾',   'format', 'approved', 'seed', unixepoch());
