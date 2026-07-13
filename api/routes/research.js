import express from "express";

import { buildDiscoveries } from "../services/discovery-service.js";
import { buildDashboard, buildNewsDetail, buildNewsList } from "../services/report-service.js";
import { buildValueScores } from "../services/scoring-service.js";


export function createResearchRouter({ repository, cacheTtlMs = 5 * 60 * 1000 }) {
  const router = express.Router();
  const cache = new Map();

  const cached = (key, load) => {
    const now = Date.now();
    const entry = cache.get(key);
    if (entry && now - entry.timestamp < cacheTtlMs) return entry.data;
    const data = load();
    cache.set(key, { data, timestamp: now });
    return data;
  };

  router.get("/api/value-scores", (_req, res) => {
    try {
      if (!repository.hasValueScoreTables()) {
        res.json({ scores: [], updatedAt: new Date().toISOString() });
        return;
      }
      res.json(cached("value_scores", () => buildValueScores(repository.getValueScoreInputs())));
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/dashboard", (_req, res) => {
    try {
      res.json(cached("dashboard", () => buildDashboard(repository.getDashboardSnapshot())));
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/discoveries", (_req, res) => {
    try {
      res.json(cached("discoveries", () => buildDiscoveries(repository.getDiscoveryInputs())));
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/news", (_req, res) => {
    try {
      res.json(cached("news", () => buildNewsList(repository.listNews())));
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/news/:id", (req, res) => {
    try {
      const row = repository.getNewsById(req.params.id);
      if (!row) {
        res.status(404).json({ error: "新闻不存在" });
        return;
      }
      res.json(buildNewsDetail(row));
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  return router;
}
