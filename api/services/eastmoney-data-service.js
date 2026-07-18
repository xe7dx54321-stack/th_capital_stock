/**
 * 东方财富增强数据服务
 *
 * 功能：
 *   1. 获取个股资金流向（主力资金、超大单、大单、中单、小单）
 *   2. 获取龙虎榜数据（机构席位买卖）
 *   3. 获取多季度历史财务数据（营收/净利趋势、单季度同比环比）
 *
 * 数据源：东方财富公开API（免费，无需key）
 *
 * 小白讲解：
 *   这个服务就像一个"资金监控器+财务趋势分析仪"：
 *   - 资金流向：看主力资金是在流入还是流出（聪明钱在做什么）
 *   - 龙虎榜：看机构席位是在买还是卖
 *   - 财务趋势：看营收和利润是加速增长还是减速（多季度对比）
 */

/**
 * 通用请求头（模拟浏览器访问）
 */
const EM_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
  "Referer": "https://data.eastmoney.com/",
  "Accept": "application/json, text/plain, */*",
};

/**
 * 带超时的 fetch 包装
 *
 * 参数：
 *   url: 请求地址
 *   timeoutMs: 超时毫秒，默认10000
 *
 * 返回：
 *   Response 对象
 */
async function fetchEM(url, timeoutMs = 10000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { headers: EM_HEADERS, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 把股票代码转换为东方财富的secid格式
 * 上交所(6开头、688开头) → 1.代码
 * 深交所(0开头、3开头) → 0.代码
 * 北交所(8开头) → 0.代码
 *
 * 参数：
 *   ticker: 股票代码（如 "688041.SH" 或 "300308.SZ"）
 *
 * 返回：
 *   secid字符串（如 "1.688041"）
 */
function tickerToSecid(ticker) {
  if (!ticker) return "";
  const code = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
  // 6开头(上交所主板)、688开头(科创板)、9开头(B股) → 上交所，market=1
  if (/^(6|688|9)/.test(code)) {
    return `1.${code}`;
  }
  // 0开头(深交所主板)、3开头(创业板)、8开头(北交所) → 深交所/北交所，market=0
  return `0.${code}`;
}

/**
 * 把股票代码转换为东方财富的SECURITY_CODE格式（纯数字）
 *
 * 参数：
 *   ticker: 股票代码（如 "688041.SH"）
 *
 * 返回：
 *   纯数字代码（如 "688041"）
 */
function tickerToCode(ticker) {
  if (!ticker) return "";
  return ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
}

/**
 * 东方财富增强数据服务类
 */
export class EastmoneyDataService {
  constructor() {
    this.stats = { totalFetched: 0, errors: [] };
  }

  /**
   * 获取个股主力资金流向（最近N天）
   *
   * 参数：
   *   ticker: 股票代码（如 "688041.SH"）
   *   days: 获取最近几天的数据，默认5天
   *
   * 返回：
   *   资金流向数组，每条含 {date, mainNet, superLargeNet, largeNet, mediumNet, smallNet, mainNetPct, closePrice}
   *   失败返回空数组
   *
   * 小白讲解：
   *   主力资金=超大单+大单。如果主力净流入为正，说明大资金在买入；
   *   如果为负，说明大资金在卖出。这是判断"聪明钱"动向的核心指标。
   */
  async getFundFlow(ticker, days = 5) {
    const secid = tickerToSecid(ticker);
    if (!secid) return [];

    const url = `https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=${secid}&lmt=${days}&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65`;

    try {
      const resp = await fetchEM(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const klines = data?.data?.klines || [];
      const flows = [];

      for (const line of klines) {
        // 格式: 日期,主力净流入,小单,中单,大单,超大单,主力净流入占比,小单占比,中单占比,大单占比,超大单占比,收盘价,涨跌幅,...
        const parts = line.split(',');
        if (parts.length < 13) continue;

        flows.push({
          date: parts[0],
          mainNet: parseFloat(parts[1]) || 0,           // 主力净流入（元）
          smallNet: parseFloat(parts[2]) || 0,          // 小单净流入
          mediumNet: parseFloat(parts[3]) || 0,         // 中单净流入
          largeNet: parseFloat(parts[4]) || 0,          // 大单净流入
          superLargeNet: parseFloat(parts[5]) || 0,     // 超大单净流入
          mainNetPct: parseFloat(parts[6]) || 0,        // 主力净流入占比%
          closePrice: parseFloat(parts[11]) || 0,       // 收盘价
          changePct: parseFloat(parts[12]) || 0,        // 涨跌幅%
        });
      }

      this.stats.totalFetched += flows.length;
      return flows;
    } catch (e) {
      this.stats.errors.push({ source: "fund_flow", error: e.message });
      console.warn(`[eastmoney] 资金流向获取失败 ${ticker}:`, e.message);
      return [];
    }
  }

  /**
   * 获取龙虎榜数据（机构席位买卖）
   *
   * 参数：
   *   ticker: 股票代码
   *   limit: 最多返回几条，默认3条
   *
   * 返回：
   *   龙虎榜数组，每条含 {date, reason, netBuy, buyAmt, sellAmt, changePct, d1Change, d5Change, d10Change, d20Change, d30Change}
   *
   * 小白讲解：
   *   龙虎榜是交易所公布的"异动股"买卖明细。如果机构席位净买入，说明机构看好；
   *   如果机构净卖出，说明机构在撤退。d1/d5/d10/d20/d30是上榜后1/5/10/20/30天的涨跌幅，
   *   可以用来评估龙虎榜信号的准确性。
   */
  async getDragonTiger(ticker, limit = 3) {
    const code = tickerToCode(ticker);
    if (!code) return [];

    const url = `https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE&sortTypes=-1&pageSize=${limit}&pageNumber=1&reportName=RPT_DAILYBILLBOARD_DETAILS&columns=ALL&source=WEB&client=WEB&filter=(SECURITY_CODE%3D%22${code}%22)`;

    try {
      const resp = await fetchEM(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const records = data?.result?.data || [];
      const tigers = [];

      for (const r of records) {
        tigers.push({
          date: r.TRADE_DATE?.substring(0, 10) || "",
          reason: r.EXPLANATION || "",
          netBuy: r.BILLBOARD_NET_AMT || 0,        // 龙虎榜净买入额（元）
          buyAmt: r.BILLBOARD_BUY_AMT || 0,        // 买入额
          sellAmt: r.BILLBOARD_SELL_AMT || 0,      // 卖出额
          changePct: r.CHANGE_RATE || 0,           // 当日涨跌幅%
          closePrice: r.CLOSE_PRICE || 0,          // 收盘价
          turnoverRate: r.TURNOVERRATE || 0,       // 换手率%
          // 上榜后N天涨跌幅（用来评估信号准确性）
          d1Change: r.D1_CLOSE_ADJCHRATE || 0,
          d5Change: r.D5_CLOSE_ADJCHRATE || 0,
          d10Change: r.D10_CLOSE_ADJCHRATE || 0,
          d20Change: r.D20_CLOSE_ADJCHRATE || 0,
          d30Change: r.D30_CLOSE_ADJCHRATE || 0,
          buyRatio: r.BUY_RATIO || 0,              // 买入占比
          sellRatio: r.SELL_RATIO || 0,            // 卖出占比
        });
      }

      this.stats.totalFetched += tigers.length;
      return tigers;
    } catch (e) {
      this.stats.errors.push({ source: "dragon_tiger", error: e.message });
      console.warn(`[eastmoney] 龙虎榜获取失败 ${ticker}:`, e.message);
      return [];
    }
  }

  /**
   * 获取多季度历史财务数据（营收/净利趋势分析）
   *
   * 参数：
   *   ticker: 股票代码
   *   limit: 最多返回几期，默认8期（约2年）
   *
   * 返回：
   *   财务数据数组（按时间倒序），每条含完整财务指标
   *
   * 小白讲解：
   *   这个函数能拿到公司过去8个季度的财务数据，比如营收、净利润、毛利率等。
   *   有了多季度数据，就能判断公司是在"加速增长"还是"增速下滑"——这是投资分析的核心。
   */
  async getFinancialHistory(ticker, limit = 8) {
    const code = tickerToCode(ticker);
    if (!code) return [];

    const url = `https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=REPORT_DATE&sortTypes=-1&pageSize=${limit}&pageNumber=1&reportName=RPT_F10_FINANCE_MAINFINADATA&columns=ALL&source=WEB&client=WEB&filter=(SECURITY_CODE%3D%22${code}%22)`;

    try {
      const resp = await fetchEM(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const records = data?.result?.data || [];
      const history = [];

      for (const r of records) {
        history.push({
          reportDate: r.REPORT_DATE?.substring(0, 10) || "",
          reportType: r.REPORT_TYPE || "",          // 年报/季报/半年报
          reportName: r.REPORT_DATE_NAME || "",     // 如"2025年报"、"2025三季报"
          // 核心财务指标
          eps: r.EPSJB || 0,                         // 每股收益
          epsDiluted: r.EPSKCJB || 0,                // 稀释每股收益
          bps: r.BPS || 0,                           // 每股净资产
          revenue: r.TOTALOPERATEREVE || 0,           // 营业收入
          netProfit: r.PARENTNETPROFIT || 0,          // 归母净利润
          netProfitDeduct: r.KCFJCXSYJLR || 0,       // 扣非净利润
          // 同比增速（关键！判断增长趋势）
          revenueYoy: r.TOTALOPERATEREVETZ || 0,      // 营收同比%
          netProfitYoy: r.PARENTNETPROFITTZ || 0,    // 净利润同比%
          netProfitDeductYoy: r.KCFJCXSYJLRTZ || 0,  // 扣非净利同比%
          // 单季度同比环比（更精准的增长判断）
          quarterlyRevenueQoQ: r.DJD_TOI_QOQ || 0,   // 单季营收环比%
          quarterlyNetProfitQoQ: r.DJD_DPNP_QOQ || 0, // 单季净利润环比%
          quarterlyRevenueYoy: r.DJD_TOI_YOY || 0,    // 单季营收同比%
          quarterlyNetProfitYoy: r.DJD_DPNP_YOY || 0, // 单季净利润同比%
          // 盈利能力
          roe: r.ROEJQ || 0,                          // ROE(加权)
          grossMargin: r.XSMLL || 0,                  // 销售毛利率%
          netMargin: r.XSJLL || 0,                    // 销售净利率%
          // 偿债能力
          debtRatio: r.ZCFZL || 0,                    // 资产负债率%
          currentRatio: r.LD || 0,                    // 流动比率
          quickRatio: r.SD || 0,                      // 速动比率
          // 现金流
          ocfPerShare: r.MGJYXJJE || 0,               // 每股经营现金流
        });
      }

      this.stats.totalFetched += history.length;
      return history;
    } catch (e) {
      this.stats.errors.push({ source: "financial_history", error: e.message });
      console.warn(`[eastmoney] 财务历史获取失败 ${ticker}:`, e.message);
      return [];
    }
  }

  /**
   * 获取个股券商研报列表（近6个月）
   *
   * 参数：
   *   ticker: 股票代码
   *   limit: 最多返回几条，默认5条
   *   days: 最近多少天的研报，默认180天（约半年）
   *
   * 返回：
   *   研报数组，每条含 {title, orgName, publishDate, rating, ratingChange, epsForecast, peForecast, researchLink}
   *
   * 小白讲解：
   *   这个函数从东方财富研报中心拿到各家券商发布的个股研报。
   *   研报里有分析师的评级（买入/增持/中性/卖出）、
   *   盈利预测（EPS、PE）、投资逻辑等。
   *   虽然没有完整研报正文，但标题+评级+预测数据已经是很有价值的"卖方共识"信号。
   */
  async getResearchReports(ticker, limit = 5, days = 180) {
    const code = tickerToCode(ticker);
    if (!code) return [];

    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - days * 24 * 60 * 60 * 1000);
    const fmt = (d) => d.toISOString().substring(0, 10);

    const url = `https://reportapi.eastmoney.com/report/list?cb=&industryCode=*&pageSize=${limit}&industry=*&rating=&ratingChange=&beginTime=${fmt(startDate)}&endTime=${fmt(endDate)}&pageNo=1&fields=&qType=0&orgCode=&code=${code}&rcode=&p=1&pageNum=1`;

    try {
      const resp = await fetchEM(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const reports = data?.data || [];
      const result = [];

      for (const r of reports) {
        result.push({
          title: r.title || "",
          orgName: r.orgSName || r.orgName || "",           // 券商名称
          publishDate: r.publishDate?.substring(0, 10) || "",  // 发布日期
          rating: r.emRatingName || r.sRatingName || "",       // 评级（买入/增持/中性/卖出）
          lastRating: r.lastEmRatingName || "",                 // 上次评级
          ratingChange: r.ratingChange || 0,                    // 评级变动（1=上调, 2=下调, 3=维持）
          // 盈利预测
          epsThisYear: r.predictThisYearEps || "",              // 今年EPS预测
          epsNextYear: r.predictNextYearEps || "",              // 明年EPS预测
          peThisYear: r.predictThisYearPe || "",                // 今年PE预测
          peNextYear: r.predictNextYearPe || "",                // 明年PE预测
          // 目标价（可能为空）
          aimPriceTop: r.indvAimPriceT || "",                   // 目标价上限
          aimPriceLow: r.indvAimPriceL || "",                   // 目标价下限
          researcher: r.researcher || r.author?.join(",") || "", // 分析师
          industry: r.indvInduName || "",                        // 所属行业
          reportType: r.reportType || 0,                         // 报告类型
          infoCode: r.infoCode || "",                            // 研报ID
          attachPages: r.attachPages || 0,                       // 报告页数
        });
      }

      this.stats.totalFetched += result.length;
      return result;
    } catch (e) {
      this.stats.errors.push({ source: "research_reports", error: e.message });
      console.warn(`[eastmoney] 研报获取失败 ${ticker}:`, e.message);
      return [];
    }
  }

  /**
   * 一键获取所有增强数据（资金流向+龙虎榜+财务历史+券商研报）
   *
   * 参数：
   *   ticker: 股票代码
   *
   * 返回：
   *   { fundFlow, dragonTiger, financialHistory, researchReports }
   *
   * 小白讲解：
   *   这是一个"全家桶"接口，一次性把资金流向、龙虎榜、财务趋势、券商研报都拿到。
   *   SubAgent调用这个方法就能获得全部增强数据。
   */
  async getAllEnhancedData(ticker) {
    console.log(`[eastmoney] 开始获取 ${ticker} 的增强数据`);

    const [fundFlow, dragonTiger, financialHistory, researchReports] = await Promise.allSettled([
      this.getFundFlow(ticker, 10),
      this.getDragonTiger(ticker, 5),
      this.getFinancialHistory(ticker, 8),
      this.getResearchReports(ticker, 5, 180),
    ]);

    const result = {
      fundFlow: fundFlow.status === "fulfilled" ? fundFlow.value : [],
      dragonTiger: dragonTiger.status === "fulfilled" ? dragonTiger.value : [],
      financialHistory: financialHistory.status === "fulfilled" ? financialHistory.value : [],
      researchReports: researchReports.status === "fulfilled" ? researchReports.value : [],
    };

    console.log(`[eastmoney] ${ticker} 增强数据: 资金流向${result.fundFlow.length}天, 龙虎榜${result.dragonTiger.length}条, 财务历史${result.financialHistory.length}期, 券商研报${result.researchReports.length}篇`);
    return result;
  }

  /**
   * 把增强数据格式化为LLM可读的文本
   *
   * 参数：
   *   data: getAllEnhancedData返回的对象
   *
   * 返回：
   *   格式化的文本字符串（直接注入LLM prompt）
   */
  formatForLLM(data) {
    if (!data) return "无东方财富增强数据";

    let text = "";

    // 1. 资金流向
    if (data.fundFlow && data.fundFlow.length > 0) {
      const n = data.fundFlow.length;
      text += `\n### 💰 主力资金流向（最近${n}天）\n`;
      text += `| 日期 | 主力净流入(万) | 超大单(万) | 大单(万) | 主力占比 | 收盘价 | 涨跌幅 |\n`;
      text += `|---|---|---|---|---|---|---|\n`;
      for (const f of data.fundFlow) {
        const mainWan = (f.mainNet / 10000).toFixed(0);
        const superWan = (f.superLargeNet / 10000).toFixed(0);
        const largeWan = (f.largeNet / 10000).toFixed(0);
        text += `| ${f.date} | ${mainWan} | ${superWan} | ${largeWan} | ${f.mainNetPct}% | ${f.closePrice} | ${f.changePct}% |\n`;
      }

      // 分段统计：近3日、近5日、近10日
      const latest = data.fundFlow[0];
      const sum3 = data.fundFlow.slice(0, Math.min(3, n)).reduce((s, f) => s + f.mainNet, 0);
      const sum5 = data.fundFlow.slice(0, Math.min(5, n)).reduce((s, f) => s + f.mainNet, 0);
      const sum10 = data.fundFlow.reduce((s, f) => s + f.mainNet, 0);
      const avgMainPct = data.fundFlow.reduce((s, f) => s + f.mainNetPct, 0) / n;

      text += `\n**资金流向统计**:\n`;
      if (n >= 3) text += `- 近3日: ${sum3 > 0 ? '净流入' : '净流出'} ${(Math.abs(sum3) / 10000).toFixed(0)}万\n`;
      if (n >= 5) text += `- 近5日: ${sum5 > 0 ? '净流入' : '净流出'} ${(Math.abs(sum5) / 10000).toFixed(0)}万\n`;
      text += `- 近${n}日: ${sum10 > 0 ? '净流入' : '净流出'} ${(Math.abs(sum10) / 10000).toFixed(0)}万，平均主力占比 ${avgMainPct.toFixed(2)}%\n`;

      // 资金-价格背离判断（最近5天）
      if (n >= 5) {
        const recent5 = data.fundFlow.slice(0, 5);
        const price5dChange = ((latest.closePrice - recent5[4].closePrice) / recent5[4].closePrice) * 100;
        const fund5dNet = recent5.reduce((s, f) => s + f.mainNet, 0);
        const priceUp = price5dChange > 0;
        const fundIn = fund5dNet > 0;

        text += `\n**资金-价格背离信号**（近5日）:\n`;
        if (priceUp && fundIn) {
          text += `- 🟢 量价齐升：股价涨${price5dChange.toFixed(1)}% + 主力净流入${(Math.abs(fund5dNet)/10000).toFixed(0)}万 → 健康上涨\n`;
        } else if (!priceUp && !fundIn) {
          text += `- 🔴 量价齐跌：股价跌${Math.abs(price5dChange).toFixed(1)}% + 主力净流出${(Math.abs(fund5dNet)/10000).toFixed(0)}万 → 持续走弱\n`;
        } else if (priceUp && !fundIn) {
          text += `- ⚠️ 价涨量缩（背离）：股价涨${price5dChange.toFixed(1)}% 但主力净流出${(Math.abs(fund5dNet)/10000).toFixed(0)}万 → 可能是散户拉升，机构出货\n`;
        } else {
          text += `- 🟡 价跌量增（背离）：股价跌${Math.abs(price5dChange).toFixed(1)}% 但主力净流入${(Math.abs(fund5dNet)/10000).toFixed(0)}万 → 可能是机构逢低吸筹\n`;
        }
      }
    }

    // 2. 龙虎榜
    if (data.dragonTiger && data.dragonTiger.length > 0) {
      text += `\n### 🐯 龙虎榜记录（机构席位动向）\n`;
      for (const t of data.dragonTiger) {
        const netWan = (t.netBuy / 10000).toFixed(0);
        text += `- ${t.date}: ${t.reason}\n`;
        text += `  净买入${netWan}万（买入${(t.buyAmt/10000).toFixed(0)}万/卖出${(t.sellAmt/10000).toFixed(0)}万），当日涨跌${t.changePct.toFixed(2)}%\n`;
        text += `  上榜后表现: 1日${t.d1Change.toFixed(1)}% / 5日${t.d5Change.toFixed(1)}% / 10日${t.d10Change.toFixed(1)}% / 20日${t.d20Change.toFixed(1)}% / 30日${t.d30Change.toFixed(1)}%\n`;
      }
    }

    // 3. 财务历史趋势
    if (data.financialHistory && data.financialHistory.length > 0) {
      text += `\n### 📊 多季度财务趋势（共${data.financialHistory.length}期）\n`;
      text += `| 报告期 | 营收(亿) | 净利(亿) | 营收同比 | 净利同比 | 毛利率 | 净利率 | ROE | 单季营收同比 | 单季净利同比 |\n`;
      text += `|---|---|---|---|---|---|---|---|---|---|\n`;
      for (const h of data.financialHistory) {
        const revYi = (h.revenue / 100000000).toFixed(2);
        const netYi = (h.netProfit / 100000000).toFixed(2);
        text += `| ${h.reportName} | ${revYi} | ${netYi} | ${h.revenueYoy.toFixed(1)}% | ${h.netProfitYoy.toFixed(1)}% | ${h.grossMargin.toFixed(1)}% | ${h.netMargin.toFixed(1)}% | ${h.roe.toFixed(2)}% | ${h.quarterlyRevenueYoy.toFixed(1)}% | ${h.quarterlyNetProfitYoy.toFixed(1)}% |\n`;
      }
      // 分析增长趋势
      if (data.financialHistory.length >= 2) {
        const latest = data.financialHistory[0];
        const prev = data.financialHistory[1];
        const revenueAccel = latest.revenueYoy - prev.revenueYoy;
        const profitAccel = latest.netProfitYoy - prev.netProfitYoy;
        text += `\n**增长趋势分析**:\n`;
        text += `- 营收增速${revenueAccel > 0 ? '加速' : '减速'} ${Math.abs(revenueAccel).toFixed(1)}个百分点\n`;
        text += `- 净利增速${profitAccel > 0 ? '加速' : '减速'} ${Math.abs(profitAccel).toFixed(1)}个百分点\n`;
        if (revenueAccel > 10 || profitAccel > 10) {
          text += `- ⚡ 增长显著加速，关注业绩拐点信号\n`;
        } else if (revenueAccel < -10 || profitAccel < -10) {
          text += `- ⚠️ 增长显著放缓，关注业绩风险\n`;
        }
      }
    }

    // 4. 券商研报摘要
    if (data.researchReports && data.researchReports.length > 0) {
      text += `\n### 📑 券商研报摘要（近6个月，${data.researchReports.length}篇）\n`;
      text += `| 日期 | 券商 | 评级 | 上次评级 | 今年EPS | 明年EPS | 今年PE | 明年PE | 标题 |\n`;
      text += `|---|---|---|---|---|---|---|---|---|\n`;
      for (const r of data.researchReports) {
        const ratingChangeTxt = r.ratingChange === 1 ? '上调' : r.ratingChange === 2 ? '下调' : '维持';
        const ratingDisplay = r.rating || '—';
        text += `| ${r.publishDate} | ${r.orgName} | ${ratingDisplay}${r.ratingChange !== 3 ? `(${ratingChangeTxt})` : ''} | ${r.lastRating || '—'} | ${r.epsThisYear || '—'} | ${r.epsNextYear || '—'} | ${r.peThisYear || '—'} | ${r.peNextYear || '—'} | ${(r.title || '').substring(0, 25)}... |\n`;
      }

      // 研报共识统计
      const ratingCounts = {};
      let totalWithRating = 0;
      for (const r of data.researchReports) {
        if (r.rating) {
          ratingCounts[r.rating] = (ratingCounts[r.rating] || 0) + 1;
          totalWithRating++;
        }
      }
      if (totalWithRating > 0) {
        text += `\n**卖方评级分布**（${totalWithRating}家）:\n`;
        for (const [rating, count] of Object.entries(ratingCounts)) {
          const pct = ((count / totalWithRating) * 100).toFixed(0);
          text += `- ${rating}: ${count}家（${pct}%）\n`;
        }
        // 盈利预测均值
        const epsNextYearList = data.researchReports.filter(r => r.epsNextYear).map(r => parseFloat(r.epsNextYear));
        const peNextYearList = data.researchReports.filter(r => r.peNextYear).map(r => parseFloat(r.peNextYear));
        if (epsNextYearList.length > 0) {
          const avgEps = epsNextYearList.reduce((a, b) => a + b, 0) / epsNextYearList.length;
          text += `- 一致预期明年EPS: ${avgEps.toFixed(2)}元（${epsNextYearList.length}家）\n`;
        }
        if (peNextYearList.length > 0) {
          const avgPe = peNextYearList.reduce((a, b) => a + b, 0) / peNextYearList.length;
          text += `- 一致预期明年PE: ${avgPe.toFixed(1)}倍（${peNextYearList.length}家）\n`;
        }
      }
    }

    return text || "无东方财富增强数据";
  }
}
