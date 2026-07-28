/**
 * TaskGraphRegistry - 任务图注册表
 *
 * 功能说明：
 *   这是所有研究任务类型的注册中心。每个任务类型必须在此注册后才能被路由器使用。
 *   核心目标：LLM 只能选择已注册的任务图，不能任意拼接工具。
 *
 *   注册的任务包含：
 *   - id: 唯一标识（如 stock_deep_dive）
 *   - name: 中文名称
 *   - description: 描述
 *   - requiresEntity: 是否需要标的实体
 *   - defaultFlow: 默认执行流程（工具步骤序列）
 *   - allowedTools: 允许使用的工具集合
 *   - artifactType: 期望制品类型
 *   - dataRequirementTemplate: 数据需求模板
 *
 * 参数说明：
 *   register(graph) - 注册一个任务图
 *   get(id) - 按 ID 获取任务图
 *   isToolAllowed(taskId, toolName) - 检查工具是否被任务允许
 *   list() - 列出所有已注册任务
 *
 * 返回值说明：
 *   get() 返回任务图对象或 null
 *   isToolAllowed() 返回 boolean
 *   list() 返回数组
 *
 * 异常处理：
 *   重复注册抛出 Error
 */

/**
 * 小白讲解：
 *   这个文件就像一个"菜单"——系统支持的所有研究任务都在菜单上。
 *   用户说"分析海光信息"时，系统从菜单上找到"个股深度研究"这道菜，
 *   然后按照菜谱（defaultFlow）一步步做。
 *   如果 LLM 想点一道菜单上没有的菜，系统会拒绝，降级为通用聊天。
 */

/**
 * TaskGraphRegistry 类
 */
export class TaskGraphRegistry {
  constructor() {
    /** @type {Map<string, Object>} */
    this._graphs = new Map();
  }

  /**
   * 注册一个任务图
   *
   * @param {Object} graph - 任务图定义
   * @param {string} graph.id - 唯一标识
   * @param {string} graph.name - 中文名称
   * @param {string} [graph.description] - 描述
   * @param {boolean} [graph.requiresEntity] - 是否需要标的
   * @param {string[]} graph.defaultFlow - 默认执行流程
   * @param {string[]} graph.allowedTools - 允许工具集
   * @param {string} [graph.artifactType] - 制品类型
   * @param {Object} [graph.dataRequirementTemplate] - 数据需求模板
   * @throws {Error} 当 id 已存在时抛出
   */
  register(graph) {
    if (!graph || !graph.id) {
      throw new Error("Task graph must have an id");
    }
    if (this._graphs.has(graph.id)) {
      throw new Error(`Task graph "${graph.id}" is already registered`);
    }

    this._graphs.set(graph.id, {
      id: graph.id,
      name: graph.name || graph.id,
      description: graph.description || "",
      requiresEntity: graph.requiresEntity || false,
      defaultFlow: graph.defaultFlow || [],
      allowedTools: graph.allowedTools || [],
      artifactType: graph.artifactType || "text",
      dataRequirementTemplate: graph.dataRequirementTemplate || {},
    });
  }

  /**
   * 按 ID 获取任务图
   * @param {string} id - 任务图 ID
   * @returns {Object|null}
   */
  get(id) {
    return this._graphs.get(id) || null;
  }

  /**
   * 检查工具是否被任务允许
   * @param {string} taskId - 任务图 ID
   * @param {string} toolName - 工具名称
   * @returns {boolean}
   */
  isToolAllowed(taskId, toolName) {
    const graph = this.get(taskId);
    if (!graph) return false;
    return graph.allowedTools.includes(toolName);
  }

  /**
   * 列出所有已注册任务
   * @returns {Object[]}
   */
  list() {
    return Array.from(this._graphs.values());
  }

  /**
   * 检查任务是否已注册
   * @param {string} id - 任务图 ID
   * @returns {boolean}
   */
  has(id) {
    return this._graphs.has(id);
  }
}

/**
 * 创建默认注册表，包含首批 10 种任务类型
 *
 * 小白讲解：
 *   这是系统出厂自带的"菜单"。每种任务都有自己的流程和工具：
 *   - 个股深度研究：走 V3 受治理长报告流程
 *   - 经营驱动估值：取财务数据 + 确定性估值计算
 *   - 双标的换仓：取两个标的数据 + 同口径比较
 *   - 主题预期差筛选：按主题扫描候选 + 矩阵比较
 *   - 产业因果解释：取产业链和新闻 + 因果分析
 *   - 公司信号计划：取认证/产能/订单数据 + 信号生成
 *   - 事实纠错：重新取数 + 前后差异 + 依赖重算
 *   - 每日简报/组合回顾/投资论更新：保留现有流程
 *
 * @returns {TaskGraphRegistry}
 */
