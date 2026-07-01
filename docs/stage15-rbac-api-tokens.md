# LocustHub 阶段 15 RBAC 与 API Token

## 1. 阶段目标

阶段 15 将认证能力从 demo token 继续推进到可运维的账号和 CI 调用模型：

- 管理员可以创建租户内用户，并分配 `admin`、`project_member`、`viewer` 角色。
- 用户可以通过 `/api/v1/auth/login` 登录，获得 bearer token。
- 登录用户可以创建、查看和撤销 API Token，供 CI 或自动化脚本调用。
- API Token 可携带 scopes，并在 `/api/v1/me` 中返回当前调用上下文。
- Swagger/OpenAPI 页面展示 Auth 相关接口摘要和说明。

## 2. 后端实现

新增接口：

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/api-tokens`
- `POST /api/v1/api-tokens`
- `POST /api/v1/api-tokens/{token_id}/revoke`

实现要点：

- `current_user` 先按用户 token 查找，失败后再按 API Token 查找。
- API Token 使用 `lhpat_` 前缀，创建时只返回一次明文 token。
- token 列表和撤销响应不返回明文 token。
- 非 admin 不能创建用户。
- 非 admin 只能访问自身租户数据。

## 3. 前端实现

管理后台新增 `Access` 页面：

- `Create User` 表单创建租户用户。
- 用户表展示 username、tenant、role。
- `Create API Token` 表单创建自动化 token。
- 创建后的 token secret 只在页面当次展示。
- token 表展示 name、scopes、revoked 状态，并支持 `Revoke Token`。

## 4. 数据模型

新增 `api_tokens` 表：

- `id`
- `tenant_id`
- `user_id`
- `name`
- `token`
- `scopes_json`
- `revoked_at`
- `created_at`

SQLite 和 MySQL schema 保持同构。scopes 使用 JSON 字符串保存，接口层返回 list，避免前端解析存储字段。

## 5. 验收

自动化测试覆盖：

- admin 可以创建用户，新用户可以登录。
- API Token 可以创建、用于访问 `/me`、撤销后不可用。
- viewer 不能创建用户。
- 前端结构包含 Access、Create User、Create API Token、Revoke Token。

阶段边界：

- 当前阶段实现基础 RBAC，不实现细粒度 scope enforcement；Stage18 接入 CI 基线时再按接口动作收敛 scopes。
- 密码 hash 保持 MVP 的标准库实现，生产部署前可替换为 passlib/bcrypt。
