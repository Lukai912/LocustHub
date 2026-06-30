# LocustHub 阶段 14 任务诊断与重跑

## 1. 阶段目标

阶段 14 强化压测任务的日常排障体验：

- 记录任务生命周期事件。
- 提供任务诊断接口。
- 支持从已有任务重新创建 run。
- 管理台展示诊断建议和生命周期事件。

## 2. 后端能力

新增表：

- `test_run_events`

任务创建和状态变化时写入事件。事件记录靠近状态变更代码写入，避免运行资源销毁后无法解释任务曾经发生过什么。

新增接口：

- `GET /api/v1/test-runs/{run_id}/diagnostics`
- `POST /api/v1/test-runs/{run_id}/rerun`

diagnostics 返回：

- run 基本信息
- lane 信息
- latest snapshot
- latest errors
- workers
- report
- lifecycle events
- recommendations

## 3. 管理台

Test Runs 页面新增：

- `Rerun`
- `Diagnostics` tab
- `Recommendations`
- `Lifecycle Events`

诊断建议基于当前状态、lane、错误行和报告归档状态生成，帮助用户快速判断下一步应该看 charts、logs、Kubernetes runtime 还是 artifact storage。

## 4. 验收

```bash
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage14_run_diagnostics.py -q
node frontend/tests/structure.test.mjs
cd frontend && npm run build
```

验收点：

- diagnostics 返回 run、lane、latest snapshot、events 和 recommendations。
- rerun 会基于原 test plan 创建新的 `CREATED` run。
- 前端包含 Diagnostics、Rerun、Recommendations、Lifecycle Events。
