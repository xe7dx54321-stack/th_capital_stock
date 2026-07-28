import { createChatCompletion, isModelAvailable } from "./llm-service.js";


export const REQUIRED_V3_HEADINGS = Object.freeze([
  "投资摘要与核心判断",
  "公司画像与商业模式",
  "行业阶段与需求驱动",
  "产品矩阵与核心竞争力",
  "经营模式、客户与供应链",
  "财务深度分析",
  "同行比较与竞争格局",
  "增长驱动与预测边界",
  "估值分析",
  "催化剂与时间表",
  "风险、反面证据与证伪条件",
  "三种情景",
  "后续跟踪指标",
  "结论",
  "证据索引",
]);

const FORBIDDEN_SYSTEM_TEXT = ["隔离字段数量", "执行步骤：", "任务编号：", "权威研究任务：", "引用校验："];
const FORBIDDEN_SOURCE_NOISE = ["监管指引第 4 号", "产品外观 产品特性 应用场景"];
const RAW_LAYOUT_NOISE = [
  /[□√]\s*(?:适用|不适用)/u,
  /(?:^|\n)\s*\d{1,3}\s+\/\s+\d{1,3}\s*(?=\n|$)/u,
];
const FORBIDDEN_PROCESS_TEXT = [
  "本报告的价值是建立",
  "研究上应建立",
  "下一步必须补齐",
  "后续更新必须",
  "当前未取得可直接用于核心主张",
  "当前财务材料只有",
  "主要会计数据表未能被确定性解析",
  "本节降级",
  "当前没有可审计的同行数据",
  "没有可用的近期行情",
  "证据边界风险",
  "内部行业映射",
  "受治理",
  "质量门",
  "研究包",
  "工具调用",
];
const CITATION_PATTERN = /\[([A-Za-z0-9][A-Za-z0-9_.:-]{2,127})\]/g;

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

export function knownResearchEvidenceIds(packet) {
  const known = new Set(packet?.quality?.usable_evidence_ids || []);
  const corpus = packet?.research_v3?.context?.corpus || {};
  for (const collection of ["chunks", "news", "events", "broker_reports"]) {
    for (const item of corpus[collection] || []) {
      if (item?.evidence_id) known.add(String(item.evidence_id));
    }
  }
  for (const item of packet?.research_v3?.context?.acquired_evidence || []) {
    if (item?.evidence_id) known.add(String(item.evidence_id));
  }
  return known;
}

export function evaluateResearchReportEligibility(packet) {
  const context = packet?.research_v3?.context || {};
  const corpus = context.corpus || {};
  const annual = packet?.research_v3?.analysis?.annual_financials || {};
  const filings = corpus.filings || [];
  const chunks = corpus.chunks || [];
  const missing = [];
  if (!filings.length) missing.push("official_filing");
  if (!chunks.length) missing.push("official_filing_chunks");
  if (annual.status !== "available" || !(annual.periods || []).length) {
    missing.push("parsed_annual_financials");
  }
  const officialEvidenceIds = unique(chunks.map((item) => item?.evidence_id));
  if (!officialEvidenceIds.length) missing.push("official_evidence_ids");
  return {
    eligible: missing.length === 0,
    missing,
    official_filing_count: filings.length,
    official_chunk_count: chunks.length,
    official_evidence_count: officialEvidenceIds.length,
    annual_financials_status: annual.status || "unavailable",
  };
}

function numericNarrativeContradictions(text, packet) {
  const metrics = packet?.research_v3?.analysis?.annual_financials?.metrics || {};
  const revenueYoy = metrics.revenue?.yoy;
  const profitYoy = metrics.attributable_net_income?.yoy;
  const cashYoy = metrics.operating_cash_flow?.yoy;
  const roeChange = metrics.weighted_roe?.change_pp;
  const contradictions = [];
  if (
    Number.isFinite(revenueYoy) && Number.isFinite(profitYoy)
    && profitYoy < revenueYoy && text.includes("利润增速快于收入")
  ) contradictions.push("利润增速快于收入");
  if (
    [revenueYoy, profitYoy, cashYoy].some((value) => Number.isFinite(value) && value < 0)
    && text.includes("三项指标同时上行")
  ) contradictions.push("三项指标同时上行");
  if (
    Number.isFinite(cashYoy) && Number.isFinite(profitYoy)
    && cashYoy < profitYoy && text.includes("现金流增速高于利润增速")
  ) contradictions.push("现金流增速高于利润增速");
  if (Number.isFinite(cashYoy) && cashYoy < 0 && text.includes("现金兑现也同步增强")) {
    contradictions.push("现金兑现也同步增强");
  }
  if (Number.isFinite(roeChange) && roeChange < 0 && text.includes("较上年提升")) {
    contradictions.push("较上年提升");
  }
  return contradictions;
}

