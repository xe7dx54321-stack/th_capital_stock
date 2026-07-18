/**
 * 测试涨跌幅数据API
 *
 * 功能：直接调用新浪财经涨跌幅API，验证返回的数据是否为当日实时数据
 * 目的：排查用户反馈"涨跌幅数据全都不对"的根本原因
 */

const today = new Date().toISOString().split("T")[0];
const weekday = new Date().toLocaleDateString("zh-CN", { weekday: "long" });
console.log(`\n========================================`);
console.log(`当前日期: ${today} (${weekday})`);
console.log(`========================================\n`);

// ========== 测试1：新浪涨跌幅API ==========
async function testSinaRank() {
  console.log(`【测试1】新浪财经涨跌幅榜API\n`);
  const url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=10&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=sort";

  try {
    const resp = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.sina.com.cn/",
      },
    });

    if (!resp.ok) {
      console.error(`HTTP错误: ${resp.status}`);
      return;
    }

    const data = await resp.json();
    console.log(`✓ 成功获取 ${data.length} 条数据\n`);
    console.log(`涨幅榜TOP 10：\n`);
    console.log(`${"序号".padEnd(4)} ${"代码".padEnd(10)} ${"名称".padEnd(10)} ${"涨跌幅(%)".padEnd(10)} ${"现价".padEnd(10)} ${"成交额(万)".padEnd(12)}`);
    console.log("-".repeat(80));

    data.forEach((item, i) => {
      const code = item.code || "";
      const symbol = item.symbol || "";
      const name = item.name || "";
      const pct = item.changepercent !== undefined ? item.changepercent : "N/A";
      const trade = item.trade || "N/A";
      const amount = item.amount ? (item.amount / 10000).toFixed(2) : "N/A";
      console.log(`${String(i+1).padEnd(4)} ${code.padEnd(10)} ${name.padEnd(10)} ${String(pct).padEnd(10)} ${String(trade).padEnd(10)} ${String(amount).padEnd(12)}`);
    });

    // 关键字段检查
    console.log(`\n📋 数据字段检查：`);
    const sample = data[0];
    console.log(`  - code: ${sample.code}`);
    console.log(`  - symbol: ${sample.symbol}`);
    console.log(`  - name: ${sample.name}`);
    console.log(`  - changepercent: ${sample.changepercent}（涨跌幅，单位%）`);
    console.log(`  - trade: ${sample.trade}（现价）`);
    console.log(`  - amount: ${sample.amount}（成交额，单位元）`);
    console.log(`  - volume: ${sample.volume}（成交量，单位股）`);
    console.log(`  - mktcap: ${sample.mktcap}（总市值，单位万元）`);
    console.log(`  - per: ${sample.per}（市盈率）`);
    console.log(`  - turnoverratio: ${sample.turnoverratio}（换手率）`);
  } catch (err) {
    console.error(`✗ 失败: ${err.message}`);
  }
}

// ========== 测试2：新浪大盘指数API（含GBK编码） ==========
async function testSinaIndices() {
  console.log(`\n【测试2】新浪大盘指数API（GBK编码）\n`);
  const indices = [
    { code: "s_sh000001", name: "上证综指" },
    { code: "s_sz399001", name: "深证成指" },
    { code: "s_sz399006", name: "创业板指" },
  ];
  const codes = indices.map(i => i.code).join(",");
  const url = `http://hq.sinajs.cn/list=${codes}`;

  try {
    const resp = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn/",
      },
    });

    const buffer = await resp.arrayBuffer();
    let text;
    try {
      const decoder = new TextDecoder("gbk");
      text = decoder.decode(buffer);
    } catch (e) {
      text = new TextDecoder("utf-8").decode(buffer);
    }

    console.log(`原始返回（已解码）：\n${text}\n`);

    const lines = text.split("\n").filter(l => l.trim());
    for (const line of lines) {
      const eq = line.indexOf("=");
      if (eq < 0) continue;
      const val = line.substring(eq + 1).replace(/^"|"$/g, "").trim();
      const parts = val.split(",");
      if (parts.length < 6) continue;

      // 大盘指数简化格式：名称,昨收,今开,最新价,最高,最低,成交量(手),成交额(元)
      console.log(`指数: ${parts[0]}`);
      console.log(`  最新价: ${parts[1]}`);
      console.log(`  涨跌幅: ${parts[3]}%`);
      console.log(`  成交量(手): ${parts[5]}`);
      console.log(`  成交额(元): ${parts[6]}`);
      console.log(`  成交额(亿元): ${parts[6] ? (parseFloat(parts[6]) / 100000000).toFixed(2) : "N/A"}`);
      console.log();
    }
  } catch (err) {
    console.error(`✗ 失败: ${err.message}`);
  }
}

// ========== 测试3：腾讯财经单股实时API ==========
async function testTencentStock() {
  console.log(`\n【测试3】腾讯财经单股实时API\n`);
  const url = "http://qt.gtimg.cn/q=sh600519,sz000001,sz300750";

  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0" },
    });
    const text = await resp.text();
    const lines = text.split(";").filter(l => l.trim());

    for (const line of lines) {
      const eq = line.indexOf("=");
      if (eq < 0) continue;
      const val = line.substring(eq + 1).replace(/^"|"$/g, "");
      const parts = val.split("~");
      if (parts.length < 50) continue;

      console.log(`股票: ${parts[1]} (${parts[2]})`);
      console.log(`  最新价: ${parts[3]}`);
      console.log(`  涨跌幅: ${parts[32]}%`);
      console.log(`  成交额(万): ${parts[37]}`);
      console.log(`  总市值(亿): ${parts[44]}`);
      console.log();
    }
  } catch (err) {
    console.error(`✗ 失败: ${err.message}`);
  }
}

// 运行所有测试
await testSinaRank();
await testSinaIndices();
await testTencentStock();

console.log(`\n========================================`);
console.log(`测试完成`);
console.log(`========================================\n`);
