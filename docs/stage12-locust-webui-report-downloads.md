# LocustHub 阶段 12 Locust WebUI 与报告下载增强

## 1. 阶段目标

阶段 12 将压测运行详情从基础表格升级为更接近 Locust WebUI 的可用状态：

- Statistics 保留 Locust 字段维度。
- Charts 展示 Users、RPS、Failures/s、Response Times 趋势。
- Failures 和 Logs 展示失败、异常、master log 预览。
- Download Data 提供 HTML report、requests CSV、failures CSV、exceptions CSV、history CSV、master log 下载。
- 报告 artifact 继续支持本地文件系统和阿里云 OSS。

## 2. 后端能力

`GET /api/v1/test-runs/{run_id}/locust/stats` 增加：

- `history`：按采样时间返回用户数、RPS、Failures/s、P50、P95、平均响应时间、失败率。
- `errors`：返回最新采样失败/异常行。

`GET /api/v1/test-runs/{run_id}/report` 增加：

- `artifacts`：归档文件列表，包含名称、类型、大小、checksum、下载 URL。
- `log_preview`：master log 预览，便于页面直接排障。

`GET /api/v1/artifacts/{artifact_id}/download`：

- 下载归档 HTML、CSV 和日志。
- 下载前检查 artifact 所属租户，避免跨租户访问。
- 本地存储返回 `FileResponse`，OSS 存储返回签名 URL 重定向。

## 3. 报告归档

停止任务时会持久化：

- `report.html`
- `requests.csv`
- `failures.csv`
- `exceptions.csv`
- `history.csv`
- `master.log`

真实 Locust master 可用时优先抓取原生报告和 CSV。若 exceptions CSV 在当前 Locust
版本不可用，会生成空 CSV，不阻塞整份报告归档。

## 4. 前端能力

Test Runs 的 Locust Detail tabs：

- `Statistics`
- `Charts`
- `Failures`
- `Workers`
- `Logs`
- `Download Data`

图表使用轻量 SVG polyline 实现，不引入额外依赖。缩放逻辑在代码中有注释，避免后续维护者误判坐标反转和比例计算。

## 5. 验收

```bash
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage12_reports_webui.py -q
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage12-full.db ARTIFACT_ROOT=/private/tmp/locusthub-stage12-artifacts PYTHONPATH=. ../.venv/bin/pytest -q
node frontend/tests/structure.test.mjs
cd frontend && npm run build
```

验收点：

- report summary 返回所有下载 artifact。
- artifact 下载接口受租户权限保护。
- Locust stats 返回 history 和 errors。
- 前端包含 Charts、Logs、Download Data 和报告下载入口。
