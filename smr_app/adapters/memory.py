from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from smr_app.runtime.event_store import immediate_transaction, utc_now


ALLOWED_RELATIONS = frozenset({"supports", "contradicts", "supersedes", "context"})
ALLOWED_TRANSITIONS = {
    "candidate": {"approve": "approved", "reject": "rejected", "archive": "archived"},
    "approved": {"archive": "archived"},
    "rejected": {"archive": "archived"},
    "archived": {},
}

# 用户偏好的"合法来源"（验收 7：不从系统生成文本中臆测用户偏好）
ALLOWED_PREFERENCE_SOURCES = frozenset({
    "user_explicit",           # 用户明确亲口说的（推荐）
    "approved_user_action",    # 用户通过批准/拒绝行为体现的偏好
    "user_preference_file",    # 用户写在偏好文件里的
})


def _loads(raw: Any, fallback: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw or "")
    except (TypeError, ValueError):
        return fallback


def field_diff(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    diff = []
    for field in sorted(set(before) | set(after)):
        old = before.get(field)
        new = after.get(field)
        if old != new:
            diff.append({"field": field, "before": old, "after": new})
    return diff


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """
    小白解释：
    ----------
    判断 SQLite 表某列存不存在。因为"ALTER TABLE ADD COLUMN"时，如果列已经存在就会报错，
    所以先查一下，有就跳过，保证幂等（跑 100 次结果都一样）。

    参数：
        conn    —— SQLite 连接
        table   —— 表名
        column  —— 列名
    返回值：True = 存在；False = 不存在
    """
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def ensure_memory_schema(conn: sqlite3.Connection) -> None:
    """
    函数功能：
        创建（或升级）记忆相关的 3 张主表 + 1 张检索日志表。幂等执行，重复调也不会炸。
        - memory_items              主表：记忆条目（验收 1/2/3/5/6/7 字段都在这）
        - memory_evidence_links     证据关联表（记忆 <-> 证据）
        - memory_review_log         审核日志表（谁什么时候 approve/reject/edit 了）
        - memory_retrieval_log      检索日志表（验收 4：记录为什么命中 + 如何使用）
    参数：conn —— SQLite 连接
    返回值：无（失败直接抛 SQLite 异常）
    """
    # ---------- 1. memory_items 主表 ----------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_items (
            memory_id               TEXT PRIMARY KEY,
            entity_type             TEXT NOT NULL,
            entity_id               TEXT NOT NULL,
            memory_type             TEXT NOT NULL,
            content                 TEXT NOT NULL,
            status                  TEXT NOT NULL DEFAULT 'candidate',
            confidence              REAL,
            source_run_id           TEXT,
            valid_from              TEXT,
            valid_until             TEXT,
            last_verified_at        TEXT,
            created_at              TEXT NOT NULL,
            updated_at              TEXT NOT NULL,
            parent_memory_id        TEXT,
            version                 INTEGER NOT NULL DEFAULT 1,
            field_diff_json         TEXT,
            reviewed_by             TEXT,
            review_reason           TEXT,
            reviewed_at             TEXT,
            -- ====== 阶段 12 新增列（验收 3 + 6 + 7 + 5） ======
            tags_json               TEXT,            -- 验收 3：标签，JSON 数组
            project_id              TEXT,            -- 验收 3：所属项目 ID
            hit_count               INTEGER NOT NULL DEFAULT 0,  -- 验收 3：命中次数
            last_hit_at             TEXT,            -- 验收 3：最近命中时间
            session_id              TEXT,            -- 验收 6：会话级记忆绑定的 session_id
            preference_source       TEXT,            -- 验收 7：user_preference 类型来源约束
            preference_explicit_ref TEXT,            -- 验收 7：用户明确表达的引用（如"会话 X 第 Y 轮"）
            conflict_flag           INTEGER NOT NULL DEFAULT 0  -- 验收 5：是否矛盾待审核（0/1）
        )
        """
    )

    # 为了兼容老库（老库可能已经有 memory_items 但缺阶段 12 的列），一列一列补上
    new_columns = [
        ("tags_json",               "TEXT"),
        ("project_id",              "TEXT"),
        ("hit_count",               "INTEGER NOT NULL DEFAULT 0"),
        ("last_hit_at",             "TEXT"),
        ("session_id",              "TEXT"),
        ("preference_source",       "TEXT"),
        ("preference_explicit_ref", "TEXT"),
        ("conflict_flag",           "INTEGER NOT NULL DEFAULT 0"),
    ]
    for col_name, col_def in new_columns:
        if not _has_column(conn, "memory_items", col_name):
            conn.execute(f"ALTER TABLE memory_items ADD COLUMN {col_name} {col_def}")

    # 加 3 个索引（加速查询，小白可以不用懂，不影响正确性）
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_entity ON memory_items(entity_type, entity_id, memory_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_status ON memory_items(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_items_session ON memory_items(session_id)")

    # ---------- 2. memory_evidence_links 证据关联表 ----------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_evidence_links (
            memory_id   TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            relation    TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            PRIMARY KEY (memory_id, evidence_id, relation)
        )
        """
    )

    # ---------- 3. memory_review_log 审核日志表 ----------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_review_log (
            review_id       TEXT PRIMARY KEY,
            memory_id       TEXT NOT NULL,
            action          TEXT NOT NULL,
            previous_status TEXT NOT NULL,
            new_status      TEXT NOT NULL,
            reviewer        TEXT NOT NULL,
            reason          TEXT NOT NULL,
            reviewed_at     TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_review_log_memory ON memory_review_log(memory_id)")

    # ---------- 4. memory_retrieval_log 检索日志表（验收 4） ----------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_retrieval_log (
            retrieval_id          TEXT PRIMARY KEY,
            memory_id             TEXT NOT NULL,
            retrieved_at          TEXT NOT NULL,
            retrieval_reason      TEXT NOT NULL,  -- 验收 4：为什么命中
            retrieval_usage       TEXT,           -- 验收 4：如何使用
            retrieval_context_json TEXT,          -- 验收 4：上下文（JSON），如 workflow、ticker
            consumer              TEXT,           -- 验收 4：谁用了（research_agent / user / router ...）
            hit_count_snapshot    INTEGER         -- 快照：命中次数记录时是多少
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_retrieval_log_memory ON memory_retrieval_log(memory_id)")


