/**
 * ResearchTaskEnvelope 契约与任务关系解析
 *
 * 功能说明：
 *   这个模块定义了研究任务信封（Envelope）的契约，以及追问关系解析器。
 *   核心目标是让多轮对话中的"继续""那第二个呢""你刚才说..."等追问
 *   不再是通用聊天，而是能继承上一轮的研究上下文。
 *
 * 参数说明：
 *   validateTaskEnvelope(envelope) - 验证信封是否合法
 *   resolveTaskRelation(userInput, previousTask) - 解析用户输入与上轮任务的关系
 *
 * 返回值说明：
 *   validateTaskEnvelope 返回 { valid: boolean, taskType: string, errors: string[] }
 *   resolveTaskRelation 返回 ResearchTaskEnvelope 对象
 *
 * 异常处理：
 *   非法信封抛出 ValidationError（包含错误信息）
 */

/**
 * 小白讲解：
 *   这个文件是"任务信封"的检验员和"追问关系"的翻译官。
 *   当你说"继续"时，它知道你不是在闲聊，而是想让上一轮的研究继续进行。
 *   当你说"那第二个呢"时，它知道你想换到上一轮提到的第二个股票。
 *   当你说"不对，市值不是199亿是260亿"时，它知道你要纠错，
 *   并触发一个专门的纠错流程来重新验证数据。
 */

// === 合法的任务类型 ===
// 小白讲解：这里列出了系统支持的所有研究任务。
// 每个任务对应不同的研究流程和输出格式。
const VALID_TASK_TYPES = new Set([
  "chat",                          // 通用对话（最低优先级，不应该把追问误判为这个）
  "stock_deep_dive",               // 个股深度研究 V3（受治理长报告）
  "operating_driver_valuation",    // 经营驱动估值模型
  "pair_switch_decision",          // 双标的换仓决策
  "theme_expectation_gap",         // 主题预期差筛选
  "industry_causal_explainer",     // 产业因果解释
  "company_signal_plan",           // 公司信号计划
  "claim_correction",              // 事实纠错
  "daily_brief",                   // 每日简报
  "portfolio_review",              // 组合回顾
  "thesis_update",                 // 观点更新
  "opportunity_scan",              // 机会扫描
  "risk_analysis",                 // 风险分析
  "market_attribution",            // 市场归因
  "multi_stock_comparison",        // 多标比较
]);

// === 合法的任务关系类型 ===
// 小白讲解：每次对话不是孤立的。当前这句话和上一轮的关系有四种：
// - continue: "继续"——接着上一轮的话题
// - derive: "那第二个呢"——从上一轮衍生出新问题
// - correct: "不对，市值是260亿"——纠正上一轮的错误
// - new_task: "帮我看看新易盛"——全新的独立任务
const VALID_RELATIONS = new Set(["continue", "derive", "correct", "new_task"]);

// === 追问关键词到关系类型的映射 ===
// 小白讲解：这是"追问探测器"的词典。
// 当用户说这些词时，系统就知道是在追问，而不是提新问题。
const FOLLOW_UP_KEYWORDS = [
  // 继续类 → continue
  { pattern: /^(继续|接着|往下)(说|讲|输出|分析|详细|展开|往下|往下说|往下讲)?$/i, relation: "continue" },
  { pattern: /^(继续输出|继续分析|继续讲|继续展开|继续详细)$/i, relation: "continue" },
  { pattern: /^(没说完|没讲完|没输出完|补充一下|补充|展开|详细|详细说|详细讲)$/i, relation: "continue" },
  { pattern: /^(然后呢|还有呢|后面呢|再说|再讲|再详细|再展开)$/i, relation: "continue" },

  // 指代类 → derive（可能继承实体或主题）
  { pattern: /^(那它呢|那这个呢|那这只呢|那这只股票呢|那这家公司呢)$/i, relation: "derive" },
  { pattern: /^那(.*)呢$/i, relation: "derive" },  // "那海光呢" "那超节点呢"
  { pattern: /^(第二个|第三个|第一只|第二只|另一只|别的呢|还有谁|还有哪家|别的公司|别的股票)$/i, relation: "derive" },

  // 纠错类 → correct
  { pattern: /^(不对|错了|不是|应该是|不是.*是|你错了|你说错了|搞错了)/i, relation: "correct" },
  { pattern: /^(不对|不是).*(亿|万|元|元|pct|%|倍)/i, relation: "correct" },
  { pattern: /^(市值|收入|利润|营收|EPS|PE|PB).*(是|为).*(不是|不对|错了)/i, relation: "correct" },

  // 指代上文 → continue（包含"刚才/上面/之前"）
  { pattern: /^(上面|刚才|之前|上一轮|上一轮对话)/i, relation: "continue" },
  { pattern: /^(你刚才说|你上面说|你之前说|你之前提到)/i, relation: "continue" },
];

