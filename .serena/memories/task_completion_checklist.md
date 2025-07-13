# 任务完成检查清单

## 代码质量检查
1. **TypeScript编译检查**
   ```bash
   npm run build
   # 或者仅检查类型
   npx tsc --noEmit
   ```

2. **运行测试**
   ```bash
   npm test
   ```

3. **代码风格检查** (如果配置了linter)
   ```bash
   # 通常是
   npm run lint
   # 或
   npx eslint src/
   ```

## 功能验证
1. **启动开发服务器**
   ```bash
   npm run dev
   ```

2. **验证功能**
   - 测试所有API端点
   - 验证数据库操作
   - 检查TOTP生成功能
   - 确认用户认证流程

3. **安全检查**
   - 确认密码加密
   - 验证会话管理
   - 检查输入验证
   - 确认CORS设置

## 部署前检查
1. **构建生产版本**
   ```bash
   npm run build
   npm start
   ```

2. **数据库迁移** (如有需要)
   - 检查数据库模式
   - 验证数据完整性

3. **环境配置**
   - 确认环境变量设置
   - 检查配置文件

## 文档更新
- 更新README.md (如有重大变更)
- 更新API文档
- 记录配置变更