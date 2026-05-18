# SMR 从脚本态到模型态的开发总计划

**更新日期**：2026-04-14  
**适用范围**：同行资本二级市场（SMR）当前目录  
**文档定位**：这是 2026-04-14 之后的最新总控文档，用来统一回答 4 件事：

- 当前到底哪些东西已经真的跑起来了
- 哪些链路必须继续由脚本做真相层
- 哪些核心业务环节应该逐步接入模型
- 什么时候才适合把真实模型接进来做业务测试

---

## 1. 先给结论

SMR 现在已经有一套能真实运行的本地工作流，但它还是**脚本态系统**，不是**模型态系统**。

当前已经真实跑起来的是：

- `Python + SQLite + Markdown + task registry + handoff + dispatch`
- 一套本地的 `OpenClaw-like`（类 OpenClaw）执行层
- 一套本地的 `Hermes-like`（类 Hermes）知识治理层

当前**还没有**真的跑起来的是：

- 原版 `OpenClaw` runtime（运行时）
- 原版 `Hermes` runtime（运行时）
- 默认开启状态下的真实模型 provider（模型供应商）业务接入
- 默认开启状态下的自动化真实模型业务调用

所以，下一阶段的正确路线不是“立刻把模型接进所有地方”，而是：

1. 先把“脚本真相层”和“模型辅助层”的边界固定。
2. 先把模型运行时配置、任务包、prompt pack（提示包）和安全门禁补齐。
3. 再让模型以 `shadow mode`（影子模式）进入，只生成候选，不改真相层。
4. 等影子模式评估稳定后，再让少数高价值环节进入人工审核下的真实业务测试。

一句话说：

- **真相层先继续靠脚本**
- **解释层、压缩层、治理建议层再逐步接模型**

---

## 2. 当前真实状态复盘

### 2.1 已经落地并真实可跑的部分

- 数据底座：
  - SQLite 数据库
  - A/H/US 行情表
  - 因子表
  - 股票池表
  - 风险预警表
- 执行链路：
  - 数据采集
  - 因子计算
  - 趋势研究批量生成
  - 动态池重建
  - 研究质量快照
  - PnL（盈亏）快照
  - 风险监控快照
  - 日报快照
- 治理与状态层：
  - `task_registry_entry`
  - `source_manifest`
  - `review_queue`
  - `wiki_draft`
  - `wiki import`
- 双 lane（双通道）最小运行时：
  - `12_smr_agents/profiles/`
  - `12_smr_agents/handoffs/`
  - `12_smr_agents/workspaces/`
- 已跑通的闭环：
  - `daily_reporting_snapshot -> hermes_reporting_editor -> dispatch_update_candidate`
  - `dynamic_pool_snapshot -> hermes_research_curator -> research_context_note -> hermes_reporting_editor -> dispatch_sync_candidate`
  - `research_quality_snapshot -> hermes_research_curator -> research_context_note -> hermes_reporting_editor -> dispatch_sync_candidate`
  - `risk_monitor_snapshot -> hermes_risk_curator -> risk_update_candidate -> hermes_reporting_editor -> dispatch_sync_candidate`
  - `trend_research_batch -> hermes_research_curator -> research_context_note -> hermes_reporting_editor -> dispatch_sync_candidate`

### 2.2 现在还没真的落地的部分

- 真实模型 provider 的正式启用
- 生产环境 provider 级 API key（密钥）注入
- 多 provider（多供应商）正式调用实现
- 影子模式下的样本评估基线
- 真实“模型辅助业务测试”

补充说明：

- `OpenAI Responses API`（OpenAI 响应接口）的 shadow 执行代码路径已经落地
- 当前仍然默认关闭，不会自动调用
- 只有在 `global_mode/route_global_mode` 打开到 `shadow/canary`，并且 provider 与 API key（密钥）都满足时，才会发真实 shadow 请求

### 2.3 上游仓库的真实角色

当前这两个仓库已经拉到本地，但它们还是**参考源码区**，不是当前生产运行时：

- `/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/12_agent_references/openclaw`
- `/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/12_agent_references/hermes-agent`

它们当前的作用是：

- 学架构
- 学 session / workspace / delegation（委派）/ memory（记忆）/ skills（技能）设计
- 学 provider / routing / agent contract（代理契约）分层

它们当前**没有**直接被本地这条业务链 import（导入）或运行。

---

## 3. 哪些流程必须继续由脚本驱动

下面这些环节必须继续由脚本作为真相层，模型不能直接替代。

### 3.1 数据真相层

- 行情采集
- 财务和基本面抓取
- 因子计算
- US linkage（美股联动）数值计算
- 股票池重建
- 推荐池门禁
- 组合 PnL 计算
- 风险规则判断

原因很简单：

- 这些环节要求可重复、可审计、可回放
- 结果必须 deterministic（确定性）
- 不能因为 prompt（提示词）变化而改变真相结果

### 3.2 状态真相层

- `task_registry_entry` 写入
- `handoff` 创建 / 领取 / 完成 / 拒绝
- `review_queue` 状态流转
- `wiki_draft` 状态流转
- `dispatch_board` 正式写回
- `risk_alert` 真正入库
- `entry.py` 是否允许开仓

