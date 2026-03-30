# Smoke Tests

This directory is reserved for cross-application smoke tests.

In the current phase, API unit tests and the OpenAPI consistency check provide the minimum safety net. The following smoke tests can be added later:

- API smoke
- end-to-end flow smoke
- baseline compare smoke

Current implemented smoke coverage:

- `test_panel_local_e2e.py`
  - validates the panel write path end-to-end across CLI, API, and PostgreSQL
  - exercises project registration, baseline upload, and run upload using real local services
