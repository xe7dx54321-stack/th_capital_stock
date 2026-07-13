/**
 * 后端 API 服务器
 * 读取 SQLite 数据库，提供 JSON API，为前端提供静态文件服务
 */

import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import { loadAllPhaseConfigs, getSchedulerPhaseRuns } from "../08_scripts/lib/phase_status_loader.js";
import { ResearchRepository } from "./repositories/research-repository.js";
import { createResearchRouter } from "./routes/research.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = process.env.SMR_DB_PATH
  ? path.resolve(process.env.SMR_DB_PATH)
  : path.resolve(__dirname, "..", "01_data", "db", "smr.db");

const app = express();

app.use(cors());
app.use(express.json());

const researchRepository = new ResearchRepository(DB_PATH);
app.use(createResearchRouter({ repository: researchRepository }));

// ============================================================
// 缓存
// ============================================================
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000;

function cached(key, fn) {
  const now = Date.now();
  const cached_item = cache.get(key);
  if (cached_item && now - cached_item.timestamp < CACHE_TTL) {
    return cached_item.data;
  }
  const data = fn();
  cache.set(key, { data, timestamp: now });
  return data;
}

// ============================================================
// API: GET /api/health
// ============================================================
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// ============================================================
// API: GET /api/phases - 研究流程状态
// 后端：从 config/phase*.json 读取 Phase 定义，
//       从 10_logs/ 读取运行历史，判断各 Phase 当前状态
// 前端暂不展示（PhaseTimeline 组件已禁用），但系统内部需要了解状态
// ============================================================
app.get("/api/phases", (_req, res) => {
  try {
    const data = cached("phases", () => {
      const phases = loadAllPhaseConfigs();
      const runInfo = getSchedulerPhaseRuns();

      // Phase ID → 中文名称映射
      const phaseNameMap = {
        phase100: "持续生产流水线",
        phase101: "实盘交易就绪",
        phase102: "回测就绪",
        phase103: "风控就绪",
        phase104: "人工审批就绪",
        phase105: "熔断就绪",
        phase106: "就绪集成",
        phase107: "模拟交易边界",
        phase108: "执行就绪",
        phase109: "操作员就绪",
        phase110: "操作员分配",
        phase111: "个人 Owner 模式",
        phase112: "机会雷达",
        phase113: "交叉评分",
        phase114: "催化剂检测",
        phase115: "候选看板",
        phase116: "研究循环",
        phase117: "每日主循环",
        phase118: "系统健康检查",
        phase119: "持续改进",
        phase120: "项目收尾",
        phase121: "外部源扩展",
        phase122: "每日研究简报",
        phase123: "反馈记忆",
        phase124: "决策日志",
        phase125: "结果追踪",
        phase126: "信号有效性评估",
        phase127: "主循环收尾",
        phase128: "外部源探测",
        phase129: "官方源兜底",
        phase130: "CNINFO 决议",
        phase131: "替代源集成",
        phase132: "估值硬化",
        phase133: "季节分析",
        phase134: "个人研究控制台",
        phase135: "Owner 反馈集成",
        phase136: "深度研究工作流",
        phase137: "深度研究执行",
        phase138: "研究论题库",
        phase139: "定时本地运行",
        phase140: "系统硬化",
        phase141: "HTML 看板",
        phase142: "标的详情页",
        phase143: "交叉链接导航",
        phase144: "反馈工作流",
        phase145: "Agent 编排",
        phase146: "Agent 记忆队列",
        phase147: "标的入池",
        phase148: "候选激活",
        phase149: "Agent 指令",
        phase150: "观察池分层",
        phase151: "自动发现管线",
        phase152: "候选入池评分",
        phase153: "候选入池评审",
        phase154: "多 Agent 研究循环",
        phase155: "Agent 调度",
        phase156: "Owner 激活评审",
        phase157: "决策输入工作流",
        phase158: "决策 UI",
        phase159: "决策提交",
        phase160: "决策示例包",
        phase161: "决策反馈 UI",
        phase162: "网络候选充实",
        phase163: "候选充实执行",
        phase164: "候选充实控制台",
        phase165: "就绪修复研究包",
        phase166: "实时证据填充",
        phase167: "决策评审包控制台",
        phase168: "决策提交",
        phase169: "决策撰写指南",
        phase170: "输入验证",
        phase171: "Owner 最终确认",
        phase172: "正式覆盖申请",
        phase173: "Owner 决策准备",
        phase174: "申请后覆盖控制台",
        phase175: "研究任务运行器",
      };

      // 判断状态：最近 24h 内运行 = active / 24h-7天 = completed / 从未运行 = pending
      const now = Date.now();
      const DAY_MS = 24 * 60 * 60 * 1000;
      const WEEK_MS = 7 * DAY_MS;

      const result = phases.map((p) => {
        const num = parseInt(p.phase_id.replace("phase", ""));
        const name = phaseNameMap[p.phase_id] || p.phase_id.replace("phase", "Phase ");
        const strategy = p.strategy.replace(/_/g, " ");
        const run = runInfo[num];

        let status = "pending";
        let pct = 0;
        let lastRunAt = null;

        if (run) {
          lastRunAt = run.latest;
          const runAge = now - new Date(run.latest).getTime();
          if (runAge < DAY_MS) {
            status = "active";
            pct = 100;
          } else if (runAge < WEEK_MS) {
            status = "completed";
            pct = 80;
          } else {
            status = "completed";
            pct = 60;
          }
        }

        return {
          phaseId: p.phase_id,
          phaseName: name,
          description: strategy,
          status,
          taskCount: 1,
          completedCount: pct === 100 ? 1 : 0,
          lastRunAt,
          runCount: run?.count || 0,
        };
      });

      // 只返回 phase100-175
      const mainPhases = result.filter((p) => {
        const n = parseInt(p.phaseId.replace("phase", ""));
        return n >= 100 && n <= 175;
      });

      return { phases: mainPhases, updatedAt: new Date().toISOString() };
    });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================================
// 静态文件服务
// ============================================================
const distDir = path.resolve(__dirname, "..", "dist");
app.use(express.static(distDir));
app.use((req, res, next) => {
  if (req.path.startsWith("/api/")) return next();
  if (req.method !== "GET") return next();
  res.sendFile(path.join(distDir, "index.html"));
});

export { app as legacyApp };
