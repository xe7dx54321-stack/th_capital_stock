/**
 * ResearchSessionState - 研究会话状态管理
 *
 * 功能说明：
 *   这个模块管理研究会话的状态，保存当前主题、标的、确认事实、
 *   模型假设、制品引用、待验证问题和用户纠错。
 *   核心目标是让会话刷新后能恢复任务状态，而不是依赖截断的聊天文本。
 *
 * 参数说明：
 *   constructor(sessionId) - 创建会话状态实例
 *   setCurrentTask(task) - 设置当前任务
 *   addConfirmedFact(fact) - 添加已确认事实
 *   addModelAssumption(assumption) - 添加模型假设
 *   getMemoryCandidates() - 获取可写入正式记忆的候选
 *
 * 返回值说明：
 *   serialize() 返回 JSON 字符串，可存入数据库
 *   deserialize(json) 从 JSON 恢复状态
 *
 * 异常处理：
 *   序列化/反序列化错误会抛出
 */

/**
 * 小白讲解：
 *   这个文件是"记忆笔记"的管理员。
 *   当你和系统聊天时，它会在后台默默记录：
 *   - 你刚才在看哪只股票？（实体）
 *   - 系统确认了哪些事实？（已确认事实）
 *   - 系统做了哪些假设？（模型假设）
 *   - 生成了哪些报告？（制品引用）
 *   - 还有哪些问题没解决？（待验证问题）
 *   - 你纠正了什么？（用户纠错）
 *
 *   关键是：临时假设不会写入正式记忆。
 *   就像草稿纸上的计算不会被当成最终答案。
 */

/**
 * ResearchSessionState 类
 *
 * 小白讲解：
 *   这是一个"记忆笔记本"类。
 *   每个会话都有一本笔记本，记录当前研究的全部上下文。
 */
export class ResearchSessionState {
  /**
   * 构造函数
   *
   * @param {string} sessionId - 会话唯一 ID
   */
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.createdAt = new Date().toISOString();
    this.updatedAt = this.createdAt;

    // 当前任务状态
    this.currentTask = null;

    // 会话工作记忆
    this.topic = null;                    // 当前研究主题
    this.entities = [];                   // 标的集合
    this.confirmedFacts = [];             // 已确认事实（有证据支撑）
    this.modelAssumptions = [];           // 模型假设（可能临时）
    this.artifactRefs = [];               // 制品引用（报告、模型等）
    this.pendingQuestions = [];           // 待验证问题
    this.userCorrections = [];            // 用户纠错记录
    this.dataSnapshots = {};              // 数据快照引用（按实体键存储）

    // 用户偏好（只保存明确表达的信息）
    this.userPreferences = {
      riskTolerance: null,                // 风险承受度
      researchStyle: null,                // 研究风格偏好
      holdingConstraints: [],             // 持仓约束
    };

