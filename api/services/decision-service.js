/**
 * 决策服务 —— 投资决策的完整生命周期管理
 *
 * 功能：
 *   1. 创建决策：研究工作流完成后，LLM 生成投资建议（买入/卖出/观察），记录为决策
 *   2. 跟踪结果：定时回填决策后 1天/1周/1月/3月 的价格表现
 *   3. 复盘学习：对比"当时判断"和"后来发生"，记录论点是否被验证
 *   4. 决策关联：把决策与当时的研究记忆、证据关联，形成完整追溯链
 *
 * 决策生命周期：
 *   open（进行中）→ confirmed（论点验证） / failed（论点失败） / expired（已过期）
 *
 * 小白讲解：
 *   想象这个系统是一个"投资日记本"——
 *   每次研究完一只股票，你写下"我认为该买入，理由是XXX"；
 *   过了 1 天/1 周/1 个月后，系统自动回填当时的股价；
 *   你可以复盘：当时的判断对不对？理由还成立吗？
 *   日积月累，你会发现自己判断的盲区，越用越准。
 */

import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import { createChatCompletion, isModelAvailable } from "./llm-service.js";
import { MarketDataService } from "./market-data-service.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MVP_DB_PATH = path.resolve(__dirname, "..", "..", "01_data", "db", "smr.db");

/**
 * 生成唯一决策ID
 * @returns {string} 带时间戳的决策ID
 */
