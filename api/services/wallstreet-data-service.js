/**
 * 华尔街分析师评级数据服务
 *
 * 功能：
 *   1. 获取美股分析师评级（Buy/Hold/Sell等）
 *   2. 获取目标价（Target Price）
 *   3. 获取评级变动趋势
 *   4. 获取盈利预测
 *
 * 数据源优先级：
 *   1. Finnhub API（最推荐，结构化数据，免费额度60次/分钟）
 *   2. Morningstar（备选，网页抓取，含星级评级和公允价值）
 *   3. Benzinga（次备选，网页抓取，含评级和目标价）
 *
 * 小白讲解：
 *   这个服务就像一个"华尔街分析师情报员"：
 *   - 分析师评级：看华尔街大佬们是看多还是看空
 *   - 目标价：分析师认为这只股票值多少钱
 *   - 评级变动：最近有没有分析师上调或下调评级
 *   - 这些数据对判断美股趋势非常重要！
 */

const WH_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
};

/**
 * 带超时的 fetch 包装
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 华尔街数据服务类
 */
export class WallstreetDataService {
  constructor() {
    this.finnhubApiKey = process.env.FINNHUB_API_KEY || '';
    this.stats = { totalFetched: 0, errors: [] };
  }

  /**
   * 获取美股分析师评级（Finnhub API）
   *
   * 参数：
   *   symbol: 股票代码（如 "AAPL"）
   *
   * 返回：
   *   评级数据对象，包含 buy/hold/sell数量、目标价、评级变动等
   *   失败返回空对象
   *
   * 小白讲解：
   *   Finnhub是一个提供金融数据的API，免费额度够用。
   *   返回的数据包括：有多少分析师给买入评级、多少给持有、多少给卖出，
   *   以及他们的平均目标价。这些数据非常有参考价值。
   */
  async getAnalystRatings(symbol) {
    if (!symbol) return {};

    // 优先使用Finnhub API
    if (this.finnhubApiKey) {
      const result = await this._getFromFinnhub(symbol);
      if (result && Object.keys(result).length > 0) {
        return result;
      }
    }

    // 备用方案：网页抓取
    console.log(`[wallstreet] Finnhub不可用，尝试网页抓取 ${symbol}`);
    const morningstar = await this._getFromMorningstar(symbol);
    if (morningstar && morningstar.fairValue) {
      return morningstar;
    }

    const benzinga = await this._getFromBenzinga(symbol);
    if (benzinga && benzinga.targetPrice) {
      return benzinga;
    }

    return {};
  }

  /**
   * 获取目标价变动历史
   *
   * 参数：
   *   symbol: 股票代码
   *
   * 返回：
   *   目标价变动数组
   */
  async getPriceTargetHistory(symbol) {
    if (!symbol || !this.finnhubApiKey) return [];

    try {
      const url = `https://finnhub.io/api/v1/stock/price-target?symbol=${symbol}&token=${this.finnhubApiKey}`;
      const resp = await fetchWithTimeout(url, {}, 10000);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const data = await resp.json();
      if (!data || !data.targets) return [];

      return data.targets.map(t => ({
        date: t.date || '',
        targetPrice: t.price || 0,
        analyst: t.analyst || '',
        company: t.company || '',
      }));
    } catch (e) {
      console.warn(`[wallstreet] 目标价历史获取失败 ${symbol}:`, e.message);
      return [];
    }
  }

  /**
   * 获取公司新闻（最近一周）
   *
   * 参数：
   *   symbol: 股票代码
   *   days: 最近多少天，默认7天
   *
   * 返回：
   *   新闻数组，每条含 {date, headline, source, url, summary}
   */
  async getCompanyNews(symbol, days = 7) {
    if (!symbol || !this.finnhubApiKey) return [];

    try {
      const to = Math.floor(Date.now() / 1000);
      const from = to - days * 24 * 60 * 60;
      const url = `https://finnhub.io/api/v1/company-news?symbol=${symbol}&from=${new Date(from * 1000).toISOString().substring(0, 10)}&to=${new Date(to * 1000).toISOString().substring(0, 10)}&token=${this.finnhubApiKey}`;
      const resp = await fetchWithTimeout(url, {}, 10000);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const data = await resp.json();
      return data.slice(0, 10).map(n => ({
        date: n.datetime ? new Date(n.datetime * 1000).toLocaleString('zh-CN') : '',
        headline: n.headline || '',
        source: n.source || '',
        url: n.url || '',
        summary: n.summary || '',
      }));
    } catch (e) {
      console.warn(`[wallstreet] 公司新闻获取失败 ${symbol}:`, e.message);
      return [];
    }
  }

