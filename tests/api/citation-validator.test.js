import assert from "node:assert/strict";
import test from "node:test";

import { validateEvidenceCitations } from "../../api/services/citation-validator.js";

const catalog = [
  { evidence_id: "E001" },
  { evidence_id: "E002" },
];

test("citation validator passes fully cited time-sensitive claims", () => {
  const result = validateEvidenceCitations(
    "上证指数上涨 1.2%。[E001]\n相关新闻共 8 条。[E002]",
    catalog,
    { can_claim_current: true },
  );

  assert.equal(result.status, "passed");
  assert.equal(result.coverage, 1);
  assert.equal(result.auditable_claim_count, 2);
});

test("citation validator reports missing and invented evidence ids", () => {
  const result = validateEvidenceCitations(
    "成交额达到 1200 亿元。\n估值处于 20% 分位。[E999]",
    catalog,
    { can_claim_current: true },
  );

  assert.equal(result.status, "warning");
  assert.deepEqual(result.unknown_citation_ids, ["E999"]);
  assert.equal(result.missing_citation_claims.length, 2);
  assert.equal(result.coverage, 0);
});

test("citation validator catches current claims when the data gate is blocked", () => {
  const result = validateEvidenceCitations(
    "当前市场上涨 2.1%。[E001]\n数据不足，不能判断今日走势。",
    catalog,
    { can_claim_current: false },
  );

  assert.equal(result.status, "warning");
  assert.equal(result.current_claim_violations.length, 1);
  assert.match(result.current_claim_violations[0].text, /当前市场/);
});