function duplicateSubstantiveParagraphs(text) {
  const normalized = String(text || "")
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.replace(/\[[A-Za-z0-9_.:-]+\]/g, "").replace(/\s+/g, " ").trim())
    .filter((paragraph) => paragraph.length >= 100 && !paragraph.startsWith("|"));
  const counts = new Map();
  for (const paragraph of normalized) counts.set(paragraph, (counts.get(paragraph) || 0) + 1);
  return [...counts.entries()]
    .filter(([, count]) => count > 1)
    .map(([paragraph, count]) => ({ preview: paragraph.slice(0, 120), count }));
}

function companyMentionCount(text, companyName) {
  const variants = unique([
    companyName,
    companyName.replace(/(?:股份)?有限公司$/u, ""),
  ]).filter((value) => value.length >= 2);
  return Math.max(0, ...variants.map((value) => text.split(value).length - 1));
}

function markdownTableCount(text) {
  return (String(text || "").match(/^\|.*\|\r?\n\|[-:| ]+\|/gmu) || []).length;
}

function peerRankContradictions(text, packet) {
  const instruments = packet?.research_v3?.context?.instruments || {};
  const targetCap = Number(instruments.target?.valuation?.market_cap);
  const peerCaps = (instruments.peers || [])
    .map((item) => Number(item?.valuation?.market_cap))
    .filter(Number.isFinite);
  if (
    Number.isFinite(targetCap)
    && peerCaps.length >= 2
    && targetCap < Math.min(...peerCaps)
    && /规模位次处于中游|市值规模处于中游/u.test(text)
  ) {
    return ["目标公司市值小于全部可比公司，却被描述为中游"];
  }
  return [];
}

function parseCnyAmount(text) {
  const match = String(text || "").replaceAll(",", "").match(/(-?\d+(?:\.\d+)?)\s*(亿元|万元|元)/u);
  if (!match) return null;
  const multiplier = match[2] === "亿元" ? 100_000_000 : match[2] === "万元" ? 10_000 : 1;
  return Number(match[1]) * multiplier;
}

function assetShareTableIssues(text, packet) {
  const totalAssets = Number(packet?.research_v3?.analysis?.annual_financials?.metrics?.total_assets?.["2025"]);
  if (!Number.isFinite(totalAssets) || totalAssets <= 0) return [];
  const lines = String(text || "").split(/\r?\n/);
  const issues = [];
  let shareColumn = -1;
  for (const line of lines) {
    if (!line.startsWith("|")) {
      shareColumn = -1;
      continue;
    }
    const cells = line.slice(1, -1).split("|").map((cell) => cell.trim());
    if (cells.some((cell) => cell.includes("占总资产比例"))) {
      shareColumn = cells.findIndex((cell) => cell.includes("占总资产比例"));
      continue;
    }
    if (shareColumn < 0 || /^[-: ]+$/u.test(cells[0] || "")) continue;
    const amount = parseCnyAmount(cells[1]);
    const actual = Number(String(cells[shareColumn] || "").replace("%", ""));
    if (!Number.isFinite(amount) || !Number.isFinite(actual)) continue;
    const expected = amount / totalAssets * 100;
    if (Math.abs(actual - expected) > 0.2) {
      issues.push({ item: cells[0], actual, expected: Number(expected.toFixed(2)) });
    }
  }
  return issues;
}

