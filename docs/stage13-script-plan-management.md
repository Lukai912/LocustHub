# LocustHub 阶段 13 脚本与计划管理增强

## 1. 阶段目标

阶段 13 将脚本和压测计划从只读列表升级为可自助维护的工作流：

- 创建 Locust 脚本版本。
- 静态校验 Locustfile。
- 创建 Test Plan。
- 复制已有 Test Plan 作为变体。
- 管理台提供对应表单入口。

## 2. API

新增或增强接口：

- `GET /api/v1/scripts`：列出当前用户可见的脚本版本。
- `POST /api/v1/scripts/validate`：静态校验 Locustfile。
- `POST /api/v1/test-plans/{plan_id}/clone`：复制已有计划。

`/scripts/validate` 使用 Python `ast` 解析源码，只检查语法、`HttpUser` 继承和
`@task` 数量，不执行租户脚本。这样可以在控制面给出快速反馈，同时避免把用户代码
加载进平台进程。

## 3. 管理台

Scripts 页面新增：

- `Validate Locustfile`
- `Create Script Version`
- 校验结果：valid/invalid、task count、错误列表

Test Plans 页面新增：

- `Create Test Plan`
- `Clone Plan`

新建脚本后会刷新脚本列表，并把新脚本 id 自动填入计划表单，方便继续创建计划。

## 4. 验收

```bash
cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage13_script_plan_management.py -q
node frontend/tests/structure.test.mjs
cd frontend && npm run build
```

验收点：

- 有效 Locustfile 返回 `valid=true`、识别 HttpUser 和 task。
- 缺少 HttpUser 的脚本返回错误。
- 计划可以复制，复制后的计划可以创建 run。
- 新建脚本可以通过 `GET /scripts` 查到。
- 前端包含脚本校验、创建脚本、创建计划、复制计划入口。
