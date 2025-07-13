# 建议的命令

## 开发命令
```bash
# 安装依赖
npm install

# 开发模式运行
npm run dev

# 构建项目
npm run build

# 生产模式运行
npm start

# 运行测试
npm test
```

## 系统命令
```bash
# 文件系统
ls -la          # 列出文件详情
cd <directory>  # 切换目录
find . -name "*.ts"  # 查找TypeScript文件
grep -r "pattern" .  # 递归搜索文本

# Git命令
git status      # 查看状态
git add .       # 添加所有文件
git commit -m "message"  # 提交更改
git log --oneline  # 查看提交历史

# 进程管理
ps aux          # 查看运行进程
kill <pid>      # 终止进程
netstat -tlnp   # 查看端口占用
```

## 数据库管理
```bash
# SQLite命令行
sqlite3 database.db
.tables         # 显示表
.schema         # 显示表结构
.quit           # 退出
```

## 开发调试
```bash
# TypeScript编译检查
npx tsc --noEmit

# 查看Node.js进程
ps aux | grep node

# 查看端口占用
lsof -i :3000
```