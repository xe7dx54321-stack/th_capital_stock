# SMR 高价值信息源扩容 Runbook

**更新日期**：2026-04-17  
**当前阶段**：第一批高价值源已落地并完成真实验证  
**主目标**：把系统的信息输入从“偏东方财富资讯流”往“官方一手材料 + 合规高质量研究入口”升级

---

## 1. 先给结论

这轮不是简单多接了几个网页，而是把信息源结构往更像机构研究的方向掰正了一步。

当前已经真实打通、并跑进系统主口径的有三类：

- `SEC` 官方披露链
- 公司 `IR`（投资者关系）官方材料链
- A 股 `CNINFO`（巨潮资讯）里原本就存在、现在被单独抬出来的“投资者关系活动记录 / 调研纪要”链

当前已经开始正式接入、但定位明确是“公开卖方信号摘要”而不是“授权研报全文”的有一类：

- `MarketScreener` 共识评级 / 目标价摘要链

当前已经开始正式接入、定位为“管理层原话复核入口”的有一类：

- `The Motley Fool` 公开电话会文字稿链

当前还**不能假装已经打通**的有两类：

- Morgan Stanley（摩根士丹利）/ J.P. Morgan（摩根大通）/ Citi（花旗）/ Goldman Sachs（高盛）这类国际投行全文研究
- 被官网反爬或挑战页拦住的公司 IR 站点

一句话说：

- **公开可合法获取的一手材料，这轮已经开始真正接进来了**
- **需要授权的卖方全文研究，这轮只建了合规接入位，没有乱抓**

---

## 2. 这轮新增了什么

### 2.1 新增脚本

- `08_scripts/lib/smr_official_intel.py`
  - 负责官方材料发现、URL 清洗、PDF 文本抽取、SEC ticker/CIK（股票代码 / 公司标识）映射
- `08_scripts/wiki/fetch_sec_official_materials.py`
  - 负责抓 `SEC submissions JSON`（公司申报清单 JSON）、主文件、业绩附件
- `08_scripts/wiki/fetch_ir_primary_materials.py`
  - 负责抓公司 `IR` 落地页、演示稿、电话会稿、webcast（电话会网页）等

### 2.2 新增控制表

- `00_control/official_intel_target_registry.md`
  - 定义哪些公司值得长期走“官方高价值源”
- `00_control/source_registry.md`
  - 已补入 `sec_*`、`official_ir_*` 和授权研究入口位

### 2.3 事件层补强

- `08_scripts/lib/smr_events.py`
  - 新增对 `official_ir_material`、`sec_filing_document`、`sec_earnings_material` 的归一化分类
  - 新增对 `CNINFO` 里“投资者关系活动记录表 / 调研纪要”的单独识别
  - 新增旧事件回收逻辑，避免同一份源文件改判后，库里同时残留旧分类和新分类

---

## 3. 已真实打通的高价值源

### 3.1 SEC 官方披露链

已接入：

- `sec_submissions_json`
- `sec_filing_document`
- `sec_earnings_material`

当前覆盖价值最高的材料类型：

- `8-K / 6-K / 10-Q / 10-K / 20-F`
- `EX-99`（业绩稿 / 演示稿 / 电话会附件）

这条链的价值在于：

- 比新闻稿更接近真相层
- 时间戳、表单类型、公司主体都更清楚
- 可以稳定沉淀成长期知识，而不是靠媒体转述

### 3.2 公司 IR 官方材料链

已验证并跑通：

- `Alibaba Group`
- `Microsoft`
- `Apple`
- `AMD`
- `Micron`
- `Marvell`
- `Lumentum`

已纳入目标池但仍按实验对象处理：

- `NVIDIA`
- `Broadcom`

当前可抓到的材料类型：

- 业绩稿
- 电话会稿 / webcast 页面
- 演示稿
- 年报 / 中报 / 季报 PDF

这条链的价值在于：

- 很多真正有营养的材料不在新闻站，而在公司 IR 官网
- 同一家公司官网通常会把“业绩稿 + 电话会 + 演示稿”串在同一个入口里

### 3.3 A 股官方调研 / IR 记录

这条链不是新抓的源，而是把现有 `cninfo_announcement` 里高价值材料单独抬出来了。

当前已经能单独识别成事件类型：

- `investor_relations_activity`

典型材料：

- 投资者关系活动记录表
- 调研纪要
- 部分业绩说明会相关公告

这类材料很重要，因为它比普通公告更接近：

- 管理层口径
- 机构调研问答
- 业务细节补充说明

### 3.4 MarketScreener 公开卖方信号摘要链

这条链当前正式抓的是公开 `consensus`（一致预期）页面，不碰授权全文研报。

当前已纳入对象：

- `NVDA`
- `AMD`
- `MSFT`
- `MRVL`
- `LITE`
- `AVGO`
- `MU`

当前抓取字段：

