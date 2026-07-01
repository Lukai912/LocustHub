# LocustHub 阶段 16 报告趋势与对比

## 1. 阶段目标

阶段 16 在 Stage12 报告归档下载的基础上，让报告不只是“可下载”，还可以用于日常分析：

- Reports 页面可以浏览历史归档报告。
- 后端提供报告趋势数据，支持查看 P95、RPS、失败率走势。
- 后端提供两次压测报告对比，返回关键指标 delta 和百分比变化。
- 对比接口继续执行租户隔离，避免跨租户读取报告。

## 2. 后端接口

新增接口：

- `GET /api/v1/reports`
- `GET /api/v1/reports/compare?base_run_id=...&candidate_run_id=...`

`GET /api/v1/reports` 返回：

- `items`：最新归档报告列表，包含 artifact 下载信息。
- `trend`：按归档时间正序排列的趋势点。

`GET /api/v1/reports/compare` 返回：

- `base`
- `candidate`
- `deltas`

`deltas` 覆盖：

- `total_requests`
- `total_failures`
- `avg_response_time`
- `p95_response_time`
- `p99_response_time`
- `total_rps`
- `fail_ratio`

## 3. 前端实现

Reports 页面新增：

- `Report History` 趋势卡。
- 历史报告表格。
- `Report Compare` 面板。
- `P95 Delta` 和 `Fail Ratio Delta` 快速判断入口。

当前默认比较“最新报告”和“上一份报告”，符合大多数性能回归排查流程。

## 4. 验收

自动化测试覆盖：

- 报告列表接口返回最新优先的报告列表。
- trend 按时间正序返回。
- 对比接口返回 base、candidate 和关键指标 deltas。
- 已认证但跨租户的用户无法对比其他租户报告。
- 前端结构包含 `Report History`、`Report Compare`、`P95 Delta`、`Fail Ratio Delta`。

阶段边界：

- 本阶段不实现复杂 baseline profile，对比目标由最新两份报告自动推导。
- 图表继续使用轻量 SVG sparkline，不引入额外图表库。
