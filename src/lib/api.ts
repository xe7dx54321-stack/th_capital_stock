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

export function fetchNews(): Promise<NewsList> {
  return apiGet<NewsList>("/api/news");
}

export function fetchNewsDetail(id: number): Promise<NewsDetail> {
  return apiGet<NewsDetail>(`/api/news/${id}`);
}

export function fetchStockDetail(code: string): Promise<StockDetail> {
  return apiGet<StockDetail>(`/api/stock/${encodeURIComponent(code)}`);
}

// ---------- Local research workflow API ----------

export interface WorkflowDefinition {
  workflow_id: string;
  title: string;
  description: string;
  enabled: boolean;
  input_schema: Record<string, unknown>;
}

export interface WorkflowArtifact {
  artifact_id: string;
  run_id: string;
  artifact_type: string;
  title: string;
  relative_path: string;
  mime_type: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface WorkflowRun {
  run_id: string;
  workflow_id: string;
  status: string;
  input: Record<string, unknown>;
  summary?: Record<string, unknown>;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  cancel_requested_at?: string | null;
  process_id?: number | null;
  process_status?: string | null;
  artifacts?: WorkflowArtifact[];
}

export interface WorkflowEvent {
  event_id?: number;
  run_id: string;
  sequence: number;
  event_type: string;
  stage_id?: string | null;
  level?: string;
  message?: string;
  payload: Record<string, unknown>;
  created_at: string;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error((body as { error?: string }).error || `API ${path} failed: ${response.status}`);
  }
  return body as T;
}

export function fetchWorkflows(): Promise<{ workflows: WorkflowDefinition[] }> {
  return apiRequest("/api/workflows");
}

export function fetchWorkflowRuns(limit = 50): Promise<{ runs: WorkflowRun[] }> {
  return apiRequest(`/api/workflow-runs?limit=${limit}`);
}

export function fetchWorkflowRun(runId: string): Promise<WorkflowRun> {
  return apiRequest(`/api/workflow-runs/${encodeURIComponent(runId)}`);
}

export function createWorkflowRun(
  workflowId: string,
  input: Record<string, unknown>,
  idempotencyKey?: string,
): Promise<WorkflowRun> {
  return apiRequest("/api/workflow-runs", {
    method: "POST",
    headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined,
    body: JSON.stringify({ workflow_id: workflowId, input }),
  });
}

export function fetchWorkflowEvents(runId: string, after = 0): Promise<{ events: WorkflowEvent[] }> {
  return apiRequest(`/api/workflow-runs/${encodeURIComponent(runId)}/events?after=${after}`);
}

export function cancelWorkflowRun(runId: string): Promise<{ requested: boolean; run: WorkflowRun }> {
  return apiRequest(`/api/workflow-runs/${encodeURIComponent(runId)}/cancel`, { method: "POST" });
}

export function artifactUrl(artifactId: string): string {
  return `/api/artifacts/${encodeURIComponent(artifactId)}`;
}

const workflowEventTypes = [
  "run.queued", "run.started", "stage.started", "stage.progress", "stage.completed",
  "stage.warning", "artifact.created", "review.requested", "run.completed", "run.failed",
  "run.cancelled",
];

export function subscribeWorkflowEvents(
  runId: string,
  after: number,
  onEvent: (event: WorkflowEvent) => void,
  onError: () => void,
): () => void {
  const source = new EventSource(
    `/api/workflow-runs/${encodeURIComponent(runId)}/stream?after=${after}`,
  );
  const handle = (raw: MessageEvent<string>) => {
    try { onEvent(JSON.parse(raw.data) as WorkflowEvent); } catch { /* heartbeat or malformed event */ }
  };
  workflowEventTypes.forEach((name) => source.addEventListener(name, handle as EventListener));
  source.onmessage = handle;
  source.onerror = onError;
  return () => source.close();
}

export interface MemoryEvidenceLink {
  evidence_id: string;
  relation: "supports" | "contradicts" | "supersedes" | "context";
  created_at: string;
}

export interface MemoryFieldDiff { field: string; before: unknown; after: unknown; }

export interface MemoryReviewLog {
  review_id: string;
  action: string;
  previous_status: string;
  new_status: string;
  reviewer: string;
  reason: string;
  reviewed_at: string;
}

export interface MemoryDetail {
  memory_id: string;
  entity_type: string;
  entity_id: string;
  memory_type: string;
  content: Record<string, unknown>;
  status: "candidate" | "approved" | "rejected" | "archived";
  confidence?: number | null;
  source_run_id?: string | null;
  parent_memory_id?: string | null;
  version: number;
  field_diff: MemoryFieldDiff[];
  evidence_links: MemoryEvidenceLink[];
  review_log: MemoryReviewLog[];
  reviewed_by?: string | null;
  review_reason?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export function fetchMemory(memoryId: string): Promise<MemoryDetail> {
  return apiRequest(`/api/memories/${encodeURIComponent(memoryId)}`);
}

export function reviewMemory(
  memoryId: string,
  action: "approve" | "reject" | "archive",
  reviewer: string,
  reason: string,
): Promise<{ memory: MemoryDetail }> {
  return apiRequest(`/api/memories/${encodeURIComponent(memoryId)}/review`, {
    method: "POST",
    body: JSON.stringify({ action, reviewer, reason }),
  });
}

// ---------- Personal decision feedback API ----------

export interface DecisionOutcome {
  outcome_id: string;
  outcome_status: string;
  summary: string;
  evidence_ids: string[];
  observed_price?: number | null;
  recorded_by: string;
  recorded_at: string;
  metadata?: Record<string, unknown>;
}

export interface DecisionDetail {
  decision_id: string;
  recommendation_id: string;
  ticker: string;
  market?: string | null;
  theme?: string | null;
  action: string;
  status: string;
  decision_time: string;
  reference_price?: number | null;
  thesis_summary: string;
  bear_case_summary: string;
  evidence_ids: string[];
  kill_conditions: string[];
  risk_notes?: string | null;
  outcome_status: string;
  outcome_summary?: string | null;
  outcome_recorded_at?: string | null;
  outcome_evidence_ids: string[];
  source_run_id?: string | null;
  source_memory_id?: string | null;
  review_due_at?: string | null;
  review_state: "upcoming" | "overdue" | "reviewed";
  outcome_history: DecisionOutcome[];
}

export interface CreateDecisionInput {
  ticker: string;
  action: string;
  thesis: string;
  counterargument: string;
  evidence_ids: string[];
  invalidation_conditions: string[];
  reference_price?: number | null;
  review_due_at: string;
  source_run_id?: string | null;
  source_memory_id?: string | null;
  recorded_by?: string;
  time_horizon?: string;
}

export function fetchDecisions(ticker?: string): Promise<{ decisions: DecisionDetail[] }> {
  const query = ticker ? `?ticker=${encodeURIComponent(ticker)}` : "";
  return apiRequest(`/api/decisions${query}`);
}

export function createDecision(input: CreateDecisionInput): Promise<{ decision: DecisionDetail }> {
  return apiRequest("/api/decisions", { method: "POST", body: JSON.stringify(input) });
}

export function recordDecisionOutcome(
  decisionId: string,
  input: {
    outcome_status: string;
    summary: string;
    evidence_ids: string[];
    observed_price?: number | null;
    recorded_by: string;
  },
): Promise<{ decision: DecisionDetail }> {
  return apiRequest(`/api/decisions/${encodeURIComponent(decisionId)}/outcome`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
