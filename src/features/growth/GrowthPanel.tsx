/**
 * 成长系统面板组件
 * 
 * 功能：
 *   1. 展示用户研究成长概览
 *   2. 显示标的成长阶段分布
 *   3. 显示用户活动统计
 *   4. 显示决策统计
 *   5. 显示里程碑列表
 * 
 * 小白讲解：
 *   这个面板就像一个"成长仪表盘"——展示你的研究活动、标的追踪、
 *   决策表现等数据，让你看到自己一步步成长的轨迹。
 */

import { useState, useEffect } from "react";
import {
  TrendingUp,
  Activity,
  Target,
  Award,
  Loader2,
  BarChart3,
} from "lucide-react";


/**
 * 成长概览类型
 */
interface GrowthOverview {
  stockGrowth: { stage: string; stageLabel: string; count: number }[];
  totalActivities: number;
  activitiesByType: { activity_type: string; count: number }[];
  recent7DaysActivities: number;
  totalDecisions: number;
  decisionsWithOutcome: number;
  decisionsByType: { decision_type: string; count: number }[];
  avgPerformance: number | null;
}


/**
 * 里程碑类型
 */
interface Milestone {
  id: number;
  milestone: string;
  achievedAt: string;
  data: any;
}


/**
 * 获取成长概览
 */
async function fetchOverview(): Promise<GrowthOverview> {
  const response = await fetch("/api/growth/overview");
  if (!response.ok) throw new Error("获取成长概览失败");
  const data = await response.json();
  return data.overview;
}


/**
 * 获取里程碑列表
 */
async function fetchMilestones(): Promise<Milestone[]> {
  const response = await fetch("/api/growth/milestones?limit=20");
  if (!response.ok) throw new Error("获取里程碑失败");
  const data = await response.json();
  return data.milestones;
}


/**
 * 格式化数字
 */
function formatNumber(num: number | null | undefined): string {
  if (num == null) return "—";
  return num.toLocaleString();
}


/**
 * 概览卡片组件
 */
function StatCard({ icon: Icon, label, value, color }: {
  icon: any;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <article className="growth-stat-card">
      <span className={`growth-stat-icon ${color}`}><Icon size={16} /></span>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
      </div>
    </article>
  );
}


/**
 * 阶段分布组件
 */
function StageDistribution({ stages }: { stages: GrowthOverview["stockGrowth"] }) {
  if (!stages || stages.length === 0) {
    return <p className="growth-empty">暂无标的追踪数据</p>;
  }

  const total = stages.reduce((sum, s) => sum + s.count, 0);

  return (
    <div className="growth-stages">
      {stages.map((s) => {
        const pct = total > 0 ? (s.count / total) * 100 : 0;
        return (
          <div key={s.stage} className="growth-stage-row">
            <div className="growth-stage-label">
              <span>{s.stageLabel}</span>
              <span className="growth-stage-count">{s.count}</span>
            </div>
            <div className="growth-stage-bar">
              <div
                className={`growth-stage-fill stage-${s.stage}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}


/**
 * 活动列表组件
 */
function ActivityList({ activities }: { activities: GrowthOverview["activitiesByType"] }) {
  if (!activities || activities.length === 0) {
    return <p className="growth-empty">暂无活动记录</p>;
  }

  return (
    <ul className="growth-activity-list">
      {activities.map((a, i) => (
        <li key={i}>
          <span className="growth-activity-type">{a.activity_type}</span>
          <span className="growth-activity-count">{a.count}</span>
        </li>
      ))}
    </ul>
  );
}


/**
 * 里程碑列表组件
 */
function MilestoneList({ milestones }: { milestones: Milestone[] }) {
  if (milestones.length === 0) {
    return <p className="growth-empty">暂无里程碑记录</p>;
  }

  return (
    <ul className="growth-milestone-list">
      {milestones.map((m) => (
        <li key={m.id}>
          <Award size={14} className="text-amber-500" />
          <div>
            <p className="growth-milestone-text">{m.milestone}</p>
            <small>{new Date(m.achievedAt).toLocaleString("zh-CN")}</small>
          </div>
        </li>
      ))}
    </ul>
  );
}


/**
 * 主组件
 */
export default function GrowthPanel() {
  const [overview, setOverview] = useState<GrowthOverview | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchOverview(), fetchMilestones()])
      .then(([ov, ms]) => {
        setOverview(ov);
        setMilestones(ms);
      })
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="growth-panel-loading">
        <Loader2 size={20} className="animate-spin" />
        <span>加载成长数据...</span>
      </div>
    );
  }

  if (!overview) {
    return <div className="growth-panel-error">加载成长数据失败</div>;
  }

  return (
    <div className="growth-panel">
      <div className="growth-panel-header">
        <TrendingUp size={18} />
        <h2>成长系统</h2>
      </div>

      {/* 核心统计 */}
      <div className="growth-stat-grid">
        <StatCard
          icon={Activity}
          label="总活动数"
          value={formatNumber(overview.totalActivities)}
          color="is-blue"
        />
        <StatCard
          icon={Target}
          label="追踪标的"
          value={formatNumber(overview.stockGrowth.reduce((s, x) => s + x.count, 0))}
          color="is-green"
        />
        <StatCard
          icon={BarChart3}
          label="决策数"
          value={formatNumber(overview.totalDecisions)}
          color="is-amber"
        />
        <StatCard
          icon={Award}
          label="近 7 天活动"
          value={formatNumber(overview.recent7DaysActivities)}
          color="is-purple"
        />
      </div>

      {/* 标的阶段分布 */}
      <section className="growth-section">
        <h3>📊 标的阶段分布</h3>
        <StageDistribution stages={overview.stockGrowth} />
      </section>

      {/* 活动统计 */}
      <section className="growth-section">
        <h3>📈 活动类型</h3>
        <ActivityList activities={overview.activitiesByType} />
      </section>

      {/* 里程碑 */}
      <section className="growth-section">
        <h3>🏆 里程碑</h3>
        <MilestoneList milestones={milestones} />
      </section>

      {overview.avgPerformance != null && (
        <section className="growth-section">
          <h3>💯 决策表现</h3>
          <div className="growth-perf">
            <strong>{overview.avgPerformance}%</strong>
            <small>平均收益率（{overview.decisionsWithOutcome} 个有结果）</small>
          </div>
        </section>
      )}
    </div>
  );
}
