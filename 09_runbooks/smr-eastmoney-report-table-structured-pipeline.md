# SMR 东方财富公开研报表格结构化快照 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股公开研报 PDF 文本到表格级结构化快照

---

## 1. 这条链做什么

这条链负责把已经落下来的：

- `research_article`（研报详情页）
- `research_pdf_text`（PDF 文本抽取）

继续加工成：

- `research_table_structured`（研报表格结构化快照）

它的定位不是替代 `research_structured`，而是补一层更细颗粒度的“表格级数据原料”。

当前会优先抽出：

- 表格年份轴
- 营收 / 净利润 / EPS / PE / ROE / DPS / 股息率
- 营收同比 / 净利润同比 / EPS 同比
- 评级动作
- 目标价
- 分析师姓名 / 执业证书 / 邮箱 / 电话

---

## 2. 前置依赖

必须先有：

```bash
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py
python3 08_scripts/wiki/extract_eastmoney_report_pdf_text.py
```

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_table_structured.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的构建：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_table_structured.py \
  --ts-code 300308.SZ \
  --ts-code 300394.SZ \
  --report-limit 2
```

强制重建：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_table_structured.py --force
```

---

## 4. 当前实现口径

- 以 `research_pdf_text` 原始文本为主来源
- 以 `research_article.search_item` 为锚点，辅助判断 EPS / PE 等字段布局
- 当前已支持 6 类常见 PDF 展开形态：
  - `header_segmented`
    - 表头在前，数值按段展开
  - `header_late_metric`
    - 表头主要指标在前，`P/E` 等晚到指标在尾部补列
  - `footer_year_blocks`
    - 年份和数值先出现，指标说明在表尾
  - `label_first`
    - 指标名集中在前，年份与数值随后按多种布局展开
  - `fragmented_year_blocks`
    - 年份块被 `资料来源 / 免责声明` 打断，但后续年份仍在下方继续展开
  - `inline_table_tag`
    - PDF 文本里保留了 `Table_Finance / Table_FinanceDetail` 内联表标签
- 输出统一 JSON 原件和可读 Markdown 快照

---

## 5. 结果如何进入系统

构建完成后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些结果会进入 `source_manifest`，类型仍然是：

- `external_source_snapshot`

但 `source_kind` 会新增：

- `research_table_structured`

---

## 6. 当前真实状态

截至 `2026-04-14`，当前机器已经真实落下：

- `research_table_structured = 8`

覆盖情况：

- `002281.SZ = 2`
- `300308.SZ = 2`
- `300394.SZ = 2`
- `300502.SZ = 2`

当前已命中的典型模式：

- `002281.SZ / AP202603301820858162`
  - `label_first`
  - 成功复原 `营收 / 净利润 / EPS / PE / ROE`
- `002281.SZ / AP202512291810626232`
  - `label_first`
  - 成功复原 `营收 / 净利润 / EPS / PE`
- `300308.SZ / AP202604091821077597`
  - `header_segmented`
  - 成功复原 `营收 / 净利润 / EPS / ROE / 营收同比 / 净利润同比`
- `300308.SZ / AP202604021820983821`
  - `header_late_metric`
  - 成功复原 `营收 / 净利润 / EPS / PE / 营收同比 / 净利润同比`
- `300394.SZ / AP202604081821063454`
  - `header_segmented`
  - 成功复原 `营收 / 净利润 / EPS / PE / 营收同比 / 净利润同比`
- `300394.SZ / AP202602101819851824`
  - `fragmented_year_blocks`
  - 成功复原 `营收 / 净利润 / EPS / PE / ROE / 毛利率 / 净利率`
- `300502.SZ / AP202602021819273624`
  - `footer_year_blocks`
  - 成功复原 `净利润 / EPS / DPS / 股息率`
  - `PE` 由 `search_item` 补齐
- `300502.SZ / AP202511011773273774`
  - `inline_table_tag`
  - 成功复原 `营收 / 净利润 / EPS / PE`

当前全量强制跑验证结果：

- `persisted = 8`
- `empty = 0`

说明当前关注池样本上的这层已经从“接上”推进到“可稳定落满”，但这不等于所有未来 PDF 都 100% 无异常。

---

## 7. 当前已知限制

- 当前关注池样本已经跑满，但新研报仍可能出现新的 PDF 变体
- 对“极散、跨页、多段错位、严重 OCR 污染”的 PDF 仍要继续补模式
- 事实校验、跨来源比对、机构观点去噪还没接上
- 这层已经接到趋势研究来源包和 `Latest External Research Snapshot`，但还没正式接到风控 / 日报主消费链

所以它现在的定位是：

- **先把公开研报从叙述型结构化推进到表格级结构化**
- **先把高价值预测字段和分析师信息抽出来**
- **先让后续推荐 / 风控 / 日报有更细颗粒度的输入可接**
- **后续继续补覆盖率、事实校验和更多来源对照**

---

## 8. 对 `opendataloader-pdf` 的结论

这轮参考了 `opendataloader-project/opendataloader-pdf` 的设计思路。

可借鉴点：

- 它强调把 PDF 变成 AI 可直接消费的结构化格式
- 它对表格、阅读顺序、Markdown / JSON 输出的思路是对的

当前不直接接入本项目运行时的原因：

- 这条主链已经有稳定的本地 `pdfminer.six` 文本抽取链
- 当前机器不适合为了这一层先改大块运行时依赖
- 现阶段先做轻量本地结构化层，推进速度更高、风险更低

当前策略：

- **先保持现有本地链稳定**
- **先把我们自己的表格级结构化跑通**
- **后续如果要再追更高精度表格恢复，再单独评估是否引入更重的解析栈**