原因：

- 这些都是“系统裁决动作”
- 裁决动作必须由脚本规则和人工审批共同保证
- 模型只能给候选，不能直接当裁判

### 3.3 永远不应该让模型自动做最终裁决的环节

- 自动批准真实研究 draft
- 自动导入正式 wiki 知识页
- 自动确认真实风险预警已处理
- 自动修改真实仓位
- 自动触发真实交易动作

这里的原则不变：

- **模型只能建议**
- **脚本才能执行**
- **高风险动作必须人工确认**

---

## 4. 哪些核心业务环节应该逐步接入模型

模型真正应该负责的是“解释、压缩、归纳、治理建议、跨源整合”。

### 4.1 第一优先级：已经有稳定上游真相、但解释还靠模板的环节

这些最适合先接模型：

- `trend_research_batch`
  - 模型做批量研究上下文压缩
  - 从一批研究卡里提炼真正重要的主线
- `dynamic_pool_snapshot`
  - 模型解释今天为什么某些票升降级
  - 不是决定升降级，而是解释升降级
- `research_quality_snapshot`
  - 模型归纳研究缺口
  - 把长期重复缺口沉淀成 checklist（清单）或 playbook（操作手册）
- `us_signal_snapshot`
  - 模型解释美股信号对 A/H 主线到底有没有实质影响
- `risk_monitor_snapshot`
  - 模型把预警压缩成真正可执行的风险观察动作
- `daily_reporting_snapshot`
  - 模型把日报快照补成更好的调度候选

### 4.2 第二优先级：高价值治理环节

- `review_queue`
  - 模型帮忙做 triage（分诊）
  - 标记优先审核对象
  - 给 reason code（原因码）建议
- `wiki_draft`
  - 模型帮忙补结构、补摘要、补交叉链接
  - 但不自动批准
- `risk_update_candidate`
  - 模型把风险候选块压缩成适合调度板的表达
- `research_context_note`
  - 模型把研究解释草稿并入日报和调度板口径

### 4.3 第三优先级：复盘和知识沉淀

- 把重复出现的风险模式沉淀为 risk case（风险案例）
- 把研究卡里的有效共识提炼为 thesis page（论点页）
- 把日报和事件序列沉淀为 timeline（时间线）
- 把成功和失败样本沉淀为入池 / 升级 / 降级规则说明

---

## 5. 建议接什么样的模型

这部分的原则是：

- 先确定**模型槽位**
- 再把具体模型名映射进去
- 不要让业务代码直接写死某一家 provider

### 5.1 必须具备的模型特质

不管最后选哪家，SMR 真正需要的模型至少要满足下面这些能力：

- 强结构化输出
  - 最好能稳定输出 JSON（结构化数据）
- 强工具调用
  - 后续要接文件、网页、数据库摘要、registry 上下文
- 稳定长上下文
  - `trend_research_batch`、review 包、dispatch 包都很容易变长
- 中文表达稳定
  - 这里的正式产物主要是中文
- 金融研究表达克制
  - 不能满嘴“强烈推荐”“必须买”
- 版本可 pin（固定版本）
  - 不能长期依赖 `latest`（最新别名）
- 成本分层明确
  - 高价值任务用强模型
  - 批量 triage（分诊）用便宜模型

### 5.2 当前建议的模型槽位

截至 **2026-04-14**，我建议先按下面 4 个槽位设计，而不是先做多供应商大杂烩。

#### 槽位 A：`reasoning_primary`

用途：

- 高价值研究压缩
- 日报增强
- 风险解释
- 复杂治理建议

建议首选：

- `gpt-5.4`

建议理由：

- 适合高价值、复杂、多步推理任务
- 后续也方便和当前 Codex / OpenAI 系技术栈衔接

#### 槽位 B：`reasoning_batch`

用途：

- 批量上下文整理
- 调度同步块补写
- 研究质量缺口归纳

建议首选：

- `gpt-5.4-mini`

建议理由：

- 成本和延迟更适合中等规模批处理
- 适合“量比较大，但每条不是最高风险”的任务

#### 槽位 C：`long_context_secondary`

用途：

- 很长的研究包
- 很长的 review 包
- 长文档交叉整合

建议首选：

- `gemini-2.5-pro`

建议理由：

- 长上下文能力非常适合做大包阅读和交叉对照
- 可以作为 OpenAI 主栈之外的长上下文补充

#### 槽位 D：`review_second_opinion`

用途：

- review queue（审核队列）二次意见
- wiki draft 审核建议
- 争议性内容 second pass（第二轮复核）

建议首选：

- `claude-sonnet-4-6`

建议理由：

- 适合作为“第二视角 reviewer（审阅者）”
- 不建议一开始就把它接进所有主链，而是先用于治理复核

### 5.3 推荐的接入策略

不要一步上 3 家。

更稳的顺序是：

1. **第一阶段只接 1 家主 provider**
   - 建议先接 OpenAI
2. **第二阶段再补 1 个长上下文 provider**
   - 建议 Gemini 只承担长包阅读
