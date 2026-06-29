# LocustHub 本地调试说明

## 启动 LocustHub

```bash
./scripts/run_local.sh
```

管理后台和 API 由同一个 FastAPI 服务提供：

```text
Admin: http://127.0.0.1:8000/
Swagger: http://127.0.0.1:8000/docs
```

默认登录 token：

```text
dev-token
```

管理页面可以完成：

- 创建并启动 Demo 压测任务
- 查看 Locust UI 风格 Statistics
- 手动采集实时指标
- 停止任务并归档报告

## API 调试

```bash
curl -H "Authorization: Bearer dev-token" http://127.0.0.1:8000/api/v1/test-plans
```

## 运行测试

```bash
./scripts/test_local.sh
```

## MVP 说明

本地 MVP 默认使用：

- SQLite 模拟 MySQL
- 本地文件系统模拟 ArtifactRepository
- 内存 manifest 模拟 Kubernetes 压测泳道
- 模拟 Locust 指标数据

Demo 压测计划默认使用 JSONPlaceholder 作为真实网络 API 验证目标：

```text
https://jsonplaceholder.typicode.com/todos/1
```

该目标只用于低并发 smoke/perf sanity 验证，默认配置为：

```text
users = 5
spawn_rate = 1
worker_count = 1
run_time_seconds = 60
```

生产适配器保持扩展点：

- MySQL repository
- AliyunOssArtifactRepository
- Kubernetes LaneController
- Real Locust MetricsCollector
