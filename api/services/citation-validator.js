const CITATION_PATTERN = /\[(E\d{3,})\]/g;
const AUDITABLE_PATTERN = /(?:\d+(?:\.\d+)?\s*(?:%|倍|元|点|亿|万)?|今日|今天|当前|实时|涨幅|跌幅|成交|估值|市盈率|市净率|PE|PB|价格|新闻|公告|数据截至)/i;
const CURRENT_CLAIM_PATTERN = /(?:今日|今天|当前|实时|截至今日|目前)/;
const CURRENT_NEGATION_PATTERN = /(?:无法|不能|不可|非实时|数据不足|不代表|仅供历史|未获取|缺失|待核验|禁止|没有)/;

function citationIds(text) {
  return [...String(text || "").matchAll(CITATION_PATTERN)].map((match) => match[1]);
}

function normalizeClaimLine(line) {
  return String(line || "")
    .replace(/^\s*(?:[-*+]\s+|\d+[.)、]\s*)/, "")
    .replace(/^>\s*/, "")
    .trim();
}

export function validateEvidenceCitations(text, evidenceCatalog = [], dataHealth = null) {
  const knownIds = new Set(evidenceCatalog.map((item) => item.evidence_id).filter(Boolean));
  const allCitedIds = [...new Set(citationIds(text))];
  const unknownCitationIds = allCitedIds.filter((id) => !knownIds.has(id));
  const auditableClaims = [];
  const missingCitationClaims = [];
  const currentClaimViolations = [];

  String(text || "").split(/\r?\n/).forEach((rawLine, index) => {
    const line = normalizeClaimLine(rawLine);
    if (!line || line.startsWith("#") || /^\|?\s*:?-{3,}/.test(line)) return;
    if (!AUDITABLE_PATTERN.test(line)) return;
    const ids = [...new Set(citationIds(line))];
    const claim = { line_number: index + 1, text: line.slice(0, 500), evidence_ids: ids };
    auditableClaims.push(claim);
    if (ids.every((id) => !knownIds.has(id))) missingCitationClaims.push(claim);
    if (dataHealth?.can_claim_current === false && CURRENT_CLAIM_PATTERN.test(line) && !CURRENT_NEGATION_PATTERN.test(line)) {
      currentClaimViolations.push(claim);
    }
  });

  const citedClaims = auditableClaims.length - missingCitationClaims.length;
  const coverage = auditableClaims.length === 0 ? 1 : citedClaims / auditableClaims.length;
  const applicable = evidenceCatalog.length > 0 || dataHealth !== null;
  const passed = applicable && unknownCitationIds.length === 0 && missingCitationClaims.length === 0 && currentClaimViolations.length === 0;
  return {
    status: !applicable ? "not_applicable" : passed ? "passed" : "warning",
    coverage: Number(coverage.toFixed(3)),
    auditable_claim_count: auditableClaims.length,
    cited_claim_count: citedClaims,
    cited_evidence_ids: allCitedIds,
    unknown_citation_ids: unknownCitationIds,
    missing_citation_claims: missingCitationClaims.slice(0, 20),
    current_claim_violations: currentClaimViolations.slice(0, 20),
  };
}

export { citationIds, normalizeClaimLine };
