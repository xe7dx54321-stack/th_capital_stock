/**
 * 测试 daily_bar 表缺失时的容错能力
 *
 * 功能：用 MVP 数据库（没有 daily_bar 表）测试所有查 daily_bar 的方法，
 *       验证它们都返回空数组而不是抛异常。
 */

import { MarketDataService } from "../api/services/market-data-service.js";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// 用 MVP 数据库（没有 daily_bar 表）
const mvpDbPath = path.resolve(__dirname, "..", "01_data", "db", "smr.db");

console.log("=" + "=".repeat(60));
console.log("测试 daily_bar 表缺失时的容错能力");
console.log("数据库路径:", mvpDbPath);
console.log("=" + "=".repeat(60) + "\n");

let service;
let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    const result = fn();
    console.log(`✓ ${name}: 通过（返回 ${Array.isArray(result) ? result.length + " 条" : result ? "对象" : "null"}）`);
    passed++;
  } catch (err) {
    console.log(`✗ ${name}: 失败（${err.message}）`);
    failed++;
  }
}

try {
  service = new MarketDataService(mvpDbPath);
  console.log(`hasDailyBar 标记: ${service.hasDailyBar}\n`);

  // 测试所有查 daily_bar 的方法
  test("resolveEntity", () => service.resolveEntity("300308.SZ"));
  test("getDailyBars", () => service.getDailyBars("300308.SZ", 5));
  test("getAllStocksWithData", () => service.getAllStocksWithData());
  test("getLatestMarketSnapshot", () => service.getLatestMarketSnapshot());
  test("getTopGainers", () => service.getTopGainers(10));
  test("getTopLosers", () => service.getTopLosers(10));
  test("getVolumeSurge", () => service.getVolumeSurge(10, 2));
  test("getPriceMovement", () => service.getPriceMovement(5, 10));
  test("getPoolSnapshot", () => service.getPoolSnapshot());

  // 测试不查 daily_bar 的方法（确保没有被破坏）
  console.log("\n--- 验证其他方法仍正常工作 ---");
  test("getValuation", () => service.getValuation("00700.HK"));
  test("getValuationExtremes", () => service.getValuationExtremes(5));
  test("getLatestNews", () => service.getLatestNews(3));
  test("getRecentFundamentals", () => service.getRecentFundamentals(3));

} catch (err) {
  console.error("初始化失败:", err.message);
  failed++;
} finally {
  if (service) service.close();
}

console.log("\n" + "=".repeat(60));
console.log(`测试结果: ${passed} 通过, ${failed} 失败`);
console.log("=" + "=".repeat(60));

process.exit(failed > 0 ? 1 : 0);
