# LocustHub 阶段 11 前后端不分离交付

## 1. 阶段目标

阶段 11 将默认交付形态从 API 容器和 Admin 容器分离，调整为单 FastAPI 服务：

- Vue 管理后台仍在 `frontend/` 中独立开发和构建。
- `backend/Dockerfile` 使用 Node 多阶段构建生成 `dist`。
- FastAPI 通过 `FRONTEND_DIST_DIR` 托管构建后的静态资源。
- `/api/v1`、`/docs`、`/openapi.json`、`/health` 保持后端接口语义。
- `/` 和前端路由回退到 `index.html`。

这样本地调试、Docker Compose 和默认 Helm 部署只需要一个业务服务，降低 MVP
交付和排障成本。

## 2. 本地启动

```bash
scripts/run_local.sh
```

脚本会安装后端依赖、安装前端依赖、执行 `npm run build`，然后启动 FastAPI。

访问入口：

- Admin: `http://127.0.0.1:8000/`
- API: `http://127.0.0.1:8000/api/v1`
- Swagger: `http://127.0.0.1:8000/docs`

## 3. Docker Compose

Compose 默认只包含：

- `mysql`
- `api`

`api` 镜像内置 Vue 管理后台产物，并设置：

```yaml
FRONTEND_DIST_DIR: /app/frontend_dist
PUBLIC_API_BASE_URL: http://127.0.0.1:8000/api/v1
PUBLIC_ADMIN_BASE_URL: http://127.0.0.1:8000
```

## 4. Helm

默认 values：

```yaml
admin:
  enabled: false
env:
  FRONTEND_DIST_DIR: /app/frontend_dist
```

Ingress 默认把 `/api` 和 `/` 都路由到 `locusthub-api`。如后续需要单独扩展管理后台，
可以设置 `admin.enabled=true`，此时 `/` 会路由到 `locusthub-admin`。

## 5. 验收点

- `backend/tests/test_integrated_frontend.py` 验证 FastAPI 可以返回前端首页、静态资源和 SPA fallback。
- Stage6/Stage7 部署测试验证 Compose、Dockerfile、Helm、Ingress 与单服务默认交付一致。
- `scripts/verify_deployment_package.py` 验证部署包仍完整。
- 本地启动后浏览器统一访问 `http://127.0.0.1:8000/`。
