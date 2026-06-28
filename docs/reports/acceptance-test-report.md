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
frontend/index.html
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

这些限制不影响业务闭环验收，生产适配器在后续 OpenSpec change 中实现。
