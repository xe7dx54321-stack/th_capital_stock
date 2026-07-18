/**
 * 会话管理服务 (Session Service)
 *
 * 功能：
 *   1:1 复现 OpenAI Codex 的 session 管理方案
 *   1. 每个对话会话（session）有唯一 ID、标题、状态（active/archived）
 *   2. 支持置顶（pinned）、归档（archived）、删除（deleted）
 *   3. 对话消息存储在 chat_messages 表中，关联到 session
 *   4. 提供 session 列表、创建、切换、恢复等 API
 *
 * 数据库表结构（1:1 对应 Codex 的 state_5.sqlite threads 表）：
 *   chat_sessions: 会话表（对应 Codex 的 threads 表）
 *     - id: 唯一会话 ID (UUID)
 *     - title: 会话标题（取自首条用户消息）
 *     - status: 状态 (active / archived)
 *     - is_pinned: 是否置顶 (0/1)
 *     - pinned_at: 置顶时间
 *     - message_count: 消息数量
 *     - last_message_at: 最后消息时间
 *     - created_at: 创建时间
 *     - updated_at: 更新时间
 *
 *   chat_messages: 消息表（对应 Codex 的 sessions/*.jsonl rollout）
 *     - id: 自增主键
 *     - session_id: 关联会话 ID
 *     - role: 消息角色 (user / assistant)
 *     - content: 消息内容
 *     - intent: 意图类型
 *     - created_at: 创建时间
 *
 * 小白讲解：
 *   这个服务就像一个"聊天记录管家"。
 *   Codex 用 sessions/*.jsonl 存完整对话流，用 state_5.sqlite 的 threads 表存会话索引。
 *   我们用同样的思路：chat_messages 表存每条消息（类似 JSONL），chat_sessions 表存会话索引（类似 threads 表）。
 *   支持的操作和 Codex 一样：新建、切换、置顶、归档、删除。
 */

import express from "express";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import crypto from "crypto";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.join(__dirname, "..", "..", "01_data", "db", "vector.db");

/**
 * SessionService 类
 *
 * 管理聊天会话的完整生命周期：创建、列表、切换、置顶、归档、删除
 */
export class SessionService {
  /**
   * 构造函数
   *
   * @param {string} dbPath - 数据库路径，默认使用 vector.db
   */
  constructor(dbPath = DB_PATH) {
    this.dbPath = dbPath;
    this.db = null;
    this.init();
  }