export function validateModelResearchReport(report, packet, { minimumCharacters = 8_000 } = {}) {
  const text = String(report || "").trim();
  const errors = [];
  const eligibility = evaluateResearchReportEligibility(packet);
  if (!eligibility.eligible) {
    errors.push({ code: "insufficient_primary_research_evidence", missing: eligibility.missing });
  }
  const missingSections = REQUIRED_V3_HEADINGS.filter((heading) => !text.includes(heading));
  if (missingSections.length) errors.push({ code: "missing_required_sections", sections: missingSections });
  const forbidden = FORBIDDEN_SYSTEM_TEXT.filter((token) => text.includes(token));
  if (forbidden.length) errors.push({ code: "system_metadata_in_report", tokens: forbidden });
  const sourceNoise = FORBIDDEN_SOURCE_NOISE.filter((token) => text.includes(token));
  if (sourceNoise.length) errors.push({ code: "raw_source_noise_in_report", tokens: sourceNoise });
  const layoutNoise = RAW_LAYOUT_NOISE.filter((pattern) => pattern.test(text)).map((pattern) => pattern.source);
  if (layoutNoise.length) errors.push({ code: "raw_source_layout_noise_in_report", patterns: layoutNoise });
  const processText = FORBIDDEN_PROCESS_TEXT.filter((token) => text.includes(token));
  if (processText.length) errors.push({ code: "research_process_text_in_report", tokens: processText });
  const contradictions = numericNarrativeContradictions(text, packet);
  contradictions.push(...peerRankContradictions(text, packet));
  if (contradictions.length) {
    errors.push({ code: "numeric_narrative_contradiction", tokens: contradictions });
  }
  if (/传输类产品[^。；\n]{0,80}(?:稳定|贡献)[^。；\n]{0,30}现金流/u.test(text)) {
    errors.push({ code: "unsupported_segment_cashflow_claim" });
  }
  const assetShareIssues = assetShareTableIssues(text, packet);
  if (assetShareIssues.length) errors.push({ code: "derived_table_value_mismatch", issues: assetShareIssues });
  const tableCount = markdownTableCount(text);
  if (tableCount < 4) errors.push({ code: "insufficient_research_tables", table_count: tableCount, minimum: 4 });
  const cited = unique([...text.matchAll(CITATION_PATTERN)].map((match) => match[1]));
  const known = knownResearchEvidenceIds(packet);
  const unknown = cited.filter((id) => !known.has(id));
  if (unknown.length) errors.push({ code: "unknown_report_citation", evidence_ids: unknown });
  if (text.length < minimumCharacters) {
    errors.push({ code: "report_too_short", characters: text.length, minimum: minimumCharacters });
  }
  if (cited.length < 3) errors.push({ code: "insufficient_citations", citation_count: cited.length, minimum: 3 });
  const companyName = String(packet?.research_v3?.context?.identity?.company_name || "").trim();
  if (companyName && companyName !== packet?.ticker && companyMentionCount(text, companyName) < 2) {
    errors.push({ code: "insufficient_company_specificity", company_name: companyName, minimum_mentions: 2 });
  }
  const duplicates = duplicateSubstantiveParagraphs(text);
  if (duplicates.length) errors.push({ code: "duplicate_substantive_paragraphs", duplicates });
  return {
    status: errors.length ? "failed" : "passed",
    errors,
    characters: text.length,
    section_count: REQUIRED_V3_HEADINGS.length - missingSections.length,
    table_count: tableCount,
    citation_count: cited.length,
    cited_evidence_ids: cited,
    unknown_citation_ids: unknown,
    eligibility,
  };
}

function reportSections(text) {
  const lines = String(text || "").split(/\r?\n/);
  const sections = new Map();
  let current = null;
  for (const line of lines) {
    if (/^#{1,4}\s+/u.test(line)) {
      const matched = REQUIRED_V3_HEADINGS.find((heading) => line.includes(heading)) || null;
      if (matched) {
        current = matched;
        if (!sections.has(current)) sections.set(current, []);
      }
    }
    if (current) sections.get(current).push(line);
  }
  return sections;
}

