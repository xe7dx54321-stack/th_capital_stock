import { getStockName } from "../registries/stock-registry.js";
import { getMoatReport } from "./research-analysis-service.js";

// ============================================================
// VFM (Value Framework Module) 价值评判框架 - JS 版
//
// 小白讲解：这个模块就是一个"打分器"，
// 对每只股票从 5 个维度给出 0-10 分的评分，
// 最后加权算出一个综合得分。
// 5 个维度：
//   1. 基本面质量（fundamental_quality）- 赚不赚钱
//   2. 估值位置（valuation_position）- 贵不贵
//   3. 技术动量（technical_momentum）- 涨势好不好
//   4. 主题相关性（theme_relevance）- 是不是热门赛道
//   5. 产业位置（industry_position）- 在行业里排第几
// ============================================================

// --- 维度权重配置（与 Python 版保持一致）---
const VFM_WEIGHTS = {
  fundamental_quality: 0.30,
  valuation_position: 0.15,
  technical_momentum: 0.25,
  theme_relevance: 0.15,
  industry_position: 0.15,
};

// --- 关注主题定义（与 Python 版 FOCUS_THEMES 对齐）---
const FOCUS_THEMES = {
  semiconductor_compute: { 关键词: ["半导体", "算力", "芯片", "GPU", "海光", "寒武纪", "澜起", "兆易", "华虹", "中芯"], baseScore: 7.0 },
  semiconductor_photonics: { 关键词: ["光模块", "CPO", "光子", "光迅", "新易盛", "中际", "天孚", "光库"], baseScore: 7.0 },
  embodied_ai: { 关键词: ["机器人", "具身", "谐波", "绿的", "拓普", "鸣志", "三花", "锋龙"], baseScore: 6.0 },
  ai_agent: { 关键词: ["AI", "agent", "讯飞", "金山", "泛微", "商汤", "阿里", "腾讯"], baseScore: 6.0 },
  quantum: { 关键词: ["量子", "国盾", "IonQ", "Rigetti", "Qubit"], baseScore: 5.0 },
};

// --- 池子类型加分表 ---
const POOL_TYPE_BONUS = {
  recommended: 3.0,
  candidate: 2.0,
  watchlist: 1.0,
  seed: 0.5,
  portfolio_seed: 0.3,
  us_benchmark: 0.2,
};

// ============================================================
// 工具函数
// ============================================================

/**
 * 安全地把任意值转成数字。
 *
 * 小白讲解：就像一个"翻译器"，不管传进来什么乱七八糟的东西，
 * 都尽量转成数字，转不了就返回 null，不会报错。
 *
 * @param {*} value - 要转换的值
 * @returns {number|null} 转换后的数字，转不了返回 null
 */
function safeNum(value) {
  if (value == null || value === "" || value === "None" || value === "nan" || value === "NaN") return null;
  const n = Number(value);
  if (isNaN(n) || !isFinite(n)) return null;
  return n;
}

/**
 * 把数值限制在 [lo, hi] 范围内。
 *
 * 小白讲解：就像一个"围栏"，数值太小了就推回 lo，
 * 太大了就推回 hi，保证不出界。
 *
 * @param {number|null} value - 要限制的值
 * @param {number} lo - 下界
 * @param {number} hi - 上界
 * @returns {number} 限制后的值
 */
function clamp(value, lo = 0, hi = 10) {
  if (value == null) return lo;
  return Math.max(lo, Math.min(hi, value));
}

/**
 * 分段线性评分函数。
 *
 * 小白讲解：给一个数值，根据它在不同区间的位置，
 * 线性地算出一个 0-10 分。
 * 比如：x 越低越好时（像 PE），就设 reverse=true。
 *
 * @param {number|null} x - 要评分的原始数值
 * @param {number} x_min - 低于这个值统一给最低分
 * @param {number} x_low - 合理区间的下界
 * @param {number} x_high - 合理区间的上界
 * @param {number} x_max - 超过这个值统一给最低分
 * @param {boolean} reverse - 是否反转（越低越好）
 * @returns {number|null} 0-10 分的评分，x 为 null 时返回 null
 */
