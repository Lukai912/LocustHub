# LocustHub 阶段 3 Kubernetes + 真实 Locust 运行时

## 1. 阶段目标

阶段 3 将阶段 1/2 的本地模拟压测运行时升级为 Kubernetes + Locust 真实执行适配：

- 生成每个 TestRun 的 Kubernetes 原生资源。
- 支持租户级 namespace 或任务级 namespace 策略。
- 支持 Locust master + worker Deployment。
- 支持 master Service 暴露 Locust Web/API。
- 支持 ServiceAccount、ConfigMap、NetworkPolicy。
- 支持配置化启用 Kubernetes apply。
- 支持从 Locust master 原生 API 采集 `/stats/requests`。
- 支持从 Locust master 下载 HTML/CSV 报告并归档。

## 2. 运行模式

默认本地模式仍然是模拟执行：

```text
LANE_RUNTIME_BACKEND=local
LOCUST_METRICS_BACKEND=simulated
KUBERNETES_APPLY_ENABLED=false
```

Kubernetes + Locust 模式：

```text
LANE_RUNTIME_BACKEND=kubernetes
LANE_NAMESPACE_STRATEGY=tenant
KUBERNETES_APPLY_ENABLED=true
LOCUST_IMAGE=locustio/locust:latest
LOCUST_METRICS_BACKEND=locust_api
LOCUST_MASTER_BASE_URL_TEMPLATE=http://{run_id}-master.{namespace}.svc.cluster.local:8089
```

## 3. 资源清单

每个 TestRun 会生成：

```text
Namespace
ServiceAccount
ConfigMap
Deployment: locust master
Service: locust master web/master ports
Deployment: locust workers
NetworkPolicy
```

master 参数示例：

```text
locust --master --headless --expect-workers N --users U --spawn-rate R --run-time Ts --host TARGET
```

worker 参数示例：

```text
locust --worker --master-host {run_id}-master
```

## 4. Locust API 采集

真实采集器使用 Locust master 原生接口：

```text
GET /stats/requests
GET /stats/report
GET /stats/requests/csv
GET /stats/failures/csv
GET /stats/requests_full_history/csv
```

`/stats/requests` 响应会转换为平台存储格式：

- `locust_run_snapshots`
- `locust_request_stat_samples`
- `locust_errors`
- `locust_workers`

报告归档优先使用 Locust 原生 HTML/CSV；如果无法访问 master，则回退到平台生成的本地报告。

## 5. Helm 权限

Helm chart 已包含：

```text
ServiceAccount: locusthub-api
ClusterRole: locusthub-lane-controller
ClusterRoleBinding: locusthub-lane-controller
```

权限范围：

- namespaces
- serviceaccounts
- configmaps
- services
- deployments
- networkpolicies

## 6. 验收边界

阶段 3 完成后：

- 代码可以生成 Kubernetes 原生 Locust 资源。
- 配置可切换为真实 Kubernetes apply。
- 配置可切换为真实 Locust API 采集。
- 报告归档可优先下载 Locust 原生 HTML/CSV。
- 本地测试仍不依赖真实集群。

阶段 3 不包含：

- Vben Admin 正式后台。
- 生产级 FQDN egress proxy。
- 多地域执行池。