export function createDefaultRegistry() {
  const registry = new TaskGraphRegistry();

  // 1. 个股深度研究 V3
  registry.register({
    id: "stock_deep_dive",
    name: "个股深度研究",
    description: "对指定股票进行全面深度研究分析（V3 受治理长报告）",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "run_governed_stock_deep_dive"],
    allowedTools: ["resolve_entity", "run_governed_stock_deep_dive"],
    artifactType: "research_report",
    dataRequirementTemplate: { market: true, financial: true, news: true, valuation: true },
  });

  // 2. 经营驱动估值
  registry.register({
    id: "operating_driver_valuation",
    name: "经营驱动估值",
    description: "基于经营驱动因子构建估值模型，数值由确定性计算完成",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "get_stock_data", "run_governed_workflow"],
    allowedTools: ["resolve_entity", "get_stock_data", "run_governed_workflow"],
    artifactType: "valuation_model",
    dataRequirementTemplate: { financial: true, market: true, valuation: true },
  });

  // 3. 双标的换仓决策
  registry.register({
    id: "pair_switch_decision",
    name: "双标的换仓决策",
    description: "比较两个标的的同口径数据，生成换仓决策备忘录",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "run_governed_workflow"],
    allowedTools: ["resolve_entity", "run_governed_workflow"],
    artifactType: "comparison_matrix",
    dataRequirementTemplate: { financial: true, market: true, valuation: true },
  });

  // 4. 主题预期差筛选
  registry.register({
    id: "theme_expectation_gap",
    name: "主题预期差筛选",
    description: "按主题扫描候选标的，构建预期差矩阵",
    requiresEntity: false,
    defaultFlow: ["run_governed_workflow"],
    allowedTools: ["run_governed_workflow", "resolve_entity"],
    artifactType: "comparison_matrix",
    dataRequirementTemplate: { thematic: true, market: true, financial: true },
  });

  // 5. 产业因果解释
  registry.register({
    id: "industry_causal_explainer",
    name: "产业因果解释",
    description: "解释产业链因果关系和催化缺失",
    requiresEntity: false,
    defaultFlow: ["run_governed_workflow"],
    allowedTools: ["run_governed_workflow", "resolve_entity"],
    artifactType: "causal_chain",
    dataRequirementTemplate: { industry: true, news: true },
  });

  // 6. 公司信号计划
  registry.register({
    id: "company_signal_plan",
    name: "公司信号计划",
    description: "基于认证、产能和订单数据生成建仓信号清单",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "run_governed_workflow"],
    allowedTools: ["resolve_entity", "run_governed_workflow"],
    artifactType: "signal_plan",
    dataRequirementTemplate: { signal: true, market: true },
  });

  // 7. 事实纠错与依赖重算
  // 小白讲解：这是"纠错流程"——当用户说"不对，市值是260亿不是199亿"时，
  // 系统会：
  // 1. 定位争议主张（市值字段）
  // 2. 重新取数（从数据源查询实际值）
  // 3. 重算所有依赖项（如估值倍数）
  // 4. 生成前后差异报告
  // 5. 更新会话状态中的确认事实
  registry.register({
    id: "claim_correction",
    name: "事实纠错",
    description: "定位争议主张、重新取数、重算依赖项、生成前后差异报告",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "get_stock_data", "run_governed_workflow"],
    allowedTools: ["resolve_entity", "get_stock_data", "run_governed_workflow"],
    artifactType: "correction_diff",
    dataRequirementTemplate: { market: true, financial: true },
  });

  // 8. 每日简报
  registry.register({
    id: "daily_brief",
    name: "每日简报",
    description: "汇总当天的市场变化和研究更新",
    requiresEntity: false,
    defaultFlow: ["get_market_indices", "get_top_gainers", "get_top_losers", "get_volume_surge", "get_latest_news", "get_pool_snapshot", "get_decisions", "analyze_with_llm"],
    allowedTools: ["get_market_indices", "get_top_gainers", "get_top_losers", "get_volume_surge", "get_latest_news", "get_pool_snapshot", "get_decisions", "analyze_with_llm"],
    artifactType: "brief",
    dataRequirementTemplate: { market: true, news: true },
  });

  // 9. 组合回顾
  registry.register({
    id: "portfolio_review",
    name: "组合回顾",
    description: "回顾当前组合的表现和风险状况",
    requiresEntity: false,
    defaultFlow: ["get_pool_snapshot", "get_decisions", "get_value_score", "analyze_with_llm"],
    allowedTools: ["get_pool_snapshot", "get_decisions", "get_value_score", "analyze_with_llm"],
    artifactType: "portfolio_review",
    dataRequirementTemplate: { portfolio: true, market: true },
  });

  // 10. 投资论更新
  registry.register({
    id: "thesis_update",
    name: "投资论更新",
    description: "更新或验证投资论点",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "query_memory", "get_news", "get_stock_data", "analyze_with_llm"],
    allowedTools: ["resolve_entity", "query_memory", "get_news", "get_stock_data", "analyze_with_llm"],
    artifactType: "thesis_update",
    dataRequirementTemplate: { memory: true, news: true, market: true },
  });

  // 通用对话（兜底）
  registry.register({
    id: "chat",
    name: "自由对话",
    description: "自由聊天，降级使用",
    requiresEntity: false,
    defaultFlow: ["query_memory", "analyze_with_llm"],
    allowedTools: ["query_memory", "analyze_with_llm", "get_stock_data", "get_news", "resolve_entity"],
    artifactType: "text",
    dataRequirementTemplate: {},
  });

  return registry;
}
