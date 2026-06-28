# LocustHub 多租户压测 PaaS Spec

## 1. 背景

本系统基于 Locust 压测工具建设一套多租户压测 PaaS。平台服务端使用 FastAPI，管理后台前端使用 `vbenjs/vue-vben-admin`。系统需要支持不同租户同时执行不同压测任务，并且压测任务的实时指标、字段维度、页面效果尽量参照 Locust 原生 Web UI。

多租户运行隔离参考测试环境泳道实现方式：每次压测任务动态拉起一条临时压测泳道，任务完成后销毁运行资源，操作数据和压测数据保存在平台侧。

## 2. 目标

- 支持多个租户、多个项目管理压测任务。
- 支持每个压测任务独立运行 Locust master 和 worker。
- 支持按租户、项目、任务隔离运行资源。
- 支持目标白名单、审批、NetworkPolicy、DNS/IP 限制。
- 支持资源配额和流量配额。
- 支持实时采集 Locust 指标，字段和展示参照 Locust UI。
- 支持任务结束后归档指标、日志、报告和操作记录。
- 支持后续接入 CI 执行性能基线。
- 第一阶段用户量不大，业务数据和指标数据统一使用 MySQL。

## 3. 非目标

- 第一阶段不建设复杂计费系统。
- 第一阶段不强制引入 ClickHouse、TimescaleDB 等时序数据库。
- 第一阶段不要求支持大规模公网压测。
- 第一阶段不要求实现跨地域压测资源池。
- 第一阶段不要求替代 Locust 自身的核心压测引擎。

## 4. 总体架构

```text
用户 / CI
  -> Vben Admin / CI API
  -> FastAPI 控制面
      -> 认证与权限
      -> 租户与项目
      -> 脚本与计划
      -> 审批与配额
      -> Run Admission Controller
      -> Lane Controller
      -> Metrics Collector
      -> Report Archiver
  -> Kubernetes 压测泳道
      -> Locust Master
      -> Locust Workers
      -> ServiceAccount
      -> ConfigMap / Secret
      -> Service / Ingress
      -> NetworkPolicy
      -> ResourceQuota / LimitRange
  -> MySQL / 对象存储
```

### 4.1 管理面

管理面常驻运行：

- FastAPI API 服务
- Vben Admin 管理后台
- 调度器
- 审批服务
- 配额服务
- 指标采集器
- 报告归档器

### 4.2 运行面

运行面按任务临时创建：

- 1 个 Locust master
- N 个 Locust worker
- 任务级 Service
- 任务级 ServiceAccount
- 任务级 ConfigMap 和 Secret
- 任务级 NetworkPolicy
- 可选任务级 Ingress

每个压测任务对应一条临时压测泳道。

## 5. 多租户泳道模型

### 5.1 基本关系

```text
Tenant
  -> Project
    -> TestPlan
      -> TestRun
        -> LoadTestLane
          -> Locust Master
          -> Locust Workers
```

### 5.2 推荐隔离粒度

第一阶段推荐租户级 namespace + 任务级资源：

```text
namespace: lt-tenant-a
  - run-001-master
  - run-001-worker
  - run-001-service
  - run-001-network-policy
  - run-002-master
  - run-002-worker
  - run-002-service
  - run-002-network-policy
```

后续可支持任务级 namespace：

```text
namespace: lt-tenant-a-run-001
namespace: lt-tenant-a-run-002
```

### 5.3 为什么每个任务一个 Locust master

Locust master 维护一次压测的控制状态、worker 连接、实时统计、错误、异常、报告和 UI API。为了避免多个任务之间统计混淆、脚本污染、启动停止互相影响，生产模式默认：

```text
1 个 TestRun = 1 个 Locust master + N 个 Locust workers
```

低并发脚本验证场景可以使用 standalone Locust 进程，但多租户正式压测不推荐共享 master。

## 6. 任务生命周期

```text
CREATED
  -> VALIDATING
  -> APPROVAL_PENDING
  -> APPROVED
  -> LANE_CREATING
  -> PROVISIONING
  -> RUNNING
  -> COLLECTING
  -> ARCHIVING
  -> DESTROYING
  -> COMPLETED
```

失败流程：

```text
FAILED
  -> ARCHIVING
  -> DESTROYING
```

取消流程：

```text
CANCELING
  -> ARCHIVING
  -> DESTROYING
  -> CANCELED
```

