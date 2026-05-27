# Phase 31 Evidence Candidate Review Queue + Manual Evidence Governance

## Goal

Phase 31 turns persisted semantic evidence candidates into governed evidence
assets. The phase adds lifecycle status, review queues, manual governance
actions, audit logs, repair queues, sensitive-variable guards, and revalidation.
It does not expand extraction scope or relax promotion rules.

## Starting Point

- Current checkpoint: `3887e24dc182f5b523c058f2e476e94504b96b36`.
- Phase 30 persisted semantic evidence candidates: `60`.
- `review_required=1`.
- `eligible_for_persistence=60`.
- `evidence_candidates_removed=1`.
- `usable_for_promotion_true=0`.
- `confirmed_variables_added=0`.
- `new_pending_created=0`.

## Implementation

1. Add evidence lifecycle schema for persisted, pending-review, approved,
   rejected, downgraded, marked-noise, needs-better-source, linked, archived,
   and removed states.
2. Add review queue output for weak candidates, review-required candidates,
   sensitive-variable candidates, rejected/noisy candidates, and download repair
   tasks.
3. Add manual review actions: approve, reject, downgrade usage, mark noise,
   request better source, link to variable pack, and archive.
4. Add append-only audit log for execute-mode actions.
5. Add governance dashboard with lifecycle distribution, sensitive flags,
   variable-pack linkage, and promotion-safety checks.
6. Add download-unavailable repair queue with idempotent upsert.
7. Add sensitive variable guard for supplier share, ASP, customer allocation,
   official consensus, and confirmed-order claims.
8. Add variable pack link audit and governance revalidation.

## Guardrails

- Persisted candidates are not automatically approved evidence.
- Approved evidence is not promotion evidence.
- `usable_for_promotion` remains false.
- Review actions cannot create confirmed supplier share, confirmed ASP,
  confirmed customer allocation, official consensus, pending review, paper
  orders, or real trades.
- Rejected, removed, and archived evidence retains auditability.
- Download repair tasks do not bypass download limits and do not enable OCR by
  default.
- Reports do not store raw source text.

## Validation

Run py_compile, full unittest discovery, Phase 3/4/5/6/14 regression commands,
Phase 30 hardening summary, Phase 31 review queue, manual action dry-runs,
audit report, governance dashboard, download repair queue summary, sensitive
guard validator, variable pack link audit, governance revalidation, and
connector dashboard.
