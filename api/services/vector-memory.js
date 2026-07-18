/**
 * 向量数据库记忆系统
 * 
 * 功能：
 *   1. 向量存储 - 将文本内容转换为向量并存储到 SQLite 数据库
 *   2. 语义检索 - 根据用户查询向量查找相似内容
 *   3. 对话历史管理 - 存储和检索对话记录
 *   4. 研究报告索引 - 索引研究报告内容
 * 
 * 小白讲解：
 *   这个系统就像一个"智能大脑"——它会把研究报告、聊天记录等内容"记住"，
 *   当用户提问时，它能找到和问题最相关的历史内容，帮助 AI 给出更准确的回答。
 *   我们用 SQLite 存储向量数据，用余弦相似度来计算内容之间的相似度。
 */

import express from "express";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import { globalCacheManager, LRUCache } from "./cache.js";
import { createEmbedding as llmCreateEmbedding, isModelAvailable } from "./llm-service.js";
import pkg from "@dqbd/tiktoken";
const { encoding_for_model } = pkg;


const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_DB_PATH = path.resolve(__dirname, "..", "..", "01_data", "db", "vector.db");


/**
 * 向量存储服务
 */
export class VectorMemory {
  constructor(dbPath = DEFAULT_DB_PATH) {
    this.dbPath = dbPath;
    this.db = null;
    this.embeddingModel = "text-embedding-3-small";
    this.embeddingDimensions = 1536;
    this.tokenizer = encoding_for_model("text-embedding-3-small");
    this.embeddingCache = globalCacheManager.getCache("vector-embedding", {
      maxSize: 500,
      ttl: 30 * 60 * 1000,
    });
    this.searchCache = globalCacheManager.getCache("vector-search", {
      maxSize: 200,
      ttl: 5 * 60 * 1000,
    });
    this.init();
  }

  /**
   * 初始化数据库
   */
  init() {
    this.db = new Database(this.dbPath);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        content_type TEXT NOT NULL,
        metadata TEXT NOT NULL,
        embedding BLOB NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        intent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_embeddings_content_type ON embeddings(content_type);
      CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);
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
   * 将文本转换为向量（使用统一 LLM 服务，带缓存）
   * 
   * 参数：
   *   text: 需要转换的文本
   * 
   * 返回：
   *   Promise<number[]>: 向量数组
   */
  async createEmbedding(text) {
    const trimmed = text.trim();
    if (!trimmed) return Array(this.embeddingDimensions).fill(0);

    // 检查缓存
    const cacheKey = LRUCache.buildKey("emb", { text: trimmed });
    const cached = this.embeddingCache.get(cacheKey);
    if (cached) return cached;

    // 如果没有可用模型，返回 0 向量（降级）
    if (!isModelAvailable()) {
      console.warn("没有可用的模型，向量搜索降级为 0 向量");
      return Array(this.embeddingDimensions).fill(0);
    }

    try {
      const result = await llmCreateEmbedding(trimmed);
      const embedding = result.embedding || Array(this.embeddingDimensions).fill(0);

      // 只缓存成功的 embedding
      if (embedding.length > 0 && !embedding.every(v => v === 0)) {
        this.embeddingCache.set(cacheKey, embedding);
      }
      return embedding;
    } catch (error) {
      console.error("Embedding creation error:", error.message);
      return Array(this.embeddingDimensions).fill(0);
    }
  }

  /**
   * 计算两个向量的余弦相似度
   * 
   * 参数：
   *   vec1: 向量1
   *   vec2: 向量2
   * 
   * 返回：
   *   number: 相似度分数（0-1，越大越相似）
   */
  cosineSimilarity(vec1, vec2) {
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (let i = 0; i < vec1.length; i++) {
      dotProduct += vec1[i] * vec2[i];
      norm1 += vec1[i] * vec1[i];
      norm2 += vec2[i] * vec2[i];
    }

    const sqrt1 = Math.sqrt(norm1);
    const sqrt2 = Math.sqrt(norm2);

    if (sqrt1 === 0 || sqrt2 === 0) return 0;
    return dotProduct / (sqrt1 * sqrt2);
  }

  /**
   * 将向量转换为 Buffer
   */
  vectorToBuffer(vector) {
    const buffer = Buffer.alloc(vector.length * 4);
    for (let i = 0; i < vector.length; i++) {
      buffer.writeFloatLE(vector[i], i * 4);
    }
    return buffer;
  }

