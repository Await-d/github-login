# 前端页面无法加载 - 诊断和解决方案

## 问题现状
- 服务器日志显示正常启动：`✅ 找到前端构建文件: /app/frontend/build`
- 但访问 http://localhost:10202 无法加载页面
- 端口10202和8000都没有在监听

## 可能的原因

### 1. Docker容器未正确启动
**检查命令：**
```bash
sudo docker ps
sudo docker-compose ps
```

**解决方案：**
```bash
# 停止现有容器
sudo docker-compose down

# 重新构建并启动
sudo docker-compose up --build -d

# 查看日志
sudo docker-compose logs -f
```

### 2. 端口映射问题
**当前配置：** `10202:8000`

**检查方法：**
```bash
# 检查容器端口映射
sudo docker port github-manager-python

# 检查宿主机端口占用
sudo netstat -tulnp | grep :10202
sudo netstat -tulnp | grep :8000
```

### 3. 防火墙或网络问题
**检查防火墙：**
```bash
sudo ufw status
sudo iptables -L
```

### 4. 容器内部服务问题
**进入容器调试：**
```bash
# 进入容器
sudo docker exec -it github-manager-python bash

# 在容器内测试
curl http://localhost:8000/api/health
curl http://localhost:8000/
ls -la /app/frontend/build/
```

## 快速修复步骤

### 步骤1：重启Docker服务
```bash
sudo docker-compose down
sudo docker-compose up --build -d
```

### 步骤2：检查容器状态
```bash
sudo docker-compose ps
sudo docker-compose logs github-manager
```

### 步骤3：测试端口连接
```bash
curl http://localhost:10202/api/health
curl http://localhost:10202/
```

### 步骤4：如果仍有问题，使用本地开发模式
```bash
# 后端
cd backend
source ../venv/bin/activate
python app/main.py

# 前端（另一个终端）
cd frontend
npm start

# 访问 http://localhost:3000
```

## 备用方案：修改端口配置

如果10202端口有冲突，可以修改为其他端口：

```yaml
# docker-compose.yml
ports:
  - "3000:8000"  # 或其他可用端口
```

## 前端静态文件检查

确保前端构建文件正确：
```bash
ls -la frontend/build/
cat frontend/build/index.html
```

## 日志分析

关键日志信息：
- ✅ `找到前端构建文件: /app/frontend/build` - 前端文件OK
- ✅ `Uvicorn running on http://0.0.0.0:8000` - 服务器启动OK
- ❌ 端口不可访问 - 网络/映射问题