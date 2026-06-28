# LocustHub Project Context

## Overview

LocustHub is a multi-tenant load testing PaaS based on Locust. It provides a FastAPI control plane, a Vben Admin management UI, and temporary Kubernetes-based load test lanes.

## Product Goals

- Support tenant-based load testing management.
- Run each load test in an isolated temporary lane.
- Reuse Locust master/worker and Locust UI-compatible metrics.
- Archive reports, logs, CSV files, and raw snapshots.
- Support future CI performance baseline execution.

## Technology Stack

- Backend: FastAPI
- Frontend: vbenjs/vue-vben-admin
- Load test engine: Locust
- Runtime platform: Kubernetes
- Metadata and low-frequency metrics: MySQL
- Artifact storage: ArtifactRepository abstraction, default Aliyun OSS
- Future metric storage extension: ClickHouse or compatible time-series store

## Architecture Principles

- Control plane and execution plane are separated.
- One running TestRun owns one Locust master and N Locust workers.
- Runtime resources are temporary and can be destroyed after archiving.
- Business data, metrics, logs, and reports must be persisted outside runtime lanes.
- Security admission happens before lane creation.
- Storage providers must be hidden behind repository interfaces.

## Development Workflow

LocustHub uses Superpowers + OpenSpec:

- Superpowers define collaboration roles and responsibility boundaries.
- OpenSpec defines accepted capabilities and proposed changes.
- Significant features require a change proposal before implementation.

See:

- `docs/superpowers-openspec-collaboration.md`
- `openspec/specs/loadtest-paas/spec.md`