  /**
   * 将 Buffer 转换为向量
   */
  bufferToVector(buffer) {
    const vector = [];
    for (let i = 0; i < buffer.length; i += 4) {
      vector.push(buffer.readFloatLE(i));
    }
    return vector;
  }

  /**
   * 存储文本内容及其向量
   * 
   * 参数：
   *   content: 文本内容
   *   contentType: 内容类型（如 "research_report", "chat_message", "news"）
   *   metadata: 元数据（JSON 对象）
   * 
   * 返回：
   *   Promise<number>: 插入记录的 ID
   */
  async storeEmbedding(content, contentType, metadata = {}) {
    const embedding = await this.createEmbedding(content);
    
    if (embedding.length === 0 || embedding.every(v => v === 0)) {
      console.warn("Empty embedding, skipping store");
      return null;
    }

    const buffer = this.vectorToBuffer(embedding);
    const metadataJson = JSON.stringify(metadata);

    const stmt = this.db.prepare(`
      INSERT INTO embeddings (content, content_type, metadata, embedding)
      VALUES (?, ?, ?, ?)
    `);

    const result = stmt.run(content, contentType, metadataJson, buffer);
    return result.lastInsertRowid;
  }

  /**
   * 根据查询向量搜索相似内容
   * 
   * 参数：
   *   query: 查询文本
   *   contentType: 内容类型过滤（可选）
   *   limit: 返回数量（默认 5）
   *   threshold: 相似度阈值（默认 0.3）
   * 
   * 返回：
   *   Promise<array>: 相似内容列表，按相似度排序
   */
  async searchSimilar(query, options = {}) {
    const { contentType, limit = 5, threshold = 0.3 } = options;

    // 检查缓存
    const cacheKey = LRUCache.buildKey("search", { query, contentType, limit, threshold });
    const cached = this.searchCache.get(cacheKey);
    if (cached) return cached;

    const queryVector = await this.createEmbedding(query);
    if (queryVector.length === 0 || queryVector.every(v => v === 0)) {
      return [];
    }

    let sql = `SELECT id, content, content_type, metadata, embedding FROM embeddings`;
    const params = [];

    if (contentType) {
      sql += ` WHERE content_type = ?`;
      params.push(contentType);
    }

    const rows = this.db.prepare(sql).all(...params);

    const results = [];
    for (const row of rows) {
      const embedding = this.bufferToVector(row.embedding);
      const similarity = this.cosineSimilarity(queryVector, embedding);

      if (similarity >= threshold) {
        results.push({
          id: row.id,
          content: row.content,
          contentType: row.content_type,
          metadata: JSON.parse(row.metadata),
          similarity: parseFloat(similarity.toFixed(4)),
        });
      }
    }

    results.sort((a, b) => b.similarity - a.similarity);
    const sliced = results.slice(0, limit);

    // 缓存结果
    this.searchCache.set(cacheKey, sliced);

    return sliced;
  }

  /**
   * 存储对话历史
   * 
   * 参数：
   *   message: 用户消息
   *   response: AI 回复
   *   intent: 意图类型（可选）
   * 
   * 返回：
   *   number: 插入记录的 ID
   */
  storeChatHistory(message, response, intent) {
    const stmt = this.db.prepare(`
      INSERT INTO chat_history (message, response, intent)
      VALUES (?, ?, ?)
    `);

    const result = stmt.run(message, response, intent || null);
    return result.lastInsertRowid;
  }

  /**
   * 获取对话历史
   * 
   * 参数：
   *   limit: 返回数量（默认 20）
   * 
   * 返回：
   *   array: 对话历史列表
   */
  getChatHistory(limit = 20) {
    const stmt = this.db.prepare(`
      SELECT id, message, response, intent, created_at
      FROM chat_history
      ORDER BY created_at DESC
      LIMIT ?
    `);

    return stmt.all(limit).map(row => ({
      id: row.id,
      message: row.message,
      response: row.response,
      intent: row.intent,
      createdAt: row.created_at,
    }));
  }

  /**
   * 获取最近的对话上下文（用于 AI 回复时参考）
   * 
   * 参数：
   *   limit: 返回数量（默认 5）
   * 
   * 返回：
   *   array: 最近的对话列表
   */
  getRecentContext(limit = 5) {
    return this.getChatHistory(limit).reverse();
  }

