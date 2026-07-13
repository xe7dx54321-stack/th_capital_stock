import Database from "better-sqlite3";

import {
  buildPeerAvgForSector,
  getFundamentalsData,
  getValuationData,
} from "./research-readers.js";


export class ResearchRepository {
  constructor(dbPath) {
    this.dbPath = dbPath;
  }

  read(callback) {
    const db = new Database(this.dbPath, { readonly: true });
    try {
      return callback(db);
    } finally {
      db.close();
    }
  }

  hasTables(tableNames) {
    return this.read((db) => {
      const placeholders = tableNames.map(() => "?").join(", ");
      const rows = db.prepare(
        `SELECT name FROM sqlite_master WHERE type='table' AND name IN (${placeholders})`,
      ).all(...tableNames);
      return rows.length === tableNames.length;
    });
  }

  hasValueScoreTables() {
    return this.hasTables([
      "stock_pool_current", "factor_daily", "daily_bar", "us_daily_bar",
    ]);
  }

  getValueScoreInputs() {
    return this.read((db) => {
      const poolRows = db.prepare(`
        SELECT ts_code, sector, pool_type
        FROM (
          SELECT ts_code, sector, pool_type,
            ROW_NUMBER() OVER (
              PARTITION BY ts_code
              ORDER BY CASE pool_type
                WHEN 'portfolio_seed' THEN 1
                WHEN 'seed' THEN 2
                WHEN 'watchlist' THEN 3
                WHEN 'candidate' THEN 4
                WHEN 'recommended' THEN 5
                WHEN 'us_benchmark' THEN 6
                ELSE 9
              END
            ) AS rn
          FROM stock_pool_current
        ) sub
        WHERE rn = 1
      `).all();

      const factorsMap = new Map();
      for (const row of db.prepare(
        "SELECT ts_code, factor_name, factor_value FROM factor_daily",
      ).all()) {
        if (!factorsMap.has(row.ts_code)) factorsMap.set(row.ts_code, {});
        factorsMap.get(row.ts_code)[row.factor_name] = row.factor_value;
      }

      const pricesMap = new Map();
      for (const row of db.prepare(`
        SELECT ts_code, close FROM daily_bar
        WHERE (ts_code, trade_date) IN (
          SELECT ts_code, MAX(trade_date) FROM daily_bar GROUP BY ts_code
        )
      `).all()) pricesMap.set(row.ts_code, row.close);
      for (const row of db.prepare(`
        SELECT symbol, close FROM us_daily_bar
        WHERE (symbol, trade_date) IN (
          SELECT symbol, MAX(trade_date) FROM us_daily_bar GROUP BY symbol
        )
      `).all()) pricesMap.set(row.symbol, row.close);

      const priceHistMap = new Map();
      for (const row of db.prepare(
        "SELECT ts_code, trade_date, close FROM daily_bar ORDER BY ts_code, trade_date ASC",
      ).all()) {
        if (!priceHistMap.has(row.ts_code)) priceHistMap.set(row.ts_code, []);
        priceHistMap.get(row.ts_code).push({ close: row.close, date: row.trade_date });
      }
      for (const row of db.prepare(`
        SELECT symbol AS ts_code, trade_date, close
        FROM us_daily_bar ORDER BY symbol, trade_date ASC
      `).all()) {
        if (!priceHistMap.has(row.ts_code)) priceHistMap.set(row.ts_code, []);
        priceHistMap.get(row.ts_code).push({ close: row.close, date: row.trade_date });
      }

      return poolRows.map(({ ts_code: tsCode, sector }) => {
        const factorMap = factorsMap.get(tsCode) || {};
        return {
          tsCode,
          sector,
          factorMap,
          priceHistory: priceHistMap.get(tsCode) || [],
          latestPrice: pricesMap.has(tsCode) ? Number(pricesMap.get(tsCode)) : null,
          valuationData: getValuationData(db, tsCode, factorMap),
          fundamentalsData: getFundamentalsData(db, tsCode, factorMap),
          peerGroupData: buildPeerAvgForSector(db, tsCode, sector),
        };
      });
    });
  }

  getDashboardSnapshot() {
    return this.read((db) => {
      const tableExists = (name) => Boolean(db.prepare(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
      ).get(name));
      const count = (table, expression) => tableExists(table)
        ? db.prepare(`SELECT COUNT(${expression ? `DISTINCT ${expression}` : "*"}) AS cnt FROM ${table}`).get()?.cnt || 0
        : 0;
      return {
        poolTotal: count("stock_pool_current", "ts_code"),
        poolByType: tableExists("stock_pool_current") ? db.prepare(
          "SELECT pool_type AS type, COUNT(*) AS count FROM stock_pool_current GROUP BY pool_type ORDER BY count DESC",
        ).all() : [],
        ahCoverage: count("daily_bar", "ts_code"),
        usCoverage: count("us_daily_bar", "symbol"),
        withFundamentals: count("factor_daily", "ts_code"),
        newsCount: count("news_items"),
        riskAlerts: count("risk_alert"),
      };
    });
  }

  getDiscoveryInputs() {
    return this.read((db) => {
      const tableExists = (name) => Boolean(db.prepare(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
      ).get(name));
      return {
      poolRows: tableExists("stock_pool_current") ? db.prepare(
        "SELECT DISTINCT ts_code, sector FROM stock_pool_current",
      ).all() : [],
      newsRows: tableExists("news_items") ? db.prepare(`
        SELECT id, title, tickers_json, published_at, source_key, url
        FROM news_items
        WHERE tickers_json IS NOT NULL AND tickers_json != '[]'
        ORDER BY published_at DESC LIMIT 500
      `).all() : [],
      ahSpikes: tableExists("daily_bar") ? db.prepare(`
        SELECT ts_code, pct_chg, trade_date FROM daily_bar
        WHERE trade_date = (SELECT MAX(trade_date) FROM daily_bar)
          AND pct_chg IS NOT NULL AND pct_chg >= 5
        ORDER BY pct_chg DESC LIMIT 20
      `).all() : [],
      usSpikes: tableExists("us_daily_bar") ? db.prepare(`
        SELECT symbol, pct_chg, trade_date FROM us_daily_bar
        WHERE trade_date = (SELECT MAX(trade_date) FROM us_daily_bar)
          AND pct_chg IS NOT NULL AND pct_chg >= 5
        ORDER BY pct_chg DESC LIMIT 20
      `).all() : [],
    };
    });
  }

  listNews(limit = 50) {
    return this.read((db) => {
      const exists = db.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='news_items'").get();
      if (!exists) return [];
      return db.prepare(`
      SELECT id, title, body, source_key, source_name, published_at,
             tickers_json, url, credibility
      FROM news_items ORDER BY published_at DESC LIMIT ?
      `).all(limit);
    });
  }

  getNewsById(id) {
    return this.read((db) => {
      const exists = db.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='news_items'").get();
      if (!exists) return undefined;
      return db.prepare(`
      SELECT id, title, body, source_key, source_name, published_at,
             tickers_json, url, credibility, themes_json
      FROM news_items WHERE id=?
      `).get(id);
    });
  }
}
