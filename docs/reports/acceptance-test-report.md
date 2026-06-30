# LocustHub MVP 验收及测试报告

## 1. 验收范围

本报告覆盖 LocustHub MVP 本地可执行调试版本。

已覆盖模块：

- M01 租户与权限模块，Demo token 和租户隔离字段
- M02 项目与脚本模块
- M03 压测计划模块
- M04 压测任务模块
- M05 准入审批与配额模块
- M06 临时压测泳道模块，本地 manifest 模拟
- M07 Locust 实时指标模块，Locust UI 字段兼容模拟数据
- M08 报告归档与对象存储模块，本地 ArtifactRepository
- M09 管理后台模块，本地调试页
- M10 CI 性能基线模块，API 预留和本地执行
- M12 审计与观测模块，基础审计事件

Demo 目标：

```text
https://jsonplaceholder.typicode.com/todos/1
```

该目标仅用于低并发真实网络 API 连通性和平台链路验证，不作为高压公共目标。

## 2. 本地运行方式

```bash
./scripts/run_local.sh
```

管理页面：

```text
http://127.0.0.1:8000/
```

测试命令：

```bash
./scripts/test_local.sh
```

## 3. 验收用例

| 用例 | 预期 | 状态 |
| --- | --- | --- |
| 健康检查 | `/health` 返回 ok | 通过 |
| 创建 TestRun | 可从 Demo TestPlan 创建任务 | 通过 |
| 启动 TestRun | 任务进入 RUNNING | 通过 |
| 准入拦截 | 未审批目标进入 APPROVAL_PENDING | 通过 |
| 实时指标 | 返回 Locust UI 风格 stats 字段 | 通过 |
| 停止归档 | 任务进入 COMPLETED 并生成 report | 通过 |
| CI 基线 | CI API 创建 source=ci 的任务 | 通过 |

## 4. 自动化测试结果

执行命令：

```text
./scripts/test_local.sh
```

测试结果：

```text
3 passed in 0.38s
```

覆盖用例：

- `test_mvp_run_lifecycle`
- `test_unapproved_target_goes_to_approval_pending`
- `test_ci_baseline_reuses_test_run_engine`

## 5. 本地服务验证

执行方式：

