/**
 * 中文财经新闻抓取服务
 *
 * 功能：
 *   1. 按需抓取 4 个 content_ready 中文源的最新新闻
 *   2. 支持按股票名称/代码过滤相关新闻
 *   3. 轻量级实现，不引入新依赖（只用 fetch + 正则）
 *
 * 数据源：
 *   - 财联社 (cls.cn): content_score=100, 快讯型
 *   - 格隆汇 (gelonghui.com): content_score=90, 深度分析型
 *   - 智通财经 (zhitongcaijing.com): content_score=100, 港美股资讯型
 *   - 中国基金报 (chnfund.com): content_score=100, 基金/行业研究型
 *   - 华尔街见闻 (wallstreetcn.com): content_score=95, 深度市场解读型
 *   - Yahoo Finance (finance.yahoo.com): content_score=85, 海外市场数据型
 *   - Business Insider (businessinsider.com): content_score=85, 海外商业媒体型
 *   - Tavily Search (tavily.com): 按需搜索引擎，根据股票关键词搜索全网新闻
 *   - CNINFO 巨潮资讯网 (cninfo.com.cn): A股官方公告，POST API 查询
 *
 * 小白讲解：
 *   这个服务就像一个小"新闻探子"，专门去 4 个中文财经网站
 *   抓取最新新闻。它很轻量，不需要装额外的库，用浏览器
 *   一样的请求方式获取网页，然后用正则从网页里"抠"出新闻标题。
 */

/**
 * 解码 HTML 实体编码（如 &#x4F70; → 佰）
 *
 * 参数：
 *   str: 可能包含 HTML 实体的字符串
 * 返回：
 *   解码后的字符串
 */
function decodeHtmlEntities(str) {
  if (!str) return "";
  return str
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCharCode(parseInt(dec, 10)))
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

/**
 * 通用请求配置
 * 模拟浏览器访问，避免被网站拒绝
 */
const DEFAULT_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
  "Accept-Encoding": "gzip, deflate, br",
  "Connection": "keep-alive",
  "Upgrade-Insecure-Requests": "1",
};

/**
 * 带超时的 fetch 包装
 *
 * 参数：
 *   url: 请求地址
 *   options: fetch 选项
 *   timeoutMs: 超时时间（毫秒），默认 8000
 *
 * 返回：
 *   Response 对象，或超时抛出错误
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(url, { ...options, signal: controller.signal });
    return resp;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 全局缓存（避免多个子Agent重复抓取同一批新闻）
 * 缓存 5 分钟，减少对外部网站的请求压力
 */
let _cachedNews = null;
let _cachedAt = 0;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 分钟

/**
 * Firecrawl 源级别配置
 *
 * 说明：控制每个数据源是否启用 Firecrawl 正文补充，
 *       以及每个源对应的清洗规则和质量阈值。
 *
 * 配置项说明：
 *   enabled:       是否启用 Firecrawl
 *   maxPerFetch:   每次 fetchAll 中该源最多抓几条正文（避免请求过多）
 *   minBodyLength: 有效正文的最小长度（低于这个值认为抓取失败/质量差）
 *   cleaner:       内容清洗函数名（在 FIRECRAWL_CLEANERS 中定义），null 表示不清洗
 *
 * 小白讲解：
 *   这个配置就像一张"权限表"，告诉程序哪些新闻源需要
 *   用 Firecrawl 去抓正文、抓几条、抓到的内容要不要清洗。
 */
const FIRECRAWL_SOURCE_CONFIG = {
  wallstreet_cn:      { enabled: true,  maxPerFetch: 3, minBodyLength: 300,  cleaner: null },
  china_fund_news:    { enabled: true,  maxPerFetch: 3, minBodyLength: 300,  cleaner: null },
  gelonghui:          { enabled: true,  maxPerFetch: 3, minBodyLength: 300,  cleaner: "cleanGelonghui" },
  business_insider:   { enabled: true,  maxPerFetch: 2, minBodyLength: 500,  cleaner: null },
  cls_cn:             { enabled: true,  maxPerFetch: 3, minBodyLength: 300,  cleaner: "cleanClsCn" },
  zhitong_caijing:    { enabled: true,  maxPerFetch: 3, minBodyLength: 300,  cleaner: "cleanZhitong" },
  yahoo_finance:      { enabled: false, maxPerFetch: 2, minBodyLength: 500,  cleaner: null },
  tavily_search:      { enabled: false, maxPerFetch: 0, minBodyLength: 0,    cleaner: null },
  cninfo_announcement: { enabled: false, maxPerFetch: 0, minBodyLength: 0,   cleaner: null },
};

/**
 * Firecrawl 内容清洗函数集合
 *
 * 说明：每个函数接收原始 Markdown 正文，返回清洗后的正文。
 *       主要是去除导航、广告、页脚等噪声内容。
 */
