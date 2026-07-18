/**
 * LRU 缓存模块
 * 
 * 功能：
 *   1. 基于 LRU（最近最少使用）策略的内存缓存
 *   2. 支持 TTL（过期时间）
 *   3. 自动淘汰过期和不常用项
 *   4. 提供缓存命中率统计
 * 
 * 小白讲解：
 *   这个缓存就像一个"记事本"——最近用过的内容会放在最上面方便查找，
 *   不常用的会自动清理。还能设置"有效期"（TTL），过期的内容会自动失效。
 */

import crypto from "node:crypto";


/**
 * LRU 缓存类
 */
export class LRUCache {
  /**
   * 
   * @param {object} options 配置选项
   * @param {number} options.maxSize 最大条目数（默认 100）
   * @param {number} options.ttl 过期时间毫秒数（默认 5 分钟）
   * @param {boolean} options.enableStats 启用统计（默认 true）
   */
  constructor(options = {}) {
    const { maxSize = 100, ttl = 5 * 60 * 1000, enableStats = true } = options;
    this.maxSize = maxSize;
    this.ttl = ttl;
    this.cache = new Map();
    this.enableStats = enableStats;
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
      expirations: 0,
    };
  }

  /**
   * 生成缓存键
   * 
   * 参数：
   *   prefix: 键前缀
   *   data: 参与生成键的数据
   * 
   * 返回：
   *   string: 缓存键
   */
  static buildKey(prefix, data) {
    const json = JSON.stringify(data, Object.keys(data).sort());
    const hash = crypto.createHash("md5").update(json).digest("hex");
    return `${prefix}:${hash}`;
  }

  /**
   * 获取缓存
   * 
   * 参数：
   *   key: 缓存键
   * 
   * 返回：
   *   any: 缓存值（过期或不存在返回 undefined）
   */
  get(key) {
    const entry = this.cache.get(key);

    if (!entry) {
      if (this.enableStats) this.stats.misses += 1;
      return undefined;
    }

    const now = Date.now();
    if (now - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      if (this.enableStats) this.stats.expirations += 1;
      return undefined;
    }

    // 移动到最新（LRU 重新排序）
    this.cache.delete(key);
    this.cache.set(key, entry);

    if (this.enableStats) this.stats.hits += 1;
    return entry.value;
  }

  /**
   * 设置缓存
   * 
   * 参数：
   *   key: 缓存键
   *   value: 缓存值
   */
  set(key, value) {
    // 如果已存在，先删除（保证顺序）
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }

    // 如果超过最大容量，删除最旧的条目
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
      if (this.enableStats) this.stats.evictions += 1;
    }

    this.cache.set(key, {
      value,
      timestamp: Date.now(),
    });
  }

  /**
   * 删除缓存
   */
  delete(key) {
    return this.cache.delete(key);
  }

  /**
   * 清空缓存
   */
  clear() {
    this.cache.clear();
  }

  /**
   * 获取统计信息
   */
  getStats() {
    const total = this.stats.hits + this.stats.misses;
    return {
      ...this.stats,
      size: this.cache.size,
      hitRate: total > 0 ? (this.stats.hits / total) : 0,
    };
  }

  /**
   * 重置统计
   */
  resetStats() {
    this.stats = { hits: 0, misses: 0, evictions: 0, expirations: 0 };
  }
}


/**
 * 全局缓存管理器
 * 
 * 小白讲解：这是一个集中管理多个缓存的工具——为不同类型的数据创建不同的缓存。
 */
class CacheManager {
  constructor() {
    this.caches = new Map();
  }

  /**
   * 获取或创建缓存
   */
  getCache(name, options = {}) {
    if (!this.caches.has(name)) {
      this.caches.set(name, new LRUCache(options));
    }
    return this.caches.get(name);
  }

  /**
   * 清理指定缓存
   */
  clearCache(name) {
    const cache = this.caches.get(name);
    if (cache) cache.clear();
  }

  /**
   * 清理所有缓存
   */
  clearAll() {
    for (const cache of this.caches.values()) {
      cache.clear();
    }
  }

  /**
   * 获取所有缓存的统计
   */
  getAllStats() {
    const stats = {};
    for (const [name, cache] of this.caches.entries()) {
      stats[name] = cache.getStats();
    }
    return stats;
  }
}


export const globalCacheManager = new CacheManager();
