# GitHub账号管理系统 v2.0

安全的GitHub账号管理和TOTP验证码生成系统，采用 **Python FastAPI + React + Ant Design** 技术栈。

## ✨ 功能特性

- 🔐 用户注册和JWT认证
- 📝 GitHub账号CRUD管理
- 🔑 TOTP验证码生成（基于PyOTP）
- 🛡️ 密码和密钥AES加密存储
- 📱 响应式前端界面（Ant Design）
- 🐳 Docker容器化部署
- 💾 SQLite数据库（生产可换PostgreSQL）

## 🏗️ 技术栈

### 后端
- **FastAPI** - 高性能Python Web框架
- **SQLAlchemy** - ORM数据库操作
- **PyOTP** - TOTP验证码生成
- **JWT** - 用户认证
- **Cryptography** - AES数据加密

### 前端
- **React 18** - 用户界面框架
- **Ant Design** - UI组件库
- **TypeScript** - 类型安全
- **Axios** - HTTP客户端

## 📁 项目结构

```
github-login/
├── backend/                 # Python后端
│   ├── app/
│   │   └── main.py         # FastAPI应用入口
│   ├── models/
│   │   ├── database.py     # 数据库模型
│   │   └── schemas.py      # Pydantic模式
│   ├── routes/
│   │   ├── auth.py         # 认证路由
│   │   └── github.py       # GitHub管理路由
│   └── utils/
│       ├── auth.py         # JWT工具
│       ├── encryption.py   # 加密工具
│       └── totp.py         # TOTP工具
├── frontend/               # React前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── pages/          # 页面
│   │   ├── hooks/          # 自定义Hooks
│   │   └── services/       # API服务
│   └── package.json
├── backup-typescript/      # 原TypeScript版本备份
├── requirements.txt        # Python依赖
├── Dockerfile             # 多阶段构建
├── docker-compose.yml     # 容器编排
└── README.md
```

## 🚀 快速开始

### 本地开发

1. **后端开发**
```bash
# 安装Python依赖
pip install -r requirements.txt

# 启动后端服务
cd backend
python app/main.py
# 后端将运行在 http://localhost:8000
```

2. **前端开发**
```bash
# 安装Node依赖
cd frontend
npm install

# 启动前端服务
npm start
# 前端将运行在 http://localhost:3000
```

### Docker部署

```bash
# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止容器
docker-compose down
```

应用将在 http://localhost:8000 运行，包含前后端。

## 📋 API文档

启动后端服务后，访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要接口

```
POST /api/auth/register     # 用户注册
POST /api/auth/login        # 用户登录
GET  /api/auth/me           # 获取当前用户

GET    /api/github/accounts           # 获取账号列表
POST   /api/github/accounts           # 创建账号
GET    /api/github/accounts/{id}      # 获取账号详情
PUT    /api/github/accounts/{id}      # 更新账号
DELETE /api/github/accounts/{id}      # 删除账号

GET /api/github/accounts/{id}/totp    # 获取TOTP验证码
GET /api/github/totp/batch            # 批量获取TOTP
```

## 🔒 安全特性

- **密码哈希**: 使用bcrypt安全哈希
- **数据加密**: GitHub密码和TOTP密钥AES加密存储
- **JWT认证**: 安全的用户会话管理
- **CORS配置**: 跨域请求保护
- **输入验证**: Pydantic数据验证

## 📊 数据格式

GitHub账号数据格式：
```
账号----密码----密钥----日期
```

示例（假数据）：
```
testuser----testpass123----ABCDEFGHIJKLMNOP----2025-07-13
```

## 🔧 环境变量

```bash
# 后端配置
PORT=8000
DATABASE_URL=sqlite:///./github_manager.db
ENCRYPTION_KEY=your-32-char-encryption-key
SECRET_KEY=your-jwt-secret-key

# 前端代理（开发模式）
REACT_APP_API_URL=http://localhost:8000
```

## 🐛 故障排除

1. **Docker构建失败**
   - 确保Docker和docker-compose已安装
   - 检查端口8000是否被占用

2. **前端无法连接后端**
   - 检查proxy配置在frontend/package.json
   - 确认后端在8000端口运行

3. **数据库权限错误**
   - 检查./data目录权限
   - 容器会自动创建fallback路径

## 📝 更新日志

### v2.0.0 (2025-07-13)
- 🔄 **技术栈升级**: TypeScript/Node.js → Python/React
- ⚡ **性能优化**: FastAPI高性能异步框架
- 🎨 **UI重构**: 全新Ant Design界面
- 🔐 **安全增强**: 改进的加密和认证机制
- 🐳 **容器化**: 多阶段Docker构建优化

### v1.0.0 (备份版本)
- 原TypeScript/Node.js实现已备份到 `backup-typescript/`

## 📞 支持

如有问题，请检查：
1. 日志输出：`docker-compose logs -f`
2. 健康检查：`curl http://localhost:8000/api/health`
3. API文档：http://localhost:8000/docs