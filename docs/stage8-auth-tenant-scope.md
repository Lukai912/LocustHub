# LocustHub 阶段 8 认证与租户范围收敛

## 1. 阶段目标

阶段 8 将 MVP 的 bearer token 从“只校验格式”升级为“必须匹配 `users` 表记录”，并让非
admin 用户只能访问自己租户的数据。

## 2. 登录与用户上下文

`POST /api/v1/auth/login` 现在会校验用户名和密码：

```json
{
  "username": "admin",
  "password": "admin"
}
```

成功后返回数据库中保存的 token。`GET /api/v1/me` 返回当前 token 对应的用户：

```json
{
  "id": "user-admin",
  "username": "admin",
  "tenant_id": "tenant-demo",
  "role": "admin"
}
```

Demo seed 同时包含：

- `admin/admin`，role 为 `admin`
- `viewer/viewer`，role 为 `viewer`，token 为 `dev-token-viewer`

## 3. 租户范围

`admin` 可以查看全部租户数据。非 admin 用户：

- `/tenants` 只返回自己的租户。
- `/projects`、`/test-plans`、`/test-runs`、治理快照等只返回自己的 `tenant_id`。
- 创建项目、脚本、计划、任务、目标白名单和 CI 运行时，`tenant_id` 必须等于当前用户租户。
- 跨租户写入返回 `403`。

## 4. 密码实现边界

当前密码 hash 使用标准库 SHA-256，并集中在 `app.core.security`。这是 MVP 本地认证实现，
后续正式部署建议替换为 bcrypt、OIDC 或企业 IdP。

## 5. 验证

```bash
cd backend
PYTHONPATH=. ../.venv/bin/pytest tests/test_stage8_auth_tenant_scope.py -q
```

## 6. 已知边界

- 本阶段不新增用户管理 API。
- 前端仍默认使用 `VITE_DEMO_TOKEN`，后续阶段再接正式登录页和 token 存储策略。
- 角色模型当前只有 `admin` 与非 admin 的粗粒度区分。

