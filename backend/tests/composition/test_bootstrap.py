"""Tests for `bootstrap()`/`shutdown()`/`lifespan()` — "startup succeeds"
and "shutdown succeeds" as actual, executed properties, not assumptions.

Every test here points `Settings.database_url` at sqlite rather than the
real `GYM_` environment/Postgres default, since `bootstrap()` calls
`Container.validate()`, which — see `app/infra/unit_of_work.py`'s module
docstring — does no I/O and therefore needs no live database, only a
syntactically valid SQLAlchemy URL to build an `Engine` from.
"""

from __future__ import annotations

import pytest

from app.composition.bootstrap import bootstrap, lifespan, shutdown
from app.composition.container import Container
from app.core.config import Settings


def _sqlite_settings() -> Settings:
    return Settings(database_url="sqlite://")


@pytest.mark.unit
def test_bootstrap_returns_a_validated_container() -> None:
    container = bootstrap(_sqlite_settings())
    try:
        assert isinstance(container, Container)
    finally:
        shutdown(container)


@pytest.mark.unit
def test_bootstrap_configures_logging(capsys: pytest.CaptureFixture[str]) -> None:
    """`configure_logging()` calls `logging.basicConfig(..., force=True)`,
    which replaces every existing root-logger handler — including
    pytest's own `caplog` capture handler — with the one this project
    configures (see `logging_config.py`'s own docstring). That is exactly
    the behavior under test, so asserting on it has to read the real
    output stream (`capsys`, stderr — `basicConfig`'s default handler
    target) rather than `caplog.records`, which this call deliberately
    stops receiving anything for.
    """
    container = bootstrap(_sqlite_settings())
    try:
        captured = capsys.readouterr()
        assert "application bootstrap complete" in captured.err
    finally:
        shutdown(container)


@pytest.mark.unit
def test_shutdown_disposes_the_engine() -> None:
    container = bootstrap(_sqlite_settings())
    pool_before = container.engine.pool
    shutdown(container)
    # Engine.dispose() replaces the pool with a fresh, empty one of the same
    # class — this is SQLAlchemy's own documented signal that every
    # existing pooled connection was discarded, which is the only
    # externally observable proof disposal actually happened (the engine
    # object itself is not marked "disposed" in any other inspectable way).
    assert container.engine.pool is not pool_before


@pytest.mark.unit
def test_shutdown_logs_start_and_complete(capsys: pytest.CaptureFixture[str]) -> None:
    container = bootstrap(_sqlite_settings())
    capsys.readouterr()  # discard bootstrap's own log output
    shutdown(container)
    captured = capsys.readouterr()
    assert "application shutdown starting" in captured.err
    assert "application shutdown complete" in captured.err


@pytest.mark.unit
def test_lifespan_yields_a_validated_container_and_shuts_down_on_clean_exit() -> None:
    with lifespan(_sqlite_settings()) as container:
        assert isinstance(container, Container)
        pool_during = container.engine.pool
    assert container.engine.pool is not pool_during


@pytest.mark.unit
def test_lifespan_shuts_down_even_if_the_body_raises() -> None:
    container_ref: Container | None = None

    with pytest.raises(RuntimeError), lifespan(_sqlite_settings()) as container:
        container_ref = container
        pool_during = container.engine.pool
        raise RuntimeError("simulated failure inside the lifespan body")

    assert container_ref is not None
    assert container_ref.engine.pool is not pool_during


@pytest.mark.unit
def test_bootstrap_defaults_to_get_settings_when_none_is_passed() -> None:
    """Proves the `settings=None` default path (`get_settings()`) also
    works — the sqlite override above exercises the explicit-argument
    path, but production `app/main.py` usage will call `bootstrap()` with
    no argument at all."""
    container = bootstrap()
    try:
        assert container.settings is not None
    finally:
        shutdown(container)
