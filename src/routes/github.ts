import express from 'express';
import { database } from '../models/database';
import { CryptoManager } from '../utils/crypto';
import { TotpManager } from '../utils/totp';
import { requireAuth } from '../middleware/auth';
import { IAddGitHubAccountRequest, IGitHubAccountResponse, ITotpResponse } from '../types';

const router = express.Router();

// 所有GitHub相关路由都需要认证
router.use(requireAuth);

/**
 * 添加GitHub账号
 * POST /api/github/accounts
 */
router.post('/accounts', async (req, res) => {
  try {
    const { username, password, totpSecret, createdAt }: IAddGitHubAccountRequest = req.body;
    const userId = req.session.userId!;

    // 输入验证
    if (!username || !password || !totpSecret) {
      return res.status(400).json({
        success: false,
        message: '用户名、密码和TOTP密钥都不能为空'
      });
    }

    // 验证日期格式 (YYYY-MM-DD)
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    const accountCreatedAt = createdAt || new Date().toISOString().split('T')[0];
    if (!dateRegex.test(accountCreatedAt)) {
      return res.status(400).json({
        success: false,
        message: '日期格式错误，请使用YYYY-MM-DD格式'
      });
    }

    // 验证TOTP密钥是否有效
    try {
      TotpManager.generateFromUserSecret(totpSecret);
    } catch (error) {
      return res.status(400).json({
        success: false,
        message: 'TOTP密钥格式无效'
      });
    }

    // 加密敏感信息
    const encryptedPassword = CryptoManager.encrypt(password);
    const encryptedTotpSecret = CryptoManager.encrypt(totpSecret);

    // 保存到数据库
    const accountId = await database.addGitHubAccount({
      userId,
      username,
      password: encryptedPassword,
      totpSecret: encryptedTotpSecret,
      createdAt: accountCreatedAt
    });

    const response: IGitHubAccountResponse = {
      success: true,
      message: 'GitHub账号添加成功',
      account: {
        id: accountId,
        userId,
        username,
        password: '***', // 不返回密码
        totpSecret: '***', // 不返回密钥
        createdAt: accountCreatedAt
      }
    };

    res.status(201).json(response);
  } catch (error) {
    console.error('Add GitHub account error:', error);
    res.status(500).json({
      success: false,
      message: '添加GitHub账号失败'
    });
  }
});

/**
 * 获取用户的所有GitHub账号
 * GET /api/github/accounts
 */
router.get('/accounts', async (req, res) => {
  try {
    const userId = req.session.userId!;
    const accounts = await database.getGitHubAccountsByUserId(userId);

    // 隐藏敏感信息
    const safeAccounts = accounts.map(account => ({
      ...account,
      password: '***',
      totpSecret: '***'
    }));

    const response: IGitHubAccountResponse = {
      success: true,
      message: '获取GitHub账号列表成功',
      accounts: safeAccounts
    };

    res.json(response);
  } catch (error) {
    console.error('Get GitHub accounts error:', error);
    res.status(500).json({
      success: false,
      message: '获取GitHub账号列表失败'
    });
  }
});

/**
 * 获取单个GitHub账号详情
 * GET /api/github/accounts/:id
 */
router.get('/accounts/:id', async (req, res) => {
  try {
    const accountId = parseInt(req.params.id);
    const userId = req.session.userId!;

    if (isNaN(accountId)) {
      return res.status(400).json({
        success: false,
        message: '无效的账号ID'
      });
    }

    const account = await database.getGitHubAccountById(accountId);
    
    if (!account) {
      return res.status(404).json({
        success: false,
        message: 'GitHub账号不存在'
      });
    }

    // 检查账号是否属于当前用户
    if (account.userId !== userId) {
      return res.status(403).json({
        success: false,
        message: '无权访问该账号'
      });
    }

    // 解密信息用于显示（但仍然标记为隐藏）
    const response: IGitHubAccountResponse = {
      success: true,
      message: '获取GitHub账号详情成功',
      account: {
        ...account,
        password: '***',
        totpSecret: '***'
      }
    };

    res.json(response);
  } catch (error) {
    console.error('Get GitHub account error:', error);
    res.status(500).json({
      success: false,
      message: '获取GitHub账号详情失败'
    });
  }
});

/**
 * 更新GitHub账号
 * PUT /api/github/accounts/:id
 */
router.put('/accounts/:id', async (req, res) => {
  try {
    const accountId = parseInt(req.params.id);
    const userId = req.session.userId!;
    const { username, password, totpSecret, createdAt } = req.body;

    if (isNaN(accountId)) {
      return res.status(400).json({
        success: false,
        message: '无效的账号ID'
      });
    }

    // 验证账号存在且属于当前用户
    const existingAccount = await database.getGitHubAccountById(accountId);
    if (!existingAccount || existingAccount.userId !== userId) {
      return res.status(404).json({
        success: false,
        message: 'GitHub账号不存在或无权修改'
      });
    }

    // 准备更新数据
    const updates: any = {};
    
    if (username) updates.username = username;
    if (password) updates.password = CryptoManager.encrypt(password);
    if (totpSecret) {
      // 验证TOTP密钥
      try {
        TotpManager.generateFromUserSecret(totpSecret);
        updates.totpSecret = CryptoManager.encrypt(totpSecret);
      } catch (error) {
        return res.status(400).json({
          success: false,
          message: 'TOTP密钥格式无效'
        });
      }
    }
    if (createdAt) {
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (!dateRegex.test(createdAt)) {
        return res.status(400).json({
          success: false,
          message: '日期格式错误，请使用YYYY-MM-DD格式'
        });
      }
      updates.createdAt = createdAt;
    }

    // 执行更新
    const success = await database.updateGitHubAccount(accountId, updates);
    
    if (success) {
      res.json({
        success: true,
        message: 'GitHub账号更新成功'
      });
    } else {
      res.status(500).json({
        success: false,
        message: 'GitHub账号更新失败'
      });
    }
  } catch (error) {
    console.error('Update GitHub account error:', error);
    res.status(500).json({
      success: false,
      message: '更新GitHub账号失败'
    });
  }
});

