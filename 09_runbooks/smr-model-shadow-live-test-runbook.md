# SMR 第一轮真实 Shadow 测试运行手册

**更新日期**：2026-04-15  
**适用范围**：同行资本二级市场（SMR）模型影子测试准备  
**目标**：在**不碰真相层**的前提下，把第一轮真实模型 shadow（影子）测试安全落地

---

## 1. 先说结论

截至 2026-04-15，当前代码层已经具备：

- `OpenAI Responses API`（OpenAI 响应接口）真实 shadow 调用能力
- shadow 输入 / 输出 / 结果留痕能力
- 缺密钥、provider 未开、模式未开等门禁拦截能力
- 运行时 override（覆盖层）能力，可临时替换 `model_profiles.json / task_routes.json`
- 受控 `OpenAI P1 canary`（第一批灰度）脚本

但当前项目默认仍然是：

- `global_mode = disabled`
- `openai.enabled = false`
- 业务脚本所在 shell（终端环境）未显式注入 `OPENAI_API_KEY`

所以现在的真实状态是：

- **代码准备好了**
- **真实模型业务还没打开**

当前已知 smoke test（冒烟测试）结果：

- `OpenAI`
  - 运行时已经能从本机 `~/.codex/auth.json + ~/.codex/config.toml` 回退读取当前 Codex（代码助理）使用的第三方中转配置
  - 已确认当前机器上的 Codex 实际走的是 `POST https://aixj.vip/responses`
  - 已确认该第三方中转需要按 `Responses API`（响应接口）的 SSE（事件流）方式读取，而不是按普通 JSON 一次性响应读取
  - 已确认 `curl / requests` 方式可稳定返回 `200`，而旧版 `urllib` 在这个三方网关上会被 Cloudflare（云防护网关）打回 `502`
  - 运行时现已切到 `requests` 发起 `OpenAI Responses API`（OpenAI 响应接口）调用
  - 截至 2026-04-15，`python3 08_scripts/verification/validate_model_shadow_live_smoke.py --provider openai` 已返回 `shadow_call_succeeded / http_status=200`
- `Anthropic`
  - 运行时代码已经支持 `Messages API`（消息接口）
  - 截至 2026-04-15，使用 `ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN` 运行 `python3 08_scripts/verification/validate_model_shadow_live_smoke.py --provider anthropic` 已返回 `shadow_call_succeeded / http_status=200`

所以当前口径应当是：

- **运行时接线已完成**
- **OpenAI 已打通，可进入受控 shadow 测试**
- **Anthropic 已打通，可进入 `review_queue / wiki_draft` 最小业务试跑**

另外，2026-04-14 已做过一轮受控 canary（灰度）实测：

- `risk_monitor_snapshot`
  - `handoff_20260413232430246123`
  - 返回 `shadow_call_succeeded / http_status=200`
- `daily_reporting_snapshot`
  - `handoff_20260413222500028675`
  - 返回 `shadow_call_failed / http_status=429`
  - provider 错误细节是：
    - `provider_error_code = USAGE_LIMIT_EXCEEDED`
    - `provider_error_reason = DAILY_LIMIT_EXCEEDED`
- `us_signal_snapshot`
  - 当时没有可用的已完成 handoff，所以被安全跳过

同日后续补充结果：

- 主项目 `us_signal_snapshot`
  - 先补跑了 `ah_daily_bar.py --us-only`
  - 再跑 `earnings_monitor.py`
  - 生成新 handoff：`handoff_20260414102750756819`
  - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
- 受控风险沙盒 `risk_monitor_snapshot`
  - 在隔离 `SMR_ROOT` 沙盒中构造了带 `alert_file` 的风险样本
  - 生成 handoff：`handoff_20260414102324573516`
  - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
- 中间出现过一次 `502 Bad Gateway`
  - 口径更接近上游瞬时网关抖动
  - 同样本重试后已成功，不属于额度耗尽
- 运行时还顺手修复了一个 SSE（事件流）解析问题
  - 之前 `response_text.md` 会把正文重复拼接一遍
  - 现已修正
- 2026-04-15 继续补做了一轮放大量级真实业务 shadow
  - `strategy_watch_batch`
    - `handoff_20260415220229992049`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - `rotation_candidate_snapshot`
    - `handoff_20260415220230141393`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - `rotation_execution_plan_snapshot`
    - `handoff_20260415220230135653`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - `portfolio_action_memo_snapshot`
    - `handoff_20260415220230158925`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - `daily_reporting_snapshot`
    - `handoff_20260415220301064730`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - 这一轮说明 `strategy_watch / rotation / daily_report` 这几条放大量级业务链，已经不仅脚本产物能跑通，模型影子验证也已经跑通
