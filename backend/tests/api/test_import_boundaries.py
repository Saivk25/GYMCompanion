"""Statically proves the API Layer's own architectural rule: `app/api`
may depend on the standard library, `app.domain`, `app.application`,
`app.composition`, `app.core`, and third-party HTTP/validation
frameworks (FastAPI, Starlette, Pydantic) — never `app.infra` directly
(only indirectly, through `app.composition.Container`), never `app.ai`,
and never `sqlalchemy` (see `app/api/routes/health.py`'s own module
docstring for why the one thing that looked like it might need
SQLAlchemy — the readiness check — instead calls `Container.
is_database_ready()`).

Mirrors `tests/application/test_import_boundaries.py` exactly — same
`ast`-based approach, same shape — with a wider allow-list matching
what this layer, unlike Application, is actually permitted to depend on.
"""

import ast
import sys
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[2] / "app" / "api"

_STDLIB_MODULES = set(sys.stdlib_module_names) | {"__future__"}

_ALLOWED_THIRD_PARTY_TOP_LEVEL = {"fastapi", "starlette", "pydantic"}

_ALLOWED_APP_PREFIXES = ("app.domain", "app.application", "app.composition", "app.core", "app.api")


def _api_source_files() -> list[Path]:
    return sorted(API_ROOT.rglob("*.py"))


def _is_allowed_absolute_import(module_name: str) -> bool:
    top_level = module_name.split(".")[0]
    if top_level in _STDLIB_MODULES:
        return True
    if top_level in _ALLOWED_THIRD_PARTY_TOP_LEVEL:
        return True
    return any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in _ALLOWED_APP_PREFIXES
    )


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
                    f"— use an absolute app... import instead"
                )
            elif node.module and not _is_allowed_absolute_import(node.module):
                violations.append(f"imports from {node.module!r}")

    return violations


@pytest.mark.unit
def test_api_package_has_python_files_to_check() -> None:
    """A guard against this test silently checking nothing — e.g. if
    API_ROOT's path computation ever breaks after a directory move."""
    assert len(_api_source_files()) > 0, f"no .py files found under {API_ROOT}"


@pytest.mark.unit
def test_api_package_has_no_forbidden_imports() -> None:
    all_violations = {
        str(path.relative_to(API_ROOT)): _violations_in(path) for path in _api_source_files()
    }
    offending = {path: v for path, v in all_violations.items() if v}

    assert not offending, (
        "app/api must not import app.infra, app.ai, or sqlalchemy directly (FastAPI API "
        "Layer phase architecture rule). Violations:\n"
        + "\n".join(
            f"  {path}: {reason}" for path, reasons in offending.items() for reason in reasons
        )
    )


@pytest.mark.unit
@pytest.mark.parametrize("module_name", ["sqlalchemy", "sqlalchemy.orm", "alembic", "psycopg"])
def test_the_checker_itself_rejects_known_infrastructure_packages(module_name: str) -> None:
    assert _is_allowed_absolute_import(module_name) is False


@pytest.mark.unit
@pytest.mark.parametrize("module_name", ["app.infra", "app.infra.unit_of_work", "app.ai"])
def test_the_checker_itself_rejects_sibling_layers(module_name: str) -> None:
    """app.api may not import app.infra directly (only indirectly, via
    app.composition.Container) or app.ai."""
    assert _is_allowed_absolute_import(module_name) is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "module_name",
    [
        "uuid",
        "datetime",
        "dataclasses",
        "typing",
        "fastapi",
        "starlette.responses",
        "pydantic",
        "app.domain.goal.identifiers",
        "app.application.goal.handlers.get_goal_handler",
        "app.composition.container",
        "app.core.config",
        "app.api.deps",
        "app.api.schemas.common",
    ],
)
def test_the_checker_itself_allows_every_permitted_dependency(module_name: str) -> None:
    assert _is_allowed_absolute_import(module_name) is True
