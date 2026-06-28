# LocustHub 阶段 2 基础设施适配

## 1. 阶段目标

阶段 2 将阶段 1 的本地模拟能力升级为可部署基础设施适配：

- 保留 SQLite + local artifact 的本地开发模式。
- 增加 MySQL 8 元数据和中低频指标存储。
- 增加阿里云 OSS ArtifactRepository。
- 增加 Dockerfile、docker-compose 和 Helm 基础配置。
- 增加 MySQL schema migration 脚本。

## 2. 本地开发模式

默认不需要外部依赖：

```bash
./scripts/run_local.sh
```

默认配置：

```text
DATABASE_BACKEND=sqlite
ARTIFACT_STORAGE_PROVIDER=local
```

## 3. MySQL 模式

复制环境变量模板：

```bash
cp .env.example .env
```

关键配置：

```text
DATABASE_BACKEND=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=locusthub
MYSQL_PASSWORD=locusthub
MYSQL_DATABASE=locusthub
```

执行 schema：

```bash
python scripts/migrate_mysql.py
```

或使用应用启动时的自动 schema 初始化。

## 4. 阿里云 OSS 模式

关键配置：

```text
ARTIFACT_STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ENDPOINT=https://oss-cn-xxx.aliyuncs.com
ALIYUN_OSS_BUCKET=your-bucket
ALIYUN_OSS_ACCESS_KEY_ID=your-access-key-id
ALIYUN_OSS_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_OSS_SIGNED_URL_EXPIRE_SECONDS=900
```

生产建议：

- OSS bucket 使用私有读写。
- 下载和预览通过 FastAPI 鉴权后生成签名 URL。
- 后续接入 RAM Role 或 STS，减少长期 AccessKey 暴露。

## 5. Docker Compose

启动 MySQL 和 API：

```bash
docker compose up --build
```

服务：

```text
API: http://127.0.0.1:8000
MySQL: 127.0.0.1:3306
```

## 6. Helm

Helm 基础包位于：

```text
deploy/helm/locusthub
```

渲染检查：

```bash
helm template locusthub deploy/helm/locusthub
```

## 7. 验收边界

阶段 2 完成后：

- 本地模式仍可运行和测试。
- 配置层支持 MySQL 和 OSS。
- MySQL DDL 覆盖 MVP 所需表结构。
- Docker Compose 可作为一体化本地部署入口。
- Helm 提供 Kubernetes 部署基础。

阶段 2 不包含：

- 真实 Kubernetes Locust 泳道执行。
- 真实 Locust master/worker 采集。
- Vben Admin 正式后台。