/**
 * 验证任务信封是否合法
 *
 * @param {Object} envelope - 任务信封对象
 * @returns {Object} { valid: boolean, taskType: string, errors: string[] }
 * @throws {Error} 当信封包含非法值时抛出
 */
export function validateTaskEnvelope(envelope) {
  if (!envelope || typeof envelope !== "object") {
    throw new Error("Envelope must be a non-null object");
  }

  const errors = [];

  // 验证 task_type
  if (!envelope.task_type) {
    errors.push("task_type is required");
  } else if (!VALID_TASK_TYPES.has(envelope.task_type)) {
    errors.push(`unknown task type: ${envelope.task_type}`);
  }

  // 验证 entities（研究类任务必须有实体）
  const isResearchTask = envelope.task_type && envelope.task_type !== "chat";
  if (isResearchTask) {
    if (!Array.isArray(envelope.entities) || envelope.entities.length === 0) {
      errors.push("empty entities: research tasks require at least one entity");
    }
  }

  // 验证 relation_to_previous
  if (!envelope.relation_to_previous) {
    errors.push("relation_to_previous is required");
  } else if (!VALID_RELATIONS.has(envelope.relation_to_previous)) {
    errors.push(`invalid relation: ${envelope.relation_to_previous}`);
  }

  // 如果关系是 continue/derive/correct，需要 parent_task_id
  const needsParent = ["continue", "derive", "correct"].includes(envelope.relation_to_previous);
  if (needsParent && !envelope.parent_task_id) {
    // 这是一个警告级别的信息，不一定致命
    errors.push("parent_task_id recommended for continue/derive/correct relations");
  }

  if (errors.length > 0) {
    const errorMessage = errors.join("; ");
    const error = new Error(errorMessage);
    error.validationErrors = errors;
    throw error;
  }

  return {
    valid: true,
    taskType: envelope.task_type,
    errors: [],
  };
}

/**
 * 解析用户输入与上轮任务的关系
 *
 * 小白讲解：这是追问关系翻译官的核心工作。
 * 当你说一句话时，它会看：
 * 1. 这话是在继续上一轮的话题吗？（continue）
 * 2. 这话是从上一轮衍生出的新问题吗？（derive）
 * 3. 这话是在纠正上一轮的错误吗？（correct）
 * 4. 这话是完全新的独立任务吗？（new_task）
 *
 * @param {string} userInput - 用户输入
 * @param {Object} previousTask - 上一轮任务状态
 * @returns {Object} ResearchTaskEnvelope
 */
export function resolveTaskRelation(userInput, previousTask) {
  // 没有上一轮任务，一定是新任务
  if (!previousTask) {
    return {
      task_type: "chat",
      entities: [],
      topic: userInput,
      relation_to_previous: "new_task",
      confidence: 0.5,
    };
  }

  // 1. 先检查 derive 指示词（优先级高于 continue）
  // 小白讲解：如果用户说"你刚才说海光很贵，那超节点还有谁"，
  // 虽然以"你刚才说"开头，但核心诉求是"还有谁"（derive），不是"继续"。
  const normalizedInput = userInput.trim();

  // derive 指示词："还有谁""还有哪家""那...呢"（即使前面有 continue 关键词）
  const deriveIndicators = [
    /还有谁/i, /还有哪家/i, /别的呢/i, /别的公司/i, /别的股票/i,
    /那(.*)呢/i, /那它呢/i, /那这个呢/i, /那这只呢/i,
    /第二个|第三个|第二只|另一只/i,
  ];
  for (const indicator of deriveIndicators) {
    if (indicator.test(normalizedInput)) {
      return buildEnvelopeForRelation("derive", userInput, previousTask);
    }
  }

  // 2. 按顺序匹配追问关键词
  for (const { pattern, relation } of FOLLOW_UP_KEYWORDS) {
    if (pattern.test(normalizedInput)) {
      // 根据关系类型构建信封
      return buildEnvelopeForRelation(relation, userInput, previousTask);
    }
  }

  // 2. 检查是否是明显的纠错（包含数值对比）
  if (looksLikeCorrection(userInput, previousTask)) {
    return buildEnvelopeForRelation("correct", userInput, previousTask);
  }

  // 3. 默认作为新任务处理（让 LLM 重新路由）
  return {
    task_type: previousTask.taskType || "chat",
    entities: previousTask.entities || [],
    topic: userInput,
    relation_to_previous: "new_task",
    parent_task_id: previousTask.taskId,
    confidence: 0.5,
    reasoning: "未匹配追问模式，作为新任务处理",
  };
}

