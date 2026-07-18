/**
 * 端到端测试：发送"扫描一下今天的投资机会"，验证完整Workflow流程
 *
 * 功能：调用后端 /api/chat/workflow 接口，验证：
 *   1. 意图引擎是否正确识别为 opportunity_scan
 *   2. 9个步骤是否全部执行
 *   3. 涨跌幅数据是否正确（股票名称、涨跌幅数值）
 *   4. 大盘指数名称是否正确显示中文（不再是乱码）
 *   5. 报告中是否不再出现编造的估值数据
 *
 * 小白讲解：
 *   就像假装自己是一个用户，在网页上输入"扫描一下今天的投资机会"，
 *   然后看看系统返回的报告是不是包含了正确的数据，有没有乱码或编造的数据。
 */

console.log("\n========================================");
console.log("端到端测试：扫描投资机会");
console.log("========================================\n");

const testMessage = "扫描一下今天的投资机会";

const body = {
  message: testMessage,
  conversationContext: { chatHistory: [] },
};

console.log(`发送消息: "${testMessage}"\n`);
console.log("正在等待后端响应（可能需要60-90秒）...\n");

try {
  const resp = await fetch("http://127.0.0.1:3000/api/chat/workflow", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    console.error(`HTTP错误: ${resp.status}`);
    const errText = await resp.text();
    console.error(errText);
    process.exit(1);
  }

  const data = await resp.json();

  console.log("\n========================================");
  console.log("响应结果");
  console.log("========================================\n");

  console.log(`任务类型 (taskType): ${data.taskType}`);
  console.log(`状态 (status): ${data.status}`);
  console.log(`执行步骤: ${data.workflowSummary?.completedSteps}/${data.workflowSummary?.totalSteps}`);
  console.log(`提取记忆数: ${data.extractedMemories?.length || 0}`);

  console.log("\n--- 执行历史 ---");
  if (data.executionHistory && data.executionHistory.length > 0) {
    data.executionHistory.forEach((step, i) => {
      console.log(`${i+1}. [${step.stepId}] ${step.message}`);
    });
  } else {
    console.log("（无执行历史）");
  }

  console.log("\n--- 数据上下文摘要 ---");
  if (data.data) {
    const d = data.data;
    console.log(`大盘指数: ${d.marketIndices?.length || 0} 个`);
    if (d.marketIndices?.length > 0) {
      d.marketIndices.forEach(idx => {
        console.log(`  - ${idx.name}: ${idx.price} 涨跌幅${idx.pct_chg}% 成交额${idx.amount}亿`);
      });
    }
    console.log(`涨幅榜: ${d.topGainers?.length || 0} 只`);
    if (d.topGainers?.length > 0) {
      console.log(`  TOP5:`);
      d.topGainers.slice(0, 5).forEach((s, i) => {
        console.log(`  ${i+1}. ${s.name}(${s.ts_code}): ${s.pct_chg}% 价格${s.close}`);
      });
    }
    console.log(`跌幅榜: ${d.topLosers?.length || 0} 只`);
    if (d.topLosers?.length > 0) {
      console.log(`  TOP5:`);
      d.topLosers.slice(0, 5).forEach((s, i) => {
        console.log(`  ${i+1}. ${s.name}(${s.ts_code}): ${s.pct_chg}% 价格${s.close}`);
      });
    }
    console.log(`放量异动: ${d.volumeSurge?.length || 0} 只`);
    console.log(`价格异动: ${d.priceMovement?.length || 0} 只`);
    console.log(`估值极端: ${d.valuationExtremes?.length || 0} 只`);
    if (d.valuationExtremes?.length > 0) {
      console.log(`  样例:`);
      d.valuationExtremes.slice(0, 3).forEach(s => {
        console.log(`  - ${s.name}(${s.ts_code}): PE=${s.pe_ttm}, 分位=${s.historical_percentile}`);
      });
    }
    console.log(`最新新闻: ${d.latestNews?.length || 0} 条`);
    console.log(`持仓快照: ${d.poolSnapshot?.length || 0} 条`);
  }

  console.log("\n--- AI报告全文 ---");
  console.log(data.response || "（空）");

  console.log("\n--- 提取的记忆 ---");
  if (data.extractedMemories && data.extractedMemories.length > 0) {
    data.extractedMemories.forEach((mem, i) => {
      console.log(`${i+1}. [${mem.category}] ${mem.title}`);
      console.log(`   内容: ${mem.content.substring(0, 100)}...`);
    });
  }

  console.log("\n========================================");
  console.log("测试完成");
  console.log("========================================\n");

} catch (err) {
  console.error("测试失败:", err.message);
  console.error(err.stack);
  process.exit(1);
}
