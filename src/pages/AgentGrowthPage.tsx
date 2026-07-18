/**
 * Agent 与成长系统页面
 * 
 * 功能：整合展示 Agent 工具箱和成长系统面板
 */

import { useState } from "react";
import { Wrench, TrendingUp } from "lucide-react";
import AgentPanel from "../features/agent/AgentPanel";
import GrowthPanel from "../features/growth/GrowthPanel";
import "./agent-growth.css";


/**
 * 主页面
 */
export default function AgentGrowthPage() {
  const [activeTab, setActiveTab] = useState<"agent" | "growth">("agent");

  return (
    <main className="agent-growth-page">
      <header className="agent-growth-header">
        <h1>🤖 Agent 与成长系统</h1>
        <p>Knevo 风格的智能工作流：让 AI 帮你做研究，让成长看得见</p>
      </header>

      <div className="agent-growth-tabs">
        <button
          className={activeTab === "agent" ? "is-active" : ""}
          onClick={() => setActiveTab("agent")}
        >
          <Wrench size={14} /> Agent 工具箱
        </button>
        <button
          className={activeTab === "growth" ? "is-active" : ""}
          onClick={() => setActiveTab("growth")}
        >
          <TrendingUp size={14} /> 成长系统
        </button>
      </div>

      <div className="agent-growth-content">
        {activeTab === "agent" ? <AgentPanel /> : <GrowthPanel />}
      </div>
    </main>
  );
}
