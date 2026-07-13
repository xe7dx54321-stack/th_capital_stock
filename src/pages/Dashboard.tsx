/**
 * 主 Dashboard 页面
 *
 * 组合了 Hero 指标卡、价值评分榜单、发现管线、新闻流
 * 点击股票行进入标的详情页
 */

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import {
  fetchDashboard,
  fetchValueScores,
  fetchDiscoveries,
  fetchNews,
  type DashboardData,
  type ValueScoreList,
  type DiscoveryList,
  type NewsList,
} from "../lib/api";
import DashboardHero from "../components/DashboardHero";
import ValueScoreTable from "../components/ValueScoreList";
import DiscoveryCards from "../components/DiscoveryCards";
import NewsFeed from "../components/NewsFeed";

interface DataState {
  dashboard?: DashboardData;
  scores?: ValueScoreList;
  discoveries?: DiscoveryList;
  news?: NewsList;
  loading: boolean;
  error?: string;
}

export default function Dashboard() {
  const [data, setData] = useState<DataState>({ loading: true });

  async function loadAll() {
    setData({ loading: true });
    try {
      const [dash, scores, discoveries, news] = await Promise.all([
        fetchDashboard(),
        fetchValueScores(),
        fetchDiscoveries(),
        fetchNews(),
      ]);
      setData({
        dashboard: dash,
        scores,
        discoveries,
        news,
        loading: false,
      });
    } catch (e) {
      setData({
        loading: false,
        error: (e as Error).message,
      });
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  return (
    <div className="min-h-screen bg-surface text-text">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-20 bg-surface/90 backdrop-blur-sm border-b border-surface-4">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-accent/20 flex items-center justify-center">
              <div className="w-3 h-3 bg-accent rounded-sm" />
            </div>
            <div>
              <div className="text-base font-medium tracking-tight">SMR 研究平台</div>
              <div className="text-xs text-text-dim">Systematic Market Research</div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="hidden md:block text-text-muted">
              {data.loading ? "加载中…" : `更新于 ${new Date().toLocaleString("zh-CN")}`}
            </div>
            <button
              onClick={loadAll}
              disabled={data.loading}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-surface-4 hover:border-accent hover:text-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={"w-3.5 h-3.5 " + (data.loading ? "animate-spin" : "")} />
              <span>刷新</span>
            </button>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        {/* 标题 */}
        <div className="animate-fade-in">
          <h1 className="text-3xl md:text-4xl font-light tracking-tight text-text">
            研究概览
          </h1>
          <p className="mt-3 text-sm text-text-muted max-w-2xl leading-relaxed">
            系统化的股票研究平台，基于财务因子、价格动量、主题相关性、新闻热度
            对覆盖标的进行多维度评分，并自动扫描市场发现新的研究线索。
          </p>
        </div>

        {/* 错误提示 */}
        {data.error && (
          <div className="card-base p-4 text-sm text-[#b74a2c] border-[#b74a2c]/30">
            数据加载失败：{data.error}
            <br />
            <span className="text-text-muted">
              请确认后端 API 服务已启动（运行 npm run start）。
            </span>
          </div>
        )}

        {/* Hero 指标卡 */}
        <section>
          <DashboardHero data={data.dashboard} loading={data.loading} />
        </section>

        {/* 价值评分榜单 */}
        <section>
          <ValueScoreTable scores={data.scores?.scores} loading={data.loading} />
        </section>

        {/* 发现管线 */}
        <section>
          <DiscoveryCards
            discoveries={data.discoveries?.discoveries}
            loading={data.loading}
          />
        </section>

        {/* 新闻流 */}
        <section>
          <NewsFeed
            items={data.news?.items}
            sources={data.news?.sources}
            loading={data.loading}
          />
        </section>

        {/* 页脚 */}
        <footer className="pt-8 border-t border-surface-4 text-center">
          <div className="text-xs text-text-dim">
            SMR 研究平台 · 本页面数据仅供研究参考，不构成投资建议
          </div>
        </footer>
      </main>
    </div>
  );
}
