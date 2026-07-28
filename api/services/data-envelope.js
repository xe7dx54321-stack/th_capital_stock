import crypto from "node:crypto";

import {
  expectedLatestTradingDay,
  isTradingDay,
  marketSessionState,
  toIsoDate,
  tradingSessionLag,
} from "./market-calendar.js";

const HOUR_MS = 60 * 60 * 1000;

const TOOL_SOURCE_POLICIES = Object.freeze({
  get_market_indices: { sourceId: "sina_realtime", sourceName: "新浪财经实时行情", market: "A", maxSessionLag: 0, currentMarket: true },
  get_top_gainers: { sourceId: "market_rank", sourceName: "实时行情榜单或本地行情库", market: "A", maxSessionLag: 0, currentMarket: true },
  get_top_losers: { sourceId: "market_rank", sourceName: "实时行情榜单或本地行情库", market: "A", maxSessionLag: 0, currentMarket: true },
  get_volume_surge: { sourceId: "market_rank", sourceName: "实时行情榜单或本地行情库", market: "A", maxSessionLag: 0, currentMarket: true },
  get_price_movement: { sourceId: "market_rank", sourceName: "实时行情榜单或本地行情库", market: "A", maxSessionLag: 0, currentMarket: true },
  get_valuation_extremes: { sourceId: "local_valuation_db", sourceName: "本地估值快照库", maxAgeHours: 24 * 30, currentMarket: false },
  get_latest_news: { sourceId: "local_news_db", sourceName: "本地新闻库", maxAgeHours: 72, currentMarket: false },
  get_pool_snapshot: { sourceId: "local_market_db", sourceName: "本地股票池与行情库", market: "A", maxSessionLag: 0, currentMarket: true },
  get_decisions: { sourceId: "local_decision_ledger", sourceName: "本地投资决策台账", maxAgeHours: null, currentMarket: false },
  get_stock_data: {
    sourceId: "composite_stock_research",
    sourceName: "个股复合数据（实时行情、本地研究库、东方财富）",
    market: "A",
    maxSessionLag: 0,
    currentMarket: true,
    fixedSource: true,
    preferredAsOfPaths: ["instrumentData.latestDate"],
  },
  get_news: { sourceId: "local_news_db", sourceName: "个股新闻与公告", maxAgeHours: 24 * 8, currentMarket: false },
  get_movement_news: { sourceId: "cninfo_announcement", sourceName: "巨潮资讯个股公告核对", maxAgeHours: 24 * 8, currentMarket: false },
});

const AS_OF_DATE_KEYS = new Set([
  "as_of", "asOf", "trade_date", "tradeDate", "published_at", "publishedAt",
  "generated_at", "generatedAt", "created_at", "createdAt",
  "updated_at", "updatedAt", "date", "timestamp",
]);
const FETCH_DATE_KEYS = new Set(["fetched_at", "fetchedAt"]);

const SOURCE_NAMES = Object.freeze({
  sina_realtime: "新浪财经实时行情",
  eastmoney_realtime: "东方财富实时行情",
  eastmoney_api: "东方财富",
  tencent_api: "腾讯财经实时行情",
  local_market_db: "本地行情库",
  local_news_db: "本地新闻库",
  local_valuation_db: "本地估值快照库",
  local_decision_ledger: "本地投资决策台账",
  tavily_search: "Tavily 新闻搜索",
  composite_stock_research: "个股复合数据（实时行情、本地研究库、东方财富）",
  cninfo_announcement: "CNINFO 巨潮资讯",
});

function readPath(value, pathExpression) {
  return String(pathExpression || "")
    .split(".")
    .filter(Boolean)
    .reduce((current, key) => current?.[key], value);
}

