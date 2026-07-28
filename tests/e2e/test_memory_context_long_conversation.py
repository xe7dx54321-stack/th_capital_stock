from __future__ import annotations

import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _module_uri(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).resolve().as_uri()


def test_24_turn_context_survives_refresh_and_cross_session_retrieval(tmp_path: Path) -> None:
    harness = tmp_path / "memory-context-e2e.mjs"
    harness.write_text(
        f"""
import {{ ContextAssembler }} from {json.dumps(_module_uri("api/services/context-assembler.js"))};
import {{ ContextBudget }} from {json.dumps(_module_uri("api/services/context-budget.js"))};
import {{ ConversationCompactor }} from {json.dumps(_module_uri("api/services/conversation-compactor.js"))};
import {{ MemoryRetrievalPolicy }} from {json.dumps(_module_uri("api/services/memory-retrieval-policy.js"))};

const sessions = new Map();
const sessionA = [];
for (let turn = 1; turn <= 24; turn += 1) {{
  sessionA.push({{
    id: `u${{turn}}`,
    role: "user",
    content: turn === 18
      ? "星网锐捷市值是260亿元，不是199亿元"
      : `第${{turn}}轮继续研究星网锐捷`,
  }});
  sessionA.push({{
    id: `a${{turn}}`,
    role: "assistant",
    content: `第${{turn}}轮回答，标的是星网锐捷`,
  }});
}}
sessions.set("session-a", sessionA);
sessions.set("session-b", [
  {{ id: "u-b1", role: "user", content: "继续之前批准的星网锐捷论点" }},
]);

const sessionService = {{
  getSessionMessages(sessionId) {{
    return sessions.get(sessionId) || [];
  }},
}};

const compactor = new ConversationCompactor({{
  keepRecentTurns: 4,
  summarize: async ({{ messages }}) => ({{
    entities: [{{ ticker: "002396.SZ", name: "星网锐捷" }}],
    userGoals: ["持续跟踪超节点预期差"],
    confirmedFacts: [],
    temporaryAssumptions: [],
    userCorrections: [{{
      entity: "002396.SZ",
      field: "market_cap",
      oldValue: 199,
      newValue: 260,
      unit: "亿元",
    }}],
    decisions: [],
    unresolvedQuestions: ["重算 PE"],
    artifactRefs: ["artifact-deep-dive"],
    coveredMessageIds: messages.map((item) => item.id),
  }}),
}});

const budget = new ContextBudget({{
  maxInputTokens: 800,
  reserveOutputTokens: 200,
  countTokens: (value) => String(value || "").length,
}});

const retrievals = [];
const memoryPolicy = new MemoryRetrievalPolicy({{
  recordRetrieval: (memoryId, reason, options) => {{
    retrievals.push({{ memoryId, reason, options }});
    return `ret-${{memoryId}}`;
  }},
}});

const snapshots = [];
const assembler = new ContextAssembler({{
  sessionService,
  compactor,
  contextBudget: budget,
  memoryPolicy,
  snapshotRepository: {{
    save(snapshot) {{
      snapshots.push(snapshot);
      return `snapshot-${{snapshots.length}}`;
    }},
  }},
}});

const memories = [
  {{
    memory_id: "approved-thesis",
    memory_type: "investment_thesis",
    entity_id: "002396.SZ",
    content: {{ text: "已批准：收入弹性需要订单验证" }},
    status: "approved",
    as_of: "2026-07-28",
    valid_until: "2027-07-28",
    evidence_ids: ["ev-approved"],
    conflict_flag: 0,
  }},
  {{
    memory_id: "candidate-thesis",
    memory_type: "investment_thesis",
    entity_id: "002396.SZ",
    content: {{ text: "候选：未经批准的高增长结论" }},
    status: "candidate",
    as_of: "2026-07-28",
    valid_until: "2027-07-28",
    evidence_ids: ["ev-candidate"],
    conflict_flag: 0,
  }},
];

const common = {{
  currentMessage: "继续，并使用修正后的260亿元市值",
  taskEnvelope: {{
    task_type: "claim_correction",
    topic: "星网锐捷市值纠错",
    entities: [{{ ticker: "002396.SZ", name: "星网锐捷" }}],
  }},
  sessionState: {{
    userCorrections: [{{
      entity: "002396.SZ",
      field: "market_cap",
      oldValue: 199,
      newValue: 260,
      unit: "亿元",
      status: "revalidated",
    }}],
    confirmedFacts: [{{
      ticker: "002396.SZ",
      field: "market_cap",
      value: 260,
      unit: "亿元",
      evidenceId: "ev-current-quote",
      asOf: "2026-07-28",
    }}],
    pendingQuestions: ["重算 PE"],
    artifactRefs: ["artifact-deep-dive"],
  }},
  memories,
  artifactDigests: [{{
    artifactId: "artifact-deep-dive",
    title: "星网锐捷深度研究",
    digest: "核心摘要",
    body: "完整报告正文不应进入上下文".repeat(200),
  }}],
  modelProfile: {{ contextWindowTokens: 800 }},
}};

const beforeRefresh = await assembler.assemble({{ ...common, sessionId: "session-a" }});
const afterRefresh = await assembler.assemble({{ ...common, sessionId: "session-a" }});
const crossSession = await assembler.assemble({{ ...common, sessionId: "session-b" }});

const serialize = (value) => JSON.stringify(value);
const output = {{
  beforeEntity: serialize(beforeRefresh.messages).includes("002396.SZ"),
  afterEntity: serialize(afterRefresh.messages).includes("002396.SZ"),
  correctionSurvived: serialize(afterRefresh.sections.pinned).includes("260"),
  approvedRetrieved: serialize(crossSession.messages).includes("approved-thesis"),
  candidateExcluded: !serialize(crossSession.messages).includes("candidate-thesis"),
  withinBudget: [beforeRefresh, afterRefresh, crossSession]
    .every((item) => item.tokenUsage.totalInputTokens <= item.tokenUsage.budgetTokens),
  snapshotCount: snapshots.length,
  retrievalCount: retrievals.length,
}};

process.stdout.write(JSON.stringify(output));
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        ["node", str(harness)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result == {
        "beforeEntity": True,
        "afterEntity": True,
        "correctionSurvived": True,
        "approvedRetrieved": True,
        "candidateExcluded": True,
        "withinBudget": True,
        "snapshotCount": 3,
        "retrievalCount": 3,
    }
