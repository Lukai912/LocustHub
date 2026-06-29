# LocustHub Development Guidelines

## API Documentation

All FastAPI endpoints must be visible and understandable in Swagger UI at `/docs`.

Required for new or changed endpoints:

- Add a stable `tags` group.
- Add a concise `summary`.
- Add a function docstring or `description` when the endpoint has workflow, security, or side effects.
- Add `Field(description=...)` to request model fields that are not self-evident.
- Add or update tests that inspect `/openapi.json` for important API groups.

## Code Comments

Comments should explain intent, boundaries, and risk. They should not repeat what a line of code already says.

Required comment locations:

- Adapter boundaries: MySQL, OSS, Kubernetes, Locust API, future CI providers.
- Fallback behavior: simulated metrics, report fallback, local artifact storage.
- Security and governance logic: target whitelist, approval, quota, NetworkPolicy, DNS/IP restrictions.
- Lifecycle decisions: lane creation, resource deletion, report archival, retry/idempotency.
- Non-obvious data mapping: Locust UI fields, persisted metric columns, report artifact keys.

Avoid:

- Comments that only restate variable names.
- Large blocks of outdated design prose inside code.
- Hidden TODOs without an issue, phase, or explicit follow-up document.

## Pull Request Gate

Every module PR must use `.github/pull_request_template.md` and paste real verification output.

A PR should not be merged if:

- New API behavior is missing Swagger metadata.
- New request fields lack descriptions.
- Complex runtime, storage, or security behavior lacks intent comments.
- Tests or acceptance notes are missing for the changed behavior.
