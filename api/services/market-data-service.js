/**
 * 市场数据服务 —— 连接原始大数据库，提供真实金融数据查询
 *
 * 功能：
 *   这个模块是"数据库翻译官"——它知道大数据库里有哪些表、怎么查，
 *   其他模块只需要调用它的方法就能拿到真实数据，不需要自己写 SQL。
 *
 * 数据来源：
 *   th_capital_stock/01_data/db/smr.db（298MB，63张表，真实A股/H股/美股数据）
 *
 * 小白讲解：
 *   想象这个文件是一个"图书管理员"——你告诉他股票代码（比如 300308），
 *   他就能帮你从书架（数据库）上找到对应的行情、估值、基本面、新闻等信息。
 */

import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

// 获取当前文件所在目录
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// 大数据库的默认路径：从 api/services 往上三级到项目根目录，再进入 th_capital_stock
const DEFAULT_BIG_DB_PATH = path.resolve(
  __dirname,
  "..",
  "..",
  "..",
  "th_capital_stock",
  "01_data",
  "db",
  "smr.db"
);

/**
 * 市场数据服务类
 *
 * 用法：
 *   const service = new MarketDataService();
 *   const valuation = service.getValuation("300308.SZ");
 *   service.close();
 */
export class MarketDataService {
  /**
   * 构造函数：打开数据库连接
   * @param {string} dbPath - 数据库文件路径，不传则用默认的大数据库
   */
  constructor(dbPath = DEFAULT_BIG_DB_PATH) {
    this.dbPath = dbPath;
    this.db = new Database(dbPath, { readonly: true });
  }

  /**
   * 解析股票实体信息
   *
   * 功能：根据股票代码，查找股票名称、所属行业、市场板块等信息
   * 查的表：stock_pool（股票池）+ sector_config（行业配置）
   *
   * @param {string} ticker - 股票代码，如 "300308.SZ" 或 "300308"
   * @returns {object} 股票实体信息 { tsCode, name, sector, sectorKey, market, poolType, status }
   */
  resolveEntity(ticker) {
    // 统一格式：去掉后缀方便模糊匹配
    const normalized = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "").toUpperCase();

    // 先查 stock_pool 表，看这个股票在不在池子里
    const poolRow = this.db
      .prepare(
        `SELECT ts_code, sector, pool_type, status, added_date, added_reason
         FROM stock_pool 
         WHERE ts_code LIKE ? OR ts_code LIKE ?`
      )
      .get(`%${normalized}%`, `${normalized}.%`);

    // 从 sector_config 表查行业名称
    let sectorName = null;
    let sectorKey = null;
    let peers = [];
    let usBenchmarks = [];

    if (poolRow?.sector) {
      const sectorRow = this.db
        .prepare(`SELECT * FROM sector_config WHERE sector_key = ?`)
        .get(poolRow.sector);
      if (sectorRow) {
        sectorName = sectorRow.sector_name;
        sectorKey = sectorRow.sector_key;
        // 同业股票列表（ah_universe 字段是用逗号分隔的股票代码）
        peers = sectorRow.ah_universe
          ? sectorRow.ah_universe.split(",").map((s) => s.trim())
          : [];
        // 美股对标公司
        usBenchmarks = sectorRow.us_benchmarks
          ? sectorRow.us_benchmarks.split(",").map((s) => s.trim())
          : [];
      }
    }

    // 从日线表推断市场类型（A股/H股/美股）
    const barRow = this.db
      .prepare(
        `SELECT market FROM daily_bar WHERE ts_code LIKE ? OR ts_code LIKE ? LIMIT 1`
      )
      .get(`%${normalized}%`, `${normalized}.%`);

