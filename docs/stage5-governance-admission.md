# LocustHub 阶段 5 准入治理能力

## 1. 阶段目标

阶段 5 将基础白名单和配额校验升级为可审计的治理模块，覆盖目标审批、
DNS/IP 风险限制、资源/流量配额快照和 Swagger 可见的治理接口。

## 2. 新增能力

- 创建目标白名单时自动生成 `approval_requests`。
- 支持审批请求批准/拒绝，并同步更新目标白名单状态。
- 启动压测前记录 DNS 解析快照。
- 阻断私网、回环、链路本地、多播、保留地址。
- 启动压测前记录配额使用快照。
- Governance API 新增：
  - `GET /api/v1/approval-requests`
  - `POST /api/v1/approval-requests/{id}/resolve`
  - `GET /api/v1/dns-resolution-snapshots`
  - `GET /api/v1/quota-usage-snapshots`
- 管理后台 Governance 页面展示审批请求、DNS 快照和配额快照。

## 3. 准入顺序

```text
Tenant quota exists
Concurrent run quota
Worker quota
Total worker quota
Users / spawn rate / duration quota
Target approved
DNS/IP policy
Quota usage snapshot
Lane creation
```

未审批目标会进入 `APPROVAL_PENDING`，不会创建运行资源。

## 4. 本地 Demo 兼容

Demo 目标 `jsonplaceholder.typicode.com` 是 `approved_by=system` 的系统种子数据。
为了保持离线或 DNS 不稳定环境下的 MVP 可调试性，系统种子目标在 DNS 临时不可解析时记录
`warning` 快照而不是阻断。显式私网或保留 IP 仍然会被阻断。

## 5. 验证

```bash
cd backend && rm -rf data artifacts && PYTHONPATH=. ../.venv/bin/pytest -q
node frontend/tests/structure.test.mjs
cd frontend && npm run build
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py
```

## 6. 后续边界

- 尚未实现超额审批自动转人工审批。
- NetworkPolicy 仍是基础 default deny + DNS + run 内部通信，后续阶段继续收紧到目标 IP/CIDR。
- DNS 快照当前在 admission 阶段同步执行，后续可改成异步解析和定期复核。