- `Mean consensus`（一致预期评级）
- `Number of Analysts`（覆盖分析师数量）
- `Last Close Price`（最新收盘价）
- `Average target price`（平均目标价）
- `Spread / Average Target`（相对平均目标价空间）
- `High / Low Price Target`（最高 / 最低目标价）

这条链的价值在于：

- 能补上“公开卖方口径”这一层
- 不依赖授权全文，也不伪装成机构终端
- 很适合做日报里的辅助证据、市场温度计和预期差提醒

### 3.5 The Motley Fool 公开电话会文字稿链

这条链当前抓的是公开网页里的电话会文字稿，不碰付费终端。

当前发现策略已经更新为：

- 优先从个股 `quote`（行情页）里挖 transcript 链接
- 如果个股页没有可用链接，再回退到 `Earnings Call Transcripts` 总列表翻页发现
- 正文页落库前再做一次代码 / 公司名校验，避免串票

当前已经纳入目标表的对象包括：

- `MRVL`
- `MU`
- `AVGO`
- `AMD`

实验跟踪对象包括：

- `NVDA`
- `MSFT`
- `AAPL`
- `09988.HK`

当前已实现的抽取字段：

- 发布时间
- 季度标签
- 发言人列表
- 发言人数
- 电话会正文摘要

这条链的价值在于：

- 它不等同于新闻转述，而是更接近管理层会中原话
- 能补足“官方材料之外”的公开复核层
- 很适合进研究页、日报页和单票详情页做二次核对

截至 `2026-04-17`，这条链已经稳定抓到：

- `MRVL`
- `MU`
- `AVGO`
- `AMD`
- `NVDA`
- `MSFT`
- `AAPL`
- `BABA`

---

## 4. 这轮真实跑出来的结果

### 4.1 本轮执行命令

```bash
python3 08_scripts/wiki/fetch_ir_primary_materials.py --target-key alibaba_primary --target-key microsoft_primary --target-key apple_primary --max-links 6 --max-asset-links 2
python3 08_scripts/wiki/fetch_sec_official_materials.py --target-key amd_primary --target-key micron_primary --target-key broadcom_primary --target-key lumentum_primary --max-filings 3 --max-materials 2 --days-back 180
python3 08_scripts/wiki/fetch_ir_primary_materials.py --target-key amd_primary --target-key micron_primary --target-key broadcom_primary --target-key lumentum_primary --max-links 4 --max-asset-links 1 --timeout 12
python3 08_scripts/wiki/fetch_sec_official_materials.py --target-key marvell_primary --target-key lumentum_primary --max-filings 3 --max-materials 2 --days-back 180
python3 08_scripts/wiki/fetch_ir_primary_materials.py --target-key marvell_primary --target-key lumentum_primary --max-links 4 --max-asset-links 1 --timeout 12
python3 08_scripts/wiki/build_source_manifest.py
python3 08_scripts/events/sync_source_registry.py
python3 08_scripts/events/normalize_market_events.py --days-back 240
```

### 4.2 真实结果

- `IR targets = 9`（累计已跑对象）
- `Fetched IR materials = 34`（累计）
- `IR latest batch failures = 0`
- `IR historical failures = 2`（历史实验中：`Broadcom / 旧 Lumentum URL`）
- `Fetched SEC materials = 41`（累计）
- `source_manifest = 565`
- `market_event rows = 396`
- `market_event_latest rows = 182`
- `stale_deleted_count（首次清理） = 6`
- `stale_deleted_count（最新重跑） = 0`

### 4.3 当前官方材料 source_kind（源类型）计数

- `ir_landing_page = 7`
- `ir_material_page = 27`
- `ir_material_pdf = 7`
- `sec_submissions_json = 8`
- `sec_filing_document = 27`
- `sec_earnings_material = 10`

### 4.4 当前高价值事件计数

- `official_ir_material | earnings_call_material = 17`
- `official_ir_material | investor_presentation = 7`
- `official_ir_material | announcement_general = 5`
- `sec_filing_document | earnings_release = 9`
- `sec_filing_document | quarterly_report = 6`
- `sec_filing_document | annual_results_announcement = 2`
- `sec_earnings_material | earnings_call_material = 2`
- `sec_earnings_material | investor_presentation = 2`
- `sec_earnings_material | earnings_release = 8`
- `cninfo_announcement | investor_relations_activity = 8`

---

## 5. 这轮解决了哪些具体问题

### 5.1 微软 IR 页面误抽脏链接

问题：

- 页面源码里有一大段 JSON 配置
- 之前的“原始 URL 扫描”把这段配置里的整块字符串误识别成链接
- 结果生成脏 URL，最后 `404`

修复：

- 对 HTML 做双层 `unescape`
- 收紧原始 URL 抽取逻辑
- 对 `sec-filings` 这类 IR 站内导航页做过滤，避免重复踩到非目标页面

结果：

- `material_count` 从 `16` 提到 `18`
- `failures` 从 `3` 降到 `0`

### 5.2 事件层旧分类残留

问题：

