/**
 * 成长系统服务
 * 
 * 功能：
 *   1. 标的成长追踪 - 跟踪标的从候选到投资的全生命周期
 *   2. 用户研究成长 - 跟踪用户的研究活动和成长曲线
 *   3. 决策追踪 - 跟踪投资决策的结果和反馈
 *   4. 里程碑记录 - 记录重要事件和成就
 * 
 * 小白讲解：
 *   这个系统就像一个"成长日记本"——它记录每个标的从被发现到最终投资的全过程，
 *   也记录用户的研究活动和决策表现，帮助用户看到自己的成长轨迹。
 */

import express from "express";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";


const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_DB_PATH = path.resolve(__dirname, "..", "..", "01_data", "db", "growth.db");


/**
 * 成长追踪服务
 */
export class GrowthTracker {
  constructor(dbPath = DEFAULT_DB_PATH) {
    this.dbPath = dbPath;
    this.db = null;
    this.init();
  }

  /**
   * 初始化数据库
   */
  init() {
    this.db = new Database(this.dbPath);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS stock_growth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_code TEXT NOT NULL,
        name TEXT,
        sector TEXT,
        stage TEXT NOT NULL,
        stage_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS stage_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_code TEXT NOT NULL,
        stage TEXT NOT NULL,
        entered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        exited_at DATETIME,
        duration_days INTEGER,
        notes TEXT
      );

      CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_type TEXT NOT NULL,
        activity_data TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS user_milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone TEXT NOT NULL,
        achieved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        data TEXT
      );

      CREATE TABLE IF NOT EXISTS decision_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        decision_id TEXT NOT NULL,
        ts_code TEXT,
        decision_type TEXT NOT NULL,
        outcome TEXT,
        outcome_date DATETIME,
        performance REAL,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_stock_growth_ts_code ON stock_growth(ts_code);
      CREATE INDEX IF NOT EXISTS idx_stage_history_ts_code ON stage_history(ts_code);
      CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);
      CREATE INDEX IF NOT EXISTS idx_decision_tracking_ts_code ON decision_tracking(ts_code);
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
   * 标的阶段定义
   */
  STAGES = {
    DISCOVERED: "discovered",
    CANDIDATE: "candidate",
    REVIEWED: "reviewed",
    WATCHLIST: "watchlist",
    PORTFOLIO: "portfolio",
    EXITED: "exited",
  };

  /**
   * 阶段中文名映射
   */
  STAGE_LABELS = {
    discovered: "新发现",
    candidate: "候选",
    reviewed: "已评审",
    watchlist: "观察池",
    portfolio: "持仓",
    exited: "已退出",
  };

  /**
   * 更新标的阶段
   * 
   * 参数：
   *   tsCode: 股票代码
   *   stage: 新阶段
   *   name: 股票名称（可选）
   *   sector: 所属板块（可选）
   *   notes: 备注（可选）
   * 
   * 返回：
   *   number: 更新记录的 ID
   */
  updateStockStage(tsCode, stage, options = {}) {
    const { name, sector, notes } = options;

    if (!this.STAGES[stage.toUpperCase()]) {
      throw new Error(`无效的阶段: ${stage}`);
    }

    const now = new Date().toISOString();

    // 更新阶段历史
    const currentStage = this.db.prepare(
      "SELECT stage, entered_at FROM stage_history WHERE ts_code = ? AND exited_at IS NULL ORDER BY entered_at DESC LIMIT 1"
    ).get(tsCode);

    if (currentStage && currentStage.stage !== stage) {
      const enteredAt = new Date(currentStage.entered_at);
      const exitedAt = new Date(now);
      const durationDays = Math.floor((exitedAt.getTime() - enteredAt.getTime()) / (1000 * 60 * 60 * 24));

      this.db.prepare(
        "UPDATE stage_history SET exited_at = ?, duration_days = ? WHERE ts_code = ? AND exited_at IS NULL"
      ).run(now, durationDays, tsCode);
    }

    // 添加新阶段记录
    this.db.prepare(
      "INSERT INTO stage_history (ts_code, stage, notes) VALUES (?, ?, ?)"
    ).run(tsCode, stage, notes || null);

    // 更新当前状态
    const existing = this.db.prepare("SELECT id FROM stock_growth WHERE ts_code = ?").get(tsCode);

    if (existing) {
      this.db.prepare(`
        UPDATE stock_growth 
        SET stage = ?, stage_date = ?, name = COALESCE(?, name), sector = COALESCE(?, sector), notes = ?
        WHERE ts_code = ?
      `).run(stage, now, name, sector, notes, tsCode);
      return existing.id;
    } else {
      const result = this.db.prepare(`
        INSERT INTO stock_growth (ts_code, name, sector, stage, stage_date, notes)
        VALUES (?, ?, ?, ?, ?, ?)
      `).run(tsCode, name || null, sector || null, stage, now, notes || null);
      return result.lastInsertRowid;
    }
  }

  /**
   * 获取标的成长信息
   * 
   * 参数：
   *   tsCode: 股票代码（可选，不传则返回全部）
   * 
   * 返回：
   *   array: 标的成长信息列表
   */
  getStockGrowth(tsCode = null) {
    let sql = `
      SELECT sg.*, sh.stage AS current_stage, sh.entered_at AS current_stage_start
      FROM stock_growth sg
      LEFT JOIN stage_history sh ON sg.ts_code = sh.ts_code AND sh.exited_at IS NULL
    `;
    const params = [];

    if (tsCode) {
      sql += " WHERE sg.ts_code = ?";
      params.push(tsCode);
    }

    return this.db.prepare(sql).all(...params).map(row => ({
      id: row.id,
      tsCode: row.ts_code,
      name: row.name,
      sector: row.sector,
      stage: row.stage,
      stageLabel: this.STAGE_LABELS[row.stage] || row.stage,
      stageDate: row.stage_date,
      currentStageStart: row.current_stage_start,
      notes: row.notes,
      createdAt: row.created_at,
    }));
  }

  /**
   * 获取标的阶段历史
   * 
   * 参数：
   *   tsCode: 股票代码
   * 
   * 返回：
   *   array: 阶段历史列表
   */
  getStockStageHistory(tsCode) {
    return this.db.prepare(`
      SELECT id, stage, entered_at, exited_at, duration_days, notes
      FROM stage_history
      WHERE ts_code = ?
      ORDER BY entered_at DESC
    `).all(tsCode).map(row => ({
      id: row.id,
      stage: row.stage,
      stageLabel: this.STAGE_LABELS[row.stage] || row.stage,
      enteredAt: row.entered_at,
      exitedAt: row.exited_at,
      durationDays: row.duration_days,
      notes: row.notes,
    }));
  }

  /**
   * 记录用户活动
   * 
   * 参数：
   *   activityType: 活动类型（如 "research_started", "analysis_completed", "decision_made"）
   *   activityData: 活动数据（JSON 对象）
   * 
   * 返回：
   *   number: 记录 ID
   */
  recordUserActivity(activityType, activityData) {
    const dataJson = typeof activityData === "string" ? activityData : JSON.stringify(activityData);
    const result = this.db.prepare(`
      INSERT INTO user_activity (activity_type, activity_data)
      VALUES (?, ?)
    `).run(activityType, dataJson);
    return result.lastInsertRowid;
  }

  /**
   * 获取用户活动历史
   * 
   * 参数：
   *   activityType: 活动类型过滤（可选）
   *   limit: 返回数量（默认 50）
   * 
   * 返回：
   *   array: 活动历史列表
   */
  getUserActivity(activityType = null, limit = 50) {
    let sql = "SELECT id, activity_type, activity_data, timestamp FROM user_activity";
    const params = [];

    if (activityType) {
      sql += " WHERE activity_type = ?";
      params.push(activityType);
    }

    sql += " ORDER BY timestamp DESC LIMIT ?";
    params.push(limit);

    return this.db.prepare(sql).all(...params).map(row => ({
      id: row.id,
      activityType: row.activity_type,
      activityData: JSON.parse(row.activity_data),
      timestamp: row.timestamp,
    }));
  }

  /**
   * 获取用户活动统计
   * 
   * 返回：
   *   object: 活动统计数据
   */
  getUserActivityStats() {
    const total = this.db.prepare("SELECT COUNT(*) AS count FROM user_activity").get().count;
    const byType = this.db.prepare(`
      SELECT activity_type, COUNT(*) AS count 
      FROM user_activity 
      GROUP BY activity_type 
      ORDER BY count DESC
    `).all();
    const recent7Days = this.db.prepare(`
      SELECT COUNT(*) AS count 
      FROM user_activity 
      WHERE timestamp >= DATETIME('now', '-7 days')
    `).get().count;

    return {
      totalActivities: total,
      activitiesByType: byType,
      recent7DaysActivities: recent7Days,
    };
  }

  /**
   * 添加用户里程碑
   * 
   * 参数：
   *   milestone: 里程碑描述
   *   data: 相关数据（可选）
   * 
   * 返回：
   *   number: 记录 ID
   */
  addMilestone(milestone, data = null) {
    const dataJson = data ? JSON.stringify(data) : null;
    const result = this.db.prepare(`
      INSERT INTO user_milestones (milestone, data)
      VALUES (?, ?)
    `).run(milestone, dataJson);
    return result.lastInsertRowid;
  }

  /**
   * 获取用户里程碑
   * 
   * 参数：
   *   limit: 返回数量（默认 20）
   * 
   * 返回：
   *   array: 里程碑列表
   */
  getMilestones(limit = 20) {
    return this.db.prepare(`
      SELECT id, milestone, achieved_at, data
      FROM user_milestones
      ORDER BY id DESC
      LIMIT ?
    `).all(limit).map(row => ({
      id: row.id,
      milestone: row.milestone,
      achievedAt: row.achieved_at,
      data: row.data ? JSON.parse(row.data) : null,
    }));
  }

  /**
   * 记录决策追踪
   * 
   * 参数：
   *   decisionId: 决策 ID
   *   tsCode: 股票代码（可选）
   *   decisionType: 决策类型（如 "buy", "sell", "hold"）
   *   outcome: 结果（可选）
   *   performance: 表现（可选）
   *   notes: 备注（可选）
   * 
   * 返回：
   *   number: 记录 ID
   */
  recordDecision(decisionId, decisionType, options = {}) {
    const { tsCode, outcome, performance, notes } = options;

    const result = this.db.prepare(`
      INSERT INTO decision_tracking (decision_id, ts_code, decision_type, outcome, performance, notes)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(decisionId, tsCode || null, decisionType, outcome || null, performance || null, notes || null);

    return result.lastInsertRowid;
  }

  /**
   * 更新决策结果
   * 
   * 参数：
   *   decisionId: 决策 ID
   *   outcome: 结果
   *   performance: 表现（可选）
   *   notes: 备注（可选）
   * 
   * 返回：
   *   number: 更新的记录数
   */
  updateDecisionOutcome(decisionId, outcome, options = {}) {
    const { performance, notes } = options;
    const now = new Date().toISOString();

    const result = this.db.prepare(`
      UPDATE decision_tracking
      SET outcome = ?, outcome_date = ?, performance = COALESCE(?, performance), notes = COALESCE(?, notes)
      WHERE decision_id = ?
    `).run(outcome, now, performance, notes, decisionId);

    return result.changes;
  }

  /**
   * 获取决策追踪记录
   * 
   * 参数：
   *   tsCode: 股票代码过滤（可选）
   *   limit: 返回数量（默认 20）
   * 
   * 返回：
   *   array: 决策记录列表
   */
  getDecisionTracking(tsCode = null, limit = 20) {
    let sql = `
      SELECT id, decision_id, ts_code, decision_type, outcome, outcome_date, performance, notes, created_at
      FROM decision_tracking
    `;
    const params = [];

    if (tsCode) {
      sql += " WHERE ts_code = ?";
      params.push(tsCode);
    }

    sql += " ORDER BY created_at DESC LIMIT ?";
    params.push(limit);

    return this.db.prepare(sql).all(...params).map(row => ({
      id: row.id,
      decisionId: row.decision_id,
      tsCode: row.ts_code,
      decisionType: row.decision_type,
      outcome: row.outcome,
      outcomeDate: row.outcome_date,
      performance: row.performance,
      notes: row.notes,
      createdAt: row.created_at,
    }));
  }

  /**
   * 获取决策统计
   * 
   * 返回：
   *   object: 决策统计数据
   */
  getDecisionStats() {
    const total = this.db.prepare("SELECT COUNT(*) AS count FROM decision_tracking").get().count;
    const withOutcome = this.db.prepare("SELECT COUNT(*) AS count FROM decision_tracking WHERE outcome IS NOT NULL").get().count;
    const byType = this.db.prepare(`
      SELECT decision_type, COUNT(*) AS count 
      FROM decision_tracking 
      GROUP BY decision_type
    `).all();

    const avgPerformance = this.db.prepare(`
      SELECT AVG(performance) AS avg 
      FROM decision_tracking 
      WHERE performance IS NOT NULL
    `).get().avg;

    return {
      totalDecisions: total,
      decisionsWithOutcome: withOutcome,
      decisionsByType: byType,
      avgPerformance: avgPerformance ? parseFloat(avgPerformance.toFixed(2)) : null,
    };
  }

  /**
   * 获取成长系统统计概览
   * 
   * 返回：
   *   object: 完整统计数据
   */
  getGrowthOverview() {
    const stockStats = this.db.prepare(`
      SELECT stage, COUNT(*) AS count 
      FROM stock_growth 
      GROUP BY stage
    `).all();

    return {
      stockGrowth: stockStats.map(row => ({
        stage: row.stage,
        stageLabel: this.STAGE_LABELS[row.stage] || row.stage,
        count: row.count,
      })),
      ...this.getUserActivityStats(),
      ...this.getDecisionStats(),
    };
  }
}


/**
 * 创建成长系统路由
 */
export function createGrowthRouter() {
  const router = express.Router();
  const tracker = new GrowthTracker();

  // GET /api/growth/overview - 获取成长概览
  router.get("/api/growth/overview", (_req, res) => {
    try {
      const overview = tracker.getGrowthOverview();
      res.json({ success: true, overview });
    } catch (error) {
      console.error("Growth overview error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取成长概览失败" });
    }
  });

  // GET /api/growth/stock - 获取标的成长信息
  router.get("/api/growth/stock", (req, res) => {
    try {
      const tsCode = req.query.tsCode || null;
      const result = tracker.getStockGrowth(tsCode);
      res.json({ success: true, data: result });
    } catch (error) {
      console.error("Stock growth error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取标的成长信息失败" });
    }
  });

  // POST /api/growth/stock/stage - 更新标的阶段
  router.post("/api/growth/stock/stage", (req, res) => {
    try {
      const { tsCode, stage, name, sector, notes } = req.body;

      if (!tsCode || typeof tsCode !== "string") {
        return res.status(400).json({ error: "请提供 tsCode 参数" });
      }

      if (!stage || typeof stage !== "string") {
        return res.status(400).json({ error: "请提供 stage 参数" });
      }

      const id = tracker.updateStockStage(tsCode, stage, { name, sector, notes });
      res.json({ success: true, id });
    } catch (error) {
      console.error("Update stock stage error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "更新标的阶段失败" });
    }
  });

  // GET /api/growth/stock/:tsCode/history - 获取标的阶段历史
  router.get("/api/growth/stock/:tsCode/history", (req, res) => {
    try {
      const history = tracker.getStockStageHistory(req.params.tsCode);
      res.json({ success: true, history });
    } catch (error) {
      console.error("Stage history error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取阶段历史失败" });
    }
  });

  // POST /api/growth/activity - 记录用户活动
  router.post("/api/growth/activity", (req, res) => {
    try {
      const { activityType, activityData } = req.body;

      if (!activityType || typeof activityType !== "string") {
        return res.status(400).json({ error: "请提供 activityType 参数" });
      }

      if (!activityData) {
        return res.status(400).json({ error: "请提供 activityData 参数" });
      }

      const id = tracker.recordUserActivity(activityType, activityData);
      res.json({ success: true, id });
    } catch (error) {
      console.error("Record activity error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "记录活动失败" });
    }
  });

  // GET /api/growth/activity - 获取用户活动
  router.get("/api/growth/activity", (req, res) => {
    try {
      const activityType = req.query.activityType || null;
      const limit = parseInt(req.query.limit) || 50;
      const activity = tracker.getUserActivity(activityType, limit);
      res.json({ success: true, activity });
    } catch (error) {
      console.error("Get activity error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取活动失败" });
    }
  });

  // GET /api/growth/activity/stats - 获取活动统计
  router.get("/api/growth/activity/stats", (_req, res) => {
    try {
      const stats = tracker.getUserActivityStats();
      res.json({ success: true, stats });
    } catch (error) {
      console.error("Activity stats error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取活动统计失败" });
    }
  });

  // POST /api/growth/milestone - 添加里程碑
  router.post("/api/growth/milestone", (req, res) => {
    try {
      const { milestone, data } = req.body;

      if (!milestone || typeof milestone !== "string") {
        return res.status(400).json({ error: "请提供 milestone 参数" });
      }

      const id = tracker.addMilestone(milestone, data);
      res.json({ success: true, id });
    } catch (error) {
      console.error("Add milestone error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "添加里程碑失败" });
    }
  });

  // GET /api/growth/milestones - 获取里程碑列表
  router.get("/api/growth/milestones", (req, res) => {
    try {
      const limit = parseInt(req.query.limit) || 20;
      const milestones = tracker.getMilestones(limit);
      res.json({ success: true, milestones });
    } catch (error) {
      console.error("Get milestones error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取里程碑失败" });
    }
  });

  // POST /api/growth/decision - 记录决策
  router.post("/api/growth/decision", (req, res) => {
    try {
      const { decisionId, tsCode, decisionType, outcome, performance, notes } = req.body;

      if (!decisionId || typeof decisionId !== "string") {
        return res.status(400).json({ error: "请提供 decisionId 参数" });
      }

      if (!decisionType || typeof decisionType !== "string") {
        return res.status(400).json({ error: "请提供 decisionType 参数" });
      }

      const id = tracker.recordDecision(decisionId, decisionType, { tsCode, outcome, performance, notes });
      res.json({ success: true, id });
    } catch (error) {
      console.error("Record decision error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "记录决策失败" });
    }
  });

  // PUT /api/growth/decision/outcome - 更新决策结果
  router.put("/api/growth/decision/outcome", (req, res) => {
    try {
      const { decisionId, outcome, performance, notes } = req.body;

      if (!decisionId || typeof decisionId !== "string") {
        return res.status(400).json({ error: "请提供 decisionId 参数" });
      }

      if (!outcome || typeof outcome !== "string") {
        return res.status(400).json({ error: "请提供 outcome 参数" });
      }

      const changed = tracker.updateDecisionOutcome(decisionId, outcome, { performance, notes });
      res.json({ success: true, changed });
    } catch (error) {
      console.error("Update decision outcome error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "更新决策结果失败" });
    }
  });

  // GET /api/growth/decisions - 获取决策记录
  router.get("/api/growth/decisions", (req, res) => {
    try {
      const tsCode = req.query.tsCode || null;
      const limit = parseInt(req.query.limit) || 20;
      const decisions = tracker.getDecisionTracking(tsCode, limit);
      res.json({ success: true, decisions });
    } catch (error) {
      console.error("Get decisions error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取决策记录失败" });
    }
  });

  // GET /api/growth/decisions/stats - 获取决策统计
  router.get("/api/growth/decisions/stats", (_req, res) => {
    try {
      const stats = tracker.getDecisionStats();
      res.json({ success: true, stats });
    } catch (error) {
      console.error("Decision stats error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "获取决策统计失败" });
    }
  });

  // 获取阶段定义
  router.get("/api/growth/stages", (_req, res) => {
    res.json({ success: true, stages: tracker.STAGES, labels: tracker.STAGE_LABELS });
  });

  // 关闭数据库连接
  process.on("exit", () => {
    tracker.close();
  });

  return router;
}
