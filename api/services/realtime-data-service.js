/**
 * 实时行情数据服务
 *
 * 功能：
 *   1. 通过腾讯财经 API 获取 A 股实时行情（价格、市值、PE、PB、PS 等）
 *   2. 通过东方财富 API 获取 A 股详细数据（备用）
 *   3. 支持批量查询多只股票的实时数据
 *   4. 5 分钟缓存，避免频繁请求外部 API
 *
 * 数据源：
 *   - 腾讯财经 (qt.gtimg.cn)：实时行情、市值、PE、PB、PS、换手率
 *   - 东方财富 (push2.eastmoney.com)：备用数据源
 *
 * 小白讲解：
 *   这个服务就像一个"实时行情探子"，专门去腾讯财经网站
 *   查询股票的最新价格、总市值、市盈率等数据。
 *   它比数据库里的数据更实时，因为数据库可能几天才更新一次。
 */

/**
 * 全局缓存（避免短时间内重复请求）
 */
let _cachedData = {};
let _cachedAt = 0;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 分钟

/**
 * 将 A 股代码转换为腾讯财经格式
 *
 * 参数：
 *   ticker: A 股代码，如 "300308.SZ"
 * 返回：
 *   腾讯格式，如 "sz300308"
 *
 * 规则：
 *   - 沪市 (.SH): sh + 代码（如 sh000063）
 *   - 深市 (.SZ): sz + 代码（如 sz300308）
 *   - 北交所 (.BJ): bj + 代码
 */
function toTencentCode(ticker) {
  if (!ticker) return "";
  const code = ticker.replace(/\.(SZ|SH|BJ)$/i, "");
  const suffix = ticker.toUpperCase().split(".").pop();
  const prefix = suffix === "SH" ? "sh" : suffix === "BJ" ? "bj" : "sz";
  return prefix + code;
}

/**
 * 解析腾讯财经 API 返回的原始数据
 *
 * 参数：
 *   rawText: API 返回的原始文本
 * 返回：
 *   按 ticker 分组的数据对象
 */
function parseTencentResponse(rawText) {
  const result = {};
  const lines = rawText.split(";");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    const eq = trimmed.indexOf("=");
    if (eq < 0) continue;

    const val = trimmed.substring(eq + 1).replace(/^"|"$/g, "");
    const parts = val.split("~");
    if (parts.length < 50) continue;

    const code = parts[2]; // 如 "300308"
    const market = parts[0] === "51" ? "SZ" : parts[0] === "1" ? "SH" : "SZ";
    const ticker = code + "." + market;

    result[ticker] = {
      ticker,
      // 腾讯财经返回的名称是 GBK 编码，这里不解析名称（用 STOCK_NAME_MAP）
      latest_price: parseFloat(parts[3]) || null,
      change_percent: parseFloat(parts[32]) || null,
      pe_ttm: parseFloat(parts[39]) || null,
      pb: parseFloat(parts[46]) || null,
      ps_ttm: parseFloat(parts[47]) || null,
      turnover_rate: parseFloat(parts[38]) || null,
      market_cap: parseFloat(parts[44]) || null,     // 总市值（亿）
      float_market_cap: parseFloat(parts[45]) || null, // 流通市值（亿）
      total_shares: parseFloat(parts[13]) || null,    // 总股本
      high: parseFloat(parts[33]) || null,
      low: parseFloat(parts[34]) || null,
      volume: parseFloat(parts[36]) || null,          // 成交量（手）
      amount: parseFloat(parts[37]) || null,          // 成交额（万）
      source: "tencent_api",
      fetched_at: new Date().toISOString(),
    };
  }

  return result;
}

/**
 * 获取单只或多只 A 股的实时行情数据
 *
 * 参数：
 *   tickers: 单个 ticker 字符串或 ticker 数组
 * 返回：
 *   单个数据对象（传入单 ticker）或按 ticker 分组的对象（传入数组）
 */
