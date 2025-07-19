import express from 'express';
import { database } from '../models/database';
import { CryptoManager } from '../utils/crypto';
import { ILoginRequest, ILoginResponse } from '../types';

const router = express.Router();

/**
 * 用户注册
 */
router.post('/register', async (req, res) => {
  try {
    const { username, password }: ILoginRequest = req.body;

    // 输入验证
    if (!username || !password) {
      return res.status(400).json({
        success: false,
        message: '用户名和密码不能为空'
      });
    }

    if (username.length < 3 || username.length > 20) {
      return res.status(400).json({
        success: false,
        message: '用户名长度必须在3-20个字符之间'
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        success: false,
        message: '密码长度至少6个字符'
      });
    }

    // 检查用户名是否已存在
    const existingUser = await database.findUserByUsername(username);
    if (existingUser) {
      return res.status(409).json({
        success: false,
        message: '用户名已存在'
      });
    }

    // 创建用户
    const hashedPassword = await CryptoManager.hashPassword(password);
    const userId = await database.createUser({
      username,
      password: hashedPassword
    });

    // 设置会话
    req.session.userId = userId;
    req.session.username = username;

    const response: ILoginResponse = {
      success: true,
      message: '注册成功',
      user: {
        id: userId,
        username
      }
    };

    res.status(201).json(response);
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({
      success: false,
      message: '注册失败'
    });
  }
});

/**
 * 用户登录
 */
router.post('/login', async (req, res) => {
  try {
    const { username, password }: ILoginRequest = req.body;

    // 输入验证
    if (!username || !password) {
      return res.status(400).json({
        success: false,
        message: '用户名和密码不能为空'
      });
    }

    // 查找用户
    const user = await database.findUserByUsername(username);
    if (!user) {
      return res.status(401).json({
        success: false,
        message: '用户名或密码错误'
      });
    }

    // 验证密码
    const isValidPassword = await CryptoManager.verifyPassword(password, user.password);
    if (!isValidPassword) {
      return res.status(401).json({
        success: false,
        message: '用户名或密码错误'
      });
    }

    // 设置会话
    req.session.userId = user.id!;
    req.session.username = user.username;

    const response: ILoginResponse = {
      success: true,
      message: '登录成功',
      user: {
        id: user.id!,
        username: user.username
      }
    };

    res.json(response);
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      message: '登录失败'
    });
  }
});

/**
 * 用户登出
 */
router.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      console.error('Logout error:', err);
      return res.status(500).json({
        success: false,
        message: '登出失败'
      });
    }

    res.clearCookie('connect.sid'); // 清除会话cookie
    res.json({
      success: true,
      message: '登出成功'
    });
  });
});

/**
 * 获取当前用户信息
 */
router.get('/me', (req, res) => {
  if (req.session && req.session.userId) {
    res.json({
      success: true,
      user: {
        id: req.session.userId,
        username: req.session.username
      }
    });
  } else {
    res.status(401).json({
      success: false,
      message: '未登录'
    });
  }
});

/**
 * 检查登录状态
 */
router.get('/status', (req, res) => {
  const isLoggedIn = !!(req.session && req.session.userId);
  res.json({
    success: true,
    isLoggedIn,
    user: isLoggedIn ? {
      id: req.session.userId,
      username: req.session.username
    } : null
  });
});

export default router;