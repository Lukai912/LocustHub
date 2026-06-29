# Stage7 Ingress and Secrets Design

## Goal

Stage7 makes the Helm deployment entrypoint closer to production use by adding HTTP routing, TLS configuration, and Secret-backed sensitive settings. It builds on the Stage6 deployment package instead of changing runtime behavior.

## Approach

Add a single Helm Ingress that routes `/api` to the API service and `/` to the admin service. Add a Secret template and wire sensitive settings through `secretKeyRef`, while keeping non-sensitive runtime values in the existing `env` map. Keep defaults runnable for demo installations, but document that real deployments should replace demo values with an existing Secret or external secret controller.

## Components

- `deploy/helm/locusthub/templates/ingress.yaml` for admin/API routing and optional TLS.
- `deploy/helm/locusthub/templates/secret.yaml` for demo or user-provided sensitive settings.
- `deploy/helm/locusthub/values.yaml` for ingress, TLS, and secret configuration.
- `backend/tests/test_stage7_ingress_secrets.py` for the Helm production entrypoint contract.
- `scripts/verify_deployment_package.py` and docs updated to include Stage7 checks.

## Acceptance

Stage7 is accepted when tests prove Helm exposes an Ingress/TLS entrypoint, sensitive values are Secret-backed in the API Deployment, deployment verification succeeds, and the PR is merged to `main`.

