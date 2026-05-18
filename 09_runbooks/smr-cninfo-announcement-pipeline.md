# SMR 巨潮公告抓取 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股公告搜索与原始公告 PDF 留痕

---

## 1. 这条链做什么

这条链负责把 `cninfo（巨潮资讯）` 里的 A 股公告结果抓下来，落到：

- `11_smr_wiki/raw/external/`

并保存：

- 公告 PDF / TXT 原件
- 公告元数据
- 公告摘要快照

---

## 2. 默认抓取对象

默认抓当前 `stock_pool_current` 里的：

- `candidate`
- `recommended`

且只抓 A 股 / 北交所代码：

- `*.SZ`
- `*.SH`
- `*.BJ`

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/fetch_cninfo_announcements.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的抓取：

```bash
python3 08_scripts/wiki/fetch_cninfo_announcements.py \
  --ts-code 300308.SZ \
  --ts-code 002281.SZ \
  --days-back 120 \
  --per-symbol-limit 5
```

---

## 4. 当前实现口径

- 用 `cninfo` 公告搜索接口按公司名查询
- 再按 `secCode` 精确回收当前标的对应结果
- 对每条结果抓取 `adjunctUrl` 指向的原始文件
- 当前以 PDF / TXT 公告原件为主

---

## 5. 结果如何进入系统

抓完后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些公告会进入 `source_manifest`，类型是：

- `external_source_snapshot`

当前默认不会自动转正式知识草稿。

---

## 6. 当前已知限制

- 目前只覆盖 A 股 / 北交所公告，不含港股公告
- 目前优先抓 `candidate / recommended`，不是全市场全量
- 目前只抓公告原件和元数据，不做 PDF 正文抽取

所以它现在的定位是：

- **先把 A 股公告原件留痕链搭起来**
- **先让研究引用有本机可复核来源**
- **HKEX（港交所）公告链已拆到独立 runbook：`smr-hkex-announcement-pipeline.md`**
- **后续再补 PDF 文本抽取**
