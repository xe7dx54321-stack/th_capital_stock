/**
 * API 工具
 *
 * 封装对后端 Express 服务器的 API 调用
 *
 * 小白讲解：这个文件就像一本"通讯录"，
 * 记录了去哪里找数据。
 * 其他组件想查数据时就调用这里的函数，
 * 不用每次都写一遍 fetch 代码。
 */

// ---------- 类型定义 ----------

export interface DashboardData {
  summary: {
    poolTotal: number;
    ahCoverage: number;
    usCoverage: number;
    withFundamentals: number;
    newsCount: number;
    riskAlerts: number;
  };
  poolByType: { type: string; count: number }[];
  dataFreshness: { source: string; status: string }[];
  updatedAt: string;
}

export interface ValueScoreItem {
  tsCode: string;
  name: string;
  market: string;
  compositeScore: number | null;
  fundamentalQuality: number | null;
  valuationPosition: number | null;
  technicalMomentum: number | null;
  themeRelevance: number | null;
  industryPosition: number | null;
  sector: string | null;
  latestClose: number | null;
  // --- 新增：综合建议 verdict（与个股详情页的 overallRecommendation.verdict 一致）
  verdict?: string | null;
}

export interface ValueScoreList {
  scores: ValueScoreItem[];
  updatedAt: string;
}

export interface DiscoveryItem {
  ticker: string;
  name: string;
  market: string;
  discoverySource: string;
  triggerReason: string;
  newsMentions: number;
  priority: string;
  status: string;
  latestNewsTitle: string;
  latestNewsAt: string;
  score: number | null;
  sector: string;
  isInFocus: boolean;
}

export interface DiscoveryList {
  discoveries: DiscoveryItem[];
  updatedAt: string;
}

export interface PhaseInfo {
  phaseId: string;
  phaseName: string;
  description: string;
  status: string;
  taskCount: number;
  completedCount: number;
}

export interface PhaseList {
  phases: PhaseInfo[];
  updatedAt: string;
}

export interface NewsItem {
  id: number;
  title: string;
  source: string;
  sourceName?: string;
  publishedAt: string;
  tickers: string[];
  url: string | null;
  credibility?: string;
  summary?: string;
  hasFullBody?: boolean;
}

export interface NewsList {
  items: NewsItem[];
  sources: string[];
  updatedAt: string;
}

// 单条新闻详情（带正文与解读）
export interface NewsDetail {
  id: number;
  title: string;
  body: string;
  source: string;
  sourceName: string;
  publishedAt: string;
  tickers: string[];
  themes: string[];
  url: string | null;
  credibility: string;
  credibilityText: string;
  insights: { type: string; text: string }[];
  updatedAt: string;
}

// 标的详情
export interface PricePoint {
  date: string;
  close: number;
  open: number;
  high: number;
  low: number;
  vol: number;
}

export interface ReportItem {
  label: string;
  metric: string;
  value: string;
  text: string;
}

export interface RiskAlertItem {
  alertId: string;
  alertTime: string;
  alertType: string;
  severity: string;
  message: string;
  action: string;
}

export interface ClaimItem {
  claimId: string;
  claimType: string;
  importance: string;
  stance: string;
  confidence: number;
  claimText: string;
  theme: string;
  createdAt: string;
}

export interface StockReport {
  overallRecommendation: {
    verdict: string;
    text: string;
    score: number;
    bullSignals: number;
    bearSignals: number;
    // --- 增强：综合投资决策字段（Task 6 引擎填充） ---
    entryPrice: number | null;       // 建议买入价
    targetPrice: number | null;       // 目标价
    stopLoss: number | null;          // 止损价
    suggestedPositionSize: number | null; // 建议仓位 (0~1)
    confidence: number | null;        // 推荐置信度 (0-1)
    timeHorizon: string;              // 推荐持有期
    reasoning: string;                // 综合判断理由
  };
  valuation: {
    score: number | null;
    pe: number | null;
    pb: number | null;
    ps: number | null;
    evEbitda: number | null;
    marginOfSafety: number | null;
    summary: string;
    items: ReportItem[];
  };
  fundamentals: {
    summary: string;
    items: ReportItem[];
    sourceQuality: string | null;
    freshness: string | null;
  };
  technical: {
    summary: string;
    items: ReportItem[];
  };
  riskAlerts: RiskAlertItem[];
  claims: ClaimItem[];

  // --- 新增：护城河评估（Task 3 引擎填充） ---
  moat: {
    totalScore: number | null;    // 0-100
    dimensions: {
      name: string;
      score: number | null;       // 0-10
      weight: number;
      evidence: string[];
    }[];
    summary: string;
    evidenceChain: string[];
  };

  // --- 新增：同业对标（Task 4 引擎填充） ---
  peerComparison: {
    sector: string;
    peerCount: number;
    metrics: {
      name: string;
      value: number | null;
      peerAvg: number | null;
      percentile: number | null;
      rank: number | null;
      total: number | null;
      interpretation: string;
    }[];
    industryPosition: string;
    avg: Record<string, number | null>;
  };

  // --- 新增：催化因素（Task 5 引擎填充） ---
  catalysts: {
    recentNews: NewsItem[];
    upcomingClaims: ClaimItem[];
    catalystScore: number | null; // -100 ~ +100
    netDirection: string;          // bullish / bearish / neutral
    summary: string;
  };
}

export interface StockDetail {
  tsCode: string;
  name: string;
  market: string;
  sector: string;
  poolType: string;
  addedDate: string;
  latestPrice: number | null;
  priceHistory: PricePoint[];
  factors: Record<string, number>;
  news: NewsItem[];
  report: StockReport;
  updatedAt: string;
}

// ---------- API 函数 ----------

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export function fetchDashboard(): Promise<DashboardData> {
  return apiGet<DashboardData>("/api/dashboard");
}

export function fetchValueScores(): Promise<ValueScoreList> {
  return apiGet<ValueScoreList>("/api/value-scores");
}

export function fetchDiscoveries(): Promise<DiscoveryList> {
  return apiGet<DiscoveryList>("/api/discoveries");
}

export function fetchPhases(): Promise<PhaseList> {
  return apiGet<PhaseList>("/api/phases");
}

export function fetchNews(): Promise<NewsList> {
  return apiGet<NewsList>("/api/news");
}

export function fetchNewsDetail(id: number): Promise<NewsDetail> {
  return apiGet<NewsDetail>(`/api/news/${id}`);
}

export function fetchStockDetail(code: string): Promise<StockDetail> {
  return apiGet<StockDetail>(`/api/stock/${encodeURIComponent(code)}`);
}
