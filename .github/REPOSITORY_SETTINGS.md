# Repository settings (GitHub website configuration)

The items below live in GitHub's own repository settings, not in a file this repository can
commit — they only take effect once this project has a real GitHub remote. This document is
the checklist for whoever administers the repository to apply by hand under **Settings** (or
the repo's top-right ⚙️/pencil icon next to the description), so nothing gets forgotten or
improvised inconsistently later.

## Repository description

Set via the pencil icon next to "About" on the repo's main page:

> A fitness-companion system with a FastAPI backend (Clean Architecture, deterministic rule
> engines) and a Flutter mobile client (6 feature modules). Every architectural decision is
> recorded as an ADR.

Keep it under ~140 characters (GitHub truncates longer descriptions in search results and the
repo list view).

## Topics

Add under the same "About" panel → Topics:

`flutter` · `fastapi` · `python` · `dart` · `clean-architecture` · `domain-driven-design` ·
`riverpod` · `rule-engine` · `fitness-app` · `mobile-app` · `rest-api` · `postgresql`

Topics drive GitHub's own topic-search discoverability — pick ones that are both accurate
(don't add `machine-learning`; `backend/app/ai/` is an empty, planned adapter layer, not a
shipped ML feature — see `docs/TECH_DEBT.md`) and ones a real developer would actually search.

## Social preview image

**Settings → General → Social preview.** GitHub renders this 1280×640px image when the repo
link is shared on social media / Slack / Discord. No image exists yet — a real one should be
generated from an actual app screenshot once `docs/screenshots/` is populated (see that
directory's own `README.md`), not a stock graphic that misrepresents what the project looks
like. Until then, GitHub falls back to a generic placeholder — acceptable for now, not worth
faking.

## Repository Discussions

**Settings → General → Features → Discussions.** Recommended to enable once this repo has
outside visitors — it gives a place for "why was X built this way" questions that aren't bug
reports (the issue template's `config.yml` already links to it). Suggested initial categories:

- **Q&A** — questions about running or understanding the codebase.
- **Ideas** — feature suggestions that aren't yet a concrete, actionable issue.
- **Show and tell** — not really applicable for a single-app portfolio project; optional to
  disable.

## Labels

GitHub ships a default label set; the issue templates in this repo already apply `bug`,
`enhancement`, `triage`, `dependencies`, `backend`, `mobile`, `ci`, `docker`, `documentation`,
and `security` — create any of these that don't already exist under **Settings → Labels**, or
via the GitHub CLI:

```bash
gh label create backend       --color 1D76DB --description "backend/ (FastAPI service)"
gh label create mobile        --color 5319E7  --description "apps/mobile/ (Flutter client)"
gh label create triage        --color D93F0B  --description "Needs initial review/labeling"
gh label create documentation --color 0075CA  --description "docs/, README, ADRs"
gh label create security      --color B60205  --description "Security-relevant"
gh label create ci            --color FBCA04  --description "GitHub Actions / CI configuration"
gh label create docker        --color 0E8A16  --description "Dockerfile / container image"
```

(`dependencies`, `bug`, and `enhancement` already exist as GitHub defaults.)

## Branch protection

**Settings → Branches → Add branch protection rule** for `master`, once this repo is pushed:

- Require a pull request before merging (no direct pushes, including from the owner, if you
  want the discipline enforced rather than just documented in `CONTRIBUTING.md`).
- Require status checks to pass: the jobs defined in `.github/workflows/ci.yml`
  (`backend-quality`, `backend-test`, `docker-build`, `mobile`) plus
  `.github/workflows/codeql.yml` and `.github/workflows/markdown-lint.yml` once they've run at
  least once (GitHub only lists checks that have executed on this repo before).
- Require branches to be up to date before merging.

## First-push checklist

1. `git remote add origin https://github.com/<owner>/<repo>.git`
2. `git push -u origin master`
3. Apply the description, topics, and social preview above.
4. Enable Discussions if desired.
5. Create the labels above (or run the `gh label create` block).
6. Add branch protection on `master`.
7. Replace every `TODO-github-username`/`<owner>/<repo>` placeholder in this repository
   (`README.md`, `CITATION.cff`, `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/config.yml`) with
   the real values — `grep -rn "TODO-github-username" .` finds them all.
