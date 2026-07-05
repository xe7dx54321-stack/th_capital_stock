# SMR-D0 opc-foundation 信息流入 Dashboard 设计

## 1. 设计原则

### 核心边界
- **Foundation 只提供证据和来源结构**，不提供投资判断
- **th_capital_stock 负责投资解释和研究判断**
- **Dashboard 负责呈现**，不做业务逻辑

### 严格禁止
- Foundation 输出 target price
- Foundation 输出买卖建议
- Foundation 输出组合建议
- Foundation 输出投资评级
- Foundation 直接控制 Dashboard 展示逻辑

### 数据流方向
```
opc-foundation (证据和来源)
    ↓
th_capital_stock 接收层 (格式转换 + 映射)
    ↓
th_capital_stock 业务层 (投资解释 + 研究判断)
    ↓
Dashboard 呈现层 (投研工作台展示)
```

## 2. Foundation 输出类型

### 2.1 EvidencePacket（证据包）
- **定义**：围绕某个主题/公司的一组结构化证据
- **包含**：
  - 证据 ID
  - 证据类型（公告/研报/新闻/IR/电话会等）
  - 证据摘要
  - 置信度（confidence）
  - 时间戳
  - 时间戳可信度
  - 关联实体（公司/行业/主题）
  - 原始来源链接
  - cannot_conclude 标记（如适用）
  - 提取的关键信息点

### 2.2 SourceObservation（原始观察）
- **定义**：从单一来源获取的原始观察记录
- **包含**：
  - 来源 ID
  - 来源类型
  - 来源 URL
  - 抓取时间
  - 原始内容摘要
  - 提取状态
  - 质量评分

### 2.3 RoutePlan（研究路径计划）
- **定义**：系统建议的研究路径/证据获取计划
- **包含**：
  - 研究主题
  - 目标实体
  - 建议步骤
  - 缺失证据清单
  - 优先级
  - 预计工作量

### 2.4 ExtractedDocument（提取后的文档）
- **定义**：从原始文档中结构化提取的内容
- **包含**：
  - 文档 ID
  - 文档类型
  - 来源
  - 提取的章节/表格/数据点
  - 提取质量评分
  - 原文引用

### 2.5 SourceHealth（源健康状态）
- **定义**：各数据源的健康状态
- **包含**：
  - 数据源 ID
  - 数据源名称
  - 最后成功抓取时间
  - 状态（正常/降级/失败）
  - 错误率
  - 最近错误信息

## 3. th_capital_stock 接收层

### 3.1 接收层职责
- 接收 Foundation 输出的数据
- 格式转换（Foundation 格式 → th_capital_stock 内部格式）
- 实体映射（Foundation 实体 ID → th_capital_stock 实体 ID）
- 去重和合并
- 写入 SQLite 快照表
- 不做任何投资判断

### 3.2 新增快照实体类型（建议）
| 实体类型 | 来源 | 说明 |
|---|---|---|
| `foundation_evidence_packet_snapshot` | EvidencePacket | Foundation 证据包快照 |
| `foundation_source_observation_snapshot` | SourceObservation | Foundation 原始观察快照 |
| `foundation_route_plan_snapshot` | RoutePlan | Foundation 研究路径计划 |
| `foundation_extracted_doc_snapshot` | ExtractedDocument | Foundation 提取文档 |
| `foundation_source_health_snapshot` | SourceHealth | Foundation 源健康状态 |

### 3.3 现有快照实体的增强
| 现有实体 | 增强方式 | 说明 |
|---|---|---|
| `opportunity_radar_snapshot` | 增加 Foundation 证据引用 | 机会雷达可引用 Foundation 证据 |
| `investment_evidence_pack_snapshot` | 合并 Foundation 证据 | 投资证据包包含 Foundation 和内部证据 |
| `data_freshness_snapshot` | 增加 Foundation 源健康 | 数据健康包含 Foundation 源状态 |
| `market_event_snapshot` | 增加 Foundation 事件 | 事件流包含 Foundation 事件 |

## 4. EvidencePacket 映射关系

### 4.1 映射到 Dashboard 页面

