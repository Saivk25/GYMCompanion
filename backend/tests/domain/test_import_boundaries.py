"""Statically proves the Domain Core's one architectural rule: "Domain
depends on nothing except the Python standard library."

This does not trust the rule to hold by convention or code review alone —
it parses every file under `app/domain/` with `ast` and inspects its
`import` statements directly, so a violation fails a test the moment it's
written, in this file or in any future one added under `app/domain/` for
Sprint 2 onward's aggregates. No import ever needs to actually execute for
this to catch it, which is what makes it reliable even for an import
nobody has exercised yet.

Two rules, both absolute:

1. Every absolute import's top-level name must be either a Python standard
   library module (checked against `sys.stdlib_module_names` — a positive
   allow-list, not a denylist of packages this project happens to use
   today, so a *new* forbidden dependency is caught automatically) or
   another `app.domain` module.
2. No relative imports (`from . import x`, `from .. import y`) at all —
   the rest of this codebase already uses only absolute imports
   throughout (see the codebase's own convention), so this doesn't cost
   `app/domain` anything, and it means this test never has to resolve
   what a relative import actually points to in order to check it.
"""

import ast
import sys
from pathlib import Path

import pytest

DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "app" / "domain"

_STDLIB_MODULES = set(sys.stdlib_module_names) | {"__future__"}


def _domain_source_files() -> list[Path]:
    return sorted(DOMAIN_ROOT.rglob("*.py"))


def _is_allowed_absolute_import(module_name: str) -> bool:
    top_level = module_name.split(".")[0]
    if top_level in _STDLIB_MODULES:
        return True
    return module_name == "app.domain" or module_name.startswith("app.domain.")


def _violations_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _is_allowed_absolute_import(alias.name):
                    violations.append(f"imports {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                violations.append(
                    f"uses a relative import ({'.' * node.level}{node.module or ''}) "
                    f"— use an absolute app.domain... import instead"
                )
            elif node.module and not _is_allowed_absolute_import(node.module):
                violations.append(f"imports from {node.module!r}")

    return violations


@pytest.mark.unit
def test_domain_package_has_python_files_to_check() -> None:
    """A guard against this test silently checking nothing — e.g. if
    DOMAIN_ROOT's path computation ever breaks after a directory move."""
    assert len(_domain_source_files()) > 0, f"no .py files found under {DOMAIN_ROOT}"


@pytest.mark.unit
def test_domain_package_has_no_forbidden_imports() -> None:
    all_violations = {
        str(path.relative_to(DOMAIN_ROOT)): _violations_in(path) for path in _domain_source_files()
    }
    offending = {path: v for path, v in all_violations.items() if v}

    assert not offending, (
        "app/domain must depend on nothing but the Python standard library "
        "(Sprint 1, Step 12 architecture rule). Violations:\n"
        + "\n".join(
            f"  {path}: {reason}" for path, reasons in offending.items() for reason in reasons
        )
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "module_name",
    ["fastapi", "sqlalchemy", "alembic", "psycopg", "pydantic", "starlette", "uvicorn"],
)
def test_the_checker_itself_rejects_known_infrastructure_packages(module_name: str) -> None:
    """Proves _is_allowed_absolute_import actually rejects the packages
    Domain Core must never import — not just that the real domain package
    happens to be clean today."""
    assert _is_allowed_absolute_import(module_name) is False


@pytest.mark.unit
@pytest.mark.parametrize("module_name", ["app.infra", "app.infra.database", "app.api", "app.ai"])
def test_the_checker_itself_rejects_sibling_layers(module_name: str) -> None:
    """app.domain may not import app.infra, app.api, or app.ai — those
    layers depend on domain, never the other way around."""
    assert _is_allowed_absolute_import(module_name) is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "module_name",
    ["uuid", "dataclasses", "datetime", "abc", "typing", "app.domain", "app.domain.shared_kernel"],
)
def test_the_checker_itself_allows_stdlib_and_domain_modules(module_name: str) -> None:
    assert _is_allowed_absolute_import(module_name) is True
