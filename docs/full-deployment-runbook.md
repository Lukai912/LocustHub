# LocustHub 完整部署与使用 Runbook

## 1. 本地验收

运行最终验收脚本：

```bash
scripts/run_acceptance_smoke.py --output docs/reports/final-acceptance-smoke.json
```

脚本覆盖：

- `/health` 和 `/openapi.json`
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
- Admin: `http://127.0.0.1:5173`

## 3. Docker Compose 全栈

```bash
cp .env.example .env
docker compose up --build
```

访问：

- API: `http://127.0.0.1:8000`
- Admin: `http://127.0.0.1:8080`

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

## 5. 阿里云 OSS

设置：

```bash
ARTIFACT_STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ENDPOINT=oss-cn-example.aliyuncs.com
ALIYUN_OSS_BUCKET=locusthub-artifacts
```

报告、CSV、日志和原始快照通过 artifact repository 抽象归档，后续可替换 MinIO/S3/COS。

## 6. CI 性能基线

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
  --max-p95-ms 500 \
  --max-fail-ratio 0.05 \
  --output locusthub-baseline.json
```

脚本在 `conclusion=failed` 时返回退出码 `1`，CI 可直接将性能回归标记为失败。

## 7. 已知生产化边界

- 用户管理后台、OIDC、细粒度 RBAC 仍是后续增强。
- Helm chart 不创建证书签发资源，需要平台已有 cert-manager 或网关能力。
- 本地验收脚本使用 SQLite 和模拟指标，真实集群联调需要 Kubernetes、MySQL、OSS 和 Locust API runtime 配套环境。

