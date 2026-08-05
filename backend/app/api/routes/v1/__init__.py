"""Version 1 of this API's HTTP surface — every route module here is
mounted under the `/api/v1` prefix by `app.main.create_app()`.

Each module (`goal.py`, `nutrition.py`, `progress.py`, `readiness.py`,
`workout.py`) exposes exactly the Application Handlers that already
exist for its aggregate — see each module's own docstring for its
route map. No route module here imports another; each is independently
mountable, the same "no route imports app.infra directly" boundary
`tests/api/test_import_boundaries.py` enforces for the whole package.
"""