function linearScore(x, x_min, x_low, x_high, x_max, reverse = false) {
  if (x == null) return null;
  let val = x;
  let min = x_min, low = x_low, high = x_high, max = x_max;

  if (reverse) {
    val = -x;
    min = -x_max;
    max = -x_min;
    low = -x_high;
    high = -x_low;
  }

  if (val < min) return 2.0;
  if (val > max) return 3.0;
  if (low <= val && val <= high) return 9.0;
  if (val < low) {
    const ratio = (val - min) / (low - min);
    return 2.0 + ratio * 7.0;
  }
  const ratio = (max - val) / (max - high);
  return 3.0 + ratio * 6.0;
}

// ============================================================
// VFM 5 维度评分函数
// ============================================================

/**
 * 维度 1：基本面质量评分。
 *
 * 小白讲解：这道题考的是"公司本身赚不赚钱"。
 * 看 ROE（净资产收益率）、EPS（每股收益）、
 * 营收增速、净利率这几个指标。
 * ROE 权重最大，因为它最能反映公司的赚钱能力。
 *
 * @param {object} factorMap - 因子字典 {因子名: 数值}
 * @param {object} fundamentalsData - 基本面数据（来自 research-readers）
 * @returns {number|null} 0-10 分的基本面质量分
 */
function scoreFundamentalQuality(factorMap, fundamentalsData) {
  const subScores = [];
  const weights = [];

  // ROE：盈利能力的核心指标。5-25% 最佳区间。
  // 优先用 fundamentalsData 里的 roe，没有再从 factorMap 里找
  const roe = safeNum(fundamentalsData?.roe)
    ?? safeNum(factorMap?.roe_est)
    ?? safeNum(factorMap?.roe_reported)
    ?? safeNum(factorMap?.roe_diluted);
  if (roe != null) {
    // Python 版用的是百分比数值（比如 15 表示 15%）
    // 但 fundamentalsData 里的 roe 是小数（比如 0.15 表示 15%）
    // 我们统一转成百分比后再评分
    const roePct = Math.abs(roe) < 1 ? roe * 100 : roe;
    const score = linearScore(roePct, -5, 5, 25, 40);
    subScores.push(score);
    weights.push(0.35);
  }

  // EPS TTM：每股盈利。>1 元就不错，>4 元优秀。
  const eps = safeNum(factorMap?.eps_ttm) ?? safeNum(factorMap?.basic_eps_reported);
  if (eps != null) {
    const score = linearScore(eps, -1, 0.5, 5.0, 15.0);
    subScores.push(score);
    weights.push(0.25);
  }

  // 营收同比：growth_yoy > 10% 加分。
  const revYoY = safeNum(fundamentalsData?.revenueYoY) ?? safeNum(factorMap?.revenue_yoy);
  if (revYoY != null) {
    // fundamentalsData 里的 revenueYoY 可能是小数也可能是百分比
    const revPct = Math.abs(revYoY) < 1 ? revYoY * 100 : revYoY;
    const score = linearScore(revPct, -20, 5, 50, 100);
    subScores.push(score);
    weights.push(0.20);
  }

  // 净利率：net_margin。15% 以上不错，30% 很好。
  const netMargin = safeNum(fundamentalsData?.netMargin) ?? safeNum(factorMap?.net_margin);
  if (netMargin != null) {
    const nmPct = Math.abs(netMargin) < 1 ? netMargin * 100 : netMargin;
    const score = linearScore(nmPct, -10, 10, 40, 80);
    subScores.push(score);
    weights.push(0.20);
  }

  if (subScores.length === 0) return null;

  const totalWeight = weights.reduce((a, b) => a + b, 0);
  const weightedSum = subScores.reduce((sum, s, i) => sum + s * weights[i], 0);
  return weightedSum / totalWeight;
}

/**
 * 维度 2：估值位置评分。
 *
 * 小白讲解：这道题考的是"现在贵不贵"。
 * 看 PE（市盈率）、PB（市净率），
 * 还会结合历史分位——如果现在比历史上大多数时候都便宜，就加分。
 *
 * @param {object} factorMap - 因子字典
 * @param {object} valuationData - 估值数据（含 historicalPercentile）
 * @returns {number|null} 0-10 分的估值分
 */
