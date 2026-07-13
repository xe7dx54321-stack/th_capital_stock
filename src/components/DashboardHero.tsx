/**
 * Hero 指标卡组件
 *
 * 展示平台整体覆盖规模的 6 个大数字指标卡
 *
 * 小白讲解：这个组件就是页面顶部的 6 个大卡片，
 * 显示最核心的"平台运营情况"——覆盖多少只股票、
 * 有多少新闻、有多少风险提示等。
 */

import { useEffect, useState } from "react";
import { Activity, Database, LineChart, Newspaper, Shield, Layers } from "lucide-react";
import type { DashboardData } from "../lib/api";

interface Props {
  data?: DashboardData;
  loading?: boolean;
}

// 数字从 0 动画递增到目标值的小工具
function useCountUp(target: number, duration = 800): number {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      setValue(Math.round(target * progress));
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

function MetricCard({
  label,
  value,
  sublabel,
  icon: Icon,
  delay,
}: {
  label: string;
  value: number;
  sublabel?: string;
  icon: React.ComponentType<{ className?: string }>;
  delay: number;
}) {
  const animated = useCountUp(value, 700 + delay * 100);
  return (
    <div
      className="card-base p-6 animate-fade-in"
      style={{ animationDelay: `${delay * 0.05}s` }}
    >
      <div className="flex items-start justify-between">
        <div className="text-text-muted text-xs uppercase tracking-wider">{label}</div>
        <Icon className="w-4 h-4 text-text-dim" />
      </div>
      <div
        className="mt-3 text-4xl font-light tracking-tight text-text animate-count"
        style={{ animationDelay: `${delay * 0.08}s` }}
      >
        {animated.toLocaleString()}
      </div>
      {sublabel && <div className="mt-1 text-xs text-text-dim">{sublabel}</div>}
    </div>
  );
}

export default function DashboardHero({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card-base p-6 h-32 animate-pulse bg-surface-2" />
        ))}
      </div>
    );
  }

  const summary = data.summary;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <MetricCard
        label="覆盖标的"
        value={summary.poolTotal}
        sublabel="纳入研究股票池"
        icon={Layers}
        delay={0}
      />
      <MetricCard
        label="A/H股"
        value={summary.ahCoverage}
        sublabel="有价格数据"
        icon={LineChart}
        delay={1}
      />
      <MetricCard
        label="美股"
        value={summary.usCoverage}
        sublabel="有价格数据"
        icon={Activity}
        delay={2}
      />
      <MetricCard
        label="有财务数据"
        value={summary.withFundamentals}
        sublabel="可计算评分"
        icon={Database}
        delay={3}
      />
      <MetricCard
        label="新闻抓取"
        value={summary.newsCount}
        sublabel="累计条数"
        icon={Newspaper}
        delay={4}
      />
      <MetricCard
        label="风险提示"
        value={summary.riskAlerts}
        sublabel="待关注事项"
        icon={Shield}
        delay={5}
      />
    </div>
  );
}
