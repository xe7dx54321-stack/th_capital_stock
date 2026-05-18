# SMR 东方财富资讯正文快照 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股资讯正文页快照与原始 HTML 留痕

---

## 1. 这条链做什么

这条链负责从已经落下来的 `东方财富资讯搜索快照` 里取最新文章链接，再去抓：

- 单篇资讯正文页

并保存：

- 正文页原始 HTML
- 正文抽取后的 Markdown 快照
- 文章编号、发布时间、媒体名、原文链接等元数据

它的定位是把“搜索页可复核”继续推进到“正文页可复核”。

---

## 2. 前置依赖

必须先有搜索页快照：

```bash
python3 08_scripts/wiki/fetch_eastmoney_news_search.py
```

正文脚本会直接读取已有搜索快照里的文章列表，不会重复搜索。

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/fetch_eastmoney_news_articles.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的抓取：

```bash
python3 08_scripts/wiki/fetch_eastmoney_news_articles.py \
  --ts-code 300308.SZ \
  --ts-code 002281.SZ \
  --article-limit 2
```

如果要强制重抓：

```bash
python3 08_scripts/wiki/fetch_eastmoney_news_articles.py --force
```

---

## 4. 当前实现口径

- 直接读取最新 `eastmoney_news_search` 快照的 `items`
- 默认每个标的抓最新 `2` 篇正文页
- 正文主容器按 `ContentBody` / `txtinfos` 提取
- 如果正文页已经在 `source_manifest` 里存在，默认跳过，不重复抓

---

## 5. 结果如何进入系统

抓完后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些正文快照会进入 `source_manifest`，类型仍然是：

- `external_source_snapshot`

但 `source_kind` 会变成：

- `news_article`

---

## 6. 当前已知限制

- 这条链目前只覆盖东方财富资讯正文页
- 目前只做正文抽取，不做事实校验
- 公开研报正文详情页、PDF 原件、PDF 文本抽取和首版表格结构化链已经接上

所以它现在的定位是：

- **先把资讯搜索页推进到资讯正文页**
- **先让研究卡能引用本机正文原文**
- **后续继续扩公开研报表格结构化覆盖率与统一全文抽取层**
