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

  // --- 新增：VFM 价值评分卡（5 维度）---
  vfmScoreCard: {
    fundamentalQuality: number | null;
    valuationPosition: number | null;
    technicalMomentum: number | null;
    themeRelevance: number | null;
    industryPosition: number | null;
    compositeScore: number | null;
    redFlags: string[];
    dataAvailableLevel: string;
    momentum5d: number | null;
    momentum20d: number | null;
    pePercentile: number | null;
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

// ---------- A股-美股映射分析 API ----------

export interface SectorMapping {
  sectorKey: string;
  sectorName: string;
  mappingType: string;
  mappingTypeName: string;
  aShareSectors: string[];
  coreTargets: string[];
  usBenchmarks: string[];
  impactLevel: string;
  correlation: number;
  description: string;
  mappingDescription: string;
}

export interface UsBenchmarkRating {
  symbol: string;
  source: string;
  totalAnalysts: number;
  buy: number;
  hold: number;
  sell: number;
  buyRatio: number;
  sellRatio: number;
  targetMeanPrice?: number;
  currentPrice?: number;
  upside?: number;
  signal: string;
  news?: Array<{ date: string; headline: string; source: string }>;
}

export interface AShareImpact {
  ticker: string;
  impactDirection: string;
  impactLevel: string;
  reasoning: string;
  correlation: number;
}

export interface SectorImpactAnalysis {
  sectorKey: string;
  sectorName: string;
  mappingType: string;
  mappingDescription: string;
  impactLevel: string;
  correlation: number;
  usBenchmarks: UsBenchmarkRating[];
  aShareImpact: AShareImpact[];
  overallSignal: string;
  overallConfidence: number;
}

export interface MappingMatrixResponse {
  success: boolean;
  data: SectorMapping[];
  sectorCount: number;
}

export interface ImpactAnalysisResponse {
  success: boolean;
  data: SectorImpactAnalysis[];
  sectorCount: number;
}

export interface TargetImpactResponse {
  success: boolean;
  ticker?: string;
  sector?: SectorMapping;
  overallSignal?: string;
  overallConfidence?: number;
  targetImpact?: AShareImpact;
  usBenchmarks?: UsBenchmarkRating[];
  report?: string;
  message?: string;
}

export interface MappingReportResponse {
  success: boolean;
  report: string;
  sectorCount: number;
}

export function fetchMappingMatrix(): Promise<MappingMatrixResponse> {
  return apiRequest("/api/mapping/matrix");
}

export function fetchMappingSectors(): Promise<{ success: boolean; data: SectorMapping[] }> {
  return apiRequest("/api/mapping/sectors");
}

export function fetchMappingImpact(sectorKey?: string): Promise<ImpactAnalysisResponse> {
  const query = sectorKey ? `?sectorKey=${encodeURIComponent(sectorKey)}` : "";
  return apiRequest(`/api/mapping/impact${query}`);
}

export function fetchTargetImpact(ticker: string): Promise<TargetImpactResponse> {
  return apiRequest(`/api/mapping/target/${encodeURIComponent(ticker)}`);
}

export function fetchMappingReport(sectorKey?: string): Promise<MappingReportResponse> {
  const query = sectorKey ? `?sectorKey=${encodeURIComponent(sectorKey)}` : "";
  return apiRequest(`/api/mapping/report${query}`);
}

// ---------- 聊天历史 API ----------

/**
 * 单条对话历史记录（后端返回格式）
 *
 * 每条记录包含用户的提问和 AI 的回复，
 * 用来在刷新页面后恢复之前的对话内容。
 */
export interface ChatHistoryItem {
  id: number;
  message: string;       // 用户发送的消息
  response: string;      // AI 的回复内容
  intent: string | null;  // 意图类型
  createdAt: string;     // 创建时间
}

/**
 * 获取聊天历史记录
 *
 * 从后端数据库加载之前保存的对话记录，
 * 这样刷新页面后还能看到之前的聊天内容。
 *
 * @param limit - 最多获取几条，默认 50
 * @returns 按时间正序排列的对话历史（最早的在最前面）
 */
export function fetchChatHistory(limit = 50): Promise<{ success: boolean; history: ChatHistoryItem[] }> {
  return apiRequest(`/api/vector/chat/history?limit=${limit}`);
}

/**
 * 清空所有聊天历史
 *
 * 删除后端数据库中的所有对话记录。
 */
export function clearChatHistory(): Promise<{ success: boolean; deleted: number }> {
  return apiRequest("/api/vector/chat/history", { method: "DELETE" });
}


// ---------- Session 管理 API ----------
// 1:1 复现 Codex 的 session 管理方案
// 每个 session 有唯一 ID、标题、状态、置顶标记
// 支持：新建、列表、切换、置顶、归档、删除

/**
 * 会话对象（对应后端 chat_sessions 表）
 *
 * 类似 Codex 的 threads 表中的每条记录
 */
export interface ChatSession {
  id: string;              // 唯一会话 ID (UUID)
  title: string;           // 会话标题
  status: "active" | "archived";  // 状态
  is_pinned: number;       // 是否置顶 (0/1)
  pinned_at: string | null;      // 置顶时间
  message_count: number;   // 消息数量
  last_message_at: string | null; // 最后消息时间
  created_at: string;      // 创建时间
  updated_at: string;      // 更新时间
}

/**
 * 会话消息对象（对应后端 chat_messages 表）
 *
 * 类似 Codex 的 sessions/*.jsonl 中的每条消息记录
 */
export interface SessionMessage {
  id: number;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  intent: string | null;
  created_at: string;
}

/**
 * 获取会话列表
 *
 * 对应 Codex 的 thread list 命令
 *
 * @param status - 筛选状态：active(默认) / archived / all
 * @param search - 按标题搜索（可选）
 * @returns 会话列表，置顶在前，然后按最后消息时间倒序
 */
export function fetchSessions(status: "active" | "archived" | "all" = "active", search?: string): Promise<{ success: boolean; sessions: ChatSession[] }> {
  const params = new URLSearchParams({ status });
  if (search) params.set("search", search);
  return apiRequest(`/api/sessions?${params.toString()}`);
}

/**
 * 创建新会话
 *
 * 对应 Codex 中开启一个新线程
 *
 * @param title - 会话标题（可选，默认"新对话"，首条消息后自动更新）
 * @returns 新创建的会话对象
 */
export function createSession(title?: string): Promise<{ success: boolean; session: ChatSession }> {
  return apiRequest("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

/**
 * 获取会话的消息列表
 *
 * 对应 Codex 从 sessions/*.jsonl 读取 rollout
 *
 * @param sessionId - 会话 ID
 * @returns 消息列表（按时间正序）
 */
export function fetchSessionMessages(sessionId: string): Promise<{ success: boolean; messages: SessionMessage[] }> {
  return apiRequest(`/api/sessions/${sessionId}/messages`);
}

/**
 * 更新会话（置顶/归档/重命名）
 *
 * 对应 Codex 的 pinned threads 和 archive 功能
 *
 * @param sessionId - 会话 ID
 * @param options - 更新选项
 *   - title: 新标题
 *   - isPinned: true=置顶, false=取消置顶
 *   - isArchived: true=归档, false=取消归档
 * @returns 更新后的会话对象
 */
export function updateSession(
  sessionId: string,
  options: { title?: string; isPinned?: boolean; isArchived?: boolean }
): Promise<{ success: boolean; session: ChatSession }> {
  return apiRequest(`/api/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(options),
  });
}

/**
 * 删除会话
 *
 * 对应 Codex 的 purge 命令（不可恢复）
 *
 * @param sessionId - 会话 ID
 */
export function deleteSession(sessionId: string): Promise<{ success: boolean; deleted: boolean }> {
  return apiRequest(`/api/sessions/${sessionId}`, { method: "DELETE" });
}

/**
 * 获取会话统计信息
 *
 * @returns 统计数据（活跃数、归档数、置顶数、总消息数）
 */
export function fetchSessionStats(): Promise<{ success: boolean; stats: { activeSessions: number; archivedSessions: number; pinnedSessions: number; totalMessages: number } }> {
  return apiRequest("/api/sessions/stats");
}
