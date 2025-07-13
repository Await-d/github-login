# GitHub账号管理系统 Docker配置文件
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装所有依赖（包括devDependencies用于构建）
RUN npm ci

# 复制源代码
COPY . .

# 构建TypeScript
RUN npm run build


# 清理开发依赖以减小镜像体积
RUN npm prune --omit=dev

# 创建非root用户和数据目录
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    mkdir -p /app/data && \
    chmod 755 /app/data && \
    chown -R nodejs:nodejs /app

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=3000
ENV DATABASE_DIR=/app/data

# 暴露端口
EXPOSE 3000

# 切换到非root用户
USER nodejs

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

# 启动应用
CMD ["npm", "start"]