const FIRECRAWL_CLEANERS = {
  /**
   * 清洗财联社正文
   *
   * 说明：财联社详情页有大量导航链接（关于我们/网站声明/首页/电报/话题...）
   *       堆在正文前面，需要找到真正的新闻内容起点。
   *
   * 参数：
   *   content: 原始 Markdown 正文
   *
   * 返回：
   *   清洗后的正文
   */
  cleanClsCn(content) {
    if (!content) return "";
    const lines = content.split("\n");

    // 财联社详情页的导航链接是折行的（如 "[首页\--](...)" 被分成两行），
    // 逐行匹配很难完全过滤。改用以下策略：
    // 1. 跳过所有纯Markdown链接行（单行短链接）
    // 2. 找到第一个出现的非导航类"###"标题行或长文本行作为正文起点
    // 3. 从起点向下截取

    const navTitleKeywords = [
      "全部", "加红", "深度", "公司", "行业", "市场", "数据", "视频",
      "电报", "话题", "盯盘", "VIP", "FM", "投研",
    ];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // 如果这行是 ### 开头的标题
      if (line.startsWith("### ")) {
        const titleText = line.replace(/^###\s*/, "").replace(/\[|\]\(.*?\)/g, "").trim();
        // 如果标题不是导航类关键词，认为找到了正文入口
        const isNavTitle = navTitleKeywords.some(kw => titleText.includes(kw));
        if (!isNavTitle && titleText.length > 5) {
          return lines.slice(i).join("\n").trim();
        }
        continue;
      }

      // 如果找到一行长度 > 80 的纯文本（不是链接），认为是正文开始
      if (line.length > 80 && !line.startsWith("[") && !line.endsWith(")")) {
        return lines.slice(i).join("\n").trim();
      }
    }

    // 如果找不到明确的正文入口，返回原文（至少比空好）
    return content.trim();
  },

  /**
   * 清洗格隆汇正文
   *
   * 说明：去除顶部的"首页 > 文章详情"面包屑和阅读量数字。
   *
   * 参数：
   *   content: 原始 Markdown 正文
   *
   * 返回：
   *   清洗后的正文
   */
  cleanGelonghui(content) {
    if (!content) return "";
    const lines = content.split("\n");
    let startIdx = 0;
    const skipPatterns = [
      /^\[首页\]\(.*\)$/,      // [首页](链接)
      /^\s*>\s*文章详情/,       // > 文章详情
      /^本文来自格隆汇/,        // 本文来自格隆汇专栏...
      /^[\d,]+\s*$/,           // 纯数字（阅读量）
      /^\d+小时前/,             // 几小时前
    ];
    for (let i = 0; i < Math.min(lines.length, 10); i++) {
      const line = lines[i].trim();
      if (!line) { startIdx = i + 1; continue; }
      const shouldSkip = skipPatterns.some(p => p.test(line));
      if (shouldSkip) {
        startIdx = i + 1;
      } else {
        break;
      }
    }
    return lines.slice(startIdx).join("\n").trim();
  },

  /**
   * 清洗智通财经正文
   *
   * 说明：智通财经详情页顶部有大量导航、广告、下载APP、分享按钮等噪声，
   *       正文内容大约在页面中部才开始。需要跳过顶部噪声，找到正文起点。
   *
   * 参数：
   *   content: 原始 Markdown 正文
   *
   * 返回：
   *   清洗后的正文
   */
  cleanZhitong(content) {
    if (!content) return "";
    const lines = content.split("\n");

    // 策略：找到第一个长度 > 50 且不是链接/图片/导航词的纯文本行
    const navKeywords = [
      "首页", "资讯", "行情", "数据", "日历", "路演", "主题",
      "下载智通财经APP", "智通媒体矩阵", "联系我们", "问题举报",
      "分享", "微信",
    ];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      if (line.startsWith("![")) continue; // 图片
      if (line.startsWith("[") && line.endsWith(")")) continue; // 链接
      if (navKeywords.some(kw => line === kw || line.startsWith(kw))) continue;
      if (line.length > 50) {
        return lines.slice(i).join("\n").trim();
      }
    }

    return content.trim();
  },
};

/**
 * 校验 Firecrawl 抓取内容的质量
 *
 * 说明：检查抓到的正文是不是有效内容，而不是错误页、空白页或全是导航。
 *
 * 参数：
 *   content: 抓取到的正文内容
 *   minLength: 最小长度阈值
 *   sourceId: 数据源ID（用于日志）
 *
 * 返回：
 *   { valid: boolean, reason: string } valid=true 表示内容有效
 */
function validateFirecrawlContent(content, minLength = 300, sourceId = "") {
  if (!content || content.trim().length === 0) {
    return { valid: false, reason: "内容为空" };
  }
  if (content.trim().length < minLength) {
    return { valid: false, reason: `内容过短（${content.trim().length}字 < ${minLength}字）` };
  }
  // 检查是否包含常见的错误页面关键词
  const errorPatterns = [
    "Oops, something went wrong",
    "404 Not Found",
    "页面不存在",
    "访问被拒绝",
    "请登录后继续",
    "Access Denied",
    /\{\{.*\}\}/,  // Vue/React 模板占位符
  ];
  for (const pat of errorPatterns) {
    if (pat instanceof RegExp ? pat.test(content) : content.includes(pat)) {
      return { valid: false, reason: "内容包含错误页面特征" };
    }
  }
  return { valid: true, reason: "" };
}

