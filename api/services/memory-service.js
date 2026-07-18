/**
 * 记忆服务 —— 让系统越用越聪明的核心
 *
 * 功能：
 *   1. 写入记忆：研究完成后，从 LLM 分析结果中自动提取关键事实，存为候选记忆
 *   2. 检索记忆：研究新标的时，自动查询相关历史记忆作为上下文
 *   3. 审核记忆：用户可以 approve/reject/archive 记忆候选
 *   4. 记忆演化：新记忆可以替代旧记忆（如估值变化），保留版本历史
 *   5. 向量联动：approved 记忆同步到向量数据库，支持语义检索
 *
 * 数据存储：
 *   - SQLite memory_items 表（MVP smr.db）—— 结构化存储，支持状态机
 *   - VectorMemory（vector.db）—— 语义检索，支持模糊匹配
 *
 * 记忆生命周期：
 *   candidate（候选）→ approved（批准）→ archived（归档）
 *                      → rejected（拒绝）
 *
 * 小白讲解：
 *   想象这个系统是一个"研究助理的笔记本"——
 *   每次研究完一只股票，助理会把关键发现记下来（候选记忆）；
 *   你审核后，有用的就批准（变成正式记忆）；
 *   下次研究同行业股票时，助理会翻看之前的笔记（检索记忆）；
 *   如果发现之前的结论过时了，会更新笔记（记忆演化）。
 */

import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import { createChatCompletion, isModelAvailable } from "./llm-service.js";
import { VectorMemory } from "./vector-memory.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// MVP smr.db 路径（记忆表在这里）
const MVP_DB_PATH = path.resolve(__dirname, "..", "..", "01_data", "db", "smr.db");

/**
 * 生成唯一ID
 * @param {string} prefix - ID 前缀
 * @returns {string} 带时间戳和随机数的唯一ID
 */
