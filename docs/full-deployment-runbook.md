# LocustHub 完整部署与使用 Runbook

## 1. 本地验收

运行最终验收脚本：

```bash
scripts/run_acceptance_smoke.py --output docs/reports/final-acceptance-smoke.json
```

脚本覆盖：

- `/health`、`/ready` 和 `/openapi.json`
- `admin/admin` 登录和 `/me`
- 压测任务创建、启动、Locust UI 兼容实时指标、停止和报告归档
- CI baseline 创建和结果查询
- `scripts/verify_deployment_package.py` 部署包检查

## 2. 本地开发调试

```bash
scripts/run_local.sh
```

访问：

- API/Swagger: `http://127.0.0.1:8000/docs`
- Admin: `http://127.0.0.1:8000/`
- Readiness: `http://127.0.0.1:8000/ready`

## 3. Docker Compose 全栈

```bash
cp .env.example .env
docker compose up --build
```

访问：

- Admin: `http://127.0.0.1:8000/`
- API: `http://127.0.0.1:8000/api/v1`
- Swagger: `http://127.0.0.1:8000/docs`
- Readiness: `http://127.0.0.1:8000/ready`

默认 Compose 只启动 `mysql` 和 `api` 两个服务。`api` 镜像在构建阶段打包 Vue
管理后台，并由 FastAPI 同源托管静态文件和 `/api/v1`。

## 4. Helm 生产部署

准备 values：

```yaml
ingress:
  host: locusthub.example.com
  tls:
    secretName: locusthub-tls
secret:
  create: false
  existingSecret: locusthub-runtime-secrets
env:
  ALIYUN_OSS_BUCKET: locusthub-artifacts
  ALIYUN_OSS_ENDPOINT: oss-cn-example.aliyuncs.com
  PUBLIC_API_BASE_URL: https://locusthub.example.com/api/v1
  PUBLIC_ADMIN_BASE_URL: https://locusthub.example.com
  FRONTEND_DIST_DIR: /app/frontend_dist
```

部署：

```bash
helm upgrade --install locusthub deploy/helm/locusthub -n locusthub --create-namespace -f values-prod.yaml
```

`locusthub-runtime-secrets` 至少包含：

- `MYSQL_PASSWORD`
- `ALIYUN_OSS_ACCESS_KEY_ID`
- `ALIYUN_OSS_ACCESS_KEY_SECRET`
- `DEMO_TOKEN`

默认 Helm 部署也是单服务入口：Ingress 的 `/api` 和 `/` 都可以路由到
`locusthub-api`。如果后续需要独立扩展管理后台，可以显式设置
`admin.enabled=true`，此时 `/` 会路由到 `locusthub-admin`。

## 5. 阿里云 OSS

设置：

```bash
ARTIFACT_STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ENDPOINT=oss-cn-example.aliyuncs.com
ALIYUN_OSS_BUCKET=locusthub-artifacts
```

报告、CSV、日志和原始快照通过 artifact repository 抽象归档，后续可替换 MinIO/S3/COS。

## 6. CI 性能基线

用于 CI 的 API Token 需要包含 `ci:run` scope。可以在管理后台 `Access`
页面创建 token，并在 `CI Baselines` 页面创建 baseline profile。

```bash
scripts/run_ci_baseline.py \
  --api-base-url https://locusthub.example.com/api/v1 \
  --token "$LOCUSTHUB_TOKEN" \
  --tenant-id "$LOCUSTHUB_TENANT_ID" \
  --project-id "$LOCUSTHUB_PROJECT_ID" \
  --test-plan-id "$LOCUSTHUB_TEST_PLAN_ID" \
  --ci-provider github-actions \
  --pipeline-id "$GITHUB_RUN_ID" \
  --job-id perf-baseline \
  --commit-sha "$GITHUB_SHA" \
  --branch "$GITHUB_REF_NAME" \
  --baseline-profile-id "$LOCUSTHUB_BASELINE_PROFILE_ID" \
  --max-p95-ms 500 \
  --max-fail-ratio 0.05 \
  --output locusthub-baseline.json
```

脚本在 `conclusion=failed` 时返回退出码 `1`，CI 可直接将性能回归标记为失败。

## 7. Stage19 运维检查

Stage19 后，每次部署前建议至少执行：

```bash
python3 scripts/verify_deployment_package.py
scripts/run_acceptance_smoke.py --output docs/reports/final-acceptance-smoke.json
```

人工检查：

- Swagger: `/docs`
- Readiness: `/ready`
- Admin: `/`
- API Token scope: `ci:run`
- 报告下载和 CI baseline profile 是否可用

## 8. 已知生产化边界

- 用户管理后台、OIDC、细粒度 RBAC 仍是后续增强。
- Helm chart 不创建证书签发资源，需要平台已有 cert-manager 或网关能力。
- 本地验收脚本使用 SQLite 和模拟指标，真实集群联调需要 Kubernetes、MySQL、OSS 和 Locust API runtime 配套环境。