function scoreValuationPosition(factorMap, valuationData) {
  const subScores = [];
  const weights = [];

  // PE TTM 评分
  const pe = safeNum(valuationData?.pe)
    ?? safeNum(factorMap?.pe_ttm)
    ?? safeNum(factorMap?.pe_dynamic);
  if (pe != null && pe > 0) {
    let score = linearScore(pe, 5, 12, 60, 120, false);
    // 中段微调（与 Python 版对齐）
    if (20 <= pe && pe <= 50) score = Math.min(10.0, score + 1.0);
    else if (pe > 100) score = Math.max(2.0, score - 2.0);

    // 历史分位修正：越低越便宜，加分
    const percentile = safeNum(valuationData?.historicalPercentile);
    if (percentile != null) {
      const pct = percentile > 1 ? percentile / 100 : percentile;
      if (pct < 0.2) score = Math.min(10.0, score + 1.5);
      else if (pct < 0.4) score = Math.min(10.0, score + 0.8);
      else if (pct > 0.8) score = Math.max(2.0, score - 1.5);
    }

    subScores.push(score);
    weights.push(0.55);
  }

  // PB 评分
  const pb = safeNum(valuationData?.pb) ?? safeNum(factorMap?.pb);
  if (pb != null && pb > 0) {
    let score = linearScore(pb, 0.5, 1.5, 10, 30, false);
    subScores.push(score);
    weights.push(0.45);
  }

  if (subScores.length === 0) return null;

  const totalWeight = weights.reduce((a, b) => a + b, 0);
  const weightedSum = subScores.reduce((sum, s, i) => sum + s * weights[i], 0);
  return weightedSum / totalWeight;
}

/**
 * 维度 3：技术动量评分。
 *
 * 小白讲解：这道题考的是"股价涨势好不好"。
 * 看趋势强度、RSI、MACD、波动率，
 * 还有真实的 5 日/20 日涨跌幅。
 * 金叉（MACD 上穿）就加分，死叉就减分。
 *
 * @param {object} factorMap - 因子字典
 * @param {object} technicalData - 技术面数据
 * @param {Array} priceHistory - 价格历史数组
 * @returns {number|null} 0-10 分的技术动量分
 */
function scoreTechnicalMomentum(factorMap, technicalData, priceHistory) {
  const subScores = [];
  const weights = [];

  // Trend strength：趋势强度（0-1 或 0-10）
  const ts = safeNum(factorMap?.trend_strength) ?? safeNum(technicalData?.trendStrength);
  if (ts != null) {
    const tsNorm = ts > 1 ? ts / 10 : ts;
    const score = 3.0 + tsNorm * 6.0;
    subScores.push(score);
    weights.push(0.20);
  }

  // RSI 14：健康区域是 45-70
  const rsi = safeNum(factorMap?.rsi_14) ?? safeNum(technicalData?.rsi14);
  if (rsi != null) {
    const score = linearScore(rsi, 20, 45, 70, 85);
    subScores.push(score);
    weights.push(0.15);
  }

  // MACD hist：正值表示动能上行
  const macdHist = safeNum(factorMap?.macd_hist) ?? safeNum(technicalData?.macdHist);
  if (macdHist != null) {
    const score = linearScore(macdHist, -5, 0, 5, 15);
    subScores.push(score);
    weights.push(0.15);
  }

  // 波动率：适度波动好，太大不好
  const vol = safeNum(factorMap?.volatility_20) ?? safeNum(technicalData?.volatility20);
  if (vol != null) {
    const volPct = vol < 1 ? vol * 100 : vol;
    const score = linearScore(volPct, 1, 4, 10, 20);
    subScores.push(score);
    weights.push(0.05);
  }

  // 真实价格动量：5 日和 20 日涨跌幅
  const closes = (priceHistory || []).slice(-60).filter(p => p?.close != null).map(p => safeNum(p.close));
  if (closes.length >= 6) {
    const latest = closes[closes.length - 1];
    const prev5 = closes[Math.max(0, closes.length - 6)];
    if (latest && prev5 && prev5 > 0) {
      const mom5 = (latest / prev5 - 1) * 100;
      const score = linearScore(mom5, -10, 0, 8, 20);
      subScores.push(score);
      weights.push(0.15);
    }
  }
  if (closes.length >= 21) {
    const latest = closes[closes.length - 1];
    const prev20 = closes[Math.max(0, closes.length - 21)];
    if (latest && prev20 && prev20 > 0) {
      const mom20 = (latest / prev20 - 1) * 100;
      const score = linearScore(mom20, -20, 0, 15, 40);
      subScores.push(score);
      weights.push(0.20);
    }
  }

  // MACD 信号：金叉/死叉的额外加减分
  // 从 factorMap 里尝试读取 macd 信号
  const macdDif = safeNum(factorMap?.macd_dif) ?? safeNum(technicalData?.macdDif);
  const macdDea = safeNum(factorMap?.macd_dea) ?? safeNum(technicalData?.macdDea);
  let macdBonus = 0;
  if (macdHist != null && macdDif != null && macdDea != null) {
    if (macdDif > macdDea) macdBonus = 0.8;
    else macdBonus = -0.8;
  }

  if (subScores.length === 0) return null;

  const totalWeight = weights.reduce((a, b) => a + b, 0);
  let baseScore = subScores.reduce((sum, s, i) => sum + s * weights[i], 0) / totalWeight;

  // MACD 后处理加减分
  baseScore = clamp(baseScore + macdBonus);

  return baseScore;
}

