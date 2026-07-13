# Historical Phase bootstrap scripts

This directory contains frozen deployment and bootstrap generators from the
Phase-era implementation. They are retained for audit and recovery only.

- They are outside the current scheduler, API, and `smr_app` runtime paths.
- They must not be used as the normal local startup or migration entrypoint.
- Current database changes belong in `migrations/`.
- Current workflows belong in `smr_app/workflows/` and its adapters.

The first archived group is documented in
`legacy_manifest/removal-log-M5.md`.
