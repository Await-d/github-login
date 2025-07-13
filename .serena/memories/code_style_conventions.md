# 代码风格和约定

## TypeScript约定
- 使用严格模式 (strict: true)
- 使用ES2020目标版本
- 强制类型检查
- 使用接口定义数据结构
- 导出类型定义

## 命名约定
- **文件名**: kebab-case (例如: github-manager.ts)
- **类名**: PascalCase (例如: GitHubAccount)
- **函数/变量**: camelCase (例如: generateTotp)
- **常量**: UPPER_SNAKE_CASE (例如: DATABASE_PATH)
- **接口**: PascalCase with I前缀 (例如: IGitHubAccount)

## 文件组织
```
src/
  ├── types/           # 类型定义 (.d.ts文件)
  ├── models/          # 数据模型和数据库操作
  ├── routes/          # Express路由处理器
  ├── middleware/      # Express中间件
  ├── utils/           # 工具函数
  └── server.ts        # 主服务器文件
```

## 代码风格
- 使用2空格缩进
- 使用单引号字符串
- 语句末尾使用分号
- 导入语句按字母顺序排列
- 函数和类使用JSDoc注释

## 安全约定
- 密码必须加密存储
- 使用环境变量存储敏感配置
- 输入验证和清理
- CORS配置
- 会话安全设置