/**
 * 维度 4：主题相关性评分。
 *
 * 小白讲解：这道题考的是"这只股票属不属于我们关注的热门赛道"。
 * 比如光模块、AI 芯片这些当前热门赛道就会得高分。
 * 还会看它在我们股票池里的层级——越受关注的池子加分越多。
 *
 * @param {string} tsCode - 股票代码
 * @param {string} sector - 行业/主题标签
 * @param {string} poolType - 池子类型（recommended/candidate/watchlist 等）
 * @param {string} stockName - 股票名称（用于关键词匹配）
 * @returns {number} 0-10 分的主题相关性分
 */
function scoreThemeRelevance(tsCode, sector, poolType, stockName = "") {
  // 基础分：先看 sector 是否在关注主题中
  let baseScore = 1.0;
  if (sector) {
    if (FOCUS_THEMES[sector]) {
      baseScore = FOCUS_THEMES[sector].baseScore;
    } else {
      // sector 不在预定义主题里，尝试用关键词匹配
      let matched = false;
      for (const theme of Object.values(FOCUS_THEMES)) {
        if (theme.关键词.some(kw => sector.includes(kw) || stockName.includes(kw))) {
          baseScore = theme.baseScore;
          matched = true;
          break;
        }
      }
      if (!matched) baseScore = 3.0;
    }
  }

  // 池子类型加分
  const bonus = POOL_TYPE_BONUS[poolType] ?? 0.0;

  return clamp(baseScore + bonus);
}

/**
 * 维度 5：产业位置评分。
 *
 * 小白讲解：这道题考的是"这公司在行业里排第几"。
 * 主要看市值——市值大的通常是行业龙头。
 * 如果有行业内相对排名数据（比如 ROE 排名、营收增速排名），还会额外加减分。
 *
 * @param {object} factorMap - 因子字典
 * @param {object} peerGroupData - 同业对标数据
 * @returns {number|null} 0-10 分的产业位置分
 */