3. **第三阶段再补 1 个 second-opinion provider**
   - 建议 Claude 只承担治理复核

这样做的原因是：

- provider 越多，调试和成本控制越难
- 先把一条链打穿，比一开始全栈都接更稳

---

## 6. 到什么阶段才适合接真实模型

### 6.1 现在还不适合直接上生产模型的原因

当前还缺：

- 模型配置目录
- prompt pack（提示包）
- 模型任务包
- 影子模式评估
- 质量对照基线
- provider 错误处理和熔断

所以现在直接把模型接进生产链，风险太高。

### 6.2 真正适合接真实模型前，至少要满足 5 个门槛

#### 门槛 1：脚本真相层稳定

要求：

- 股票池、风控、日报、registry、dispatch 主链稳定
- 关键字段口径不再来回变

当前状态：

- **基本满足**

#### 门槛 2：模型任务包标准化

要求：

- 每次模型调用前，都能先生成结构化任务包
- 任务包里要明确：
  - 来源对象
  - 上游文件
  - 输出契约
  - 安全边界

当前状态：

- **本轮开始补**

#### 门槛 3：prompt pack（提示包）标准化

要求：

- 不同 profile 有自己的固定系统提示
- 不再靠一次性 prompt 临时拼接

当前状态：

- **本轮开始补**

#### 门槛 4：影子模式评估

要求：

- 模型只生成候选，不写正式真相层
- 要能比较：
  - 模板输出
  - 模型输出
  - 人工最终采用结果

当前状态：

- **还没开始**

#### 门槛 5：高风险动作仍然保持人工确认

要求：

- 模型不能直接批准真实 draft
- 模型不能直接写正式 wiki
- 模型不能直接改仓位和风控真相

当前状态：

- **已经满足，且必须继续保持**

### 6.3 我的建议时间点

如果按现在的施工顺序，**最适合开始真实模型业务测试的时点**是：

- 先把模型任务包和 prompt pack（提示包）做出来
- 再完成 `risk_alert` 显著分支和 `us_signal` 显著分支的样本验证
- 然后让模型先进入下面 3 条链的 `shadow mode`（影子模式）：
  - `risk_monitor_snapshot -> risk_update_candidate`
  - `us_signal_snapshot -> research_context_note`
  - `daily_reporting_snapshot -> dispatch_update_candidate`

只有这 3 条影子链连续稳定后，才适合做第一轮真实业务测试。

补充说明：

- `trend_research_batch` 当前仍然绑定 `google / gemini-2.5-pro`
- 但截至 2026-04-14，真实 shadow 执行器先只实现了 `OpenAI Responses API`（OpenAI 响应接口）
- 所以 `trend_research_batch` 不是第一批真实 shadow 对象
- 它要么等后续补 `google` provider 适配层，要么临时改路由后再测

---

## 7. 新的阶段顺序

### P0：把系统从“纯脚本态”推进到“可接模型态”

目标：

- 不做真实模型调用
- 先把模型接入底座搭好

这阶段要完成：

- 新总控文档
- `model_runtime` 配置目录
- prompt pack（提示包）
- 模型任务包生成器
- 风险显著分支沙盒验证
- US signal 显著分支样本验证

### P1：影子模式

目标：

- 真实调用模型
- 但只写候选，不改正式真相层

这阶段要完成：

- provider 接入
- API key 环境变量契约
- provider 熔断和重试
- 结果对照评估
- 模型输出打分

### P2：人工审核下的真实业务测试

目标：

- 模型输出进入真实工作流
- 但仍然必须人工确认

先开放的链路：

- `trend_research_batch`
- `risk_monitor_snapshot`
- `daily_reporting_snapshot`

暂不开放：

- `review_queue` 自动批准
- `wiki_draft` 自动导入
- 任何真实交易动作

### P3：扩大模型作用范围

目标：

- 把模型从“解释器”升级成“治理助手”

这阶段再考虑：

- review queue 分诊
- wiki draft 结构补写
- risk case / playbook 自动候选
- decision / timeline 自动草稿

---

## 8. 这轮文档落完后，马上要做什么

按新的顺序，文档之后的第一步不是直接连真实模型，而是：

1. 建 `12_smr_agents/model_runtime/`
2. 建 prompt pack（提示包）
3. 建模型任务包生成脚本
4. 让已有 handoff 能先产出标准化模型任务包
5. 保持 `global_mode=disabled`（全局禁用真实模型调用）

这一步做完，系统就从“纯脚本系统”升级成了“可安全接模型的脚手架系统”。

---

## 9. 这份文档对应的控制原则

最后把控制原则写死：

- 真相层优先脚本
- 解释层优先模型
- 治理层必须人工兜底
- 高风险动作永不自动化
- 先影子模式，再真实测试
- 先单 provider 打穿，再考虑多 provider

如果后面要改路线，也必须先回答下面这 3 个问题：

1. 这次改动是改真相层，还是改解释层？
2. 这次改动是否会扩大模型的裁决权？
3. 这次改动是否破坏了“候选层和正式层分离”？

只要这 3 个问题没答清楚，就不应该继续往前接模型。
