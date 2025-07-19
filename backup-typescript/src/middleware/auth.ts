import { Request, Response, NextFunction } from 'express';

/**
 * 认证中间件
 * 检查用户是否已登录
 */
export const requireAuth = (req: Request, res: Response, next: NextFunction) => {
  if (req.session && req.session.userId) {
    // 用户已登录，继续处理请求
    next();
  } else {
    // 用户未登录，返回401错误
    res.status(401).json({
      success: false,
      message: '请先登录'
    });
  }
};

/**
 * 检查用户是否已登录(不阻止请求)
 * 将用户信息添加到req对象中
 */
export const checkAuth = (req: Request, res: Response, next: NextFunction) => {
  if (req.session && req.session.userId) {
    // 将用户信息添加到request对象
    (req as any).user = {
      id: req.session.userId,
      username: req.session.username
    };
  }
  next();
};

/**
 * 设置安全头
 */
export const securityHeaders = (req: Request, res: Response, next: NextFunction) => {
  // 禁用X-Powered-By头
  res.removeHeader('X-Powered-By');
  
  // 设置安全相关头
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  
  // 设置CSP头(根据需要调整)
  res.setHeader('Content-Security-Policy', 
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data:; " +
    "connect-src 'self'"
  );
  
  next();
};

/**
 * 请求速率限制中间件
 * 简单的内存存储方式(生产环境建议使用Redis)
 */
const requestCounts = new Map<string, { count: number; resetTime: number }>();

export const rateLimit = (maxRequests: number = 100, windowMs: number = 15 * 60 * 1000) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
    const now = Date.now();
    
    const clientData = requestCounts.get(clientIp);
    
    if (!clientData || now > clientData.resetTime) {
      // 重置计数器
      requestCounts.set(clientIp, {
        count: 1,
        resetTime: now + windowMs
      });
      next();
    } else if (clientData.count < maxRequests) {
      // 增加计数
      clientData.count++;
      next();
    } else {
      // 超过限制
      res.status(429).json({
        success: false,
        message: '请求过于频繁，请稍后再试'
      });
    }
  };
};

/**
 * 错误处理中间件
 */
export const errorHandler = (err: any, req: Request, res: Response, next: NextFunction) => {
  console.error('Error:', err);
  
  // 根据错误类型返回不同的响应
  if (err.code === 'ENOENT') {
    res.status(404).json({
      success: false,
      message: '资源未找到'
    });
  } else if (err.name === 'ValidationError') {
    res.status(400).json({
      success: false,
      message: '输入数据无效'
    });
  } else if (err.code === 'SQLITE_CONSTRAINT') {
    res.status(409).json({
      success: false,
      message: '数据冲突'
    });
  } else {
    res.status(500).json({
      success: false,
      message: '服务器内部错误'
    });
  }
};

/**
 * 日志中间件
 */
export const logger = (req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  const timestamp = new Date().toISOString();
  const method = req.method;
  const url = req.url;
  const userAgent = req.get('User-Agent') || '';
  const ip = req.ip || req.connection.remoteAddress;
  
  // 记录请求开始
  console.log(`[${timestamp}] ${method} ${url} - ${ip} - ${userAgent}`);
  
  // 监听响应结束
  res.on('finish', () => {
    const duration = Date.now() - start;
    const status = res.statusCode;
    console.log(`[${timestamp}] ${method} ${url} - ${status} - ${duration}ms`);
  });
  
  next();
};