  /**
   * 删除对话历史
   * 
   * 参数：
   *   id: 记录 ID（可选，不传则删除全部）
   * 
   * 返回：
   *   number: 删除的记录数
   */
  deleteChatHistory(id = null) {
    if (id) {
      const stmt = this.db.prepare("DELETE FROM chat_history WHERE id = ?");
      return stmt.run(id).changes;
    } else {
      const stmt = this.db.prepare("DELETE FROM chat_history");
      return stmt.run().changes;
    }
  }

  /**
   * 获取统计信息
   * 
   * 返回：
   *   object: 统计数据
   */
  getStats() {
    const embeddingCount = this.db.prepare("SELECT COUNT(*) AS count FROM embeddings").get().count;
    const chatCount = this.db.prepare("SELECT COUNT(*) AS count FROM chat_history").get().count;
    const types = this.db.prepare("SELECT content_type, COUNT(*) AS count FROM embeddings GROUP BY content_type").all();

    return {
      totalEmbeddings: embeddingCount,
      totalChats: chatCount,
      embeddingTypes: types,
    };
  }
}


/**
 * 创建向量数据库路由
 */
export function createVectorRouter() {
  const router = express.Router();
  const memory = new VectorMemory();

  // GET /api/vector/stats - 获取统计信息
  router.get("/api/vector/stats", (_req, res) => {
    try {
      const stats = memory.getStats();
      res.json({ ...stats, cache: globalCacheManager.getAllStats() });
    } catch (error) {
      console.error("Vector stats error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取统计信息失败" });
    }
  });

  // POST /api/vector/store - 存储内容向量
  router.post("/api/vector/store", async (req, res) => {
    try {
      const { content, contentType, metadata } = req.body;

      if (!content || typeof content !== "string") {
        return res.status(400).json({ error: "请提供 content 参数" });
      }

      if (!contentType || typeof contentType !== "string") {
        return res.status(400).json({ error: "请提供 contentType 参数" });
      }

      const id = await memory.storeEmbedding(content, contentType, metadata || {});
      res.json({ success: true, id });
    } catch (error) {
      console.error("Vector store error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "存储向量失败" });
    }
  });

  // POST /api/vector/search - 语义搜索
  router.post("/api/vector/search", async (req, res) => {
    try {
      const { query, contentType, limit, threshold } = req.body;

      if (!query || typeof query !== "string") {
        return res.status(400).json({ error: "请提供 query 参数" });
      }

      const results = await memory.searchSimilar(query, {
        contentType,
        limit: limit || 5,
        threshold: threshold || 0.3,
      });

      res.json({ success: true, results });
    } catch (error) {
      console.error("Vector search error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "搜索失败" });
    }
  });

  // POST /api/vector/chat - 存储对话历史
  router.post("/api/vector/chat", (req, res) => {
    try {
      const { message, response, intent } = req.body;

      if (!message || typeof message !== "string") {
        return res.status(400).json({ error: "请提供 message 参数" });
      }

      if (!response || typeof response !== "string") {
        return res.status(400).json({ error: "请提供 response 参数" });
      }

      const id = memory.storeChatHistory(message, response, intent);
      res.json({ success: true, id });
    } catch (error) {
      console.error("Chat history error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "存储对话历史失败" });
    }
  });

  // GET /api/vector/chat/history - 获取对话历史
  router.get("/api/vector/chat/history", (req, res) => {
    try {
      const limit = parseInt(req.query.limit) || 20;
      const history = memory.getChatHistory(limit);
      res.json({ success: true, history });
    } catch (error) {
      console.error("Chat history error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取对话历史失败" });
    }
  });

  // GET /api/vector/chat/context - 获取最近对话上下文
  router.get("/api/vector/chat/context", (req, res) => {
    try {
      const limit = parseInt(req.query.limit) || 5;
      const context = memory.getRecentContext(limit);
      res.json({ success: true, context });
    } catch (error) {
      console.error("Chat context error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取对话上下文失败" });
    }
  });

  // DELETE /api/vector/chat/history - 删除对话历史
  router.delete("/api/vector/chat/history", (req, res) => {
    try {
      const id = req.query.id ? parseInt(req.query.id) : null;
      const deleted = memory.deleteChatHistory(id);
      res.json({ success: true, deleted });
    } catch (error) {
      console.error("Delete chat history error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "删除对话历史失败" });
    }
  });

  // 关闭数据库连接（服务器关闭时调用）
  process.on("exit", () => {
    memory.close();
  });

  return router;
}
