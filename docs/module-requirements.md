# LocustHub 模块需求拆分

## 1. 拆分原则

LocustHub 按可独立交付、独立验收、独立扩展的业务能力拆分模块。每个模块后续都可以对应一个或多个 OpenSpec change。

优先级定义：

```text
P0: 第一阶段必须实现，否则主流程不可用
P1: 第一阶段建议实现，影响平台可用性和安全性
P2: 后续增强，适合第二阶段或 CI 场景
```

## 2. 模块总览

```text
M01 租户与权限模块
M02 项目与脚本模块
M03 压测计划模块
M04 压测任务模块
M05 准入审批与配额模块
M06 临时压测泳道模块
M07 Locust 实时指标模块
M08 报告归档与对象存储模块
M09 管理后台模块
M10 CI 性能基线模块
M11 运维部署模块
M12 审计与观测模块
```

第一阶段最小闭环：

```text
M01 -> M02 -> M03 -> M04 -> M05 -> M06 -> M07 -> M08 -> M09
```

CI 能力作为预留和第二阶段增强：

```text
M10
```

## 3. M01 租户与权限模块

优先级：P0

### 目标

提供多租户基础能力，确保用户只能访问自己租户和项目内的数据。

### 需求

- 支持租户创建、启用、禁用。
- 支持用户登录和当前用户信息查询。
- 支持用户归属租户。
- 支持角色和权限码。
- 支持项目级权限控制。
- 所有业务查询必须带租户隔离条件。

### 主要数据

```text
tenants
users
roles
permissions
user_roles
projects
```

### 主要接口

```text
POST /api/v1/auth/login
GET  /api/v1/me
GET  /api/v1/tenants
POST /api/v1/tenants
GET  /api/v1/users
GET  /api/v1/roles
```

### 验收标准

- 不同租户用户无法查看彼此项目、任务、报告。
- 禁用租户后，该租户用户不能创建新任务。
- 无权限用户不能进入管理页面或调用对应 API。

## 4. M02 项目与脚本模块

优先级：P0

### 目标

管理项目、Locust 脚本包和脚本版本，为压测计划提供可复用执行资产。

### 需求

- 支持项目创建、编辑、归档。
- 支持上传 `locustfile.py`。
- 支持上传脚本包和 `requirements.txt`。
- 支持脚本版本管理。
- 支持脚本基础校验。
- 支持脚本文件归档到 ArtifactRepository，默认阿里云 OSS。

### 主要数据

```text
projects
script_packages
script_versions
```

### 主要接口

```text
GET  /api/v1/projects
POST /api/v1/projects
POST /api/v1/scripts
GET  /api/v1/scripts/{id}/versions
GET  /api/v1/script-versions/{id}
```

### 验收标准

- 用户可以在项目下上传脚本并生成版本。
- 压测计划可以引用指定脚本版本。
- 脚本文件在 OSS 中有对象记录，MySQL 中有索引。

## 5. M03 压测计划模块

优先级：P0

### 目标

沉淀可重复执行的压测配置，区分计划和单次执行任务。

### 需求

- 支持创建压测计划。
- 支持配置目标地址、并发用户数、spawn rate、运行时长、worker 数。
- 支持绑定脚本版本。
- 支持配置环境变量和 Secret 引用。
- 支持计划启用、禁用、复制。

### 主要数据

```text
test_plans
```

### 主要接口

```text
GET  /api/v1/test-plans
POST /api/v1/test-plans
GET  /api/v1/test-plans/{id}
PUT  /api/v1/test-plans/{id}
POST /api/v1/test-plans/{id}/clone
```

### 验收标准

- 用户可以基于脚本版本创建压测计划。
- 用户可以从计划启动一次 TestRun。
- 禁用计划不能启动新任务。

## 6. M04 压测任务模块

优先级：P0

### 目标

管理单次压测执行生命周期，连接计划、准入、泳道、指标和报告。

### 需求

- 支持从压测计划创建 TestRun。
- 支持手动启动、停止、取消任务。
- 支持任务状态机。
- 支持任务来源：`manual`、`api`、`ci`、`schedule`。
- 支持任务详情查询。
- 支持运行中和已结束任务列表。

### 状态机

```text
CREATED
VALIDATING
APPROVAL_PENDING
APPROVED
LANE_CREATING
PROVISIONING
RUNNING
COLLECTING
ARCHIVING
DESTROYING
COMPLETED
FAILED
CANCELING
CANCELED
```

### 主要数据

```text
test_runs
test_run_lanes
```

### 主要接口