核心原则：先归档，再销毁。任务结束或失败后，需要先采集最后一批指标、日志、错误、异常、报告和 Kubernetes 事件，再销毁泳道资源。

## 7. 安全准入

每次 TestRun 进入 `LANE_CREATING` 前，需要经过 Run Admission Controller 校验。

### 7.1 准入流程

```text
创建 TestRun
  -> 目标白名单校验
  -> DNS/IP 解析与风险检查
  -> 审批状态校验
  -> 资源配额校验
  -> 流量配额校验
  -> NetworkPolicy 生成校验
  -> 审计记录写入
  -> 创建临时压测泳道
```

未通过准入校验的任务不能拉起 Locust。

### 7.2 目标白名单

白名单需要结构化保存：

```text
target_whitelists
- id
- tenant_id
- project_id
- target_type: domain | ip | cidr
- value
- ports
- protocols
- environment
- status: pending | approved | rejected | expired
- risk_level
- approved_by
- approved_at
- expires_at
- reason
- proof_url
```

任务目标必须匹配：

- 租户
- 项目
- host 或 IP
- 端口
- 协议
- 环境
- 审批状态
- 有效期

### 7.3 审批

需要支持两类审批：

- 目标审批：新增域名、IP、CIDR，访问生产环境，访问公网目标，访问跨租户内网地址。
- 超额审批：worker 数、并发用户数、spawn rate、运行时长、RPS、带宽超过默认配额。

审批记录保存：

```text
approval_requests
- id
- tenant_id
- project_id
- request_type: target | quota | run
- status
- applicant_id
- approver_id
- payload_json
- decision_reason
- created_at
- approved_at
```

### 7.4 DNS/IP 限制

Kubernetes 原生 NetworkPolicy 不支持直接按域名做 FQDN 出网限制。第一阶段采用：

- 域名启动前解析为 IP。
- 保存 DNS 快照。
- 将解析出的 IP 写入 NetworkPolicy。
- 任务运行中定期复查 DNS。
- DNS 漂移超出白名单时暂停或终止任务。

增强版本可接入：

- Cilium FQDN Policy
- Calico FQDN Policy
- Egress Proxy

生产推荐最终采用默认拒绝出网 + 允许 DNS + 允许 Egress Proxy 的模式。

### 7.5 NetworkPolicy

默认策略：

- 禁止任务 Pod 访问其他任务 Pod。
- worker 只允许访问本任务 master。
- 任务 Pod 只允许访问审批通过的目标 IP/CIDR 和端口。
- 允许访问 DNS。
- 可选允许访问对象存储、指标采集服务、平台回调服务。

示例策略：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: run-001-egress
spec:
  podSelector:
    matchLabels:
      test-run-id: run-001
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    - to:
        - ipBlock:
            cidr: 203.0.113.10/32
      ports:
        - protocol: TCP
          port: 443
```

## 8. 配额设计

### 8.1 资源配额

租户级资源配额：

```text
tenant_quotas
- max_concurrent_runs
- max_workers_per_run
- max_total_workers
- max_cpu_cores
- max_memory_gb
- max_run_duration_seconds
- max_artifact_storage_gb
- max_metric_retention_days
```

Kubernetes 层：

- ResourceQuota
- LimitRange
- Pod CPU requests/limits
- Pod memory requests/limits

### 8.2 流量配额

平台业务层控制：

```text
traffic_quotas
- max_users
- max_spawn_rate
- max_rps
- max_fail_ratio_before_abort
- max_duration_seconds
- max_bandwidth_mbps
- max_requests_total
```

第一阶段可直接限制：

- Locust users
- spawn rate
- run time
- worker 数量

后续再通过 Egress Proxy、CNI、tc 或 eBPF 限制 RPS 和带宽。

## 9. 数据存储

用户量不大，第一阶段统一使用 MySQL 保存业务数据和中低频指标数据。

### 9.1 MySQL

MySQL 保存：

- 租户
- 用户
- 权限
- 项目
- 脚本版本
- 压测计划
- 压测任务
- 压测泳道
- 审批记录
- 配额记录
- 操作审计
- Locust 实时指标
- 请求统计快照
- 错误统计
- 异常统计
- Worker 状态
- 历史趋势汇总
- 报告索引
- CI 基线配置和结果

### 9.2 对象存储与阿里云 OSS

第一阶段对象存储默认接入阿里云 OSS，但系统设计需要保持可扩展。业务层只依赖 `ArtifactRepository` 抽象，不直接依赖 OSS SDK、bucket、endpoint 或签名 URL 细节。后续如需切换到 MinIO、AWS S3、腾讯云 COS、华为云 OBS 或内部对象存储，只需要新增适配器实现。

对象存储保存：

- locustfile.py
- 脚本包
- requirements.txt
- HTML report
- CSV report
- 日志归档
- 原始 JSON 快照
- 任务运行产物

第一阶段实现：

```text
ArtifactRepository interface
  -> AliyunOssArtifactRepository
