# SMR 外部来源留痕 Runbook

**更新日期**：2026-04-14  
**适用范围**：`11_smr_wiki/raw/external/` 与外部网页原始来源抓取流程

---

## 1. 这条链解决什么问题

这条链解决的是：

- 研究引用的公开网页、公告、新闻、公开研报摘要，没有在当前机器上落原文
- source manifest（来源清单）里没有外部原始来源这一层
- 后续研究卡很容易只剩结论，没有当前机器可复核的原始网页快照

这条链的目标不是直接产研报，而是先把原始来源留痕下来。

---

## 2. 当前目录结构

抓下来的外部来源统一放在：

```text
11_smr_wiki/raw/external/<entity_type>/<entity_id>/<YYYY-MM-DD>/
```

每条来源默认会落 3 个文件：

- `*.md`
  - 可读快照，带 frontmatter（头部元数据）和抽取文本
- `*.raw.html`
  - 原始网页内容
- `*.meta.json`
  - 请求 URL、最终 URL、抓取时间、内容类型、响应头等元数据

---

## 3. 使用命令

通用网页快照命令：

最小抓取命令：

```bash
python3 08_scripts/wiki/fetch_external_source.py \
  --url "https://example.com" \
  --entity-type stock \
  --entity-id 300394.SZ \
  --source-kind news \
  --title "示例来源" \
  --tag smoke
```

常用参数：

- `--url`
  - 来源 URL，可重复传多次
- `--entity-type`
  - 归属对象类型，例如 `stock`、`sector`、`topic`
- `--entity-id`
  - 归属对象 ID，例如 `300394.SZ`
- `--source-kind`
  - 来源类别，例如 `news`、`announcement`、`research`
- `--title`
  - 可选；单链接时可手工指定标题
- `--tag`
  - 可重复，用于补标签
- `--note`
  - 记录补充说明

当前已经落地的专用适配器：

- `python3 08_scripts/wiki/fetch_cninfo_announcements.py`
  - A 股 / 北交所公告原件
- `python3 08_scripts/wiki/fetch_hkex_announcements.py`
  - H 股公告原件
- `python3 08_scripts/wiki/fetch_eastmoney_stock_reports.py`
  - A 股公开研报列表快照
- `python3 08_scripts/wiki/fetch_eastmoney_report_articles.py`
  - A 股公开研报详情页快照 + PDF 原件留痕
- `python3 08_scripts/wiki/extract_eastmoney_report_pdf_text.py`
  - A 股公开研报 PDF 文本抽取
- `python3 08_scripts/wiki/extract_eastmoney_report_structured.py`
  - A 股公开研报结构化快照
- `python3 08_scripts/wiki/extract_eastmoney_report_table_structured.py`
  - A 股公开研报表格结构化快照
- `python3 08_scripts/wiki/fetch_eastmoney_news_search.py`
  - A 股资讯搜索列表快照
- `python3 08_scripts/wiki/fetch_eastmoney_news_articles.py`
  - A 股资讯正文页快照

这些专用适配器当前统一支持的扩量参数：

- `--profile`
  - 从 `00_control/research_amplification_registry.md` 读取覆盖策略
- `--pool-type`
  - 手动覆盖池类型，可重复传
- `--limit`
  - 控制本次最多处理多少只标的

进入“放大量级”时，建议优先看：

- `09_runbooks/smr-amplified-research-coverage.md`

---

## 4. 抓完之后怎么进系统

抓完网页快照后，运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这样 `raw external` 会进入 `source_manifest`，类型是：

- `source_type = external_source_snapshot`

注意：

- 这一步只进入来源清单
- 默认不会自动变成正式 wiki
- 默认也不会自动变成可直接导入的高置信知识

---

## 5. 为什么默认不自动转 draft

外部网页原始快照是“原材料”，不是“结论”。

所以当前规则是：

- 可以进入 `source_manifest`
- 默认不自动混进普通 `create_ingest_draft.py` 主流程
- 只有明确带 `--include-raw-external` 时，才允许把 raw external 也转成 draft

对应命令：

```bash
python3 08_scripts/wiki/create_ingest_draft.py --include-raw-external
```

---

## 6. 当前阶段的正确用法

当前阶段建议这样用：

1. 先抓公开网页原始来源。
2. 如果接下来要跑“详情页 / 正文 / PDF / 结构化”下一层，先更新一次 `source_manifest`。
3. 再由研究脚本或人工从这些来源中提炼研究卡。
4. 需要继续下钻时，再在中间层之间重复执行 `build_source_manifest.py`。
5. 不要把原始网页快照直接当成正式知识页。

---

## 7. 当前已知限制

- 通用抓取器当前优先支持普通网页 HTML 快照
- 强反爬、纯 JS 渲染、登录后内容，仍可能需要专门适配层
- 公告专用适配器已经支持 `PDF / HTM` 原件，但还没有统一全文抽取层
- 东方财富新闻搜索页、资讯正文页、公开研报列表快照、公开研报正文详情页、PDF 原件、PDF 文本抽取、基础结构化快照和首版表格结构化快照已经落地，但覆盖率还不完整，事实校验也还没有统一抽取层

所以这条链现在的定位是：

- **先把通用网页原始来源落下来**
- **先把来源留痕和 manifest 接口搭起来**
- **公告站、资讯搜索页、资讯正文页、公开研报列表 / 正文这些高价值入口先跑起来**
- **后续继续扩表格结构化覆盖率，再补事实校验和更多公开来源**
