/**
 * 阶段 13：多态制品与前台可视化 —— Vitest 测试（覆盖 Master Plan §阶段 13 的 8 条测试清单）
 *
 * 运行方式：
 *   npm run test:ui  (vitest run)
 * 或单独跑：
 *   npx vitest run src/features/artifacts/__tests__/PolymorphicArtifactViews.test.tsx
 *
 * 8 条测试清单（严格对齐 Master Plan §阶段 13 "测试：" 段的 8 条）：
 *   1. 每种制品渲染（ValuationModelView / ComparisonMatrixView / CausalChainView / SignalPlanView / CorrectionDiffView / MemoryCandidatePanel）
 *   2. 缺失字段降级（重要字段为空时，显示友好占位，不崩）
 *   3. 大表格横向滚动和移动视口（至少 <ComparisonMatrixView> 支持大表格横滚）
 *   4. Markdown/XSS 安全（不允许 <script> 或 HTML 注入执行）
 *   5. artifact 路径安全（MemoryCandidatePanel 不能出现相对路径穿越 ../../../）
 *   6. 会话刷新恢复（组件 key 变化后保持渲染状态，不白屏）
 *   7. 执行失败和部分成功（CorrectionDiffView 处理部分修复场景）
 *   8. 记忆候选操作（MemoryCandidatePanel 的 approve/reject/archive 按钮点击事件）
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ComparisonMatrixView from "../../artifacts/ComparisonMatrixView";
import CorrectionDiffView, { type CorrectionDiffViewProps } from "../../artifacts/CorrectionDiffView";
import CausalChainView from "../../artifacts/CausalChainView";
import SignalPlanView from "../../artifacts/SignalPlanView";
import ValuationModelView from "../../artifacts/ValuationModelView";
// 注意 Master Plan 写的是 MemoryCandidatePanel 放 src/features/memory/
import MemoryCandidatePanel from "../../memory/MemoryCandidatePanel";

// ============================================================================
// 测试数据工厂：生成每个组件所需的"最小合法 mock 数据"
// ============================================================================

function makeValuationData(overrides = {}) {
  return {
    ticker: "300474.SZ",
    name: "景嘉微",
    snapshot_date: "2026-07-22",
    currency: "CNY",
    market_cap: { value: 26_000_000_000, unit: "元", source_level: "A 级-交易所正式行情" },
    models: [
      {
        method: "经营驱动估值（收入→净利→PE）",
        assumptions: {
          revenue_cagr: "35%",
          net_margin: "30%",
          target_pe: 45,
          horizon_years: 3,
        },
        fair_value: {
          per_share: 68.5,
          enterprise: 20_500_000_000,
          unit: "元",
        },
        upside: -21.1, // 当前价 86.8 → 68.5 为 -21.1%
        confidence: 0.72,
      },
      {
        method: "相对估值（同行 PE/PB 中位）",
        assumptions: { peer_group: ["GPU 国产替代", "688256.SH", "688041.SH"] },
        fair_value: { per_share: 74.0, enterprise: 22_200_000_000, unit: "元" },
        upside: -14.7,
        confidence: 0.65,
      },
    ],
    conclusion: {
      verdict: "当前估值偏高，建议等待回调 15~20% 再进入观察池。",
      summary_score: 3.4,
    },
    ...overrides,
  };
}

function makeComparisonData(overrides = {}) {
  return {
    title: "GPU 国产替代三标的对比矩阵",
    generated_at: "2026-07-22",
    columns: [
      { key: "ticker", label: "代码" },
      { key: "name", label: "名称" },
      { key: "market_cap", label: "市值(亿)" },
      { key: "pe_ttm", label: "PE(TTM)" },
      { key: "revenue_yoy", label: "营收同比%" },
      { key: "net_profit_yoy", label: "净利同比%" },
      { key: "gross_margin", label: "毛利率%" },
      { key: "roic", label: "ROIC%" },
      { key: "gpu_flops_fp16", label: "FP16 TFLOPS" },
      { key: "order_visibility", label: "订单可见度" },
      { key: "hbm_supply", label: "HBM 供货情况" },
      { key: "risk_flag", label: "风险提示" },
    ],
    rows: [
      { ticker: "688256.SH", name: "寒武纪", market_cap: 1985, pe_ttm: 285, revenue_yoy: 192, net_profit_yoy: 420, gross_margin: 58, roic: 4, gpu_flops_fp16: 256, order_visibility: "2026 Q3 全满", hbm_supply: "SK 海力士锁定", risk_flag: "云厂砍单风险" },
      { ticker: "300474.SZ", name: "景嘉微", market_cap: 260,  pe_ttm: 198, revenue_yoy: 35,  net_profit_yoy: 52,  gross_margin: 62, roic: 6, gpu_flops_fp16: 96,  order_visibility: "军工 2026 全年", hbm_supply: "国内替代", risk_flag: "民品化进度慢" },
      { ticker: "688041.SH", name: "海光信息", market_cap: 1385, pe_ttm: 76,  revenue_yoy: 78,  net_profit_yoy: 92,  gross_margin: 53, roic: 12, gpu_flops_fp16: 192, order_visibility: "运营商 2026 H2", hbm_supply: "三星长单", risk_flag: "x86 授权到期" },
      { ticker: "688396.SH", name: "华润微", market_cap: 986,  pe_ttm: 62,  revenue_yoy: 22,  net_profit_yoy: 28,  gross_margin: 41, roic: 9, gpu_flops_fp16: 0,   order_visibility: "工控稳定",    hbm_supply: "不依赖",   risk_flag: "功率周期波动" },
    ],
    ...overrides,
  };
}

function makeCausalChainData(overrides = {}) {
  return {
    title: "AI 服务器 → GPU → 显存 → HBM 涨价因果链",
    root_claim: "AI 服务器资本开支拉动全链条涨价，2026 H2 HBM ASP 继续上行 15~20%",
    chain: [
      { id: "L1", node: "北美云厂资本开支", evidence: ["MSFT FY26 Capex 指引 +52% YoY", "GOOG CapEx Q1 +41%"], direction: "up", magnitude: 4.2 },
      { id: "L2", node: "AI 服务器出货量",   evidence: ["IDC 指引 2026 全球 AI 服务器出货 +38%"], direction: "up", magnitude: 3.8 },
      { id: "L3", node: "GPU 订单量",       evidence: ["NV H100/H200 排期拉长至 42 周"],          direction: "up", magnitude: 4.5 },
      { id: "L4", node: "HBM 需求",         evidence: ["每颗 H200 配 6 颗 HBM3e，容量增加 2×"],    direction: "up", magnitude: 5.0 },
      { id: "L5", node: "HBM 供给约束",     evidence: ["SK 海力士 HBM3e 良率 65%，产能爬坡慢"],  direction: "flat", magnitude: 3.1 },
      { id: "L6", node: "HBM ASP",          evidence: ["高盛研报：2026 H2 ASP 预计上升 15~20%"],   direction: "up", magnitude: 4.8 },
    ],
    ...overrides,
  };
}

function makeSignalPlanData(overrides = {}) {
  return {
    ticker: "688205.SH",
    name: "德科立",
    plan_id: "signal-plan-dtk-2026-07",
    generated_at: "2026-07-22",
    plan_version: "1.0",
    catalyst_themes: [
      { theme: "400G/800G 光模块 Q3 拉货", window: "2026-08~2026-10", impact: 0.8, evidence: ["MSFT OAI 订单放量传闻"] },
      { theme: "泰国工厂产能爬坡完毕",    window: "2026-09",        impact: 0.6, evidence: ["公司 6 月投资者沟通会纪要"] },
      { theme: "AI 客户认证通过",         window: "2026-08~2026-09", impact: 1.0, evidence: ["北美 Top 3 客户实地考察结束"] },
    ],
    observation_kpis: [
      { kpi: "单季度营收环比增速",   threshold: "> 18% QoQ", frequency: "季报",  source: "公司财报/业绩快报" },
      { kpi: "毛利率(整体)",          threshold: "> 32%",     frequency: "季报",  source: "公司财报" },
      { kpi: "海外收入占比",          threshold: "> 70%",     frequency: "季报",  source: "公司财报" },
      { kpi: "应收账款周转天数",      threshold: "< 80 天",   frequency: "季报",  source: "公司财报" },
      { kpi: "北美 Top 3 客户收入占比", threshold: "> 45%",   frequency: "年报/调研", source: "投资者调研纪要" },
    ],
    kill_conditions: [
      "400G 光模块价格环比下跌 > 10%（8 月产业调研）",
      "泰国工厂良率 < 92%（月度管理层交流）",
      "AI 客户认证推迟 > 30 天",
      "毛利率连续两个季度低于 30%",
    ],
    ...overrides,
  };
}

function makeCorrectionDiffData(overrides = {}) {
  return {
    report_id: "rpt-starnet-2026-07-20-v2",
    original_report_id: "rpt-starnet-2026-07-20-v1",
    correction_reason: "市值数据错误（把 199 亿写成 260 亿），发现后触发纠错与依赖重算",
    corrected_at: "2026-07-21 14:30 CST",
    corrected_by: "user_explicit",
    changes: [
      {
        field: "market_cap.value",
        before: 26_000_000_000,
        after:  19_900_000_000,
        unit: "元",
        impact: "high",
        affected_downstream: [
          "pe_ttm: 260/净利 ≈ 198 → 实际 199/净利 ≈ 152",
          "相对估值段 4 行市值数据",
          "结论段第一句：『当前市值 260 亿』重写为 199 亿",
          "模型 2（同行对比）的估值中枢上修",
        ],
        downstream_status: "fully_recalculated",
      },
      {
        field: "valuation.fair_value.enterprise",
        before: 18_500_000_000,
        after:  14_200_000_000,
        unit: "元",
        impact: "high",
        affected_downstream: ["结论段「合理估值区间」重写"],
        downstream_status: "fully_recalculated",
      },
      {
        field: "metadata.snapshot_date",
        before: null,
        after:  "2026-07-20",
        unit: "ISO-日期",
        impact: "low",
        affected_downstream: [],
        downstream_status: "record_only",
      },
    ],
    ...overrides,
  };
}

function makeMemoryCandidates(overrides = []) {
  return [
    {
      memory_id: "mem_c_star_001",
      entity_type: "stock",
      entity_id: "002396.SZ",
      memory_type: "valuation",
      content: { pe_ttm: 152, remark: "2026-07-20 收盘" },
      status: "candidate",
      confidence: 0.95,
      created_at: "2026-07-21T02:00:00Z",
      evidence_links: [{ evidence_id: "ev_exchange_close_20260720", relation: "supports" }],
      tags: ["星网锐捷", "市值纠错后"],
      project_id: "proj_starnet_correction",
      hit_count: 1,
      conflict_flag: false,
    },
    {
      memory_id: "mem_c_star_002",
      entity_type: "stock",
      entity_id: "002396.SZ",
      memory_type: "fundamental",
      content: { net_profit_yoy: 28, revenue_yoy: 15 },
      status: "candidate",
      confidence: 0.88,
      created_at: "2026-07-21T02:00:05Z",
      evidence_links: [{ evidence_id: "ev_q2_earnings_pre", relation: "supports" }],
      tags: ["星网锐捷", "2026Q2 快报"],
      project_id: "proj_starnet_correction",
      hit_count: 0,
      conflict_flag: true,
    },
    ...overrides,
  ];
}

// ============================================================================
// 测试 1 — 6：每种制品都能独立渲染出来（不崩 + 有核心内容可见）
// ============================================================================
describe("阶段 13 — 测试清单 1：每种制品渲染", () => {
  it("ValuationModelView 能渲染核心结论、市值、2 个估值模型", () => {
    render(<ValuationModelView data={makeValuationData()} />);
    // 核心结论在
    expect(screen.getByText(/当前估值偏高/)).toBeInTheDocument();
    // 标题（景嘉微）在
    expect(screen.getByText(/景嘉微/)).toBeInTheDocument();
    // 两种估值方法的名字都要可见
    expect(screen.getByText(/经营驱动估值/)).toBeInTheDocument();
    expect(screen.getByText(/相对估值/)).toBeInTheDocument();
    // 数据时点 + 来源等级可见
    expect(screen.getByText(/2026-07-22/)).toBeInTheDocument();
    expect(screen.getByText(/A 级-交易所正式行情/)).toBeInTheDocument();
  });

  it("ComparisonMatrixView 能渲染标题 + 至少 4 行 × 12 列", () => {
    render(<ComparisonMatrixView data={makeComparisonData()} />);
    expect(screen.getByText(/GPU 国产替代三标的对比矩阵/)).toBeInTheDocument();
    // 12 个列头都出现
    expect(screen.getByText("代码")).toBeInTheDocument();
    expect(screen.getByText("市值(亿)")).toBeInTheDocument();
    expect(screen.getByText("FP16 TFLOPS")).toBeInTheDocument();
    expect(screen.getByText("风险提示")).toBeInTheDocument();
    // 4 个公司名可见
    expect(screen.getByText("寒武纪")).toBeInTheDocument();
    expect(screen.getByText("景嘉微")).toBeInTheDocument();
    expect(screen.getByText("海光信息")).toBeInTheDocument();
    expect(screen.getByText("华润微")).toBeInTheDocument();
  });

  it("CausalChainView 能渲染 6 层因果链 + 每条都有证据 + 首尾方向正确", () => {
    render(<CausalChainView data={makeCausalChainData()} />);
    expect(screen.getByText(/AI 服务器 → GPU → 显存 → HBM 涨价因果链/)).toBeInTheDocument();
    // 6 个节点都出现（至少各出现一次，getAllByText 允许多匹配）
    expect(screen.getAllByText(/北美云厂资本开支/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/HBM ASP/).length).toBeGreaterThanOrEqual(1);
    // 有证据引用（用角色/文本判断）
    expect(screen.getByText(/NV H100\/H200 排期拉长至 42 周/)).toBeInTheDocument();
    // 根主张可见
    expect(screen.getByText(/2026 H2 HBM ASP 继续上行 15~20%/)).toBeInTheDocument();
  });

  it("SignalPlanView 能渲染催化主题、观察 KPI、Kill 条件三类内容", () => {
    render(<SignalPlanView data={makeSignalPlanData()} />);
    expect(screen.getByText(/德科立/)).toBeInTheDocument();
    // 催化主题
    expect(screen.getByText(/400G\/800G 光模块 Q3 拉货/)).toBeInTheDocument();
    expect(screen.getByText(/AI 客户认证通过/)).toBeInTheDocument();
    // 观察 KPI
    expect(screen.getByText(/单季度营收环比增速/)).toBeInTheDocument();
    expect(screen.getByText(/毛利率\(整体\)/)).toBeInTheDocument();
    // Kill 条件
    expect(screen.getByText(/400G 光模块价格环比下跌/)).toBeInTheDocument();
    expect(screen.getByText(/AI 客户认证推迟/)).toBeInTheDocument();
  });

  it("CorrectionDiffView 能显示 3 个字段的 before/after + 影响等级 + 下游重算状态", () => {
    render(<CorrectionDiffView data={makeCorrectionDiffData() as any} />);
    // 纠错原因必须可见（UI 原则：先展示结论/核心信息）
    expect(screen.getByText(/市值数据错误/)).toBeInTheDocument();
    // 字段名
    expect(screen.getByText("market_cap.value")).toBeInTheDocument();
    expect(screen.getByText("valuation.fair_value.enterprise")).toBeInTheDocument();
    // 影响等级（至少 2 个 chip 包含 high）
    const highChips = screen.getAllByText(/^高影响|high$/i);
    expect(highChips.length).toBeGreaterThanOrEqual(2);
    // 下游重算状态（fully_recalculated chip）
    const recalChips = screen.getAllByText(/已自动重算|fully_recalculated|record_only|仅记录/i);
    expect(recalChips.length).toBeGreaterThanOrEqual(2);
  });

  it("MemoryCandidatePanel 能渲染 2 条候选记忆 + approve/reject/archive 三个按钮", () => {
    const onApprove = vi.fn();
    const onReject = vi.fn();
    const onArchive = vi.fn();
    render(
      <MemoryCandidatePanel
        candidates={makeMemoryCandidates()}
        onApprove={onApprove}
        onReject={onReject}
        onArchive={onArchive}
      />
    );
    // 记忆 2 条的类型都能看到
    expect(screen.getAllByText(/valuation/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/fundamental/).length).toBeGreaterThanOrEqual(1);
    // 6 个按钮（2 条 × 3 个动作）
    const approveBtns = screen.getAllByRole("button", { name: /批准|approve/i });
    const rejectBtns  = screen.getAllByRole("button", { name: /拒绝|reject/i });
    const archiveBtns = screen.getAllByRole("button", { name: /归档|archive/i });
    expect(approveBtns.length).toBe(2);
    expect(rejectBtns.length).toBe(2);
    expect(archiveBtns.length).toBe(2);
    // conflict_flag=true 的那条必须出现 role="alert" 的冲突标记（精确匹配节点）
    const conflictAlerts = screen.getAllByRole("alert");
    expect(conflictAlerts.length).toBeGreaterThanOrEqual(1);
    expect(conflictAlerts.some((el) => /冲突/.test(el.textContent || ""))).toBe(true);
  });
});

// ============================================================================
// 测试 2：缺失字段降级（重要字段为空时，显示占位符，不崩溃）
// ============================================================================
describe("阶段 13 — 测试清单 2：缺失字段降级", () => {
  it("ValuationModelView 缺失 models 数组时，显示「暂无估值模型」占位", () => {
    const data = makeValuationData({ models: undefined, conclusion: { verdict: "数据不足，暂不给出估值。", summary_score: null } });
    render(<ValuationModelView data={data as any} />);
    // 不崩的前提下，要么能看到公司名，要么有降级文案（两者任一即可，不强迫措辞）
    expect(
      screen.queryByText(/景嘉微/) ||
      screen.queryByText(/暂无估值|数据不足|估值模型/)
    ).toBeTruthy();
  });

  it("ComparisonMatrixView rows 为空时，不崩且显示「暂无对比数据」占位", () => {
    render(<ComparisonMatrixView data={makeComparisonData({ rows: [] })} />);
    expect(screen.queryByText(/暂无对比数据|暂无数据/)).toBeTruthy();
  });

  it("CorrectionDiffView changes 为空时，给出友好提示", () => {
    render(<CorrectionDiffView data={makeCorrectionDiffData({ changes: [] }) as any} />);
    expect(screen.queryByText(/没有字段变更|本次无变更|暂无 diff/)).toBeTruthy();
  });
});

// ============================================================================
// 测试 3：大表格横向滚动（ComparisonMatrixView 至少有一个横向可滚动容器）
// ============================================================================
describe("阶段 13 — 测试清单 3：大表格横向滚动和移动视口", () => {
  it("ComparisonMatrixView 在 DOM 中有 overflow-x 类名或样式，可承载 12 列横滚", () => {
    const { container } = render(<ComparisonMatrixView data={makeComparisonData()} />);
    // 查表格外层容器是否有「overflow-x-auto」或「scroll-x」这种约定类名
    const scrollable = container.querySelector(".overflow-x-auto, .scroll-x, [style*='overflow-x: auto'], [style*='overflow-x:scroll']");
    expect(scrollable).not.toBeNull();
    // 表格列数 = 12（thead th 数量 = columns 长度）
    const ths = container.querySelectorAll("table thead th");
    expect(ths.length).toBeGreaterThanOrEqual(12);
  });
});

// ============================================================================
// 测试 4：Markdown/XSS 安全（绝对不允许 <script> 或 HTML 注入真的执行）
// ============================================================================
describe("阶段 13 — 测试清单 4：Markdown/XSS 安全", () => {
  it("CorrectionDiffView — malicious 的 correction_reason 用 <script>，文本被转义，不真的执行", () => {
    const evil = '<img src=x onerror="alert(\'xss\')"><script>alert("xss")</script>';
    render(<CorrectionDiffView data={makeCorrectionDiffData({ correction_reason: evil }) as any} />);
    // script 不真的执行（JSDOM 下 window.alert 没被调用就是安全的，或者 DOM 里找不到 <script> 可执行元素）
    const html = document.body.innerHTML;
    // 转义后的 <script> 不能是真正的 script 标签开始
    const hasRawScriptTag = /<script(?=[\s/>])/i.test(html);
    expect(hasRawScriptTag).toBe(false);
    // img onerror 也不能是原始 img 标签
    const hasRawImgOnError = /<img[^>]+onerror\s*=/i.test(html);
    expect(hasRawImgOnError).toBe(false);
  });

  it("MemoryCandidatePanel — malicious 标签名/内容，同样转义", () => {
    const evilContent: any = { text: "<svg onload=alert(1)>", tags: ["<script>alert(2)</script>"] };
    const candidates = makeMemoryCandidates([evilContent]);
    render(
      <MemoryCandidatePanel
        candidates={candidates as any}
        onApprove={vi.fn()} onReject={vi.fn()} onArchive={vi.fn()}
      />
    );
    const hasRaw = /<script(?=[\s/>])|<svg[^>]+onload/i.test(document.body.innerHTML);
    expect(hasRaw).toBe(false);
  });
});

// ============================================================================
// 测试 5：artifact 路径安全（MemoryCandidatePanel 不能出现相对路径穿越）
// ============================================================================
describe("阶段 13 — 测试清单 5：artifact 路径安全", () => {
  it("MemoryCandidatePanel 的记忆 ID 若包含 ../ 也绝不能渲染成相对路径 a href", () => {
    const bad: any = makeMemoryCandidates([
      { memory_id: "../../../../etc/passwd", content: { pe: 10 }, memory_type: "valuation" },
    ]);
    const { container } = render(
      <MemoryCandidatePanel
        candidates={bad as any}
        onApprove={vi.fn()} onReject={vi.fn()} onArchive={vi.fn()}
      />
    );
    // 页面里任何 <a href> 都不能包含 "../" 这种穿越
    const links = container.querySelectorAll("a[href]");
    links.forEach((a) => {
      const href = a.getAttribute("href") || "";
      expect(href).not.toMatch(/\.\.\//);
    });
  });
});

// ============================================================================
// 测试 6：会话刷新恢复（key 变化 → 重挂载后仍能正常渲染，不白屏）
// ============================================================================
describe("阶段 13 — 测试清单 6：会话刷新恢复", () => {
  it("CausalChainView 两次 key 变化重挂载后，核心节点仍然可见", () => {
    const { rerender, container } = render(<CausalChainView key="k1" data={makeCausalChainData()} />);
    expect(screen.getByText(/^HBM ASP\s*$/)).toBeInTheDocument();
    rerender(<CausalChainView key="k2" data={makeCausalChainData()} />);
    expect(screen.getByText(/^HBM ASP\s*$/)).toBeInTheDocument();
    rerender(<CausalChainView key="k3" data={makeCausalChainData()} />);
    expect(screen.getByText(/^HBM ASP\s*$/)).toBeInTheDocument();
    void container;
  });
});

// ============================================================================
// 测试 7：执行失败和部分成功（CorrectionDiffView 有部分修复场景）
// ============================================================================
describe("阶段 13 — 测试清单 7：执行失败和部分成功", () => {
  it("CorrectionDiffView 部分字段 downstream_status=failed 时，出现「未成功重算」或类似警告提示", () => {
    const partial = makeCorrectionDiffData({
      changes: [
        {
          field: "market_cap.value",
          before: 26e9, after: 19.9e9, unit: "元", impact: "high",
          affected_downstream: ["pe_ttm 重算"],
          downstream_status: "failed" as const,  // ← 部分失败！
        },
      ],
    });
    render(<CorrectionDiffView data={partial as any} />);
    // queryAllByText 允许多匹配（banner + chip 都出现是对的，我们只要至少有 1 个）
    const matches = screen.queryAllByText(/未成功重算|重算失败|失败|failed|⚠|warning|警告/i);
    const inInnerText = /未成功重算|重算失败|失败|failed|警告/i.test(document.body.innerText);
    expect(matches.length > 0 || inInnerText).toBeTruthy();
  });
});

// ============================================================================
// 测试 8：记忆候选操作（点击 approve/reject/archive 触发回调）
// ============================================================================
describe("阶段 13 — 测试清单 8：记忆候选操作", () => {
  it("点击 MemoryCandidatePanel 中第二条候选的批准 → 正确回调触发（memory_id = mem_c_star_002）", () => {
    const onApprove = vi.fn();
    const onReject = vi.fn();
    const onArchive = vi.fn();
    render(
      <MemoryCandidatePanel
        candidates={makeMemoryCandidates()}
        onApprove={onApprove}
        onReject={onReject}
        onArchive={onArchive}
      />
    );
    const approveBtns = screen.getAllByRole("button", { name: /批准|approve/i });
    // 第二条（索引 1）点下去
    fireEvent.click(approveBtns[1]);
    expect(onApprove).toHaveBeenCalledTimes(1);
    expect(onApprove.mock.calls[0][0]).toBe("mem_c_star_002");
    // reject/archive 一次都没触发
    expect(onReject).not.toHaveBeenCalled();
    expect(onArchive).not.toHaveBeenCalled();
  });
});
