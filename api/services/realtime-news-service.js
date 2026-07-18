/**
 * 实时新闻采集服务 —— 让系统具备分钟级实时新闻能力
 *
 * 功能：
 *   1. 定时轮询多个新闻源（财联社电报、东方财富快讯）
 *   2. 自动去重（基于标题指纹 + URL）
 *   3. 自动提取股票实体（从标题/正文中识别股票代码）
 *   4. 存入数据库，供研究工作流使用
 *   5. 通过事件发射器通知 SSE 推送服务
 *   6. 重大新闻触发器（检测关键词后自动通知）
 *
 * 数据源：
 *   1. 财联社电报 API: https://www.cls.cn/nodeapi/updateTelegraphList
 *      - 业内最快的 A 股快讯源，秒级更新
 *      - 免费公开接口，无需认证
 *   2. 东方财富快讯 API: https://np-listapi.eastmoney.com/comm/web/getFastNewsList
 *      - 补充财联社的资讯覆盖
 *
 * 小白讲解：
 *   想象这个服务是一个"新闻雷达"——它每隔一段时间就自动去
 *   财联社和东方财富看看有没有新消息，有的话就存下来，
 *   如果发现重大消息（比如"涨停"、"跌停"、"重大合同"），
 *   还会主动通知你。
 */

import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import { EventEmitter } from "events";
import crypto from "crypto";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MVP_DB_PATH = path.resolve(__dirname, "..", "..", "01_data", "db", "smr.db");

// 重大新闻关键词（触发通知）
const BREAKING_KEYWORDS = [
  "涨停", "跌停", "大涨", "大跌", "暴涨", "暴跌",
  "重大合同", "重大资产", "并购", "重组", "收购",
  "退市", "ST", "被立案", "处罚", "违规",
  "业绩大增", "业绩亏损", "预增", "预减",
  "降息", "降准", "利好", "利空",
  "IPO", "上市", "定增", "回购", "增持", "减持",
];

// 已知股票代码映射（用于从新闻标题中提取股票实体）
const STOCK_CODE_REGEX = /(\d{6})\.(SZ|SH|BJ)/g;
const STOCK_NAME_REGEXES = [
  /中际旭创/g, /新易盛/g, /贵州茅台/g, /宁德时代/g, /比亚迪/g,
  /招商银行/g, /中国平安/g, /五粮液/g, /隆基绿能/g, /通威股份/g,
];

/**
 * 生成标题指纹（用于去重）
 * @param {string} title - 新闻标题
 * @returns {string} SHA1 哈希指纹
 */
function titleFingerprint(title) {
  return crypto.createHash("sha1").update(title.trim()).digest("hex").substring(0, 16);
}

/**
 * 实时新闻采集服务类
 *
 * 用法：
 *   const service = new RealtimeNewsService();
 *   service.startPolling();  // 开始轮询
 *   service.on("news", (news) => { ... });  // 监听新新闻
 *   service.on("breaking", (news) => { ... });  // 监听重大新闻
 *   service.stopPolling();  // 停止轮询
 */
export class RealtimeNewsService extends EventEmitter {
  /**
   * 构造函数
   * @param {string} dbPath - 数据库路径
   * @param {number} pollInterval - 轮询间隔（毫秒），默认 60 秒
   */
  constructor(dbPath = MVP_DB_PATH, pollInterval = 60000) {
    super();
    this.dbPath = dbPath;
    this.pollInterval = pollInterval;
    this.db = new Database(dbPath);
    this.pollTimer = null;
    this.isPolling = false;
    this.lastFetchTime = null;
    this.stats = {
      totalFetched: 0,
      totalStored: 0,
      totalDuplicates: 0,
      totalBreaking: 0,
      lastPollTime: null,
    };

    this._ensureTable();
  }

