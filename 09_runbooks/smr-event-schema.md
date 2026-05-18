# SMR 事件层 Schema

**更新日期**：2026-04-16  
**适用范围**：`market_event`、事件日历、事件驱动研究、风险与轮动链  

---

## 1. 目标

事件层解决的是一个老问题：

- 原始来源很多
- 标题和正文都能抓
- 但系统还没有统一回答：
  - 这到底是什么事件
  - 对谁生效
  - 发生在什么时候
  - 重要性多高
  - 是事实层，还是解释层

所以事件层必须是：

- append-only（追加式）
- 来源可追溯
- 时间语义明确
- 事件类型有限而清楚

---

## 2. 核心对象

### 2.1 `input_source_registry`

定义输入源家族。

最重要字段：

- `source_key`
- `layer`
- `provider`
- `source_class`
- `entity_scope`
- `markets`
- `cadence`
- `freshness_sla_hours`
- `status`
- `enabled`
- `cost_level`
- `confidence_level`
- `owner_profile_id`

### 2.2 `market_event`

定义结构化后的事件对象。

最重要字段：

- `event_id`
- `source_key`
- `source_id`
- `event_family`
- `event_type`
- `entity_type`
- `entity_id`
- `title`
- `event_date`
- `publish_time`
- `market_effective_time`
- `importance`
- `status`
- `source_rel_path`
- `payload_json`

---

## 3. 时间语义

### 3.1 `event_date`

事件归属日期。

使用规则：

- 有明确公告 / 披露日期时，用公告日期
- 有明确事件发生日时，用事件发生日
- 都没有时，退回 `published_at` 的日期

### 3.2 `publish_time`

信息首次公开可见时间。

使用规则：

- 优先用来源里的 `published_at`
- 没有时可退回 `notice_date 00:00:00`
- 再没有时退回 `fetched_at`

### 3.3 `market_effective_time`

市场最早可交易生效时间。

使用规则：

- 公告 / 新闻发布时间在交易时段前，通常可视为当日开盘前生效
- 交易时段后披露，通常推到下一交易日开盘前
- 当前阶段允许先用启发式口径，后续再接交易日历精细化

---

## 4. 事件分层

### 4.1 `event_family`

当前统一为以下几大类：

- `announcement`
- `research`
- `news`
- `calendar`
- `capital_flow`
- `macro`
- `risk`

### 4.2 `event_type`

当前首批标准类型如下。

#### `announcement`

- `board_meeting_notice`
- `annual_results_announcement`
- `interim_results_announcement`
- `quarterly_report`
- `earnings_preannouncement`
- `dividend_notice`
- `equity_movement`
- `monthly_return`
- `announcement_general`

#### `research`

- `analyst_report`
- `analyst_report_table`
- `analyst_report_structured`

#### `news`

- `news_article`
- `news_digest_item`

#### `calendar`

- `earnings_calendar_item`
- `corp_action_calendar_item`

#### `capital_flow`

- `northbound_flow`
- `southbound_flow`
- `margin_balance_change`
- `short_interest_update`
- `block_trade_update`

---

## 5. 重要性口径

### `importance`

可选值：

- `high`
- `medium`
- `low`

当前启发式规则：

- 财报披露、董事会公告、业绩预告、分红、重大股本变动：`high`
- 研报正文、结构化研报、新闻正文：`medium`
- 搜索页摘要、月报、轻量动态：`low`

---

## 6. 事实层和解释层边界

事件层默认只记录**事实层**：

- 谁
- 在什么时候
- 披露了什么
- 属于什么事件类型

解释层不直接写入 `market_event` 主字段，而是进入：

- `payload_json.interpretation_candidates`
- `thesis delta`
- `wiki`
- `research update`

换句话说：

- `market_event` 先记录“发生了什么”
- Hermes 再回答“这意味着什么”

---

## 7. 和现有链路怎么接

### 7.1 OpenClaw-like（类 OpenClaw）负责

- 抓原始来源
- 清洗 frontmatter（前置元数据）
- 归一化时间
- 分类事件
- 落 `market_event`
- 产出事件快照

### 7.2 Hermes-like（类 Hermes）负责

- 事件重要性复核
- 相互矛盾信息的消解
- 事件对 thesis（投资逻辑）的影响
- 事件对组合和风控的影响解释

---

## 8. 当前阶段的落地边界

这次先做的是：

- 来源注册表
- 事件主表
- 从现有 `raw external`（外部原始来源）归一化出第一批 `announcement / research / news`

还没做的是：

- 北向 / 南向 / 两融 / 大宗交易正式抓取
- 真正的财报 / 解禁 / 分红日历
- 宏观时间序列表
- 统一交易日历精细化

所以当前正确理解是：

- 事件底座开始成型了
- 但机构级事件工厂还没建完
