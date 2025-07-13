import express from 'express';
import session from 'express-session';
import cors from 'cors';
import path from 'path';
import { securityHeaders, logger, errorHandler, rateLimit } from './middleware/auth';
import authRoutes from './routes/auth';
import githubRoutes from './routes/github';

const app = express();
const PORT = process.env.PORT || 3000;

// 基础中间件
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// CORS配置
app.use(cors({
  origin: process.env.NODE_ENV === 'production' ? false : 'http://localhost:3000',
  credentials: true
}));

// 会话配置
app.use(session({
  secret: process.env.SESSION_SECRET || 'github-manager-secret-key-change-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production', // HTTPS only in production
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// 安全和日志中间件
app.use(securityHeaders);
app.use(logger);
app.use(rateLimit(200, 15 * 60 * 1000)); // 200 requests per 15 minutes

// 静态文件服务
app.use(express.static(path.join(__dirname, '../public')));

// API路由
app.use('/api/auth', authRoutes);
app.use('/api/github', githubRoutes);

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: 'GitHub Manager API is running',
    timestamp: new Date().toISOString()
  });
});

// 前端路由处理（SPA fallback）
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// 错误处理中间件
app.use(errorHandler);

// 启动服务器
app.listen(PORT, () => {
  console.log(`🚀 GitHub Manager Server is running on port ${PORT}`);
  console.log(`📱 Web interface: http://localhost:${PORT}`);
  console.log(`🔗 API endpoint: http://localhost:${PORT}/api`);
  console.log(`💻 Environment: ${process.env.NODE_ENV || 'development'}`);
});

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('🛑 SIGTERM received, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('🛑 SIGINT received, shutting down gracefully...');
  process.exit(0);
});

export default app;