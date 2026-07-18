/**
 * A股-美股映射分析页面
 *
 * 功能：
 *   1. 展示映射矩阵（行业配置）
 *   2. 展示海外评级影响分析结果
 *   3. 展示A股标的影响建议
 *   4. 生成完整影响分析报告
 */

import { useState, useEffect } from "react";
import {
  fetchMappingMatrix,
  fetchMappingImpact,
  fetchMappingReport,
  SectorMapping,
  SectorImpactAnalysis,
  MappingMatrixResponse,
  ImpactAnalysisResponse,
} from "../lib/api";

function getSignalEmoji(signal: string): string {
  switch (signal) {
    case "bullish":
      return "🟢";
    case "slightly_bullish":
      return "🟡";
    case "bearish":
      return "🔴";
    case "slightly_bearish":
      return "🟠";
    default:
      return "⚪";
  }
}

function getSignalText(signal: string): string {
  switch (signal) {
    case "bullish":
      return "强烈看多";
    case "slightly_bullish":
      return "小幅看多";
    case "bearish":
      return "强烈看空";
    case "slightly_bearish":
      return "小幅看空";
    default:
      return "中性";
  }
}

function getDirectionEmoji(direction: string): string {
  switch (direction) {
    case "positive":
      return "⬆️";
    case "negative":
      return "⬇️";
    default:
      return "➡️";
  }
}

