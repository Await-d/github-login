# GitHub账号管理系统 - 部署指南

## 🚀 线上部署步骤

### 1. 环境要求
- Python 3.8+ (推荐 3.12)
- Git
- 系统依赖：gcc, libffi-dev, libssl-dev

### 2. 部署步骤

#### 步骤1: 克隆代码
```bash
git clone http://gogs.52067373.xyz/await/github-manager.git
cd github-manager
```

#### 步骤2: 安装系统依赖（Ubuntu/Debian）
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv gcc g++ libffi-dev libssl-dev
```

#### 步骤3: 创建虚拟环境
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### 步骤4: 安装Python依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 步骤5: 检查依赖
```bash
python check_dependencies.py
```

#### 步骤6: 构建前端（如需要）
```bash
cd ../frontend
npm install
npm run build
cd ../backend
```

#### 步骤7: 启动服务
```bash
# 开发环境
python app/main.py

# 生产环境
python -c "
from app.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

### 3. 环境变量配置

创建 `.env` 文件：
```bash
DATABASE_URL=/path/to/your/data
CREATE_DEFAULT_ADMIN=true
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=your_secure_password
PORT=8000
```

### 4. 使用systemd服务（推荐）

创建服务文件 `/etc/systemd/system/github-manager.service`：
```ini
[Unit]
Description=GitHub Manager Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/github-manager/backend
Environment=PATH=/path/to/github-manager/backend/venv/bin
ExecStart=/path/to/github-manager/backend/venv/bin/python app/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable github-manager
sudo systemctl start github-manager
sudo systemctl status github-manager
```

### 5. 使用Nginx反代理（可选）

Nginx配置示例：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔍 故障排除

### 依赖问题
如果遇到 `ModuleNotFoundError`：
1. 确保在虚拟环境中运行：`source venv/bin/activate`
2. 重新安装依赖：`pip install -r requirements.txt`
3. 运行依赖检查：`python check_dependencies.py`

### 端口占用
如果8000端口被占用：
```bash
# 查找占用进程
sudo netstat -tulpn | grep :8000
# 或修改端口
export PORT=8080
```

### 数据库问题
如果数据库初始化失败：
1. 检查data目录权限
2. 删除旧数据库文件重新初始化
3. 检查磁盘空间

## 📱 访问地址

部署成功后访问：
- 前端应用: http://your-server:8000/
- API文档: http://your-server:8000/docs
- 健康检查: http://your-server:8000/api/health

## 🔐 默认账号

首次部署后可以：
1. 使用创建的默认管理员账号登录
2. 或注册新账号使用
3. 建议登录后立即修改默认密码

## 📞 技术支持

如遇问题，请提供：
1. 错误日志
2. 依赖检查结果 (`python check_dependencies.py`)
3. 系统环境信息