```

后续可扩展：

```text
ArtifactRepository interface
  -> AliyunOssArtifactRepository
  -> MinioArtifactRepository
  -> S3ArtifactRepository
  -> CosArtifactRepository
  -> LocalFsArtifactRepository，仅限开发测试
```

OSS bucket 建议使用私有读写，不直接公开。所有上传、下载和预览都经过 FastAPI 鉴权：

```text
用户
  -> Vben Admin
  -> FastAPI 鉴权和租户权限校验
  -> ArtifactRepository 生成临时访问 URL
  -> 下载或预览报告文件
```

对象 Key 按租户、项目、任务分层：

```text
loadtest-artifacts/
  tenants/{tenant_id}/
    projects/{project_id}/
      runs/{run_id}/
        scripts/
          locustfile.py
          package.zip
          requirements.txt
        reports/
          report.html
          requests.csv
          failures.csv
          history.csv
        logs/
          master.log
          workers.log
        raw/
          stats-final.json
          exceptions-final.json
          workers-final.json
          stats-snapshots.jsonl
```

FastAPI 需要提供统一的文件归档适配层：

```text
ArtifactRepository
- upload_script_package()
- upload_report()
- upload_csv()
- upload_log_archive()
- upload_raw_snapshot()
- generate_download_url()
- generate_preview_url()
- delete_artifact()
- get_artifact_metadata()
```

阿里云 OSS 适配器配置项：

```text
ARTIFACT_STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ENDPOINT
ALIYUN_OSS_REGION
ALIYUN_OSS_BUCKET
ALIYUN_OSS_ACCESS_KEY_ID
ALIYUN_OSS_ACCESS_KEY_SECRET
ALIYUN_OSS_ROLE_ARN，可选
ALIYUN_OSS_SIGNED_URL_EXPIRE_SECONDS
```

生产环境优先使用 RAM 角色或 STS 临时凭证，避免在应用中长期保存高权限 AccessKey。OSS bucket 需要配置生命周期规则，例如日志和原始快照保留 30 到 90 天，HTML/CSV 报告按业务要求长期保留。

### 9.3 MySQL 指标保留策略

建议：

- 实时采集频率：2s 或 5s。
- 原始采样保留：7 到 15 天。
- 任务结束后生成汇总报告。
- 历史查询优先查汇总表。
- 大文件、原始快照、CSV 和 HTML 报告通过 `ArtifactRepository` 放入对象存储。

后续规模增大后，可将历史指标迁移到 ClickHouse，但 API 层应通过 `MetricsRepository` 抽象，避免绑定具体存储。

## 10. 数据模型

### 10.1 基础表

```text
tenants
users
roles
permissions
user_roles
projects
```

### 10.2 脚本与计划

```text
script_packages
script_versions
test_plans
```

### 10.3 压测任务

```text
test_runs
- id
- tenant_id
- project_id
- test_plan_id
- script_version_id
- source: manual | ci | schedule | api
- status
- target_host
- users
- spawn_rate
- run_time_seconds
- worker_count
- config_json
- created_by
- created_at
- updated_at
- started_at
- ended_at
```

```text
test_run_lanes
- id
- tenant_id
- project_id
- test_run_id
- namespace
- master_pod_name
- master_service_name
- worker_deployment_name
- worker_count
- service_account_name
- network_policy_name
- manifest_snapshot_json
- status
- created_at
- destroyed_at
```

### 10.4 指标表

```text
locust_run_snapshots
- id
- tenant_id
- project_id
- run_id
- sample_time
- state
- user_count
- worker_count
- total_rps
- total_fail_per_sec
- fail_ratio
- current_p50
- current_p95
- avg_response_time
```

```text
locust_request_stat_samples
- id
- tenant_id
- project_id
- run_id
- sample_time
- method
- name
- num_requests
- num_failures
- current_rps
- current_fail_per_sec
- total_rps
- total_fail_per_sec
- avg_response_time
- median_response_time
- min_response_time
- max_response_time
- response_time_percentile_0_95
- response_time_percentile_0_99
- avg_content_length
```

```text
locust_error_samples
- id
- tenant_id
- project_id
- run_id
- sample_time
- method
- name
- error
- occurrences
- first_seen
- last_seen
```

```text
locust_exception_samples
- id
- tenant_id
- project_id
- run_id
- sample_time
- count
- message
- traceback
- nodes
```

```text
locust_worker_samples
- id
- tenant_id
- project_id
- run_id
- sample_time
- worker_id
- state
- user_count
- cpu_usage
- memory_usage
```

建议索引：

```text
(run_id, sample_time)
(tenant_id, run_id, sample_time)
(run_id, method, name, sample_time)
```

### 10.5 报告与审计

```text
locust_report_summaries
audit_logs
approval_requests
tenant_quotas
quota_usage_snapshots
target_whitelists
```

## 11. Locust UI 对齐

### 11.1 实时采集接口

每个任务有独立 Locust master，因此可以采集原生接口：

```text
GET /stats/requests
GET /exceptions
GET /tasks
GET /logs
GET /worker-count
GET /stats/report
GET /stats/requests/csv
GET /stats/failures/csv
GET /stats/requests_full_history/csv
```

### 11.2 页面效果

Vben 后台的任务详情页参照 Locust UI：

```text
Run Detail
  - Header
  - Control Bar
  - Statistics
  - Charts
  - Failures
  - Exceptions
  - Workers
  - Logs
  - Download
