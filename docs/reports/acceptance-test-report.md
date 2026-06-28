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

## 6. 验收结论

LocustHub MVP 本地调试版本通过当前自动化验收。用户可以在本地启动 FastAPI 服务，并通过本地管理页面完成 Demo 压测任务创建、启动、实时指标查看、停止归档等主流程。

## 7. MVP 限制

- 本地 MVP 使用 SQLite 模拟 MySQL。
- 本地 MVP 使用本地文件系统模拟阿里云 OSS。
- 本地 MVP 使用 manifest 模拟 Kubernetes 资源创建。
- 本地 MVP 使用模拟指标替代真实 Locust master 采集。

这些限制不影响业务闭环验收，生产适配器在后续 OpenSpec change 中实现。