    // 推断股票名称（从新闻或事件中提取）
    let name = ticker;
    const newsRow = this.db
      .prepare(
        `SELECT title FROM news_items WHERE tickers_json LIKE ? ORDER BY published_at DESC LIMIT 1`
      )
      .get(`%${normalized}%`);
    if (newsRow?.title) {
      // 尝试从标题中提取中文名称
      const match = newsRow.title.match(/([\u4e00-\u9fa5]{2,8})/);
      if (match) name = match[1];
    }

    return {
      tsCode: poolRow?.ts_code || ticker,
      name,
      sector: sectorName,
      sectorKey,
      market: barRow?.market || null,
      poolType: poolRow?.pool_type || null,
      poolStatus: poolRow?.status || null,
      peers,
      usBenchmarks,
    };
  }

  /**
   * 获取最新日线行情
   *
   * 功能：查询最近 N 天的开盘价、收盘价、最高价、最低价、成交量、涨跌幅
   * 查的表：daily_bar
   *
   * @param {string} ticker - 股票代码
   * @param {number} limit - 获取最近几天的数据，默认 5 天
   * @returns {Array} 日线数组，按日期倒序排列
   */
  getDailyBars(ticker, limit = 5) {
    return this.db
      .prepare(
        `SELECT ts_code, trade_date, open, close, high, low, vol, amount, pct_chg, turnover, market
         FROM daily_bar 
         WHERE ts_code = ? OR ts_code LIKE ?
         ORDER BY trade_date DESC 
         LIMIT ?`
      )
      .all(ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`, limit);
  }

  /**
   * 获取估值数据
   *
   * 功能：查询最新的 PE、PB、市值、历史分位数等估值指标
   * 查的表：valuation_snapshot
   *
   * @param {string} ticker - 股票代码
   * @returns {object|null} 估值数据
   */
  getValuation(ticker) {
    return this.db
      .prepare(
        `SELECT ticker, market, generated_at, current_price, market_cap, 
                pe_ttm, ps_ttm, pb, ev_ebitda_ttm, 
                historical_percentile, historical_percentile_1y, 
                historical_percentile_3y, historical_percentile_5y,
                peer_percentile, broker_target_price, 
                valuation_status, valuation_confidence
         FROM valuation_snapshot 
         WHERE ticker = ? OR ticker LIKE ?
         ORDER BY generated_at DESC 
         LIMIT 1`
      )
      .get(ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`);
  }

  /**
   * 获取基本面数据
   *
   * 功能：查询最新的营收、净利润、ROE、毛利率等财务指标
   * 查的表：fundamentals_snapshot
   *
   * @param {string} ticker - 股票代码
   * @returns {object|null} 基本面数据
   */
  getFundamentals(ticker) {
    return this.db
      .prepare(
        `SELECT ticker, period, fiscal_year, fiscal_quarter,
                revenue, gross_profit, operating_income, net_income, 
                eps_basic, eps_diluted, operating_cash_flow, capex, 
                free_cash_flow, cash_and_equivalents, total_debt, 
                shareholders_equity, gross_margin, operating_margin, 
                net_margin, roe, roic, source_quality, freshness_status, 
                confidence, created_at
         FROM fundamentals_snapshot 
         WHERE ticker = ? OR ticker LIKE ?
         ORDER BY created_at DESC 
         LIMIT 1`
      )
      .get(ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`);
  }

  /**
   * 获取技术因子数据
   *
   * 功能：查询最新的 RSI、MACD、均线、波动率等技术指标
   * 查的表：factor_daily（每只股票每天一行，每个因子是一行记录）
   *
   * 小白讲解：
   *   factor_daily 表的结构很特殊——它不是一行包含所有指标，
   *   而是每个指标占一行。所以查出来后要"转置"成一个对象。
   *
   * @param {string} ticker - 股票代码
   * @returns {object} 技术因子字典 { rsi_14: 36.46, macd_dif: 2.15, ... }
   */
  getFactors(ticker) {
    // 先找到这只股票最新的交易日
    const latestDate = this.db
      .prepare(
        `SELECT MAX(trade_date) as d FROM factor_daily 
         WHERE ts_code = ? OR ts_code LIKE ?`
      )
      .get(ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`);

    if (!latestDate?.d) return {};

    // 查这一天所有的因子
    const rows = this.db
      .prepare(
        `SELECT factor_name, factor_value 
         FROM factor_daily 
         WHERE ts_code = ? OR ts_code LIKE ?
         AND trade_date = ?`
      )
      .all(ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`, latestDate.d);

    // 把行列表转成 { 因子名: 值 } 的字典
    const factors = {};
    for (const row of rows) {
      factors[row.factor_name] = row.factor_value;
    }
    factors._tradeDate = latestDate.d;
    return factors;
  }

  /**
   * 获取相关新闻
   *
   * 功能：查询与指定股票相关的新闻和研报
   * 查的表：news_items
   *
   * @param {string} ticker - 股票代码
   * @param {number} limit - 获取几条，默认 10 条
   * @returns {Array} 新闻数组
   */
  getNews(ticker, limit = 10) {
    const normalized = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "").toUpperCase();
    return this.db
      .prepare(
        `SELECT id, news_id, title, body, published_at, source_name, 
                url, tickers_json, themes_json, language, market, credibility
         FROM news_items 
         WHERE tickers_json LIKE ? OR tickers_json LIKE ?
         ORDER BY published_at DESC 
         LIMIT ?`
      )
      .all(`%${normalized}%`, `%${ticker}%`, limit);
  }

  /**
   * 获取市场事件（公告、投资者关系活动等）
   *
   * 功能：查询指定股票的公告和事件
   * 查的表：market_event
   *
   * @param {string} ticker - 股票代码
   * @param {number} limit - 获取几条，默认 5 条
   * @returns {Array} 事件数组
   */
  getMarketEvents(ticker, limit = 5) {
    const normalized = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "").toUpperCase();
    return this.db
      .prepare(
        `SELECT event_id, event_family, event_type, entity_id, title, 
                event_date, publish_time, importance, status, payload_json
         FROM market_event 
         WHERE entity_id LIKE ? OR entity_id LIKE ?
         ORDER BY event_date DESC 
         LIMIT ?`
      )
      .all(`%${normalized}%`, `%${ticker}%`, limit);
  }

  /**
   * 获取风险告警
   *
   * 功能：查询指定股票的风险告警记录
   * 查的表：risk_alert
   *
   * @param {string} ticker - 股票代码
   * @param {number} limit - 获取几条，默认 5 条
   * @returns {Array} 风险告警数组
   */
  getRiskAlerts(ticker, limit = 5) {
    const normalized = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "").toUpperCase();
    return this.db
      .prepare(
        `SELECT alert_id, alert_time, alert_type, severity, ts_code, message, action, acknowledged
         FROM risk_alert 
         WHERE ts_code LIKE ? OR ts_code LIKE ?
         ORDER BY alert_time DESC 
         LIMIT ?`
      )
      .all(`%${normalized}%`, `%${ticker}%`, limit);
  }

  /**
   * 获取股票池信息
   *
   * 功能：查询股票在池子中的状态（种子池/观察池/核心池）
   * 查的表：stock_pool
   *
   * @param {string} ticker - 股票代码
   * @returns {object|null} 股票池记录
   */
  getStockPoolInfo(ticker) {
    const normalized = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "").toUpperCase();
    return this.db
      .prepare(
        `SELECT * FROM stock_pool WHERE ts_code LIKE ? OR ts_code LIKE ?`
      )
      .get(`%${normalized}%`, `${normalized}.%`);
  }

  /**
   * 获取决策记录
   *
   * 功能：查询该股票的历史决策记录（买入/卖出/观察）
   * 查的表：decision_ledger
   *
   * @param {string} ticker - 股票代码
   * @param {number} limit - 获取几条，默认 3 条
   * @returns {Array} 决策记录数组
   */
  getDecisions(ticker, limit = 3) {
    return this.db
      .prepare(
        `SELECT decision_id, ticker, action, status, decision_time, 
                reference_price, thesis_summary, outcome_status, 
                outcome_price_1d, outcome_price_1w, outcome_price_1m
         FROM decision_ledger 
         WHERE ticker = ? OR ticker LIKE ?
         ORDER BY decision_time DESC 
         LIMIT ?`
      )
      .all(ticker, `${ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "")}.%`, limit);
  }

  /**
   * 获取所有有数据股票列表
   *
   * 功能：查询数据库中有日线数据的所有股票代码
   * 查的表：daily_bar
   *
   * @returns {Array} 股票代码数组
   */
  getAllStocksWithData() {
    return this.db
      .prepare(
        `SELECT DISTINCT ts_code, market FROM daily_bar ORDER BY ts_code`
      )
      .all();
  }

  /**
   * 获取最新交易日的所有股票行情
   *
   * 功能：找到最新的交易日，然后获取当天所有股票的行情数据
   * 查的表：daily_bar
   *
   * @returns {Array} 最新交易日的行情数组
   */
  getLatestMarketSnapshot() {
    const latestDate = this.db
      .prepare(`SELECT MAX(trade_date) as date FROM daily_bar`)
      .get();

    if (!latestDate?.date) return [];

    return this.db
      .prepare(
        `SELECT ts_code, trade_date, open, close, high, low, vol, amount, pct_chg, turnover, market
         FROM daily_bar 
         WHERE trade_date = ?
         ORDER BY pct_chg DESC`
      )
      .all(latestDate.date);
  }

  /**
   * 获取今日涨幅榜
   *
   * 功能：获取最新交易日涨幅最大的股票列表
   *
   * @param {number} limit - 获取几只，默认 10 只
   * @returns {Array} 涨幅榜数组，按涨幅从高到低排列
   */
  getTopGainers(limit = 10) {
    const latestDate = this.db
      .prepare(`SELECT MAX(trade_date) as date FROM daily_bar`)
      .get();

    if (!latestDate?.date) return [];

    return this.db
      .prepare(
        `SELECT ts_code, trade_date, open, close, high, low, vol, amount, pct_chg, turnover, market
         FROM daily_bar 
         WHERE trade_date = ?
         AND pct_chg > 0
         ORDER BY pct_chg DESC 
         LIMIT ?`
      )
      .all(latestDate.date, limit);
  }

  /**
   * 获取今日跌幅榜
   *
   * 功能：获取最新交易日跌幅最大的股票列表
   *
   * @param {number} limit - 获取几只，默认 10 只
   * @returns {Array} 跌幅榜数组，按跌幅从低到高排列
   */
  getTopLosers(limit = 10) {
    const latestDate = this.db
      .prepare(`SELECT MAX(trade_date) as date FROM daily_bar`)
      .get();

    if (!latestDate?.date) return [];

    return this.db
      .prepare(
        `SELECT ts_code, trade_date, open, close, high, low, vol, amount, pct_chg, turnover, market
         FROM daily_bar 
         WHERE trade_date = ?
         AND pct_chg < 0
         ORDER BY pct_chg ASC 
         LIMIT ?`
      )
      .all(latestDate.date, limit);
  }

  /**
   * 获取放量股票（成交量异常放大）
   *
   * 功能：获取最新交易日成交量相比前几天明显放大的股票
   * 查的表：daily_bar
   *
   * @param {number} limit - 获取几只，默认 10 只
   * @param {number} volumeRatioThreshold - 放量倍数阈值，默认 2 倍
   * @returns {Array} 放量股票数组
   */
  getVolumeSurge(limit = 10, volumeRatioThreshold = 2) {
    const latestDate = this.db
      .prepare(`SELECT MAX(trade_date) as date FROM daily_bar`)
      .get();

    if (!latestDate?.date) return [];

    const prevDate = this.db
      .prepare(
        `SELECT MAX(trade_date) as date FROM daily_bar WHERE trade_date < ?`
      )
      .get(latestDate.date);

    if (!prevDate?.date) return [];

    const result = this.db
      .prepare(
        `SELECT 
           t1.ts_code, t1.trade_date, t1.close, t1.pct_chg, t1.vol as current_vol,
           t2.vol as prev_vol,
           CAST(t1.vol AS REAL) / CAST(t2.vol AS REAL) as vol_ratio
         FROM daily_bar t1
         JOIN daily_bar t2 ON t1.ts_code = t2.ts_code AND t2.trade_date = ?
         WHERE t1.trade_date = ?
           AND t2.vol > 0
           AND CAST(t1.vol AS REAL) / CAST(t2.vol AS REAL) >= ?
         ORDER BY vol_ratio DESC
         LIMIT ?`
      )
      .all(prevDate.date, latestDate.date, volumeRatioThreshold, limit);

    return result;
  }

  /**
   * 获取最新新闻热点
   *
   * 功能：获取最新发布的新闻，按时间倒序排列
   * 查的表：news_items
   *
   * @param {number} limit - 获取几条，默认 15 条
   * @returns {Array} 新闻数组
   */
  getLatestNews(limit = 15) {
    return this.db
      .prepare(
        `SELECT id, news_id, title, body, published_at, source_name, 
                url, tickers_json, themes_json, language, market, credibility
         FROM news_items 
         ORDER BY published_at DESC 
         LIMIT ?`
      )
      .all(limit);
  }

  /**
   * 获取今日异动股票（涨跌幅超过阈值）
   *
   * 功能：获取最新交易日涨跌幅超过指定阈值的股票
   * 查的表：daily_bar
   *
   * @param {number} threshold - 涨跌幅阈值（百分比），默认 5%
   * @param {number} limit - 获取几只，默认 10 只
   * @returns {Array} 异动股票数组
   */
  getPriceMovement(threshold = 5, limit = 10) {
    const latestDate = this.db
      .prepare(`SELECT MAX(trade_date) as date FROM daily_bar`)
      .get();

    if (!latestDate?.date) return [];

    return this.db
      .prepare(
        `SELECT ts_code, trade_date, open, close, high, low, vol, amount, pct_chg, turnover, market
         FROM daily_bar 
         WHERE trade_date = ?
         AND ABS(pct_chg) >= ?
         ORDER BY ABS(pct_chg) DESC 
         LIMIT ?`
      )
      .all(latestDate.date, threshold, limit);
  }

  /**
   * 获取股票池内标的的最新行情
   *
   * 功能：获取股票池中所有标的在最新交易日的行情数据
   * 查的表：stock_pool + daily_bar
   *
   * @returns {Array} 股票池标的行情数组
   */
  getPoolSnapshot() {
    const latestDate = this.db
      .prepare(`SELECT MAX(trade_date) as date FROM daily_bar`)
      .get();

    if (!latestDate?.date) return [];

    return this.db
      .prepare(
        `SELECT 
           p.ts_code, p.sector, p.pool_type, p.status,
           b.trade_date, b.close, b.pct_chg, b.vol, b.amount, b.market
         FROM stock_pool p
         LEFT JOIN daily_bar b ON p.ts_code = b.ts_code AND b.trade_date = ?
         ORDER BY b.pct_chg DESC`
      )
      .all(latestDate.date);
  }

  /**
   * 获取最新基本面更新
   *
   * 功能：获取最近更新的基本面数据
   * 查的表：fundamentals_snapshot
   *
   * @param {number} limit - 获取几条，默认 10 条
   * @returns {Array} 基本面更新数组
   */
  getRecentFundamentals(limit = 10) {
    return this.db
      .prepare(
        `SELECT ticker, period, fiscal_year, fiscal_quarter,
                revenue, net_income, roe, gross_margin,
                freshness_status, created_at
         FROM fundamentals_snapshot 
         ORDER BY created_at DESC 
         LIMIT ?`
      )
      .all(limit);
  }

  /**
   * 获取估值异常标的（处于历史低位或高位）
   *
   * 功能：获取估值百分位处于极端位置的股票
   * 查的表：valuation_snapshot
   *
   * 参数：
   *   limit: 获取几只，默认 10 只
   *
   * 返回：
   *   估值异常标的数组，每项包含 ts_code, name, pe_ttm, historical_percentile 等
   *
   * 小白讲解：
   *   这个方法就像一个"估值扫描仪"，从数据库中找出估值处于历史极端位置的股票。
   *   修复3个严重问题：
   *   1. 字段重命名：ticker → ts_code，让下游代码能用 s.ts_code 访问
   *   2. 只取每只股票最新的一条快照（避免同一股票的历史快照被当成多只）
   *   3. 过滤掉 pe_ttm 和 historical_percentile 都为 null 的无效数据
   *   4. historical_percentile 在数据库里是 0-1 的小数（如 0.0516 = 5.16%），
   *      所以 WHERE 条件应该用 0.2 和 0.8，而不是 20 和 80
   *
   * @param {number} limit - 获取几只，默认 10 只
   * @returns {Array} 估值异常标的数组
   */
  getValuationExtremes(limit = 10) {
    return this.db
      .prepare(
        `SELECT v.ticker AS ts_code,
                v.market,
                v.current_price,
                v.market_cap,
                v.pe_ttm,
                v.pb,
                v.historical_percentile,
                v.valuation_status,
                v.valuation_confidence,
                v.generated_at
         FROM valuation_snapshot v
         INNER JOIN (
           -- 子查询：取每只股票最新的一条快照，避免同一股票的历史快照被当成多只
           SELECT ticker, MAX(generated_at) AS max_gen_at
           FROM valuation_snapshot
           WHERE pe_ttm IS NOT NULL
             AND historical_percentile IS NOT NULL
           GROUP BY ticker
         ) latest ON v.ticker = latest.ticker
                  AND v.generated_at = latest.max_gen_at
         WHERE v.historical_percentile IS NOT NULL
           AND v.pe_ttm IS NOT NULL
           AND v.pe_ttm > 0
           -- historical_percentile 是 0-1 的小数，0.2 = 20%分位，0.8 = 80%分位
           AND (v.historical_percentile <= 0.2 OR v.historical_percentile >= 0.8)
         ORDER BY ABS(v.historical_percentile - 0.5) DESC
         LIMIT ?`
      )
      .all(limit);
  }

  /**
   * 获取行业配置数据
   * 
   * 功能：从sector_config表中获取指定行业的配置信息
   * 
   * 小白讲解：
   *   数据库里有一张表叫sector_config，记录了每个行业的信息，
   *   比如光模块行业有哪些美股对标公司、A股有哪些同业公司。
   *   这个方法就是用来查询这些信息的。
   * 
   * @param {string} ticker - 股票代码，如 "300308.SZ"
   * @returns {Object|null} 行业配置数据，包含同业标的和对标公司
   */
  getSectorConfig(ticker) {
    const tickerPrefix = ticker.split('.')[0];
    const rows = this.db
      .prepare("SELECT * FROM sector_config")
      .all();
    
    for (const row of rows) {
      const ahUniverse = row.ah_universe || "";
      const tickers = ahUniverse.split(',').map(t => t.trim());
      if (tickers.includes(tickerPrefix)) {
        return {
          sectorKey: row.sector_key,
          sectorName: row.sector_name,
          usBenchmarks: (row.us_benchmarks || "").split(',').map(t => t.trim()),
          ahUniverse: tickers,
          description: row.description || ""
        };
      }
    }
    return null;
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