export async function fetchRealtimeData(tickers) {
  const isArray = Array.isArray(tickers);
  const tickerList = isArray ? tickers : [tickers];

  if (tickerList.length === 0) {
    return isArray ? {} : null;
  }

  // 检查缓存
  const now = Date.now();
  if (now - _cachedAt < CACHE_TTL_MS) {
    const cachedResult = {};
    let allHit = true;
    for (const t of tickerList) {
      if (_cachedData[t]) {
        cachedResult[t] = _cachedData[t];
      } else {
        allHit = false;
        break;
      }
    }
    if (allHit) {
      return isArray ? cachedResult : cachedResult[tickerList[0]];
    }
  }

  // 腾讯财经 API 每次最多支持约 60 只股票
  const codes = tickerList.map(toTencentCode).filter(Boolean);
  if (codes.length === 0) {
    return isArray ? {} : null;
  }

  const url = `http://qt.gtimg.cn/q=${codes.join(",")}`;

  try {
    const resp = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://quote.eastmoney.com/",
      },
    });

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }

    const text = await resp.text();
    const parsed = parseTencentResponse(text);

    // 更新缓存
    for (const [ticker, data] of Object.entries(parsed)) {
      _cachedData[ticker] = data;
    }
    _cachedAt = now;

    return isArray ? parsed : parsed[tickerList[0]] || null;
  } catch (err) {
    console.warn("[RealtimeDataService] 腾讯财经 API 请求失败:", err.message);
    // 返回缓存数据（即使过期）作为 fallback
    const fallback = {};
    for (const t of tickerList) {
      if (_cachedData[t]) fallback[t] = _cachedData[t];
    }
    if (Object.keys(fallback).length > 0) {
      return isArray ? fallback : fallback[tickerList[0]];
    }
    return isArray ? {} : null;
  }
}

// ==================== 涨幅榜/跌幅榜（东方财富行情中心） ====================

/**
 * 涨幅榜/跌幅榜缓存
 */
let _rankCache = { gainers: null, losers: null, fetchedAt: 0 };
const RANK_CACHE_TTL = 2 * 60 * 1000; // 2分钟缓存

/**
 * 东方财富行情中心 API 请求头
 */
const EM_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
  "Referer": "https://data.eastmoney.com/",
  "Accept": "application/json, text/plain, */*",
};

/**
 * 带超时的 fetch 包装
 *
 * @param {string} url - 请求地址
 * @param {number} timeoutMs - 超时毫秒，默认 10000
 * @returns {Promise<Response>} Response 对象
 */