function generateDecisionId() {
  return `decision_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * 决策服务类
 *
 * 用法：
 *   const service = new DecisionService();
 *   const decision = service.createDecision({ ticker, action, thesis, ... });
 *   service.updateOutcome(decisionId);  // 回填价格结果
 *   service.reviewDecision(decisionId, { thesisConfirmed: true, ... });
 *   service.close();
 */
export class DecisionService {
  /**
   * 构造函数
   * @param {string} dbPath - MVP 数据库路径
   */
  constructor(dbPath = MVP_DB_PATH) {
    this.dbPath = dbPath;
    this.db = new Database(dbPath);
  }

  /**
   * 创建一条投资决策
   *
   * 功能：把研究工作流的投资建议存为一条正式决策记录，
   *       包含论点、证据、止损条件、参考价格等。
   *
   * @param {object} params - 决策参数
   * @param {string} params.ticker - 股票代码
   * @param {string} params.action - 操作方向：buy / sell / watch / reduce
   * @param {string} params.thesisSummary - 投资论点摘要
   * @param {string} params.bearCaseSummary - 反方论点
   * @param {number} params.referencePrice - 参考价格
   * @param {string} params.killConditions - 止损/kill 条件 JSON
   * @param {string} params.sourceRunId - 来源工作流ID
   * @param {Array} params.evidenceIds - 关联证据ID列表
   * @param {Array} params.memoryIds - 关联记忆ID列表
   * @returns {object} 创建的决策记录
   */
  createDecision({
    ticker,
    action,
    thesisSummary,
    bearCaseSummary = null,
    referencePrice = null,
    killConditions = [],
    sourceRunId = null,
    evidenceIds = [],
    memoryIds = [],
    suggestedPositionPct = null,
    maxPositionPct = null,
  }) {
    const decisionId = generateDecisionId();
    const now = new Date().toISOString();

    // 设置复盘到期日（默认 30 天后）
    const reviewDueAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

    this.db
      .prepare(
        `INSERT INTO decision_ledger 
         (decision_id, recommendation_id, ticker, action, status, decision_time,
          reference_price, currency, thesis_summary, bear_case_summary,
          kill_conditions_json, evidence_ids_json, risk_notes,
          suggested_position_pct, max_position_pct,
          human_review_status, outcome_status,
          source_run_id, review_due_at,
          metadata_json, created_at, updated_at)
         VALUES (?, ?, ?, ?, 'open', ?, ?, 'CNY', ?, ?, ?, ?, ?, ?, ?, 'pending', 'open', ?, ?, ?, ?, ?)`
      )
      .run(
        decisionId,
        decisionId, // recommendation_id 复用 decision_id
        ticker,
        action,
        now,
        referencePrice,
        thesisSummary,
        bearCaseSummary,
        JSON.stringify(killConditions),
        JSON.stringify(evidenceIds),
        `关联记忆: ${memoryIds.join(", ") || "无"}`,
        suggestedPositionPct,
        maxPositionPct,
        sourceRunId,
        reviewDueAt,
        JSON.stringify({ memoryIds, createdAt: now }),
        now,
        now
      );

    return this.db.prepare(`SELECT * FROM decision_ledger WHERE decision_id = ?`).get(decisionId);
  }

  /**
   * 用 LLM 从研究报告中提取投资决策建议
   *
   * 功能：把研究报告喂给 LLM，让它生成结构化的投资建议
   *
   * @param {string} ticker - 股票代码
   * @param {string} aiAnalysis - LLM 研究报告全文
   * @param {object} context - 工作流上下文（含价格等数据）
   * @returns {object} 结构化决策建议
   */
  async generateDecisionFromAnalysis(ticker, aiAnalysis, context = {}) {
    if (!isModelAvailable()) {
      return this._ruleBasedDecision(ticker, aiAnalysis, context);
    }

    const stock = context.stockEntity || {};
    const data = context.instrumentData || {};

    const systemPrompt = `你是一位严谨的投资决策委员会成员。基于研究报告，给出结构化的投资决策建议。

输出要求（JSON 格式）：
{
  "action": "buy|sell|watch|reduce",
  "confidence": 0.0-1.0,
  "thesis_summary": "一句话核心论点（50字以内）",
  "bear_case_summary": "最大的反方论点（50字以内）",
  "kill_conditions": ["止损条件1", "止损条件2"],
  "suggested_position_pct": 0-100,
  "time_horizon": "短期|中期|长期",
  "key_risks": ["风险1", "风险2"]
}

决策标准：
- buy: 估值合理+基本面强劲+技术面支撑
- watch: 有亮点但存在不确定性，需观察
- reduce: 估值过高或基本面恶化
- sell: 明确的下行信号`;

    const userPrompt = `股票：${stock.name || ticker}（${ticker}）
最新价：${data.latestPrice || "未知"}
PE：${data.valuation?.pe || "未知"}
RSI：${data.technical?.rsi14 || "未知"}

研究报告摘要：
${aiAnalysis?.substring(0, 2000) || "无报告"}

请给出投资决策建议。`;

    try {
      const result = await createChatCompletion(
        [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt },
        ],
        { maxTokens: 800, temperature: 0.4 }
      );

      const jsonMatch = result.content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.error("LLM 决策生成失败，降级到规则:", e.message);
    }

    return this._ruleBasedDecision(ticker, aiAnalysis, context);
  }

  /**
   * 基于规则的决策建议（降级方案，LLM 不可用时使用）
   */
  _ruleBasedDecision(ticker, aiAnalysis, context = {}) {
    const data = context.instrumentData || {};
    const stock = context.stockEntity || {};

    const pe = data.valuation?.pe;
    const rsi = data.technical?.rsi14;
    const revenueYoy = data.technical?.revenueYoy;

    let action = "watch";
    let confidence = 0.5;
    const killConditions = [];
    const risks = [];

    // 简单规则：PE 高 + RSI 低 = 观望
    if (pe && pe > 100) {
      action = "watch";
      confidence = 0.4;
      risks.push("估值偏高");
      killConditions.push("PE 回落至 50 倍以下");
    } else if (pe && pe < 20 && revenueYoy > 0) {
      action = "buy";
      confidence = 0.7;
      killConditions.push("营收同比转负");
    }

    if (rsi && rsi < 30) {
      risks.push("技术面超卖");
      killConditions.push("RSI 低于 20");
    }

    return {
      action,
      confidence,
      thesis_summary: `${stock.name || ticker} PE=${pe?.toFixed(1) || "N/A"}，营收同比=${revenueYoy?.toFixed(1) || "N/A"}%`,
      bear_case_summary: risks[0] || "市场系统性风险",
      kill_conditions: killConditions,
      suggested_position_pct: action === "buy" ? 5 : 0,
      time_horizon: "中期",
      key_risks: risks,
    };
  }

  /**
   * 回填决策的价格结果
   *
   * 功能：查询决策后 1天/1周/1月/3月 的实际价格，更新到决策记录
   *
   * @param {string} decisionId - 决策ID
   * @returns {object} 更新后的决策记录
   */
  updateOutcome(decisionId) {
    const decision = this.db.prepare(`SELECT * FROM decision_ledger WHERE decision_id = ?`).get(decisionId);
    if (!decision) throw new Error(`决策 ${decisionId} 不存在`);

    const marketService = new MarketDataService();
    try {
      // 获取决策后的日线数据
      const bars = marketService.getDailyBars(decision.ticker, 90);

      if (!bars.length) {
        return { ...decision, outcomeUpdateStatus: "no_price_data" };
      }

      // 找到决策日附近的行情
      const decisionDate = decision.decision_time?.substring(0, 10);
      const decisionBar = bars.find((b) => b.trade_date <= decisionDate) || bars[bars.length - 1];
      const refPrice = decision.reference_price || decisionBar?.close;

      // 计算决策后 1天/1周/1月/3月 的价格
      const sortedBars = [...bars].reverse(); // 从旧到新
      const decisionIdx = sortedBars.findIndex((b) => b.trade_date <= decisionDate);
      if (decisionIdx === -1) return { ...decision, outcomeUpdateStatus: "no_match" };

      const price1d = sortedBars[decisionIdx + 1]?.close || null;
      const price1w = sortedBars[decisionIdx + 5]?.close || null;
      const price1m = sortedBars[decisionIdx + 20]?.close || null;
      const price3m = sortedBars[decisionIdx + 60]?.close || null;

      // 判断论点是否被验证（简单规则：buy 且价格上涨 = confirmed）
      let thesisConfirmed = null;
      let outcomeStatus = "open";

      if (price1m != null && refPrice) {
        const return1m = (price1m - refPrice) / refPrice;
        if (decision.action === "buy" || decision.action === "watch") {
          thesisConfirmed = return1m > 0.05 ? 1 : return1m < -0.1 ? 0 : null;
        } else if (decision.action === "sell" || decision.action === "reduce") {
          thesisConfirmed = return1m < -0.05 ? 1 : return1m > 0.1 ? 0 : null;
        }
        outcomeStatus = thesisConfirmed !== null ? (thesisConfirmed ? "confirmed" : "failed") : "open";
      }

      // 如果超过 3 个月，标记为 expired
      const decisionAge = (Date.now() - new Date(decision.decision_time).getTime()) / (1000 * 60 * 60 * 24);
      if (decisionAge > 90 && outcomeStatus === "open") {
        outcomeStatus = "expired";
      }

      const now = new Date().toISOString();
      this.db
        .prepare(
          `UPDATE decision_ledger 
           SET outcome_price_1d = ?, outcome_price_1w = ?, outcome_price_1m = ?, outcome_price_3m = ?,
               thesis_confirmed = ?, outcome_status = ?, performance_update_status = 'updated',
               updated_at = ?, outcome_recorded_at = ?
           WHERE decision_id = ?`
        )
        .run(price1d, price1w, price1m, price3m, thesisConfirmed, outcomeStatus, now, now, decisionId);

      return this.db.prepare(`SELECT * FROM decision_ledger WHERE decision_id = ?`).get(decisionId);
    } finally {
      marketService.close();
    }
  }

  /**
   * 人工复盘决策
   *
   * 功能：用户查看决策结果后，写下复盘结论
   *
   * @param {string} decisionId - 决策ID
   * @param {object} review - 复盘内容 { thesisConfirmed, outcomeSummary, failureReason, reviewer }
   * @returns {object} 更新后的决策记录
   */
  reviewDecision(decisionId, { thesisConfirmed, outcomeSummary, failureReason, reviewer = "user" }) {
    const decision = this.db.prepare(`SELECT * FROM decision_ledger WHERE decision_id = ?`).get(decisionId);
    if (!decision) throw new Error(`决策 ${decisionId} 不存在`);

    const now = new Date().toISOString();
    const outcomeStatus = thesisConfirmed ? "confirmed" : "failed";

    this.db
      .prepare(
        `UPDATE decision_ledger 
         SET thesis_confirmed = ?, outcome_status = ?, outcome_summary = ?, failure_reason = ?,
             human_review_status = 'reviewed', reviewer = ?, review_comment = ?,
             updated_at = ?, outcome_recorded_at = ?
         WHERE decision_id = ?`
      )
      .run(
        thesisConfirmed ? 1 : 0,
        outcomeStatus,
        outcomeSummary || "",
        failureReason || "",
        reviewer,
        outcomeSummary || "",
        now,
        now,
        decisionId
      );

    return this.db.prepare(`SELECT * FROM decision_ledger WHERE decision_id = ?`).get(decisionId);
  }

  /**
   * 查询决策列表
   *
   * @param {object} options - 查询选项 { ticker, status, action, limit }
   * @returns {Array} 决策列表
   */
  getDecisions(options = {}) {
    const { ticker, status, action, limit = 20 } = options;
    let sql = `SELECT * FROM decision_ledger WHERE 1=1`;
    const params = [];

    if (ticker) {
      sql += ` AND (ticker = ? OR ticker LIKE ?)`;
      params.push(ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`);
    }
    if (status) {
      sql += ` AND outcome_status = ?`;
      params.push(status);
    }
    if (action) {
      sql += ` AND action = ?`;
      params.push(action);
    }

    sql += ` ORDER BY decision_time DESC LIMIT ?`;
    params.push(limit);

    return this.db.prepare(sql).all(...params);
  }

  /**
   * 获取待复盘的决策（到期但未复盘的）
   *
   * @param {number} limit - 返回数量
   * @returns {Array} 待复盘决策列表
   */
  getPendingReviews(limit = 20) {
    return this.db
      .prepare(
        `SELECT * FROM decision_ledger 
         WHERE outcome_status = 'open' 
         AND review_due_at < ? 
         ORDER BY review_due_at ASC 
         LIMIT ?`
      )
      .all(new Date().toISOString(), limit);
  }

  /**
   * 获取决策统计
   *
   * @returns {object} { total, open, confirmed, failed, expired, confirmedRate }
   */
  getStats() {
    const total = this.db.prepare(`SELECT COUNT(*) as c FROM decision_ledger`).get().c;
    const byStatus = this.db
      .prepare(`SELECT outcome_status, COUNT(*) as c FROM decision_ledger GROUP BY outcome_status`)
      .all()
      .reduce((acc, r) => {
        acc[r.outcome_status] = r.c;
        return acc;
      }, {});

    const confirmed = byStatus.confirmed || 0;
    const failed = byStatus.failed || 0;
    const reviewed = confirmed + failed;

    return {
      total,
      open: byStatus.open || 0,
      confirmed,
      failed,
      expired: byStatus.expired || 0,
      confirmedRate: reviewed > 0 ? (confirmed / reviewed * 100).toFixed(1) + "%" : "N/A",
    };
  }

  /**
   * 批量回填所有待更新决策的价格结果
   *
   * @returns {Array} 更新结果
   */
  batchUpdateOutcomes() {
    const pending = this.db
      .prepare(
        `SELECT decision_id FROM decision_ledger 
         WHERE outcome_status = 'open' 
         AND performance_update_status IS NULL OR performance_update_status != 'updated'`
      )
      .all();

    const results = [];
    for (const { decision_id } of pending) {
      try {
        const updated = this.updateOutcome(decision_id);
        results.push({ decisionId: decision_id, success: true, status: updated.outcome_status });
      } catch (e) {
        results.push({ decisionId: decision_id, success: false, error: e.message });
      }
    }
    return results;
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
