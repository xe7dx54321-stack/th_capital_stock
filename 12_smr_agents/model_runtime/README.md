# SMR 模型运行时配置

这个目录是 SMR 进入模型态前的最小配置层。

当前状态：

- 已建立配置结构
- 已建立模型槽位
- 已建立任务路由
- 已建立 `OpenAI Responses API`（OpenAI 响应接口）shadow 执行器
- **默认不启用真实模型调用**

也就是说，现在这里的作用不是“已经开跑模型”，而是：

- 先把 provider（供应商）配置契约定下来
- 先把业务任务和模型槽位的映射定下来
- 先把 prompt pack（提示包）和任务包标准定下来

## 当前文件

- `model_profiles.json`
  - 模型供应商、环境变量契约、模型槽位
- `task_routes.json`
  - 不同 `entity_type` 应该走哪个模型槽位

## 当前安全模式

- `global_mode = disabled`

含义：

- 当前可以生成模型任务包
- 当前可以运行 shadow 执行器，但默认不应该直接发起真实模型调用

补充说明：

- `08_scripts/agents/run_model_shadow.py`
  - 会在执行时重读当前 `model_profiles.json + task_routes.json`
  - 只有在 `global_mode` 和 `route_global_mode` 都进入 `shadow/canary`，且 provider 已打开、认证信息可用时，才会真的发起 shadow 请求
  - 默认状态下依然只会生成 `compiled_prompt / request / response / result` 留痕文件，不会调用真实模型
  - 当前失败留痕里会额外写出 `provider_error_code / provider_error_reason`，便于区分是代码错误、鉴权错误，还是上游额度错误
- 运行时 override（覆盖层）补充：
  - 可通过 `SMR_MODEL_PROFILES_PATH`
  - 和 `SMR_TASK_ROUTES_PATH`
  - 临时覆盖运行时配置，而不改仓内正式文件
- `08_scripts/agents/run_openai_p1_shadow_canary.py`
  - 就是建立在 override（覆盖层）之上的受控灰度入口
  - 默认只放行：
    - `risk_monitor_snapshot`
    - `us_signal_snapshot`
    - `daily_reporting_snapshot`
  - 自动选样本时，会优先挑 source docs（源文档）更完整的已完成 handoff
  - 默认遇到额度耗尽类 `429` 会停止后续 handoff，避免继续撞上游
- `OpenAI` 补充：
  - 如果 shell（终端环境）里没有 `OPENAI_API_KEY / OPENAI_BASE_URL`
  - 运行时会尝试回退读取本机 `~/.codex/auth.json + ~/.codex/config.toml`
  - 这个 fallback（回退读取）只对 `openai` 生效
- 截至 2026-04-14
  - 真实 shadow 执行器已经实现 `OpenAI Responses API` 和 `Anthropic Messages API`（Anthropic 消息接口）
  - `OpenAI` 已经按本机 Codex 同口径打通：
    - 默认走 `/responses`
    - 读取 `text/event-stream`（事件流）返回
    - `validate_model_shadow_live_smoke.py --provider openai` 已通过
    - `run_openai_p1_shadow_canary.py` 实测结果：
      - 风控链 `http_status=200`
      - 日报链 `http_status=429 / provider_error_code=USAGE_LIMIT_EXCEEDED / provider_error_reason=DAILY_LIMIT_EXCEEDED`
  - `google` 槽位当前还没有真实 provider 调用适配层
  - `Anthropic` 运行时代码已接好，但当前 `api.ailinkmax.com/v1` 这组配置还没有验证通过
  - 第一批真实 shadow 仍然优先走 `OpenAI`

后续允许的模式：

- `disabled`
  - 完全不调用真实模型
- `shadow`
  - 调真实模型，但只生成候选
- `canary`
  - 小流量真实测试，仍需人工审核
- `active`
  - 仅允许低风险候选层使用，仍不代表自动裁决

## 启用前必须满足

1. 先补完模型任务包和 prompt pack（提示包）
2. 先完成风险显著分支和 US signal 显著分支样本验证
3. 先做影子模式对照评估
4. 先确认 provider 错误处理和熔断策略

## 永不放开的边界

- 不自动批准真实研究 draft
- 不自动导入正式 wiki
- 不自动写真实风险处置结果
- 不自动触发真实交易