  /**
   * 从Finnhub API获取评级数据
   */
  async _getFromFinnhub(symbol) {
    try {
      const url = `https://finnhub.io/api/v1/stock/recommendation?symbol=${symbol}&token=${this.finnhubApiKey}`;
      const resp = await fetchWithTimeout(url, {}, 10000);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const data = await resp.json();
      if (!data || data.length === 0) return {};

      const latest = data[0];
      const total = (latest.buy || 0) + (latest.outperform || 0) + (latest.hold || 0) + (latest.underperform || 0) + (latest.sell || 0);

      this.stats.totalFetched++;
      return {
        source: 'finnhub',
        symbol,
        period: latest.period || '',
        buy: latest.buy || 0,
        outperform: latest.outperform || 0,
        hold: latest.hold || 0,
        underperform: latest.underperform || 0,
        sell: latest.sell || 0,
        totalAnalysts: total,
        buyRatio: total > 0 ? ((latest.buy || 0) / total * 100).toFixed(1) : '0',
        sellRatio: total > 0 ? ((latest.sell || 0) / total * 100).toFixed(1) : '0',
        targetMeanPrice: latest.targetMeanPrice || null,
        targetHighPrice: latest.targetHighPrice || null,
        targetLowPrice: latest.targetLowPrice || null,
        currentPrice: latest.price || null,
        upside: latest.targetMeanPrice && latest.price
          ? (((latest.targetMeanPrice - latest.price) / latest.price) * 100).toFixed(1)
          : null,
      };
    } catch (e) {
      this.stats.errors.push({ source: 'finnhub', symbol, error: e.message });
      console.warn(`[wallstreet] Finnhub获取失败 ${symbol}:`, e.message);
      return {};
    }
  }

  /**
   * 从Morningstar网页抓取评级数据
   */
  async _getFromMorningstar(symbol) {
    try {
      const url = `https://www.morningstar.com/stocks/xnas/${symbol.toLowerCase()}/quote`;
      const resp = await fetchWithTimeout(url, { headers: WH_HEADERS }, 15000);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const html = await resp.text();

      let starRating = null;
      const starMatch = html.match(/(\d)\s*Star\s*Rating/i);
      if (starMatch) starRating = parseInt(starMatch[1]);

      let fairValue = null;
      const fairValueMatch = html.match(/Fair\s*Value[^$]*\$([\d.]+)/i);
      if (fairValueMatch) {
        fairValue = parseFloat(fairValueMatch[1]);
      } else {
        const fvJsonMatch = html.match(/"fairValue":\s*"([^"]+)"/);
        if (fvJsonMatch) fairValue = parseFloat(fvJsonMatch[1]);
      }

      let currentPrice = null;
      const priceMatch = html.match(/Current\s*Price[^$]*\$([\d.]+)/i);
      if (priceMatch) currentPrice = parseFloat(priceMatch[1]);

      let ratingText = null;
      const ratingMatch = html.match(/ratingText["']:\s*["']([^"']+)["']/);
      if (ratingMatch) ratingText = ratingMatch[1];

      if (starRating || fairValue) {
        this.stats.totalFetched++;
        return {
          source: 'morningstar',
          symbol,
          starRating,
          fairValue,
          currentPrice,
          ratingText,
          upside: fairValue && currentPrice
            ? (((fairValue - currentPrice) / currentPrice) * 100).toFixed(1)
            : null,
        };
      }

      return {};
    } catch (e) {
      this.stats.errors.push({ source: 'morningstar', symbol, error: e.message });
      console.warn(`[wallstreet] Morningstar抓取失败 ${symbol}:`, e.message);
      return {};
    }
  }

  /**
   * 从Benzinga网页抓取评级数据
   */
  async _getFromBenzinga(symbol) {
    try {
      const url = `https://www.benzinga.com/quote/${symbol}`;
      const resp = await fetchWithTimeout(url, { headers: WH_HEADERS }, 15000);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const html = await resp.text();

      let targetPrice = null;
      const targetMatch = html.match(/Price\s*Target[^$]*\$([\d.]+)/i);
      if (targetMatch) {
        targetPrice = parseFloat(targetMatch[1]);
      } else {
        const targetJsonMatch = html.match(/"targetPrice"\s*:\s*"([^"]+)"/);
        if (targetJsonMatch) targetPrice = parseFloat(targetJsonMatch[1]);
      }

      let currentPrice = null;
      const priceMatch = html.match(/"price"\s*:\s*"([^"]+)"/);
      if (priceMatch) currentPrice = parseFloat(priceMatch[1]);