| Dashboard 页面 | 模块 | 使用 Foundation 数据的方式 |
|---|---|---|
| 今日总览 | 今日最重要变化 | 新 EvidencePacket 触发"今日变化" |
| 今日总览 | 公司重大动态 | 按公司聚合的新 EvidencePacket |
| 今日总览 | 行业主题变化 | 按主题聚合的新 EvidencePacket |
| 覆盖池 | 证据完整度 | EvidencePacket 数量和质量 |
| 信号流 | 证据时间线 | EvidencePacket 是信号流的主要数据源 |
| 信号流 | 证据强度 | EvidencePacket.confidence |
| 信号流 | cannot_conclude 标记 | EvidencePacket.cannot_conclude |
| 研究队列 | 已有证据 | EvidencePacket 按主题聚合 |
| 研究队列 | 缺失证据 | EvidencePacket 缺口分析 |

### 4.2 字段映射表

| EvidencePacket 字段 | th_capital_stock 内部字段 | Dashboard 展示字段 |
|---|---|---|
| evidence_id | foundation_evidence_id | 证据 ID（技术向，默认隐藏） |
| evidence_type | evidence_type | 来源类型标签 |
| summary | evidence_summary | 证据摘要 |
| confidence | evidence_strength | 证据强度（强/中/弱） |
| timestamp | event_time | 时间戳 |
| timestamp_confidence | timestamp_confidence | 时间戳可信度 |
| entities | related_entities | 关联公司/行业标签 |
| source_url | source_rel_path | 原始来源入口 |
| cannot_conclude | cannot_conclude | cannot_conclude 标记 |
| key_points | key_points | 关键信息点（详情抽屉） |

### 4.3 证据合并策略
- **内部证据 + Foundation 证据** 合并展示
- **去重规则**：同一来源同一事件的证据只展示一次
- **优先级**：高置信度证据优先展示
- **标记区分**：Foundation 来源的证据有特殊标记，与内部证据区分

## 5. SourceObservation 映射关系

### 5.1 映射到 Dashboard 页面

| Dashboard 页面 | 模块 | 使用 Foundation 数据的方式 |
|---|---|---|
| 信号流 | 原始来源入口 | SourceObservation 提供原始观察详情 |
| 信号流 | 证据详情抽屉 | 展示原始观察数据 |
| 数据健康 | 数据源状态 | SourceObservation 反映源健康度 |
| 覆盖池 | 证据完整度 | SourceObservation 数量反映覆盖程度 |

### 5.2 字段映射表

| SourceObservation 字段 | th_capital_stock 内部字段 | Dashboard 展示字段 |
|---|---|---|
| source_id | source_id | 来源 ID（技术向） |
| source_type | source_type | 来源类型 |
| source_url | source_url | 原始链接 |
| fetched_at | fetched_at | 抓取时间 |
| content_summary | content_summary | 内容摘要 |
| extraction_status | extraction_status | 提取状态 |
| quality_score | quality_score | 质量评分 |

## 6. RoutePlan 映射关系

### 6.1 映射到 Dashboard 页面

| Dashboard 页面 | 模块 | 使用 Foundation 数据的方式 |
|---|---|---|
| 研究队列 | 待深挖主题 | RoutePlan 转化为研究队列条目 |
| 研究队列 | 下一步建议动作 | RoutePlan.steps |
| 研究队列 | 缺失证据 | RoutePlan.missing_evidence |
| 研究队列 | 研究优先级 | RoutePlan.priority |

### 6.2 字段映射表

| RoutePlan 字段 | th_capital_stock 内部字段 | Dashboard 展示字段 |
|---|---|---|
| research_topic | research_topic | 研究主题 |
| target_entity | target_entity | 关联公司/行业 |
| suggested_steps | suggested_steps | 下一步建议动作 |
| missing_evidence | missing_evidence | 缺失证据清单 |
| priority | priority | 研究优先级 |
| estimated_effort | estimated_effort | 预计工作量（可选展示） |

### 6.3 重要：只做研究建议，不做投资建议
- RoutePlan 的 **priority 是研究优先级**，不是投资优先级
- RoutePlan 的 **suggested_steps 是研究动作**，不是交易动作
- Dashboard 展示时必须明确标注"系统研究建议，非投资建议"

## 7. Dashboard 展示位置

### 7.1 各页面 Foundation 数据占比预估