- 2026-04-15 继续补做了第二轮扩面与治理试跑
  - `dynamic_pool_snapshot`
    - `handoff_20260413232410432088`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - `research_context_note`
    - `handoff_20260415220316638446`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - `review_queue`
    - `handoff_20260415225720698617`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - `wiki_draft`
    - `handoff_20260415225752441251`
    - 真实 shadow 结果：`shadow_call_succeeded / http_status=200`
  - 为了让 `review_queue` 真正具备可审核上下文，`build_model_task_packet.py` 已补 `review_queue -> export_rel_path` 的 source document（源文档）映射，模型现在能直接读到审核队列导出 Markdown（标记文档）

---

## 2. 第一轮真实 shadow 应该先测哪几条链

### 2.1 第一批

先测这 3 条：

- `risk_monitor_snapshot -> hermes_risk_curator`
- `us_signal_snapshot -> hermes_research_curator`
- `daily_reporting_snapshot -> hermes_reporting_editor`

原因：

- 都是候选层增强，不碰真相层
- 输入短、边界清晰、容易人工判断好坏
- 当前都走 `OpenAI` 槽位，和现有运行时代码一致

### 2.2 第二批

第一批稳定后，再测：

- `dynamic_pool_snapshot`
- `research_quality_snapshot`
- `portfolio_pnl_snapshot`
- `research_context_note`
- `risk_update_candidate`

### 2.3 暂时不要进第一批的链

- `trend_research_batch`
  - 当前路由到 `google / gemini-2.5-pro`
  - 当前真实 shadow 执行器还没有实现 `google` provider 调用适配层
  - 所以它现在不是第一批真实 shadow 对象
- `review_queue`
  - 治理风险更高
- `wiki_draft`
  - 容易越过审批边界

---

## 3. 真实 shadow 前的检查顺序

按这个顺序走，不要跳步：

1. 跑就绪度体检：
   - `python3 08_scripts/verification/report_model_shadow_readiness.py`
2. 跑无密钥前门禁验证：
   - `python3 08_scripts/verification/validate_model_shadow_openai_preflight.py`
3. 准备 `OpenAI` 认证
   - 优先显式注入 `OPENAI_API_KEY / OPENAI_BASE_URL`
   - 如果本机就是通过 Codex 第三方中转在跑，且 `~/.codex/auth.json + ~/.codex/config.toml` 可用，也可以先用 fallback（回退读取）测试
4. 先只在沙盒或单样本环境把：
   - `model_profiles.json -> global_mode = shadow`
   - `model_profiles.json -> providers.openai.enabled = true`
   - `task_routes.json -> global_mode = shadow`
5. 只跑单链路样本，不要一上来全量
6. 人工检查 `response_text.md`
7. 对照候选层原文本，确认模型没有胡编
8. 连续稳定后，再扩大到第二批链路

---

## 4. 真实 shadow 的最小执行流程

### 4.1 准备上游样本

先用现有脚本跑出真实 handoff 和 model task packet（模型任务包）。

例如风险链：

```bash
python3 08_scripts/risk_engine/monitor.py
python3 08_scripts/agents/run_agent_control_loop.py --date 2026-04-14 --research-governance-mode skip
python3 08_scripts/agents/build_model_task_packet.py --handoff-id <handoff_id>
```

### 4.2 发起真实 shadow

```bash
python3 08_scripts/agents/run_model_shadow.py --handoff-id <handoff_id>
```

### 4.3 检查产物

重点看下面 3 个文件：

- `shadow_runs/*__response.json`
- `shadow_runs/*__response_text.md`
- `shadow_runs/*__result.md`

判断标准：

- `result.md` 里是 `shadow_call_succeeded`
- `response_text.md` 里有清晰中文输出
- 输出区分事实、解释、建议动作、不确定性
- 没有越权指令
- 没有把猜测写成事实

### 4.4 更推荐的受控执行入口：P1 canary 脚本

如果不是在排某一条明确 handoff（交接单），更推荐直接用这条脚本：

```bash
python3 08_scripts/agents/run_openai_p1_shadow_canary.py --dry-run
python3 08_scripts/agents/run_openai_p1_shadow_canary.py
```

它和直接手改运行时配置相比，优势是：

- 会临时复制一份运行时配置，不改仓内正式 `model_profiles.json / task_routes.json`
- 会强制只打开 `openai`
- 会强制 `global_mode = shadow`
- 会只放行 P1 三条链：
  - `risk_monitor_snapshot`
  - `us_signal_snapshot`
  - `daily_reporting_snapshot`
- 自动挑样本时，会优先选 source documents（源文档）更完整的已完成 handoff，而不是机械只选最新一条
- 其余所有 `entity_type` 都会被改成 `disabled_canary`
- 默认遇到明确的额度耗尽类 `429` 会停止后续 handoff，避免继续撞上游额度

如果你明知道上游已经恢复，仍想继续试完后面的 handoff，才显式加：

