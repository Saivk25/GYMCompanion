"""Statically proves the Application Layer's own architectural rule:
"Application depends on nothing except the Python standard library and
`app.domain`."

Mirrors `tests/domain/test_import_boundaries.py` exactly — same `ast`-
based approach, same two absolute rules — with one difference: `app/
domain` may depend on nothing but the standard library, while `app/
application` may additionally depend on `app.domain` (its whole
purpose is to orchestrate the Domain Layer). Either way, `app.infra`,
`app.api`, `app.ai`, and every third-party framework (FastAPI,
SQLAlchemy, Pydantic, ...) remain forbidden.
"""

import ast
import sys
from pathlib import Path

import pytest

APPLICATION_ROOT = Path(__file__).resolve().parents[2] / "app" / "application"

_STDLIB_MODULES = set(sys.stdlib_module_names) | {"__future__"}


def _application_source_files() -> list[Path]:
    return sorted(APPLICATION_ROOT.rglob("*.py"))


def _is_allowed_absolute_import(module_name: str) -> bool:
    top_level = module_name.split(".")[0]
    if top_level in _STDLIB_MODULES:
        return True
    if module_name == "app.domain" or module_name.startswith("app.domain."):
        return True
    return module_name == "app.application" or module_name.startswith("app.application.")


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
def test_application_package_has_python_files_to_check() -> None:
    """A guard against this test silently checking nothing — e.g. if
    APPLICATION_ROOT's path computation ever breaks after a directory
    move."""
    assert len(_application_source_files()) > 0, f"no .py files found under {APPLICATION_ROOT}"


@pytest.mark.unit
def test_application_package_has_no_forbidden_imports() -> None:
    all_violations = {
        str(path.relative_to(APPLICATION_ROOT)): _violations_in(path)
        for path in _application_source_files()
    }
    offending = {path: v for path, v in all_violations.items() if v}

    assert not offending, (
        "app/application must depend on nothing but the Python standard library and "
        "app/domain (Sprint 4, Phase 1 architecture rule). Violations:\n"
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
    the Application Layer must never import — not just that the real
    package happens to be clean today."""
    assert _is_allowed_absolute_import(module_name) is False


@pytest.mark.unit
@pytest.mark.parametrize("module_name", ["app.infra", "app.infra.database", "app.api", "app.ai"])
def test_the_checker_itself_rejects_sibling_layers(module_name: str) -> None:
    """app.application may not import app.infra, app.api, or app.ai —
    those layers depend on the Application Layer (eventually), never
    the other way around."""
    assert _is_allowed_absolute_import(module_name) is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "module_name",
    [
        "uuid",
        "dataclasses",
        "datetime",
        "abc",
        "typing",
        "app.domain",
        "app.domain.shared_kernel",
        "app.application",
        "app.application.shared",
    ],
)
def test_the_checker_itself_allows_stdlib_domain_and_application_modules(module_name: str) -> None:
    assert _is_allowed_absolute_import(module_name) is True
