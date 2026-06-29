# LocustHub 阶段 6 部署交付包

## 1. 阶段目标

阶段 6 将本地 MVP 推进到可部署交付形态。当前默认交付为单服务结构：
后端镜像先构建 Vue 管理后台，再由 FastAPI 同源托管 `dist`、API 和 Swagger。
Docker Compose 只需要 MySQL 与 API 服务即可完成本地全栈启动。

## 2. 本地 Compose 调试

开发模式一键构建管理后台并启动 FastAPI：

```bash
scripts/run_local.sh
```

该脚本提供：

- Admin: `http://127.0.0.1:8000/`
- API: `http://127.0.0.1:8000/api/v1`
- Swagger: `http://127.0.0.1:8000/docs`

Compose 模式启动完整容器栈：

```bash
cp .env.example .env
docker compose up --build
```

启动后：

- Admin: `http://127.0.0.1:8000/`
- API: `http://127.0.0.1:8000/api/v1`
- Swagger: `http://127.0.0.1:8000/docs`
- FastAPI 直接托管构建后的前端静态资源，前端默认请求同源 `/api/v1`。

## 3. 生产化配置入口

`.env.example` 现在覆盖：

- MySQL: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- OSS: `ARTIFACT_STORAGE_PROVIDER`, `ALIYUN_OSS_ENDPOINT`, `ALIYUN_OSS_BUCKET`
- Kubernetes Locust runtime: `LANE_RUNTIME_BACKEND`, `KUBERNETES_APPLY_ENABLED`
- Locust metrics: `LOCUST_METRICS_BACKEND`, `LOCUST_MASTER_BASE_URL_TEMPLATE`
- Public URL: `PUBLIC_API_BASE_URL`, `PUBLIC_ADMIN_BASE_URL`

生产环境不要直接使用 `.env.example` 中的示例密钥。MySQL 密码、OSS AK/SK 和
`DEMO_TOKEN` 应由 Secret 管理。

## 4. Helm 部署包

Helm chart 默认使用 API 镜像同时提供管理后台：

```yaml
api:
  image:
    repository: locusthub-api
admin:
  enabled: false
  image:
    repository: locusthub-admin
```

API Deployment 增加 `/health` readiness/liveness probes，并通过
`FRONTEND_DIST_DIR=/app/frontend_dist` 定位内置前端产物。`admin.enabled=true`
时可以重新启用独立 Admin Deployment/Service；默认关闭以降低 PaaS 交付复杂度。
ServiceAccount/RBAC 仍沿用阶段 3 的 Locust 泳道控制权限。

## 5. 部署包验证

无需安装 Docker 或 Helm 即可先做静态验收：

```bash
python3 scripts/verify_deployment_package.py
```

该脚本检查 compose 服务、后端多阶段镜像、环境变量、Helm 单服务默认入口、
可选 Admin 工作负载和关键健康检查。

## 6. 已知边界

- 独立 Admin 容器仍保留为 Helm 可选项，但默认交付不再依赖它。
- Helm values 中的敏感字段仍以明文示例展示，生产环境需要替换为 Secret/ExternalSecret。
- 本地环境未强制执行真实 Docker/Helm 命令，自动化验收以静态部署包检查为主。
