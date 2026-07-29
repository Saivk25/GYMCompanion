#!/usr/bin/env python3
"""Fails if any Alembic migration's upgrade() path contains a destructive
operation without an explicit review marker.

Implements the Engineering Master Plan's CI/CD section (migration strategy
row): "Alembic, additive-by-default; no destructive migration runs without
a prior backup step, enforced by a CI check on migration file content."

This is deliberately a narrow, high-signal check, not a general SQL safety
linter: it looks for the small set of operations that unconditionally
destroy data (drop table, drop column, truncate) inside `upgrade()`, since
that's the path every normal deploy runs. `downgrade()` is expected to
contain drops (undoing a create) and is not scanned — rolling back a
migration is already an exceptional, manual action, not something that
runs unattended.

To acknowledge an intentional destructive migration (the backup step the
Engineering Master Plan requires happened out of band), add this exact
comment anywhere in the file:

    # destructive-migration-reviewed: <why, and where the backup lives>

Usage: python scripts/check_destructive_migrations.py
Exit status: 0 if clean, 1 if any unacknowledged destructive migration is found.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSIONS_DIR = REPO_ROOT / "backend" / "alembic" / "versions"

ACK_MARKER = "destructive-migration-reviewed"

# Matches both the Alembic op helpers and raw SQL fallbacks (op.execute),
# since this migration set already uses raw SQL for anything Alembic has
# no op for (see the Step 10 RLS migration).
DESTRUCTIVE_PATTERNS = [
    re.compile(r"op\.drop_table\s*\("),
    re.compile(r"op\.drop_column\s*\("),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+COLUMN\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
]


def upgrade_body(source: str) -> str:
    """Returns just the text of the upgrade() function, so downgrade()'s
    legitimate drops (undoing a create) are never flagged."""
    match = re.search(r"def upgrade\s*\([^)]*\)[^:]*:", source)
    if not match:
        return ""
    start = match.end()
    next_def = re.search(r"\ndef \w+\s*\(", source[start:])
    end = start + next_def.start() if next_def else len(source)
    return source[start:end]


def check_file(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    if ACK_MARKER in source:
        return []

    findings = []
    body = upgrade_body(source)
    for pattern in DESTRUCTIVE_PATTERNS:
        for match in pattern.finditer(body):
            line_number = body.count("\n", 0, match.start()) + 1
            findings.append(f"{path.relative_to(REPO_ROOT)}:~{line_number}: {match.group(0)!r}")
    return findings


def main() -> int:
    if not VERSIONS_DIR.is_dir():
        print(f"no migrations directory at {VERSIONS_DIR}, nothing to check")
        return 0

    all_findings = []
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        all_findings.extend(check_file(path))

    if all_findings:
        print("Destructive operation(s) found in migration upgrade() without review marker:")
        for finding in all_findings:
            print(f"  {finding}")
        print()
        print(
            f"If this is intentional and a backup step happened out of band, "
            f"add a '# {ACK_MARKER}: <why>' comment to the file."
        )
        return 1

    print("No unacknowledged destructive migrations found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
