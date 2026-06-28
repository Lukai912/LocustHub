# Superpowers + OpenSpec 协同开发规范

## 1. 目标

LocustHub 使用 Superpowers + OpenSpec 进行协同开发：

- Superpowers 定义人和 AI 在项目中的协作方式、职责边界和交付习惯。
- OpenSpec 定义需求、设计、实现、验收之间的规格驱动流程。

核心原则：

```text
先规格，后实现。
先讨论变更，再修改代码。
每个重要能力都要有可追踪的 spec、tasks 和验收标准。
```

## 2. Superpowers 协作角色

### 2.1 Product Superpower

负责明确产品目标和业务边界：

- 多租户压测 PaaS 的业务目标。
- 租户、项目、压测计划、压测任务的使用流程。
- 管理后台页面和用户体验。
- CI 性能基线的使用场景。
- 第一阶段和后续阶段的取舍。

输出物：

- 需求描述
- 用户故事
- 验收标准
- 页面草图或页面说明

### 2.2 Architecture Superpower

负责系统架构和技术边界：

- FastAPI 控制面。
- Vben Admin 管理后台。
- Locust master/worker 运行面。
- 多租户临时压测泳道。
- MySQL 元数据和指标存储。
- 阿里云 OSS 文件归档。
- Kubernetes NetworkPolicy、ResourceQuota、ServiceAccount。

输出物：

- 架构 spec
- 数据模型
- API 契约
- 安全策略
- 组件边界

### 2.3 Backend Superpower

负责服务端实现：

- FastAPI API。
- SQLAlchemy 模型和 Alembic migration。
- MySQL Repository。
- Run Admission Controller。
- Lane Controller。
- Metrics Collector。
- ArtifactRepository。
- CI API。

输出物：

- 后端代码
- 单元测试
- API 文档
- 数据库 migration

### 2.4 Frontend Superpower

负责 Vben Admin 管理后台：

- 租户管理。
- 项目管理。
- 脚本管理。
- 压测计划。
- 压测任务详情。
- Locust UI 风格 Statistics、Charts、Failures、Exceptions、Workers、Logs、Download。
- CI 基线页面。

输出物：

- Vben 页面
- API 类型定义
- 组件拆分
- 交互状态

### 2.5 DevOps Superpower

负责运行和交付：

- Kubernetes manifest。
- Helm 或 Kustomize。
- Locust master/worker 镜像。
- NetworkPolicy。
- ResourceQuota。
- 阿里云 OSS 配置。
- CI/CD。

输出物：

- 部署清单
- 环境变量说明
- 运维手册
- CI pipeline

### 2.6 QA Superpower

负责验证和质量：

- API 测试。
- 多租户隔离测试。
- 准入审批测试。
- 指标采集测试。
- 报告归档测试。
- CI 基线判定测试。

输出物：

- 测试用例
- 验收报告
- 回归清单

## 3. OpenSpec 目录

```text
openspec/
  project.md
  specs/
    loadtest-paas/
      spec.md
  changes/
    README.md
```

说明：

- `openspec/project.md` 保存项目长期上下文、技术约束和开发原则。
- `openspec/specs/*/spec.md` 保存已经接受的能力规格。
- `openspec/changes/*` 保存待评审或正在实现的变更。

## 4. 变更流程

重要功能必须走 OpenSpec 变更流程。

```text
需求提出
  -> 新建 openspec/changes/{change-id}
  -> 编写 proposal.md
  -> 编写 tasks.md
  -> 必要时编写 design.md
  -> 评审通过
  -> 实现代码
  -> 更新测试
  -> 验收
  -> 合并到 specs
```

### 4.1 Change ID 命名

使用动词开头：

```text
add-ci-baseline
add-oss-artifact-repository
add-locust-metrics-collector
change-lane-namespace-strategy
```

### 4.2 proposal.md

```markdown
# Proposal

## Why

说明为什么需要这个变更。

## What Changes

- 变更点 1
- 变更点 2

## Impact

- API 影响
- 数据库影响
- 前端影响
- 部署影响
```

### 4.3 tasks.md

```markdown
# Tasks

- [ ] 更新数据模型
- [ ] 实现后端 API
- [ ] 实现前端页面
- [ ] 增加测试
- [ ] 更新文档
```

### 4.4 design.md

复杂变更需要 `design.md`，例如：

- Kubernetes 压测泳道创建逻辑。
- Run Admission Controller。
- Locust 实时指标采集。
- 阿里云 OSS 归档。
- CI 性能基线比较。

## 5. Spec 写法

OpenSpec 中的 capability spec 使用 `MUST`、`SHOULD`、`MAY` 表达约束强度。

示例：

```markdown
## Requirement: TestRun creates an isolated Locust lane

The system MUST create an isolated Locust lane for each running TestRun.

### Scenario: Start a normal load test

- GIVEN an approved target whitelist
- AND tenant quota is sufficient
- WHEN a user starts a TestRun
- THEN the system creates one Locust master and N Locust workers
- AND the task status becomes RUNNING
```

## 6. 开发约定

- 不直接实现未经确认的大功能，先补 OpenSpec change。
- 小修复可以直接提交，但需要在 PR 描述里说明原因和验证方式。
- 数据模型变更必须包含 migration。
- 对外 API 变更必须更新接口文档或 spec。
- 前端页面必须能对应到具体用户流程。
- 与 Locust UI 对齐的字段不能随意改名，存储层可做映射。
- 文件归档只能依赖 `ArtifactRepository` 抽象。
- 指标存储只能依赖 `MetricsRepository` 抽象。
- 从 MVP bootstrap 之后，模块增强 PR 必须包含真实内容变更，例如代码、测试、文档、配置或 migration。
- 不再使用空提交 PR 作为模块交付追踪；如果只是记录状态，应更新交付报告或 OpenSpec 文档。

## 7. PR 检查清单

```text
- 是否有关联 OpenSpec change？
- 是否包含该模块的真实文件变更？
- 是否更新了 docs 或 openspec？
- 是否包含测试或验证说明？
- 是否影响数据库 migration？
- 是否影响部署配置？
- 是否影响租户隔离、安全准入或配额？
- 是否影响 Locust UI 字段兼容？
- 是否影响 OSS 归档和下载？
```

## 8. 第一批建议变更

```text
add-fastapi-backend-skeleton
add-vben-admin-skeleton
add-mysql-domain-models
add-artifact-repository-oss
add-locust-lane-controller
add-run-admission-controller
add-locust-metrics-collector
add-ci-baseline-api
```