```

Statistics 表字段：

```text
Type
Name
Requests
Fails
Median
Average
Min
Max
Average size
Current RPS
Current Failures/s
95%
99%
```

Charts：

```text
Total Requests per Second
- RPS
- Failures/s

Response Times
- P50
- P95

Number of Users
- user_count
```

### 11.3 字段命名

后端采集和前端 API 尽量保留 Locust 原始字段名：

```text
current_rps
current_fail_per_sec
num_requests
num_failures
avg_response_time
median_response_time
min_response_time
max_response_time
response_time_percentile_0.95
response_time_percentile_0.99
avg_content_length
```

MySQL 列名不支持点号时，存储层可转换为：

```text
response_time_percentile_0_95
response_time_percentile_0_99
```

API 输出层再映射回 Locust 风格字段。

## 12. FastAPI API

### 12.1 管理 API

```text
POST   /api/v1/auth/login
GET    /api/v1/me

GET    /api/v1/tenants
POST   /api/v1/tenants

GET    /api/v1/projects
POST   /api/v1/projects

POST   /api/v1/scripts
GET    /api/v1/scripts/{id}/versions

POST   /api/v1/test-plans
GET    /api/v1/test-plans
GET    /api/v1/test-plans/{id}

POST   /api/v1/test-runs
GET    /api/v1/test-runs
GET    /api/v1/test-runs/{id}
POST   /api/v1/test-runs/{id}/stop
```

### 12.2 Locust 任务 API

```text
GET /api/v1/test-runs/{run_id}/locust/stats
GET /api/v1/test-runs/{run_id}/locust/exceptions
GET /api/v1/test-runs/{run_id}/locust/tasks
GET /api/v1/test-runs/{run_id}/locust/logs
GET /api/v1/test-runs/{run_id}/locust/workers
GET /api/v1/test-runs/{run_id}/locust/events
```

实时推送：

```text
WS /api/v1/test-runs/{run_id}/locust/ws
```

### 12.3 审批与配额 API

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

## 13. CI 性能基线

后续 CI 不直接绕过平台跑 Locust，而是调用平台 API 创建 TestRun。

```text
CI Pipeline
  -> POST /api/v1/ci/performance-runs
  -> 平台准入校验
  -> 创建临时压测泳道
  -> 实时采集指标
  -> 生成报告
  -> 返回基线判定结果
  -> CI 决定通过或失败
