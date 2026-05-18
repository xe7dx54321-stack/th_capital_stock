# SMR Wiki Bootstrap Runbook

## 目标

跑通当前第一批最小闭环：

1. 建 source manifest
2. 从 source manifest 生成 ingest draft
3. 把 draft 导出成 markdown 供人工查看

## 运行顺序

### 1. 建 source manifest

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

输出：

- SQLite 表 `source_manifest`
- 快照文件 `11_smr_wiki/raw/manifests/source_manifest_latest.md`

### 2. 创建 ingest draft

```bash
python3 08_scripts/wiki/create_ingest_draft.py --limit 20
```

如果要重建已有 draft：

```bash
python3 08_scripts/wiki/create_ingest_draft.py --limit 20 --include-existing
```

### 3. 查看 draft 列表

```bash
python3 08_scripts/wiki/list_ingest_drafts.py --limit 20
```

### 4. 导出 draft markdown

```bash
python3 08_scripts/wiki/export_draft_markdown.py --limit 10
```

输出目录：

- `11_smr_wiki/drafts/ingest/`

## 当前阶段口径

- `daily_report / dispatch_snapshot / pool_snapshot` 默认 `ready`
- `industry_research / stock_research / recommendation_card / risk_alert_snapshot` 默认 `review_required`

进入治理阶段后，继续看：

- [smr-wiki-governance.md](/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/09_runbooks/smr-wiki-governance.md)
- [smr-task-registry.md](/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/09_runbooks/smr-task-registry.md)

## 当前阶段已经完成

- source manifest
- ingest draft
- scan
- review queue
- review resolution
- import execution
- wiki 正式页最小导入
- task registry 承接层

## 当前阶段还没做的事

- 批量导入策略
- 更复杂的知识页 merge
- lint / stale backlog