def get_memory(conn: sqlite3.Connection, memory_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT memory_id, entity_type, entity_id, memory_type, content, status, confidence,
               source_run_id, valid_from, valid_until, last_verified_at, created_at, updated_at,
               parent_memory_id, version, field_diff_json, reviewed_by, review_reason, reviewed_at,
               tags_json, project_id, hit_count, last_hit_at, session_id,
               preference_source, preference_explicit_ref, conflict_flag
        FROM memory_items WHERE memory_id=?
        """,
        (memory_id,),
    ).fetchone()
    if row is None:
        return None
    links = conn.execute(
        "SELECT evidence_id, relation, created_at FROM memory_evidence_links WHERE memory_id=? ORDER BY evidence_id, relation",
        (memory_id,),
    ).fetchall()
    logs = conn.execute(
        """SELECT review_id, action, previous_status, new_status, reviewer, reason, reviewed_at
           FROM memory_review_log WHERE memory_id=? ORDER BY reviewed_at DESC, review_id DESC""",
        (memory_id,),
    ).fetchall()
    return {
        "memory_id": row[0], "entity_type": row[1], "entity_id": row[2], "memory_type": row[3],
        "content": _loads(row[4], {}), "status": row[5], "confidence": row[6],
        "source_run_id": row[7],
        "valid_from": row[8], "valid_until": row[9], "last_verified_at": row[10],
        "created_at": row[11], "updated_at": row[12],
        "parent_memory_id": row[13], "version": int(row[14] or 1),
        "field_diff": _loads(row[15], []),
        "reviewed_by": row[16], "review_reason": row[17], "reviewed_at": row[18],
        # ====== 阶段 12 新增字段 ======
        "tags": _loads(row[19], []),
        "project_id": row[20],
        "hit_count": int(row[21] or 0),
        "last_hit_at": row[22],
        "session_id": row[23],
        "preference_source": row[24],
        "preference_explicit_ref": row[25],
        "conflict_flag": bool(row[26] or 0),
        # 关联表
        "evidence_links": [{"evidence_id": item[0], "relation": item[1], "created_at": item[2]} for item in links],
        "review_log": [
            {"review_id": item[0], "action": item[1], "previous_status": item[2], "new_status": item[3],
             "reviewer": item[4], "reason": item[5], "reviewed_at": item[6]}
            for item in logs
        ],
    }


def current_approved(
    conn: sqlite3.Connection, entity_type: str, entity_id: str, memory_type: str,
) -> dict[str, Any] | None:
    row = conn.execute(
        """SELECT memory_id FROM memory_items
           WHERE entity_type=? AND entity_id=? AND memory_type=? AND status='approved'
           ORDER BY version DESC, datetime(updated_at) DESC LIMIT 1""",
        (entity_type, entity_id, memory_type),
    ).fetchone()
    return get_memory(conn, row[0]) if row else None


def create_memory_candidate(
    conn: sqlite3.Connection, *, entity_type: str, entity_id: str, memory_type: str,
    content: dict[str, Any], evidence_links: list[dict[str, str]],
    source_run_id: str | None = None, confidence: float | None = None,
    tags: list[str] | None = None, project_id: str | None = None,
    session_id: str | None = None,
    preference_source: str | None = None,
    preference_explicit_ref: str | None = None,
) -> dict[str, Any]:
    """
    函数功能：创建一条「候选记忆 candidate」
    参数：
        entity_type/entity_id/memory_type  —— 三元组（实体类型、实体 ID、记忆类型），比如 stock/002396.SZ/valuation
        content                            —— 记忆内容（dict，不能空）
        evidence_links                     —— 证据链接 list[{evidence_id, relation}]；session_working/user_preference 可以空
        source_run_id                      —— 来源运行 ID（可选）
        confidence                         —— 置信度（0~1 浮点数，可选）
        tags                               —— 验收 3：标签（可选）
        project_id                         —— 验收 3：项目 ID（可选）
        session_id                         —— 验收 6：绑定会话 ID（仅会话工作记忆用）
        preference_source                  —— 验收 7：用户偏好必须指定合法来源（memory_type == 'user_preference' 时强制）
    返回值：创建好的记忆 dict
    异常：ValueError（参数校验失败）；sqlite3 异常（数据库写失败）
    """
    if not entity_type.strip() or not entity_id.strip() or not memory_type.strip():
        raise ValueError("memory entity and type are required")
    if not isinstance(content, dict) or not content:
        raise ValueError("memory content must be a non-empty object")

    # ====== 验收 7：user_preference 类型，来源必须是用户明确说的 ======
    if memory_type == "user_preference":
        if preference_source not in ALLOWED_PREFERENCE_SOURCES:
            raise ValueError(
                f"用户偏好(memory_type='user_preference')必须显式指定 preference_source，"
                f"合法值：{sorted(ALLOWED_PREFERENCE_SOURCES)}。禁止使用 'system_inferred'（AI 臆测）。"
            )
        if not (preference_explicit_ref or "").strip():
            raise ValueError(
                "用户偏好必须提供 preference_explicit_ref（引用用户原话的位置，例如'会话 s_abc 第 3 轮'）。"
            )

    # 证据校验：
    #   ✅ 强制要证据的类型（事实/论点类）：thesis, valuation, fundamental, technical, risk, event, research_fact, claim
    #   ✅ 可以无证据的类型（主观/框架/会话类）：session_working, user_preference, analysis_framework
    EVIDENCE_REQUIRED_TYPES = frozenset({
        "thesis", "valuation", "fundamental", "technical",
        "risk", "event", "research_fact", "claim",
    })
    normalized_links = []
    if memory_type in EVIDENCE_REQUIRED_TYPES and not evidence_links:
        raise ValueError(f"{memory_type} 类型记忆必须提供至少 1 条证据链接")
    for link in evidence_links:
        evidence_id = str(link.get("evidence_id") or "").strip()
        relation = str(link.get("relation") or "supports").strip()
        if evidence_links and (not evidence_id or relation not in ALLOWED_RELATIONS):
            raise ValueError("invalid memory evidence link")
        if evidence_id:
            normalized_links.append({"evidence_id": evidence_id, "relation": relation})

    approved = current_approved(conn, entity_type, entity_id, memory_type)
    row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) FROM memory_items WHERE entity_type=? AND entity_id=? AND memory_type=?",
        (entity_type, entity_id, memory_type),
    ).fetchone()
    version = int(row[0] or 0) + 1
    memory_id = f"memory_{uuid.uuid4().hex}"
    now = utc_now()
    diff = field_diff(approved["content"] if approved else {}, content)
    with immediate_transaction(conn):
        conn.execute(
            """
            INSERT INTO memory_items(
                memory_id, entity_type, entity_id, memory_type, content, status, confidence,
                source_run_id, created_at, updated_at, parent_memory_id, version, field_diff_json,
                tags_json, project_id, hit_count, last_hit_at, session_id,
                preference_source, preference_explicit_ref, conflict_flag
            ) VALUES (?, ?, ?, ?, ?, 'candidate', ?, ?, ?, ?, ?, ?, ?,
                      ?, ?, 0, NULL, ?,
                      ?, ?, 0)
            """,
            (
                memory_id, entity_type, entity_id, memory_type,
                json.dumps(content, ensure_ascii=False, sort_keys=True),
                confidence, source_run_id, now, now,
                approved["memory_id"] if approved else None, version,
                json.dumps(diff, ensure_ascii=False, sort_keys=True),
                json.dumps(tags or [], ensure_ascii=False, sort_keys=True),
                project_id,
                session_id,
                preference_source, preference_explicit_ref,
            ),
        )
        for link in normalized_links:
            conn.execute(
                "INSERT INTO memory_evidence_links(memory_id, evidence_id, relation, created_at) VALUES (?, ?, ?, ?)",
                (memory_id, link["evidence_id"], link["relation"], now),
            )
    return get_memory(conn, memory_id)  # type: ignore[return-value]


def edit_memory_candidate(
    conn: sqlite3.Connection, *, memory_id: str,
    content: dict[str, Any], evidence_links: list[dict[str, str]] | None = None,
    editor: str, edit_reason: str,
    tags: list[str] | None = None, project_id: str | None = None,
) -> dict[str, Any]:
    """
    函数功能（验收 2 - 编辑）：
        用户在"approve 之前"，修改 candidate 记忆的内容、证据、标签等。
        必须留下 review_log 痕迹，保证可审核。
    参数：
        memory_id      —— 要编辑的记忆 ID，必须是 candidate 状态
        content        —— 新内容（dict，非空）
        evidence_links —— 新证据链接（可 None 表示不修改）
        editor         —— 编辑人（非空）
        edit_reason    —— 编辑理由（非空）
        tags/project_id —— 验收 3：新标签/项目（可 None 表示不修改）
    返回值：编辑后的记忆 dict
    异常：KeyError（记忆不存在）；ValueError（状态不对或参数非法）
    """
    mem = get_memory(conn, memory_id)
    if mem is None:
        raise KeyError(f"unknown memory: {memory_id}")
    if mem["status"] != "candidate":
        raise ValueError(
            f"只有 candidate 状态的记忆可以编辑，当前状态={mem['status']}。"
            f"如果要修改已 approved 记忆，请新建 candidate 版本并走 approve 流程。"
        )
    if not isinstance(content, dict) or not content:
        raise ValueError("content 必须是非空 dict")
    editor = editor.strip()
    edit_reason = edit_reason.strip()
    if not editor or not edit_reason:
        raise ValueError("editor 和 edit_reason 都不能为空")

    now = utc_now()
    diff = field_diff(mem["content"], content)

    with immediate_transaction(conn):
        # 1) 更新 content / 字段
        conn.execute(
            """
            UPDATE memory_items
               SET content = ?,
                   field_diff_json = ?,
                   tags_json = COALESCE(?, tags_json),
                   project_id = COALESCE(?, project_id),
                   updated_at = ?,
                   conflict_flag = 0  -- 编辑后先撤销之前的冲突标记，等待下次重新评估
             WHERE memory_id = ?
            """,
            (
                json.dumps(content, ensure_ascii=False, sort_keys=True),
                json.dumps(diff, ensure_ascii=False, sort_keys=True),
                json.dumps(tags, ensure_ascii=False, sort_keys=True) if tags is not None else None,
                project_id,
                now,
                memory_id,
            ),
        )

        # 2) 如果传了新的 evidence_links，先删后插（整体替换）
        if evidence_links is not None:
            normalized = []
            for link in evidence_links:
                eid = str(link.get("evidence_id") or "").strip()
                rel = str(link.get("relation") or "supports").strip()
                if not eid or rel not in ALLOWED_RELATIONS:
                    raise ValueError("编辑记忆时 evidence_links 非法")
                normalized.append({"evidence_id": eid, "relation": rel})
            conn.execute("DELETE FROM memory_evidence_links WHERE memory_id=?", (memory_id,))
            for link in normalized:
                conn.execute(
                    "INSERT INTO memory_evidence_links(memory_id, evidence_id, relation, created_at) VALUES (?, ?, ?, ?)",
                    (memory_id, link["evidence_id"], link["relation"], now),
                )

        # 3) 写 review_log（动作 = "edit"）
        conn.execute(
            "INSERT INTO memory_review_log VALUES (?, ?, 'edit', 'candidate', 'candidate', ?, ?, ?)",
            (f"review_{uuid.uuid4().hex}", memory_id, editor, edit_reason, now),
        )

    return get_memory(conn, memory_id)  # type: ignore[return-value]


def review_memory(
    conn: sqlite3.Connection, memory_id: str, action: str, reviewer: str, reason: str,
) -> dict[str, Any]:
    memory = get_memory(conn, memory_id)
    if memory is None:
        raise KeyError(f"unknown memory: {memory_id}")
    reviewer = reviewer.strip()
    reason = reason.strip()
    if not reviewer or not reason:
        raise ValueError("reviewer and reason are required")
    new_status = ALLOWED_TRANSITIONS.get(memory["status"], {}).get(action)
    if not new_status:
        raise ValueError(f"action {action} is not allowed from {memory['status']}")
    now = utc_now()
    with immediate_transaction(conn):
        if action == "approve":
            previous = current_approved(conn, memory["entity_type"], memory["entity_id"], memory["memory_type"])
            if previous and previous["memory_id"] != memory_id:
                conn.execute(
                    "UPDATE memory_items SET status='archived', reviewed_by=?, review_reason=?, reviewed_at=?, updated_at=? WHERE memory_id=?",
                    (reviewer, reason, now, now, previous["memory_id"]),
                )
                conn.execute(
                    "INSERT INTO memory_review_log VALUES (?, ?, 'supersede', 'approved', 'archived', ?, ?, ?)",
                    (f"review_{uuid.uuid4().hex}", previous["memory_id"], reviewer, reason, now),
                )
        conn.execute(
            "UPDATE memory_items SET status=?, reviewed_by=?, review_reason=?, reviewed_at=?, updated_at=? WHERE memory_id=?",
            (new_status, reviewer, reason, now, now, memory_id),
        )
        conn.execute(
            "INSERT INTO memory_review_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"review_{uuid.uuid4().hex}", memory_id, action, memory["status"], new_status, reviewer, reason, now),
        )
    return get_memory(conn, memory_id)  # type: ignore[return-value]


# ============================================================
# 验收 3 + 4：记忆命中计数 + 检索日志
# ============================================================

def record_retrieval(
    conn: sqlite3.Connection, *, memory_id: str,
    retrieval_reason: str, retrieval_usage: str | None = None,
    retrieval_context: dict[str, Any] | None = None,
    consumer: str | None = None,
) -> str:
    """
    函数功能（验收 4 核心）：
        每次"某条记忆被命中并使用"时，写一条检索日志。
        回答「为什么命中 + 如何使用」两个关键问题。
    参数：
        memory_id          —— 被命中的记忆 ID
        retrieval_reason   —— 为什么命中（例如"300474 与 688256 同属 GPU 赛道"）—— 必填
        retrieval_usage    —— 如何使用（例如"写入报告 §2.2 作为行业比较段"）—— 可选但建议填
        retrieval_context  —— 上下文 dict（workflow、ticker、run_id 等）—— 可选
        consumer           —— 谁用的（research_agent_v3 / user / router）—— 可选
    返回值：retrieval_id（新建日志的 ID）
    异常：KeyError —— memory_id 不存在；ValueError —— retrieval_reason 空
    """
    mem = get_memory(conn, memory_id)
    if mem is None:
        raise KeyError(f"record_retrieval: memory_id={memory_id} 不存在")
    retrieval_reason = (retrieval_reason or "").strip()
    if not retrieval_reason:
        raise ValueError("record_retrieval: retrieval_reason 不能为空（要说明『为什么命中』）")

    retrieval_id = f"ret_{uuid.uuid4().hex}"
    now = utc_now()
    new_hit_count = mem["hit_count"] + 1

    with immediate_transaction(conn):
        # 1) 更新主表的 hit_count + last_hit_at（验收 3）
        conn.execute(
            "UPDATE memory_items SET hit_count = ?, last_hit_at = ?, updated_at = ? WHERE memory_id = ?",
            (new_hit_count, now, now, memory_id),
        )
        # 2) 写检索日志（验收 4）
        conn.execute(
            """
            INSERT INTO memory_retrieval_log(
                retrieval_id, memory_id, retrieved_at,
                retrieval_reason, retrieval_usage, retrieval_context_json,
                consumer, hit_count_snapshot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                retrieval_id, memory_id, now,
                retrieval_reason,
                (retrieval_usage or "").strip() or None,
                json.dumps(retrieval_context or {}, ensure_ascii=False, sort_keys=True),
                (consumer or "").strip() or None,
                new_hit_count,
            ),
        )
    return retrieval_id