| 页面 | 内部数据占比 | Foundation 数据占比 | 说明 |
|---|---|---|---|
| 今日总览 | 70% | 30% | Foundation 触发变化，但汇总逻辑在内层 |
| 覆盖池 | 60% | 40% | 证据完整度大量依赖 Foundation |
| 信号流 | 40% | 60% | 信号流主要数据源是 Foundation |
| 研究队列 | 50% | 50% | 研究建议来自 Foundation 和内部共同判断 |
| 数据健康 | 80% | 20% | 内部 pipeline 健康为主，Foundation 源健康为辅 |

### 7.2 Foundation 数据的视觉区分
- **标记方式**：Foundation 来源的证据有一个小的 "F" 标记或特殊边框
- **颜色区分**：Foundation 证据用浅蓝色调，内部证据用中性色调
- **详情说明**：点击展开后，明确标注数据来源是 Foundation 还是内部 pipeline

### 7.3 降级策略
- **Foundation 不可用时**：
  - 信号流只展示内部证据
  - 研究队列只展示内部生成的
  - 数据健康页显示 Foundation 连接断开
  - 其他页面不受影响或影响较小
- **降级标记**：明显位置标注"Foundation 数据暂不可用"

## 8. 不允许 Foundation 输出的内容

### 8.1 严格禁止清单
- ❌ Target price / 目标价
- ❌ Buy/Sell/Hold 评级
- ❌ 仓位建议
- ❌ 组合配置建议
- ❌ 买卖时点建议
- ❌ 止损/止盈点位
- ❌ 投资收益率预测
- ❌ 风险评级（投资意义上的）

### 8.2 允许输出的内容
- ✅ 证据和事实
- ✅ 证据置信度
- ✅ 证据缺口识别
- ✅ 研究路径建议
- ✅ 数据源健康状态
- ✅ 文档结构化提取
- ✅ 实体关系图谱
- ✅ 时间线整理

### 8.3 边界模糊地带的处理原则
- **"研究优先级" vs "投资优先级"**：Foundation 可以给研究优先级，但不能给投资优先级
- **"风险提示" vs "投资风险"**：Foundation 可以提示数据风险、证据风险，但不能提示投资风险
- **"建议关注" vs "建议买入"**：Foundation 可以建议"值得研究关注"，但不能建议"值得买入"

## 9. 后续 SMR-D2/D3 建议

### 9.1 SMR-D1（下一步）：效果图设计
- 基于本蓝图设计 5 个页面的高保真效果图
- 确认视觉风格和交互细节
- 不写代码

### 9.2 SMR-D2：Dashboard 重构（内部数据）
- 用内部现有数据实现新 Dashboard 的 5 个页面
- 不接入 Foundation
- 重点：信息架构重构、投研语言、证据追溯
- 技术栈决策：继续用 Python HTTP + HTML，还是换 Streamlit / 其他

### 9.3 SMR-D3：Foundation 接入
- 实现 Foundation 接收层
- 新增 Foundation 相关快照表
- 信号流接入 Foundation EvidencePacket
- 研究队列接入 Foundation RoutePlan
- 数据健康接入 Foundation SourceHealth
- 联调和测试

### 9.4 SMR-D4：迭代优化
- 根据实际使用反馈优化
- 补充缺失的功能
- 性能优化
- 移动端适配（如果需要）

## 10. 风险和注意事项

### 10.1 技术风险
- Foundation 数据格式可能变化，需要版本兼容
- 证据去重逻辑复杂，可能出现重复或遗漏
- 数据量增大后 SQLite 性能可能不足

### 10.2 业务风险
- Foundation 证据质量不稳定，影响 Dashboard 可信度
- 研究建议和投资建议边界容易模糊
- 用户可能混淆"系统建议"和"人工决策"

### 10.3 合规风险
- 必须严格区分"事实/证据"和"投资判断"
- 所有自动生成的内容必须有"系统生成，仅供参考"的标记
- 人工审核流程必须留痕

### 10.4 边界控制
- Foundation 接入层必须是独立的模块，便于开关
- Dashboard 必须能在 Foundation 不可用时正常工作（降级模式）
- 内部数据和 Foundation 数据在代码层面要清晰分离
