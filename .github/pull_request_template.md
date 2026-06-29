## 变更范围

- 阶段 / 模块：
- 关联需求 / OpenSpec：
- 本 PR 是否包含真实内容变更：

## 变更说明

- 

## API / Swagger 注释检查

- [ ] 新增或修改的 FastAPI 接口已设置 `tags`
- [ ] 新增或修改的 FastAPI 接口已设置 `summary`
- [ ] 关键接口已补充 `description` 或函数 docstring
- [ ] 请求 / 响应模型字段含义清晰，必要时已补充字段说明
- [ ] 本地可通过 `/docs` 查看 Swagger UI

## 代码注释检查

- [ ] 复杂业务规则已补充“为什么这样做”的注释
- [ ] 适配器边界已补充注释，例如 MySQL、OSS、Kubernetes、Locust API
- [ ] 降级 / fallback 行为已补充注释
- [ ] 安全相关逻辑已补充注释，例如白名单、审批、NetworkPolicy、配额
- [ ] 没有添加解释显而易见代码的噪音注释

## 多租户与安全检查

- [ ] 租户隔离字段已保留或校验
- [ ] 目标白名单 / 审批 / 配额逻辑未被绕过
- [ ] Kubernetes namespace / service account / NetworkPolicy 变更已说明
- [ ] 未提交密钥、token、云账号凭证或本地私有配置

## 数据与归档检查

- [ ] 操作数据仍可持久化
- [ ] 压测指标仍可实时采集或查询
- [ ] 压测报告仍可归档
- [ ] OSS / 本地 artifact 行为保持兼容
- [ ] 如涉及 schema 变更，已补充迁移脚本或说明

## 验证方式

请粘贴实际执行结果，不要只写“已测试”。

```text
# 示例
cd backend && rm -rf data artifacts && PYTHONPATH=. ../.venv/bin/pytest -q
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py
```

## 验收结论

- [ ] 本 PR 满足当前阶段目标
- [ ] 文档 / 验收报告已更新
- [ ] 已知限制已写明
