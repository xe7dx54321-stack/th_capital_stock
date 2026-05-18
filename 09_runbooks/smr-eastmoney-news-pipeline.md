# SMR 东方财富资讯搜索快照 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股资讯搜索页快照与原始 JSONP 留痕

---

## 1. 这条链做什么

这条链负责把 `东方财富资讯搜索页` 的搜索结果抓下来，落到：

- `11_smr_wiki/raw/external/`

并保存：

- 东方财富资讯搜索原始 JSONP
- 资讯列表摘要快照
- 搜索参数、命中结果和搜索 ID（搜索请求 ID）元数据

它的定位不是抓单篇新闻全文，而是先把“资讯搜索入口页 / 列表页”变成当前机器可复核来源。

---

## 2. 默认抓取对象

默认抓当前 `stock_pool_current` 里的：

- `candidate`
- `recommended`

且只抓：

- `*.SZ`
- `*.SH`
- `*.BJ`

搜索关键词默认用：

- 当前标的中文简称

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/fetch_eastmoney_news_search.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的抓取：

```bash
python3 08_scripts/wiki/fetch_eastmoney_news_search.py \
  --ts-code 300308.SZ \
  --ts-code 002281.SZ \
  --sort time \
  --per-symbol-limit 5
```

---

## 4. 当前实现口径

- 直接调用东方财富新版搜索接口 `search/jsonp`
- 使用 `/news/s` 对应的 `cmsArticleWebOld` 资讯类型
- 默认按 `time`（时间）排序，优先落最新资讯
- 每个标的一次性保存一份“资讯列表快照”
- Markdown 快照里会保留最近几条资讯的时间、媒体、标题、摘要、原文链接

---

## 5. 结果如何进入系统

抓完后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些快照会进入 `source_manifest`，类型是：

- `external_source_snapshot`

当前默认不会自动转正式知识草稿。

---

## 6. 当前已知限制

- 这条链当前抓的是“资讯搜索列表快照”，不是单篇新闻正文
- 搜索结果是基于关键词匹配，不等于已经完成事实核验
- 如果指定标的没有返回资讯记录，会记成 `empty`，不会乱落库

所以它现在的定位是：

- **先把资讯搜索入口列表留痕链搭起来**
- **先让研究卡能引用当前机器上的资讯搜索快照**
- **后续再决定是否补单篇正文抓取或全文抽取**