- 同一份源文件如果重新判成新事件类型，旧事件行会残留在 `market_event`

修复：

- 在 `normalize_market_events.py` 接入旧事件回收

结果：

- 首次清理时一共清掉 `6` 条旧口径事件
- 最新重跑时 `stale_deleted_count = 0`，说明当前表已经稳定

### 5.3 CNINFO 高价值材料被普通公告淹没

问题：

- “投资者关系活动记录表”原来混在普通公告里

修复：

- 在事件层新增 `investor_relations_activity`

### 5.4 公开电话会文字稿还没有进入业务主界面

问题：

- 之前底层已经开始接电话会文字稿，但前台页面还没有专门面板
- 单票详情里也没有把这层作为独立证据展示

修复：

- 在 `日报页 / 研究页 / 单票研究详情页` 新增“公开电话会文字稿”面板
- 在 `Hermes` 日报解释链里补入 `public_transcript_digest`
- 在 dashboard 来源标签里把 `public_transcript` 单独标成“公开电话会文字稿”

结果：

- 这条链不再混在“外部资料”里
- 可以直接作为管理层原话复核入口对外展示

结果：

- 当前已有 `8` 条这类高价值事件被单独抬出来

### 5.4 官方目标池扩容后，IR 抓取不会再因单站超时整批崩溃

问题：

- 目标池一扩，任何一个官网只要超时，就可能把整批 `IR fetch`（IR 抓取）打断

修复：

- `fetch_ir_primary_materials.py / fetch_sec_official_materials.py` 都改成更宽的异常兜底
- 超时、403、连接被断开，现在都只会记成 `failure`，不会把整批任务炸掉
- 外部源落盘文件名也已缩短并附哈希，避免长标题触发 `File name too long`

结果：

- 新增对象测试时，`Broadcom` 虽然没有完全跑通 IR 官网，但整条批处理仍正常结束
- `AMD / Micron / Marvell / Lumentum` 已经能沉淀出新增官方材料

---

## 6. 哪些源现在还不能说“已经打通”

### 6.1 国际投行全文研究

当前状态：

- `premium_research_morgan_stanley`
- `premium_research_jpm`
- `premium_research_citi`
- `premium_research_goldman`

都已经在 `source_registry.md` 里留了合规接入位，但状态仍是：

- `planned`
- `enabled = no`

原因很简单：

- 这些是 `licensed_sellside_research`（授权卖方研究）
- 不能把机构授权平台当成公开网页乱抓

后续正确接法：

- 公司已有账号 / 终端 / 订阅
- 或企业统一的 API / 导出 / 邮件落地链

### 6.2 被站点防护拦住的官网

当前最典型的是：

- `NVIDIA IR`
- `Broadcom IR`

当前状态：

- 目标还保留在 `official_intel_target_registry.md`
- 但官网存在 `Cloudflare challenge`（Cloudflare 挑战页）、远端主动断连或路径稳定性问题
- 当前更多依赖 `SEC` 披露补位

### 6.3 可以接“公开卖方信号摘要”，但不把它当全文研报替代

当前已在 `source_registry.md` 里补入 3 个下一批候选入口：

- `public_analyst_signal_marketscreener`
- `public_analyst_signal_marketbeat`
- `public_transcript_seekingalpha`

这些入口的定位不是“白嫖投行全文”，而是：

- 吃公开页上已经展示出来的评级变化、目标价共识、摘要信号
- 吃公开电话会文本 / 业绩会文本
- 给系统补“公开卖方信号层”和“管理层原话层”

---

## 7. 下一批优先扩什么

按优先级，建议下一批继续做这几件事：

### 7.1 扩官方 IR 目标池

优先扩：

- 当前组合参照层里的重点港股 / 美股映射票
- 与现有持仓强相关的海外对标公司

原则：

- 不是盲目铺满
- 是先把“对策略判断最有帮助的公司”纳进官方高价值源

### 7.2 扩 SEC 高价值表单

优先方向：

- `Form 4`（内部人交易）
- `13D / 13G`（重要股东持仓变动）
- `13F`（机构持仓，偏中频）

这类数据的价值比一般资讯更高，更适合做机会发现和交易前预警。

### 7.3 把官方材料优先送入下游研究链

当前这些材料已经进入：

- `source_manifest`
- `market_event`

下一步要做的是：

- 在 `strategy_watch`
- `rotation`
- `daily_report`

这些链路里明确提高官方一手材料的引用优先级。

---

## 8. 当前边界

这轮完成后，系统的信息输入层已经明显比“只看东方财富资讯”强了一层，但还没有到机构级全量覆盖。

更准确的说法是：

- **第一批官方高价值源已经打通**
- **授权研究入口已经建位，但还没接账号**
- **反爬严重的官网还需要更重型抓取方案**

所以当前阶段最合理的开发方向不是盲目继续堆资讯，而是：

- 继续扩“官方一手材料”
- 把授权研究的接入方案做成合规可插拔
- 让下游策略链真正优先消费这些高价值源
