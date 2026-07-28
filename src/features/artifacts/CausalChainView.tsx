/**
 * 组件：CausalChainView（产业因果链 / 传导链图）
 * -------------------------------------------------
 * 功能（小白版）：把"从上游到下游，谁影响谁"画成一条链式的流程图。
 * 比如「云厂 Capex ↑ → 服务器出货 ↑ → GPU 订单 ↑ → HBM 需求 ↑ → HBM ASP ↑」
 * 用户一眼就能看懂整个产业逻辑链，以及每一步的"证据来源"是什么。
 *
 * UI 原则：
 *   - 先放「根主张（最终结论）」（UI 原则先结论后证据）
 *   - 再展示节点链式 + 每个节点证据
 *   - 方向（↑/↓/→）用颜色 + 文字表达
 *   - 数据缺失不崩（测试清单 2）
 *   - 用户注入文本纯文本输出，不 innerHTML（测试清单 4 XSS 安全）
 */

import React from "react";

export interface CausalChainNode {
  id: string;
  node: string;
  direction: "up" | "down" | "flat" | string;
  magnitude?: number; // 0~5 越大影响越大
  evidence?: string[];
}

export interface CausalChainViewProps {
  data: {
    title?: string;
    root_claim?: string;
    chain?: CausalChainNode[];
  };
}

function directionMeta(direction: string) {
  switch (direction) {
    case "up":
      return { label: "↑", cls: "dir-up", zh: "上升" };
    case "down":
      return { label: "↓", cls: "dir-down", zh: "下降" };
    case "flat":
      return { label: "→", cls: "dir-flat", zh: "持平" };
    default:
      return { label: "→", cls: "dir-flat", zh: String(direction) };
  }
}

export default function CausalChainView(props: CausalChainViewProps) {
  const { data } = props;
  if (!data) {
    return <div className="artifact-card degraded">暂无因果链数据</div>;
  }

  const chain = data.chain || [];

  return (
    <article className="artifact-card causal-chain-view" aria-label="产业因果链">
      {/* ====== 先放「根主张」（最终结论 = UI 原则先结论后证据） ====== */}
      <header className="card-header root-claim-band">
        <h3>{data.title || "产业因果链"}</h3>
        {data.root_claim ? (
          <p className="root-claim">核心结论：{data.root_claim}</p>
        ) : null}
      </header>

      {/* ====== 然后是链式节点图 ====== */}
      {chain.length === 0 ? (
        <div className="degraded">暂无传导链节点</div>
      ) : (
        <ol className="chain-rail" aria-label="因果传导链节点">
          {chain.map((node, idx) => {
            const d = directionMeta(node.direction || "flat");
            const isLast = idx === chain.length - 1;
            const mag = node.magnitude ?? 3;
            const magPct = Math.min(100, Math.max(10, (mag / 5) * 100));
            return (
              <li className={`chain-node ${d.cls}`} key={node.id || idx}>
                <div className="node-head">
                  <span className="node-index">L{idx + 1}</span>
                  <span className="node-title">{node.node}</span>
                  <span className={`node-direction ${d.cls}`} title={d.zh}>
                    {d.label} {d.zh}
                  </span>
                  {node.magnitude != null ? (
                    <span className="magnitude-bar" title={`影响力度 ${mag}/5`}>
                      <span style={{ width: `${magPct}%` }} />
                    </span>
                  ) : null}
                </div>
                <ul className="evidence-list">
                  {(node.evidence || []).length === 0 ? (
                    <li className="degraded">（无证据引用）</li>
                  ) : (
                    node.evidence.map((e, ei) => <li key={ei}>{e}</li>)
                  )}
                </ul>
                {!isLast ? <div className="chain-arrow">↓</div> : null}
              </li>
            );
          })}
        </ol>
      )}
    </article>
  );
}