```text
POST /api/v1/test-runs
GET  /api/v1/test-runs
GET  /api/v1/test-runs/{id}
POST /api/v1/test-runs/{id}/start
POST /api/v1/test-runs/{id}/stop
POST /api/v1/test-runs/{id}/cancel
```

### 验收标准

- 启动任务后状态按预期流转。
- 停止任务后进入归档和销毁流程。
- 失败任务保留失败原因和归档数据。

## 7. M05 准入审批与配额模块

优先级：P0

### 目标

在创建运行资源前完成安全准入，避免未授权目标访问、超配额压测和不受控流量。

### 需求

- 支持目标白名单。
- 支持目标审批。
- 支持超额审批。
- 支持 DNS 解析快照。
- 支持 IP/CIDR 风险校验。
- 支持租户资源配额。
- 支持流量配额。
- 支持生成 NetworkPolicy 输入。

### 主要数据

```text
target_whitelists
approval_requests
tenant_quotas
quota_usage_snapshots
```

### 主要接口

```text
GET  /api/v1/target-whitelists
POST /api/v1/target-whitelists
POST /api/v1/target-whitelists/{id}/approve
POST /api/v1/target-whitelists/{id}/reject

GET  /api/v1/approval-requests
POST /api/v1/approval-requests/{id}/approve
POST /api/v1/approval-requests/{id}/reject

GET  /api/v1/tenant-quotas
PUT  /api/v1/tenant-quotas/{tenant_id}
```

### 验收标准

- 未审批目标不能启动压测。
- 超过配额的任务不能启动，或进入审批。
- NetworkPolicy 只允许访问审批通过的 IP/CIDR 和端口。

## 8. M06 临时压测泳道模块

优先级：P0

### 目标

参考测试环境泳道，为每个运行中的 TestRun 动态创建独立 Locust 运行环境。

### 需求

- 每个 TestRun 创建 1 个 Locust master 和 N 个 worker。
- 支持租户级 namespace + 任务级资源。
- 支持后续扩展任务级 namespace。
- 创建 ServiceAccount、ConfigMap、Secret、Service、NetworkPolicy。
- 支持 worker 只连接本任务 master。
- 任务完成后销毁运行资源。

### 主要组件

```text
LaneController
KubernetesManifestBuilder
LocustCommandBuilder
```

### 主要数据

```text
test_run_lanes
```

### 验收标准

- 同时运行的多个任务拥有不同 master 和 worker。
- worker 不会连接到其他任务的 master。
- 任务销毁后 Kubernetes 运行资源被清理。

## 9. M07 Locust 实时指标模块

优先级：P0

### 目标

实时采集每个任务的 Locust UI 数据，并按 Locust UI 效果展示。

### 需求

- 定时采集每个 Locust master 的 `/stats/requests`。
- 定时采集 `/exceptions`、`/tasks`、`/logs`、`/worker-count`。
- 支持 WebSocket 或 SSE 推送给前端。
- 支持写入 MySQL。
- 保留 Locust 原始字段语义。
- 支持任务结束后查询历史指标。

### 主要数据

```text
locust_run_snapshots
locust_request_stat_samples
locust_error_samples
locust_exception_samples
locust_worker_samples
```

### 主要接口

```text
GET /api/v1/test-runs/{run_id}/locust/stats
GET /api/v1/test-runs/{run_id}/locust/exceptions
GET /api/v1/test-runs/{run_id}/locust/tasks
GET /api/v1/test-runs/{run_id}/locust/logs
GET /api/v1/test-runs/{run_id}/locust/workers
WS  /api/v1/test-runs/{run_id}/locust/ws
```

### 验收标准

- 运行中任务可以实时看到 RPS、Failures/s、P50、P95、用户数。
- Statistics 表字段和 Locust UI 对齐。
- 多个任务同时运行时，指标互不混淆。

## 10. M08 报告归档与对象存储模块

优先级：P0

### 目标

任务结束后归档报告、CSV、日志和原始快照，确保运行资源销毁后仍可查看和下载。

### 需求

- 定义 `ArtifactRepository` 抽象。
- 第一阶段实现 `AliyunOssArtifactRepository`。
- 上传 HTML report、requests CSV、failures CSV、history CSV。
- 上传 master/worker 日志。
- 上传最终 JSON 快照。
- MySQL 保存 provider、bucket、object key、checksum、文件大小、content type。
- 支持生成临时下载或预览 URL。

### 主要数据

```text
locust_report_summaries
artifact_objects
```

### 主要接口

```text
GET /api/v1/test-runs/{run_id}/report
GET /api/v1/test-runs/{run_id}/artifacts
GET /api/v1/artifacts/{artifact_id}/download-url
GET /api/v1/artifacts/{artifact_id}/preview-url
```

