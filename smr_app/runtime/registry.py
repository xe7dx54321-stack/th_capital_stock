from __future__ import annotations

from collections.abc import Iterable

from .contracts import WorkflowDefinition


PRODUCTION_WORKFLOW_IDS = frozenset(
    {
        "daily_brief",
        "stock_deep_dive",
        "thesis_update",
        "portfolio_review",
    }
)


class WorkflowRegistry:
    def __init__(self, definitions: Iterable[WorkflowDefinition]):
        self._definitions = {definition.workflow_id: definition for definition in definitions}

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))

    def list(self) -> list[WorkflowDefinition]:
        return [self._definitions[workflow_id] for workflow_id in self.ids()]

    def get(self, workflow_id: str) -> WorkflowDefinition:
        try:
            return self._definitions[workflow_id]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow_id: {workflow_id}") from exc


def production_registry() -> WorkflowRegistry:
    metadata = {
        "daily_brief": ("Daily brief", "Summarize material changes for the day."),
        "stock_deep_dive": ("Stock deep dive", "Build an evidence-backed company research report."),
        "thesis_update": ("Thesis update", "Propose a governed update to an investment thesis."),
        "portfolio_review": ("Portfolio review", "Review paper portfolio risk and decisions."),
    }
    definitions = []
    for workflow_id in sorted(PRODUCTION_WORKFLOW_IDS):
        if workflow_id == "stock_deep_dive":
            from smr_app.workflows.stock_deep_dive import stock_deep_dive_definition

            definitions.append(stock_deep_dive_definition())
        elif workflow_id == "daily_brief":
            from smr_app.workflows.daily_brief import daily_brief_definition

            definitions.append(daily_brief_definition())
        elif workflow_id == "portfolio_review":
            from smr_app.workflows.portfolio_review import portfolio_review_definition

            definitions.append(portfolio_review_definition())
        elif workflow_id == "thesis_update":
            from smr_app.workflows.thesis_update import thesis_update_definition

            definitions.append(thesis_update_definition())
        else:
            definitions.append(
                WorkflowDefinition(
                    workflow_id=workflow_id,
                    title=metadata[workflow_id][0],
                    description=metadata[workflow_id][1],
                    enabled=False,
                )
            )
    return WorkflowRegistry(definitions)
