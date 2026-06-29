# LocustHub 阶段 4 Vben 风格管理后台

## 1. 阶段目标

阶段 4 将早期单文件调试页升级为可构建、可扩展的 Vue 3 管理后台工程。

本阶段选择轻量 Vben 风格实现，而不是直接复制完整 `vue-vben-admin`
monorepo。这样可以先完成 LocustHub 的业务控制台闭环，同时保留后续迁移到
完整 Vben 生态的空间。

## 2. 新增能力

- Vue 3 + Vite + TypeScript 前端工程。
- Vben 风格布局：侧边栏、顶部栏、模块化内容区、密集表格。
- API client：统一调用 FastAPI `/api/v1`。
- 管理模块：
  - Dashboard
  - Tenants
  - Projects
  - Scripts
  - Test Plans
  - Test Runs
  - Governance
  - Reports
- Test Runs 页面支持创建 Demo run、采集、停止、查看实时 Locust stats。
- Locust Detail 保留 Locust UI 风格 tabs：
  - Statistics
  - Failures
  - Workers
  - Download

## 3. 本地运行

```bash
cd frontend
npm install --registry=https://registry.npmjs.org/
npm run dev
```

默认连接：

```text
Frontend: http://127.0.0.1:5173
Backend:  http://127.0.0.1:8000/api/v1
```

可通过环境变量覆盖：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_DEMO_TOKEN=dev-token
```

## 4. 验证

```bash
node frontend/tests/structure.test.mjs
cd frontend && npm run build
cd backend && rm -rf data artifacts && PYTHONPATH=. ../.venv/bin/pytest -q
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py
```

## 5. 已知边界

- 该阶段未引入完整 `vue-vben-admin` monorepo。
- 认证仍使用 MVP demo token，后续阶段替换为正式用户会话。
- 当前构建关闭 Vite minify；生产压缩可交给 Nginx/CDN，或在升级 Node 后再恢复。
- 尚未做 Playwright 端到端截图验证，后续 UI 深化阶段补充。