### 验收标准

- 任务进入 DESTROYING 前，报告和日志已完成归档。
- 用户可以在任务结束后下载 HTML/CSV/日志。
- 业务代码只依赖 ArtifactRepository，不直接依赖 OSS SDK。

## 11. M09 管理后台模块

优先级：P0

### 目标

使用 Vben Admin 实现平台管理和任务监控页面。

### 页面需求

```text
仪表盘
租户管理
项目管理
目标白名单
脚本管理
压测计划
执行记录
任务详情
报告中心
审批中心
系统配置
```

### 任务详情页

参照 Locust UI：

```text
RunHeader
RunControlBar
StatisticsTable
RealtimeCharts
FailuresTable
ExceptionsTable
WorkersTable
LogsPanel
DownloadPanel
```

### 验收标准

- 用户可以从后台完成创建计划、启动任务、查看实时数据、下载报告。
- 任务详情页面的表格和图表效果参照 Locust UI。
- 前端权限和后端权限一致。

## 12. M10 CI 性能基线模块

优先级：P2

### 目标

支持 CI 通过 API 发起性能基线任务，并返回通过、失败或警告结果。

### 需求

- 支持 CI token。
- 支持 baseline profile。
- 支持固定阈值。
- 支持 CI 创建 TestRun。
- 支持查询基线结果。
- 后续支持相对基线对比。

### 主要数据

```text
ci_tokens
baseline_profiles
baseline_runs
baseline_threshold_violations
```

### 主要接口

```text
POST /api/v1/ci/performance-runs
GET  /api/v1/ci/performance-runs/{test_run_id}/result
```

### 验收标准

- CI 可以通过 token 创建压测任务。
- 基线任务复用同一套 TestRun、泳道、指标和报告链路。
- 超过阈值时返回 failed，并包含违规项。

## 13. M11 运维部署模块

优先级：P1

### 目标

提供可部署、可配置、可运维的运行环境。

### 需求

- FastAPI 镜像。
- Vben Admin 镜像。
- Locust runner 镜像。
- Kubernetes manifest 或 Helm chart。
- MySQL 配置。
- 阿里云 OSS 配置。
- Kubernetes RBAC。
- Namespace、ResourceQuota、LimitRange、NetworkPolicy 模板。

### 验收标准

- 可以在 Kubernetes 环境部署管理面。
- 可以动态创建压测泳道。
- 配置项不写死在代码中。

## 14. M12 审计与观测模块

优先级：P1

### 目标

记录关键操作和系统运行状态，支撑排查、审计和安全追踪。

### 需求

- 记录登录、创建任务、启动任务、停止任务。
- 记录目标审批、配额审批。
- 记录准入校验结果。
- 记录泳道创建和销毁事件。
- 记录报告归档状态。
- 支持查询审计日志。

### 主要数据

```text
audit_logs
system_events
```

### 验收标准

- 可以按租户、用户、任务查询操作日志。
- 任务失败时可以看到失败阶段和原因。
- 审计日志不能被普通用户删除。

## 15. 推荐 OpenSpec 变更拆分

```text
add-fastapi-backend-skeleton
add-vben-admin-skeleton
add-mysql-domain-models
add-tenant-rbac
add-project-script-management
add-test-plan-management
add-test-run-lifecycle
add-run-admission-controller
add-locust-lane-controller
add-locust-metrics-collector
add-artifact-repository-oss
add-locust-report-archive
add-admin-run-detail-ui
add-audit-events
add-ci-baseline-api
```

模块增强交付要求：

- 每个模块增强都必须通过远端 PR 合并。
- PR 必须包含真实内容变更，不能使用空提交作为交付记录。
- 真实内容可以是代码、测试、文档、配置、migration 或 OpenSpec 变更。
- PR 描述必须标明影响模块、验证方式和是否影响租户隔离、安全准入、Locust UI 字段或报告归档。
- 如果一个 PR 同时影响多个模块，需要在 PR 描述中列出模块映射。

## 16. 第一阶段建议排期

### Milestone 1: 项目骨架和基础数据

- M01 租户与权限模块
- M02 项目与脚本模块
- M03 压测计划模块
- MySQL migration 基础结构

### Milestone 2: 压测任务主链路

- M04 压测任务模块
- M05 准入审批与配额模块基础版
- M06 临时压测泳道模块

### Milestone 3: 实时指标和报告

- M07 Locust 实时指标模块
- M08 报告归档与对象存储模块
- M09 任务详情页

### Milestone 4: 平台可用性

- M11 运维部署模块
- M12 审计与观测模块
- M10 CI 性能基线预留接口