function scoreIndustryPosition(factorMap, peerGroupData) {
  // 基础分：市值评分
  const mcap = safeNum(factorMap?.market_cap) ?? safeNum(factorMap?.float_market_cap);
  let baseScore = null;

  if (mcap != null) {
    // Python 版市值单位是亿，这里做兼容判断
    // 如果 mcap > 10000，说明单位可能是万元，转成亿
    let mcapYi = mcap;
    if (mcap > 10000) mcapYi = mcap / 10000;

    if (mcapYi < 50) baseScore = 3.0;
    else if (mcapYi < 200) baseScore = 6.0;
    else if (mcapYi < 1000) baseScore = 8.5;
    else if (mcapYi < 5000) baseScore = 9.0;
    else if (mcapYi < 15000) baseScore = 8.0;
    else baseScore = 7.0;
  }

  // 如果有同业对标数据，用行业排名来调整
  if (peerGroupData?.metrics && baseScore != null) {
    // 找 ROE 排名
    const roeMetric = peerGroupData.metrics.find(m => m.name === "ROE" || m.name === "roe");
    if (roeMetric?.percentile != null) {
      const rankPct = roeMetric.percentile / 100;
      if (rankPct >= 0.7) baseScore = Math.min(10.0, baseScore + 1.5);
      else if (rankPct >= 0.5) baseScore = Math.min(10.0, baseScore + 0.5);
      else if (rankPct < 0.3) baseScore = Math.max(0.0, baseScore - 1.0);
    }

    // 找营收增速排名
    const revMetric = peerGroupData.metrics.find(m => m.name === "营收同比" || m.name === "revenueYoY");
    if (revMetric?.percentile != null) {
      const rankPct = revMetric.percentile / 100;
      if (rankPct >= 0.7) baseScore = Math.min(10.0, baseScore + 1.0);
      else if (rankPct < 0.3) baseScore = Math.max(0.0, baseScore - 0.5);
    }
  }

  return baseScore;
}

/**
 * 检测警示信号（red flags）。
 *
 * 小白讲解：就是从数据里找"危险信号"，
 * 比如 PE 太高了、ROE 太低了、RSI 超买了等等。
 * 把这些警告收集起来，展示给用户看。
 *
 * @param {object} factorMap - 因子字典
 * @param {object} vfmScores - VFM 5 维度得分
 * @param {object} valuationData - 估值数据
 * @returns {string[]} 警示信息列表
 */
function detectRedFlags(factorMap, vfmScores, valuationData) {
  const flags = [];

  // PE 极高
  const pe = safeNum(valuationData?.pe) ?? safeNum(factorMap?.pe_ttm);
  if (pe != null) {
    if (pe > 100) flags.push(`PE=${pe.toFixed(0)}，估值偏高`);
    else if (pe <= 0) flags.push("PE为负，盈利可能有问题");
  }

  // ROE 为负或极低
  const roe = safeNum(factorMap?.roe_est) ?? safeNum(factorMap?.roe_reported);
  if (roe != null) {
    const roePct = Math.abs(roe) < 1 ? roe * 100 : roe;
    if (roePct < 5) flags.push(`ROE=${roePct.toFixed(1)}%，盈利能力偏弱`);
  }

  // RSI 超买
  const rsi = safeNum(factorMap?.rsi_14);
  if (rsi != null && rsi > 75) flags.push(`RSI=${rsi.toFixed(1)}，短线可能过热`);

  // 技术面强但估值太高
  const valScore = vfmScores?.valuation_position;
  const techScore = vfmScores?.technical_momentum;
  if (valScore != null && techScore != null) {
    if (techScore >= 7 && valScore <= 3) {
      flags.push("技术面强但估值偏高，注意追高风险");
    }
  }

  return flags;
}

/**
 * 计算单只股票的完整 VFM 评分卡。
 *
 * 小白讲解：这是"主入口"函数，
 * 你给它一只股票的数据，它把 5 个维度都算一遍，
 * 最后加权算出综合得分，还会检测警示信号。
 *
 * @param {object} input - 股票输入数据
 * @returns {object} 完整的 VFM 评分卡
 */