/**
 * 删除GitHub账号
 * DELETE /api/github/accounts/:id
 */
router.delete('/accounts/:id', async (req, res) => {
  try {
    const accountId = parseInt(req.params.id);
    const userId = req.session.userId!;

    if (isNaN(accountId)) {
      return res.status(400).json({
        success: false,
        message: '无效的账号ID'
      });
    }

    // 验证账号存在且属于当前用户
    const existingAccount = await database.getGitHubAccountById(accountId);
    if (!existingAccount || existingAccount.userId !== userId) {
      return res.status(404).json({
        success: false,
        message: 'GitHub账号不存在或无权删除'
      });
    }

    // 删除账号
    const success = await database.deleteGitHubAccount(accountId);
    
    if (success) {
      res.json({
        success: true,
        message: 'GitHub账号删除成功'
      });
    } else {
      res.status(500).json({
        success: false,
        message: 'GitHub账号删除失败'
      });
    }
  } catch (error) {
    console.error('Delete GitHub account error:', error);
    res.status(500).json({
      success: false,
      message: '删除GitHub账号失败'
    });
  }
});

/**
 * 获取账号的TOTP验证码
 * GET /api/github/accounts/:id/totp
 */
router.get('/accounts/:id/totp', async (req, res) => {
  try {
    const accountId = parseInt(req.params.id);
    const userId = req.session.userId!;

    if (isNaN(accountId)) {
      return res.status(400).json({
        success: false,
        message: '无效的账号ID'
      });
    }

    const account = await database.getGitHubAccountById(accountId);
    
    if (!account || account.userId !== userId) {
      return res.status(404).json({
        success: false,
        message: 'GitHub账号不存在或无权访问'
      });
    }

    // 解密TOTP密钥并生成验证码
    const decryptedSecret = CryptoManager.decrypt(account.totpSecret);
    const token = TotpManager.generateFromUserSecret(decryptedSecret);

    const response: ITotpResponse = {
      success: true,
      token: {
        token: TotpManager.formatToken(token.token),
        timeRemaining: token.timeRemaining
      }
    };

    res.json(response);
  } catch (error) {
    console.error('Get TOTP error:', error);
    res.status(500).json({
      success: false,
      message: '获取TOTP验证码失败'
    });
  }
});

/**
 * 批量获取所有账号的TOTP验证码
 * GET /api/github/totp/all
 */
router.get('/totp/all', async (req, res) => {
  try {
    const userId = req.session.userId!;
    const accounts = await database.getGitHubAccountsByUserId(userId);

    const totpResults = [];
    
    for (const account of accounts) {
      try {
        const decryptedSecret = CryptoManager.decrypt(account.totpSecret);
        const token = TotpManager.generateFromUserSecret(decryptedSecret);
        
        totpResults.push({
          id: account.id,
          username: account.username,
          token: TotpManager.formatToken(token.token),
          timeRemaining: token.timeRemaining
        });
      } catch (error) {
        totpResults.push({
          id: account.id,
          username: account.username,
          token: 'ERROR',
          timeRemaining: 0
        });
      }
    }

    res.json({
      success: true,
      accounts: totpResults
    });
  } catch (error) {
    console.error('Get all TOTP error:', error);
    res.status(500).json({
      success: false,
      message: '获取所有TOTP验证码失败'
    });
  }
});

/**
 * 导出账号信息（按指定格式）
 * GET /api/github/export
 */
router.get('/export', async (req, res) => {
  try {
    const userId = req.session.userId!;
    const accounts = await database.getGitHubAccountsByUserId(userId);

    const exportData = [];
    
    for (const account of accounts) {
      try {
        const decryptedPassword = CryptoManager.decrypt(account.password);
        const decryptedSecret = CryptoManager.decrypt(account.totpSecret);
        
        // 格式：账号----密码---密钥----日期
        const line = `${account.username}----${decryptedPassword}----${decryptedSecret}----${account.createdAt}`;
        exportData.push(line);
      } catch (error) {
        console.error(`Failed to decrypt account ${account.id}:`, error);
      }
    }

    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.setHeader('Content-Disposition', 'attachment; filename="github-accounts.txt"');
    res.send(exportData.join('\n'));
  } catch (error) {
    console.error('Export accounts error:', error);
    res.status(500).json({
      success: false,
      message: '导出账号信息失败'
    });
  }
});

export default router;