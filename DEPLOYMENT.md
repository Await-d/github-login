# 部署指南

## 🐳 Docker 部署

### 问题修复说明

原始Dockerfile有以下问题：
1. ❌ 缺少 `package-lock.json` 文件
2. ❌ 使用过时的 `npm ci --only=production` 参数

### 修复内容
1. ✅ 添加 `package-lock.json` 到版本控制
2. ✅ 更新为 `npm ci --omit=dev` 命令
3. ✅ 创建优化版多阶段构建Dockerfile

## 🚀 快速部署

### 方式1: 基础部署
```bash
# 构建镜像
docker build -t github-manager .

# 运行容器
docker run -d \
  --name github-manager \
  -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  github-manager
```

### 方式2: Docker Compose (推荐)
```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 方式3: 优化版构建
```bash
# 使用多阶段构建减小镜像体积
docker build -f Dockerfile.optimized -t github-manager:optimized .

# 运行优化版
docker run -d \
  --name github-manager \
  -p 3000:3000 \
  -e SESSION_SECRET="your-secret-key" \
  -e ENCRYPTION_KEY="your-32-char-key" \
  -v github-data:/app/data \
  github-manager:optimized
```

## 📋 环境变量配置

创建 `.env` 文件：
```bash
cp .env.example .env
# 编辑 .env 文件，修改安全相关配置
```

**重要**: 生产环境必须修改以下变量：
- `SESSION_SECRET` - 会话密钥
- `ENCRYPTION_KEY` - 数据加密密钥

## 🔧 Drone CI/CD 部署

项目包含完整的 `.drone.yml` 配置，支持自动部署到1Panel环境。

### 部署流程
1. 代码推送到仓库
2. Drone自动触发构建
3. 构建Docker镜像
4. 创建必要目录
5. 启动容器服务

### 部署目录结构
```
/volume1/docker/1panel/apps/local/github_manager/
└── localmanager/
    ├── data/     # 数据库文件
    └── config/   # 配置文件
```

## 🏥 健康检查

访问健康检查端点：
```bash
curl http://localhost:3000/api/health
```

预期响应：
```json
{
  "success": true,
  "message": "GitHub Manager API is running",
  "timestamp": "2025-07-13T06:45:00.000Z"
}
```

## 📊 监控和日志

### 查看容器日志
```bash
docker logs github-manager

# 实时日志
docker logs -f github-manager
```

### 容器状态监控
```bash
docker stats github-manager
```

## 🔒 生产环境安全建议

1. **修改默认密钥**
   ```bash
   # 生成安全的密钥
   openssl rand -hex 32  # ENCRYPTION_KEY
   openssl rand -hex 64  # SESSION_SECRET
   ```

2. **使用HTTPS**
   - 配置反向代理 (Nginx/Traefik)
   - 申请SSL证书

3. **网络安全**
   - 使用防火墙限制端口访问
   - 配置CORS白名单

4. **数据备份**
   ```bash
   # 备份数据库
   docker exec github-manager cp /app/data/github-manager.db /tmp/
   docker cp github-manager:/tmp/github-manager.db ./backup/
   ```

## 🛠️ 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker logs github-manager
   
   # 检查端口占用
   netstat -tlnp | grep 3000
   ```

2. **数据库权限问题**
   ```bash
   # 修复数据目录权限
   sudo chown -R 1001:1001 ./data
   ```

3. **内存不足**
   ```bash
   # 增加资源限制
   docker update --memory=512m github-manager
   ```

## 📈 性能优化

1. **镜像优化**
   - 使用 `Dockerfile.optimized` 多阶段构建
   - 清理npm缓存
   - 使用Alpine基础镜像

2. **运行时优化**
   - 设置合适的内存限制
   - 配置健康检查
   - 使用容器编排工具

## 🔄 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 滚动更新
docker-compose up -d --no-deps github-manager
```