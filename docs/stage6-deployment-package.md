# LocustHub 阶段 6 部署交付包

## 1. 阶段目标

阶段 6 将本地 MVP 推进到可部署交付形态，补齐管理后台容器、Docker Compose
全栈启动、Helm API/Admin 工作负载和部署包验证脚本。

## 2. 本地 Compose 调试

开发模式一键启动 API 和 Admin：

```bash
scripts/run_local.sh
```

该脚本启动：

- API: `http://127.0.0.1:8000/docs`
- Admin dev server: `http://127.0.0.1:5173`

Compose 模式启动完整容器栈：

```bash
cp .env.example .env
docker compose up --build
```

启动后：

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Admin: `http://127.0.0.1:8080`
- Admin 通过 Nginx 将 `/api/` 代理到 compose 内部 API 服务。

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

Helm chart 拆分了 API 和 Admin 镜像：

```yaml
api:
  image:
    repository: locusthub-api
admin:
  image:
    repository: locusthub-admin
```

API Deployment 增加 `/health` readiness/liveness probes，Admin Deployment 使用
Nginx 首页作为健康检查。ServiceAccount/RBAC 仍沿用阶段 3 的 Locust 泳道控制权限。

## 5. 部署包验证

无需安装 Docker 或 Helm 即可先做静态验收：

```bash
python3 scripts/verify_deployment_package.py
```

该脚本检查 compose 服务、前端容器、环境变量、Helm API/Admin 工作负载和关键健康检查。

## 6. 已知边界

- 本阶段不引入 Ingress Controller 模板，后续可按云厂商网关或公司统一网关补充。
- Helm values 中的敏感字段仍以明文示例展示，生产环境需要替换为 Secret/ExternalSecret。
- 本地环境未强制执行真实 Docker/Helm 命令，自动化验收以静态部署包检查为主。
