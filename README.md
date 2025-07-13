# GitHub账号管理系统

一个专业的GitHub账号管理系统，支持安全存储多个GitHub账号信息并提供TOTP验证码生成功能。

## ✨ 功能特性

- 🔐 **安全的用户认证系统** - 支持用户注册和登录
- 📝 **GitHub账号管理** - 添加、编辑、删除GitHub账号信息
- 🔑 **TOTP验证码生成** - 基于存储的密钥实时生成两步验证码
- 💾 **数据安全存储** - 密码和密钥采用强加密算法存储
- 📊 **批量管理** - 支持批量查看所有账号的TOTP验证码
- 📁 **数据导出** - 按指定格式导出账号信息
- 🎨 **现代化界面** - 响应式Web界面，支持移动设备

## 🚀 快速开始

### 环境要求

- Node.js 16.0 或更高版本
- npm 或 yarn

### 安装依赖

```bash
npm install
```

### 构建项目

```bash
npm run build
```

### 启动服务

```bash
# 开发模式
npm run dev

# 生产模式
npm start
```

### 访问应用

打开浏览器访问: http://localhost:3000

## 📋 使用说明

### 1. 用户注册/登录

首次使用需要注册账号，后续可直接登录。

### 2. 添加GitHub账号

使用以下格式添加GitHub账号：
- **用户名**: GitHub账号用户名
- **密码**: GitHub账号密码
- **TOTP密钥**: 16位TOTP密钥(如: E4GKGXAPVRYD6T4O)
- **创建日期**: 账号创建日期(YYYY-MM-DD格式)

### 3. 管理账号

- **查看列表**: 显示所有添加的GitHub账号
- **获取TOTP**: 点击"获取TOTP"按钮获取验证码
- **批量显示**: 点击"显示/隐藏TOTP"查看所有账号的验证码
- **导出数据**: 按格式导出所有账号信息

### 4. 支持的数据格式

系统支持以下格式的账号信息:
```
账号----密码----密钥----日期
demo_user_001----P@ssw0rd123----ABCD1234EFGH5678----2025-01-15
example_account----SecretPass456----WXYZ9876QRST4321----2025-02-20
```

## 🔧 API接口

### 认证接口

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/status` - 检查登录状态

### GitHub账号管理

- `GET /api/github/accounts` - 获取账号列表
- `POST /api/github/accounts` - 添加新账号
- `PUT /api/github/accounts/:id` - 更新账号信息
- `DELETE /api/github/accounts/:id` - 删除账号

### TOTP相关

- `GET /api/github/accounts/:id/totp` - 获取单个账号的TOTP
- `GET /api/github/totp/all` - 获取所有账号的TOTP
- `GET /api/github/export` - 导出账号信息

## 🛡️ 安全特性

- **密码加密**: 使用bcrypt进行密码哈希
- **数据加密**: 敏感信息使用AES-256-GCM加密
- **会话管理**: 安全的会话管理机制
- **输入验证**: 严格的输入验证和清理
- **CSRF保护**: 内置CSRF保护机制
- **速率限制**: API请求速率限制

## 📁 项目结构

```
src/
├── models/          # 数据模型
│   └── database.ts  # 数据库操作
├── routes/          # 路由处理
│   ├── auth.ts      # 认证路由
│   └── github.ts    # GitHub管理路由
├── middleware/      # 中间件
│   └── auth.ts      # 认证中间件
├── utils/           # 工具类
│   ├── totp.ts      # TOTP生成器
│   └── crypto.ts    # 加密工具
├── types/           # 类型定义
│   └── index.ts     # 接口定义
└── server.ts        # 主服务器文件

public/
├── css/             # 样式文件
├── js/              # 前端脚本
└── index.html       # 主页面

data/                # 数据库文件目录
```

## 🧪 测试

运行系统测试:

```bash
node test-system.js
```

测试包括:
- TOTP功能测试
- 加密功能测试
- 数据库功能测试
- 格式解析测试

## 🔗 相关链接

- [TOTP生成器参考](https://github.com/jaden/totp-generator)
- [Speakeasy库文档](https://github.com/speakeasyjs/speakeasy)

## 📝 开发说明

### 技术栈

- **后端**: Node.js + TypeScript + Express
- **数据库**: SQLite3
- **加密**: bcrypt + crypto
- **TOTP**: speakeasy
- **前端**: 原生HTML/CSS/JavaScript

### 开发命令

```bash
npm run dev      # 开发模式
npm run build    # 构建项目
npm start        # 生产模式
npm test         # 运行测试
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交问题和改进建议！

---

**⚠️ 安全提醒**: 
- 请务必更改生产环境中的默认密钥
- 定期备份数据库文件
- 不要在公共网络中暴露管理界面