def search_memories_with_hit_tracking(
    conn: sqlite3.Connection, *, entity_type: str, entity_id: str, memory_type: str | None = None,
    status: str = "approved", limit: int = 20,
    retrieval_reason: str = "", retrieval_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    函数功能（验收 3 包装）：
        按三元组检索 approved 记忆，对每条命中的记录都 +1 hit_count 并写 retrieval_log。
    参数：
        entity_type/entity_id  —— 必填（实体类型+ID）
        memory_type            —— 可选（None 表示该实体下所有记忆类型）
        status                 —— 只搜什么状态（默认 'approved'，保证 candidate 不会被误用！验收 1 隐含！）
        limit                  —— 最多返回多少条
        retrieval_reason       —— 为什么要检索（验收 4 必填）
        retrieval_context      —— 上下文（验收 4 可选）
    返回值：命中的记忆列表（[dict]）
    """
    retrieval_reason = (retrieval_reason or "").strip()
    if not retrieval_reason:
        raise ValueError("search_memories_with_hit_tracking: 必须提供 retrieval_reason（说明为什么命中）")

    where_sql = ["entity_type=?", "entity_id=?", "status=?"]
    params: list[Any] = [entity_type, entity_id, status]
    if memory_type:
        where_sql.append("memory_type=?")
        params.append(memory_type)

    sql = (
        "SELECT memory_id FROM memory_items WHERE "
        + " AND ".join(where_sql)
        + " ORDER BY hit_count DESC, datetime(updated_at) DESC LIMIT ?"
    )
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        mem_id = row[0]
        # 每条命中都记日志
        record_retrieval(
            conn, memory_id=mem_id,
            retrieval_reason=retrieval_reason,
            retrieval_usage=None,
            retrieval_context=retrieval_context,
            consumer=f"search:{entity_type}/{entity_id}" + (f"/{memory_type}" if memory_type else ""),
        )
        got = get_memory(conn, mem_id)
        if got is not None:
            results.append(got)
    return results


# ============================================================
# 验收 5：矛盾记忆并存 + 标记进入审核
# ============================================================

def flag_conflicting_memories(
    conn: sqlite3.Connection, *, entity_type: str, entity_id: str, memory_type: str,
) -> list[str]:
    """
    函数功能（验收 5）：
        在某实体 + 某记忆类型范围内，找出"多条 candidate 记忆并存"的情况，
        把它们全部打上 conflict_flag=1，表示"内容互相矛盾，请人工审核"。
        不会自动删除任何一条，全部保留并存进入审核。
    参数：entity_type/entity_id/memory_type 三元组
    返回值：被打上冲突标记的 memory_id 列表
    """
    rows = conn.execute(
        """SELECT memory_id, status FROM memory_items
           WHERE entity_type=? AND entity_id=? AND memory_type=?
           ORDER BY datetime(created_at) DESC""",
        (entity_type, entity_id, memory_type),
    ).fetchall()

    # 规则：同三元组下，candidate 数量 >= 2 → 认为"存在矛盾待审核"，全部打标
    # （小白解释：可能内容不一定真矛盾，但既然有 2+ 条候选没审核，说明需要用户判断，先保守打标）
    candidates = [r[0] for r in rows if r[1] == "candidate"]
    if len(candidates) < 2:
        return []

    now = utc_now()
    with immediate_transaction(conn):
        for mid in candidates:
            conn.execute(
                "UPDATE memory_items SET conflict_flag=1, updated_at=? WHERE memory_id=?",
                (now, mid),
            )
            # 留一条审核日志，说明被标记为冲突
            conn.execute(
                "INSERT INTO memory_review_log VALUES (?, ?, 'flag_conflict', 'candidate', 'candidate', 'system_auto', '同类型多条候选并存，进入审核', ?)",
                (f"review_{uuid.uuid4().hex}", mid, now),
            )
    return candidates


def list_conflicting_candidates(conn: sqlite3.Connection, limit: int = 100) -> list[dict[str, Any]]:
    """
    函数功能（验收 5 第 3 步）：
        列出所有 conflict_flag=1 的 candidate 记忆，等待人工审核。
    参数：limit —— 最多返回多少条
    返回值：记忆列表（带完整字段的 dict）
    """
    rows = conn.execute(
        """SELECT memory_id FROM memory_items
           WHERE status='candidate' AND conflict_flag=1
           ORDER BY datetime(updated_at) DESC, memory_id LIMIT ?""",
        (limit,),
    ).fetchall()
    results = []
    for row in rows:
        got = get_memory(conn, row[0])
        if got is not None:
            results.append(got)
    return results


# ============================================================
# 验收 6：删除会话只删会话级记忆，不碰正式研究记忆
# ============================================================

def delete_session_memories(conn: sqlite3.Connection, *, session_id: str) -> int:
    """
    函数功能（验收 6 核心）：
        删除某个会话下的所有"会话工作记忆"（entity_type='session' 或 session_id=给定值 且 memory_type='session_working'）。
        **绝对不会** 删 approved 状态的研究事实、用户偏好、分析框架等正式记忆。
    参数：session_id —— 要销毁的会话 ID
    返回值：实际删除了几条
    异常：sqlite3 异常（数据库写失败）
    """
    if not (session_id or "").strip():
        raise ValueError("delete_session_memories: session_id 不能为空")

    # 严格 WHERE 条件：session_id 匹配 + memory_type == 'session_working'
    # （故意没加 status 过滤 —— 会话记忆就算被 approve 了也要跟着会话走，但 session_working 类型本身就是临时的）
    rows = conn.execute(
        "SELECT memory_id FROM memory_items WHERE session_id=? AND memory_type='session_working'",
        (session_id,),
    ).fetchall()
    mem_ids = [r[0] for r in rows]
    if not mem_ids:
        return 0

    with immediate_transaction(conn):
        # 先清理关联表（外键没有就可以直接删，手动清保证干净）
        placeholders = ",".join(["?"] * len(mem_ids))
        conn.execute(f"DELETE FROM memory_evidence_links WHERE memory_id IN ({placeholders})", mem_ids)
        conn.execute(f"DELETE FROM memory_review_log WHERE memory_id IN ({placeholders})", mem_ids)
        conn.execute(f"DELETE FROM memory_retrieval_log WHERE memory_id IN ({placeholders})", mem_ids)
        # 最后删主表
        conn.execute(f"DELETE FROM memory_items WHERE memory_id IN ({placeholders})", mem_ids)
    return len(mem_ids)
