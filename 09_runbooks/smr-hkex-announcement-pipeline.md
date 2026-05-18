# SMR 港交所公告抓取 Runbook

**更新日期**：2026-04-14  
**适用范围**：H 股公告搜索与原始公告文件留痕

---

## 1. 这条链做什么

这条链负责把 `HKEX News（港交所披露易）` 里的 H 股公告结果抓下来，落到：

- `11_smr_wiki/raw/external/`

并保存：

- 公告 PDF / HTM 原件
- 公告元数据
- 公告摘要快照

---

## 2. 默认抓取对象

默认抓当前活跃 H 股覆盖范围里的：

- `recommended`
- `candidate`
- `watchlist`
- `seed`

当前主项目里，这意味着会覆盖当前 H 股种子池。

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/fetch_hkex_announcements.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的抓取：

```bash
python3 08_scripts/wiki/fetch_hkex_announcements.py \
  --ts-code 00981.HK \
  --ts-code 01347.HK \
  --days-back 365 \
  --per-symbol-limit 3
```

---

## 4. 当前实现口径

- 用 `HKEX` 官方 `prefix.do / partial.do` 解析 `stockId`
- 再调用 `titleSearchServlet.do` 回收该股票最近公告
- 对每条结果抓取 `FILE_LINK` 指向的原始文件
- 当前以 `PDF / HTM` 公告原件为主

---

## 5. 当前安全护栏

由于本地主项目里的 H 股注册表名称主要是中文，而 `HKEX` 搜索结果主要是英文简称，所以这条链加了一层名称护栏：

- 对当前已知 H 股核心标的，要求官方英文简称与预期提示一致
- 如果发现“代码能搜到，但搜到的是另一家公司”，直接记失败，不落库

这一步是为了避免把错码静默抓进系统。

---

## 6. 结果如何进入系统

抓完后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些公告会进入 `source_manifest`，类型是：

- `external_source_snapshot`

当前默认不会自动转正式知识草稿。

---

## 7. 当前已知限制

- 现在优先抓标题搜索结果里的原始文件，不做全文语义抽取
- 如果本地 H 股代码本身有错，这条链会显式失败，不会自动纠正真相层
- 当前名称护栏先覆盖本项目已知核心 H 股，不是全市场通用别名字典

所以它现在的定位是：

- **先把 H 股公告原件留痕链搭起来**
- **先让 H 股研究引用也有本机可复核来源**
- **先把本地错码问题显式暴露出来，而不是静默污染系统**
