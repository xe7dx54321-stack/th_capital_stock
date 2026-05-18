# SMR 东方财富公开研报正文 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股公开研报详情页快照、正文抽取与 PDF 原件留痕

---

## 1. 这条链做什么

这条链负责从已经落下来的 `东方财富公开研报快照` 里取最新研报编号，再去抓：

- 单篇研报详情页
- 详情页对应 PDF 原件

并保存：

- 研报详情页原始 HTML
- 研报正文抽取后的 Markdown 快照
- PDF 原件
- 研报编号、发布时间、机构、研究员、评级、PDF 链接等元数据

它的定位是把“公开研报列表可复核”继续推进到“公开研报正文和原件可复核”。

---

## 2. 前置依赖

必须先有公开研报列表快照：

```bash
python3 08_scripts/wiki/fetch_eastmoney_stock_reports.py
```

正文脚本会直接读取已有 `research_search` 快照里的 `items`，不会重复跑列表接口。

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的抓取：

```bash
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py \
  --ts-code 300308.SZ \
  --ts-code 002281.SZ \
  --report-limit 2
```

如果只抓正文、不抓 PDF：

```bash
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py --skip-pdf
```

如果要强制重抓：

```bash
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py --force
```

---

## 4. 当前实现口径

- 直接读取最新 `eastmoney_report` 列表快照的 `items`
- 默认每个标的抓最新 `2` 篇研报详情页
- 详情页 URL 口径：
  - `https://data.eastmoney.com/report/info/{infoCode}.html`
- PDF URL 口径：
  - `https://pdf.dfcfw.com/pdf/H3_{infoCode}_1.pdf`
- 正文优先从页面内嵌 `zwinfo.notice_content` 提取
- 如果详情页或 PDF 已经在 `source_manifest` 里存在，默认跳过，不重复抓

---

## 5. 结果如何进入系统

抓完后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些正文 / PDF 快照会进入 `source_manifest`，类型仍然是：

- `external_source_snapshot`

但 `source_kind` 会新增：

- `research_article`
- `research_pdf`

---

## 6. 当前真实状态

截至 `2026-04-14` 当前机器已经真实落下：

- `300308.SZ`
  - `research_article = 2`
  - `research_pdf = 2`
- `002281.SZ`
  - `research_article = 2`
  - `research_pdf = 2`

当前重复跑验证结果：

- `article_persisted = 0`
- `pdf_persisted = 0`
- `article_skipped = 4`
- `pdf_skipped = 4`

说明这条链已经具备稳定的“已存在即跳过”能力。

---

## 7. 当前已知限制

- 当前只覆盖已经有 `research_search` 快照的标的
- 当前已经拿到详情页正文和 PDF 原件，并且 PDF 文本抽取链也已经接上
- 当前基础结构化快照和首版表格结构化快照都已经接上，但覆盖率和事实校验还没补齐
- 当前还没做事实校验和机构观点去噪

所以它现在的定位是：

- **先把公开研报列表推进到正文详情页**
- **先把 PDF 原件一起留痕到本机**
- **先让研究卡能引用当前机器上的公开研报正文、原件和抽取文本**
- **结构化快照另走专用链**
- **后续继续扩表格结构化覆盖率，并补事实校验与更多公开来源**