```bash
cd backend
PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

验证结果：

```text
GET /health -> 200 OK, {"status":"ok","app":"LocustHub"}
GET /api/v1/test-plans -> 200 OK, returns JSONPlaceholder Demo Plan
```

## 6. 远端 PR 交付记录

MVP 汇总 PR：

- PR #1: https://github.com/Lukai912/LocustHub/pull/1

模块交付 PR：

| 模块 | PR |
| --- | --- |
| M01 租户与权限模块 | https://github.com/Lukai912/LocustHub/pull/2 |
| M02 项目与脚本模块 | https://github.com/Lukai912/LocustHub/pull/3 |
| M03 压测计划模块 | https://github.com/Lukai912/LocustHub/pull/4 |
| M04 压测任务模块 | https://github.com/Lukai912/LocustHub/pull/5 |
| M05 准入审批与配额模块 | https://github.com/Lukai912/LocustHub/pull/6 |
| M06 临时压测泳道模块 | https://github.com/Lukai912/LocustHub/pull/7 |
| M07 Locust 实时指标模块 | https://github.com/Lukai912/LocustHub/pull/8 |
| M08 报告归档与对象存储模块 | https://github.com/Lukai912/LocustHub/pull/9 |
| M09 管理后台模块 | https://github.com/Lukai912/LocustHub/pull/10 |
| M10 CI 性能基线模块 | https://github.com/Lukai912/LocustHub/pull/11 |
| M11 运维部署模块 | https://github.com/Lukai912/LocustHub/pull/12 |
| M12 审计与观测模块 | https://github.com/Lukai912/LocustHub/pull/13 |

以上 PR 均已合并到远端 `main`。其中 PR #2 到 PR #13 是 MVP bootstrap 阶段的模块交付追踪 PR，用于补齐远端模块记录；这些 PR 不代表后续模块增强的交付方式。

后续规则：

- 模块增强 PR 必须包含真实内容变更。
- 不再使用空提交 PR 做模块交付追踪。
- 每个真实模块 PR 需要在描述中标明模块编号、变更内容和验证方式。
- 每个真实模块 PR 必须使用 `.github/pull_request_template.md` 做自检。
- 新增或修改的 API 必须接入 Swagger：`tags`、`summary`、必要的 docstring/description、请求字段说明。
- 复杂运行时、存储、安全、治理逻辑必须补充维护性注释，说明设计意图和边界。

## 7. 验收结论

LocustHub MVP 本地调试版本通过当前自动化验收。用户可以在本地启动 FastAPI 服务，并通过本地管理页面完成 Demo 压测任务创建、启动、实时指标查看、停止归档等主流程。

## 8. MVP 限制

- 本地 MVP 使用 SQLite 模拟 MySQL。
- 本地 MVP 使用本地文件系统模拟阿里云 OSS。
- 本地 MVP 使用 manifest 模拟 Kubernetes 资源创建。
- 本地 MVP 使用模拟指标替代真实 Locust master 采集。

## 9. 阶段 2 基础设施适配验收

阶段 2 新增范围：

- MySQL 8 schema：`backend/app/db/mysql_schema.sql`
- MySQL migration 脚本：`scripts/migrate_mysql.py`
- MySQL 运行时连接适配：`MySQLDatabase`、`MySQLRepository`
- 阿里云 OSS ArtifactRepository：`AliyunOssArtifactRepository`
- 配置模板：`.env.example`
- API Dockerfile：`backend/Dockerfile`
- 本地部署：`docker-compose.yml`
- Helm 基础包：`deploy/helm/locusthub`
- 阶段 2 文档：`docs/stage2-infrastructure.md`

阶段 2 自动化测试覆盖：

- 环境变量可切换 MySQL 和 OSS provider
- MySQL schema 包含核心表
- Local ArtifactRepository 仍可用
- Aliyun OSS provider 会校验必需配置

阶段 2 测试结果：

```text
./scripts/test_local.sh -> 7 passed in 0.39s
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py -> passed
```

阶段 2 部署配置验证：

```text
docker compose config -> not executed, docker is not installed in the current environment
helm template locusthub deploy/helm/locusthub -> not executed, helm is not installed in the current environment
```

阶段 2 保留边界：

- 默认本地模式仍使用 SQLite 和本地文件归档，便于开发。
- MySQL 和阿里云 OSS 已具备配置、schema 和运行时适配。
- 真实 Kubernetes Locust 泳道和真实 Locust 指标采集进入阶段 3。

## 10. 阶段 3 Kubernetes + Locust 运行时验收

阶段 3 新增范围：

- Kubernetes manifest builder：`KubernetesManifestBuilder`
- Kubernetes lane runtime：`KubernetesLaneRuntime`
- 配置化 Kubernetes apply：`KUBERNETES_APPLY_ENABLED`
- Locust master API client：`LocustMasterApiClient`
- Locust API 指标转换：`LocustApiMetricsCollector`
- Locust 原生报告抓取：`LocustReportFetcher`
- Helm ServiceAccount/RBAC：`deploy/helm/locusthub/templates/rbac.yaml`
- Swagger 元信息和 API 字段说明：`backend/app/api/routes.py`、`backend/app/models/schemas.py`
- PR 模板：`.github/pull_request_template.md`
- 开发注释与 Swagger 规范：`docs/development-guidelines.md`
- 阶段 3 文档：`docs/stage3-kubernetes-locust.md`

阶段 3 自动化测试覆盖：

- 生成 Namespace、ServiceAccount、master Deployment、worker Deployment、Service、NetworkPolicy。
- 任务级 namespace 策略会按 manifest namespace 入库。
- Kubernetes apply 启用时，停止任务会触发 master/worker/Service/ConfigMap/ServiceAccount/NetworkPolicy 删除；任务级 namespace 策略会删除 namespace。
- Locust `/stats/requests` 原生响应转换为平台 snapshot、stats、errors、workers。
- Locust API 采集会使用已持久化的 lane namespace，兼容 tenant/run 两种 namespace 策略。
- 报告归档优先使用真实 Locust master HTML/CSV 响应。
- OpenAPI 文档包含核心接口 tags、summary 和请求字段 description。

阶段 3 测试结果：

```text
cd backend && rm -rf data artifacts && PYTHONPATH=. ../.venv/bin/pytest -q -> 14 passed in 0.52s
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py -> passed
helm template locusthub deploy/helm/locusthub -> not executed, helm is not installed in the current environment
```

阶段 3 验收边界：

- 当前环境没有真实 Kubernetes 集群，因此未执行真实 apply。
- 当前环境没有真实 Locust master，因此真实 HTTP 采集由 payload 转换测试和报告 fetcher 假实现覆盖。
- 生产环境启用方式见 `docs/stage3-kubernetes-locust.md`。

这些限制不影响阶段 3 本地验收；真实集群联调和更严格的 DNS/IP egress 治理将在后续阶段继续推进。

## 11. 阶段 4 Vben 风格管理后台验收

阶段 4 新增范围：

- Vue 3 + Vite + TypeScript 前端工程：`frontend/package.json`
- Vben 风格后台布局：`frontend/src/App.vue`
- 前端 API client：`frontend/src/api/client.ts`
- 前端业务类型：`frontend/src/types.ts`
- 前端构建脚本：`frontend/scripts/build.mjs`
- 前端结构测试：`frontend/tests/structure.test.mjs`
- 阶段 4 文档：`docs/stage4-vben-admin-console.md`

阶段 4 自动化测试覆盖：

- 前端工程必需文件存在。
- 前端 npm scripts 包含 dev/build/test:structure。
- API client 暴露 TestRun 启动、采集、停止和 Locust stats 查询函数。
- 管理后台包含 Dashboard、Tenants、Projects、Scripts、Test Plans、Test Runs、Governance、Reports 模块。
- Test Runs 详情包含 Locust UI 风格 tabs：Statistics、Failures、Workers、Download。

阶段 4 测试结果：

```text
npm install --registry=https://registry.npmjs.org/ -> installed 48 packages
node frontend/tests/structure.test.mjs -> passed
cd frontend && npm run build -> passed, built in 456ms
cd backend && rm -rf data artifacts && PYTHONPATH=. ../.venv/bin/pytest -q -> 14 passed in 0.59s
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py -> passed
git diff --check -> passed
npm audit --registry=https://registry.npmjs.org/ --omit=dev -> not executed, network approval rejected by current usage limit
```

阶段 4 验收边界：

- 本阶段未直接引入完整 `vue-vben-admin` monorepo，而是实现 Vben 风格的轻量前端工程。
- 认证仍使用 MVP demo token。
- 当前构建关闭 Vite minify；生产压缩可由 Nginx/CDN 或后续 Node 升级后处理。

## 12. 阶段 5 准入治理能力验收

阶段 5 新增范围：

- 审批记录表：`approval_requests`
- DNS/IP 风险快照表：`dns_resolution_snapshots`
- 配额使用快照表：`quota_usage_snapshots`
- DNS/IP policy：`DnsIpPolicy`
- 准入增强：`RunAdmissionController`
- Governance API：
  - `GET /api/v1/approval-requests`
  - `POST /api/v1/approval-requests/{id}/resolve`
  - `GET /api/v1/dns-resolution-snapshots`
  - `GET /api/v1/quota-usage-snapshots`
- 管理后台 Governance 视图展示审批、DNS、配额快照。
- 阶段 5 文档：`docs/stage5-governance-admission.md`

阶段 5 自动化测试覆盖：

- 创建目标白名单自动生成审批记录。
- 审批请求 approve/reject 会同步更新目标状态。
- 准入会阻断私网/保留 IP，并记录 DNS/IP 快照。
- 准入通过时记录配额使用快照。
- OpenAPI 文档包含治理接口 summary/tags。
- 前端结构测试覆盖新增治理接口和 Governance 标签。

阶段 5 测试结果：

```text
cd backend && rm -rf data artifacts && PYTHONPATH=. ../.venv/bin/pytest -q -> 18 passed in 0.63s
node frontend/tests/structure.test.mjs -> passed
cd frontend && npm run build -> passed, built in 487ms
```

阶段 5 验收边界：

- 超额审批仍按拒绝/待审批简化处理，后续阶段可扩展为正式审批流。
- NetworkPolicy 尚未按 DNS 快照收敛到具体目标 IP/CIDR。
- DNS 快照为同步 admission 记录，后续可扩展为异步复核。

## 13. 阶段 6 部署交付包验收

阶段 6 新增范围：

- 管理后台容器：`frontend/Dockerfile`
- 管理后台 Nginx 配置：`frontend/nginx.conf`
- Docker Compose 全栈服务：MySQL、API、Admin
- Helm API/Admin 镜像配置和 Admin workload
- 部署包验证脚本：`scripts/verify_deployment_package.py`
- 阶段 6 文档：`docs/stage6-deployment-package.md`

阶段 6 自动化测试覆盖：

- Compose 必须包含 `mysql`、`api`、`admin` 服务。
- Admin 镜像必须构建 Vite bundle 并通过 Nginx 代理 `/api/`。
- `.env.example` 必须覆盖本地、MySQL、OSS、Kubernetes、Locust、公开 URL 配置。
- Helm chart 必须包含 API/Admin workload 和健康检查。
- 部署包验证脚本必须输出 ready 结论。

阶段 6 测试结果：

```text
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage6_deployment_package.py -q -> 6 passed in 0.03s
node frontend/tests/structure.test.mjs -> passed
cd frontend && npm run build -> passed, built in 514ms
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage6-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage6-full-artifacts PYTHONPATH=. ../.venv/bin/pytest -q -> 24 passed in 0.64s
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py -> passed
python3 scripts/verify_deployment_package.py -> LocustHub deployment package ready
git diff --check -> passed
scripts/test_local.sh -> passed, includes npm install/build, 24 pytest cases, deployment verifier, compileall
```

阶段 6 验收边界：

- 本阶段补齐部署交付包，不直接执行真实 Docker/Helm 集群部署。
- 生产 Secret 管理、Ingress、TLS 和云厂商网关留给后续阶段。

## 14. 阶段 7 Ingress/TLS 与 Secret-ready Helm 验收

阶段 7 新增范围：

- Helm Ingress 模板：`deploy/helm/locusthub/templates/ingress.yaml`
- Helm Secret 模板：`deploy/helm/locusthub/templates/secret.yaml`
- API Deployment 敏感配置改为 `secretKeyRef`
- Helm values 新增 `ingress`、`secret` 配置块
- 部署包验证脚本覆盖 Ingress/TLS/Secret 检查
- 阶段 7 文档：`docs/stage7-ingress-secrets.md`

阶段 7 自动化测试覆盖：

- values 必须提供 Ingress/TLS 和 Secret 配置入口。
- API Deployment 必须通过 Secret 注入 MySQL 密码、OSS AK/SK 和 `DEMO_TOKEN`。
- Secret 模板支持 demo Secret 创建，也支持使用已有 Secret。
- Ingress 模板必须将 `/api` 路由到 API，将 `/` 路由到 Admin，并支持 TLS Secret。

阶段 7 测试结果：

```text
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage6_deployment_package.py tests/test_stage7_ingress_secrets.py -q -> 10 passed in 0.03s
python3 scripts/verify_deployment_package.py -> LocustHub deployment package ready, includes ingress, TLS, and Secret-backed settings
node frontend/tests/structure.test.mjs -> passed
cd frontend && npm run build -> passed, built in 472ms
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage7-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage7-full-artifacts PYTHONPATH=. ../.venv/bin/pytest -q -> 28 passed in 0.70s
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py -> passed
```

阶段 7 验收边界：

- 本阶段不创建证书签发资源，不绑定具体 Ingress Controller。
- 正式认证与租户权限模型仍在后续阶段替换 MVP demo token。

## 15. 阶段 8 认证与租户范围收敛验收

阶段 8 新增范围：

- 登录校验：`POST /api/v1/auth/login`
- 当前用户上下文：`GET /api/v1/me`
- 用户表密码 hash 字段：`users.password_hash`
- repository 用户查找：`get_user_by_token`、`get_user_by_username`
- FastAPI `current_user` 依赖和租户范围 helper
- Demo viewer 用户：`viewer/viewer`
- 阶段 8 文档：`docs/stage8-auth-tenant-scope.md`

阶段 8 自动化测试覆盖：

- 错误密码返回 `401`。
- 不存在于 `users` 表的 bearer token 返回 `401`。
- `/me` 返回 token 对应的持久化用户上下文。
- 非 admin 用户只能看到自己租户的项目。
- 非 admin 用户跨租户创建项目返回 `403`。

阶段 8 测试结果：

```text
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage8_auth_tenant_scope.py -q -> 5 passed in 0.58s
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage8-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage8-full-artifacts PYTHONPATH=. ../.venv/bin/pytest -q -> 33 passed in 0.96s
cd frontend && npm run build -> passed, built in 474ms
python3 scripts/verify_deployment_package.py -> LocustHub deployment package ready
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py -> passed
node frontend/tests/structure.test.mjs -> passed
```

阶段 8 验收边界：

- 本阶段不新增用户管理后台。
- 前端仍保留 demo token fallback，正式登录页和 token 存储策略进入后续阶段。
- 密码 hash 使用标准库实现，后续生产化可替换为 bcrypt/OIDC/企业 IdP。

## 16. 阶段 9 CI 性能基线流水线验收

阶段 9 新增范围：

- CI baseline 请求阈值：`max_p95_ms`、`max_fail_ratio`、`min_total_rps`
- CI baseline 结果查询：`GET /api/v1/ci/performance-runs/{test_run_id}/result`
- CI CLI：`scripts/run_ci_baseline.py`
- baseline violation JSON 留档
- 阶段 9 文档：`docs/stage9-ci-baseline-pipeline.md`

阶段 9 自动化测试覆盖：

- 请求级严格阈值会生成 `p95`、`fail_ratio`、`total_rps` violation。
- 结果接口返回持久化 baseline run 和 violations。
- 结果接口遵守 Stage8 租户范围。
- CLI 在 passed 结果下退出 `0` 并写 JSON artifact。
- CLI 在 failed 结果下退出 `1` 并写 JSON artifact。

阶段 9 测试结果：

```text
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage9_ci_baseline_pipeline.py -q -> 4 passed in 0.51s
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage9-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage9-full-artifacts PYTHONPATH=. ../.venv/bin/pytest -q -> 37 passed in 1.25s
cd frontend && npm run build -> passed, built in 464ms
python3 scripts/verify_deployment_package.py -> LocustHub deployment package ready
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py scripts/run_ci_baseline.py -> passed
node frontend/tests/structure.test.mjs -> passed
git diff --check -> passed
```

阶段 9 验收边界：

- 本阶段不新增 baseline profile 管理 API。
- CI 脚本为同步调用，后续可扩展为异步轮询长任务。

## 17. 阶段 10 端到端验收与完整使用文档

阶段 10 新增范围：

- 最终验收脚本：`scripts/run_acceptance_smoke.py`
- 完整部署与使用 Runbook：`docs/full-deployment-runbook.md`
- 最终验收 JSON 报告输出能力：`docs/reports/final-acceptance-smoke.json`

阶段 10 自动化测试覆盖：

- 验收脚本必须退出 `0` 并生成 JSON 报告。
- JSON 报告必须覆盖 health、auth、load test、report、CI baseline、deployment package。
- runbook 必须包含本地调试、Compose、Helm、OSS、CI 的实际命令入口。

阶段 10 测试结果：

```text
scripts/run_acceptance_smoke.py --output docs/reports/final-acceptance-smoke.json -> LocustHub acceptance smoke passed
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage10_e2e_acceptance.py -q -> 2 passed in 0.78s
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage10-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage10-full-artifacts PYTHONPATH=. ../.venv/bin/pytest -q -> 39 passed in 1.75s
cd frontend && npm run build -> passed, built in 460ms
python3 scripts/verify_deployment_package.py -> LocustHub deployment package ready
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py scripts/run_ci_baseline.py scripts/run_acceptance_smoke.py -> passed
node frontend/tests/structure.test.mjs -> passed
git diff --check -> passed
```

阶段 10 验收边界：

- 本阶段完成本地 deterministic 验收，不直接连接真实 Kubernetes/MySQL/OSS 环境。
- 真实云环境联调仍需要用户提供集群、域名、证书、OSS bucket 和 Secret。

## 18. 阶段 11 前后端不分离交付验收

阶段 11 新增范围：

- FastAPI 同源托管构建后的 Vue 管理后台。
- 前端默认 API 地址调整为 `/api/v1`。
- `scripts/run_local.sh` 改为先构建前端、再启动单个 FastAPI 服务。
- `backend/Dockerfile` 改为多阶段构建，后端镜像内置前端 `dist`。
- Docker Compose 默认只启动 `mysql` 与 `api`。
- Helm 默认 `admin.enabled=false`，Ingress 根路径路由到 `locusthub-api`。
- 阶段 11 文档：`docs/stage11-integrated-frontend-backend.md`

阶段 11 自动化测试覆盖：

- `/` 返回前端 `index.html`。
- `/assets/*` 返回静态资源。
- 前端路由 fallback 不吞掉 `/api/v1`、`/health`、Swagger/OpenAPI。
- Stage6/Stage7 部署契约与单服务默认交付一致。

阶段 11 测试结果：

```text
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_integrated_frontend.py tests/test_stage6_deployment_package.py tests/test_stage7_ingress_secrets.py -q -> 12 passed in 0.39s
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage11-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage11-artifacts PYTHONPATH=. ../.venv/bin/pytest -q -> 41 passed in 1.85s
cd frontend && npm run build -> passed, built in 468ms
python3 scripts/verify_deployment_package.py -> LocustHub deployment package ready, single api service serves admin console
scripts/run_acceptance_smoke.py --output docs/reports/final-acceptance-smoke.json -> LocustHub acceptance smoke passed
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py scripts/run_ci_baseline.py scripts/run_acceptance_smoke.py -> passed
git diff --check -> passed
```

阶段 11 验收边界：

- 前端源码仍保留独立 Vite 工程，便于后续复杂 UI 开发。
- Helm 独立 Admin workload 仍作为可选兼容路径保留，默认不启用。
- 本阶段验证本地单服务和静态部署包，未执行真实 Docker build 或 Helm template。

## 19. 阶段 12 Locust WebUI 与报告下载增强验收

阶段 12 新增范围：

- Locust Detail 增加 `Charts`、`Logs`、`Download Data`。
- 图表覆盖 RPS、Failures/s、Response Times、User Count。
- `/locust/stats` 返回 `history` 和最新 `errors`。
- `/report` 返回 artifact 列表和 master log 预览。
- 新增 artifact 下载接口：`GET /api/v1/artifacts/{artifact_id}/download`。
- 停止任务后归档 HTML report、requests CSV、failures CSV、exceptions CSV、history CSV、master log。
- 阶段 12 文档：`docs/stage12-locust-webui-report-downloads.md`

阶段 12 自动化测试覆盖：

- 报告 summary 暴露所有可下载 artifact。
- artifact 下载接口执行租户权限检查。
- 指标接口返回历史趋势和错误行。
- 前端结构包含 Charts、Logs、Download Data 和下载项。

阶段 12 测试结果：

```text
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage12_reports_webui.py -q -> 3 passed in 0.58s
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage12-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage12-artifacts PYTHONPATH=. ../.venv/bin/pytest -q -> 44 passed in 2.01s
node frontend/tests/structure.test.mjs -> passed
cd frontend && npm run build -> passed, built in 466ms
```

阶段 12 验收边界：

- 图表使用内置 SVG polyline，不引入 Chart.js/ECharts。
- 真实 Locust exceptions CSV 端点不可用时生成空 CSV，不阻塞报告归档。
- 本阶段聚焦运行详情和报告下载，完整报告对比进入后续 Stage16。
