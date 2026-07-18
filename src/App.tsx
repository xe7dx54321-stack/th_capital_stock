/** 新研究工作台为默认入口，上一版看板与个股详情按需加载。 */

import { lazy, Suspense, type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ResearchWorkbench from "./app/ResearchWorkbench";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const StockDetailPage = lazy(() => import("./pages/StockDetailPage"));
const AgentGrowthPage = lazy(() => import("./pages/AgentGrowthPage"));
const MappingAnalysisPage = lazy(() => import("./pages/MappingAnalysisPage"));

function LegacyPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<div className="route-loading">正在打开经典看板…</div>}>{children}</Suspense>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ResearchWorkbench />} />
        <Route path="/workbench" element={<ResearchWorkbench />} />
        <Route path="/agent" element={<AgentGrowthPage />} />
        <Route path="/legacy/dashboard" element={<LegacyPage><Dashboard /></LegacyPage>} />
        <Route path="/stock/:code" element={<LegacyPage><StockDetailPage /></LegacyPage>} />
        <Route path="/mapping" element={<LegacyPage><MappingAnalysisPage /></LegacyPage>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