/**
 * 中文财经新闻服务类
 */
export class ChineseNewsService {
  /**
   * 构造函数
   */
  constructor() {
    this.stats = { totalFetched: 0, errors: [] };
  }

  /**
   * 清除缓存（测试或强制刷新时使用）
   */
  static clearCache() {
    _cachedNews = null;
    _cachedAt = 0;
  }

  /**
   * 抓取所有 4 个中文源的最新新闻
   *
   * 参数：
   *   limit: 每个源最多抓几条，默认 5 条
   *
   * 返回：
   *   合并后的新闻数组，按来源分组
   *
   * 小白讲解：
   *   同时去 4 个网站抓新闻，哪个成功算哪个，失败的记个日志。
   *   最后把所有新闻合并成一个列表返回。
   */
  async fetchAll(limit = 5) {
    // 检查缓存（全局共享，避免多个子Agent重复抓取）
    if (_cachedNews && Date.now() - _cachedAt < CACHE_TTL_MS) {
      return _cachedNews;
    }

    const results = await Promise.allSettled([
      this.fetchClsCn(limit),
      this.fetchGelonghui(limit),
      this.fetchZhitongcaijing(limit),
      this.fetchChinaFundNews(limit),
      this.fetchWallstreetCn(limit),
      this.fetchYahooFinance(limit),
      this.fetchBusinessInsider(limit),
    ]);

    const allNews = [];
    const sources = ["cls_cn", "gelonghui", "zhitong_caijing", "china_fund_news", "wallstreet_cn", "yahoo_finance", "business_insider"];

    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (result.status === "fulfilled") {
        allNews.push(...result.value);
        this.stats.totalFetched += result.value.length;
      } else {
        this.stats.errors.push({ source: sources[i], error: result.reason?.message || String(result.reason) });
      }
    }

    // 按发布时间倒序排列（最新的在前）
    allNews.sort((a, b) => {
      const ta = a.published_at ? new Date(a.published_at).getTime() : 0;
      const tb = b.published_at ? new Date(b.published_at).getTime() : 0;
      return tb - ta;
    });

    // 写入全局缓存
    _cachedNews = allNews;
    _cachedAt = Date.now();

