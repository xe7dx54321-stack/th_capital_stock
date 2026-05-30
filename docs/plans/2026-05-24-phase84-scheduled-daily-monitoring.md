# Phase 84: Scheduled Daily Monitoring Runner & Portfolio Watch Board v1

## Goal
Integrate Phase 83 multi-market monitoring into a daily runner with portfolio watch board and internal brief.

## Key Decisions
1. Daily runner supports dry-run / execute / skip-network modes
2. 8 ticker universe: 7 covered, 1 blocked (300394.SZ)
3. Run history written to gitignored JSONL path
4. Previous run comparison handles first_run_baseline gracefully
5. Status classifier priority: blocked > anomaly > strengthened > weakened > unchanged
6. Portfolio watch board: 5 sections for quick human scan
7. Daily internal brief: boss summary first, analyst detail later
8. Cron disabled by default; valuation/portfolio construction explicitly disabled
9. No mock/fixture; no raw/OCR/browser; no pending/order/trade

## Daily Schedule
- Mode: manual runner ready (cron_enabled=false)
- Recommended frequency: daily
- Timezone: Asia/Shanghai
- Run window: after market close or morning review

## Integration Points
- Signals loaded from Phase 83 multi-market monitoring
- Watchlist intelligence refreshed daily
- Coverage blocker refreshed daily (300394 preserved)
- Evidence memory written daily
- Multi-source capability matrix updated with daily monitoring field

## Safety Boundaries
- Daily monitoring is NOT a trading signal
- Strengthened does NOT mean confirmed
- Anomaly is NOT a buy/sell recommendation
- Blocked ticker is NOT hidden
- No valuation integration (Phase 85)
- No portfolio construction
