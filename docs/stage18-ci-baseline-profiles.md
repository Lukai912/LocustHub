# LocustHub 阶段 18 CI 基线 Profile 与 Token Scope

## 1. 阶段目标

阶段 18 将 CI 性能基线从“每次请求都传阈值”升级为更适合流水线复用的模式：

- 支持创建和查询 baseline profile。
- CI run 可以通过 `baseline_profile_id` 复用阈值。
- API Token 调用 CI run 时必须具备 `ci:run` scope。
- CLI 支持 `--baseline-profile-id`。
- 管理后台新增 `CI Baselines` 页面管理 profile。

## 2. 后端接口

新增接口：

- `GET /api/v1/ci/baseline-profiles`
- `POST /api/v1/ci/baseline-profiles`

增强接口：

- `POST /api/v1/ci/performance-runs`
- `GET /api/v1/ci/performance-runs/{test_run_id}/result`

当请求带有 `baseline_profile_id` 时，系统使用 profile 中的 `max_p95_ms`、`max_fail_ratio`、`min_total_rps` 作为判定阈值。

## 3. Token Scope

普通用户 bearer token 不受 scope 限制。API Token 调用 CI run 时必须包含：

- `ci:run`

缺失该 scope 时返回 `403`，避免只用于报告读取的 token 发起真实压测流量。

## 4. CLI

`scripts/run_ci_baseline.py` 新增：

```bash
--baseline-profile-id profile-main
```

脚本仍保留直接传阈值的模式，便于本地调试和临时流水线使用。

## 5. 前端

管理后台新增 `CI Baselines` 导航：

- `Baseline Profiles`
- `Create Baseline Profile`
- `Max P95`
- `Max Fail Ratio`
- `Min RPS`

## 6. 验收

自动化测试覆盖：

- baseline profile 可以驱动 CI 阈值判定。
- 缺少 `ci:run` scope 的 API Token 无法发起 CI run。
- CLI 可以把 `baseline_profile_id` 写入请求 payload。
- 旧的 Stage9 请求级阈值模式仍通过测试。

阶段边界：

- 当前阶段不实现 profile 编辑和删除。
- 当前阶段不做跨分支自动选择 profile，CI 需要显式传入 profile id。
