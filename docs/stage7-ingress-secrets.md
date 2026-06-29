# LocustHub 阶段 7 Ingress/TLS 与 Secret-ready Helm

## 1. 阶段目标

阶段 7 将 Helm 部署入口推进到更接近生产使用的形态：

- 通过 Ingress 暴露统一访问入口。
- `/api` 路由到 FastAPI 服务，`/` 路由到管理后台服务。
- TLS 通过 `ingress.tls.secretName` 配置。
- MySQL 密码、OSS AK/SK、`DEMO_TOKEN` 通过 Kubernetes Secret 注入。

## 2. Ingress 配置

默认 values：

```yaml
ingress:
  enabled: true
  className: nginx
  host: locusthub.example.com
  tls:
    enabled: true
    secretName: locusthub-tls
```

部署前需要将 `host` 和 `secretName` 替换为真实域名与 TLS Secret。

## 3. Secret 配置

默认 chart 会创建一个 demo Secret：

```yaml
secret:
  create: true
  existingSecret: ""
  stringData:
    MYSQL_PASSWORD: locusthub
    ALIYUN_OSS_ACCESS_KEY_ID: ""
    ALIYUN_OSS_ACCESS_KEY_SECRET: ""
    DEMO_TOKEN: dev-token
```

生产环境推荐关闭 demo Secret，并引用外部 Secret：

```yaml
secret:
  create: false
  existingSecret: locusthub-runtime-secrets
```

`locusthub-runtime-secrets` 需要包含：

- `MYSQL_PASSWORD`
- `ALIYUN_OSS_ACCESS_KEY_ID`
- `ALIYUN_OSS_ACCESS_KEY_SECRET`
- `DEMO_TOKEN`

## 4. 验证

```bash
cd backend
PYTHONPATH=. ../.venv/bin/pytest tests/test_stage7_ingress_secrets.py -q
cd ..
python3 scripts/verify_deployment_package.py
```

## 5. 已知边界

- 本阶段不绑定具体 Ingress Controller，也不创建证书签发资源。
- `DEMO_TOKEN` 仍是 MVP 认证方式，后续阶段会替换为正式用户会话和租户权限模型。
- 如果接入 ExternalSecret、SealedSecret 或云厂商 Secret Manager，只需要让
  `secret.existingSecret` 指向同步后的 Kubernetes Secret。

