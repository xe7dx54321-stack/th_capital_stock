/**
 * 测试 extractStructuredMemories 记忆提取效果
 *
 * 功能：构造一份模拟的分析报告，调用 extractStructuredMemories
 *       看看分类是否正确，是否不再全是"分析结论"
 */

import { WorkflowEngine } from "../api/services/workflow-engine.js";

const engine = new WorkflowEngine();

const sampleReport = `# 📊 A股机会扫描报告

## 一、市场概览

今日A股整体呈现震荡上行态势，三大指数集体收涨。上证指数上涨1.23%，深证成指上涨1.56%，创业板指上涨2.15%。两市成交额合计2.66万亿元，较昨日放量约15%。市场情绪明显回暖，北向资金全天净买入85亿元。

## 二、涨幅榜分析

涨幅前十的股票中，AI算力板块占据4席，新能源板块3席，半导体2席，消费1席。云创退(301171.SZ)以+29.49%领涨，主要受益于AI算力需求爆发。米奥会展(300795.SZ) +20.05%，开润股份(300577.SZ) +19.98%。

## 三、跌幅榜分析

跌幅前十的股票主要集中在前期涨幅较大的题材股。龙鑫智能以-22.24%领跌，主要因前期炒作过度后的获利回吐。先河环保-20.03%，创业黑马-20.02%。

## 四、放量异动

今日放量异动股票共12只，主要集中在AI算力和新能源赛道。量比超过3倍的有5只，显示资金关注度显著提升。

重点关注标的：
- 中际旭创(300308.SZ)：量比2.8，成交额超50亿，机构资金持续流入
- 新易盛(300502.SZ)：量比3.2，突破前期平台，有望继续上行
- 天孚通信(300394.SZ)：量比2.5，800G光模块需求旺盛

## 五、估值极端标的

估值处于历史低位的标的：腾讯控股(00700.HK) PE 17.90，历史分位5.16%，具有较高的安全边际。

估值处于历史高位的标的：寒武纪(688256.SH) PE 285，历史分位92.3%，估值偏高需谨慎。

## 六、投资建议

建议关注AI算力和新能源两条主线，逢低布局业绩确定性高的龙头标的。仓位建议维持在6-7成，注意控制回撤风险。

## 七、风险提示

1. 海外市场波动风险：美联储加息预期升温可能导致全球市场动荡
2. 政策预期变化风险：行业监管政策调整可能影响相关板块估值
3. 个股业绩不及预期风险：中报披露期需警惕业绩雷
4. 地缘政治风险：国际关系紧张可能冲击市场情绪
`;

console.log("=" + "=".repeat(60));
console.log("测试 extractStructuredMemories 记忆提取");
console.log("=" + "=".repeat(60));

const memories = engine.extractStructuredMemories(sampleReport);

console.log(`\n提取到 ${memories.length} 条记忆：\n`);

memories.forEach((mem, i) => {
  console.log(`【${i+1}】[${mem.category}] ${mem.title}`);
  console.log(`    置信度: ${mem.confidence}`);
  console.log(`    内容: ${mem.content.substring(0, 80)}${mem.content.length > 80 ? "..." : ""}`);
  console.log();
});

// 统计分类分布
const categoryCount = {};
memories.forEach(m => {
  categoryCount[m.category] = (categoryCount[m.category] || 0) + 1;
});

console.log("=" + "=".repeat(60));
console.log("分类统计:");
for (const [cat, cnt] of Object.entries(categoryCount)) {
  console.log(`  ${cat}: ${cnt} 条`);
}
console.log("=" + "=".repeat(60));