  /**
   * 初始化数据库表
   *
   * 创建 chat_sessions 和 chat_messages 表（如果不存在）
   * 同时创建必要的索引
   */
  init() {
    this.db = new Database(this.dbPath);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL DEFAULT '新对话',
        status TEXT NOT NULL DEFAULT 'active',
        is_pinned INTEGER NOT NULL DEFAULT 0,
        pinned_at DATETIME,
        message_count INTEGER NOT NULL DEFAULT 0,
        last_message_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        intent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);
      CREATE INDEX IF NOT EXISTS idx_chat_sessions_pinned ON chat_sessions(is_pinned);
      CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
      CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
    `);
  }

  /**
   * 关闭数据库连接
   */
  close() {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }

  /**
   * 生成唯一会话 ID
   *
   * 使用 UUID v4 格式，和 Codex 的 thread_id 生成方式一致
   *
   * @returns {string} UUID 格式的会话 ID
   */
  generateSessionId() {
    return crypto.randomUUID();
  }

  /**
   * 创建新会话
   *
   * @param {string} title - 会话标题，默认"新对话"
   * @returns {Object} 新创建的会话对象
   *
   * 小白讲解：
   *   就像在微信里点"发起聊天"，系统会创建一个新对话窗口。
   *   这里的 title 就是对话标题，之后会根据第一条消息自动更新。
   */
  createSession(title = "新对话") {
    const id = this.generateSessionId();
    const stmt = this.db.prepare(`
      INSERT INTO chat_sessions (id, title)
      VALUES (?, ?)
    `);
    stmt.run(id, title);
    return this.getSession(id);
  }

  /**
   * 获取单个会话信息
   *
   * @param {string} sessionId - 会话 ID
   * @returns {Object|null} 会话对象，不存在则返回 null
   */
  getSession(sessionId) {
    const stmt = this.db.prepare(`
      SELECT id, title, status, is_pinned, pinned_at,
             message_count, last_message_at,
             created_at, updated_at
      FROM chat_sessions
      WHERE id = ?
    `);
    return stmt.get(sessionId) || null;
  }

  /**
   * 获取会话列表
   *
   * 对应 Codex 的 thread list 命令
   * 排序规则：先按置顶（pinned在前），再按最后消息时间倒序
   *
   * @param {Object} options - 查询选项
   *   - status: 筛选状态 (active/archived/all)，默认 active
   *   - limit: 返回数量，默认 50
   *   - search: 按标题搜索
   * @returns {Array} 会话列表
   *
   * 小白讲解：
   *   就像微信的聊天列表，置顶的对话排在最上面，
   *   其余的按最后消息时间从新到旧排列。
   *   默认只显示"活跃"的对话，归档的可以单独查看。
   */
  listSessions(options = {}) {
    const { status = "active", limit = 50, search = null } = options;

    let sql = `
      SELECT id, title, status, is_pinned, pinned_at,
             message_count, last_message_at,
             created_at, updated_at
      FROM chat_sessions
    `;
    const params = [];
    const conditions = [];

    if (status !== "all") {
      conditions.push("status = ?");
      params.push(status);
    }

    if (search) {
      conditions.push("title LIKE ?");
      params.push(`%${search}%`);
    }

    if (conditions.length > 0) {
      sql += " WHERE " + conditions.join(" AND ");
    }

    // 排序：置顶在前，然后按最后消息时间倒序
    sql += " ORDER BY is_pinned DESC, pinned_at DESC, last_message_at DESC, created_at DESC";
    sql += " LIMIT ?";
    params.push(limit);

    const stmt = this.db.prepare(sql);
    return stmt.all(...params);
  }

  /**
   * 获取会话中的所有消息
   *
   * 对应 Codex 从 sessions/*.jsonl 读取 rollout 的操作
   *
   * @param {string} sessionId - 会话 ID
   * @returns {Array} 消息列表（按时间正序）
   *
   * 小白讲解：
   *   就像打开微信某个聊天窗口，把之前的消息全部加载出来。
   *   Codex 是从 JSONL 文件读取，我们是从数据库读取，效果一样。
   */
  getSessionMessages(sessionId) {
    const stmt = this.db.prepare(`
      SELECT id, session_id, role, content, intent, created_at
      FROM chat_messages
      WHERE session_id = ?
      ORDER BY created_at ASC
    `);
    return stmt.all(sessionId);
  }

  /**
   * 向会话添加消息
   *
   * 同时更新会话的 message_count、last_message_at 和 title（如果是第一条用户消息）
   *
   * @param {string} sessionId - 会话 ID
   * @param {string} role - 消息角色 (user/assistant)
   * @param {string} content - 消息内容
   * @param {string} intent - 意图类型（可选）
   * @returns {number} 新消息的 ID
   *
   * 小白讲解：
   *   每发一条消息，就往数据库里存一条记录。
   *   如果是用户的第一条消息，还会自动把会话标题更新为这条消息的内容摘要。
   */
  addMessage(sessionId, role, content, intent = null) {
    // 插入消息
    const insertStmt = this.db.prepare(`
      INSERT INTO chat_messages (session_id, role, content, intent)
      VALUES (?, ?, ?, ?)
    `);
    const result = insertStmt.run(sessionId, role, content, intent);

    // 更新会话统计信息
    const session = this.getSession(sessionId);
    if (session) {
      const newCount = session.message_count + 1;
      const updates = [`message_count = ?`, `last_message_at = CURRENT_TIMESTAMP`, `updated_at = CURRENT_TIMESTAMP`];
      const params = [newCount];

      // 如果是第一条用户消息，用消息内容前30字作为标题
      if (role === "user" && session.title === "新对话" && session.message_count === 0) {
        const title = content.substring(0, 30) + (content.length > 30 ? "..." : "");
        updates.push("title = ?");
        params.push(title);
      }

      params.push(sessionId);
      const updateStmt = this.db.prepare(`
        UPDATE chat_sessions SET ${updates.join(", ")} WHERE id = ?
      `);
      updateStmt.run(...params);
    }

    return result.lastInsertRowid;
  }

  /**
   * 置顶/取消置顶会话
   *
   * 对应 Codex 的 pinned threads 功能
   *
   * @param {string} sessionId - 会话 ID
   * @param {boolean} pinned - true=置顶, false=取消置顶
   * @returns {Object} 更新后的会话对象
   *
   * 小白讲解：
   *   就像微信里的"置顶聊天"，置顶后对话会固定在列表最上面。
   *   Codex 用 Command-1~9 快捷键跳转置顶线程，我们也支持类似操作。
   */
  togglePin(sessionId, pinned = true) {
    const stmt = this.db.prepare(`
      UPDATE chat_sessions
      SET is_pinned = ?, pinned_at = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    stmt.run(pinned ? 1 : 0, pinned ? new Date().toISOString() : null, sessionId);
    return this.getSession(sessionId);
  }

  /**
   * 归档/取消归档会话
   *
   * 对应 Codex 的 archive 功能
   * 归档后从默认列表中隐藏，但可通过 status=archived 查看
   *
   * @param {string} sessionId - 会话 ID
   * @param {boolean} archived - true=归档, false=取消归档
   * @returns {Object} 更新后的会话对象
   *
   * 小白讲解：
   *   就像把不常用的微信对话"折叠"起来，不在主列表显示。
   *   但数据还在，需要的时候可以"取消归档"恢复回来。
   */
  archive(sessionId, archived = true) {
    const stmt = this.db.prepare(`
      UPDATE chat_sessions
      SET status = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    stmt.run(archived ? "archived" : "active", sessionId);
    return this.getSession(sessionId);
  }

  /**
   * 删除会话及其所有消息
   *
   * 对应 Codex 的 purge 命令（不可恢复）
   *
   * @param {string} sessionId - 会话 ID
   * @returns {boolean} 是否删除成功
   *
   * 小白讲解：
   *   就像把微信对话"删除"，对话和里面所有消息都会被清除。
   *   和归档不同，删除是不可恢复的，所以要谨慎操作。
   */
  deleteSession(sessionId) {
    // 先删除所有消息
    const deleteMsgs = this.db.prepare("DELETE FROM chat_messages WHERE session_id = ?");
    deleteMsgs.run(sessionId);

    // 再删除会话
    const deleteSession = this.db.prepare("DELETE FROM chat_sessions WHERE id = ?");
    const result = deleteSession.run(sessionId);

    return result.changes > 0;
  }

  /**
   * 更新会话标题
   *
   * @param {string} sessionId - 会话 ID
   * @param {string} title - 新标题
   * @returns {Object} 更新后的会话对象
   */
  renameSession(sessionId, title) {
    const stmt = this.db.prepare(`
      UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    `);
    stmt.run(title, sessionId);
    return this.getSession(sessionId);
  }

  /**
   * 获取统计信息
   *
   * @returns {Object} 统计数据
   */
  getStats() {
    const activeCount = this.db.prepare("SELECT COUNT(*) AS count FROM chat_sessions WHERE status = 'active'").get().count;
    const archivedCount = this.db.prepare("SELECT COUNT(*) AS count FROM chat_sessions WHERE status = 'archived'").get().count;
    const pinnedCount = this.db.prepare("SELECT COUNT(*) AS count FROM chat_sessions WHERE is_pinned = 1").get().count;
    const totalMessages = this.db.prepare("SELECT COUNT(*) AS count FROM chat_messages").get().count;

    return {
      activeSessions: activeCount,
      archivedSessions: archivedCount,
      pinnedSessions: pinnedCount,
      totalMessages,
    };
  }
}


/**
 * 创建会话管理路由
 *
 * 提供以下 API 端点（1:1 对应 Codex 的操作）：
 *   GET    /api/sessions              - 列表（支持 status/search 参数）
 *   POST   /api/sessions              - 创建新会话
 *   GET    /api/sessions/:id          - 获取单个会话信息
 *   GET    /api/sessions/:id/messages - 获取会话消息
 *   PATCH  /api/sessions/:id          - 更新会话（标题/置顶/归档）
 *   DELETE /api/sessions/:id          - 删除会话
 *   GET    /api/sessions/stats        - 统计信息
 *
 * @returns {express.Router} Express 路由
 */
export function createSessionRouter() {
  const router = express.Router();

  /**
   * GET /api/sessions - 获取会话列表
   *
   * 查询参数：
   *   status: active(默认) / archived / all
   *   search: 按标题搜索
   *   limit: 返回数量，默认 50
   */
  router.get("/api/sessions", (req, res) => {
    try {
      const session = new SessionService();
      const options = {
        status: req.query.status || "active",
        limit: parseInt(req.query.limit) || 50,
        search: req.query.search || null,
      };
      const sessions = session.listSessions(options);
      session.close();
      res.json({ success: true, sessions });
    } catch (error) {
      console.error("获取会话列表失败:", error);
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * POST /api/sessions - 创建新会话
   *
   * 请求体：
   *   title: 会话标题（可选，默认"新对话"）
   */
  router.post("/api/sessions", (req, res) => {
    try {
      const session = new SessionService();
      const { title } = req.body;
      const newSession = session.createSession(title);
      session.close();
      res.json({ success: true, session: newSession });
    } catch (error) {
      console.error("创建会话失败:", error);
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * GET /api/sessions/stats - 获取统计信息
   */
  router.get("/api/sessions/stats", (req, res) => {
    try {
      const session = new SessionService();
      const stats = session.getStats();
      session.close();
      res.json({ success: true, stats });
    } catch (error) {
      console.error("获取统计信息失败:", error);
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * GET /api/sessions/:id - 获取单个会话信息
   */
  router.get("/api/sessions/:id", (req, res) => {
    try {
      const session = new SessionService();
      const result = session.getSession(req.params.id);
      session.close();
      if (!result) {
        return res.status(404).json({ error: "会话不存在" });
      }
      res.json({ success: true, session: result });
    } catch (error) {
      console.error("获取会话失败:", error);
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * GET /api/sessions/:id/messages - 获取会话消息列表
   */
  router.get("/api/sessions/:id/messages", (req, res) => {
    try {
      const session = new SessionService();
      const messages = session.getSessionMessages(req.params.id);
      session.close();
      res.json({ success: true, messages });
    } catch (error) {
      console.error("获取会话消息失败:", error);
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * PATCH /api/sessions/:id - 更新会话
   *
   * 请求体（支持以下任意字段的组合）：
   *   title: 新标题
   *   isPinned: true/false（置顶/取消置顶）
   *   isArchived: true/false（归档/取消归档）
   */
  router.patch("/api/sessions/:id", (req, res) => {
    try {
      const svc = new SessionService();
      const { title, isPinned, isArchived } = req.body;
      let result = svc.getSession(req.params.id);

      if (!result) {
        svc.close();
        return res.status(404).json({ error: "会话不存在" });
      }

      if (title !== undefined) {
        result = svc.renameSession(req.params.id, title);
      }
      if (isPinned !== undefined) {
        result = svc.togglePin(req.params.id, isPinned);
      }
      if (isArchived !== undefined) {
        result = svc.archive(req.params.id, isArchived);
      }

      svc.close();
      res.json({ success: true, session: result });
    } catch (error) {
      console.error("更新会话失败:", error);
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * DELETE /api/sessions/:id - 删除会话
   */
  router.delete("/api/sessions/:id", (req, res) => {
    try {
      const session = new SessionService();
      const deleted = session.deleteSession(req.params.id);
      session.close();
      if (!deleted) {
        return res.status(404).json({ error: "会话不存在" });
      }
      res.json({ success: true, deleted: true });
    } catch (error) {
      console.error("删除会话失败:", error);
      res.status(500).json({ error: error.message });
    }
  });

  return router;
}
