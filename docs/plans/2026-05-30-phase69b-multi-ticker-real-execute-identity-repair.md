# Phase 69b: Multi-ticker Real Execute & Identity Repair v1

## 日期
2026-05-30

## 背景
Phase 69 完成了多标的披露管线的框架泛化，但存在口径冲突：
- 688041.SH 被标记 pass 但注明 metadata/PDF/deep evidence 待真实 execute 验证
- 300394.SZ 被 blocked 但 blocker 不够具体

Phase 69b 目标是将 Phase 69 从配置泛化压实到真实执行泛化。

## 覆盖标的
1. **300308.SZ** — baseline regression，确保不回退
2. **688041.SH** — 第二交易所/科创板 real execute 验证
3. **300394.SZ** — identity repair + real execute 验证

## 施工内容

### Lib
- `smr_phase69b_cninfo_identity_repair.py` — 300394.SZ CNINFO identity 修复

### Jobs
- `run_phase69b_688041_real_execute.py` — 688041 real execute
- `run_phase69b_300394_real_execute.py` — 300394 real execute
- `run_phase69b_write_real_execute_evidence_memory.py` — evidence memory 写入
- `run_phase69b_multi_ticker_real_execute_and_identity_repair.py` — runner

### Reporting
- 688041/300394 real execute reports
- 300394 identity repair report
- real execute capability matrix
- generic vs ticker-specific report
- evidence memory update report
- research packet + internal brief
- brief quality lint + dashboard

### Tests
- 11 test files covering all modules

## 核心约束
- no_pass_without_execute=true
- mock/fixture=false, raw/OCR=false
- pending/order/trade=0/0/0
- 不复用 300308 org_id
- 不硬套 AI 光模块变量
- 不输出交易建议
