
# Phase 75: Fallback HTML Real Execute & Evidence Breakthrough v1

## 目标

- 真实执行 IRM/SSE/Hygon/seeded URL HTML parser
- 获取 fallback usable text
- 写入 evidence memory
- 推进 fallback_texts_usable 和 fallback_deep_evidence_created 从 0 到 >0

## 产出

- Config: 1
- Lib: 2
- Jobs: 7 (含 runner)
- Reporting: 14
- Tests: 15
- 总计: ~39 文件

## 验收

- py_compile: 0 错误
- unittest: 通过
- Phase 74 未回退
- fallback_texts_usable > 0
- fallback_deep_evidence_created > 0
- tickers_with_fallback_gain >= 1
- mock/fixture=false
- pending/order/trade=0
