# LocustHub 阶段 19 最终加固、Swagger 审计与 Runbook

## 1. 阶段目标

阶段 19 对 Stage12-Stage18 的增强做最终收口：

- 增加 `/ready` 就绪接口，便于部署和网关探活。
- 用自动化测试审计 `/api/v1` 下所有接口必须具备 Swagger tags、summary 和函数 docstring。
- 更新完整部署 Runbook，覆盖 Swagger、Readiness、CI baseline profile、`ci:run` scope。
- 重新生成最终验收 JSON 报告。

## 2. Readiness

`GET /ready` 返回：

- `status`
- `app`
- `database_backend`
- `artifact_storage_provider`
- `lane_runtime_backend`

该接口不暴露密钥、OSS endpoint、数据库密码或 token，只用于部署层确认服务配置形态。

## 3. Swagger 注释审计

新增测试会遍历 FastAPI `/api/v1` routes，要求每个接口都有：

- `tags`
- `summary`
- route docstring/description

这把“后续阶段实现要补充足够注释、API 接入 Swagger”的要求变成自动化约束。

## 4. Runbook

`docs/full-deployment-runbook.md` 补充：

- `/ready`
- `/docs`
- `--baseline-profile-id`
- `ci:run`
- Stage19 部署前检查命令

## 5. 验收

自动化测试覆盖：

- `/ready` 返回部署关键配置。
- `/api/v1` 接口均具备 Swagger 摘要和 docstring。
- Runbook 包含 Stage19 运维入口。

阶段边界：

- `/ready` 不主动连接 MySQL/OSS/Kubernetes 做深度探测，避免本地调试被外部依赖阻塞。
- 真实生产环境可以在后续增加 deep readiness 或单独的 diagnostics endpoint。
