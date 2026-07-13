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

export function getCatalystsReport(newsClaimsData) {
  const news = (newsClaimsData?.news || []).slice(0, 10);
  const claims = newsClaimsData?.claims || [];
  const risks = newsClaimsData?.risks || [];

  // 利好 / 利空关键词（启发式匹配，中英文兼顾）
  const bullKeywords = ["增长", "上涨", "创新高", "买入", "增持", "超预期", "超预期增长",
    "获批", "中标", "签", "回购", "分红", "业绩预增", "预增", "利好",
    "涨价", "量价齐升", "订单", "突破", "入选", "上市",
    "buy", "hold", "outperform", "positive", "upgrade", "beat"];
  const bearKeywords = ["下跌", "亏损", "利空", "减持", "卖出", "下修", "调查",
    "诉讼", "违约", "风险", "暴雷", "下滑", "亏损", "承压", "拖累",
    "sell", "downgrade", "miss", "negative", "warning"];

  // --- 1) 分析每条新闻的方向 + 强度 ---
  const scoredNews = news.map((n) => {
    const txt = `${n.title || ""} ${n.summary || ""}`.toLowerCase();
    let bull = 0, bear = 0;
    for (const k of bullKeywords) if (txt.includes(k.toLowerCase())) bull++;
    for (const k of bearKeywords) if (txt.includes(k.toLowerCase())) bear++;
    // 方向：+1 利好，-1 利空，0 中性
    let direction = 0;
    if (bull > bear) direction = 1;
    else if (bear > bull) direction = -1;
    // 强度 = 关键词命中数量
    return { ...n, direction, intensity: bull + bear };
  });

  // --- 2) 分析研究主张（research claims） ---
  // 用 `stance` 字段作方向，`confidence` 作强度
  const scoredClaims = claims.map((c) => {
    const s = (c.stance || "").toLowerCase();
    let direction = 0;
    if (/买|多|加|bull|buy|outperform|strong|overweight/i.test(s)) direction = 1;
    else if (/卖|空|减|sell|bear|underweight|down|negative/i.test(s)) direction = -1;
    const intensity = (c.confidence != null ? Number(c.confidence) : 0.5) * 2;
    return { ...c, direction, intensity };
  });

  // --- 3) 综合催化评分：新闻占 60%，研究主张占 40% ---
  let newsScore = 0, newsTotal = 0;
  for (const n of scoredNews) {
    if (n.direction !== 0) {
      const w = Math.min(10, n.intensity);
      newsScore += n.direction * (10 + w * 10); // 每条 -100 ~ +100 之间加权
      newsTotal++;
    }
  }
  const newsAvg = newsTotal > 0 ? newsScore / newsTotal : 0;

  let claimScore = 0, claimTotal = 0;
  for (const c of scoredClaims) {
    if (c.direction !== 0) {
      claimScore += c.direction * (30 + c.intensity * 40); // 研究主张权重更大
      claimTotal++;
    }
  }
  const claimAvg = claimTotal > 0 ? claimScore / claimTotal : 0;

  // 风险提示对催化评分的负面影响
  let riskPenalty = 0;
  const highRisks = risks.filter((r) => (r.severity || "").toString().toLowerCase().includes("高") || (r.severity || "") === "HIGH");
  riskPenalty = Math.min(30, highRisks.length * 10);

  // 综合（-100 ~ +100）
  let catalystScore = null;
  let netDirection = "neutral";
  let summary = "暂无近期新闻或研究主张，无法评估催化方向。";
  if (newsTotal > 0 || claimTotal > 0) {
    // 按新闻 60%，研究主张 40% 加权（若无其中一项则 100% 给另一项）
    if (newsTotal > 0 && claimTotal > 0) catalystScore = Math.round(newsAvg * 0.6 + claimAvg * 0.4 - riskPenalty);
    else if (newsTotal > 0) catalystScore = Math.round(newsAvg - riskPenalty);
    else catalystScore = Math.round(claimAvg - riskPenalty);
    catalystScore = Math.max(-100, Math.min(100, catalystScore));

    if (catalystScore >= 30) netDirection = "bullish";
    else if (catalystScore <= -30) netDirection = "bearish";

    if (catalystScore >= 40) summary = `催化评分 ${catalystScore}，市场情绪显著偏多，需关注利好兑现时点。`;
    else if (catalystScore >= 10) summary = `催化评分 ${catalystScore}，市场情绪偏积极。`;
    else if (catalystScore >= -10) summary = `催化评分 ${catalystScore}，市场情绪中性，缺乏明确催化。`;
    else if (catalystScore >= -40) summary = `催化评分 ${catalystScore}，市场情绪偏谨慎，需关注利空消化。`;
    else summary = `催化评分 ${catalystScore}，市场情绪显著偏空，需高度谨慎。`;
  }

  // --- 4) 返回：取前 5 条新闻、前 10 条研究主张用于前端标签页展示 ---
  //    同时补充每条新闻的方向标签（bullish / bearish / neutral）
  const recentNews = scoredNews.slice(0, 5).map((n) => ({
    id: n.id, title: n.title, source: n.source, sourceName: n.sourceName,
    publishedAt: n.publishedAt, tickers: n.tickers, url: n.url,
    credibility: n.credibility, summary: n.summary, hasFullBody: n.hasFullBody,
    direction: n.direction > 0 ? "bullish" : (n.direction < 0 ? "bearish" : "neutral"),
    intensity: n.intensity,
  }));
  const upcomingClaims = scoredClaims.slice(0, 10).map((c) => ({
    claimId: c.claimId, claimType: c.claimType, theme: c.theme,
    claimText: c.claimText, stance: c.stance, importance: c.importance,
    confidence: c.confidence, createdAt: c.createdAt,
    direction: c.direction > 0 ? "bullish" : (c.direction < 0 ? "bearish" : "neutral"),
    intensity: c.intensity,
  }));

  return {
    recentNews,
    upcomingClaims,
    catalystScore,
    netDirection,
    summary,
  };
}
