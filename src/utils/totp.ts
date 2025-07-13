import speakeasy from 'speakeasy';
import QRCode from 'qrcode';
import { ITotpToken } from '../types';

/**
 * TOTP工具类
 * 基于提供的GitHub库 https://github.com/jaden/totp-generator 的概念
 * 使用speakeasy库实现TOTP功能
 */
export class TotpManager {
  
  /**
   * 生成TOTP令牌
   * @param secret TOTP密钥
   * @returns TOTP令牌和剩余时间
   */
  static generateToken(secret: string): ITotpToken {
    // 使用speakeasy生成TOTP令牌
    const token = speakeasy.totp({
      secret: secret,
      encoding: 'base32',
      time: Math.floor(Date.now() / 1000),
      step: 30, // 30秒步长
      digits: 6  // 6位数字
    });

    // 计算剩余时间
    const timeRemaining = 30 - (Math.floor(Date.now() / 1000) % 30);

    return {
      token,
      timeRemaining
    };
  }

  /**
   * 验证TOTP令牌
   * @param token 用户输入的令牌
   * @param secret TOTP密钥
   * @param window 时间窗口(允许前后几个步长)
   * @returns 验证结果
   */
  static verifyToken(token: string, secret: string, window: number = 1): boolean {
    return speakeasy.totp.verify({
      secret: secret,
      encoding: 'base32',
      token: token,
      step: 30,
      digits: 6,
      window: window
    });
  }

  /**
   * 生成新的TOTP密钥
   * @param name 账号名称
   * @param issuer 发行者名称
   * @returns 密钥信息
   */
  static generateSecret(name: string, issuer: string = 'GitHub Manager'): {
    secret: string;
    base32: string;
    otpauth_url: string;
  } {
    const secret = speakeasy.generateSecret({
      name: name,
      issuer: issuer,
      length: 32
    });

    return {
      secret: secret.ascii,
      base32: secret.base32,
      otpauth_url: secret.otpauth_url || ''
    };
  }

  /**
   * 生成QR码
   * @param otpauth_url OTP认证URL
   * @returns Base64编码的QR码图片
   */
  static async generateQRCode(otpauth_url: string): Promise<string> {
    try {
      const qrCodeData = await QRCode.toDataURL(otpauth_url);
      return qrCodeData;
    } catch (error) {
      throw new Error('Failed to generate QR code: ' + error);
    }
  }

  /**
   * 根据用户提供的密钥生成TOTP（兼容GitHub的TOTP格式）
   * @param secret 用户提供的密钥字符串
   * @returns TOTP令牌信息
   */
  static generateFromUserSecret(secret: string): ITotpToken {
    // 清理密钥字符串（移除空格和特殊字符）
    const cleanSecret = secret.replace(/\s+/g, '').toUpperCase();
    
    try {
      return this.generateToken(cleanSecret);
    } catch (error) {
      throw new Error('Invalid TOTP secret format');
    }
  }

  /**
   * 格式化显示TOTP令牌
   * @param token TOTP令牌
   * @returns 格式化的令牌字符串 (例如: 123 456)
   */
  static formatToken(token: string): string {
    if (token.length === 6) {
      return `${token.substring(0, 3)} ${token.substring(3)}`;
    }
    return token;
  }

  /**
   * 获取下一个令牌的时间
   * @returns 下一个令牌生成的时间戳
   */
  static getNextTokenTime(): number {
    const now = Math.floor(Date.now() / 1000);
    const nextStep = Math.ceil(now / 30) * 30;
    return nextStep * 1000;
  }

  /**
   * 批量生成多个账号的TOTP
   * @param accounts 账号列表，包含密钥
   * @returns 所有账号的TOTP令牌
   */
  static generateMultipleTokens(accounts: Array<{id: number, username: string, totpSecret: string}>): Array<{
    id: number;
    username: string;
    token: ITotpToken;
  }> {
    return accounts.map(account => {
      try {
        const token = this.generateFromUserSecret(account.totpSecret);
        return {
          id: account.id,
          username: account.username,
          token
        };
      } catch (error) {
        return {
          id: account.id,
          username: account.username,
          token: {
            token: 'ERROR',
            timeRemaining: 0
          }
        };
      }
    });
  }
}