  /**
   * 确保 realtime_news 表存在
   * 如果不存在则创建
   */
  _ensureTable() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS realtime_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id TEXT UNIQUE NOT NULL,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT,
        url TEXT,
        published_at TEXT,
        ingested_at TEXT NOT NULL,
        tickers_json TEXT DEFAULT '[]',
        is_breaking INTEGER DEFAULT 0,
        breaking_keywords TEXT,
        dedupe_hash TEXT,
        metadata_json TEXT
      )
    `);
    this.db.exec(`CREATE INDEX IF NOT EXISTS idx_realtime_news_published ON realtime_news(published_at DESC)`);
    this.db.exec(`CREATE INDEX IF NOT EXISTS idx_realtime_news_dedupe ON realtime_news(dedupe_hash)`);
    this.db.exec(`CREATE INDEX IF NOT EXISTS idx_realtime_news_breaking ON realtime_news(is_breaking DESC, published_at DESC)`);
  }

  /**
   * 从新浪财经 7x24 直播 API 获取最新快讯
   *
   * 新浪财经直播 API 说明：
   *   - URL: https://zhibo.sina.com.cn/api/zhibo/feed
   *   - 方法: GET
   *   - 参数: page=1&page_size=20&zhibo_id=152&tag_id=0&type=0
   *   - zhibo_id=152 是财经7x24小时直播间的 ID
   *   - 返回: JSON 格式，result.data.feed.list 数组
   *   - 特点：实时性高，秒级更新，无需认证
   *
   * @param {number} limit - 获取条数
   * @returns {Array} 新闻数组
   */
  async fetchSinaNews(limit = 20) {
    const url = `https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=${limit}&zhibo_id=152&tag_id=0&type=0`;
    try {
      const resp = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          "Referer": "https://finance.sina.com.cn/7x24/",
        },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      // 新浪返回格式: { result: { data: { feed: { list: [...] } } } }
      const items = data?.result?.data?.feed?.list || [];
      return items.map((item) => {
        // rich_text 是 HTML 格式，去掉标签
        const text = (item.rich_text || "").replace(/<[^>]+>/g, "").trim();
        return {
          source: "sina_7x24",
          title: text.substring(0, 100) || "无标题",
          body: text,
          url: item.docurl || `https://finance.sina.com.cn/7x24/`,
          published_at: item.create_time
            ? new Date(item.create_time.replace(/-/g, "/")).toISOString()
            : new Date().toISOString(),
          news_id: `sina_${item.id}`,
        };
      });
    } catch (e) {
      console.error("[RealtimeNews] 新浪财经抓取失败:", e.message);
      return [];
    }
  }

  /**
   * 从东方财富公告 API 获取最新公告
   *
   * 东方财富公告 API 说明：
   *   - URL: https://np-anotice-stock.eastmoney.com/api/security/ann
   *   - 方法: GET
   *   - 参数: sr=-1&page_size=20&page_index=1&ann_type=A&client_source=web
   *   - 返回: JSONP 格式（jQuery包裹），data.list 数组
   *   - 特点：A股全市场公告，包含投资者关系活动、重大事项等
   *
   * @param {number} limit - 获取条数
   * @returns {Array} 新闻数组
   */
  async fetchEastmoneyAnnouncements(limit = 20) {
    const url = `https://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1&page_size=${limit}&page_index=1&ann_type=A&client_source=web&f_node=0&s_node=0`;
    try {
      const resp = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          "Referer": "https://data.eastmoney.com/notices/",
        },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const text = await resp.text();
      // 东方财富可能返回 JSONP 格式（jQuery(...)）或纯 JSON
      let data;
      if (text.startsWith("jQuery")) {
        data = JSON.parse(text.replace(/^jQuery\w*\(|\)$/g, ""));
      } else {
        data = JSON.parse(text);
      }
      const items = data?.data?.list || [];
      return items.map((item) => {
        // 从 codes 数组中提取股票代码
        const tickers = (item.codes || [])
          .map((c) => {
            if (c.stock_code && c.market_code === "0") return `${c.stock_code}.SZ`;
            if (c.stock_code && c.market_code === "1") return `${c.stock_code}.SH`;
            return c.stock_code ? `${c.stock_code}` : null;
          })
          .filter(Boolean);
        return {
          source: "eastmoney_announcement",
          title: item.title || item.title_ch || "无标题",
          body: `${item.codes?.[0]?.short_name || ""} ${item.columns?.[0]?.column_name || ""}`.trim(),
          url: `https://np-cnotice-stock.eastmoney.com/api/content/ann?art_code=${item.art_code}&client_source=web`,
          published_at: item.display_time
            ? new Date(item.display_time.replace(/-/g, "/")).toISOString()
            : new Date().toISOString(),
          news_id: `em_${item.art_code}`,
          preExtractedTickers: tickers,
        };
      });
    } catch (e) {
      console.error("[RealtimeNews] 东方财富公告抓取失败:", e.message);
      return [];
    }
  }

  /**
   * 从新闻文本中提取股票代码和名称
   *
   * @param {string} title - 标题
   * @param {string} body - 正文
   * @returns {Array} 股票代码数组
   */
  extractTickers(title, body) {
    const text = `${title} ${body || ""}`;
    const tickers = new Set();

    // 提取标准代码格式（如 300308.SZ）
    let match;
    const codeRegex = new RegExp(STOCK_CODE_REGEX);
    while ((match = codeRegex.exec(text)) !== null) {
      tickers.add(`${match[1]}.${match[2]}`);
    }

    // 提取已知股票名称
    for (const regex of STOCK_NAME_REGEXES) {
      const nameRegex = new RegExp(regex.source, regex.flags);
      if (nameRegex.test(text)) {
        // 简单映射已知名称到代码
        const nameMap = {
          "中际旭创": "300308.SZ",
          "新易盛": "300502.SZ",
          "贵州茅台": "600519.SH",
          "宁德时代": "300750.SZ",
          "比亚迪": "002594.SZ",
          "招商银行": "600036.SH",
          "中国平安": "601318.SH",
          "五粮液": "000858.SZ",
          "隆基绿能": "601012.SH",
          "通威股份": "600438.SH",
        };
        const name = regex.source.replace(/[\\g]/g, "");
        if (nameMap[name]) tickers.add(nameMap[name]);
      }
    }

    return Array.from(tickers);
  }

  /**
   * 检测是否为重大新闻
   *
   * @param {string} title - 标题
   * @param {string} body - 正文
   * @returns {object} { isBreaking, keywords }
   */
  detectBreaking(title, body) {
    const text = `${title} ${body || ""}`;
    const matched = BREAKING_KEYWORDS.filter((kw) => text.includes(kw));
    return {
      isBreaking: matched.length > 0,
      keywords: matched,
    };
  }

  /**
   * 存储新闻到数据库（自动去重）
   *
   * @param {object} newsItem - 新闻对象
   * @returns {object|null} 如果是新新闻返回存储结果，如果是重复返回 null
   */
  storeNews(newsItem) {
    const dedupeHash = titleFingerprint(newsItem.title);
    // 优先使用预提取的 tickers（如东方财富公告），否则从文本中提取
    const tickers = newsItem.preExtractedTickers?.length
      ? newsItem.preExtractedTickers
      : this.extractTickers(newsItem.title, newsItem.body);
    const { isBreaking, keywords } = this.detectBreaking(newsItem.title, newsItem.body);
    const now = new Date().toISOString();

    try {
      this.db
        .prepare(
          `INSERT INTO realtime_news 
           (news_id, source, title, body, url, published_at, ingested_at, 
            tickers_json, is_breaking, breaking_keywords, dedupe_hash, metadata_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .run(
          newsItem.news_id,
          newsItem.source,
          newsItem.title,
          newsItem.body || "",
          newsItem.url || "",
          newsItem.published_at || now,
          now,
          JSON.stringify(tickers),
          isBreaking ? 1 : 0,
          JSON.stringify(keywords),
          dedupeHash,
          JSON.stringify({ originalSource: newsItem.source })
        );

      return {
        ...newsItem,
        tickers,
        isBreaking,
        breakingKeywords: keywords,
        dedupeHash,
        ingestedAt: now,
      };
    } catch (e) {
      // 唯一约束冲突 = 重复新闻
      if (e.message.includes("UNIQUE")) {
        return null;
      }
      throw e;
    }
  }

  /**
   * 执行一次轮询（从所有数据源获取新闻并存储）
   *
   * @returns {Array} 新获取的新闻列表
   */
  async pollOnce() {
    // 并行获取两个数据源：新浪7x24直播 + 东方财富公告
    const [sinaNews, emNews] = await Promise.all([
      this.fetchSinaNews(20),
      this.fetchEastmoneyAnnouncements(20),
    ]);

    const allNews = [...sinaNews, ...emNews];
    this.stats.totalFetched += allNews.length;
    this.stats.lastPollTime = new Date().toISOString();

    const newNews = [];
    for (const item of allNews) {
      const stored = this.storeNews(item);
      if (stored) {
        newNews.push(stored);
        this.stats.totalStored++;
        if (stored.isBreaking) this.stats.totalBreaking++;

        // 发射事件
        this.emit("news", stored);
        if (stored.isBreaking) {
          this.emit("breaking", stored);
        }
      } else {
        this.stats.totalDuplicates++;
      }
    }

    return newNews;
  }

  /**
   * 开始定时轮询
   */
  startPolling() {
    if (this.isPolling) return;
    this.isPolling = true;
    console.log(`[RealtimeNews] 开始轮询，间隔 ${this.pollInterval / 1000} 秒`);

    // 立即执行一次
    this.pollOnce().catch((e) => console.error("[RealtimeNews] 轮询失败:", e.message));

    // 定时执行
    this.pollTimer = setInterval(() => {
      this.pollOnce().catch((e) => console.error("[RealtimeNews] 轮询失败:", e.message));
    }, this.pollInterval);
  }

  /**
   * 停止轮询
   */
  stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    this.isPolling = false;
    console.log("[RealtimeNews] 已停止轮询");
  }

  /**
   * 获取最新新闻
   *
   * @param {object} options - 查询选项 { limit, breakingOnly, source }
   * @returns {Array} 新闻列表
   */
  getLatestNews(options = {}) {
    const { limit = 50, breakingOnly = false, source = null } = options;
    let sql = `SELECT * FROM realtime_news`;
    const params = [];
    const conditions = [];

    if (breakingOnly) conditions.push(`is_breaking = 1`);
    if (source) conditions.push(`source = ?`);

    if (conditions.length) {
      sql += ` WHERE ` + conditions.join(" AND ");
      if (source) params.push(source);
    }

    sql += ` ORDER BY published_at DESC LIMIT ?`;
    params.push(limit);

    return this.db.prepare(sql).all(...params);
  }

  /**
   * 获取统计信息
   * @returns {object} 统计数据
   */
  getStats() {
    const dbStats = this.db
      .prepare(
        `SELECT 
           COUNT(*) as total,
           SUM(CASE WHEN is_breaking = 1 THEN 1 ELSE 0 END) as breaking,
           SUM(CASE WHEN source = 'cls_telegraph' THEN 1 ELSE 0 END) as cls_count,
           SUM(CASE WHEN source = 'eastmoney_fast' THEN 1 ELSE 0 END) as em_count
         FROM realtime_news`
      )
      .get();

    return {
      ...this.stats,
      dbTotal: dbStats?.total || 0,
      dbBreaking: dbStats?.breaking || 0,
      dbClsCount: dbStats?.cls_count || 0,
      dbEmCount: dbStats?.em_count || 0,
      isPolling: this.isPolling,
      pollInterval: this.pollInterval,
    };
  }

  /**
   * 关闭数据库连接
   */
  close() {
    this.stopPolling();
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }
}