async function fetchWithTimeout(url, timeoutMs = 10000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { headers: EM_HEADERS, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 解析新浪财经排行榜数据为统一格式
 *
 * 功能：把新浪财经返回的原始数据转换成我们系统内部用的统一格式
 *
 * @param {Object} item - 新浪财经返回的单条股票数据
 * @returns {Object} 格式化后的股票数据
 *
 * 小白讲解：
 *   就像翻译官一样，把新浪财经说的"话"
 *   翻译成我们系统能听懂的"话"。
 *   这样不管用哪个数据源，后面的代码都不用改。
 */
function parseSinaRankItem(item) {
  // symbol 格式如 sz300795, sh600519, bj920305
  const symbol = item.symbol || "";
  let market = "SZ";
  if (symbol.startsWith("sh")) market = "SH";
  else if (symbol.startsWith("bj")) market = "BJ";

  const code = item.code || "";
  const tsCode = code + "." + market;

  // 新浪的成交量单位是股，我们要转成手（1手=100股）
  const vol = item.volume ? Math.round(item.volume / 100) : null;
  // 新浪的成交额单位是元，我们要转成万元
  const amount = item.amount ? item.amount / 10000 : null;
  // 新浪的总市值/流通市值单位是万元，我们保留
  const totalMv = item.mktcap ? item.mktcap * 10000 : null; // 转成元
  const floatMv = item.nmc ? item.nmc * 10000 : null;

  return {
    ts_code: tsCode,
    name: item.name,
    trade_date: new Date().toISOString().split("T")[0],
    open: item.open ? parseFloat(item.open) : null,
    close: item.trade ? parseFloat(item.trade) : null,
    high: item.high ? parseFloat(item.high) : null,
    low: item.low ? parseFloat(item.low) : null,
    vol: vol,
    amount: amount,
    pct_chg: item.changepercent !== undefined ? item.changepercent : null,
    turnover: item.turnoverratio !== undefined ? item.turnoverratio : null,
    market: "A",
    volume_ratio: null, // 新浪没有量比数据
    pe_ttm: item.per !== undefined ? item.per : null,
    total_mv: totalMv,
    float_mv: floatMv,
    source: "sina_realtime",
  };
}

/**
 * 从新浪财经获取涨幅榜/跌幅榜
 *
 * 功能：调用新浪财经API获取A股排行榜数据
 *
 * @param {number} limit - 获取几只
 * @param {number} asc - 0=涨幅榜（降序）, 1=跌幅榜（升序）
 * @returns {Promise<Array>} 股票列表
 */
async function fetchSinaRank(limit, asc) {
  const pageSize = Math.max(limit, 30);
  const url = `https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=${pageSize}&sort=changepercent&asc=${asc}&node=hs_a&symbol=&_s_r_a=sort`;

  const resp = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
      "Referer": "https://finance.sina.com.cn/",
    },
    signal: AbortSignal.timeout(10000),
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

  const data = await resp.json();
  if (!Array.isArray(data)) throw new Error("返回数据格式错误");

  return data.map(parseSinaRankItem).filter(item => item.pct_chg !== null && item.close !== null);
}

/**
 * 从东方财富获取涨幅榜/跌幅榜（备用）
 *
 * 功能：调用东方财富API获取排行榜数据（备用方案）
 *
 * @param {number} limit - 获取几只
 * @param {number} po - 1=涨幅榜（降序）, 0=跌幅榜（升序）
 * @returns {Promise<Array>} 股票列表
 */
async function fetchEastmoneyRank(limit, po) {
  const pageSize = Math.max(limit, 20);
  const url = `https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=${pageSize}&po=${po}&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21`;

  const resp = await fetchWithTimeout(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

  const data = await resp.json();
  const diff = data?.data?.diff || [];

  return diff.map(item => {
    const tsCode = item.f12 + "." + (item.f12?.startsWith("6") || item.f12?.startsWith("688") ? "SH" : "SZ");
    return {
      ts_code: tsCode,
      name: item.f14,
      trade_date: new Date().toISOString().split("T")[0],
      open: item.f17 !== "-" ? item.f17 : null,
      close: item.f2 !== "-" ? item.f2 : null,
      high: item.f15 !== "-" ? item.f15 : null,
      low: item.f16 !== "-" ? item.f16 : null,
      vol: item.f5 !== "-" ? Math.round(item.f5 / 100) : null,
      amount: item.f6 !== "-" ? item.f6 / 10000 : null,
      pct_chg: item.f3 !== "-" ? item.f3 : null,
      turnover: item.f8 !== "-" ? item.f8 : null,
      market: "A",
      volume_ratio: item.f10 !== "-" ? item.f10 : null,
      pe_ttm: item.f9 !== "-" ? item.f9 : null,
      total_mv: item.f20 !== "-" ? item.f20 : null,
      float_mv: item.f21 !== "-" ? item.f21 : null,
      source: "eastmoney_realtime",
    };
  }).filter(item => item.pct_chg !== null && item.close !== null);
}

/**
 * 获取实时涨幅榜
 *
 * 功能：获取最新交易日涨幅最大的股票列表
 * 数据源优先级：新浪财经 -> 东方财富 -> 缓存
 *
 * @param {number} limit - 获取几只，默认 20 只
 * @returns {Promise<Array>} 涨幅榜数组，按涨幅从高到低排列
 *
 * 小白讲解：
 *   这个函数就像去财经网站看"涨幅排行榜"，
 *   能拿到今天涨得最多的股票，包括涨跌幅、价格、成交量、换手率等。
 *   优先用新浪财经的数据，连不上就试试东方财富，
 *   都不行就用之前缓存的数据，保证总能拿到数据。
 */
export async function fetchTopGainers(limit = 20) {
  // 检查缓存
  const now = Date.now();
  if (_rankCache.gainers && now - _rankCache.fetchedAt < RANK_CACHE_TTL) {
    return _rankCache.gainers.slice(0, limit);
  }

  // 方案1：新浪财经（首选）
  try {
    const result = await fetchSinaRank(limit, 0);
    if (result.length > 0) {
      _rankCache.gainers = result;
      _rankCache.fetchedAt = now;
      console.log(`[RealtimeDataService] 新浪财经涨幅榜获取成功，共 ${result.length} 只`);
      return result.slice(0, limit);
    }
  } catch (err) {
    console.warn("[RealtimeDataService] 新浪财经涨幅榜失败:", err.message);
  }

  // 方案2：东方财富（备用）
  try {
    const result = await fetchEastmoneyRank(limit, 1);
    if (result.length > 0) {
      _rankCache.gainers = result;
      _rankCache.fetchedAt = now;
      console.log(`[RealtimeDataService] 东方财富涨幅榜获取成功，共 ${result.length} 只`);
      return result.slice(0, limit);
    }
  } catch (err) {
    console.warn("[RealtimeDataService] 东方财富涨幅榜失败:", err.message);
  }

  // 方案3：返回缓存数据（即使过期）
  if (_rankCache.gainers) {
    console.warn("[RealtimeDataService] 使用过期缓存的涨幅榜数据");
    return _rankCache.gainers.slice(0, limit);
  }

  return [];
}

/**
 * 获取实时跌幅榜
 *
 * 功能：获取最新交易日跌幅最大的股票列表
 * 数据源优先级：新浪财经 -> 东方财富 -> 缓存
 *
 * @param {number} limit - 获取几只，默认 20 只
 * @returns {Promise<Array>} 跌幅榜数组，按跌幅从低到高排列
 *
 * 小白讲解：
 *   和涨幅榜相反，这个函数拿的是今天跌得最多的股票，
 *   用来发现风险、避开雷区，或者寻找超跌反弹的机会。
 *   优先用新浪财经的数据，连不上就试试东方财富，
 *   都不行就用之前缓存的数据。
 */
export async function fetchTopLosers(limit = 20) {
  // 检查缓存
  const now = Date.now();
  if (_rankCache.losers && now - _rankCache.fetchedAt < RANK_CACHE_TTL) {
    return _rankCache.losers.slice(0, limit);
  }

  // 方案1：新浪财经（首选）
  try {
    const result = await fetchSinaRank(limit, 1); // asc=1 表示升序（跌幅从大到小）
    if (result.length > 0) {
      _rankCache.losers = result;
      _rankCache.fetchedAt = now;
      console.log(`[RealtimeDataService] 新浪财经跌幅榜获取成功，共 ${result.length} 只`);
      return result.slice(0, limit);
    }
  } catch (err) {
    console.warn("[RealtimeDataService] 新浪财经跌幅榜失败:", err.message);
  }

  // 方案2：东方财富（备用）
  try {
    const result = await fetchEastmoneyRank(limit, 0); // po=0 表示升序
    if (result.length > 0) {
      _rankCache.losers = result;
      _rankCache.fetchedAt = now;
      console.log(`[RealtimeDataService] 东方财富跌幅榜获取成功，共 ${result.length} 只`);
      return result.slice(0, limit);
    }
  } catch (err) {
    console.warn("[RealtimeDataService] 东方财富跌幅榜失败:", err.message);
  }

  // 方案3：返回缓存数据（即使过期）
  if (_rankCache.losers) {
    console.warn("[RealtimeDataService] 使用过期缓存的跌幅榜数据");
    return _rankCache.losers.slice(0, limit);
  }

  return [];
}

/**
 * 获取实时放量异动股票（基于涨幅榜数据筛选）
 *
 * 功能：从实时涨幅榜中筛选出成交量异常放大的股票
 * 优先使用量比指标，没有量比时用换手率作为替代
 *
 * @param {number} limit - 获取几只，默认 10 只
 * @param {number} volumeRatioThreshold - 量比阈值，默认 1.5
 * @returns {Promise<Array>} 放量股票数组
 *
 * 小白讲解：
 *   量比是衡量成交量放大程度的指标，
 *   量比越大说明今天成交量比平时大越多，
 *   往往意味着有大资金在行动，可能是机会也可能是风险。
 *   如果量比数据拿不到，就用换手率来凑合，
 *   换手率高也说明交易活跃。
 */
export async function fetchVolumeSurge(limit = 10, volumeRatioThreshold = 1.5) {
  // 先拿涨幅榜
  const gainers = await fetchTopGainers(Math.max(limit * 3, 30));
  
  // 先尝试用量比筛选
  const withVolumeRatio = gainers.filter(item => item.volume_ratio && item.volume_ratio >= volumeRatioThreshold);
  if (withVolumeRatio.length > 0) {
    withVolumeRatio.sort((a, b) => (b.volume_ratio || 0) - (a.volume_ratio || 0));
    return withVolumeRatio.slice(0, limit);
  }
  
  // 没有量比数据时，用换手率作为替代指标（换手率高也算放量）
  console.log("[RealtimeDataService] 无量比数据，使用换手率作为放量替代指标");
  const withTurnover = gainers.filter(item => item.turnover && item.turnover > 5); // 换手率>5%算活跃
  if (withTurnover.length > 0) {
    withTurnover.sort((a, b) => (b.turnover || 0) - (a.turnover || 0));
    return withTurnover.slice(0, limit);
  }
  
  // 实在不行就返回涨幅榜前几名
  return gainers.slice(0, limit);
}

/**
 * 获取实时价格异动股票（涨跌幅超过阈值）
 *
 * 功能：获取涨跌幅超过指定阈值的股票（包括涨和跌）
 *
 * @param {number} threshold - 涨跌幅阈值（百分比），默认 5%
 * @param {number} limit - 获取几只，默认 10 只
 * @returns {Promise<Array>} 异动股票数组
 *
 * 小白讲解：
 *   把涨幅榜和跌幅榜放一起，挑出波动大的股票，
 *   看看今天市场上哪些股票最"热闹"。
 */
export async function fetchPriceMovement(threshold = 5, limit = 10) {
  const [gainers, losers] = await Promise.all([
    fetchTopGainers(Math.floor(limit / 2) + 10),
    fetchTopLosers(Math.floor(limit / 2) + 10),
  ]);
  const all = [...gainers, ...losers];
  // 按涨跌幅绝对值排序
  all.sort((a, b) => Math.abs(b.pct_chg || 0) - Math.abs(a.pct_chg || 0));
  // 过滤超过阈值的
  return all.filter(item => Math.abs(item.pct_chg || 0) >= threshold).slice(0, limit);
}

/**
 * 清除所有缓存（涨幅榜/跌幅榜+个股数据）
 */
export function clearRealtimeDataCache() {
  _cachedData = {};
  _cachedAt = 0;
  _rankCache = { gainers: null, losers: null, fetchedAt: 0 };
}


/**
 * 获取A股主要大盘指数实时数据
 *
 * 通过新浪财经 API 获取上证指数、深证成指、创业板指、科创50、北证50 的实时行情
 *
 * 参数：
 *   无
 * 返回：
 *   指数数组，每项包含：代码、名称、最新价、涨跌幅、成交量、成交额等
 *
 * 小白讲解：
 *   就是获取"大盘今天怎么样"的数据——
 *   上证指数（沪指）、深证成指、创业板指等等，看看今天市场整体是涨是跌。
 */
export async function fetchMarketIndices() {
  // A股主要指数的新浪代码
  const indexCodes = {
    sh000001: "上证指数",
    sz399001: "深证成指",
    sz399006: "创业板指",
    sh000688: "科创50",
    sz399997: "中证白酒",
    sh000300: "沪深300",
    sh000016: "上证50",
    sz399005: "中小板指",
  };

  const codes = Object.keys(indexCodes);

  try {
    const url = `https://hq.sinajs.cn/list=${codes.join(",")}`;
    const resp = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://finance.sina.com.cn/",
      },
      signal: AbortSignal.timeout(10000),
    });

    if (!resp.ok) {
      console.warn("[RealtimeDataService] 获取大盘指数失败, HTTP:", resp.status);
      return [];
    }

    // 修复：新浪API返回的是GBK编码，需要正确解码中文
    // 小白讲解：新浪服务器返回的数据是GBK编码的（老格式），
    // 如果直接用resp.text()会用UTF-8解码，中文会变成乱码。
    // 解决方法：用TextDecoder指定GBK编码来正确读取中文。
    const buffer = await resp.arrayBuffer();
    let text;
    try {
      // 尝试用GBK解码
      const decoder = new TextDecoder("gbk");
      text = decoder.decode(buffer);
    } catch (e) {
      // 如果不支持GBK（Node.js需要iconv-lite），回退到UTF-8
      console.warn("[RealtimeDataService] GBK解码失败，回退UTF-8:", e.message);
      text = new TextDecoder("utf-8").decode(buffer);
    }
    const lines = text.split("\n").filter(l => l.includes('="'));
    const result = [];

    for (const line of lines) {
      // 新浪大盘指数格式：hq_str_sh000001="上证指数,3400.12,3380.00,3405.56,3410.00,3375.00,..."
      // 和个股不同，大盘指数不需要 s_ 前缀
      const match = line.match(/hq_str_([a-z]+\d+)="(.+)"/);
      if (!match) continue;

      const code = match[1];
      const name = indexCodes[code];
      if (!name) continue;

      const parts = match[2].split(",");
      // 新浪大盘指数数据格式（索引从0开始）：
      // 0:名称, 1:当前点位, 2:昨收, 3:今开, 4:最高, 5:最低,
      // 6-7:保留, 8:成交量(手), 9:成交额(元), ...
      // 小白讲解：注意！parts[8]是成交量（手数），不是成交额！
      // 成交额在 parts[9]，单位是元，要除以1亿才是亿元
      if (parts.length >= 10) {
        const currentPrice = parseFloat(parts[1]) || 0;
        const yesterdayClose = parseFloat(parts[2]) || 0;
        const pctChg = yesterdayClose > 0 ? ((currentPrice - yesterdayClose) / yesterdayClose * 100) : 0;
        // 成交额在 parts[9]，单位是元，转换为亿元
        const amountYi = parseFloat(parts[9]) ? parseFloat(parts[9]) / 100000000 : 0;

        result.push({
          code,
          name: parts[0] || name,
          price: currentPrice,
          pct_chg: parseFloat(pctChg.toFixed(2)),
          amount: amountYi,
          source: "sina_realtime",
        });
      }
    }

    return result;
  } catch (err) {
    console.warn("[RealtimeDataService] 获取大盘指数异常:", err.message);
    return [];
  }
}
