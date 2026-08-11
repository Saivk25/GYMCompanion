# Security Policy

## Current deployment status

Gym Companion has **no live, publicly-reachable deployment** as of this writing — the backend
has not been deployed to any hosting provider, and the Flutter client has not been published to
any app store (see `docs/adr/0054-testing-and-release-readiness.md`'s release-readiness
assessment and `docs/RELEASE_PROCESS.md`). This means today's security surface is the source
code and its dependency tree, not a running service with real user data. This policy will be
updated with live-service specifics (e.g. a bug bounty scope, a status page) once a real
deployment exists.

## Supported versions

This project is pre-1.0 (`0.x`) and does not yet maintain multiple supported release lines.
Only the latest commit on `master` receives security fixes.

| Version | Supported |
| ------- | --------- |
| `master` (latest) | ✅ |
| Anything else | ❌ |

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.** Instead:

1. Use GitHub's private vulnerability reporting (this repository's **Security** tab → **Report
   a vulnerability**), if enabled, **or**
2. Email **<saibalaji250904@gmail.com>** with a description of the issue, steps to reproduce, and
   its potential impact.

You should receive an acknowledgment within a few days. This is a single-maintainer project run
outside of working hours, so response times will not match a company with a dedicated security
team — please be patient, and note that a slow response does not mean the report was ignored.

Please include, where relevant:

- The component affected (`backend/` vs. `apps/mobile/`) and the specific file/endpoint/screen.
- A minimal reproduction.
- The potential impact (what an attacker could actually do).
- Whether you believe this is already covered by a known, disclosed gap in
  `docs/TECH_DEBT.md` (some architectural trade-offs — e.g. `docs/adr/0033`'s resource-ownership
  authorization scope — are already documented; a report that names a genuinely new issue is far
  more valuable than one that rediscovers a disclosed one, but when in doubt, report it anyway).

## Scope

In scope:

- `backend/app/` — authentication, authorization, input validation, data isolation between
  users (row-level security, see `backend/app/infra/database.py`'s `tenant_scope()`).
- `apps/mobile/lib/` — token storage (`SecureTokenStorage`), network layer
  (`lib/core/network/`), and any client-side handling of sensitive data.
- Supply-chain issues in this repository's own dependency manifests
  (`backend/pyproject.toml`/`requirements-lock.txt`, `apps/mobile/pubspec.yaml`) and CI
  configuration (`.github/workflows/`).

Out of scope:

- Findings that require physical access to an already-compromised device.
- Denial-of-service reports based purely on volume (this project has no production
  infrastructure to protect yet).
- Issues already tracked publicly in `docs/TECH_DEBT.md` with a known, accepted trade-off (you're
  still welcome to report these — see above — but they won't be treated as novel disclosures).

## Disclosure

Please give us a reasonable window to address a confirmed vulnerability before any public
disclosure. There is no bug bounty program at this time.