export function computeVfmScoreCard(input) {
  const { tsCode, sector, poolType, factorMap, priceHistory, valuationData, fundamentalsData, peerGroupData, name } = input;

  // 逐个维度计算分数
  const scores = {
    fundamental_quality: scoreFundamentalQuality(factorMap, fundamentalsData),
    valuation_position: scoreValuationPosition(factorMap, valuationData),
    technical_momentum: scoreTechnicalMomentum(factorMap, null, priceHistory),
    theme_relevance: scoreThemeRelevance(tsCode, sector, poolType, name),
    industry_position: scoreIndustryPosition(factorMap, peerGroupData),
  };

  // 计算综合得分（加权平均）
  const availableScores = [];
  const availableWeights = [];
  for (const [dim, w] of Object.entries(VFM_WEIGHTS)) {
    const s = scores[dim];
    if (s != null) {
      availableScores.push(s);
      availableWeights.push(w);
    }
  }

  let composite = null;
  if (availableScores.length > 0) {
    const totalW = availableWeights.reduce((a, b) => a + b, 0);
    const weightedSum = availableScores.reduce((sum, s, i) => sum + s * availableWeights[i], 0);
    composite = clamp(weightedSum / totalW);
  }

  // 判断数据可用级别
  const nonNull = Object.values(scores).filter(v => v != null).length;
  let dataLevel = "none";
  if (nonNull >= 4) dataLevel = "full";
  else if (nonNull >= 2) dataLevel = "partial";

  // 警示信号
  const redFlags = detectRedFlags(factorMap, scores, valuationData);

  // 计算动量辅助数据（供前端展示）
  const closes = (priceHistory || []).slice(-60).filter(p => p?.close != null).map(p => safeNum(p.close));
  let momentum5d = null, momentum20d = null;
  if (closes.length >= 6) {
    const latest = closes[closes.length - 1];
    const prev5 = closes[Math.max(0, closes.length - 6)];
    if (latest && prev5 && prev5 > 0) momentum5d = (latest / prev5 - 1) * 100;
  }
  if (closes.length >= 21) {
    const latest = closes[closes.length - 1];
    const prev20 = closes[Math.max(0, closes.length - 21)];
    if (latest && prev20 && prev20 > 0) momentum20d = (latest / prev20 - 1) * 100;
  }

  return {
    fundamental_quality: scores.fundamental_quality != null ? Math.round(scores.fundamental_quality * 10) / 10 : null,
    valuation_position: scores.valuation_position != null ? Math.round(scores.valuation_position * 10) / 10 : null,
    technical_momentum: scores.technical_momentum != null ? Math.round(scores.technical_momentum * 10) / 10 : null,
    theme_relevance: scores.theme_relevance != null ? Math.round(scores.theme_relevance * 10) / 10 : null,
    industry_position: scores.industry_position != null ? Math.round(scores.industry_position * 10) / 10 : null,
    composite_score: composite != null ? Math.round(composite * 10) / 10 : null,
    red_flags: redFlags,
    data_available_level: dataLevel,
    momentum_5d: momentum5d != null ? Math.round(momentum5d * 10) / 10 : null,
    momentum_20d: momentum20d != null ? Math.round(momentum20d * 10) / 10 : null,
    pe_percentile: valuationData?.historicalPercentile != null
      ? (valuationData.historicalPercentile > 1 ? valuationData.historicalPercentile / 100 : valuationData.historicalPercentile)
      : null,
  };
}


export function getTechnicalData(db, code, factorMap, priceHistory) {
  const rsi14 = factorMap["rsi_14"] != null ? Number(factorMap["rsi_14"]) : null;
  const macdHist = factorMap["macd_hist"] != null ? Number(factorMap["macd_hist"]) : null;
  const macdDif = factorMap["macd_dif"] != null ? Number(factorMap["macd_dif"]) : null;
  const macdDea = factorMap["macd_dea"] != null ? Number(factorMap["macd_dea"]) : null;
  const trendStrength = factorMap["trend_strength"] != null ? Number(factorMap["trend_strength"]) : null;
  const volatility20 = factorMap["volatility_20"] != null ? Number(factorMap["volatility_20"]) : null;
  const ma20 = factorMap["ma_20"] != null ? Number(factorMap["ma_20"]) : null;

  let change5d = null, change20d = null;
  if (priceHistory && priceHistory.length >= 2) {
    const latest = priceHistory[priceHistory.length - 1]?.close;
    const p5 = priceHistory[Math.max(0, priceHistory.length - 5)]?.close;
    const p20 = priceHistory[Math.max(0, priceHistory.length - 20)]?.close;
    if (latest && p5 && p5 > 0) change5d = (latest / p5 - 1) * 100;
    if (latest && p20 && p20 > 0) change20d = (latest / p20 - 1) * 100;
  }
  const latestClose = priceHistory && priceHistory.length ? priceHistory[priceHistory.length - 1]?.close : null;

  const keyFields = [rsi14, macdHist, macdDif, macdDea, trendStrength, volatility20, change5d, change20d];
  const dataQuality = Math.round((keyFields.filter(v => v != null).length / keyFields.length) * 100);

  return {
    rsi14, macdHist, macdDif, macdDea, trendStrength, volatility20, ma20,
    change5d, change20d, latestClose,
    // 兼容字段：latestPrice 与 latestClose 相同，供后续价格计算逻辑使用
    latestPrice: latestClose,
    dataQuality,
  };
}