function generateId(prefix = "mem") {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * 记忆服务类
 *
 * 用法：
 *   const service = new MemoryService();
 *   await service.extractAndSaveMemories(ticker, aiAnalysis, workflowContext);
 *   const memories = service.getMemoriesForTicker("300308.SZ");
 *   service.reviewMemory(memoryId, "approve", "user", "确认有效");
 *   service.close();
 */
export class MemoryService {
  /**
   * 构造函数：打开数据库连接
   * @param {string} dbPath - MVP 数据库路径
   */
  constructor(dbPath = MVP_DB_PATH) {
    this.dbPath = dbPath;
    this.db = new Database(dbPath);
  }

  /**
   * 从 LLM 分析结果中提取关键事实，存为候选记忆
   *
   * 功能：
   *   1. 用 LLM 从分析报告中提取关键事实（如估值、增长、风险等）
   *   2. 每个事实存为一条 candidate 状态的记忆
   *   3. 同时写入向量数据库，支持语义检索
   *
   * 小白讲解：
   *   研究完一只股票后，让 AI 读一遍自己写的报告，
   *   把重要的结论提取出来，每条结论单独存一条记忆。
   *   比如提取出"PE 198倍，估值偏高"、"营收同比+192%"等。
   *
   * @param {string} ticker - 股票代码
   * @param {string} aiAnalysis - LLM 生成的分析报告全文
   * @param {object} context - 工作流上下文（含结构化数据）
   * @param {string} runId - 工作流运行ID
   * @returns {Array} 创建的记忆列表
   */
  async extractAndSaveMemories(ticker, aiAnalysis, context = {}, runId = null) {
    // 如果 LLM 不可用，用简单规则提取
    let memories = [];
    if (isModelAvailable()) {
      memories = await this._llmExtractMemories(ticker, aiAnalysis, context);
    } else {
      memories = this._ruleExtractMemories(ticker, aiAnalysis, context);
    }

    // 写入数据库
    const savedMemories = [];
    const now = new Date().toISOString();
    for (const mem of memories) {
      const memoryId = generateId("mem");
      this.db
        .prepare(
          `INSERT INTO memory_items 
           (memory_id, entity_type, entity_id, memory_type, content, status, confidence, 
            source_run_id, valid_from, created_at, updated_at, version)
           VALUES (?, ?, ?, ?, ?, 'candidate', ?, ?, ?, ?, ?, 1)`
        )
        .run(
          memoryId,
          "stock",
          ticker,
          mem.memory_type,
          mem.content,
          mem.confidence || 0.7,
          runId,
          now,
          now,
          now
        );

      savedMemories.push({ memory_id: memoryId, ...mem });
    }

    // 同步到向量数据库
    await this._syncToVector(savedMemories, ticker);

    return savedMemories;
  }

  /**
   * 用 LLM 从分析报告中提取关键事实
   *
   * @param {string} ticker - 股票代码
   * @param {string} aiAnalysis - LLM 分析报告
   * @param {object} context - 工作流上下文
   * @returns {Array} 记忆列表 [{ memory_type, content, confidence }]
   */
  async _llmExtractMemories(ticker, aiAnalysis, context) {
    const stock = context.stockEntity || {};
    const data = context.instrumentData || {};

    const systemPrompt = `你是一个信息提取助手。从股票分析报告中提取关键事实，每个事实要简洁、可验证、有价值。

提取规则：
1. 每个事实独立成一条记忆
2. 记忆类型分为：thesis（投资论点）、valuation（估值判断）、fundamental（基本面事实）、technical（技术面判断）、risk（风险因素）、event（事件影响）
3. 内容用一句话描述，包含具体数据
4. 只提取有信息价值的事实，不要提取泛泛之谈
5. 最多提取 8 条最重要的记忆

输出 JSON 数组格式：
[{"memory_type": "valuation", "content": "PE 198倍处于历史高位", "confidence": 0.8}]`;

    const userPrompt = `股票：${stock.name || ticker}（${ticker}）
行业：${stock.sector || "未知"}
最新价：${data.latestPrice || "未知"}
数据日期：${data.latestDate || "未知"}

分析报告：
${aiAnalysis}

请提取关键事实记忆。`;

    try {
      const result = await createChatCompletion(
        [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt },
        ],
        { maxTokens: 1500, temperature: 0.3 }
      );

      // 解析 LLM 返回的 JSON
      const jsonMatch = result.content.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.error("LLM 提取记忆失败，降级到规则提取:", e.message);
    }

    // 降级到规则提取
    return this._ruleExtractMemories(ticker, aiAnalysis, context);
  }

  /**
   * 用规则从分析报告和数据中提取关键事实（降级方案）
   *
   * @param {string} ticker - 股票代码
   * @param {string} aiAnalysis - 分析报告
   * @param {object} context - 工作流上下文
   * @returns {Array} 记忆列表
   */
  _ruleExtractMemories(ticker, aiAnalysis, context) {
    const memories = [];
    const data = context.instrumentData || {};
    const stock = context.stockEntity || {};

    // 估值记忆
    if (data.valuation?.pe) {
      memories.push({
        memory_type: "valuation",
        content: `${stock.name || ticker} PE(TTM) = ${data.valuation.pe.toFixed(1)}倍，数据日期 ${data.valuation.snapshotDate?.substring(0, 10) || "未知"}`,
        confidence: 0.9,
      });
    }

    // 基本面记忆
    if (data.technical?.revenueYoy != null) {
      memories.push({
        memory_type: "fundamental",
        content: `${stock.name || ticker} 营收同比 ${data.technical.revenueYoy > 0 ? "+" : ""}${data.technical.revenueYoy?.toFixed(2)}%，净利同比 ${data.technical.netProfitYoy > 0 ? "+" : ""}${data.technical.netProfitYoy?.toFixed(2)}%`,
        confidence: 0.85,
      });
    }
    if (data.technical?.grossMargin != null) {
      memories.push({
        memory_type: "fundamental",
        content: `${stock.name || ticker} 毛利率 ${data.technical.grossMargin?.toFixed(2)}%，净利率 ${data.technical.netMargin?.toFixed(2)}%`,
        confidence: 0.8,
      });
    }
    if (data.technical?.roeReported != null) {
      memories.push({
        memory_type: "fundamental",
        content: `${stock.name || ticker} ROE(报告) = ${data.technical.roeReported?.toFixed(2)}%，资产负债率 ${data.technical.debtAssetRatio?.toFixed(2)}%`,
        confidence: 0.8,
      });
    }

    // 技术面记忆
    if (data.technical?.rsi14 != null) {
      memories.push({
        memory_type: "technical",
        content: `${stock.name || ticker} 技术面：RSI(14)=${data.technical.rsi14?.toFixed(2)}，MACD HIST=${data.technical.macdHist?.toFixed(2)}，MA20=${data.technical.ma20?.toFixed(2)}，数据日期 ${data.technical.tradeDate}`,
        confidence: 0.7,
      });
    }

    // 行情记忆
    if (data.latestPrice) {
      memories.push({
        memory_type: "event",
        content: `${stock.name || ticker} 收盘价 ${data.latestPrice}（${data.latestDate}），5日涨跌 ${data.momentum?.m5d != null ? data.momentum.m5d.toFixed(2) + "%" : "无数据"}`,
        confidence: 0.9,
      });
    }

    // 新闻记忆
    const news = context.news || [];
    if (news.length > 0) {
      const topNews = news.slice(0, 2).map((n) => n.title).join("; ");
      memories.push({
        memory_type: "event",
        content: `${stock.name || ticker} 近期动态：${topNews}`,
        confidence: 0.7,
      });
    }

    return memories;
  }

  /**
   * 把记忆同步到向量数据库（支持语义检索）
   *
   * @param {Array} memories - 记忆列表
   * @param {string} ticker - 股票代码
   */
  async _syncToVector(memories, ticker) {
    if (!memories.length) return;

    const vector = new VectorMemory();
    try {
      for (const mem of memories) {
        await vector.addDocument({
          id: mem.memory_id,
          content: `[${mem.memory_type}] ${ticker}: ${mem.content}`,
          metadata: {
            ticker,
            memory_type: mem.memory_type,
            source: "research_workflow",
            created_at: new Date().toISOString(),
          },
        });
      }
    } catch (e) {
      console.error("向量同步记忆失败（不影响主流程）:", e.message);
    } finally {
      vector.close();
    }
  }

  /**
   * 查询某只股票的所有记忆
   *
   * @param {string} ticker - 股票代码
   * @param {object} options - 查询选项 { status, memoryType, limit }
   * @returns {Array} 记忆列表
   */
  getMemoriesForTicker(ticker, options = {}) {
    const { status = null, memoryType = null, limit = 20 } = options;

    let sql = `SELECT * FROM memory_items WHERE entity_id = ? OR entity_id LIKE ?`;
    const params = [ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`];

    if (status) {
      sql += ` AND status = ?`;
      params.push(status);
    }
    if (memoryType) {
      sql += ` AND memory_type = ?`;
      params.push(memoryType);
    }

    sql += ` ORDER BY created_at DESC LIMIT ?`;
    params.push(limit);

    return this.db.prepare(sql).all(...params);
  }

  /**
   * 查询某行业的所有记忆（用于同行业研究时引用）
   *
   * @param {Array} tickers - 同行业股票代码列表
   * @param {object} options - 查询选项
   * @returns {Array} 记忆列表
   */
  getMemoriesForPeerGroup(tickers, options = {}) {
    const { status = "approved", limit = 10 } = options;
    if (!tickers?.length) return [];

    const placeholders = tickers.map(() => "?").join(",");
    return this.db
      .prepare(
        `SELECT * FROM memory_items 
         WHERE entity_id IN (${placeholders}) 
         AND status = ?
         ORDER BY created_at DESC 
         LIMIT ?`
      )
      .all(...tickers, status, limit);
  }

  /**
   * 审核记忆（approve/reject/archive/supersede）
   *
   * 功能：
   *   1. 更新记忆状态
   *   2. 记录审核日志
   *   3. 如果是 supersede，创建新版本
   *
   * @param {string} memoryId - 记忆ID
   * @param {string} action - 审核动作（approve/reject/archive/supersede）
   * @param {string} reviewer - 审核人
   * @param {string} reason - 审核理由
   * @returns {object} 更新后的记忆
   */
  reviewMemory(memoryId, action, reviewer = "user", reason = "") {
    // 获取当前记忆
    const current = this.db.prepare(`SELECT * FROM memory_items WHERE memory_id = ?`).get(memoryId);
    if (!current) {
      throw new Error(`记忆 ${memoryId} 不存在`);
    }

    const statusMap = {
      approve: "approved",
      reject: "rejected",
      archive: "archived",
      supersede: "archived", // 旧记忆归档
    };

    const newStatus = statusMap[action];
    if (!newStatus) {
      throw new Error(`无效的审核动作: ${action}`);
    }

    const now = new Date().toISOString();

    // 更新记忆状态
    this.db
      .prepare(
        `UPDATE memory_items 
         SET status = ?, reviewed_by = ?, review_reason = ?, reviewed_at = ?, updated_at = ?
         WHERE memory_id = ?`
      )
      .run(newStatus, reviewer, reason, now, now, memoryId);

    // 记录审核日志
    const reviewId = generateId("rev");
    this.db
      .prepare(
        `INSERT INTO memory_review_log 
         (review_id, memory_id, action, previous_status, new_status, reviewer, reason, reviewed_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .run(reviewId, memoryId, action, current.status, newStatus, reviewer, reason, now);

    return this.db.prepare(`SELECT * FROM memory_items WHERE memory_id = ?`).get(memoryId);
  }

  /**
   * 获取所有待审核的记忆候选
   *
   * @param {number} limit - 返回数量
   * @returns {Array} 候选记忆列表
   */
  getPendingMemories(limit = 50) {
    return this.db
      .prepare(
        `SELECT * FROM memory_items 
         WHERE status = 'candidate' 
         ORDER BY created_at DESC 
         LIMIT ?`
      )
      .all(limit);
  }

  /**
   * 获取记忆统计信息
   *
   * @returns {object} { total, candidate, approved, rejected, archived, byType }
   */
  getMemoryStats() {
    const total = this.db.prepare(`SELECT COUNT(*) as c FROM memory_items`).get().c;
    const byStatus = this.db
      .prepare(
        `SELECT status, COUNT(*) as c FROM memory_items GROUP BY status`
      )
      .all()
      .reduce((acc, r) => {
        acc[r.status] = r.c;
        return acc;
      }, {});

    const byType = this.db
      .prepare(
        `SELECT memory_type, COUNT(*) as c FROM memory_items GROUP BY memory_type`
      )
      .all()
      .reduce((acc, r) => {
        acc[r.memory_type] = r.c;
        return acc;
      }, {});

    return {
      total,
      candidate: byStatus.candidate || 0,
      approved: byStatus.approved || 0,
      rejected: byStatus.rejected || 0,
      archived: byStatus.archived || 0,
      byType,
    };
  }

  /**
   * 格式化记忆列表为 LLM 可读的上下文文本
   *
   * 功能：把记忆列表转成文本，喂给 LLM 做分析时引用
   *
   * @param {Array} memories - 记忆列表
   * @returns {string} 格式化的文本
   */
  formatMemoriesAsContext(memories) {
    if (!memories?.length) return "无历史记忆";

    const typeLabels = {
      thesis: "投资论点",
      valuation: "估值判断",
      fundamental: "基本面",
      technical: "技术面",
      risk: "风险因素",
      event: "事件动态",
    };

    return memories
      .map((m, i) => {
        const label = typeLabels[m.memory_type] || m.memory_type;
        const date = m.created_at?.substring(0, 10);
        const status = m.status === "approved" ? "✓" : m.status === "candidate" ? "?" : "";
        return `${i + 1}. [${label}] ${status} ${m.content} (${date})`;
      })
      .join("\n");
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
}