```bash
python3 08_scripts/agents/run_openai_p1_shadow_canary.py --continue-on-quota-exhausted
```

---

## 5. 第一轮建议模型口径

### 5.1 建议先接的模型

- `reasoning_primary -> gpt-5.4`
- `reasoning_batch -> gpt-5.4`

原因：

- 当前运行时已经直接实现 `OpenAI Responses API`
- 第一轮目标是打通最短路径，不是多 provider 炫技

### 5.2 暂缓的模型

- `gemini-2.5-pro`
  - 等 `google` provider 适配层补完，再进真实 shadow
- `claude-opus-4-6`
  - 适合 second opinion（第二意见）和治理复核，不适合作为第一轮打通对象

---

## 6. 每次真实 shadow 后必须检查什么

每次都要看：

- `execution_status`
- `http_status`
- `response_id`
- `output_text_chars`
- `error`
- `provider_error_code`
- `provider_error_reason`
- `route_drift`

如果出现下面任一情况，就不能继续扩大范围：

- 输出明显虚构事实
- 输出口吻变成投资建议
- 输出直接越权要求改真相层
- 同一类样本波动很大
- 连续出现 provider 错误
- 出现 `429 + USAGE_LIMIT_EXCEEDED + DAILY_LIMIT_EXCEEDED`
  - 这类错误优先按“上游额度耗尽”处理
  - 同一天内不要机械重试

---

## 7. 2026-04-14 这轮 canary 的实测结论

### 7.1 成功样本

- 风控链：
  - `handoff_20260413232430246123`
  - `entity_type = risk_monitor_snapshot`
  - `http_status = 200`
  - 已生成：
    - `12_smr_agents/workspaces/hermes_risk_curator/shadow_runs/handoff_20260413232430246123__response.json`
    - `12_smr_agents/workspaces/hermes_risk_curator/shadow_runs/handoff_20260413232430246123__response_text.md`

### 7.2 失败样本

- 日报链：
  - `handoff_20260413222500028675`
  - `entity_type = daily_reporting_snapshot`
  - `http_status = 429`
  - `provider_error_code = USAGE_LIMIT_EXCEEDED`
  - `provider_error_reason = DAILY_LIMIT_EXCEEDED`
  - 已生成：
    - `12_smr_agents/workspaces/hermes_reporting_editor/shadow_runs/handoff_20260413222500028675__response.json`

### 7.3 这轮实测真正说明了什么

- 说明 `OpenAI Responses API + SSE` 这条真实调用链已经打通
- 说明当前受控 canary 门禁有效，默认配置并没有被误打开
- 说明上游额度是实际业务测试中的硬约束，不能只看代码通不通
- 还不能说明“模型业务质量已经稳定”
  - 因为风控那条成功样本的 source documents（源文档）不完整，更多是在验证链路通，不是在验证高质量解释

### 7.4 第二轮补充说明了什么

- 说明主项目里已经可以产出真实的 `us_signal_snapshot -> handoff -> model shadow`
- 说明在主库没有真实风险样本时，可以用隔离 `SMR_ROOT` 沙盒构造受控风险样本，而不污染正式真相库
- 说明 `source_documents` 完整时，模型输出的信息密度明显高于“只有元数据、没有源文档”的旧样本
- 说明当前上游偶发 `502` 需要按“可重试型网关抖动”处理，不能和额度型 `429` 混为一谈

---

## 8. 回滚原则

如果发现异常，立刻回滚到：

- `model_profiles.json -> global_mode = disabled`
- `model_profiles.json -> providers.openai.enabled = false`
- `task_routes.json -> global_mode = disabled`

并停止真实 shadow，只保留：

- `build_model_task_packet.py`
- `run_model_shadow.py` 的留痕能力

也就是说，回滚目标不是删代码，而是：

- **把模型重新打回只留痕、不实调的状态**

---

## 9. 当前最现实的下一步

按 2026-04-14 当前工程状态，最现实的下一步不是直接全业务开模型，而是：

1. 先跑 `report_model_shadow_readiness.py`
2. 如果要做稳定业务化，仍建议把 `OPENAI_API_KEY / OPENAI_BASE_URL` 显式配置到业务线 shell 环境
3. 先准备更高质量的 P1 样本
   - 优先补带完整 source documents（源文档）的 `risk_monitor_snapshot`
   - 再补一条新的 `us_signal_snapshot`
4. 优先用 `run_openai_p1_shadow_canary.py --dry-run` 做计划确认
5. 等上游额度恢复后，再重新跑 P1 canary
6. 连续稳定后，再决定要不要扩到第二批
7. 等公司给到 `Anthropic` 的正确网关接法后，再补第二 provider 的 live smoke

---

## 10. 记住这条底线

这套系统里，模型永远只是：

- 解释器
- 压缩器
- 治理建议器

它不是：

- 真相裁判
- 风控裁判
- 审批裁判
- 交易裁判
