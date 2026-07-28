-- 迁移 0008：研究会话状态表
-- 创建时间：2026-07-22
-- 目的：保存研究会话状态，支持多轮对话中的任务连续性
--
-- 小白讲解：
--   这个表就像"记忆笔记本"的存档柜。
--   每个会话（session）都有一本笔记本，记录当前研究的全部上下文。
--   当页面刷新时，系统可以从这个表恢复笔记本内容，
--   而不是依赖截断的聊天历史。

CREATE TABLE IF NOT EXISTS research_session_state (
    session_id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 添加会话状态表的更新索引
CREATE INDEX IF NOT EXISTS idx_research_session_state_updated
ON research_session_state(updated_at);
