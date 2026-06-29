# LocustHub 阶段 9 CI 性能基线流水线

## 1. 阶段目标

阶段 9 将已有 CI baseline API 扩展为可直接接入流水线的能力：

- `POST /api/v1/ci/performance-runs` 支持请求级阈值。
- `GET /api/v1/ci/performance-runs/{test_run_id}/result` 查询持久化结论。
- `scripts/run_ci_baseline.py` 可在 CI 中调用 API、保存 JSON 结果并用退出码表达 pass/fail。

## 2. API 阈值

请求体新增：

```json
{
  "max_p95_ms": 500,
  "max_fail_ratio": 0.05,
  "min_total_rps": 10
}
```

判断规则：

- `current_p95 <= max_p95_ms`
- `fail_ratio <= max_fail_ratio`
- 如果设置 `min_total_rps`，则 `total_rps >= min_total_rps`

违反阈值会写入 `baseline_runs.violations_json`，并让 `conclusion` 为 `failed`。

## 3. CI 脚本

```bash
scripts/run_ci_baseline.py \
  --api-base-url https://locusthub.example.com/api/v1 \
  --token "$LOCUSTHUB_TOKEN" \
  --tenant-id tenant-demo \
  --project-id project-demo \
  --test-plan-id plan-demo \
  --ci-provider github-actions \
  --pipeline-id "$GITHUB_RUN_ID" \
  --job-id perf-baseline \
  --commit-sha "$GITHUB_SHA" \
  --branch "$GITHUB_REF_NAME" \
  --max-p95-ms 500 \
  --max-fail-ratio 0.05 \
  --min-total-rps 10 \
  --output artifacts/locusthub-baseline.json
```

脚本退出码：

- `0`: baseline `conclusion` 不是 `failed`
- `1`: baseline `conclusion` 为 `failed`

## 4. GitHub Actions 示例

```yaml
- name: Run LocustHub baseline
  run: |
    scripts/run_ci_baseline.py \
      --api-base-url "$LOCUSTHUB_API_BASE_URL" \
      --token "$LOCUSTHUB_TOKEN" \
      --tenant-id "$LOCUSTHUB_TENANT_ID" \
      --project-id "$LOCUSTHUB_PROJECT_ID" \
      --test-plan-id "$LOCUSTHUB_TEST_PLAN_ID" \
      --ci-provider github-actions \
      --pipeline-id "$GITHUB_RUN_ID" \
      --job-id perf-baseline \
      --commit-sha "$GITHUB_SHA" \
      --branch "$GITHUB_REF_NAME" \
      --output locusthub-baseline.json
```

## 5. 已知边界

- 本阶段不新增完整 baseline profile 管理 API，阈值由 CI 请求传入。
- CI 脚本使用同步 API 调用，后续可扩展为异步轮询长任务。
- 结果 JSON 由 CI 系统归档，LocustHub 仍负责保存 baseline run 和压测报告 artifact。

