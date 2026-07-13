function parseStringArray(value) {
  try {
    const parsed = JSON.parse(value || "[]");
    return Array.isArray(parsed) ? parsed.filter((item) => item && typeof item === "string") : [];
  } catch {
    return [];
  }
}

export function buildDashboard(snapshot, now = new Date()) {
  return {
    summary: {
      poolTotal: snapshot.poolTotal,
      ahCoverage: snapshot.ahCoverage,
      usCoverage: snapshot.usCoverage,
      withFundamentals: snapshot.withFundamentals,
      newsCount: snapshot.newsCount,
      riskAlerts: snapshot.riskAlerts,
    },
    poolByType: snapshot.poolByType.length > 0 ? snapshot.poolByType : [],
    dataFreshness: [
      { source: "eastmoney_news_search", status: "active" },
      { source: "yahoo_finance_rss", status: "active" },
      { source: "akshare_fundamentals", status: "active" },
    ],
    updatedAt: now.toISOString(),
  };
}

export function buildNewsList(rows, now = new Date()) {
  const items = rows.map((row) => {
    const body = row.body || "";
    return {
      id: row.id,
      title: row.title,
      source: row.source_key,
      sourceName: row.source_name || row.source_key,
      publishedAt: row.published_at,
      tickers: parseStringArray(row.tickers_json).slice(0, 5),
      url: row.url,
      credibility: row.credibility || "",
      summary: body.length > 180 ? `${body.substring(0, 180)}…` : body,
      hasFullBody: body.length > 0,
    };
  });
  const sources = Array.from(new Set(rows.map((row) => row.source_key))).sort();
  return { items, sources, updatedAt: now.toISOString() };
}

export function buildNewsDetail(row, now = new Date()) {
  const tickers = parseStringArray(row.tickers_json);
  const themes = parseStringArray(row.themes_json);
  const searchable = `${row.body || ""} ${row.title || ""}`;
  const insights = [];

  if (/\b(?:增持|买入|看好|优于|推荐|outperform|buy|strong buy)\b/i.test(searchable)) {
    insights.push({ type: "bull", text: "文中出现买入/增持/看好等正面评级，属于利好信号。" });
  }
  if (/\b(?:减持|卖出|中性|回避|underperform|sell|hold)\b/i.test(searchable)) {
    insights.push({ type: "bear", text: "文中出现减持/卖出/中性等负面或中性评级，注意风险。" });
  }
  if (/\b(?:业绩|营收|净利润|盈利|亏损|同比|增长|下降)\b/.test(searchable)) {
    insights.push({ type: "fundamentals", text: "内容涉及业绩/营收/盈利情况，属于基本面驱动事件。" });
  }
  if (/\b(?:AI|人工智能|大模型|算力|GPU|芯片|半导体|具身|机器人)\b/i.test(searchable)) {
    insights.push({ type: "theme", text: "内容涉及 AI/算力/半导体/机器人等科技主题方向。" });
  }
  if (/\b(?:量子|量子计算|量子通信)\b/.test(searchable)) {
    insights.push({ type: "theme", text: "内容涉及量子科技主题方向。" });
  }
  if (/\b(?:订单|中标|合同|客户|订单量)\b/.test(searchable)) {
    insights.push({ type: "order", text: "内容涉及订单/中标/合同等商业落地信号。" });
  }
  if (/\b(?:监管|处罚|警告|风险|合规|诉讼|调查|调查)\b/.test(searchable)) {
    insights.push({ type: "risk", text: "内容涉及监管/处罚/合规风险等负面信号，需高度注意。" });
  }
  if (insights.length === 0) {
    insights.push({ type: "neutral", text: "该新闻暂未识别出明确的利好/利空信号，建议结合其他信息判断。" });
  }

  const credibilityMap = {
    high: "高（来源为券商研报/权威媒体）",
    medium: "中（常规资讯）",
    low: "低（非权威来源）",
  };

  return {
    id: row.id,
    title: row.title,
    body: row.body || "",
    source: row.source_key,
    sourceName: row.source_name || row.source_key,
    publishedAt: row.published_at,
    tickers,
    themes,
    url: row.url,
    credibility: row.credibility || "",
    credibilityText: credibilityMap[row.credibility] || "未标注",
    insights,
    updatedAt: now.toISOString(),
  };
}
