/**
 * 实时新闻路由 —— SSE 推送 + 新闻管理 + 重大新闻触发
 *
 * 功能：
 *   1. SSE 端点：前端通过 EventSource 连接，实时接收新新闻
 *   2. 新闻列表查询：支持按来源/重大程度/股票筛选
 *   3. 手动触发抓取：不等轮询，立即去拉一次新闻
 *   4. 统计信息：查看抓取量、去重率、重大新闻数
 *   5. 重大新闻触发器：检测到重大新闻后自动启动研究工作流
 *
 * 小白讲解：
 *   这个文件是"新闻控制台"——前端通过它实时收到新闻推送，
 *   也可以手动让系统去抓一次新闻，或者查看统计信息。
 *   如果检测到重大新闻（如涨停、并购），会自动启动研究工作流。
 */

import express from "express";
import { RealtimeNewsService } from "../services/realtime-news-service.js";
import { ResearchWorkflow } from "../services/research-workflow.js";

// 全局单例：整个应用共享一个实时新闻服务实例
let newsServiceInstance = null;

/**
 * 获取全局新闻服务实例（懒加载）
 * @returns {RealtimeNewsService}
 */
function getNewsService() {
  if (!newsServiceInstance) {
    newsServiceInstance = new RealtimeNewsService();
  }
  return newsServiceInstance;
}

/**
 * 创建实时新闻路由
 * @returns {express.Router}
 */
export function createRealtimeNewsRouter() {
  const router = express.Router();
  const newsService = getNewsService();

  // ========================================
  // SSE 端点：实时推送新闻到前端
  // ========================================

  // GET /api/realtime/news/stream
  // 前端通过 EventSource 连接此端点，实时接收新闻
  router.get("/api/realtime/news/stream", (req, res) => {
    // 设置 SSE 响应头
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "Access-Control-Allow-Origin": "*",
    });

    // 发送连接成功消息
    res.write(`event: connected\ndata: ${JSON.stringify({ message: "SSE 已连接", time: new Date().toISOString() })}\n\n`);

    // 监听新新闻事件
    const onNews = (news) => {
      res.write(`event: news\ndata: ${JSON.stringify(news)}\n\n`);
    };

    // 监听重大新闻事件
    const onBreaking = (news) => {
      res.write(`event: breaking\ndata: ${JSON.stringify(news)}\n\n`);
    };

    newsService.on("news", onNews);
    newsService.on("breaking", onBreaking);

    // 心跳：每 30 秒发一次，防止连接超时
    const heartbeat = setInterval(() => {
      res.write(`: heartbeat ${Date.now()}\n\n`);
    }, 30000);

    // 客户端断开连接时清理
    req.on("close", () => {
      clearInterval(heartbeat);
      newsService.off("news", onNews);
      newsService.off("breaking", onBreaking);
    });
  });

  // ========================================
  // 新闻查询接口
  // ========================================

  // GET /api/realtime/news
  // 查询最新新闻列表
  router.get("/api/realtime/news", (req, res) => {
    try {
      const { limit, breaking, source } = req.query;
      const news = newsService.getLatestNews({
        limit: parseInt(limit) || 50,
        breakingOnly: breaking === "true" || breaking === "1",
        source: source || null,
      });
      res.json({ success: true, count: news.length, news });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // GET /api/realtime/news/stats
  // 查看新闻服务统计信息
  router.get("/api/realtime/news/stats", (req, res) => {
    try {
      const stats = newsService.getStats();
      res.json({ success: true, stats });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // ========================================
  // 轮询控制接口
  // ========================================

  // POST /api/realtime/news/poll
  // 手动触发一次新闻抓取（不等轮询周期）
  router.post("/api/realtime/news/poll", async (req, res) => {
    try {
      const newNews = await newsService.pollOnce();
      res.json({
        success: true,
        fetched: newNews.length,
        news: newNews,
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/realtime/news/polling/start
  // 启动自动轮询
  router.post("/api/realtime/news/polling/start", (req, res) => {
    try {
      const interval = req.body?.interval ? parseInt(req.body.interval) * 1000 : undefined;
      if (interval && interval !== newsService.pollInterval) {
        newsService.stopPolling();
        newsService.pollInterval = interval;
      }
      newsService.startPolling();
      res.json({
        success: true,
        message: "轮询已启动",
        interval: newsService.pollInterval / 1000 + "秒",
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/realtime/news/polling/stop
  // 停止自动轮询
  router.post("/api/realtime/news/polling/stop", (req, res) => {
    try {
      newsService.stopPolling();
      res.json({ success: true, message: "轮询已停止" });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // GET /api/realtime/news/polling/status
  // 查看轮询状态
  router.get("/api/realtime/news/polling/status", (req, res) => {
    try {
      res.json({
        success: true,
        isPolling: newsService.isPolling,
        interval: newsService.pollInterval / 1000 + "秒",
        lastPollTime: newsService.stats.lastPollTime,
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // ========================================
  // 重大新闻触发器
  // ========================================

  // POST /api/realtime/news/trigger/enable
  // 启用重大新闻自动触发研究工作流
  router.post("/api/realtime/news/trigger/enable", (req, res) => {
    try {
      // 防止重复绑定
      if (newsService.listenerCount("breaking") > 1) {
        return res.json({ success: true, message: "触发器已启用" });
      }

      // 监听重大新闻事件，自动启动研究工作流
      newsService.on("breaking", async (news) => {
        console.log(`[触发器] 检测到重大新闻: ${news.title}`);
        // 如果新闻中提到了具体股票代码，自动启动研究工作流
        if (news.tickers?.length > 0) {
          for (const ticker of news.tickers) {
            console.log(`[触发器] 自动启动 ${ticker} 的研究工作流`);
            try {
              const workflow = new ResearchWorkflow(ticker);
              await workflow.execute();
              console.log(`[触发器] ${ticker} 研究工作流完成`);
            } catch (e) {
              console.error(`[触发器] ${ticker} 研究工作流失败:`, e.message);
            }
          }
        }
      });

      res.json({ success: true, message: "重大新闻触发器已启用" });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  return router;
}
