# SMR 东方财富公开研报 PDF 文本抽取 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股公开研报 PDF 原件到正文文本抽取

---

## 1. 这条链做什么

这条链负责读取已经落下来的 `research_pdf`（研报 PDF 原件快照），在本机做文本抽取，再落一层：

- `research_pdf_text`

并保存：

- 抽取后的原始文本 `*.raw.txt`
- 可读 Markdown 快照
- 研报编号、机构、研究员、评级、PDF 链接、详情页链接等元数据

它的定位是把“PDF 原件可复核”继续推进到“PDF 文本可检索、可引用”。

---

## 2. 前置依赖

必须先有东方财富研报 PDF 原件：

```bash
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py
```

本机还需要 PDF 抽取依赖：

```bash
python3 -m pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple pdfminer.six
```

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_pdf_text.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的抽取：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_pdf_text.py \
  --ts-code 300308.SZ \
  --ts-code 002281.SZ \
  --pdf-limit 2
```

强制重抽：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_pdf_text.py --force
```

---

## 4. 当前实现口径

- 从 `source_manifest` 中读取 `research_pdf`
- 默认每个标的抽最新 `2` 份 PDF
- 使用 `pdfminer.six` 做本机文本抽取
- 抽取文本会落成新的 `research_pdf_text` 快照
- 如果对应 `research_pdf_text` 已存在，默认跳过

---

## 5. 结果如何进入系统

抽取完成后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些抽取结果会进入 `source_manifest`，类型仍然是：

- `external_source_snapshot`

但 `source_kind` 会新增：

- `research_pdf_text`

---

## 6. 当前真实状态

截至 `2026-04-14` 当前机器 4 只活跃 A 股都已经具备：

- `research_search = 1`
- `research_article = 2`
- `research_pdf = 2`
- `research_pdf_text = 2`

当前重复跑验证结果：

- `persisted = 0`
- `skipped = 8`

说明这条链已经具备稳定的“已存在即跳过”能力。

---

## 7. 当前已知限制

- 当前文本抽取已可用，首版统一表格结构化也已经接上
- 抽取文本里仍可能保留 `[Table_*]` 这类占位符
- 当前还没做分段重排、表格复原和事实校验

所以它现在的定位是：

- **先把 PDF 原件推进到可读文本**
- **先让研究卡能引用本机抽取正文**
- **结构化快照另走专用链**
- **后续继续扩表格结构化覆盖率，再补清洗和事实校验**
