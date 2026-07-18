/**
 * LRU 缓存模块单元测试
 */

import assert from "node:assert/strict";
import test from "node:test";

import { LRUCache, globalCacheManager } from "../../api/services/cache.js";


test("LRUCache - 设置和获取", () => {
  const cache = new LRUCache({ maxSize: 3, ttl: 1000, enableStats: false });
  cache.set("a", 1);
  cache.set("b", 2);

  assert.equal(cache.get("a"), 1, "应该能获取到 a");
  assert.equal(cache.get("b"), 2, "应该能获取到 b");
  assert.equal(cache.get("c"), undefined, "c 不存在应该返回 undefined");
});


test("LRUCache - LRU 淘汰策略", () => {
  const cache = new LRUCache({ maxSize: 3, ttl: 1000, enableStats: false });
  cache.set("a", 1);
  cache.set("b", 2);
  cache.set("c", 3);

  // 访问 a，让 a 成为最近使用
  cache.get("a");

  // 添加 d，应该淘汰 b（最久未访问）
  cache.set("d", 4);

  assert.equal(cache.get("a"), 1, "a 应该还在");
  assert.equal(cache.get("b"), undefined, "b 应该被淘汰");
  assert.equal(cache.get("c"), 3, "c 应该还在");
  assert.equal(cache.get("d"), 4, "d 应该存在");
});


test("LRUCache - TTL 过期", async () => {
  const cache = new LRUCache({ maxSize: 10, ttl: 50, enableStats: true });
  cache.set("a", 1);

  assert.equal(cache.get("a"), 1, "立即获取应该成功");

  await new Promise((resolve) => setTimeout(resolve, 80));

  assert.equal(cache.get("a"), undefined, "过期后应该返回 undefined");
  assert.equal(cache.getStats().expirations, 1, "应该记录一次过期");
});


test("LRUCache - 统计信息", () => {
  const cache = new LRUCache({ maxSize: 10, ttl: 1000, enableStats: true });
  cache.set("a", 1);

  cache.get("a");
  cache.get("a");
  cache.get("b"); // miss

  const stats = cache.getStats();
  assert.equal(stats.hits, 2, "应该有 2 次命中");
  assert.equal(stats.misses, 1, "应该有 1 次未命中");
  assert.equal(stats.hitRate, 2 / 3, "命中率应该是 2/3");
});


test("LRUCache - buildKey 工具函数", () => {
  const key1 = LRUCache.buildKey("test", { a: 1, b: 2 });
  const key2 = LRUCache.buildKey("test", { b: 2, a: 1 });
  assert.equal(key1, key2, "相同内容不同顺序应该生成相同键");

  const key3 = LRUCache.buildKey("test", { a: 1, b: 3 });
  assert.notEqual(key1, key3, "不同内容应该生成不同键");
});


test("LRUCache - 清空", () => {
  const cache = new LRUCache({ maxSize: 10, ttl: 1000, enableStats: false });
  cache.set("a", 1);
  cache.set("b", 2);

  cache.clear();
  assert.equal(cache.get("a"), undefined, "清空后应该获取不到");
});


test("globalCacheManager - 多缓存管理", () => {
  const cache1 = globalCacheManager.getCache("test-1");
  const cache2 = globalCacheManager.getCache("test-2");

  assert.notEqual(cache1, cache2, "应该返回不同的缓存实例");

  const sameCache = globalCacheManager.getCache("test-1");
  assert.equal(cache1, sameCache, "同名应该返回同一实例");

  const allStats = globalCacheManager.getAllStats();
  assert.ok(allStats["test-1"], "应该包含 test-1 统计");
  assert.ok(allStats["test-2"], "应该包含 test-2 统计");
});
