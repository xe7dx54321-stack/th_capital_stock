import Database from "better-sqlite3";


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