/**
 * 判断用户输入是否像是纠错
 *
 * 小白讲解：如果用户提到某个数值，而且这个数值和上一轮的数据不同，
 * 那很可能是在纠错。比如"星网锐捷市值是260亿，不是199亿"。
 */
function looksLikeCorrection(userInput, previousTask) {
  // 检查是否包含"不是""错了"等纠错词
  const correctionWords = /不是|错了|不对|应该是|你错了|你说错了|搞错了/;
  if (!correctionWords.test(userInput)) {
    return false;
  }

  // 检查是否提到上一轮中的某个实体
  if (previousTask.entities && previousTask.entities.length > 0) {
    const tickerMentions = previousTask.entities.some(e => {
      const ticker = e.ticker || "";
      const name = e.name || "";
      return userInput.includes(ticker) || userInput.includes(name);
    });
    if (tickerMentions) return true;
  }

  // 检查是否提到上一轮的主题
  if (previousTask.topic && userInput.includes(previousTask.topic)) {
    return true;
  }

  return false;
}

/**
 * 根据关系类型构建任务信封
 *
 * @param {string} relation - 关系类型（continue/derive/correct/new_task）
 * @param {string} userInput - 用户原始输入
 * @param {Object} previousTask - 上一轮任务
 * @returns {Object} ResearchTaskEnvelope
 */
function buildEnvelopeForRelation(relation, userInput, previousTask) {
  const baseEnvelope = {
    task_type: previousTask.taskType || "chat",
    entities: structuredClone(previousTask.entities || []),
    topic: previousTask.topic || userInput,
    relation_to_previous: relation,
    parent_task_id: previousTask.taskId,
    confidence: 0.9,
  };

  switch (relation) {
    case "continue": {
      // 小白讲解："继续"就是接着上一轮的话题做同样的任务
      // 保留所有上下文
      return {
        ...baseEnvelope,
        confirmedFacts: previousTask.confirmedFacts || [],
        modelAssumptions: previousTask.modelAssumptions || [],
        artifactRefs: previousTask.artifactRefs || [],
        pendingQuestions: previousTask.pendingQuestions || [],
        reasoning: `用户要求继续上一轮任务（${previousTask.taskType}），继承所有上下文`,
      };
    }

    case "derive": {
      // 小白讲解："那第二个呢""那超节点还有谁"是从上一轮衍生出的新问题
      // 保留实体集合，但可能需要调整焦点
      const derivedEnvelope = {
        ...baseEnvelope,
        relation_to_previous: "derive",
        reasoning: `用户从上一轮任务（${previousTask.taskType}）衍生出新问题`,
      };

      // 优先级 1：如果是估值/深研任务且用户问"还有谁/还有哪家"，
      // 优先识别为主题筛选意图（不需要第二个实体）
      if (/还有谁|还有哪家|别的呢|别的公司|别的股票/.test(userInput)
          && previousTask.derivedTheme
          && ["operating_driver_valuation", "stock_deep_dive", "stock_deep_analysis"].includes(previousTask.taskType)) {
        derivedEnvelope.task_type = "theme_expectation_gap";
        derivedEnvelope.topic = previousTask.derivedTheme;
        derivedEnvelope.entities = []; // 主题筛选不预选实体
        derivedEnvelope.reasoning += "，从估值任务衍生为主题筛选";
        return derivedEnvelope;
      }

      // 优先级 2：如果用户提到"第二个"且有多个实体，切换到第二个实体
      if (/第[二三]个|第二只|另一只/.test(userInput)) {
        const entities = previousTask.entities || [];
        if (entities.length >= 2) {
          derivedEnvelope.entities = [entities[1]];
          derivedEnvelope.entities[0].role = "target";
          derivedEnvelope.reasoning += "，聚焦第二个实体";
        }
      }

      return derivedEnvelope;
    }

    case "correct": {
      // 小白讲解：用户纠错时，触发专门的纠错工作流
      // 纠错需要：实体 + 被纠正的字段 + 用户声称的新值
      const correctionTarget = extractCorrectionTarget(userInput, previousTask);

      return {
        ...baseEnvelope,
        task_type: "claim_correction",
        relation_to_previous: "correct",
        correctionTarget,
        confirmedFacts: previousTask.confirmedFacts || [],
        reasoning: `用户纠正上一轮数据：${correctionTarget?.field || "未知字段"}`,
      };
    }

    default:
      return baseEnvelope;
  }
}