export function computeUnifiedScore(valuationData, fundamentalsData, technicalData, moatReport) {
  // 1) 估值：historicalPercentile 直接用（0-100，越高越便宜）
  let valScore = null;
  if (valuationData?.historicalPercentile != null) valScore = Number(valuationData.historicalPercentile);
  else if (valuationData?.pe != null && !isNaN(valuationData.pe) && valuationData.pe > 0) {
    const pe = valuationData.pe;
    if (pe < 15) valScore = 80;
    else if (pe < 25) valScore = 60;
    else if (pe < 40) valScore = 40;
    else valScore = 20;
  }

  // 2) 基本面：ROE + 毛利率 + 营收同比
  let fundScore = null;
  let fSub = 0, fCnt = 0;
  if (fundamentalsData?.roe != null) {
    const roe = Number(fundamentalsData.roe);
    if (roe > 0.20) fSub += 90;
    else if (roe > 0.15) fSub += 80;
    else if (roe > 0.08) fSub += 60;
    else if (roe > 0) fSub += 40;
    else fSub += 20;
    fCnt++;
  }
  if (fundamentalsData?.grossMargin != null) {
    const gm = Number(fundamentalsData.grossMargin);
    if (gm > 0.40) fSub += 90;
    else if (gm > 0.25) fSub += 75;
    else if (gm > 0.10) fSub += 60;
    else fSub += 40;
    fCnt++;
  }
  if (fundamentalsData?.revenueYoY != null) {
    const r = Number(fundamentalsData.revenueYoY);
    if (r > 20) fSub += 90;
    else if (r > 10) fSub += 75;
    else if (r > 0) fSub += 60;
    else fSub += 30;
    fCnt++;
  }
  if (fCnt > 0) fundScore = Math.round(fSub / fCnt);

  // 3) 技术面：trendStrength + change20d + volatility20
  let techScore = null;
  let tSub = 0, tCnt = 0;
  if (technicalData?.trendStrength != null) {
    tSub += Number(technicalData.trendStrength) * 10;
    tCnt++;
  }
  if (technicalData?.change20d != null) {
    const c20 = Number(technicalData.change20d);
    if (c20 > 15) tSub += 90;
    else if (c20 > 5) tSub += 75;
    else if (c20 > -5) tSub += 55;
    else if (c20 > -15) tSub += 35;
    else tSub += 20;
    tCnt++;
  }
  if (technicalData?.volatility20 != null) {
    const vol = Number(technicalData.volatility20);
    if (vol > 0.5) tSub -= 10;
    tCnt++;
  }
  if (tCnt > 0) techScore = Math.max(0, Math.min(100, Math.round(tSub / tCnt)));

  // 4) 护城河：使用完整的 getMoatReport 引擎（与详情页一致）
  const moatScore = moatReport?.totalScore;

  // 5-6) 同业对标 & 催化因素：列表页快速计算（在详情页完整版另行计算）
  const peerScore = null;
  const catalystScore = null;

  // === 综合得分（权重与详情页 getEnhancedRecommendation 完全一致）
  const weights = { valScore: 0.20, fundScore: 0.25, techScore: 0.15, moatScore: 0.15, peerScore: 0.10, catalystScore: 0.15 };
  const scoreItems = { valScore, fundScore, techScore, moatScore, peerScore, catalystScore };
  let totalWeight = 0;
  let weighted = 0;
  for (const key of Object.keys(weights)) {
    const s = scoreItems[key];
    if (s != null && !isNaN(s)) {
      weighted += s * weights[key];
      totalWeight += weights[key];
    }
  }
  const compositeScore = totalWeight > 0 ? Math.round(weighted / totalWeight) : null;

  // === verdict 阈值与详情页保持一致
  let verdict = "观望";
  if (compositeScore != null) {
    if (compositeScore >= 75) verdict = "强烈看多";
    else if (compositeScore >= 60) verdict = "看多";
    else if (compositeScore >= 45) verdict = "中性偏多";
    else if (compositeScore >= 35) verdict = "中性";
    else if (compositeScore >= 25) verdict = "中性偏空";
    else verdict = "看空";
  }

  return { valScore, fundScore, techScore, moatScore, peerScore, catalystScore, compositeScore, verdict };
}

