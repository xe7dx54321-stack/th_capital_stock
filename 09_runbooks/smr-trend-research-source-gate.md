# SMR 趋势研究来源门禁 Runbook

**更新日期**：2026-04-14  
**适用范围**：`generate_trend_batch.py` 生成的行业卡 / 个股卡

---

## 1. 这条门禁做什么

这条门禁负责把趋势研究入口从“直接写卡”改成：

- 先收集本机来源包
- 再判断是否允许进入正式 `research_index`

如果没有足够的本机支持来源，就：

- 只落研究草稿
- 不写入正式 `research_index`

---

## 2. 当前门禁覆盖范围

当前已经接入门禁的入口：

- `python3 08_scripts/research/generate_trend_batch.py`

它会同时处理：

- 行业趋势卡
- 个股初始趋势研究卡

---

## 3. 门禁检查什么

每张研究卡会先生成一个 `source bundle（来源包）`。

来源包分两层：

- `Base Local Sources`
  - 本机 `daily_bar`
  - 本机 `factor_daily`
  - 本机 `us_daily_bar`
  - 本机趋势汇总快照
- `Supporting Local Sources`
  - 当前机器上的历史研究卡
  - 推荐卡
  - A/H 公告快照
  - 当前批次已通过门禁的行业卡

当前规则很明确：

- 只有基础本机真相层还不够
- 还必须至少找到一条 `Supporting Local Sources`

否则就只允许出草稿。

---

## 4. 通过和失败分别会发生什么

通过门禁时：

- 正式研究卡会落到 `02_research/...`
- 会额外生成 `90_sources.md`
- 会写入 `research_index`

未通过门禁时：

- 草稿会落到 `02_research/drafts/<report_id>/00_research-draft.md`
- 不写入 `research_index`
- 批次状态会保留为 `draft_only` 或混合状态

---

## 5. 命令

```bash
python3 08_scripts/research/generate_trend_batch.py
```

执行后建议再刷新：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

---

## 6. 当前已验证事实

- `300308.SZ / 300394.SZ / 300502.SZ / 002281.SZ / 300620.SZ` 当前都能通过门禁
- `002050.SZ / 688041.SH` 当前支持来源数为 `0`

这意味着：

- 已有来源沉淀的主线标的可以继续生成正式研究卡
- 完全没有支持来源的新标的，当前会被门禁挡成草稿

---

## 7. 这条门禁现在还没覆盖什么

- 历史遗留的深度研究卡不是这次自动改写的
- 其他未来新增的研究生成脚本，还需要逐条接同样的门禁协议

所以这条门禁现在的定位是：

- **先把还在真实写卡的趋势研究入口管起来**
- **先保证新生成研究卡都带本机来源包**
- **后续再把同样规则扩到其他研究入口**
