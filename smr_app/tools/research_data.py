from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from smr_app.acquisition.contracts import AcquisitionMode, AcquisitionProvider
from smr_app.acquisition.kernel import AcquisitionKernel
from smr_app.acquisition.providers.factory import capabilities, default_research_providers
from smr_app.acquisition.store import AcquisitionStore
from smr_app.research.data_requirements_v3 import requirement_from_manifest_item
from smr_app.runtime.migrations import apply_migrations


class ResearchDataTools:
    """Shared, auditable data acquisition facade for every governed workflow."""

    def __init__(
        self,
        db_path: str | Path,
        providers: Iterable[AcquisitionProvider] | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        apply_migrations(self.db_path)
        self.providers = tuple(providers or default_research_providers())
        self.store = AcquisitionStore(self.db_path)
        self.kernel = AcquisitionKernel(self.store, self.providers)

    def provider_status(self, *, probe_local_firecrawl: bool = False) -> dict[str, Any]:
        rows = []
        for provider in self.providers:
            row: dict[str, Any] = {
                "provider_id": provider.provider_id,
                "priority": provider.priority,
                "authority_tier": provider.authority_tier.value,
                "markets": sorted(provider.markets),
                "data_types": sorted(provider.data_types),
                "configured": True,
                "reachable": None,
                "detail": "",
                "mode": getattr(provider, "_transport_mode", None),
            }
            transport = getattr(provider, "_transport", None)
            base_url = getattr(transport, "base_url", None)
            if base_url:
                row["base_url"] = base_url
                hostname = (urlparse(base_url).hostname or "").lower()
                row["mode"] = getattr(provider, "_transport_mode", "http")
                if probe_local_firecrawl and hostname in {"127.0.0.1", "localhost"}:
                    try:
                        import requests  # type: ignore

                        response = requests.get(base_url, timeout=3)
                        row["reachable"] = response.status_code == 200
                        row["detail"] = f"HTTP {response.status_code}"
                    except Exception as exc:
                        row["reachable"] = False
                        row["detail"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            rows.append(row)
        return {
            "providers": rows,
            "capabilities": capabilities(self.providers),
            "all_configured": all(item["configured"] for item in rows),
            "local_firecrawl_reachable": all(
                item["reachable"] is not False
                for item in rows
                if item.get("mode") == "local_http"
            ),
        }

    def acquire_manifest(
        self,
        manifest: Mapping[str, Any],
        *,
        mode: AcquisitionMode = AcquisitionMode.REFRESH_IF_STALE,
        workflow_run_id: str | None = None,
        only_data_types: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        selected = set(only_data_types or ())
        results: dict[str, Any] = {}
        for item in manifest.get("requirements") or []:
            data_type = str(item.get("data_type") or "")
            if selected and data_type not in selected:
                continue
            requirement = requirement_from_manifest_item(item)
            result = self.kernel.acquire(
                requirement,
                mode=mode,
                workflow_run_id=workflow_run_id,
            )
            results[str(item["requirement_id"])] = {
                "request_id": result.request_id,
                "status": result.status,
                "provider_id": result.provider_id,
                "persisted_documents": result.persisted_documents,
                "persisted_facts": result.persisted_facts,
                "persisted_evidence_candidates": result.persisted_evidence_candidates,
                "dataset_state": asdict(result.dataset_state) if result.dataset_state else None,
                "errors": [dict(error) for error in result.errors],
            }
        return {
            "results": results,
            "succeeded": sum(
                result["status"] in {"acquired", "cache_hit"}
                for result in results.values()
            ),
            "failed": sum(
                result["status"] in {"failed", "cache_miss"}
                for result in results.values()
            ),
        }
