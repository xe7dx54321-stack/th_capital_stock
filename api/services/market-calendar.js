const MARKET_ALIASES = Object.freeze({
  A: "A", CN: "A", SH: "A", SZ: "A", BJ: "A",
  H: "H", HK: "H",
  US: "US", USA: "US",
});

// 与仓库现有 Python 日历保持一致。2027 年起若没有新增官方日历，函数会明确退化为工作日规则。
const HOLIDAYS_2026 = Object.freeze({
  A: new Set([
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20",
    "2026-04-06", "2026-05-01", "2026-06-19", "2026-09-25",
    "2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06", "2026-10-07",
  ]),
  H: new Set([
    "2026-01-01", "2026-02-17", "2026-02-18", "2026-02-19", "2026-04-03", "2026-04-06",
    "2026-04-07", "2026-05-01", "2026-05-25", "2026-06-19", "2026-07-01", "2026-09-26",
    "2026-10-01", "2026-10-19", "2026-12-25",
  ]),
  US: new Set([
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19",
    "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
  ]),
});

function normalizeMarket(market = "A") {
  const normalized = String(market || "A").trim().toUpperCase();
  return MARKET_ALIASES[normalized] || normalized;
}

function toIsoDate(value) {
  if (typeof value === "string") {
    const compact = value.trim().match(/^(\d{4})(\d{2})(\d{2})$/);
    const candidate = compact ? `${compact[1]}-${compact[2]}-${compact[3]}` : value.trim().slice(0, 10);
    if (/^\d{4}-\d{2}-\d{2}$/.test(candidate) && !Number.isNaN(new Date(`${candidate}T00:00:00Z`).getTime())) return candidate;
  }
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value.toISOString().slice(0, 10);
  return null;
}

function addDays(isoDate, delta) {
  const date = new Date(`${isoDate}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + delta);
  return date.toISOString().slice(0, 10);
}

function shanghaiParts(now = new Date()) {
  const parsed = now instanceof Date ? now : new Date(now);
  if (Number.isNaN(parsed.getTime())) throw new TypeError("Invalid calendar timestamp");
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hourCycle: "h23",
  }).formatToParts(parsed);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return { date: `${values.year}-${values.month}-${values.day}`, hour: Number(values.hour) };
}

export function isTradingDay(market, value) {
  const isoDate = toIsoDate(value);
  if (!isoDate) return false;
  const normalized = normalizeMarket(market);
  const weekday = new Date(`${isoDate}T00:00:00Z`).getUTCDay();
  if (weekday === 0 || weekday === 6) return false;
  return !(HOLIDAYS_2026[normalized]?.has(isoDate));
}

export function previousTradingDay(market, value, { includeSame = true } = {}) {
  let cursor = toIsoDate(value);
  if (!cursor) throw new TypeError("Invalid calendar date");
  if (!includeSame) cursor = addDays(cursor, -1);
  for (let index = 0; index < 370; index += 1) {
    if (isTradingDay(market, cursor)) return cursor;
    cursor = addDays(cursor, -1);
  }
  throw new Error(`Could not resolve previous trading day for ${market}`);
}

export function expectedLatestTradingDay(market = "A", now = new Date()) {
  const normalized = normalizeMarket(market);
  const local = shanghaiParts(now);
  if (normalized === "US") {
    const anchor = addDays(local.date, local.hour >= 7 ? -1 : -2);
    return previousTradingDay(normalized, anchor);
  }
  const closeHour = 18; // 等待日线数据稳定落库，盘中只认上一已完成交易日。
  const anchor = local.hour >= closeHour ? local.date : addDays(local.date, -1);
  return previousTradingDay(normalized, anchor);
}

export function marketSessionState(market = "A", now = new Date()) {
  const normalized = normalizeMarket(market);
  const local = shanghaiParts(now);
  if (normalized === "US") {
    return { market: normalized, local_date: local.date, status: "closed", observation_date: expectedLatestTradingDay(normalized, now) };
  }
  if (!isTradingDay(normalized, local.date)) {
    return { market: normalized, local_date: local.date, status: "closed", observation_date: previousTradingDay(normalized, local.date) };
  }
  if (local.hour < 9) {
    return { market: normalized, local_date: local.date, status: "preopen", observation_date: previousTradingDay(normalized, local.date, { includeSame: false }) };
  }
  if (local.hour < 15) {
    return { market: normalized, local_date: local.date, status: "open", observation_date: local.date };
  }
  if (local.hour < 18) {
    return { market: normalized, local_date: local.date, status: "settling", observation_date: local.date };
  }
  return { market: normalized, local_date: local.date, status: "closed", observation_date: local.date };
}

export function tradingSessionLag(market, actualLatest, expectedLatest) {
  const actual = toIsoDate(actualLatest);
  const expected = toIsoDate(expectedLatest);
  if (!actual || !expected) return null;
  if (!isTradingDay(market, actual) || actual > expected) return null;
  if (actual === expected) return 0;
  let lag = 0;
  let cursor = actual;
  for (let index = 0; index < 370 && cursor < expected; index += 1) {
    cursor = addDays(cursor, 1);
    if (isTradingDay(market, cursor)) lag += 1;
  }
  return cursor === expected ? lag : null;
}

export { HOLIDAYS_2026, normalizeMarket, shanghaiParts, toIsoDate };
