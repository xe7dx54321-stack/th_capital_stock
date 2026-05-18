# SMR Wiki Governance Workflow

## 目标

把 `source manifest -> ingest draft -> review -> import` 这条治理链路跑顺。

## 当前可用脚本

### 1. 扫描草稿状态

```bash
python3 08_scripts/wiki/scan_ingest_drafts.py --limit 200
```

作用：

- 检查已导入 source 的重复导入风险
- 检查 singleton 页面是否会覆盖现有知识页
- 更新 draft 的 `governance_status / approval_status / review_reason_code`

### 2. 生成人工审核队列

```bash
python3 08_scripts/wiki/build_review_queue.py --limit 50
```

输出：

- `11_smr_wiki/drafts/review_exports/review_queue_*.md`

默认只包含：

- `review_required + pending_manual_review`
- `review_required + reopened`

如果要看已拒绝对象：

```bash
python3 08_scripts/wiki/build_review_queue.py --include-rejected --limit 50
```

### 3. 审核决议

批准：

```bash
python3 08_scripts/wiki/resolve_review.py \
  --draft-id 'draft__stock_research__002281_sz_2026-04-10_deep_research' \
  --decision approved \
  --reason '人工审核通过'
```

拒绝：

```bash
python3 08_scripts/wiki/resolve_review.py \
  --draft-id 'draft__stock_research__300620_sz_2026-04-10_deep_research' \
  --decision rejected \
  --reason-code insufficient_evidence \
  --reason '订单与商业化证据不足'
```

重开：

```bash
python3 08_scripts/wiki/resolve_review.py \
  --draft-id 'draft__stock_research__300620_sz_2026-04-10_deep_research' \
  --decision reopened \
  --reason '补证据后重新评估'
```

### 4. 正式导入 Wiki

```bash
python3 08_scripts/wiki/import_wiki_entry.py \
  --draft-id 'draft__stock_research__002281_sz_2026-04-10_deep_research'
```

导入条件：

- `governance_status=ready`
- `approval_status in (approved, auto_ready)`

导入成功后会：

- 写正式 wiki 页
- 更新 `smr_wiki_knowledge_index`
- 记录 `smr_wiki_import_execution`
- 将原 draft 标记为 `duplicate_source`
- 同步写 `task_registry_entry`

## 当前状态语义

### governance_status

- `ready`
- `review_required`
- `blocked`

### approval_status

- `auto_ready`
- `pending_manual_review`
- `approved`
- `rejected`
- `reopened`

## 当前最常见的 reason code

- `needs_human_judgement`
- `duplicate_source`
- `duplicate_thesis`
- `insufficient_evidence`
- `conflicts_with_latest_research`

## 当前阶段边界

- 现在已经能做：scan / review queue / review resolution / import
- 对象状态已经能追到 task registry
- 还没做：更复杂的 merge、批量 import、知识页 lint、治理后台