/**
 * 从用户输入中提取纠错目标
 *
 * 小白讲解：当用户说"市值是260亿，不是199亿"时，
 * 系统需要知道：
 * - 被纠正的字段是什么？（市值）
 * - 用户声称的正确值是多少？（260亿）
 * - 上一轮的错误值是多少？（199亿）
 */
function extractCorrectionTarget(userInput, previousTask) {
  // 尝试匹配"X是Y，不是Z"或"X不是Z，是Y"的模式
  const patterns = [
    /(市值|收入|利润|营收|EPS|PE|PB|总资产|净资产|毛利率|净利率)[是为]?(\d+(?:\.\d+)?)[万亿]?[元个]?[,，]?(?:不是|错了|不对)[是为]?(\d+(?:\.\d+)?)/i,
    /(?:不是|错了|不对)[是为]?(\d+(?:\.\d+)?)[万亿]?[元个]?[,，]?(市值|收入|利润|营收|EPS|PE|PB|总资产|净资产|毛利率|净利率)[是为]?(\d+(?:\.\d+)?)/i,
  ];

  for (const pattern of patterns) {
    const match = userInput.match(pattern);
    if (match) {
      return {
        field: match[1] || match[2],
        claimedValue: parseFloat(match[2] || match[3]),
        previousValue: parseFloat(match[3] || match[1]),
        entity: previousTask.entities?.[0]?.ticker || null,
      };
    }
  }

  // 如果没有匹配到具体模式，返回基于关键词的推断
  const fieldKeywords = {
    "市值": "market_cap",
    "收入": "revenue",
    "营收": "revenue",
    "利润": "net_income",
    "净利润": "net_income",
    "EPS": "eps",
    "PE": "pe_ttm",
    "PB": "pb",
  };

  for (const [keyword, field] of Object.entries(fieldKeywords)) {
    if (userInput.includes(keyword)) {
      return {
        field,
        claimedValue: null, // 无法精确提取
        entity: previousTask.entities?.[0]?.ticker || null,
      };
    }
  }

  return {
    field: "unknown",
    claimedValue: null,
    entity: previousTask.entities?.[0]?.ticker || null,
  };
}

/**
 * 判断用户输入是否是追问
 *
 * 小白讲解：这是一个轻量级的追问检测器。
 * 它只判断"这句话看起来像不像追问"，但不决定具体怎么处理。
 * 具体怎么处理（continue/derive/correct）由 resolveTaskRelation 决定。
 *
 * @param {string} userInput - 用户输入
 * @returns {boolean}
 */
export function isFollowUpQuestion(userInput) {
  if (!userInput || typeof userInput !== "string") return false;

  const normalized = userInput.trim();

  for (const { pattern } of FOLLOW_UP_KEYWORDS) {
    if (pattern.test(normalized)) return true;
  }

  return false;
}

// === 导出验证过的任务类型集合（供其他模块使用）===
export { VALID_TASK_TYPES, VALID_RELATIONS };
