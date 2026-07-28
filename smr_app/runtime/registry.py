from __future__ import annotations

from collections.abc import Iterable

from .contracts import WorkflowDefinition


PRODUCTION_WORKFLOW_IDS = frozenset(
    {
        "daily_brief",
        "stock_deep_dive",
        "thesis_update",
        "portfolio_review",
        "operating_driver_valuation",
        "pair_switch_decision",
        "theme_expectation_gap",
        "industry_causal_explainer",
        "company_signal_plan",
        "claim_correction",
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
        "operating_driver_valuation": (
            "Operating driver valuation",
            "Build a deterministic valuation model from operating driver assumptions.",
        ),
        "pair_switch_decision": (
            "Pair switch decision V1",
            "Side-by-side comparison and four-scenario decision for switching a pair of tickers.",
        ),
        "theme_expectation_gap": (
            "Theme expectation gap V1",
            "8-dimension deterministic ranking of theme candidates with transparent universe.",
        ),
        "company_signal_plan": (
            "Company signal plan V1",
            "Signal registry (4-state) + 3 transmission timelines + position readiness gate.",
        ),
        "industry_causal_explainer": (
            "Industry causal explainer V1",
            "Evidence-aware eight-step causal chain with alternatives and falsification conditions.",
        ),
        "claim_correction": (
            "Claim correction",
            "Correct an evidence-backed claim and deterministically recompute every dependent claim.",
        ),
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
        elif workflow_id == "operating_driver_valuation":
            from smr_app.workflows.operating_driver_valuation import (
                operating_driver_valuation_definition,
            )

            definitions.append(operating_driver_valuation_definition())
        elif workflow_id == "pair_switch_decision":
            from smr_app.workflows.pair_switch_decision import (
                pair_switch_decision_definition,
            )

            definitions.append(pair_switch_decision_definition())
        elif workflow_id == "theme_expectation_gap":
            from smr_app.workflows.theme_expectation_gap import (
                theme_expectation_gap_definition,
            )

            definitions.append(theme_expectation_gap_definition())
        elif workflow_id == "company_signal_plan":
            from smr_app.workflows.company_signal_plan import (
                company_signal_plan_definition,
            )

            definitions.append(company_signal_plan_definition())
        elif workflow_id == "industry_causal_explainer":
            from smr_app.workflows.industry_causal_explainer import (
                industry_causal_explainer_definition,
            )

            definitions.append(industry_causal_explainer_definition())
        elif workflow_id == "claim_correction":
            from smr_app.workflows.claim_correction import claim_correction_definition

            definitions.append(claim_correction_definition())
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