    // 任务历史
    this.taskHistory = [];                // 已完成任务列表
  }

  // === 任务管理 ===

  /**
   * 设置当前任务
   *
   * @param {Object} task - 任务对象
   *   - taskId: 任务 ID
   *   - taskType: 任务类型
   *   - entities: 实体列表
   *   - topic: 主题
   *   - confirmedFacts: 已确认事实
   *   - modelAssumptions: 模型假设
   *   - artifactRefs: 制品引用
   *   - pendingQuestions: 待验证问题
   */
  setCurrentTask(task) {
    // 如果已有当前任务，先归档到历史
    if (this.currentTask) {
      this.taskHistory.push({
        ...this.currentTask,
        endedAt: new Date().toISOString(),
      });
    }

    this.currentTask = {
      taskId: task.taskId || this._generateTaskId(),
      taskType: task.taskType || "chat",
      entities: task.entities || [],
      topic: task.topic || null,
      confirmedFacts: task.confirmedFacts || [],
      modelAssumptions: task.modelAssumptions || [],
      artifactRefs: task.artifactRefs || [],
      pendingQuestions: task.pendingQuestions || [],
      derivedTheme: task.derivedTheme || null, // 衍生主题（用于主题筛选追问）
      correctionTarget: task.correctionTarget || null, // 纠错目标
      startedAt: new Date().toISOString(),
    };

    // 更新会话级别的实体和主题
    if (task.topic) this.topic = task.topic;
    if (task.entities && task.entities.length > 0) {
      this.entities = this._mergeEntities(this.entities, task.entities);
    }

    this.updatedAt = new Date().toISOString();
  }

  /**
   * 获取当前任务
   * @returns {Object|null}
   */
  getCurrentTask() {
    return this.currentTask;
  }

  // === 事实管理 ===

  /**
   * 添加已确认事实
   *
   * 小白讲解：已确认事实 = 有证据支撑的、可靠的数据。
   * 比如从年报里读到的收入数据。
   *
   * @param {Object} fact - 事实对象
   *   - field: 字段名
   *   - value: 值
   *   - unit: 单位
   *   - source: 来源
   *   - evidenceId: 证据 ID
   *   - asOf: 数据时点
   */
  addConfirmedFact(fact) {
    if (!fact || !fact.field) return;

    // 检查是否已存在同一字段的事实，如果是则更新
    const existingIndex = this.confirmedFacts.findIndex(
      f => f.field === fact.field && f.ticker === (fact.ticker || null)
    );

    if (existingIndex >= 0) {
      // 更新已有事实（保留历史版本）
      const oldFact = this.confirmedFacts[existingIndex];
      this.confirmedFacts[existingIndex] = {
        ...fact,
        previousValue: oldFact.value,
        updatedAt: new Date().toISOString(),
      };
    } else {
      this.confirmedFacts.push({
        ...fact,
        addedAt: new Date().toISOString(),
      });
    }

    this.updatedAt = new Date().toISOString();
  }

  // === 假设管理 ===

  /**
   * 添加模型假设
   *
   * 小白讲解：模型假设 = 系统为了计算或分析而做的推测。
   * 比如"假设明年DCU出货量50万颗"。
   * 临时假设不会进入正式记忆。
   *
   * @param {Object} assumption - 假设对象
   *   - variable: 变量名
   *   - value: 值
   *   - unit: 单位
   *   - isTemporary: 是否临时（true = 不进入正式记忆）
   *   - source: 来源（用户指定/系统推断/默认值）
   */
  addModelAssumption(assumption) {
    if (!assumption || !assumption.variable) return;

    this.modelAssumptions.push({
      ...assumption,
      addedAt: new Date().toISOString(),
    });

    this.updatedAt = new Date().toISOString();
  }

  // === 制品管理 ===

  /**
   * 添加制品引用
   * @param {string} artifactRef - 制品引用 ID 或路径
   */
  addArtifactRef(artifactRef) {
    if (!artifactRef) return;
    if (!this.artifactRefs.includes(artifactRef)) {
      this.artifactRefs.push(artifactRef);
      this.updatedAt = new Date().toISOString();
    }
  }

  // === 问题管理 ===

  /**
   * 添加待验证问题
   * @param {string} question - 问题描述
   */
  addPendingQuestion(question) {
    if (!question) return;
    if (!this.pendingQuestions.includes(question)) {
      this.pendingQuestions.push(question);
      this.updatedAt = new Date().toISOString();
    }
  }

  /**
   * 移除已解决的待验证问题
   * @param {string} question - 问题描述
   */
  resolvePendingQuestion(question) {
    this.pendingQuestions = this.pendingQuestions.filter(q => q !== question);
    this.updatedAt = new Date().toISOString();
  }

  // === 纠错管理 ===

  /**
   * 记录用户纠错
   *
   * 小白讲解：当用户说"不对，市值是260亿不是199亿"时，
   * 系统会记录这次纠错，并触发重新验证。
   *
   * @param {Object} correction - 纠错对象
   *   - field: 被纠正的字段
   *   - oldValue: 旧值
   *   - newValue: 用户声称的新值
   *   - entity: 相关实体
   *   - reason: 用户说明（可选）
   */
  addUserCorrection(correction) {
    if (!correction || !correction.field) return;

    this.userCorrections.push({
      ...correction,
      correctedAt: new Date().toISOString(),
      status: correction.status || "pending_revalidation", // pending_revalidation | revalidated | disputed
    });

    this.updatedAt = new Date().toISOString();
  }

  // === 记忆候选 ===

  /**
   * 获取可写入正式记忆的候选
   *
   * 小白讲解：这是"筛选器"——只把有价值的内容放入正式记忆。
   * 临时假设不会进入。
   *
   * @returns {Object[]} 记忆候选列表
   */
  getMemoryCandidates() {
    const candidates = [];

    // 已确认事实 → 记忆候选
    for (const fact of this.confirmedFacts) {
      if (fact.evidenceId) {
        candidates.push({
          type: "fact",
          category: "research_fact",
          content: `${fact.field}=${fact.value}${fact.unit || ""}`,
          evidenceId: fact.evidenceId,
          asOf: fact.asOf,
          source: fact.source,
        });
      }
    }

    // 非临时假设 → 记忆候选
    for (const assumption of this.modelAssumptions) {
      if (!assumption.isTemporary) {
        candidates.push({
          type: "assumption",
          category: "model_assumption",
          content: `${assumption.variable}=${assumption.value}${assumption.unit || ""}`,
          source: assumption.source,
        });
      }
    }

    // 用户明确确认的偏好 → 记忆候选
    if (this.userPreferences.riskTolerance) {
      candidates.push({
        type: "preference",
        category: "user_preference",
        content: `risk_tolerance=${this.userPreferences.riskTolerance}`,
      });
    }

    return candidates;
  }

  // === 序列化与恢复 ===

  /**
   * 序列化为 JSON
   * @returns {string} JSON 字符串
   */
  serialize() {
    return JSON.stringify({
      sessionId: this.sessionId,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      currentTask: this.currentTask,
      topic: this.topic,
      entities: this.entities,
      confirmedFacts: this.confirmedFacts,
      modelAssumptions: this.modelAssumptions,
      artifactRefs: this.artifactRefs,
      pendingQuestions: this.pendingQuestions,
      userCorrections: this.userCorrections,
      dataSnapshots: this.dataSnapshots,
      userPreferences: this.userPreferences,
      taskHistory: this.taskHistory.slice(-10), // 只保留最近10条历史
    });
  }

  /**
   * 从 JSON 恢复状态
   * @param {string} json - JSON 字符串
   */
  deserialize(json) {
    if (!json) return;

    try {
      const data = typeof json === "string" ? JSON.parse(json) : json;

      this.sessionId = data.sessionId || this.sessionId;
      this.createdAt = data.createdAt || this.createdAt;
      this.updatedAt = data.updatedAt || this.updatedAt;
      this.currentTask = data.currentTask || null;
      this.topic = data.topic || null;
      this.entities = data.entities || [];
      this.confirmedFacts = data.confirmedFacts || [];
      this.modelAssumptions = data.modelAssumptions || [];
      this.artifactRefs = data.artifactRefs || [];
      this.pendingQuestions = data.pendingQuestions || [];
      this.userCorrections = data.userCorrections || [];
      this.dataSnapshots = data.dataSnapshots || {};
      this.userPreferences = data.userPreferences || { riskTolerance: null, researchStyle: null, holdingConstraints: [] };
      this.taskHistory = data.taskHistory || [];
    } catch (error) {
      console.error("[ResearchSessionState] 反序列化失败:", error.message);
      // 失败时保持当前空状态，不抛异常
    }
  }

  // === 私有方法 ===

  /**
   * 生成任务 ID
   */
  _generateTaskId() {
    return `task_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
  }

  /**
   * 合并实体列表（去重）
   */
  _mergeEntities(existing, incoming) {
    const seen = new Set(existing.map(e => e.ticker || e.name));
    const merged = [...existing];

    for (const entity of incoming) {
      const key = entity.ticker || entity.name;
      if (key && !seen.has(key)) {
        merged.push(entity);
        seen.add(key);
      }
    }

    return merged;
  }
}

/**
 * 会话状态存储器
 *
 * 小白讲解：这个类负责把"记忆笔记本"保存到数据库，
 * 并在会话恢复时从数据库读回来。
 */
export class SessionStateStore {
  constructor(db) {
    this.db = db;
  }

  /**
   * 保存会话状态
   * @param {ResearchSessionState} state - 会话状态
   */
  async save(state) {
    if (!this.db) return;

    const sql = `
      INSERT INTO research_session_state (session_id, state_json, updated_at)
      VALUES (?, ?, ?)
      ON CONFLICT(session_id) DO UPDATE SET
        state_json = excluded.state_json,
        updated_at = excluded.updated_at
    `;

    this.db.prepare(sql).run(
      state.sessionId,
      state.serialize(),
      new Date().toISOString()
    );
  }

  /**
   * 加载会话状态
   * @param {string} sessionId - 会话 ID
   * @returns {ResearchSessionState|null}
   */
  async load(sessionId) {
    if (!this.db) return null;

    const row = this.db.prepare(
      "SELECT state_json FROM research_session_state WHERE session_id = ?"
    ).get(sessionId);

    if (!row || !row.state_json) return null;

    const state = new ResearchSessionState(sessionId);
    state.deserialize(row.state_json);
    return state;
  }

  /**
   * 删除会话状态
   * @param {string} sessionId - 会话 ID
   */
  async delete(sessionId) {
    if (!this.db) return;
    this.db.prepare("DELETE FROM research_session_state WHERE session_id = ?").run(sessionId);
  }
}