      let rating = null;
      const ratingMatch = html.match(/"rating"\s*:\s*"([^"]+)"/);
      if (ratingMatch) rating = ratingMatch[1];

      let analystCount = null;
      const analystMatch = html.match(/(\d+)\s+analyst/i);
      if (analystMatch) analystCount = parseInt(analystMatch[1]);

      if (targetPrice || rating) {
        this.stats.totalFetched++;
        return {
          source: 'benzinga',
          symbol,
          targetPrice,
          currentPrice,
          rating,
          analystCount,
          upside: targetPrice && currentPrice
            ? (((targetPrice - currentPrice) / currentPrice) * 100).toFixed(1)
            : null,
        };
      }

      return {};
    } catch (e) {
      this.stats.errors.push({ source: 'benzinga', symbol, error: e.message });
      console.warn(`[wallstreet] Benzinga抓取失败 ${symbol}:`, e.message);
      return {};
    }
  }

  /**
   * 一键获取所有华尔街数据（评级+目标价历史+新闻）
   *
   * 参数：
   *   symbol: 股票代码
   *
   * 返回：
   *   { ratings, priceTargets, news }
   */
  async getAllWallstreetData(symbol) {
    console.log(`[wallstreet] 开始获取 ${symbol} 的华尔街数据`);

    const [ratings, priceTargets, news] = await Promise.allSettled([
      this.getAnalystRatings(symbol),
      this.getPriceTargetHistory(symbol),
      this.getCompanyNews(symbol, 7),
    ]);

    const result = {
      ratings: ratings.status === "fulfilled" ? ratings.value : {},
      priceTargets: priceTargets.status === "fulfilled" ? priceTargets.value : [],
      news: news.status === "fulfilled" ? news.value : [],
    };

    const source = result.ratings.source || 'none';
    const analystCount = result.ratings.totalAnalysts || result.ratings.analystCount || 0;
    console.log(`[wallstreet] ${symbol} 华尔街数据: 来源=${source}, 分析师${analystCount}人, 目标价${result.priceTargets.length}条, 新闻${result.news.length}条`);

    return result;
  }

  /**
   * 把华尔街数据格式化为LLM可读的文本
   *
   * 参数：
   *   data: getAllWallstreetData返回的对象
   *
   * 返回：
   *   格式化的文本字符串
   */
  formatForLLM(data) {
    if (!data || (!data.ratings && !data.priceTargets && !data.news)) {
      return "无华尔街数据（需配置FINNHUB_API_KEY或使用网页抓取）";
    }

    let text = "";

    // 1. 分析师评级
    if (data.ratings && Object.keys(data.ratings).length > 0) {
      const r = data.ratings;
      text += `\n### 🏦 华尔街分析师评级（来源: ${r.source.toUpperCase()}）\n`;

      if (r.source === 'finnhub') {
        text += `| 评级类型 | 数量 | 占比 |\n`;
        text += `|---|---|---|\n`;
        const total = r.totalAnalysts || 1;
        text += `| 👍 Buy（买入） | ${r.buy || 0} | ${((r.buy || 0) / total * 100).toFixed(1)}% |\n`;
        text += `| ⬆️ Outperform（跑赢大盘） | ${r.outperform || 0} | ${((r.outperform || 0) / total * 100).toFixed(1)}% |\n`;
        text += `| 👐 Hold（持有） | ${r.hold || 0} | ${((r.hold || 0) / total * 100).toFixed(1)}% |\n`;
        text += `| ⬇️ Underperform（跑输大盘） | ${r.underperform || 0} | ${((r.underperform || 0) / total * 100).toFixed(1)}% |\n`;
        text += `| 👎 Sell（卖出） | ${r.sell || 0} | ${((r.sell || 0) / total * 100).toFixed(1)}% |\n`;

        if (r.targetMeanPrice) {
          text += `\n**目标价分析**:\n`;
          text += `- 目标价均值: $${r.targetMeanPrice}\n`;
          if (r.targetHighPrice) text += `- 目标价最高: $${r.targetHighPrice}\n`;
          if (r.targetLowPrice) text += `- 目标价最低: $${r.targetLowPrice}\n`;
          if (r.currentPrice) {
            text += `- 当前价格: $${r.currentPrice}\n`;
            text += `- 上行空间: ${r.upside || 0}%\n`;
          }
        }
      } else if (r.source === 'morningstar') {
        text += `- ⭐ 星级评级: ${r.starRating || 'N/A'}星\n`;
        text += `- 💰 公允价值: $${r.fairValue || 'N/A'}\n`;
        if (r.currentPrice) {
          text += `- 当前价格: $${r.currentPrice}\n`;
          text += `- 上行空间: ${r.upside || 0}%\n`;
        }
        text += `- 📝 评级文字: ${r.ratingText || 'N/A'}\n`;
      } else if (r.source === 'benzinga') {
        text += `- 📊 评级: ${r.rating || 'N/A'}\n`;
        text += `- 🎯 目标价: $${r.targetPrice || 'N/A'}\n`;
        if (r.currentPrice) {
          text += `- 当前价格: $${r.currentPrice}\n`;
          text += `- 上行空间: ${r.upside || 0}%\n`;
        }
        text += `- 👥 分析师数量: ${r.analystCount || 'N/A'}人\n`;
      }
    }

    // 2. 目标价变动历史
    if (data.priceTargets && data.priceTargets.length > 0) {
      text += `\n### 📈 目标价变动历史（最近${data.priceTargets.length}条）\n`;
      for (const t of data.priceTargets.slice(0, 5)) {
        text += `- ${t.date || 'N/A'}: ${t.analyst || t.company || '分析师'} → $${t.targetPrice}\n`;
      }
    }

    // 3. 公司新闻
    if (data.news && data.news.length > 0) {
      text += `\n### 📰 公司新闻（最近一周，${data.news.length}条）\n`;
      for (const n of data.news.slice(0, 5)) {
        text += `- ${n.date || ''} [${n.source || '未知'}] ${n.headline || ''}\n`;
      }
    }

    return text || "无华尔街数据";
  }

  /**
   * 检查Finnhub API是否可用
   */
  isFinnhubAvailable() {
    return !!this.finnhubApiKey;
  }
}