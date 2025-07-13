# 安全说明

## ⚠️ 重要安全提醒

### 🔒 敏感数据保护

本项目严格保护用户隐私和数据安全。所有文档、示例和测试代码均使用虚构数据：

#### ✅ 安全的示例数据格式
```
账号----密码----密钥----日期
demo_user_001----P@ssw0rd123----ABCD1234EFGH5678----2025-01-15
example_account----SecretPass456----JBSWY3DPEHPK3PXP----2025-02-20
```

#### ❌ 禁止在代码中包含
- 真实的GitHub账号信息
- 真实的密码
- 真实的TOTP密钥
- 真实的个人信息

### 🛡️ 数据安全措施

1. **加密存储**
   - 所有密码使用bcrypt哈希
   - 敏感数据使用AES-256-GCM加密
   - TOTP密钥加密保存

2. **访问控制**
   - 用户只能访问自己的数据
   - 完整的会话管理
   - API认证保护

3. **安全配置**
   - 强制HTTPS（生产环境）
   - 安全头设置
   - CORS白名单
   - 速率限制

### 🔐 生产环境安全checklist

- [ ] 修改默认SESSION_SECRET
- [ ] 修改默认ENCRYPTION_KEY  
- [ ] 启用HTTPS
- [ ] 配置防火墙
- [ ] 设置CORS白名单
- [ ] 定期备份数据库
- [ ] 监控异常访问
- [ ] 更新依赖包

### 📋 安全最佳实践

1. **环境变量**
   ```bash
   # 生成安全密钥
   openssl rand -hex 32  # ENCRYPTION_KEY
   openssl rand -hex 64  # SESSION_SECRET
   ```

2. **权限控制**
   ```bash
   # 设置文件权限
   chmod 600 .env
   chmod 700 data/
   ```

3. **网络安全**
   - 使用反向代理
   - 配置SSL/TLS
   - 限制直接数据库访问

### 🚨 安全事件报告

如发现安全漏洞，请：
1. 不要公开披露
2. 立即联系项目维护者
3. 提供详细的漏洞信息
4. 等待修复后再公开

### 📚 相关资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Node.js Security Checklist](https://blog.risingstack.com/node-js-security-checklist/)
- [Docker Security Best Practices](https://snyk.io/blog/10-docker-image-security-best-practices/)

---

**记住：安全是每个人的责任！**