/**
 * 生成价值评分列表（VFM 版）。
 *
 * 小白讲解：这个函数遍历所有股票，
 * 对每只股票调用 VFM 评分器，
 * 然后把结果整理成前端能直接用的格式，
 * 最后按综合得分从高到低排序。
 *
 * @param {Array} inputs - 股票输入数据数组
 * @param {Date} now - 当前时间（用于生成 updatedAt）
 * @returns {{scores: Array, updatedAt: string}} 评分列表
 */
export function buildValueScores(inputs, now = new Date()) {
  const scores = inputs.map((input) => {
    const { tsCode, sector, poolType, factorMap, priceHistory, latestPrice, valuationData, fundamentalsData, peerGroupData } = input;
    let market = "其他";
    if (tsCode.endsWith(".SH") || tsCode.endsWith(".SZ")) market = "A";
    else if (tsCode.endsWith(".HK")) market = "H";
    else if (/^[A-Z]/.test(tsCode)) market = "US";

    const stockName = getStockName(tsCode) || tsCode;

    // === 调用真正的 VFM 评分器 ===
    const vfmCard = computeVfmScoreCard({
      tsCode,
      sector,
      poolType,
      factorMap,
      priceHistory,
      valuationData,
      fundamentalsData,
      peerGroupData,
      name: stockName,
    });

    // 根据综合得分给出投资建议
    const composite = vfmCard.composite_score;
    let verdict = "观望";
    if (composite != null) {
      if (composite >= 7.5) verdict = "强烈看多";
      else if (composite >= 6.0) verdict = "看多";
      else if (composite >= 4.5) verdict = "中性偏多";
      else if (composite >= 3.5) verdict = "中性";
      else if (composite >= 2.5) verdict = "中性偏空";
      else verdict = "看空";
    }

    // 计算 MACD 信号（供前端展示）
    const macdHist = factorMap?.macd_hist != null ? Number(factorMap.macd_hist) : null;
    const macdSignal = macdHist != null ? (macdHist > 0 ? "bullish" : "bearish") : null;

    return {
      tsCode,
      name: stockName,
      market,
      // 5 维评分（来自真正的 VFM）
      compositeScore: vfmCard.composite_score,
      fundamentalQuality: vfmCard.fundamental_quality,
      valuationPosition: vfmCard.valuation_position,
      technicalMomentum: vfmCard.technical_momentum,
      themeRelevance: vfmCard.theme_relevance,
      industryPosition: vfmCard.industry_position,
      // 基本信息
      sector: sector || "未分类",
      poolType: poolType || "",
      latestClose: latestPrice != null ? Number(Number(latestPrice).toFixed(2)) : null,
      verdict,
      // 辅助数据
      pePercentile: vfmCard.pe_percentile,
      momentum5d: vfmCard.momentum_5d,
      momentum20d: vfmCard.momentum_20d,
      macdSignal,
      // VFM 特有：警示信号和数据级别
      redFlags: vfmCard.red_flags || [],
      dataAvailableLevel: vfmCard.data_available_level,
    };
  });
  scores.sort((a, b) => (b.compositeScore || 0) - (a.compositeScore || 0));
  return { scores, updatedAt: now.toISOString() };
}
