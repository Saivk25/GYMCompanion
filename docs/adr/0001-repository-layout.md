# ADR 0001: Repository layout follows the Engineering Master Plan's Section 2 exactly

- Status: accepted
- Date: 2026-07-29

## Context

The initial commit ("Initial project structure") created placeholder directories
(`frontend/`, top-level `tests/`, `assets/`, `datasets/`, `models/`) before the
Engineering Master Plan existed. That document's Section 2 specifies a concrete
monorepo layout (`apps/mobile/`, `backend/app/{domain,api,ai,infra,jobs}/`, `infra/`,
`docs/`, `scripts/`) with an explicit rationale for each folder, and explicitly
rejects a `packages/` workspace and a top-level `ai/` folder as premature.

## Decision

- `frontend/` is replaced by `apps/mobile/` (Flutter, Section 2's stated choice).
- Top-level `tests/` is scoped to `tests/e2e/` specifically, since backend and
  Flutter each get their own colocated test directories; an unscoped top-level
  `tests/` folder would have been ambiguous about what belongs there.
- `assets/`, `datasets/`, `models/` are kept from the initial commit, each with a
  README stating current status, rather than deleted — they cost nothing empty and
  the Engineering Master Plan doesn't say to remove them.
- The six planning documents move from the repository root into `docs/`, matching
  Section 2's description of that folder.

## Consequences

The repository now matches the frozen Engineering Master Plan exactly, so every
future ADR and sprint can reference paths from that document without translation.
