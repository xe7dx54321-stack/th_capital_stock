/**
 * A股-美股映射分析API路由
 *
 * 提供映射矩阵查询、海外评级影响分析、A股标的影响分析等接口
 */

import express from "express";
import { MappingAnalysisService } from "../services/mapping-analysis-service.js";

export function createMappingRouter() {
  const router = express.Router();
  const mappingService = new MappingAnalysisService();

  /**
   * GET /api/mapping/matrix
   * 获取完整的映射矩阵
   */
  router.get("/api/mapping/matrix", (_req, res) => {
    try {
      const matrix = mappingService.buildMappingMatrix();
      res.json({
        success: true,
        data: matrix,
        sectorCount: matrix.length,
      });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });

  /**
   * GET /api/mapping/sectors
   * 获取所有行业配置列表
   */
  router.get("/api/mapping/sectors", (_req, res) => {
    try {
      const sectors = mappingService.getAllSectors();
      res.json({
        success: true,
        data: sectors.map(s => ({
          sectorKey: s.sectorKey,
          sectorName: s.sectorName,
          mappingType: s.mappingType,
          usBenchmarkCount: s.usBenchmarks.length,
          targetCount: s.coreTargets.length,
          impactLevel: s.impactLevel,
          correlation: s.correlation,
        })),
      });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });

  /**
   * GET /api/mapping/impact
   * 分析海外评级变动对A股的影响
   * 
   * 参数：
   *   sectorKey: 行业Key（可选，不传则分析所有行业）
   */
  router.get("/api/mapping/impact", async (req, res) => {
    try {
      const { sectorKey } = req.query;
      const results = await mappingService.analyzeImpact(sectorKey);
      res.json({
        success: true,
        data: results,
        sectorCount: results.length,
      });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });

  /**
   * GET /api/mapping/target/:ticker
   * 分析单个A股标的的海外影响
   * 
   * 参数：
   *   ticker: A股标的代码（如688041.SH）
   */
  router.get("/api/mapping/target/:ticker", async (req, res) => {
    try {
      const { ticker } = req.params;
      const result = await mappingService.analyzeTargetImpact(ticker);
      res.json(result);
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });

  /**
   * GET /api/mapping/report
   * 生成完整的影响分析报告
   * 
   * 参数：
   *   sectorKey: 行业Key（可选，不传则生成全行业报告）
   */
  router.get("/api/mapping/report", async (req, res) => {
    try {
      const { sectorKey } = req.query;
      const results = await mappingService.analyzeImpact(sectorKey);
      const report = mappingService.generateImpactReport(results);
      res.json({
        success: true,
        report,
        sectorCount: results.length,
      });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });

  return router;
}