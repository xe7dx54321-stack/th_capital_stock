from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .contracts import AdapterResult, loads_json, relation_exists


@dataclass(frozen=True)
class EvidenceRequest:
    ticker: str
    limit: int = 30
    minimum_quality: float = 0.0


def load_evidence(conn: sqlite3.Connection, request: EvidenceRequest) -> AdapterResult:
    ticker = request.ticker.strip().upper()
    if not ticker:
        return AdapterResult("error", error="ticker is required")
    if not relation_exists(conn, "evidence_items"):
        return AdapterResult("missing", {"ticker": ticker, "count": 0, "items": []})

    linked_ids: set[str] = set()
    if relation_exists(conn, "research_claims") and relation_exists(conn, "claim_evidence_links"):
        linked_ids = {
            row[0]
            for row in conn.execute(
                """
                SELECT DISTINCT link.evidence_id
                FROM claim_evidence_links link
                JOIN research_claims claim ON claim.claim_id=link.claim_id
                WHERE UPPER(claim.ticker)=?
                """,
                (ticker,),
            ).fetchall()
            if row[0]
        }

    conditions = ["UPPER(COALESCE(metadata_json, '')) LIKE ?"]
    params: list[object] = [f"%{ticker}%"]
    if linked_ids:
        placeholders = ",".join("?" for _ in linked_ids)
        conditions.append(f"evidence_id IN ({placeholders})")
        params.extend(sorted(linked_ids))
    params.extend([float(request.minimum_quality), max(1, min(int(request.limit), 200))])
    rows = conn.execute(
        f"""
        SELECT evidence_id, source_key, source_type, source_quality, source_status,
               published_at, ingested_at, text_excerpt, url_or_doc_id, metadata_json,
               created_at, COALESCE(quality_score, 0), COALESCE(usable_for_core_claim, 0)
        FROM evidence_items
        WHERE ({' OR '.join(conditions)}) AND COALESCE(quality_score, 0)>=?
        ORDER BY COALESCE(usable_for_core_claim, 0) DESC,
                 COALESCE(quality_score, 0) DESC,
                 datetime(COALESCE(published_at, created_at)) DESC
        LIMIT ?
        """,
        tuple(params),
    ).fetchall()
    items = [
        {
            "evidence_id": row[0],
            "source_key": row[1],
            "source_type": row[2],
            "source_quality": row[3],
            "source_status": row[4],
            "published_at": row[5],
            "ingested_at": row[6],
            "text_excerpt": row[7],
            "url_or_doc_id": row[8],
            "metadata": loads_json(row[9], {}),
            "created_at": row[10],
            "quality_score": row[11],
            "usable_for_core_claim": bool(row[12]),
        }
        for row in rows
    ]
    status = "ok" if items else "missing"
    return AdapterResult(status, {"ticker": ticker, "count": len(items), "items": items})
