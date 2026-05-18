# SMR 研究索引路径清洗 Runbook

**更新日期**：2026-04-14  
**适用范围**：`research_index.file_path` 从旧机器路径迁回当前项目目录

---

## 1. 这条链做什么

这条链负责把 `research_index` 里仍然残留的旧路径，例如：

- `/Users/apple/Documents/同行资本二级市场/...`

清洗成当前机器下的规范绝对路径，例如：

- `/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/...`

它只处理两类安全情况：

- 旧路径能映射到当前项目目录
- 且映射后的真实文件在当前机器上确实存在

---

## 2. 为什么要先做这一步

如果这一步不做，系统虽然“看起来能找到文件”，但数据库主口径仍是旧机器路径，会带来两个问题：

- 审计报告一直显示 `legacy_path_mapped_exists`
- 后续任何基于 `research_index.file_path` 的留痕、导出、复核，都还是脏口径

所以这一步的目标不是“让文件能打开”，而是：

- **把数据库主口径也清成当前机器真实路径**

---

## 3. 命令

先做预演，不回写数据库：

```bash
python3 08_scripts/research/migrate_research_source_paths.py
```

确认报告后，再正式回写：

```bash
python3 08_scripts/research/migrate_research_source_paths.py --apply
python3 08_scripts/research/audit_research_source_paths.py
python3 08_scripts/wiki/build_source_manifest.py
```

---

## 4. 结果文件

预演和正式回写都会生成：

- `02_research/summary/research_source_migration_latest.md`

回写后再看：

- `02_research/summary/research_source_audit_latest.md`

理想结果是：

- `legacy_path_mapped_exists` 显著下降
- `current_path_exists` 显著上升

---

## 5. 当前安全边界

这条链不会：

- 自动改 Markdown 文件内容
- 自动重建研究卡
- 自动批准 wiki 草稿

它只做一件事：

- **把数据库里已经能在当前机器复核到的研究文件路径，回写成当前机器规范路径**
