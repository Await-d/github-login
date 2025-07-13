import sqlite3 from 'sqlite3';
import path from 'path';
import fs from 'fs';
import { IUser, IGitHubAccount } from '../types';

/**
 * 数据库管理类
 */
export class Database {
  private db: sqlite3.Database;
  private dbPath: string;

  constructor() {
    // 支持环境变量配置数据库路径
    const dataDir = process.env.DATABASE_DIR || path.join(__dirname, '../../data');
    this.dbPath = path.join(dataDir, 'github-manager.db');
    
    // 确保数据目录存在
    this.ensureDataDirectory();
    
    this.db = new sqlite3.Database(this.dbPath, (err) => {
      if (err) {
        console.error('数据库连接失败:', err.message);
        console.error('数据库路径:', this.dbPath);
        throw err;
      } else {
        console.log('✅ 数据库连接成功:', this.dbPath);
      }
    });
    
    this.initTables();
  }

  /**
   * 确保数据目录存在
   */
  private ensureDataDirectory(): void {
    const dataDir = path.dirname(this.dbPath);
    try {
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
        console.log('📁 创建数据目录:', dataDir);
      }
    } catch (error) {
      console.error('创建数据目录失败:', error);
      throw error;
    }
  }

  /**
   * 初始化数据库表
   */
  private initTables(): void {
    // 创建用户表
    const createUsersTable = `
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `;

    // 创建GitHub账号表
    const createGitHubAccountsTable = `
      CREATE TABLE IF NOT EXISTS github_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        totp_secret TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
      )
    `;

    this.db.serialize(() => {
      this.db.run(createUsersTable);
      this.db.run(createGitHubAccountsTable);
    });
  }

  /**
   * 创建用户
   */
  createUser(user: Omit<IUser, 'id' | 'createdAt'>): Promise<number> {
    return new Promise((resolve, reject) => {
      const sql = 'INSERT INTO users (username, password) VALUES (?, ?)';
      this.db.run(sql, [user.username, user.password], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve(this.lastID);
        }
      });
    });
  }

  /**
   * 根据用户名查找用户
   */
  findUserByUsername(username: string): Promise<IUser | null> {
    return new Promise((resolve, reject) => {
      const sql = 'SELECT * FROM users WHERE username = ?';
      this.db.get(sql, [username], (err, row: any) => {
        if (err) {
          reject(err);
        } else {
          if (row) {
            resolve({
              id: row.id,
              username: row.username,
              password: row.password,
              createdAt: row.created_at
            });
          } else {
            resolve(null);
          }
        }
      });
    });
  }

  /**
   * 根据ID查找用户
   */
  findUserById(id: number): Promise<IUser | null> {
    return new Promise((resolve, reject) => {
      const sql = 'SELECT * FROM users WHERE id = ?';
      this.db.get(sql, [id], (err, row: any) => {
        if (err) {
          reject(err);
        } else {
          if (row) {
            resolve({
              id: row.id,
              username: row.username,
              password: row.password,
              createdAt: row.created_at
            });
          } else {
            resolve(null);
          }
        }
      });
    });
  }

  /**
   * 添加GitHub账号
   */
  addGitHubAccount(account: Omit<IGitHubAccount, 'id' | 'updatedAt'>): Promise<number> {
    return new Promise((resolve, reject) => {
      const sql = `
        INSERT INTO github_accounts (user_id, username, password, totp_secret, created_at) 
        VALUES (?, ?, ?, ?, ?)
      `;
      this.db.run(sql, [
        account.userId,
        account.username,
        account.password,
        account.totpSecret,
        account.createdAt
      ], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve(this.lastID);
        }
      });
    });
  }

  /**
   * 获取用户的所有GitHub账号
   */
  getGitHubAccountsByUserId(userId: number): Promise<IGitHubAccount[]> {
    return new Promise((resolve, reject) => {
      const sql = 'SELECT * FROM github_accounts WHERE user_id = ? ORDER BY created_at DESC';
      this.db.all(sql, [userId], (err, rows: any[]) => {
        if (err) {
          reject(err);
        } else {
          const accounts = rows.map(row => ({
            id: row.id,
            userId: row.user_id,
            username: row.username,
            password: row.password,
            totpSecret: row.totp_secret,
            createdAt: row.created_at,
            updatedAt: row.updated_at
          }));
          resolve(accounts);
        }
      });
    });
  }

  /**
   * 根据ID获取GitHub账号
   */
  getGitHubAccountById(id: number): Promise<IGitHubAccount | null> {
    return new Promise((resolve, reject) => {
      const sql = 'SELECT * FROM github_accounts WHERE id = ?';
      this.db.get(sql, [id], (err, row: any) => {
        if (err) {
          reject(err);
        } else {
          if (row) {
            resolve({
              id: row.id,
              userId: row.user_id,
              username: row.username,
              password: row.password,
              totpSecret: row.totp_secret,
              createdAt: row.created_at,
              updatedAt: row.updated_at
            });
          } else {
            resolve(null);
          }
        }
      });
    });
  }

  /**
   * 更新GitHub账号
   */
  updateGitHubAccount(id: number, updates: Partial<IGitHubAccount>): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const fields = [];
      const values = [];
      
      if (updates.username) {
        fields.push('username = ?');
        values.push(updates.username);
      }
      if (updates.password) {
        fields.push('password = ?');
        values.push(updates.password);
      }
      if (updates.totpSecret) {
        fields.push('totp_secret = ?');
        values.push(updates.totpSecret);
      }
      if (updates.createdAt) {
        fields.push('created_at = ?');
        values.push(updates.createdAt);
      }

      fields.push('updated_at = CURRENT_TIMESTAMP');
      values.push(id);

      const sql = `UPDATE github_accounts SET ${fields.join(', ')} WHERE id = ?`;
      
      this.db.run(sql, values, function(err) {
        if (err) {
          reject(err);
        } else {
          resolve(this.changes > 0);
        }
      });
    });
  }

  /**
   * 删除GitHub账号
   */
  deleteGitHubAccount(id: number): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const sql = 'DELETE FROM github_accounts WHERE id = ?';
      this.db.run(sql, [id], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve(this.changes > 0);
        }
      });
    });
  }

  /**
   * 关闭数据库连接
   */
  close(): void {
    this.db.close();
  }
}

// 导出单例实例
export const database = new Database();