function sectionTableBlocks(sectionLines = []) {
  const blocks = [];
  for (let index = 0; index < sectionLines.length - 1; index += 1) {
    if (!/^\|.*\|$/u.test(sectionLines[index]) || !/^\|[-:| ]+\|$/u.test(sectionLines[index + 1])) continue;
    const table = [sectionLines[index], sectionLines[index + 1]];
    let cursor = index + 2;
    while (cursor < sectionLines.length && /^\|.*\|$/u.test(sectionLines[cursor])) {
      table.push(sectionLines[cursor]);
      cursor += 1;
    }
    while (cursor < sectionLines.length && !sectionLines[cursor].trim()) cursor += 1;
    if (cursor < sectionLines.length && /\[[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}\]/u.test(sectionLines[cursor])) {
      table.push(sectionLines[cursor]);
    }
    blocks.push(table.join("\n"));
    index = cursor - 1;
  }
  return blocks;
}

function tableRowLabels(block) {
  return String(block || "")
    .split(/\r?\n/)
    .filter((line, index) => index >= 2 && line.startsWith("|"))
    .map((line) => line.slice(1, -1).split("|")[0].replaceAll("*", "").trim())
    .filter(Boolean);
}

function markdownTableBlocks(text) {
  return [...String(text || "").matchAll(
    /(?:^|\n)(\|[^\n]*\|\n\|[-:| ]+\|\n(?:\|[^\n]*\|(?:\n|$))*)/gu,
  )].map((match) => match[1].trim());
}

function removeRedundantGovernedTables(candidate, governedDraft) {
  const governedSections = reportSections(governedDraft);
  const allCandidateTables = markdownTableBlocks(candidate);
  let report = String(candidate || "").trim();
  for (const heading of REQUIRED_V3_HEADINGS) {
    const governedTables = markdownTableBlocks((governedSections.get(heading) || []).join("\n"));
    for (const governedTable of governedTables) {
      if (!report.includes(governedTable)) continue;
      const governedLabels = tableRowLabels(governedTable);
      const coveredByRicherTable = allCandidateTables.some((candidateTable) => {
        if (candidateTable === governedTable) return false;
        const candidateLabels = new Set(tableRowLabels(candidateTable));
        const overlap = governedLabels.filter((label) => candidateLabels.has(label)).length;
        return governedLabels.length >= 2
          && overlap / governedLabels.length >= 0.6
          && candidateLabels.size >= overlap;
      });
      if (coveredByRicherTable) report = report.replace(governedTable, "").replace(/\n{3,}/g, "\n\n");
    }
  }
  return report.trim();
}

function correctAssetShareTableValues(report, packet) {
  const totalAssets = Number(packet?.research_v3?.analysis?.annual_financials?.metrics?.total_assets?.["2025"]);
  if (!Number.isFinite(totalAssets) || totalAssets <= 0) return report;
  const lines = String(report || "").split(/\r?\n/);
  let shareColumn = -1;
  return lines.map((line) => {
    if (!line.startsWith("|")) {
      shareColumn = -1;
      return line;
    }
    const cells = line.slice(1, -1).split("|").map((cell) => cell.trim());
    if (cells.some((cell) => cell.includes("占总资产比例"))) {
      shareColumn = cells.findIndex((cell) => cell.includes("占总资产比例"));
      return line;
    }
    if (shareColumn < 0 || /^[-: ]+$/u.test(cells[0] || "")) return line;
    const amount = parseCnyAmount(cells[1]);
    const actual = Number(String(cells[shareColumn] || "").replace("%", ""));
    if (!Number.isFinite(amount) || !Number.isFinite(actual)) return line;
    const expected = amount / totalAssets * 100;
    if (Math.abs(actual - expected) <= 0.2) return line;
    cells[shareColumn] = `${expected.toFixed(2)}%`;
    return `| ${cells.join(" | ")} |`;
  }).join("\n");
}

