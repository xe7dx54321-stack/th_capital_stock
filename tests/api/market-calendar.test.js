import assert from "node:assert/strict";
import test from "node:test";

import {
  expectedLatestTradingDay,
  isTradingDay,
  marketSessionState,
  tradingSessionLag,
} from "../../api/services/market-calendar.js";

test("A-share calendar uses the latest completed session on weekends and before close", () => {
  assert.equal(expectedLatestTradingDay("A", "2026-07-19T08:00:00.000Z"), "2026-07-17"); // 周日
  assert.equal(expectedLatestTradingDay("A", "2026-07-20T02:00:00.000Z"), "2026-07-17"); // 周一 10:00
  assert.equal(expectedLatestTradingDay("A", "2026-07-20T10:30:00.000Z"), "2026-07-20"); // 周一 18:30
});

test("market session distinguishes intraday observations from completed sessions", () => {
  assert.deepEqual(marketSessionState("A", "2026-07-20T02:00:00.000Z"), {
    market: "A", local_date: "2026-07-20", status: "open", observation_date: "2026-07-20",
  });
  assert.deepEqual(marketSessionState("A", "2026-07-19T08:00:00.000Z"), {
    market: "A", local_date: "2026-07-19", status: "closed", observation_date: "2026-07-17",
  });
});

test("A-share calendar excludes configured 2026 exchange holidays", () => {
  assert.equal(isTradingDay("A", "2026-06-19"), false);
  assert.equal(expectedLatestTradingDay("A", "2026-06-19T11:00:00.000Z"), "2026-06-18");
});

test("trading-session lag counts sessions instead of natural days", () => {
  assert.equal(tradingSessionLag("A", "2026-07-17", "2026-07-20"), 1);
  assert.equal(tradingSessionLag("A", "2026-07-18", "2026-07-20"), null);
  assert.equal(tradingSessionLag("A", "2026-07-21", "2026-07-20"), null);
});