function parseEvidenceDate(value) {
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value;
  if (typeof value !== "string" && typeof value !== "number") return null;
  const raw = String(value).trim();
  if (!raw) return null;
  const compact = raw.match(/^(\d{4})(\d{2})(\d{2})$/);
  const normalized = compact ? `${compact[1]}-${compact[2]}-${compact[3]}` : raw;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function walk(value, visitor, depth = 0) {
  if (depth > 5 || value === null || value === undefined) return;
  if (Array.isArray(value)) {
    for (const item of value.slice(0, 100)) walk(item, visitor, depth + 1);
    return;
  }
  if (typeof value !== "object") return;
  for (const [key, item] of Object.entries(value)) {
    visitor(key, item);
    if (item && typeof item === "object") walk(item, visitor, depth + 1);
  }
}

function collectDates(value, keys = AS_OF_DATE_KEYS) {
  const dates = [];
  walk(value, (key, item) => {
    if (!keys.has(key)) return;
    const parsed = parseEvidenceDate(item);
    if (parsed) dates.push(parsed);
  });
  return dates.sort((a, b) => a.getTime() - b.getTime());
}

function collectStrings(value, keys) {
  const values = [];
  walk(value, (key, item) => {
    if (keys.has(key) && typeof item === "string" && item.trim()) values.push(item.trim());
  });
  return [...new Set(values)];
}

function inferSource(policy, result) {
  if (policy.fixedSource) {
    return { sourceId: policy.sourceId, sourceName: policy.sourceName || SOURCE_NAMES[policy.sourceId] || policy.sourceId };
  }
  const sources = collectStrings(result?.data, new Set(["source", "source_id", "sourceId"]));
  const message = String(result?.message || "");
  // 结构化来源字段比工具提示语可靠；部分旧工具的提示语会把新浪回包误写成东方财富。
  if (sources[0]) {
    return { sourceId: sources[0], sourceName: SOURCE_NAMES[sources[0]] || policy.sourceName || sources[0] };
  }
  if (message.includes("本地数据库")) return { sourceId: policy.sourceId.startsWith("local_") ? policy.sourceId : "local_market_db", sourceName: "本地行情库" };
  if (message.includes("东方财富")) return { sourceId: "eastmoney_realtime", sourceName: SOURCE_NAMES.eastmoney_realtime };
  if (message.includes("新浪")) return { sourceId: "sina_realtime", sourceName: SOURCE_NAMES.sina_realtime };
  const sourceId = policy.sourceId;
  return { sourceId, sourceName: SOURCE_NAMES[sourceId] || policy.sourceName || sourceId };
}

function countItems(value) {
  if (Array.isArray(value)) return value.length;
  if (!value || typeof value !== "object") return value === null || value === undefined || value === "" ? 0 : 1;
  const arrays = Object.values(value).filter(Array.isArray);
  return arrays.length > 0 ? arrays.reduce((sum, items) => sum + items.length, 0) : Object.keys(value).length > 0 ? 1 : 0;
}

function sanitizeSnapshotValue(value, state, depth = 0) {
  if (value === null || value === undefined || typeof value === "number" || typeof value === "boolean") return value ?? null;
  if (typeof value === "string") {
    if (value.length > 2_000) state.truncated = true;
    return value.slice(0, 2_000);
  }
  if (typeof value !== "object") return String(value).slice(0, 500);
  if (state.seen.has(value)) return "[CIRCULAR]";
  if (depth >= 6) {
    state.truncated = true;
    return "[MAX_DEPTH]";
  }
  state.seen.add(value);
  if (Array.isArray(value)) {
    if (value.length > 100) state.truncated = true;
    return value.slice(0, 100).map((item) => sanitizeSnapshotValue(item, state, depth + 1));
  }
  const output = {};
  const entries = Object.entries(value);
  if (entries.length > 100) state.truncated = true;
  for (const [key, item] of entries.slice(0, 100)) {
    if (/api[_-]?key|authorization|cookie|password|secret|token/i.test(key)) {
      output[key] = "[REDACTED]";
    } else {
      output[key] = sanitizeSnapshotValue(item, state, depth + 1);
    }
  }
  return output;
}

export function createEvidenceSnapshot({ evidence, result, maxBytes = 256 * 1024 }) {
  const state = { truncated: false, seen: new WeakSet() };
  let data = sanitizeSnapshotValue(result?.data, state);
  let serialized = JSON.stringify(data);
  if (Buffer.byteLength(serialized, "utf8") > maxBytes) {
    state.truncated = true;
    data = Array.isArray(data)
      ? { kind: "array", original_count: data.length, preview: data.slice(0, 10) }
      : { kind: typeof data, preview: data && typeof data === "object" ? Object.fromEntries(Object.entries(data).slice(0, 20)) : String(data).slice(0, 10_000) };
    serialized = JSON.stringify(data);
  }
  const snapshotSha256 = crypto.createHash("sha256").update(serialized).digest("hex");
  return {
    schema_version: 1,
    evidence_id: evidence.evidence_id,
    tool_id: evidence.tool_id,
    source_id: evidence.source_id,
    captured_at: evidence.captured_at,
    success: result?.success === true,
    message: String(result?.message || "").slice(0, 2_000),
    truncated: state.truncated,
    snapshot_sha256: snapshotSha256,
    data,
  };
}

export function createEvidenceEnvelope({ evidenceId, toolId, result, capturedAt = new Date() }) {
  const policy = TOOL_SOURCE_POLICIES[toolId];
  if (!policy) return null;
  const captured = parseEvidenceDate(capturedAt) || new Date();
  const success = result?.success === true;
  const itemCount = countItems(result?.data);
  const collectedDates = collectDates(result?.data, AS_OF_DATE_KEYS);
  const preferredDates = (policy.preferredAsOfPaths || [])
    .map((pathExpression) => parseEvidenceDate(readPath(result?.data, pathExpression)))
    .filter(Boolean);
  const dates = preferredDates.length > 0 ? preferredDates : collectedDates;
  const fetchedDates = collectDates(result?.data, FETCH_DATE_KEYS);
  const source = inferSource(policy, result);
  const sourceUrls = collectStrings(result?.data, new Set(["url", "source_url", "sourceUrl"])).slice(0, 10);

  const asOfDate = dates.at(-1) || null;
  const ageHours = asOfDate ? Math.max(0, (captured.getTime() - asOfDate.getTime()) / HOUR_MS) : null;
  const expectedTradeDate = policy.market ? expectedLatestTradingDay(policy.market, captured) : null;
  const sessionState = policy.market ? marketSessionState(policy.market, captured) : null;
  const actualTradeDate = asOfDate ? toIsoDate(asOfDate) : null;
  const isLiveObservation = policy.market && actualTradeDate && sessionState
    ? ["open", "settling"].includes(sessionState.status) && actualTradeDate === sessionState.observation_date
    : false;
  const actualTradeDateValid = policy.market && actualTradeDate
    ? isTradingDay(policy.market, actualTradeDate) && (actualTradeDate <= expectedTradeDate || isLiveObservation)
    : true;
  const sessionLag = policy.market && actualTradeDateValid
    ? isLiveObservation ? 0 : tradingSessionLag(policy.market, actualTradeDate, expectedTradeDate)
    : null;

  let freshness = "fresh";
  let missingReason = null;
  if (!success) {
    freshness = "fetch_failed";
    missingReason = result?.message || "数据工具执行失败";
  } else if (itemCount === 0) {
    freshness = "missing";
    missingReason = result?.message || "数据源返回空结果";
  } else if (!asOfDate) {
    freshness = "undated";
    missingReason = "数据存在，但无法识别数据截至时间";
  } else if (policy.market && !actualTradeDateValid) {
    freshness = "invalid_date";
    missingReason = `行情日期 ${actualTradeDate} 不是有效的已完成交易日`;
  } else if (policy.market && sessionLag > policy.maxSessionLag) {
    freshness = "stale";
    missingReason = `行情落后预期交易日 ${expectedTradeDate} 共 ${sessionLag} 个交易日`;
  } else if (!policy.market && policy.maxAgeHours !== null && ageHours > policy.maxAgeHours) {
    freshness = "stale";
    missingReason = `数据已超过 ${policy.maxAgeHours} 小时新鲜度阈值`;
  }

  return {
    evidence_id: evidenceId,
    tool_id: toolId,
    source_id: source.sourceId,
    source_name: source.sourceName,
    source_urls: sourceUrls,
    captured_at: captured.toISOString(),
    source_fetched_at: fetchedDates.at(-1)?.toISOString() || null,
    as_of: asOfDate?.toISOString() || null,
    oldest_as_of: dates[0]?.toISOString() || null,
    as_of_basis: isLiveObservation ? "market_observation" : policy.market && asOfDate ? "market_calendar" : asOfDate ? "source_field" : "unknown",
    freshness,
    age_hours: ageHours === null ? null : Number(ageHours.toFixed(1)),
    max_age_hours: policy.maxAgeHours,
    market: policy.market || null,
    market_session_status: sessionState?.status || null,
    expected_trade_date: expectedTradeDate,
    trading_session_lag: sessionLag,
    item_count: itemCount,
    current_market_evidence: policy.currentMarket,
    missing_reason: missingReason,
  };
}

export function summarizeDataHealth(evidenceCatalog = []) {
  const counts = { fresh: 0, stale: 0, missing: 0, undated: 0, invalid_date: 0, fetch_failed: 0 };
  for (const item of evidenceCatalog) {
    if (Object.hasOwn(counts, item.freshness)) counts[item.freshness] += 1;
  }
  const currentEvidence = evidenceCatalog.filter((item) => item.current_market_evidence);
  const freshCurrent = currentEvidence.filter((item) => item.freshness === "fresh");
  const canClaimCurrent = freshCurrent.length > 0;
  const status = evidenceCatalog.length === 0 || (currentEvidence.length > 0 && !canClaimCurrent)
    ? "blocked"
    : counts.stale + counts.missing + counts.undated + counts.invalid_date + counts.fetch_failed > 0
      ? "warning"
      : "healthy";
  return {
    status,
    can_claim_current: canClaimCurrent,
    total_evidence: evidenceCatalog.length,
    fresh_current_evidence: freshCurrent.length,
    counts,
    checked_at: new Date().toISOString(),
  };
}

export function formatEvidenceCatalogForPrompt(evidenceCatalog = [], dataHealth = summarizeDataHealth(evidenceCatalog)) {
  if (evidenceCatalog.length === 0) return "无可用证据。不得生成带有具体数字的当期市场判断。";
  const healthLabel = dataHealth.status === "healthy" ? "健康" : dataHealth.status === "warning" ? "有警告" : "不可支持当期判断";
  const lines = evidenceCatalog.map((item) => {
    const asOf = item.as_of || "未知";
    const urls = item.source_urls.length > 0 ? `；链接=${item.source_urls.join(", ")}` : "";
    const session = item.expected_trade_date ? `；预期交易日=${item.expected_trade_date}；滞后=${item.trading_session_lag ?? "未知"}个交易日` : "";
    return `[${item.evidence_id}] ${item.source_name}；工具=${item.tool_id}；截至=${asOf}；依据=${item.as_of_basis}；状态=${item.freshness}；条目=${item.item_count}${session}${urls}`;
  });
  return `数据健康=${healthLabel}；是否允许声称“当前/今日”=${dataHealth.can_claim_current ? "是" : "否"}\n${lines.join("\n")}`;
}

export { TOOL_SOURCE_POLICIES, parseEvidenceDate };