```

### 13.1 CI 模型

```text
baseline_profiles
- id
- tenant_id
- project_id
- name
- target_env
- test_plan_id
- branch_pattern
- trigger_type: manual | ci | schedule
- thresholds_json
- compare_strategy
- enabled
```

```text
baseline_runs
- id
- tenant_id
- project_id
- test_run_id
- ci_provider
- pipeline_id
- job_id
- commit_sha
- branch
- tag
- mr_id
- pr_id
- status
- conclusion: passed | failed | warning
- report_url
```

```text
ci_tokens
- id
- tenant_id
- project_id
- name
- token_hash
- scopes
- expires_at
- last_used_at
```

### 13.2 基线阈值

第一阶段支持固定阈值：

```text
p95 <= 400ms
p99 <= 800ms
fail_ratio <= 0.1%
total_rps >= 1000
error_count == 0
```

后续支持相对基线：

```text
p95 不比 main 分支最近成功基线恶化超过 10%
avg_response_time 不比上一次 release 基线恶化超过 15%
fail_ratio 不高于最近 7 次均值 + 阈值
```

## 14. 前端页面

Vben Admin 菜单建议：

```text
仪表盘
  - 平台概览
  - 租户资源使用
  - 当前运行任务

租户管理
  - 租户列表
  - 用户管理
  - 角色权限
  - 配额管理

压测管理
  - 项目列表
  - 目标白名单
  - 脚本管理
  - 压测计划
  - 执行记录

任务监控
  - 实时任务
  - Statistics
  - Charts
  - Failures
  - Exceptions
  - Workers
  - Logs

报告中心
  - 报告列表
  - 基线对比
  - SLA 判定

系统管理
  - 集群配置
  - 镜像配置
  - 审计日志
  - 告警配置
```

任务详情组件建议：

```text
views/load-test/run-detail/
  index.vue
  components/
    RunHeader.vue
    RunControlBar.vue
    StatisticsTable.vue
    RealtimeCharts.vue
    FailuresTable.vue
    ExceptionsTable.vue
    WorkersTable.vue
    LogsPanel.vue
    DownloadPanel.vue
```

## 15. 归档策略

任务结束时进入 `ARCHIVING`，需要保存：

- 最后一批 `/stats/requests`
- errors
- exceptions
- workers
- logs
- HTML report
- requests CSV
- failures CSV
- history CSV
- Kubernetes events
- Pod termination reason
- 操作审计
- 准入校验记录
- 审批记录

归档阶段需要通过 `ArtifactRepository` 将 HTML、CSV、日志和原始 JSON 快照上传到对象存储。第一阶段默认落到阿里云 OSS。MySQL 的报告索引表保存 provider、bucket、object key、文件大小、content type、checksum 和归档状态。归档成功后才能进入 `DESTROYING`。

## 16. 第一阶段实施范围

第一阶段实现：

- FastAPI 控制面。
- Vben Admin 管理后台。
- MySQL 统一保存业务数据和中低频指标。
- `ArtifactRepository` 文件归档抽象，第一阶段默认使用阿里云 OSS 保存脚本、报告、CSV、日志和原始快照。
- 租户级 namespace。
- 每任务独立 Locust master + workers。
- 目标白名单。
- 审批流。
- 资源配额。
- 基础 NetworkPolicy。
- DNS 解析快照。
- 实时采集 Locust 指标。
- 任务结束归档并销毁泳道。
- CI 基线模型预留。

## 17. 第二阶段演进

第二阶段可增强：

- 任务级 namespace。
- Egress Proxy。
- FQDN NetworkPolicy。
- RPS 和带宽限速。
- 多地域执行池。
- ClickHouse 历史指标。
- 相对基线对比。
- 自动告警。
- 租户账单。
- 高级报表。

## 18. 验收标准

- 一个租户可以创建项目、上传脚本、创建压测计划并执行任务。
- 一个 TestRun 会创建独立 Locust master 和 worker。
- 任务运行时 Vben 页面能看到参照 Locust UI 的 Statistics、Charts、Failures、Exceptions、Workers、Logs。
- 指标字段与 Locust 原生字段保持一致或可映射。
- 未审批目标不能启动压测。
- 超过配额的任务不能启动或进入审批。
- NetworkPolicy 限制任务只能访问审批通过的目标。
- 任务结束后运行资源被销毁。
- 任务结束后操作记录、指标、日志、报告可查询。
- CI 可以通过 API 创建基线压测任务，并获取最终判定结果。
