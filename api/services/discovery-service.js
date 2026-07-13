import { getStockName } from "../registries/stock-registry.js";


const SECTOR_NAMES = {
  semiconductor_compute: "半导体算力",
  semiconductor_photonics: "半导体光子",
  embodied_ai: "具身智能",
  ai_agent: "AI 智能体",
  quantum: "量子科技",
};

const KNOWN_SECTORS = {
  NVDA: "semiconductor_compute", AMD: "semiconductor_compute", AVGO: "semiconductor_compute",
  INTC: "semiconductor_compute", MU: "semiconductor_compute", SNPS: "semiconductor_compute",
  CDNS: "semiconductor_compute", "603986.SH": "semiconductor_compute",
  "688008.SH": "semiconductor_compute", "688041.SH": "semiconductor_compute",
  "688256.SH": "semiconductor_compute", "688521.SH": "semiconductor_compute",
  "688525.SH": "semiconductor_compute", "688800.SH": "semiconductor_compute",
  "300593.SZ": "semiconductor_compute", "301269.SZ": "semiconductor_compute",
  "00981.HK": "semiconductor_compute", "01347.HK": "semiconductor_compute",
  LITE: "semiconductor_photonics", COHR: "semiconductor_photonics",
  MRVL: "semiconductor_photonics", VRT: "semiconductor_photonics",
  "000063.SZ": "semiconductor_photonics", "002281.SZ": "semiconductor_photonics",
  "002796.SZ": "semiconductor_photonics", "002837.SZ": "semiconductor_photonics",
  "300308.SZ": "semiconductor_photonics", "300394.SZ": "semiconductor_photonics",
  "300502.SZ": "semiconductor_photonics", "300620.SZ": "semiconductor_photonics",
  "688205.SH": "semiconductor_photonics",
  TSLA: "embodied_ai", "002050.SZ": "embodied_ai", "002600.SZ": "embodied_ai",
  "002957.SZ": "embodied_ai", "300124.SZ": "embodied_ai", "301368.SZ": "embodied_ai",
  "600580.SH": "embodied_ai", "601689.SH": "embodied_ai", "603728.SH": "embodied_ai",
  "688017.SH": "embodied_ai", "688322.SH": "embodied_ai", "09980.HK": "embodied_ai",
  "872808.BJ": "embodied_ai",
  MSFT: "ai_agent", CRM: "ai_agent", NOW: "ai_agent", "002230.SZ": "ai_agent",
  "301171.SZ": "ai_agent", "688111.SH": "ai_agent", "603039.SH": "ai_agent",
  "00020.HK": "ai_agent", "09988.HK": "ai_agent",
  IONQ: "quantum", QBTS: "quantum", RGTI: "quantum", "688027.SH": "quantum",
};

function marketOf(ticker) {
  if (ticker.endsWith(".SH") || ticker.endsWith(".SZ")) return "A";
  if (ticker.endsWith(".HK")) return "H";
  if (/^[A-Z]/.test(ticker)) return "US";
  return "其他";
}

function sectorFields(ticker, codeToSector) {
  const sector = codeToSector.get(ticker) || KNOWN_SECTORS[ticker] || null;
  return {
    sector: sector ? (SECTOR_NAMES[sector] || sector) : "待评估",
    isInFocus: sector ? Object.hasOwn(SECTOR_NAMES, sector) : false,
  };
}

export function buildDiscoveries(inputs, now = new Date()) {
  const coveredCodes = new Set(inputs.poolRows.map((row) => row.ts_code));
  const codeToSector = new Map(inputs.poolRows.map((row) => [row.ts_code, row.sector]));
  const tickerCounter = new Map();
  const tickerNews = new Map();

  for (const row of inputs.newsRows) {
    try {
      const tickers = JSON.parse(row.tickers_json);
      for (const ticker of tickers) {
        if (!ticker || coveredCodes.has(ticker)) continue;
        tickerCounter.set(ticker, (tickerCounter.get(ticker) || 0) + 1);
        if (!tickerNews.has(ticker)) {
          tickerNews.set(ticker, { title: row.title, at: row.published_at });
        }
      }
    } catch {
      // Invalid legacy ticker metadata is ignored, matching the previous endpoint.
    }
  }

  const priceSpikes = new Map();
  for (const row of inputs.ahSpikes) {
    if (!coveredCodes.has(row.ts_code)) {
      priceSpikes.set(row.ts_code, { pct_chg: row.pct_chg, trade_date: row.trade_date });
    }
  }
  for (const row of inputs.usSpikes) {
    if (!coveredCodes.has(row.symbol)) {
      priceSpikes.set(row.symbol, { pct_chg: row.pct_chg, trade_date: row.trade_date });
    }
  }

  const discoveries = [];
  const sortedSpikes = Array.from(priceSpikes.entries()).sort((a, b) => b[1].pct_chg - a[1].pct_chg);
  for (const [ticker, spike] of sortedSpikes.slice(0, 10)) {
    discoveries.push({
      ticker,
      name: getStockName(ticker) || ticker,
      market: marketOf(ticker),
      discoverySource: "price_spike",
      triggerReason: `价格异动：日内涨幅 +${spike.pct_chg.toFixed(1)}%`,
      pctChange: spike.pct_chg,
      tradeDate: spike.trade_date,
      priority: spike.pct_chg >= 8 ? "high" : "medium",
      status: "new",
      latestNewsTitle: "",
      latestNewsAt: spike.trade_date || "",
      score: null,
      ...sectorFields(ticker, codeToSector),
    });
  }

  const sortedMentions = Array.from(tickerCounter.entries()).sort((a, b) => b[1] - a[1]);
  for (const [ticker, mentions] of sortedMentions.slice(0, 15)) {
    const news = tickerNews.get(ticker);
    discoveries.push({
      ticker,
      name: getStockName(ticker) || ticker,
      market: marketOf(ticker),
      discoverySource: "news_event",
      triggerReason: `${mentions} 次新闻提及`,
      newsMentions: mentions,
      priority: mentions >= 20 ? "high" : mentions >= 8 ? "medium" : "low",
      status: "new",
      latestNewsTitle: news?.title || "",
      latestNewsAt: news?.at || "",
      score: null,
      ...sectorFields(ticker, codeToSector),
    });
  }

  return {
    discoveries,
    priceSpikeCount: priceSpikes.size,
    newsCandidateCount: tickerCounter.size,
    updatedAt: now.toISOString(),
  };
}
