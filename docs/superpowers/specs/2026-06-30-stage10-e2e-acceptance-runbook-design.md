# Stage10 E2E Acceptance and Runbook Design

## Goal

Stage10 closes the MVP delivery loop with a repeatable local acceptance script and a full deployment/use runbook. The goal is to prove that the platform can be debugged locally, packaged for deployment, and exercised through the key user workflows.

## Approach

Add a standard-library Python acceptance script that uses FastAPI's TestClient to run the control-plane flow without requiring Docker, Helm, or a live cluster. Pair it with the deployment package verifier so local acceptance checks both application behavior and deployable artifacts.

## Coverage

- Health and Swagger/OpenAPI availability.
- Login and `/me` user context.
- Test plan discovery, run creation, start, Locust-compatible stats, stop, and report archive.
- CI baseline execution and result lookup.
- Deployment package verification.

## Acceptance

Stage10 is accepted when the script exits 0, writes a JSON acceptance report, automated tests cover the script contract, and final documentation points users to local, Compose, Helm, OSS, and CI usage paths.

