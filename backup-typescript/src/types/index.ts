/**
 * 数据库和应用程序的类型定义
 */

// 用户接口
export interface IUser {
  id?: number;
  username: string;
  password: string; // 加密后的密码
  createdAt?: string;
}

// GitHub账号接口
export interface IGitHubAccount {
  id?: number;
  userId: number; // 关联的用户ID
  username: string; // GitHub用户名
  password: string; // 加密后的GitHub密码
  totpSecret: string; // TOTP密钥
  createdAt: string; // 创建日期 (YYYY-MM-DD格式)
  updatedAt?: string;
}

// TOTP令牌接口
export interface ITotpToken {
  token: string;
  timeRemaining: number; // 剩余有效时间(秒)
}

// API请求和响应类型
export interface ILoginRequest {
  username: string;
  password: string;
}

export interface ILoginResponse {
  success: boolean;
  message: string;
  user?: {
    id: number;
    username: string;
  };
}

export interface IAddGitHubAccountRequest {
  username: string;
  password: string;
  totpSecret: string;
  createdAt: string;
}

export interface IGitHubAccountResponse {
  success: boolean;
  message: string;
  account?: IGitHubAccount;
  accounts?: IGitHubAccount[];
}

export interface ITotpResponse {
  success: boolean;
  token?: ITotpToken;
  message?: string;
}

// 会话类型扩展
declare module 'express-session' {
  interface SessionData {
    userId?: number;
    username?: string;
  }
}