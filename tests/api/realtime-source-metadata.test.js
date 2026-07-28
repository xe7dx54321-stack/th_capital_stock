import assert from "node:assert/strict";
import test from "node:test";

import {
  parseEastmoneyRankItem,
  parseSinaRankItem,
  parseTencentResponse,
} from "../../api/services/realtime-data-service.js";

const metadata = {
  tradeDate: "2026-07-17",
  sessionStatus: "closed",
  fetchedAt: "2026-07-19T08:00:00.000Z",
  sourceUrl: "https://source.example/rank",
};

test("Sina rank adapter emits normalized source and session metadata", () => {
  const item = parseSinaRankItem({
    symbol: "sz300308", code: "300308", name: "中际旭创", trade: "188.8", changepercent: 3.2,
  }, metadata);

  assert.equal(item.ts_code, "300308.SZ");
  assert.equal(item.trade_date, "2026-07-17");
  assert.equal(item.source, "sina_realtime");
  assert.equal(item.source_url, metadata.sourceUrl);
  assert.equal(item.fetched_at, metadata.fetchedAt);
  assert.equal(item.market_session_status, "closed");
});

test("Eastmoney rank adapter uses the same normalized metadata contract", () => {
  const item = parseEastmoneyRankItem({
    f12: "600519", f14: "贵州茅台", f2: 1500, f3: -1.2, f5: 10000, f6: 3000000,
    f8: 0.2, f9: 22, f10: 1.1, f15: 1520, f16: 1490, f17: 1510, f20: 1, f21: 1,
  }, metadata);

  assert.equal(item.ts_code, "600519.SH");
  assert.equal(item.trade_date, "2026-07-17");
  assert.equal(item.source, "eastmoney_realtime");
  assert.equal(item.source_url, metadata.sourceUrl);
  assert.equal(item.fetched_at, metadata.fetchedAt);
  assert.equal(item.market_session_status, "closed");
});

test("Tencent adapter maps valuation fields by the documented protocol positions", () => {
  const fields = Array.from({ length: 60 }, () => "");
  fields[0] = "51";
  fields[2] = "300308";
  fields[3] = "1060.80";
  fields[39] = "79.14"; // PE(TTM)
  fields[44] = "9123.45"; // 流通市值（亿元）
  fields[45] = "11830.41"; // 总市值（亿元）
  fields[46] = "34.15"; // PB
  fields[47] = "1166.88"; // 涨停价，不能映射为 PS
  fields[52] = "51.58"; // 预测/动态 PE
  fields[53] = "109.57"; // 上年 PE

  const parsed = parseTencentResponse(`v_sz300308="${fields.join("~")}";`)["300308.SZ"];

  assert.equal(parsed.pe_ttm, 79.14);
  assert.equal(parsed.pe_forward, 51.58);
  assert.equal(parsed.pe_lyr, 109.57);
  assert.equal(parsed.pb, 34.15);
  assert.equal(parsed.ps_ttm, null);
  assert.equal(parsed.market_cap, 11830.41);
  assert.equal(parsed.float_market_cap, 9123.45);
});
