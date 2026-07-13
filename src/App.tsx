/**
 * 应用入口
 *
 * 配置 React Router：首页(Dashboard) + 标的详情页(StockDetailPage)
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import StockDetailPage from "./pages/StockDetailPage";
import ResearchWorkbench from "./app/ResearchWorkbench";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/stock/:code" element={<StockDetailPage />} />
        <Route path="/workbench" element={<ResearchWorkbench />} />
      </Routes>
    </BrowserRouter>
  );
}
