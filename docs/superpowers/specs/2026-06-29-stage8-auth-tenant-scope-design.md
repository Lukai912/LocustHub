# Stage8 Auth and Tenant Scope Design

## Goal

Stage8 replaces format-only bearer token checks with repository-backed user authentication and tenant-aware API scoping. It keeps the MVP demo credentials working while making unauthorized or cross-tenant access fail.

## Approach

Use the existing `users` table as the authority for login and token validation. Add a password hash field with a lightweight standard-library hash for the MVP; the implementation is intentionally isolated so it can be replaced by bcrypt or an IdP integration later. Route dependencies resolve the current user once and helper functions enforce tenant visibility.

## Scope

- Login checks username and password before returning a token.
- Bearer tokens must match a persisted user.
- `/me` returns the persisted user context.
- Non-admin users see only records for their tenant.
- Cross-tenant create/update attempts return `403`.

## Acceptance

Stage8 is accepted when API tests prove invalid tokens fail, bad passwords fail, tenant users are scoped, admin behavior remains compatible, and the PR is merged to `main`.