    return allNews;
  }

  /**
   * 按股票名称/代码过滤相关新闻
   *
   * 参数：
   *   newsList: 新闻数组
   *   ticker: 股票代码（如 "300308.SZ"）
   *   stockName: 股票中文名称（如 "中际旭创"）
   *
   * 返回：
   *   与股票相关的新闻数组
   */
  filterByStock(newsList, ticker, stockName) {
    if (!ticker && !stockName) return [];
    const codeOnly = ticker ? ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "") : "";
    const keywords = [stockName, codeOnly].filter(Boolean);
    if (keywords.length === 0) return [];

    return newsList.filter((item) => {
      const text = `${item.title || ""} ${item.body || ""}`;
      return keywords.some((kw) => text.includes(kw));
    });
  }

  /**
   * 抓取财联社 (cls.cn) 最新新闻
   *
   * 参数：
   *   limit: 最多抓几条
   *
   * 返回：
   *   新闻对象数组
   */
  async fetchClsCn(limit = 5) {
    const resp = await fetchWithTimeout("https://www.cls.cn/", { headers: DEFAULT_HEADERS }, 10000);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const html = await resp.text();

    const news = [];
    // 财联社主页新闻格式：时间戳 + <a href="/detail/数字">标题</a>
    const regex = /<a[^>]*href="(\/detail\/\d+)"[^>]*>([^<]+)<\/a>/gi;

    let match;
    while ((match = regex.exec(html)) !== null && news.length < limit) {
      const url = match[1].startsWith("http") ? match[1] : `https://www.cls.cn${match[1]}`;
      const title = decodeHtmlEntities(match[2].trim());
      if (title.length < 5) continue; // 过滤太短的内容
      // 过滤导航类文本
      const navTexts = ["推荐", "港股", "A股", "美股", "新股", "首页", "行情", "搜索", "登录", "注册"];
      if (navTexts.includes(title)) continue;
      news.push({
        source_name: "财联社",
        source_id: "cls_cn",
        title,
        url,
        published_at: new Date().toISOString(), // 财联社主页没有精确日期，用当前时间
        body: "",
        language: "zh",
      });
    }

    return news;
  }

  /**
   * 抓取格隆汇 (gelonghui.com) 最新新闻
   *
   * 参数：
   *   limit: 最多抓几条
   *
   * 返回：
   *   新闻对象数组
   */
  async fetchGelonghui(limit = 5) {
    const resp = await fetchWithTimeout("https://www.gelonghui.com/", { headers: DEFAULT_HEADERS }, 10000);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const html = await resp.text();

    const news = [];
    // 格隆汇文章链接格式（桌面版 + 移动版混合）
    // 桌面版: <a href="/p/5592718">标题</a>
    // 移动版: <a href="https://m.gelonghui.com/p/5592718">标题</a>
    const regex = /<a[^>]*href="([^"]*\/p\/\d+)"[^>]*>([^<]+)<\/a>/gi;

    let match;
    while ((match = regex.exec(html)) !== null && news.length < limit) {
      const title = decodeHtmlEntities(match[2].trim());
      if (title.length < 5) continue;
      // 过滤导航类文本
      const navTexts = ["推荐", "港股", "A股", "美股", "新股", "首页", "行情", "搜索", "登录", "注册"];
      if (navTexts.includes(title)) continue;

      let url = match[1].trim();
      if (url.startsWith("/")) {
        url = `https://www.gelonghui.com${url}`;
      }

      news.push({
        source_name: "格隆汇",
        source_id: "gelonghui",
        title,
        url,
        published_at: new Date().toISOString(),
        body: "",
        language: "zh",
      });
    }

    return news;
  }

  /**
   * 抓取智通财经 (zhitongcaijing.com) 最新新闻
   *
   * 参数：
   *   limit: 最多抓几条
   *
   * 返回：
   *   新闻对象数组
   */
  async fetchZhitongcaijing(limit = 5) {
    const resp = await fetchWithTimeout("https://www.zhitongcaijing.com/", { headers: DEFAULT_HEADERS }, 10000);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const html = await resp.text();

    const news = [];
    // 智通财经文章链接格式：
    // <a href="/content/detail/数字.html">...<div>标题</div>...</a>
    // a标签内可能嵌套div等子元素，标题需要去除HTML标签后提取
    const regex = /<a[^>]*href="([^"]*content\/detail\/\d+\.html)"[^>]*>([\s\S]*?)<\/a>/gi;

    let match;
    while ((match = regex.exec(html)) !== null && news.length < limit) {
      // 去除标签内所有HTML标签，只保留纯文本作为标题
      const rawText = match[2].replace(/<[^>]+>/g, "").trim();
      const title = decodeHtmlEntities(rawText);
      if (title.length < 8) continue;
      // 过滤导航类文本
      const navTexts = ["推荐", "港股", "A股", "美股", "新股", "首页", "行情", "搜索", "登录", "注册"];
      if (navTexts.includes(title)) continue;

      let url = match[1].trim();
      if (url.startsWith("/")) {
        url = `https://www.zhitongcaijing.com${url}`;
      }

      // 去重：同一URL只保留一次
      if (news.some(n => n.url === url)) continue;

      news.push({
        source_name: "智通财经",
        source_id: "zhitong_caijing",
        title,
        url,
        published_at: new Date().toISOString(),
        body: "",
        language: "zh",
      });
    }

    return news;
  }

  /**
   * 抓取中国基金报 (chnfund.com) 最新新闻
   *
   * 参数：
   *   limit: 最多抓几条
   *
   * 返回：
   *   新闻对象数组
   */
  async fetchChinaFundNews(limit = 5) {
    const resp = await fetchWithTimeout("https://www.chnfund.com/", { headers: DEFAULT_HEADERS }, 10000);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const html = await resp.text();

    const news = [];
    // 中国基金报文章链接格式：<a href="/article/AR...">标题</a>
    const regex = /<a[^>]*href="(\/article\/AR[^"]+)"[^>]*>([^<]+)<\/a>/gi;

    let match;
    while ((match = regex.exec(html)) !== null && news.length < limit) {
      const title = decodeHtmlEntities(match[2].trim());
      if (title.length < 5) continue;
      // 过滤导航和固定文本
      const skipTexts = ["更多阅读 >>", "阅读更多 >>", "首页", "公募", "私募", "资管", "环球", "闪讯", "视频", "公司", "IPO", "投教"];
      if (skipTexts.includes(title)) continue;
      news.push({
        source_name: "中国基金报",
        source_id: "china_fund_news",
        title,
        url: `https://www.chnfund.com${match[1]}`,
        published_at: new Date().toISOString(),
        body: "",
        language: "zh",
      });
    }

    return news;
  }

  /**
   * 抓取华尔街见闻 (wallstreetcn.com) 最新新闻
   *
   * 说明：华尔街见闻首页包含 __SSR__ 变量，存储了文章数据。
   *       解析该变量获取文章标题和链接。
   *
   * 参数：
   *   limit: 最多抓几条
   *
   * 返回：
   *   新闻对象数组
   */
  async fetchWallstreetCn(limit = 5) {
    try {
      const resp = await fetchWithTimeout("https://wallstreetcn.com", { 
        headers: { "User-Agent": "Mozilla/5.0" } 
      }, 10000);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const html = await resp.text();

      const news = [];
      
      const ssrMatch = html.match(/<script>__SSR__\s*=\s*({[\s\S]*?})<\/script>/);
      if (ssrMatch) {
        try {
          const ssrData = JSON.parse(ssrMatch[1]);
          const items = ssrData?.state?.default?.children?.default?.data?.items || [];
          
          for (const item of items) {
            if (news.length >= limit) break;
            if (item.resource_type !== 'article') continue;
            
            const resource = item.resource;
            if (!resource?.title || !resource?.uri) continue;
            
            const title = decodeHtmlEntities(resource.title.trim());
            if (title.length < 5) continue;
            
            news.push({
              source_name: "华尔街见闻",
              source_id: "wallstreet_cn",
              title,
              url: resource.uri,
              published_at: resource.display_time 
                ? new Date(resource.display_time * 1000).toISOString() 
                : new Date().toISOString(),
              body: resource.content_short || "",
              language: "zh",
            });
          }
        } catch (e) {
          console.warn("[wallstreet_cn] SSR data parse failed:", e.message);
        }
      }
      
      if (news.length === 0) {
        const articleRegex = /<a[^>]*href="(\/articles\/\d+)"[^>]*>([^<]+)<\/a>/gi;
        let match;
        while ((match = articleRegex.exec(html)) !== null && news.length < limit) {
          const title = decodeHtmlEntities(match[2].trim());
          if (title.length < 8) continue;
          const skipTexts = ["推荐", "港股", "A股", "美股", "首页", "行情", "搜索", "登录", "注册"];
          if (skipTexts.includes(title)) continue;
          
          news.push({
            source_name: "华尔街见闻",
            source_id: "wallstreet_cn",
            title,
            url: `https://wallstreetcn.com${match[1]}`,
            published_at: new Date().toISOString(),
            body: "",
            language: "zh",
          });
        }
      }

      return news;
    } catch (e) {
      throw new Error(`华尔街见闻抓取失败: ${e.message}`);
    }
  }

  /**
   * 抓取 Yahoo Finance 全球市场新闻（使用 RSS 源）
   *
   * 参数：
   *   limit: 最多抓几条
   *
   * 返回：
   *   新闻对象数组
   */
  async fetchYahooFinance(limit = 5) {
    try {
      const resp = await fetchWithTimeout("https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL", { 
        headers: { "User-Agent": DEFAULT_HEADERS["User-Agent"] }, 
        timeoutMs: 10000 
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const xml = await resp.text();

      const news = [];
      const itemMatches = xml.match(/<item>([\s\S]*?)<\/item>/gi);
      
      if (itemMatches) {
        for (const item of itemMatches) {
          if (news.length >= limit) break;
          
          const titleMatch = item.match(/<title>([^<]*?)<\/title>/i);
          const linkMatch = item.match(/<link>([^<]*?)<\/link>/i);
          const pubDateMatch = item.match(/<pubDate>([^<]*?)<\/pubDate>/i);
          
          if (!titleMatch || !linkMatch) continue;
          
          const title = decodeHtmlEntities(titleMatch[1].trim());
          if (title.length < 8) continue;
          
          news.push({
            source_name: "Yahoo Finance",
            source_id: "yahoo_finance",
            title,
            url: linkMatch[1],
            published_at: pubDateMatch ? new Date(pubDateMatch[1]).toISOString() : new Date().toISOString(),
            body: "",
            language: "en",
          });
        }
      }

      return news;
    } catch (e) {
      throw new Error(`Yahoo Finance 抓取失败: ${e.message}`);
    }
  }

  /**
   * 抓取 Business Insider 新闻（使用 JSON-LD 结构化数据）
   *
   * 参数：
   *   limit: 最多抓几条
   *
   * 返回：
   *   新闻对象数组
   */
  async fetchBusinessInsider(limit = 5) {
    try {
      const resp = await fetchWithTimeout("https://www.businessinsider.com/news", { headers: DEFAULT_HEADERS }, 10000);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const html = await resp.text();

      const news = [];
      
      const jsonLdMatch = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
      if (jsonLdMatch) {
        try {
          const jsonLd = JSON.parse(jsonLdMatch[1]);
          const items = jsonLd?.mainEntity?.itemListElement || [];
          
          for (const item of items) {
            if (news.length >= limit) break;
            const url = item.url;
            if (!url) continue;
            
            const titleMatch = url.match(/\/([^\/]+)-\d{4}-\d{2}$/);
            let title = "";
            if (titleMatch) {
              title = titleMatch[1].replace(/-/g, ' ').trim();
            } else {
              const altMatch = url.match(/\/([^\/]+)$/);
              title = altMatch ? altMatch[1].replace(/-/g, ' ').trim() : url.substring(url.lastIndexOf('/') + 1);
            }
            
            title = title.replace(/\b(\d{4})\b/g, '').trim();
            title = title.replace(/\b(\d{1,2})\b/g, '').trim();
            title = title.replace(/\s+/g, ' ').trim();
            
            if (title.length < 5) continue;
            
            const words = title.split(' ');
            title = words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            
            news.push({
              source_name: "Business Insider",
              source_id: "business_insider",
              title,
              url,
              published_at: new Date().toISOString(),
              body: "",
              language: "en",
            });
          }
        } catch (e) {
          console.warn("[business_insider] JSON-LD parse failed:", e.message);
        }
      }

      if (news.length === 0) {
        const articleRegex = /<a[^>]*href="(\/articles\/[^"]+)"[^>]*>([^<]+)<\/a>/gi;
        let match;
        while ((match = articleRegex.exec(html)) !== null && news.length < limit) {
          const title = decodeHtmlEntities(match[2].trim());
          if (title.length < 10) continue;
          const skipTexts = ["Home", "Tech", "Finance", "Politics", "Business", "Markets", "Sign In", "Search"];
          if (skipTexts.includes(title)) continue;

          news.push({
            source_name: "Business Insider",
            source_id: "business_insider",
            title,
            url: `https://www.businessinsider.com${match[1]}`,
            published_at: new Date().toISOString(),
            body: "",
            language: "en",
          });
        }
      }

      return news;
    } catch (e) {
      throw new Error(`Business Insider 抓取失败: ${e.message}`);
    }
  }

  /**
   * 使用 Tavily Search API 搜索股票相关新闻
   *
   * 说明：Tavily 是一个通用网络搜索引擎 API，与上面直接抓取网站不同。
   *       它通过 POST 请求搜索全网内容，返回结构化的搜索结果。
   *       特别适合按股票名称/代码搜索最新新闻，弥补首页抓取无法定向搜索的不足。
   *
   * 参数：
   *   query: 搜索关键词（如 "中际旭创 财报" 或 "300308"）
   *   limit: 最多返回几条结果，默认 5
   *
   * 返回：
   *   新闻对象数组
   *
   * 异常处理：
   *   如果 API key 缺失，返回空数组（不抛异常，避免影响其他源）
   *   如果请求失败，抛出带详细信息的错误
   */
  async fetchTavilySearch(query, limit = 5, options = {}) {
    const apiKey = process.env.TAVILY_API_KEY || "";
    if (!apiKey) {
      console.warn("[tavily_search] TAVILY_API_KEY 未配置，跳过 Tavily 搜索");
      return [];
    }

    try {
      const resp = await fetchWithTimeout("https://api.tavily.com/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          api_key: apiKey,
          query: query,
          max_results: limit,
          search_depth: "advanced", // 用 advanced 深度搜索，获取更完整的内容
          topic: options.topic || "general",
          ...(options.days ? { days: options.days } : {}),
          ...(options.includeDomains?.length ? { include_domains: options.includeDomains } : {}),
        }),
      }, 15000);

      if (!resp.ok) {
        const errText = await resp.text().catch(() => "");
        throw new Error(`HTTP ${resp.status}: ${errText.substring(0, 200)}`);
      }

      const data = await resp.json();
      const results = data.results || [];

      const news = [];
      for (const item of results) {
        if (news.length >= limit) break;
        if (!item.title || !item.url) continue;

        const fetchedAt = new Date().toISOString();
        news.push({
          source_name: "Tavily Search",
          source_id: "tavily_search",
          title: item.title,
          url: item.url,
          published_at: item.published_date
            ? new Date(item.published_date).toISOString()
            : null,
          fetched_at: fetchedAt,
          date_precision: item.published_date ? "source" : "unknown",
          body: item.content || "",
          language: "mixed",
        });
      }

      return news;
    } catch (e) {
      throw new Error(`Tavily 搜索失败: ${e.message}`);
    }
  }

  /**
   * 多维度 Tavily 搜索：围绕一只股票从多个角度获取高价值信息
   *
   * 功能：
   *   对单只股票执行 4 个维度的 Tavily 搜索，获取高质量投研信息：
   *   1. 目标价和评级（卖方一致预期）
   *   2. 业绩说明会和纪要（管理层指引）
   *   3. 最新消息和公告（基本面动态）
   *   4. 华尔街/海外分析师观点（针对美股/港股，或A股的海外映射）
   *
   * 参数：
   *   stockName: 股票中文名（如 "海光信息"）
   *   ticker: 股票代码（如 "688041.SH"）
   *   perDimension: 每个维度最多返回几条，默认 3 条
   *
   * 返回：
   *   合并后的 Tavily 新闻数组（带 dimension 标签，方便后续区分）
   *
   * 小白讲解：
   *   原来只搜一次"海光信息 最新消息"，信息太单薄。
   *   现在改成搜 4 次：目标价、纪要、新闻、华尔街观点，
   *   这样能拿到分析师评级、管理层指引等高价值投研信息。
   */
  async fetchTavilyMultiDimension(stockName, ticker, perDimension = 3) {
    const apiKey = process.env.TAVILY_API_KEY || "";
    if (!apiKey) {
      console.warn("[tavily_search] TAVILY_API_KEY 未配置，跳过多维度搜索");
      return [];
    }

    // 4 个搜索维度（覆盖卖方预期、管理层指引、基本面、海外观点）
    const dimensions = [
      {
        key: "target_price_rating",
        query: `${stockName} 目标价 评级 研报 分析师`,
        label: "目标价与评级",
      },
      {
        key: "earnings_guidance",
        query: `${stockName} 业绩说明会 纪要 指引 电话会`,
        label: "业绩纪要与指引",
      },
      {
        key: "latest_news",
        query: `${stockName} 最新消息 财报 业绩`,
        label: "最新动态",
      },
      {
        key: "overseas_view",
        query: `${stockName} 海外 华尔街 analyst target price rating`,
        label: "海外分析师观点",
      },
    ];

    const allResults = [];

    // 并行执行 4 个维度的搜索（提高效率）
    const searchPromises = dimensions.map(async (dim) => {
      try {
        const results = await this.fetchTavilySearch(dim.query, perDimension);
        // 给每条结果打上维度标签
        return results.map(r => ({
          ...r,
          dimension: dim.key,
          dimension_label: dim.label,
          source_name: `Tavily-${dim.label}`,
        }));
      } catch (e) {
        console.warn(`[tavily_multidim] 维度 "${dim.key}" 搜索失败:`, e.message);
        return [];
      }
    });

    const dimensionResults = await Promise.allSettled(searchPromises);
    for (const result of dimensionResults) {
      if (result.status === "fulfilled" && result.value) {
        allResults.push(...result.value);
      }
    }

    console.log(`[tavily_multidim] ${stockName} 共获取 ${allResults.length} 条多维度信息`);
    return allResults;
  }

  /**
   * 从 CNINFO（巨潮资讯网）查询 A 股官方公告
   *
   * 说明：巨潮资讯网是深交所/上交所官方信息披露平台，
   *       通过 POST API 按股票代码查询最新公告（年报、季报、临时公告等）。
   *       这与新闻网站不同，提供的是交易所官方披露的一手信息。
   *
   * 参数：
   *   stockCode: 股票代码（如 "300308" 或 "000063"），不含交易所后缀
   *   limit: 最多返回几条，默认 5
   *
   * 返回：
   *   新闻对象数组（source_name 为 "CNINFO 巨潮资讯"）
   *
   * 异常处理：
   *   请求失败时抛出带详细信息的错误
   *
   * 小白讲解：
   *   巨潮资讯网就像 A 股的"官方公告栏"，所有上市公司必须在这里
   *   发布年报、季报、重大事项公告。我们用 POST 方式查询某只股票
   *   的最新公告，获取最权威的一手信息。
   */
  async fetchCninfoAnnouncements(stockCode, limit = 5) {
    if (!stockCode) return [];

    try {
      const formData = new URLSearchParams({
        stock: "",
        tabName: "fulltext",
        pageSize: String(limit),
        pageNum: "1",
        column: "szse",
        category: "",
        plate: "",
        seDate: "",
        searchkey: stockCode,
        secid: "",
        asset: "",
        keyWord: "",
        isHLtitle: "true",
      });

      const resp = await fetchWithTimeout("https://www.cninfo.com.cn/new/hisAnnouncement/query", {
        method: "POST",
        headers: {
          "User-Agent": DEFAULT_HEADERS["User-Agent"],
          "Content-Type": "application/x-www-form-urlencoded",
          "Accept": "application/json, text/plain, */*",
          "Origin": "https://www.cninfo.com.cn",
          "Referer": "https://www.cninfo.com.cn/new/hisAnnouncement/query",
        },
        body: formData.toString(),
      }, 15000);

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();
      const announcements = data.announcements || data.data || data.list || [];

      const news = [];
      for (const item of announcements) {
        if (news.length >= limit) break;

        const title = (item.announcementTitle || item.title || "").replace(/<\/?em>/g, "");
        const annId = item.announcementId || item.id || "";
        const secCode = item.secCode || item.stockCode || item.code || stockCode;
        const secName = (item.secName || item.stockName || item.name || "").replace(/<\/?em>/g, "");
        const adjunctUrl = item.adjunctUrl || item.pdfUrl || item.fileUrl || "";

        if (!title) continue;

        // 解析公告时间（毫秒时间戳或日期字符串）
        let publishedAt = new Date().toISOString();
        const timeVal = item.announcementTime || item.time || item.date;
        if (timeVal) {
          if (typeof timeVal === "number") {
            publishedAt = new Date(timeVal > 1e12 ? timeVal : timeVal * 1000).toISOString();
          } else {
            const parsed = new Date(timeVal);
            if (!isNaN(parsed.getTime())) publishedAt = parsed.toISOString();
          }
        }

        // PDF 链接拼接
        let pdfUrl = "";
        if (adjunctUrl) {
          pdfUrl = adjunctUrl.startsWith("http")
            ? adjunctUrl
            : `https://www.cninfo.com.cn/${adjunctUrl}`;
        }

        // 详情页链接
        const detailUrl = `https://www.cninfo.com.cn/new/disclosure/detail?stockCode=${secCode}&announcementId=${annId}`;

        news.push({
          source_name: "CNINFO 巨潮资讯",
          source_id: "cninfo_announcement",
          title: `${secName ? `[${secName}] ` : ""}${title}`,
          url: detailUrl,
          published_at: publishedAt,
          body: pdfUrl ? `公告PDF: ${pdfUrl}` : "",
          language: "zh",
        });
      }

      return news;
    } catch (e) {
      throw new Error(`CNINFO 巨潮资讯抓取失败: ${e.message}`);
    }
  }

  /**
   * 使用 Firecrawl 提取网页正文内容
   *
   * 说明：Firecrawl 是一个网页内容提取工具，能把任意网页转成干净的 Markdown。
   *       它会自动处理 JS 渲染、去除广告/导航/页脚等噪声，只保留正文。
   *       本方法调用本地自托管的 Firecrawl 实例（http://localhost:3002）。
   *
   * 参数：
   *   url: 要提取内容的网页 URL
   *
   * 返回：
   *   对象 { title, content, markdown }，提取失败返回 null
   *
   * 异常处理：
   *   如果 Firecrawl 服务不可用或请求失败，返回 null（不抛异常，避免影响主流程）
   *
   * 小白讲解：
   *   比如你有一篇华尔街见闻的文章链接，用普通 fetch 只能拿到 HTML 源码
   *   （一大堆乱七八糟的标签），但用 Firecrawl 就能直接拿到干净的文章正文，
   *   就像"只读模式"的浏览器，帮你把废话都过滤掉了。
   */
  async scrapeWithFirecrawl(url) {
    if (!url) return null;

    try {
      const resp = await fetchWithTimeout("http://localhost:3002/v1/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          formats: ["markdown"],
          onlyMainContent: true,
        }),
      }, 30000);

      if (!resp.ok) {
        console.warn(`[firecrawl] HTTP ${resp.status} for ${url}`);
        return null;
      }

      const data = await resp.json();
      if (!data || !data.data) return null;

      return {
        title: data.data.metadata?.title || "",
        content: data.data.markdown || "",
        markdown: data.data.markdown || "",
      };
    } catch (e) {
      console.warn(`[firecrawl] scrape failed for ${url}: ${e.message}`);
      return null;
    }
  }

  /**
   * 对已有新闻列表用 Firecrawl 补充正文内容（按源配置执行）
   *
   * 说明：很多新闻源只抓到了标题和链接，body 是空的。
   *       用 Firecrawl 逐条抓取文章正文，填充 body 字段。
   *       根据 FIRECRAWL_SOURCE_CONFIG 控制哪些源启用、抓几条、是否清洗。
   *
   * 参数：
   *   newsList: 新闻对象数组
   *   options: 可选配置 { maxTotalScrape: 总共最多抓几条（所有源合计），默认10 }
   *
   * 返回：
   *   补充了 body 的数组（原数组会被修改），同时返回统计信息
   *
   * 小白讲解：
   *   就像给新闻列表"填空"——哪些源需要补充正文、补充几条，
   *   都按配置表来执行。抓到的内容还会过一下"质量检测"，
   *   不合格的就丢掉不用。
   */
  async enrichWithFirecrawl(newsList, options = {}) {
    const maxTotal = options.maxTotalScrape || 10;

    // 按源分组
    const bySource = {};
    for (const news of newsList) {
      const sid = news.source_id || "";
      if (!bySource[sid]) bySource[sid] = [];
      bySource[sid].push(news);
    }

    let totalScraped = 0;
    let totalSuccess = 0;
    const stats = {}; // 每源的统计

    for (const [sourceId, list] of Object.entries(bySource)) {
      const config = FIRECRAWL_SOURCE_CONFIG[sourceId];
      if (!config || !config.enabled) {
        stats[sourceId] = { attempted: 0, success: 0, skipped: "未启用" };
        continue;
      }

      let sourceAttempted = 0;
      let sourceSuccess = 0;

      for (const news of list) {
        if (totalScraped >= maxTotal) break;
        if (sourceAttempted >= config.maxPerFetch) break;
        if (news.body && news.body.length > config.minBodyLength) continue; // 已有足够正文就跳过
        if (!news.url) continue;

        sourceAttempted++;
        totalScraped++;

        const result = await this.scrapeWithFirecrawl(news.url);
        if (!result || !result.content) continue;

        let cleanContent = result.content;

        // 按配置调用清洗函数
        if (config.cleaner && FIRECRAWL_CLEANERS[config.cleaner]) {
          cleanContent = FIRECRAWL_CLEANERS[config.cleaner](cleanContent);
        }

        // 质量校验
        const quality = validateFirecrawlContent(cleanContent, config.minBodyLength, sourceId);
        if (!quality.valid) {
          console.warn(`[firecrawl] ${sourceId} 内容质量不达标(${quality.reason}): ${news.url.substring(0, 60)}`);
          continue;
        }

        // 写入正文
        news.body = cleanContent.substring(0, 2000);
        news.title = news.title || result.title;
        sourceSuccess++;
        totalSuccess++;
      }

      stats[sourceId] = { attempted: sourceAttempted, success: sourceSuccess };
    }

    console.log(`[firecrawl] 正文补充完成：尝试 ${totalScraped} 条，成功 ${totalSuccess} 条`);

    // 返回值同时兼容两种用法：
    // - 老代码：直接当数组用（newsList）
    // - 新代码：解构获取 stats 等统计信息
    newsList.stats = stats;
    newsList.totalScraped = totalScraped;
    newsList.totalSuccess = totalSuccess;
    return newsList;
  }
}
