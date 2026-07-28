/**
 * 组件：ComparisonMatrixView（对比矩阵 / 比较表格）
 * --------------------------------------------------
 * 功能（小白版）：把"多只股票的同一个维度"列成一张大表，一眼看懂"谁好谁差"。
 * 表头就是对比维度（PE、市值、营收增速、毛利率……），每行是一个公司。
 *
 * UI 原则：
 *   - 表格外层加 overflow-x-auto，支持 12+ 列横向滚动（测试清单 3）
 *   - 先展示标题/生成时间，再放表格
 *   - 缺失值用「—」占位，不崩（测试清单 2）
 *   - 内容全部通过 React 纯文本渲染，不 innerHTML（测试清单 4 XSS 安全）
 */

import React from "react";

export interface ComparisonMatrixColumn {
  key: string;
  label: string;
  /** 可选：数值列，用来排序/右对齐 */
  align?: "left" | "right" | "center";
  /** 可选：是否数值列（展示千分位） */
  numeric?: boolean;
}

export interface ComparisonMatrixRow {
  [key: string]: any;
}

export interface ComparisonMatrixViewProps {
  data: {
    title?: string;
    generated_at?: string;
    columns?: ComparisonMatrixColumn[];
    rows?: ComparisonMatrixRow[];
    /** 可选：每一行的"风险/告警"颜色字段（比如风险>高的就背景标红） */
    highlight_keys?: string[];
  };
}

/**
 * 格式化单元格：
 *   - 数字 → 千分位（太大的话转中文"亿"）
 *   - 数组 → 「、」连接
 *   - null/undefined → "—"
 */
function formatCell(value: any): string {
  if (value == null) return "—";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) return "—";
    // > 1e8 的数按"xx 亿"显示（小白友好）
    if (Math.abs(value) >= 1e8) return `${(value / 1e8).toFixed(2)}亿`;
    return value.toLocaleString("zh-CN");
  }
  if (Array.isArray(value)) return value.join("、");
  return String(value);
}

export default function ComparisonMatrixView(props: ComparisonMatrixViewProps) {
  const { data } = props;
  if (!data) {
    return <div className="artifact-card degraded">暂无对比数据</div>;
  }

  const columns = data.columns || [];
  const rows = data.rows || [];

  return (
    <article className="artifact-card comparison-matrix-view" aria-label="对比矩阵">
      <header className="card-header">
        <h3>{data.title || "标的对比"}</h3>
        {data.generated_at ? <small className="meta">生成于 {data.generated_at}</small> : null}
      </header>

      {/* ====== 关键：overflow-x-auto 类名（测试清单 3 横滚检查点）====== */}
      <div className="overflow-x-auto" role="region" aria-label="对比表格横向滚动区域">
        {rows.length === 0 || columns.length === 0 ? (
          <div className="degraded table-empty">暂无对比数据</div>
        ) : (
          <table className="comparison-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={`col-${col.align || "left"}`}
                    style={col.numeric ? { textAlign: "right" } : undefined}
                    scope="col"
                  >
                    {col.label || col.key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIdx) => (
                <tr key={rowIdx} className={rowIdx % 2 === 0 ? "row-even" : "row-odd"}>
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      style={col.numeric ? { textAlign: "right" } : undefined}
                      data-col={col.key}
                    >
                      {formatCell(row[col.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </article>
  );
}
