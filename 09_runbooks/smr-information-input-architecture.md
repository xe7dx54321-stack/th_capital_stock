# SMR 信息输入架构与 Knowhow 补强

**更新日期**：2026-04-16  
**适用范围**：SMR 当前项目的研究、监控、轮动、风控、日报链  
**文档定位**：这份文档不是讲脚本怎么跑，而是讲“系统到底应该吃什么信息、从哪里来、怎么处理、为什么现在还远远不够”。

---

## 1. 先说结论

你刚才那个判断是对的。

SMR 现在还只是：

- 一套**最小研究流程**
- 一套**能形成初步建议的业务骨架**
- 一套**脚本链能跑通的原型系统**

它还完全不是机构级的信息工厂。

当前系统已经有：

- A / H / 美股映射的日线价格
- 轻量趋势因子
- 轻量基本面因子
- 部分公告 / 研报 / 新闻抓取
- 股票池、轮动候选、动作备忘
- 最小风控和日报快照

但专业系统真正要吃的信息，远不止这些。

外部公开资料能直接说明这一点：

- BlackRock（贝莱德）Systematic 页面明确写到，它们会用**传统数据 + 另类数据（alternative data，另类数据）**，并且每天对**数千只证券**形成观点；其平台会分析 **15,000+ equity securities（15,000+ 只股票）**、使用 **300+ unstructured data sources（300+ 非结构化数据源）**、维护 **1,000+ alpha signals（1,000+ 阿尔法信号）**。[BlackRock Systematic](https://www.blackrock.com/uk/solutions/systematic-investing)
- BlackRock 2025 年的 data-and-AI（数据与 AI）文章明确写到，它们过去几十年已经建立了 **1,000+ data-driven investment signals（1,000+ 数据驱动投资信号）**，还会把 **job postings（招聘信息）**、**earnings call transcripts（业绩会文本）** 等输入拿来做预测。[Reimagining alpha with data and AI](https://www.blackrock.com/us/financial-professionals/insights/data-driven-investing)
- AQR（阿卡迪亚量化）也把 systematic equity（系统化股票）定义成：用**可重复、数据驱动、跨大范围股票池**的量化模型，信号不只是一种，而是一整组持续扩展的 signals（信号集）。[AQR Systematic Equities](https://www.aqr.com/Learning-Center/Systematic-Equities)

所以，SMR 接下来要补的不是“再多抓几条新闻”，而是把输入层升级成一个**分层数据体系**。

---

## 2. 对当前系统的真实判断

### 2.1 当前系统已经覆盖的输入

截至这份文档更新时，SMR 已接入或部分接入的输入大类主要是：

1. **价格与基础行情**
   - A / H / 美股映射日线
   - 最近 5 日价格抓取
   - 基于日线的趋势特征

2. **轻量因子**
   - trend（趋势）
   - fundamental（轻量基本面）
   - us_linkage（美股映射联动）

3. **外部文本来源**
   - 东方财富研报搜索 / 正文 / PDF / 表格结构化
   - 东方财富新闻搜索 / 正文
   - 巨潮公告
   - HKEX 公告

4. **研究与组合对象**
   - objective monitor（客观监控）
   - strategy watch（策略观察）
   - rotation candidates（轮动候选）
   - execution plan（执行计划）
   - portfolio action memo（动作建议稿）

5. **最小组合与风控**
   - position（持仓主表）
   - pnl（盈亏更新）
   - risk monitor（风控巡检）

### 2.2 当前系统最缺的不是“结论”，而是“输入宽度和密度”

现在最大的问题不是脚本不会总结，而是输入层太薄。

更直白一点说：

- 现在系统知道“股价怎么走”
- 也知道“一部分研报和公告写了什么”
- 但还不知道很多机构每天真正盯着的东西：
  - 资金流怎么走
  - 谁在加仓减仓
  - 北向 / 南向 / 融资融券 / 短仓怎么变
  - 期货 / 期权 / 基差 / 波动率怎么看
  - 产业链景气到底是政策驱动、订单驱动、价格驱动，还是库存驱动
  - 同一条消息是事实，还是市场已经 price in（提前计价，提前反映）

所以现在系统给出的很多建议，本质上还是：

- 用有限信息做出的“像样建议”
- 不是用足够信息做出的“强结论”

---

## 3. 专业级输入地图

下面这张图是 SMR 接下来应该建立的输入总图。

### 3.1 第一层：交易与市场微观结构层

这是最容易被低配系统忽略、但专业资金每天都在看的层。

#### 这层应该包含什么

- 日线之外的 **intraday bars（分时 / 分钟级行情）**
- 成交额、换手率、量比、开盘竞价、收盘竞价
- 涨跌停、炸板、连板、板块广度
- ETF 资金流、行业 ETF 相对强弱
- 北向 / 南向 / Stock Connect（互联互通）流向
- 融资融券、两融余额、融券变化
- short interest（卖空仓位）
- block trades（大宗交易）
- options / futures open interest（期权 / 期货持仓）
- implied volatility（隐含波动率）
- basis / spread（基差 / 利差）
- CCASS shareholding（中央结算持股分布，香港市场）

#### 这些信息在哪里

- 中国公告与公开市场信息总入口：  
  [CNINFO（巨潮资讯）](https://www.cninfo.com.cn/)
- 上交所公司公告、融资融券、股票期权信息：  
  [SSE 公司公告](https://www.sse.com.cn/assortment/stock/list/info/announcement/)
- 深交所定期报告与信息披露：  
  [SZSE 定期报告](https://www.szse.cn/disclosure/listed/fixed/index.html)
- 港股公告、CCASS、披露权益：  
  [HKEXnews](https://www.hkexnews.hk/)
- 港股 / A 股互联互通每日统计、可交易证券：  
  [HKEX Connect Hub](https://www.hkex.com.hk/Mutual-Market/Connect-Hub)
- 美股 short interest（卖空仓位）：  
  [FINRA Short Interest Reporting](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest)  
  [Nasdaq Short Interest Report](https://www.nasdaq.com/solutions/data/equities/short-interest)
- 美股衍生品持仓 / 期货定位：  
  [CFTC Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)

#### 这层怎么获取

- 对公开入口，优先做：
  - 页面抓取
  - 表格抽取
  - 官方 API（数据 API）
  - 每日增量快照
- 对高频 / 分钟级 / 深度盘口：
  - 这类通常不能只靠免费网页抓，后面需要单独的数据授权或商业源

#### 这层怎么分析

- 先做**事实层**，不要一上来做观点层：
  - 今天北向净买入多少
  - 两融余额变了多少
  - 盘中放量发生在几点
  - 某板块广度是扩散还是缩窄
- 再做**相对层**：
  - 相对过去 20 日 / 60 日是否异常
  - 相对行业和主题是否领先
- 最后做**事件解释层**：
  - 是趋势强化
  - 是短线拥挤
  - 是资金切主线
  - 还是纯消息脉冲

### 3.2 第二层：公司事实与事件层

这是 SMR 现在已经接了一部分，但还远不够。

#### 这层应该包含什么

- 年报、半年报、季报
- 临时公告
- 业绩预告 / 快报
- 再融资、可转债、增发、回购、减持、解禁
- 股权质押、股东变动、高管持股
- 并购、诉讼、行政处罚、监管问询
- earnings releases（业绩披露）
- earnings calls（业绩会）
- investor presentations（投资者演示材料）
- management guidance（管理层指引）
- investor Q&A（投资者问答 / 互动平台）

#### 这些信息在哪里

- A 股法定披露与公开信息总入口：  
  [CNINFO（巨潮资讯）](https://www.cninfo.com.cn/)
- CNINFO 的数据平台、数据 API、互动易：  
  [CNINFO Data / API / 互动易](https://www.cninfo.com.cn/)
- 上交所公告全文、PDF 下载：  
  [SSE 公司公告](https://www.sse.com.cn/assortment/stock/list/info/announcement/)
- 深交所定期报告：  
  [SZSE 定期报告](https://www.szse.cn/disclosure/listed/fixed/index.html)
- 港股公告、披露权益、CCASS：  
  [HKEXnews](https://www.hkexnews.hk/)
- 美股法定文件、13F、8-K、10-K、10-Q、Forms 3/4/5：  
  [SEC EDGAR Search & APIs](https://www.sec.gov/search-filings)

#### 这层怎么获取

- 把公告和文件拆成 3 个对象：
  - source file（原文）
  - structured event（结构化事件）
  - knowledge delta（对 thesis 的影响增量）
- 每一份文件都要绑定：
  - entity（公司 / 行业 / 标的）
  - event_date（事件日期）
  - publish_time（发布时间）
  - event_type（事件类型）
  - materiality（重要性）

#### 这层怎么分析

- 不能只抽“摘要”，要抽“变化”：
  - 比上次披露变好还是变坏
  - 是市场预期内还是预期外
  - 影响收入、利润、现金流、订单、资本开支、股本哪个环节
- 研究系统最终要落到：
  - thesis strengthened（逻辑增强）
  - thesis unchanged（逻辑不变）
  - thesis weakened（逻辑减弱）
  - thesis broken（逻辑证伪）

### 3.3 第三层：财务、估值与一致预期层

SMR 现在有轻量基本面，但没有完整财务分析层。

#### 这层应该包含什么

- 全量三大报表
- 分部收入、区域收入、毛利率、费用率
- 现金流、资本开支、存货、应收、合同负债
- ROE / ROIC / FCF / 盈利质量
- forward valuation（前瞻估值）
- analyst consensus（分析师一致预期）
- estimate revision（预期上调 / 下调）
- target price dispersion（目标价分歧）

#### 这些信息在哪里

- 美股财报与 XBRL：  
  [SEC EDGAR APIs](https://www.sec.gov/search-filings)
- A 股 / 港股原始报告与公告：  
  [CNINFO（巨潮资讯）](https://www.cninfo.com.cn/)  
  [HKEXnews](https://www.hkexnews.hk/)
- 卖方一致预期这类信息，公开源通常不完整。  
  这里我明确判断：**如果后面要做更强的 surprise（预期差）分析，迟早要接商业数据源。**  
  这不是现在马上买，而是业务上必须承认这个缺口存在。

#### 这层怎么分析

- 把绝对值分析，升级成“变化率 + 相对预期 + 行业比较”
- 重点看：
  - 盈利是否超预期
  - 收入和利润谁驱动
  - 现金流是否支持利润
  - 存货 / 应收是否恶化
  - 估值是否靠情绪拉升而不是业绩兑现

### 3.4 第四层：行业链与宏观层

这层现在几乎还是空白，但对你这种“赛道+轮动”系统非常关键。

#### 这层应该包含什么

- 工业增加值
- 制造业分行业景气
- 出口 / 进口 / 海关分品类数据
- 社融、M2、利率、汇率
- PMI、消费、投资、地产、就业
- 原材料价格、运价、电力、库存
- 行业产量、装机量、出货量、渗透率

#### 这些信息在哪里

- 中国工业与制造业官方数据：  
  [国家统计局 NBS](https://www.stats.gov.cn/english/)
- 中国货币、社融、M2：  
  [中国人民银行 PBC](https://www.pbc.gov.cn/en/)
- 中国进出口与海关分项：  
  [General Administration of Customs of China](https://english.customs.gov.cn/)
- 美国 CPI / PPI / 就业 / JOLTS 等：  
  [BLS](https://www.bls.gov/)
- 美国 GDP / 企业利润：  
  [BEA GDP](https://www.bea.gov/data/gdp/gross-domestic-product)
- 跨源宏观时间序列汇总：  
  [FRED](https://fred.stlouisfed.org/)

#### 这层怎么获取

- 宏观不要只抓 headline（标题数字）
- 要按主题建表：
  - 增长
  - 通胀
  - 流动性
  - 信用
  - 外需
  - 大宗商品
- 行业链要做：
  - 官方源
  - 行业协会
  - 公司公告
  - 新闻
  - 卖方研究
  的交叉校验

#### 这层怎么分析

- 不直接把宏观数据拿去推单票
- 先做三层传播：
  - macro -> sector（宏观到行业）
  - sector -> company（行业到公司）
  - company -> portfolio（公司到组合）
- 例如：
  - 出口增速变化影响光模块、设备、消费电子链
  - 社融和利率变化影响券商、银行、地产链
  - 产业产量和价格影响上游资源、中游制造、下游消费的利润分配

### 3.5 第五层：文本、舆情与管理层语言层

这是 LLM（大模型）最能发挥作用的一层。

#### 这层应该包含什么

- 新闻正文
- 公告正文
- 研报正文
- earnings call transcript（业绩会文字稿）
- 投资者问答
- 管理层口径变化
- 卖方观点变化

#### 这些信息在哪里

- 研报 / 新闻：  
  当前系统已经接了东方财富链
- 投资者互动：  
  [CNINFO 互动易](https://www.cninfo.com.cn/)
- 港股公告与披露：  
  [HKEXnews](https://www.hkexnews.hk/)
- 美股原始文件与补充材料：  
  [SEC EDGAR](https://www.sec.gov/search-filings)  
  公司 IR（投资者关系）官网

#### 这层怎么获取

- 先做清洗：
  - 去广告、去模板、去导航
  - 抽段落、表格、问答、风险提示
- 再做结构化：
  - entity extraction（实体抽取）
  - event extraction（事件抽取）
  - sentiment / stance（语气 / 立场）
  - change detection（口径变化检测）

#### 这层怎么分析

- 重点不是“总结全文”
- 重点是：
  - 相比上次，多说了什么，少说了什么
  - 风险提示是否变重
  - 管理层是否更保守
  - 分析师是否开始下修
  - 消息是否被多源交叉证实

### 3.6 第六层：另类数据层

这层不是现在立刻全做，但必须提前在 knowhow（业务认知）里留位置。

#### 这层可以包含什么

- job postings（招聘信息）
- web traffic（网站流量）
- app rankings / downloads（应用排名 / 下载）
- search trend（搜索趋势）
- geolocation（地理位置）
- transaction activity（交易活动）
- satellite imagery（卫星图像）
- patents（专利）
- tenders / procurement（招投标 / 采购）
- shipping / logistics（航运 / 物流）

#### 这层怎么理解

- 不是所有赛道都需要这层
- 但一旦你想比“看公告和研报的人”更早一步，这层就很重要

#### 这层适合谁

- 更适合类 Hermes 的研究提炼和特征实验
- 不适合一上来就全量投入主链

---

## 4. 信息获取之后，不能直接出结论，必须先过 6 道处理

专业系统真正强的地方，不只是“抓到了”，而是“处理对了”。

### 4.1 统一对象化

所有输入最后都要落到统一对象：

- security（证券）
- company（公司）
- sector（行业 / 主题）
- event（事件）
- factor snapshot（因子快照）
- thesis delta（逻辑变化）
- portfolio impact（组合影响）

### 4.2 时间统一

必须区分：

- event_time（事件发生时间）
- publish_time（发布时间）
- ingest_time（入库时间）
- market_effective_time（市场可交易时间）

如果这件事不严，很多回测和解释都会变成假象。

### 4.3 事实层和解释层分离

系统里必须有两层：

- fact layer（事实层）
- interpretation layer（解释层）

例如：

- 事实层：北向净买入 23 亿
- 解释层：资金回流半导体主线

不能把解释写成事实。

### 4.4 做 surprise（预期差）而不是只做 level（绝对水平）

市场交易的不是“好不好”，而是“比预期好还是差”。

所以很多字段都要做：

- vs previous（比上次）
- vs consensus（比预期）
- vs sector（比同行）
- vs regime（比当前市场环境）

### 4.5 做 cross-confirmation（交叉验证）

一条信息单独看，很容易误判。

必须问：

- 有没有第二来源确认
- 价格有没有响应
- 成交量有没有配合
- 公告 / 新闻 / 管理层口径是否一致

### 4.6 做 signal decay（信号衰减）和 half-life（半衰期）

不是每条信号都值一样久。

例如：

- 财报 surprise（财报超预期）可能影响数周
- 单条新闻脉冲可能只影响数小时到数天
- 行业景气切换可能影响数月

所以系统不能只记录“有信号”，还要记录“信号还能不能用”。

---

## 5. 按当前项目阶段，应该怎么补

### 5.1 第一优先级：把“官方事实层”补齐

这一步最值钱，也最不容易跑偏。

必须优先补的输入：

1. A / H / 美股公告与法定文件全量化
2. 北向 / 南向 / 融资融券 / short interest（卖空仓位）
3. 日历类事件
   - 财报日
   - 解禁日
   - 股东会
   - 分红除权
   - 回购 / 减持窗口
4. 更完整的财务字段
5. 宏观和行业链官方时间序列

### 5.2 第二优先级：把“市场行为层”补齐

这一步解决“为什么今天强 / 弱”的判断力。

建议补：

- 分时 / 分钟级数据
- 行业广度
- ETF 流向
- 量价异常
- 大宗交易
- 期权 / 期货定位

### 5.3 第三优先级：把“预期差层”补齐

这一步决定系统能不能从“看新闻”升级到“看预期差”。

建议补：

- analyst revision（一致预期修正）
- 管理层指引变化
- earnings call transcript（业绩会文字稿）
- 投资者问答语气变化

### 5.4 第四优先级：把“另类数据实验层”做成沙盒

这一步不要一上来并进主链。

更合理的是：

- 先建实验区
- 先做 sector-specific（行业定制）特征
- 先评估是否真有增量
- 再决定是否进入正式主链

---

## 6. 对应到双 agent（双代理）怎么拆

这块和你前面强调的 OpenClaw / Hermes 思路是一致的，而且现在更清楚了。

### 6.1 类 OpenClaw 负责什么

类 OpenClaw 适合做：

- 定时抓取
- 增量同步
- 网页下载
- PDF 抽取
- 表格结构化
- 时间序列更新
- 字段标准化
- 去重
- 事件分类
- 因子计算
- 数据质检

一句话：

- **它负责把外部世界变成干净、可计算、可追踪的事实对象。**

### 6.2 类 Hermes 负责什么

类 Hermes 适合做：

- 事实冲突消解
- thesis 更新
- 事件重要性判断
- 跨来源整合
- 赛道叙事变化判断
- 研究卡补充
- 轮动逻辑解释
- 风险成因归因
- wiki 知识沉淀

一句话：

- **它负责把事实对象变成可复用的判断、知识和决策语言。**

### 6.3 一条正确的流水线应该长这样

```text
外部源
-> 类 OpenClaw 抓取
-> 原始快照
-> 结构化事件 / 时间序列 / 因子
-> 事实层校验
-> 类 Hermes 解释与整合
-> thesis delta / research update / portfolio impact
-> registry + wiki + daily report + rotation / risk
```

---

## 7. 对 SMR 的阶段性判断

这部分是我基于当前代码、runbook（运行手册）和外部资料做出的判断。

### 7.1 当前 SMR 大概处在什么位置

如果把系统能力粗分成 5 个阶段：

1. 只有人工看盘
2. 有脚本和日报
3. 有对象化研究链
4. 有分层数据工厂
5. 有机构级信号工厂和持续验证

那么 SMR 现在大概在：

- **2.5 到 3 之间**

也就是：

- 已经超过“只是写日报”
- 但离“分层数据工厂”还差很远

### 7.2 现在最不该自欺的地方

当前最容易自欺的点有 4 个：

1. 以为“有了几个研究产物”就等于信息够了
2. 以为“跑了几次批处理”就等于覆盖够了
3. 以为“有 LLM 能总结”就等于理解够了
4. 以为“有轮动建议”就等于决策闭环已经成熟

这些都还不是。

---

## 8. 下一步施工建议

这部分不是宏观口号，是可以直接落地到当前项目里的施工顺序。

### Step 1

补“事实层输入注册表”：

- 给每个输入源建 source registry（来源注册表）
- 写清：
  - source_type（来源类型）
  - entity_scope（覆盖对象）
  - frequency（频率）
  - freshness SLA（新鲜度要求）
  - cost level（成本等级）
  - confidence（可信度）

### Step 2

补“事件层 schema（结构化字段）”：

- 公告事件
- 财报事件
- 资金流事件
- 两融 / 卖空事件
- 解禁 / 减持 / 回购事件
- 宏观数据事件

### Step 3

补“市场行为层脚本”

优先做：

- 北向 / 南向
- 两融
- 解禁
- 大宗交易
- 财报 / 分红 / 股东会日历

### Step 4

补“行业链时间序列”

优先围绕你当前重点赛道做：

- 光模块 / 光通信
- 算力 / 芯片 / 存储
- AI 应用 / agent（智能体）链
- 机器人 / embodied AI（具身智能）

### Step 5

把现有研究链升级成“预期差链”

也就是让系统不只会说：

- 这票趋势强

而是会说：

- 这票为什么比市场预期更强
- 这次强，是业绩、资金、产业、还是情绪驱动
- 这个强还能持续多久

---

## 9. 附：这次外部检索用到的关键参考

- BlackRock Systematic Investing  
  [https://www.blackrock.com/uk/solutions/systematic-investing](https://www.blackrock.com/uk/solutions/systematic-investing)
- BlackRock Reimagining alpha with data and AI  
  [https://www.blackrock.com/us/financial-professionals/insights/data-driven-investing](https://www.blackrock.com/us/financial-professionals/insights/data-driven-investing)
- AQR Systematic Equities  
  [https://www.aqr.com/Learning-Center/Systematic-Equities](https://www.aqr.com/Learning-Center/Systematic-Equities)
- CNINFO（巨潮资讯）  
  [https://www.cninfo.com.cn/](https://www.cninfo.com.cn/)
- Shanghai Stock Exchange（上交所）公司公告  
  [https://www.sse.com.cn/assortment/stock/list/info/announcement/](https://www.sse.com.cn/assortment/stock/list/info/announcement/)
- Shenzhen Stock Exchange（深交所）定期报告  
  [https://www.szse.cn/disclosure/listed/fixed/index.html](https://www.szse.cn/disclosure/listed/fixed/index.html)
- HKEXnews  
  [https://www.hkexnews.hk/](https://www.hkexnews.hk/)
- HKEX Connect Hub  
  [https://www.hkex.com.hk/Mutual-Market/Connect-Hub](https://www.hkex.com.hk/Mutual-Market/Connect-Hub)
- SEC EDGAR Search & APIs  
  [https://www.sec.gov/search-filings](https://www.sec.gov/search-filings)
- FINRA Short Interest Reporting  
  [https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest)
- Nasdaq Short Interest Report  
  [https://www.nasdaq.com/solutions/data/equities/short-interest](https://www.nasdaq.com/solutions/data/equities/short-interest)
- CFTC Commitments of Traders  
  [https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)
- 国家统计局 NBS  
  [https://www.stats.gov.cn/english/](https://www.stats.gov.cn/english/)
- 中国人民银行 PBC  
  [https://www.pbc.gov.cn/en/](https://www.pbc.gov.cn/en/)
- 中国海关总署英文站  
  [https://english.customs.gov.cn/](https://english.customs.gov.cn/)
- BLS  
  [https://www.bls.gov/](https://www.bls.gov/)
- BEA GDP  
  [https://www.bea.gov/data/gdp/gross-domestic-product](https://www.bea.gov/data/gdp/gross-domestic-product)
- FRED  
  [https://fred.stlouisfed.org/](https://fred.stlouisfed.org/)