function getImpactLevelStyle(level: string): string {
  switch (level) {
    case "high":
      return "bg-red-100 text-red-700";
    case "medium":
      return "bg-yellow-100 text-yellow-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
}

function getImpactLevelEmoji(level: string): string {
  switch (level) {
    case "high":
      return "🚨";
    case "medium":
      return "⚠️";
    default:
      return "ℹ️";
  }
}

export default function MappingAnalysisPage() {
  const [matrix, setMatrix] = useState<MappingMatrixResponse | null>(null);
  const [impactAnalysis, setImpactAnalysis] = useState<ImpactAnalysisResponse | null>(null);
  const [report, setReport] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"matrix" | "impact" | "report">("impact");
  const [selectedSector, setSelectedSector] = useState<string | null>(null);

  useEffect(() => {
    loadMatrix();
  }, []);

  async function loadMatrix() {
    setLoading(true);
    try {
      const data = await fetchMappingMatrix();
      setMatrix(data);
    } catch (e) {
      console.error("加载映射矩阵失败:", e);
    } finally {
      setLoading(false);
    }
  }

  async function loadImpactAnalysis(sectorKey?: string) {
    setLoading(true);
    setSelectedSector(sectorKey || null);
    try {
      const data = await fetchMappingImpact(sectorKey);
      setImpactAnalysis(data);
    } catch (e) {
      console.error("加载影响分析失败:", e);
    } finally {
      setLoading(false);
    }
  }

  async function loadReport(sectorKey?: string) {
    setLoading(true);
    try {
      const data = await fetchMappingReport(sectorKey);
      setReport(data.report);
    } catch (e) {
      console.error("加载报告失败:", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            🌍 A股-美股映射分析
          </h1>
          <p className="mt-2 text-gray-600">
            追踪海外评级变动，分析对A股相关板块和标的的影响传导
          </p>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={() => {
              setActiveTab("matrix");
            }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "matrix"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-100"
            }`}
          >
            📊 映射矩阵
          </button>
          <button
            onClick={() => {
              setActiveTab("impact");
              loadImpactAnalysis();
            }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "impact"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-100"
            }`}
          >
            📈 影响分析
          </button>
          <button
            onClick={() => {
              setActiveTab("report");
              loadReport();
            }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "report"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-100"
            }`}
          >
            📋 完整报告
          </button>
        </div>

        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!loading && activeTab === "matrix" && (
          <div className="space-y-6">
            {matrix?.data.map((sector: SectorMapping) => (
              <div
                key={sector.sectorKey}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
              >
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{sector.sectorName}</h3>
                      <p className="mt-1 text-sm text-gray-500">{sector.description}</p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${getImpactLevelStyle(
                        sector.impactLevel,
                      )}`}
                    >
                      {getImpactLevelEmoji(sector.impactLevel)} {sector.impactLevel}
                    </span>
                  </div>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-3">🇺🇸 美股对标公司</h4>
                      <div className="flex flex-wrap gap-2">
                        {sector.usBenchmarks.map((symbol) => (
                          <span
                            key={symbol}
                            className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium"
                          >
                            {symbol}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-3">🇨🇳 A股核心标的</h4>
                      <div className="flex flex-wrap gap-2">
                        {sector.coreTargets.map((target) => (
                          <span
                            key={target}
                            className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm font-medium"
                          >
                            {target}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-gray-500">
                        <strong>映射类型:</strong> {sector.mappingTypeName}
                      </span>
                      <span className="text-gray-500">
                        <strong>相关性:</strong> {(sector.correlation * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-600">{sector.mappingDescription}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && activeTab === "impact" && (
          <div className="space-y-6">
            <div className="flex flex-wrap gap-2 mb-6">
              <button
                onClick={() => loadImpactAnalysis()}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  !selectedSector
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
                }`}
              >
                全部行业
              </button>
              {matrix?.data.map((sector: SectorMapping) => (
                <button
                  key={sector.sectorKey}
                  onClick={() => loadImpactAnalysis(sector.sectorKey)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    selectedSector === sector.sectorKey
                      ? "bg-blue-600 text-white"
                      : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
                  }`}
                >
                  {sector.sectorName}
                </button>
              ))}
            </div>

            {impactAnalysis?.data.map((sector: SectorImpactAnalysis) => (
              <div
                key={sector.sectorKey}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
              >
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {getSignalEmoji(sector.overallSignal)} {sector.sectorName}
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">{sector.mappingDescription}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xl font-bold text-gray-900">
                        {getSignalText(sector.overallSignal)}
                      </span>
                      <div className="text-sm text-gray-500">
                        置信度: {sector.overallConfidence}%
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">🇺🇸 海外对标评级</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="px-4 py-2 text-left font-medium text-gray-600">标的</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-600">分析师</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-600">Buy</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-600">Hold</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-600">Sell</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-600">Buy%</th>
                            <th className="px-4 py-2 text-center font-medium text-gray-600">信号</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sector.usBenchmarks.map((benchmark) => (
                            <tr key={benchmark.symbol} className="border-t border-gray-100">
                              <td className="px-4 py-3 font-medium text-gray-900">
                                {benchmark.symbol}
                              </td>
                              <td className="px-4 py-3 text-right text-gray-600">
                                {benchmark.totalAnalysts}
                              </td>
                              <td className="px-4 py-3 text-right text-green-600">
                                {benchmark.buy}
                              </td>
                              <td className="px-4 py-3 text-right text-yellow-600">
                                {benchmark.hold}
                              </td>
                              <td className="px-4 py-3 text-right text-red-600">
                                {benchmark.sell}
                              </td>
                              <td className="px-4 py-3 text-right text-gray-600">
                                {benchmark.buyRatio}%
                              </td>
                              <td className="px-4 py-3 text-center">
                                <span className="text-xl">{getSignalEmoji(benchmark.signal)}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">📈 A股影响建议</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="px-4 py-2 text-left font-medium text-gray-600">
                              A股标的
                            </th>
                            <th className="px-4 py-2 text-center font-medium text-gray-600">
                              影响方向
                            </th>
                            <th className="px-4 py-2 text-center font-medium text-gray-600">
                              影响级别
                            </th>
                            <th className="px-4 py-2 text-right font-medium text-gray-600">
                              相关性
                            </th>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">理由</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sector.aShareImpact.map((impact) => (
                            <tr key={impact.ticker} className="border-t border-gray-100">
                              <td className="px-4 py-3 font-medium text-gray-900">
                                {impact.ticker}
                              </td>
                              <td className="px-4 py-3 text-center text-xl">
                                {getDirectionEmoji(impact.impactDirection)}
                              </td>
                              <td className="px-4 py-3 text-center">
                                <span
                                  className={`px-2 py-1 rounded-full text-xs font-medium ${getImpactLevelStyle(
                                    impact.impactLevel,
                                  )}`}
                                >
                                  {impact.impactLevel}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right text-gray-600">
                                {(impact.correlation * 100).toFixed(0)}%
                              </td>
                              <td className="px-4 py-3 text-gray-600">{impact.reasoning}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && activeTab === "report" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">📋 A股-美股映射影响分析报告</h3>
            </div>
            <div className="p-6">
              <div
                className="prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{
                  __html: report
                    .replace(/\n/g, "<br/>")
                    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
                    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
                    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
                    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                    .replace(/\|(.+)\|/g, (match) => {
                      const parts = match.split("|").filter((p) => p.trim());
                      if (parts.length > 1 && parts[0].includes("---")) {
                        return "";
                      }
                      return `<tr>${parts.map((p) => `<td>${p.trim()}</td>`).join("")}</tr>`;
                    })
                    .replace(/<tr>(.*?)<\/tr>/g, (match) => {
                      if (!match.includes("<td>")) return match;
                      return `<table class="border-collapse w-full text-sm mb-4">${match}</table>`;
                    })
                    .replace(/<td>(.*?)<\/td>/g, "<td class='border border-gray-200 px-3 py-2'>$1</td>"),
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}