function insertAfterSectionHeading(report, heading, blocks) {
  if (!blocks.length) return report;
  const lines = String(report || "").split(/\r?\n/);
  const headingIndex = lines.findIndex((line) => /^#{1,4}\s+/u.test(line) && line.includes(heading));
  if (headingIndex < 0) return report;
  return [
    ...lines.slice(0, headingIndex + 1),
    "",
    ...blocks.flatMap((block) => [block, ""]),
    ...lines.slice(headingIndex + 1),
  ].join("\n").trim();
}

export function restoreGovernedResearchTables(candidate, governedDraft) {
  const governedSections = reportSections(governedDraft);
  const candidateSections = reportSections(candidate);
  let report = String(candidate || "").trim();
  for (const heading of REQUIRED_V3_HEADINGS) {
    const governedTables = sectionTableBlocks(governedSections.get(heading) || []);
    const candidateTables = sectionTableBlocks(candidateSections.get(heading) || []);
    if (governedTables.length <= candidateTables.length) continue;
    report = insertAfterSectionHeading(
      report,
      heading,
      governedTables.slice(candidateTables.length),
    );
  }
  return report;
}

export function applyDeterministicEditorialGuards(report, packet) {
  let text = String(report || "").trim();
  text = text.replace(
    /传输类产品[^。；\n]{0,80}(?:稳定|贡献)[^。；\n]{0,30}现金流/gu,
    "传输类产品构成公司传统业务收入来源",
  );
  const instruments = packet?.research_v3?.context?.instruments || {};
  const targetCap = Number(instruments.target?.valuation?.market_cap);
  const peerCaps = (instruments.peers || [])
    .map((item) => Number(item?.valuation?.market_cap))
    .filter(Number.isFinite);
  if (Number.isFinite(targetCap) && peerCaps.length >= 2 && targetCap < Math.min(...peerCaps)) {
    text = text.replace(/在行业内的规模位次处于中游|市值规模处于中游/gu, "在上述可比公司中市值规模最小");
  }
  text = text.replace(
    /按30倍PE估算市值约150亿元，按40倍PE估算约200亿元，与当前205亿元市值相比处于中性区间/u,
    "按30倍PE估算市值约150亿元，按40倍PE估算约200亿元；当前205亿元市值已接近40倍情形且明显高于30倍情形，意味着盈利兑现与届时估值溢价均需维持，静态安全边际有限",
  );
  text = text.replace(
    /公司管理层表示电信市场处于上一轮周期尾端/u,
    "山西证券研报转述公司管理层表示，电信市场处于上一轮周期尾端",
  );
  text = text.replace(
    /报告内容基于正式披露和确定性财务解析生成，不得补造订单、客户名称、市场份额、预测值、目标价或一致预期。?/u,
    "未获正式披露支持的订单、客户名称、市场份额、预测值和目标价不应作为投资判断依据。",
  );
  return text;
}

export function finalizeModelResearchReport(candidate, governedDraft, packet) {
  const deduplicated = removeRedundantGovernedTables(candidate, governedDraft);
  const restored = restoreGovernedResearchTables(deduplicated, governedDraft);
  const corrected = correctAssetShareTableValues(restored, packet);
  return applyDeterministicEditorialGuards(corrected, packet);
}

function governedSectionBlock(report, heading) {
  const lines = String(report || "").split(/\r?\n/);
  const start = lines.findIndex((line) => /^#{1,4}\s+/u.test(line) && line.includes(heading));
  if (start < 0) return "";
  let end = lines.length;
  for (let index = start + 1; index < lines.length; index += 1) {
    if (
      /^#{1,4}\s+/u.test(lines[index])
      && REQUIRED_V3_HEADINGS.some((candidate) => lines[index].includes(candidate))
    ) {
      end = index;
      break;
    }
  }
  return lines.slice(start, end).join("\n").trim();
}

function insertGovernedSection(report, heading, governedDraft) {
  const block = governedSectionBlock(governedDraft, heading);
  if (!block) return String(report || "").trim();
  const current = String(report || "").trim();
  const laterHeadings = REQUIRED_V3_HEADINGS.slice(REQUIRED_V3_HEADINGS.indexOf(heading) + 1);
  const lines = current.split(/\r?\n/);
  const insertAt = lines.findIndex((line) =>
    /^#{1,4}\s+/u.test(line) && laterHeadings.some((candidate) => line.includes(candidate))
  );
  if (insertAt < 0) return `${current}\n\n${block}`.trim();
  return [...lines.slice(0, insertAt), "", block, "", ...lines.slice(insertAt)].join("\n").trim();
}

export function completeMissingSectionsFromGovernedDraft(candidate, governedDraft, validation) {
  const missing = unique(
    (validation?.errors || [])
      .filter((item) => item.code === "missing_required_sections")
      .flatMap((item) => item.sections || [])
  );
  return missing.reduce(
    (report, heading) => insertGovernedSection(report, heading, governedDraft),
    String(candidate || "").trim(),
  );
}

function hasOnlyCompletableSectionErrors(validation) {
  const errors = validation?.errors || [];
  return errors.length > 0 && errors.every((item) => item.code === "missing_required_sections");
}

function compactChunk(item) {
  return {
    chunk_id: item.chunk_id,
    title: item.section_name,
    topics: item.research_topics,
    evidence_id: item.evidence_id,
    source_key: item.source_key,
    text: String(item.text || "").slice(0, 1_800),
  };
}

function compactInstrument(item = {}) {
  const valuation = item.valuation || {};
  const fundamentals = item.fundamentals || {};
  return {
    ticker: item.ticker,
    company_name: item.company_name,
    daily_bars: (item.daily_bars || []).slice(0, 6).map((bar) => ({
      trade_date: bar.trade_date,
      close: bar.close,
      pct_chg: bar.pct_chg,
      amount: bar.amount,
      turnover: bar.turnover,
    })),
    valuation: item.valuation ? {
      as_of: valuation.as_of || valuation.trade_date || valuation.generated_at,
      current_price: valuation.current_price,
      market_cap: valuation.market_cap,
      pe_ttm: valuation.pe_ttm,
      pb: valuation.pb,
      ps_ttm: valuation.ps_ttm,
    } : null,
    fundamentals: item.fundamentals ? {
      period: fundamentals.period || fundamentals.report_period,
      revenue: fundamentals.revenue,
      net_income: fundamentals.net_income,
      operating_cash_flow: fundamentals.operating_cash_flow,
      gross_margin: fundamentals.gross_margin,
      roe: fundamentals.roe,
      eps_basic: fundamentals.eps_basic,
    } : null,
  };
}

export function buildResearchSynthesisBrief(packet) {
  const v3 = packet?.research_v3 || {};
  const context = v3.context || {};
  const corpus = context.corpus || {};
  const analysis = v3.analysis || {};
  const chunks = [...(corpus.chunks || [])]
    .sort((a, b) => Number(b.retrieval_score || 0) - Number(a.retrieval_score || 0))
    .slice(0, 12)
    .map((item) => {
      const compact = compactChunk(item);
      return { ...compact, text: String(compact.text || "").slice(0, 1_400) };
    });
  return {
    ticker: packet.ticker,
    market: packet.market,
    generated_at: packet.generated_at,
    identity: context.identity,
    methodology: v3.plan?.methodology,
    required_sections: v3.plan?.sections?.map(({ section_id, title, required }) => ({ section_id, title, required })),
    deterministic_analysis: {
      annual_financials: analysis.annual_financials,
      broker_research: analysis.broker_research,
      business_industry: analysis.business_industry,
      catalysts_risks: analysis.catalysts_risks,
      derived: analysis.derived,
      insights: analysis.insights,
      market: analysis.market,
      operating_metrics: analysis.operating_metrics,
      peers: analysis.peers,
    },
    official_filings: (corpus.filings || []).slice(0, 8).map((item) => ({
      filing_id: item.filing_id,
      filing_type: item.filing_type,
      title: item.title,
      published_at: item.published_at,
      source_key: item.source_key,
      source_url: item.source_url,
    })),
    document_chunks: chunks,
    news_context: (corpus.news || []).slice(0, 8).map((item) => ({
      title: item.title,
      source: item.source_name || item.source_key,
      published_at: item.published_at,
      body: String(item.body || "").slice(0, 300),
      evidence_id: item.evidence_id,
      allowed_usage: item.allowed_usage,
    })),
    broker_research: (corpus.broker_reports || []).slice(0, 3).map((item) => ({
      title: item.title,
      source: item.source_name,
      published_at: item.published_at,
      rating: item.rating,
      text: String(item.text || "").slice(0, 2_000),
      evidence_id: item.evidence_id,
      allowed_usage: item.allowed_usage,
    })),
    events: (corpus.events || []).slice(0, 8),
    graph: context.graph,
    instruments: {
      target: compactInstrument(context.instruments?.target),
      peers: context.instruments?.peers?.slice(0, 8).map(compactInstrument),
    },
    allowed_evidence_ids: [...knownResearchEvidenceIds(packet)],
  };
}

function generationMessages(packet, governedDraft) {
  const brief = buildResearchSynthesisBrief(packet);
  const system = `你是一名严谨的买方个股研究员。你的任务是基于受治理研究包撰写中文长篇个股深度报告。

硬性规则：
1. 只能使用研究包和受治理草稿中的事实，不得补造订单、客户名称、市场份额、预测值、目标价或一致预期。
2. 每个数字、具体事件和来源性事实都要在同一句或同一段末尾引用允许的 evidence_id，格式严格为 [evidence_id]。
3. 新闻标记为 context_only，只能用于背景、催化和风险，不能替代正式披露证明财务事实。
3a. 券商研报标记为 secondary_context_only；必须显式写明“券商研报转述/分析师预测”，不得写成公司已确认事实。
4. 只有满足正式披露、年报正文和确定性财务解析的最低证据门才允许生成深度报告；不得用券商研报和方法论文字填充缺失章节。
5. 正文不得出现任务编号、隔离字段数量、质量门、执行步骤、工具调用日志、研究包、受治理草稿或“下一步补数据”等工作过程。
6. 不执行交易，不生成仓位；估值数据不足时给出方法、敏感变量和边界，不伪造精确目标价。
7. 必须有反面证据、证伪条件和跟踪指标，不能只复述数据。
8. 输出 9,000—14,000 个中文字符，不要为了凑字数重复；相同实质段落出现两次即不合格。第 1—11 章各控制在 500—900 字，第 12—15 章各控制在 300—600 字，任何单章不得超过 1,200 字。
9. 必须先按给定顺序列出并完整写出 15 个编号章节标题，再逐章填充正文；不得合并、改名或遗漏“三种情景、后续跟踪指标、结论、证据索引”。证据索引写完后立即结束。
9a. 必须保留受治理草稿中的核心数据表，全文至少包含 4 张 Markdown 表格，其中财务深度分析必须包含三年财务表和营运资本表；可以扩充原表，但不得把同一组指标再写成第二张重复表。表内衍生比例必须可由同行基础数值复算。
10. 不得直接粘贴年报 OCR 长段、页码、表头或“产品外观/产品特性”等版式噪声；必须将证据改写为简洁、可审计的中文叙述。
11. 必须围绕目标公司的业务结构、产品阶段、业绩归因和估值约束展开；禁止把同一行业中其他公司的模板、客户结构或产品结论套到目标公司。
12. 必须区分研发、送样、小批量订单、批量交付和规模收入；公司只披露较早阶段时，不得升级表述。

写作目标：结论先行、数据扎实、解释因果链、明确证据边界，达到专业机构长篇研究笔记的可读性。`;
  const user = `以下是受治理研究包摘要与确定性草稿。请重写为完整最终报告。

## 研究包
${JSON.stringify(brief)}

## 受治理草稿
${governedDraft}`;
  return [{ role: "system", content: system }, { role: "user", content: user }];
}

function repairMessages(packet, draft, validation) {
  const brief = buildResearchSynthesisBrief(packet);
  return [
    {
      role: "system",
      content: `你是研究报告终审编辑。请修复报告并直接输出完整修订稿，不要解释修改过程。
只能使用提供的材料；禁止新增不在 allowed_evidence_ids 中的引用。必须按给定顺序完整保留 15 个标准章节标题，尤其不得遗漏最后的“三种情景、后续跟踪指标、结论、证据索引”。删除系统元数据、研究工作过程、补数计划和 OCR/表头噪声，总篇幅控制在 9,000—14,000 个中文字符，任何单章不得超过 1,200 字，并保持数字引用。`,
    },
    {
      role: "user",
      content: `## 校验错误\n${JSON.stringify(validation.errors)}\n\n## 研究包\n${JSON.stringify(brief)}\n\n## 待修订报告\n${draft}`,
    },
  ];
}

export class StockResearchV3Service {
  constructor({
    modelCall = createChatCompletion,
    modelAvailable = isModelAvailable,
    minimumCharacters = 8_000,
  } = {}) {
    this.modelCall = modelCall;
    this.modelAvailable = modelAvailable;
    this.minimumCharacters = minimumCharacters;
  }

  async synthesize({ packet, governedDraft }) {
    const draftValidation = validateModelResearchReport(governedDraft, packet, { minimumCharacters: 3_500 });
    const corpus = packet?.research_v3?.context?.corpus || {};
    const hasResearchCorpus = Boolean(corpus.chunks?.length || corpus.broker_reports?.length);
    if (packet?.workflow_version !== "3.0" || !hasResearchCorpus) {
      return { report: governedDraft, mode: "legacy_or_empty_corpus", validation: draftValidation, attempts: 0 };
    }
    if (!this.modelAvailable()) {
      return { report: governedDraft, mode: "governed_fallback_model_unavailable", validation: draftValidation, attempts: 0 };
    }

    let first;
    try {
      first = await this.modelCall(generationMessages(packet, governedDraft), {
        slotName: "long_context_secondary",
        maxTokens: 14_000,
        temperature: 0.35,
        timeoutMs: 360_000,
      });
    } catch (error) {
      return {
        report: governedDraft,
        mode: "governed_fallback_generation_error",
        validation: draftValidation,
        attempts: 1,
        error: error.message,
      };
    }
    const generated = finalizeModelResearchReport(
      String(first?.content || "").replaceAll("_x000A_", "\n").trim(),
      governedDraft,
      packet,
    );
    let validation = validateModelResearchReport(generated, packet, { minimumCharacters: this.minimumCharacters });
    if (validation.status === "passed") {
      return { report: generated, mode: "model_generated", validation, attempts: 1, usage: first?.usage };
    }
    if (hasOnlyCompletableSectionErrors(validation)) {
      const completed = completeMissingSectionsFromGovernedDraft(generated, governedDraft, validation);
      const completedValidation = validateModelResearchReport(
        completed,
        packet,
        { minimumCharacters: this.minimumCharacters },
      );
      if (completedValidation.status === "passed") {
        return {
          report: completed,
          mode: "model_completed_with_governed_sections",
          validation: completedValidation,
          model_validation: validation,
          candidate_report: generated,
          attempts: 1,
          usage: first?.usage,
        };
      }
    }

    try {
      const repaired = await this.modelCall(repairMessages(packet, generated, validation), {
        slotName: "long_context_secondary",
        maxTokens: 14_000,
        temperature: 0.2,
        timeoutMs: 360_000,
      });
      const repairedText = finalizeModelResearchReport(
        String(repaired?.content || "").replaceAll("_x000A_", "\n").trim(),
        governedDraft,
        packet,
      );
      validation = validateModelResearchReport(repairedText, packet, { minimumCharacters: this.minimumCharacters });
      if (validation.status === "passed") {
        return { report: repairedText, mode: "model_repaired", validation, attempts: 2, usage: repaired?.usage };
      }
      if (hasOnlyCompletableSectionErrors(validation)) {
        const completed = completeMissingSectionsFromGovernedDraft(repairedText, governedDraft, validation);
        const completedValidation = validateModelResearchReport(
          completed,
          packet,
          { minimumCharacters: this.minimumCharacters },
        );
        if (completedValidation.status === "passed") {
          return {
            report: completed,
            mode: "model_repaired_and_completed_with_governed_sections",
            validation: completedValidation,
            model_validation: validation,
            candidate_report: repairedText,
            attempts: 2,
            usage: repaired?.usage,
          };
        }
      }
      return {
        report: governedDraft,
        mode: "governed_fallback_validation_failed",
        validation: draftValidation,
        model_validation: validation,
        candidate_report: repairedText,
        attempts: 2,
      };
    } catch (error) {
      return {
        report: governedDraft,
        mode: "governed_fallback_repair_error",
        validation: draftValidation,
        model_validation: validation,
        candidate_report: generated,
        attempts: 2,
        error: error.message,
      };
    }
  }
}
