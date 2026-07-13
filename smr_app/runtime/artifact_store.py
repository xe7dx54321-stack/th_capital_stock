from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterable

from .event_store import immediate_transaction, utc_now


class ArtifactPathError(ValueError):
    pass


class ArtifactStore:
    def __init__(self, conn: sqlite3.Connection, allowed_roots: Iterable[str | Path]):
        self.conn = conn
        self.allowed_roots = [Path(root).resolve() for root in allowed_roots]
        if not self.allowed_roots:
            raise ValueError("At least one artifact root is required")

    def _relative_location(self, path: str | Path) -> tuple[int, Path, Path]:
        resolved = Path(path).resolve()
        for index, root in enumerate(self.allowed_roots):
            try:
                relative = resolved.relative_to(root)
            except ValueError:
                continue
            return index, relative, resolved
        raise ArtifactPathError(f"Artifact path is outside allowed roots: {resolved}")

    def register_artifact(
        self,
        run_id: str,
        artifact_type: str,
        title: str,
        path: str | Path,
        mime_type: str,
        *,
        metadata: dict[str, Any] | None = None,
        artifact_id: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        root_index, relative, _resolved = self._relative_location(path)
        artifact_id = artifact_id or f"artifact_{uuid.uuid4().hex}"
        created_at = created_at or utc_now()
        stored_metadata = {**(metadata or {}), "artifact_root_index": root_index}
        relative_path = relative.as_posix()
        with immediate_transaction(self.conn):
            self.conn.execute(
                """
                INSERT INTO workflow_artifacts(
                    artifact_id, run_id, artifact_type, title, relative_path,
                    mime_type, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    run_id,
                    artifact_type,
                    title,
                    relative_path,
                    mime_type,
                    json.dumps(stored_metadata, ensure_ascii=False, sort_keys=True),
                    created_at,
                ),
            )
        return {
            "artifact_id": artifact_id,
            "run_id": run_id,
            "artifact_type": artifact_type,
            "title": title,
            "relative_path": relative_path,
            "mime_type": mime_type,
            "metadata": stored_metadata,
            "created_at": created_at,
        }

    def resolve_artifact(self, artifact_id: str) -> Path:
        row = self.conn.execute(
            "SELECT relative_path, metadata_json FROM workflow_artifacts WHERE artifact_id=?",
            (artifact_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown artifact: {artifact_id}")
        relative = Path(row[0])
        if relative.is_absolute():
            raise ArtifactPathError("Stored artifact path must be relative")
        metadata = json.loads(row[1] or "{}")
        root_index = int(metadata.get("artifact_root_index", 0))
        if root_index < 0 or root_index >= len(self.allowed_roots):
            raise ArtifactPathError("Stored artifact root is not allowed")
        root = self.allowed_roots[root_index]
        resolved = (root / relative).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ArtifactPathError("Stored artifact path escapes its allowed root") from exc
        return resolved
