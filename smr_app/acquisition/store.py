from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import (
    AcquisitionBatch,
    AcquisitionMode,
    AcquisitionRequest,
    AuthorityTier,
    DataRequirement,
    DatasetState,
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


class AcquisitionStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=15000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def _connection(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_request(self, request: AcquisitionRequest) -> None:
        requirement = request.requirement
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO acquisition_request(
                    request_id, workflow_run_id, entity_key, data_type, market, as_of, mode,
                    required_fields_json, maximum_age_seconds, minimum_authority, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    request.request_id,
                    request.workflow_run_id,
                    requirement.entity_key,
                    requirement.data_type,
                    requirement.market,
                    requirement.as_of,
                    request.mode.value,
                    _json(requirement.required_fields),
                    int(requirement.maximum_age.total_seconds()) if requirement.maximum_age is not None else None,
                    requirement.minimum_authority.value,
                    request.created_at,
                ),
            )

    def finish_request(self, request_id: str, status: str, completed_at: str, summary: dict[str, Any] | None = None) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE acquisition_request SET status=?, completed_at=?, summary_json=? WHERE request_id=?",
                (status, completed_at, _json(summary or {}), request_id),
            )

    def start_run(self, request_id: str, provider_id: str, started_at: str) -> str:
        run_id = f"acqrun_{uuid.uuid4().hex}"
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO acquisition_run(run_id, request_id, provider_id, status, started_at) VALUES (?, ?, ?, 'running', ?)",
                (run_id, request_id, provider_id, started_at),
            )
        return run_id

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        completed_at: str,
        error: Exception | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE acquisition_run
                SET status=?, completed_at=?, error_code=?, error_message=?, summary_json=?
                WHERE run_id=?
                """,
                (
                    status,
                    completed_at,
                    type(error).__name__ if error else None,
                    str(error)[:2000] if error else None,
                    _json(summary or {}),
                    run_id,
                ),
            )

    def get_dataset_state(self, requirement: DataRequirement) -> DatasetState | None:
        with self._connection() as conn:
            row = self._get_dataset_state_row(conn, requirement)
        return self._dataset_state(row) if row else None

    @staticmethod
    def _get_dataset_state_row(conn, requirement: DataRequirement):
        return conn.execute(
            "SELECT * FROM dataset_state WHERE entity_key=? AND data_type=? AND market=?",
            (requirement.entity_key, requirement.data_type, requirement.market),
        ).fetchone()

    def upsert_dataset_state(self, state: DatasetState) -> None:
        with self._connection() as conn:
            self._upsert_dataset_state(conn, state)

    @staticmethod
    def _upsert_dataset_state(conn: sqlite3.Connection, state: DatasetState) -> None:
        conn.execute(
            """
            INSERT INTO dataset_state(
                entity_key, data_type, market, available_through, last_checked_at,
                last_successful_fetch_at, required_fields_present_json, quality_status,
                is_complete, source_ids_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_key, data_type, market) DO UPDATE SET
                available_through=excluded.available_through,
                last_checked_at=excluded.last_checked_at,
                last_successful_fetch_at=excluded.last_successful_fetch_at,
                required_fields_present_json=excluded.required_fields_present_json,
                quality_status=excluded.quality_status,
                is_complete=excluded.is_complete,
                source_ids_json=excluded.source_ids_json,
                metadata_json=excluded.metadata_json
            """,
            (
                state.entity_key,
                state.data_type,
                state.market,
                state.available_through,
                state.last_checked_at,
                state.last_successful_fetch_at,
                _json(state.required_fields_present),
                state.quality_status,
                1 if state.is_complete else 0,
                _json(state.source_ids),
                _json(state.metadata),
            ),
        )

    @staticmethod
    def _dataset_state(row: sqlite3.Row) -> DatasetState:
        return DatasetState(
            entity_key=row["entity_key"],
            data_type=row["data_type"],
            market=row["market"],
            available_through=row["available_through"],
            last_checked_at=row["last_checked_at"],
            last_successful_fetch_at=row["last_successful_fetch_at"],
            required_fields_present=tuple(_loads(row["required_fields_present_json"], [])),
            quality_status=row["quality_status"],
            is_complete=bool(row["is_complete"]),
            source_ids=tuple(_loads(row["source_ids_json"], [])),
            metadata=_loads(row["metadata_json"], {}),
        )

    def persist_batch(
        self,
        request: AcquisitionRequest,
        provider_id: str,
        batch: AcquisitionBatch,
        completed_at: str,
    ) -> tuple[int, int, int, DatasetState, int]:
        documents = {item.document_id: item for item in batch.documents}
        referenced = {
            fact.source_document_id for fact in batch.facts
        } | {
            document_id
            for candidate in batch.evidence_candidates
            for document_id in candidate.source_document_ids
        }
        unknown = referenced - set(documents)
        if unknown:
            raise ValueError(f"batch references unknown source documents: {sorted(unknown)}")

        inserted_documents = 0
        inserted_facts = 0
        inserted_candidates = 0
        conflicts = 0
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                for document in batch.documents:
                    cursor = conn.execute(
                        """
                        INSERT OR IGNORE INTO source_document(
                            document_id, acquisition_request_id, source_id, entity_key, data_type,
                            source_type, authority_tier, source_url, title, published_at, fetched_at,
                            content_hash, raw_text, raw_payload_json, parser_version, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            document.document_id,
                            request.request_id,
                            document.source_id,
                            document.entity_key,
                            document.data_type,
                            document.source_type,
                            document.authority_tier.value,
                            document.source_url,
                            document.title,
                            document.published_at,
                            document.fetched_at,
                            document.content_hash,
                            document.raw_text,
                            _json(document.raw_payload),
                            document.parser_version,
                            _json(document.metadata),
                        ),
                    )
                    inserted_documents += max(0, cursor.rowcount)

                for fact in batch.facts:
                    conflict = conn.execute(
                        """
                        SELECT fact_id, value_json FROM normalized_fact
                        WHERE entity_key=? AND data_type=? AND field_name=?
                          AND COALESCE(as_of, '')=COALESCE(?, '')
                          AND COALESCE(unit, '')=COALESCE(?, '')
                          AND verification_status='verified'
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (fact.entity_key, fact.data_type, fact.field_name, fact.as_of, fact.unit),
                    ).fetchone()
                    stored_fact = fact
                    if conflict and _loads(conflict["value_json"], None) != fact.value:
                        conflicts += 1
                        stored_fact = replace(
                            fact,
                            verification_status="conflict",
                            metadata={**dict(fact.metadata), "conflicts_with_fact_id": conflict["fact_id"]},
                        )
                    cursor = conn.execute(
                        """
                        INSERT OR IGNORE INTO normalized_fact(
                            fact_id, acquisition_request_id, entity_key, data_type, field_name,
                            value_json, unit, period_start, period_end, as_of, source_document_id,
                            authority_tier, verification_status, confidence, metadata_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            stored_fact.fact_id,
                            request.request_id,
                            stored_fact.entity_key,
                            stored_fact.data_type,
                            stored_fact.field_name,
                            _json(stored_fact.value),
                            stored_fact.unit,
                            stored_fact.period_start,
                            stored_fact.period_end,
                            stored_fact.as_of,
                            stored_fact.source_document_id,
                            stored_fact.authority_tier.value,
                            stored_fact.verification_status,
                            stored_fact.confidence,
                            _json(stored_fact.metadata),
                            completed_at,
                        ),
                    )
                    inserted_facts += max(0, cursor.rowcount)

                for candidate in batch.evidence_candidates:
                    cursor = conn.execute(
                        """
                        INSERT OR IGNORE INTO evidence_candidate(
                            candidate_id, acquisition_request_id, entity_key, data_type, claim_type,
                            text, source_document_ids_json, authority_tier, occurred_at,
                            usable_for_json, status, metadata_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            candidate.candidate_id,
                            request.request_id,
                            candidate.entity_key,
                            candidate.data_type,
                            candidate.claim_type,
                            candidate.text,
                            _json(candidate.source_document_ids),
                            candidate.authority_tier.value,
                            candidate.occurred_at,
                            _json(candidate.usable_for),
                            candidate.status,
                            _json(candidate.metadata),
                            completed_at,
                        ),
                    )
                    inserted_candidates += max(0, cursor.rowcount)

                prior_row = self._get_dataset_state_row(conn, request.requirement)
                prior = self._dataset_state(prior_row) if prior_row else None
                source_ids = tuple(dict.fromkeys([*(prior.source_ids if prior else ()), provider_id]))
                present = tuple(dict.fromkeys([*(prior.required_fields_present if prior else ()), *batch.required_fields_present]))
                quality_status = "conflict" if conflicts else batch.quality_status
                state = DatasetState(
                    entity_key=request.requirement.entity_key,
                    data_type=request.requirement.data_type,
                    market=request.requirement.market,
                    available_through=batch.available_through or (prior.available_through if prior else None),
                    last_checked_at=completed_at,
                    last_successful_fetch_at=completed_at,
                    required_fields_present=present,
                    quality_status=quality_status,
                    is_complete=batch.is_complete and not conflicts,
                    source_ids=source_ids,
                    metadata={**(dict(prior.metadata) if prior else {}), **dict(batch.metadata)},
                )
                self._upsert_dataset_state(conn, state)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return inserted_documents, inserted_facts, inserted_candidates, state, conflicts

    def count(self, table: str) -> int:
        allowed = {"acquisition_request", "acquisition_run", "source_document", "normalized_fact", "evidence_candidate", "dataset_state"}
        if table not in allowed:
            raise ValueError("unsupported table")
        with self._connection() as conn:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def list_runs(self, request_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM acquisition_run WHERE request_id=? ORDER BY started_at, rowid",
                (request_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_facts(self, entity_key: str, data_type: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM normalized_fact WHERE entity_key=? AND data_type=? ORDER BY created_at, rowid",
                (entity_key, data_type),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["value"] = _loads(item.pop("value_json"), None)
            item["metadata"] = _loads(item.pop("metadata_json"), {})
            result.append(item)
        return result

    def list_documents(self, entity_key: str, data_type: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM source_document WHERE entity_key=? AND data_type=? "
                "ORDER BY COALESCE(published_at, fetched_at) DESC, rowid DESC",
                (entity_key, data_type),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["raw_payload"] = _loads(item.pop("raw_payload_json"), {})
            item["metadata"] = _loads(item.pop("metadata_json"), {})
            result.append(item)
        return result

    def list_evidence_candidates(self, entity_key: str, data_type: str | None = None) -> list[dict[str, Any]]:
        params: tuple[Any, ...]
        if data_type:
            where = "entity_key=? AND data_type=?"
            params = (entity_key, data_type)
        else:
            where = "entity_key=?"
            params = (entity_key,)
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM evidence_candidate WHERE {where} ORDER BY created_at DESC, rowid DESC",
                params,
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["source_document_ids"] = _loads(item.pop("source_document_ids_json"), [])
            item["usable_for"] = _loads(item.pop("usable_for_json"), [])
            item["metadata"] = _loads(item.pop("metadata_json"), {})
            result.append(item)
        return result
