# LocustHub 阶段 17 出网治理与 NetworkPolicy 收敛

## 1. 阶段目标

阶段 17 强化目标白名单、DNS/IP 限制和 Kubernetes NetworkPolicy 的闭环：

- 准入阶段校验目标端口必须在白名单端口内。
- DNS 解析结果继续写入 `dns_resolution_snapshots`。
- 准入通过后返回可审计的 egress policy。
- 任务 lane manifest 将解析出的目标 IP 写入 NetworkPolicy `ipBlock`。
- NetworkPolicy 只允许任务内部通信、DNS、以及审批目标 IP + 端口。

## 2. 准入规则

准入检查顺序：

1. 租户资源和流量配额。
2. 目标 host 是否在已审批白名单中。
3. 目标 port 是否在白名单 `ports` 中。
4. DNS/IP 是否解析到公网可访问地址。
5. 写入 DNS 快照和 quota usage snapshot。

如果目标端口未审批，任务进入 `APPROVAL_PENDING`，并记录拒绝原因。

## 3. NetworkPolicy

生成的 NetworkPolicy egress 包含：

- 同一 `test-run-id` pod 间通信。
- DNS UDP/TCP 53。
- 准入阶段解析出的目标 IPBlock。
- 准入阶段确认的目标 TCP 端口。

Kubernetes 原生 NetworkPolicy 不支持 FQDN，因此 LocustHub 在准入阶段解析域名，将解析结果快照化，再将 IP 写入 manifest。这样报告、审计和运行时资源能对齐同一次准入决策。

## 4. 验收

自动化测试覆盖：

- 目标端口未在白名单内时准入拒绝。
- 准入结果携带 host、port、resolved IPs、allowed ports。
- NetworkPolicy 使用解析 IP 生成 `/32` IPBlock，并限制到目标 TCP 端口。

阶段边界：

- 当前阶段使用准入时 DNS 快照，不做长时间运行中的周期性 DNS 复核。
- 如果目标域名解析结果变化，需要重启任务重新准入。
