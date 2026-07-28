const GROUPS = [
  { id: "preparation", label: "研究准备" },
  { id: "retrieval", label: "资料检索" },
  { id: "analysis", label: "证据与分析" },
  { id: "report", label: "报告生成" },
  { id: "review", label: "复核与归档" },
];

const STAGES = [
  ["validate_input", "校验研究标的", "preparation"],
  ["build_research_plan", "生成研究计划与章节矩阵", "preparation"],
  ["build_data_requirements", "生成本次研究的数据需求清单", "preparation"],
  ["check_provider_health", "检查数据源健康状态", "preparation"],
  ["load_structured_data", "读取结构化财务与风险数据", "retrieval"],
  ["retrieve_official_filings", "检索定期报告与公告", "retrieval"],
  ["retrieve_memory", "检索公司与行业研究记忆", "retrieval"],
  ["retrieve_news_events", "检索新闻、催化与风险事件", "retrieval"],
  ["retrieve_industry_graph", "读取产业图谱并选择可比公司", "retrieval"],
  ["retrieve_instruments", "拉取目标公司与同行数据", "retrieval"],
  ["assemble_research_context", "汇总研究上下文", "retrieval"],
  ["evaluate_cached_requirements", "评估本地数据完整性与时效性", "retrieval"],
  ["acquire_missing_requirements", "按需补取缺失或过期数据", "retrieval"],
  ["validate_acquired_data", "校验补取结果并隔离冲突", "retrieval"],
  ["materialize_acquired_data", "将已核验新数据回流研究上下文", "retrieval"],
  ["normalize_research_data", "标准化、去重并隔离异常数据", "analysis"],
  ["build_research_packet", "建立证据账本与研究数据包", "analysis"],
  ["analyze_market_peers", "分析行情、估值与同行比较", "analysis"],
  ["analyze_financials", "分析财务趋势与现金流", "analysis"],
  ["analyze_business_industry", "分析业务、行业与竞争力", "analysis"],
  ["analyze_catalysts_risks", "分析催化剂、风险与证伪条件", "analysis"],
  ["assemble_analysis", "汇总章节分析结论", "analysis"],
  ["compile_claims", "编译可引用主张与情景", "analysis"],
  ["quality_gate", "执行证据与完整性门禁", "analysis"],
  ["draft_report", "生成受治理研究初稿", "report"],
  ["validate_report", "校验初稿结构、事实与引用", "report"],
  ["persist_outputs", "保存初稿、证据包与审计记录", "report"],
  ["report_synthesis", "模型综合完整研究报告", "report"],
  ["final_report_review", "复核最终报告质量", "review"],
  ["persist_final_report", "归档最终报告与质量结果", "review"],
].map(([id, label, groupId], order) => ({ id, label, groupId, order }));

const STAGE_BY_ID = new Map(STAGES.map((stage) => [stage.id, stage]));

function deriveStatus(eventType) {
  if (eventType === "stage.failed") return "failed";
  if (eventType === "stage.warning") return "warning";
  if (eventType === "stage.completed") return "completed";
  return "running";
}

export function buildResearchExecutionSummary(events = []) {
  const stateById = new Map();
  for (const event of events) {
    const stageId = event.stage_id;
    if (!stageId || !STAGE_BY_ID.has(stageId) || !String(event.event_type || "").startsWith("stage.")) continue;
    const catalog = STAGE_BY_ID.get(stageId);
    const previous = stateById.get(stageId) || {};
    stateById.set(stageId, {
      id: stageId,
      label: catalog.label,
      groupId: catalog.groupId,
      order: catalog.order,
      status: deriveStatus(event.event_type),
      message: event.event_type === "stage.completed"
        ? "已完成"
        : event.event_type === "stage.started"
          ? "执行中"
          : event.message || previous.message || "",
      startedAt: event.event_type === "stage.started" ? event.created_at : previous.startedAt || null,
      completedAt: event.event_type !== "stage.started" ? event.created_at : previous.completedAt || null,
      level: event.level || previous.level || "info",
    });
  }
  const stages = STAGES.map((catalog) => stateById.get(catalog.id) || {
    id: catalog.id,
    label: catalog.label,
    groupId: catalog.groupId,
    order: catalog.order,
    status: "pending",
    message: "等待中",
    startedAt: null,
    completedAt: null,
    level: "info",
  });
  const groups = GROUPS.map((group) => {
    const groupStages = stages.filter((stage) => stage.groupId === group.id);
    return {
      id: group.id,
      label: group.label,
      stages: groupStages,
      completedStages: groupStages.filter((stage) => ["completed", "warning"].includes(stage.status)).length,
      totalStages: groupStages.length,
    };
  });
  const hasPendingStages = stages.some((stage) => stage.status === "pending");
  const hasRunningStages = stages.some((stage) => stage.status === "running");
  return {
    status: stages.some((stage) => stage.status === "failed")
      ? "failed"
      : hasPendingStages || hasRunningStages
        ? "running"
        : stages.some((stage) => stage.status === "warning") ? "warning" : "completed",
    completedStages: stages.filter((stage) => ["completed", "warning"].includes(stage.status)).length,
    totalStages: stages.length,
    warningStages: stages.filter((stage) => stage.status === "warning").length,
    failedStages: stages.filter((stage) => stage.status === "failed").length,
    groups,
  };
}

export const researchStageCatalog = Object.freeze(STAGES);
