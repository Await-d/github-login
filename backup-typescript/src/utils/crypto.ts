import bcrypt from 'bcrypt';
import crypto from 'crypto';

/**
 * 加密工具类
 */
export class CryptoManager {
  private static readonly SALT_ROUNDS = 12;
  private static readonly ALGORITHM = 'aes-256-gcm';
  private static readonly KEY_LENGTH = 32;
  
  // 用于加密敏感数据的密钥(在生产环境中应该从环境变量获取)
  private static readonly ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || crypto.randomBytes(32);

  /**
   * 哈希密码
   * @param password 明文密码
   * @returns 哈希后的密码
   */
  static async hashPassword(password: string): Promise<string> {
    return await bcrypt.hash(password, this.SALT_ROUNDS);
  }

  /**
   * 验证密码
   * @param password 明文密码
   * @param hash 哈希后的密码
   * @returns 验证结果
   */
  static async verifyPassword(password: string, hash: string): Promise<boolean> {
    return await bcrypt.compare(password, hash);
  }

  /**
   * 加密敏感数据(如GitHub密码和TOTP密钥)
   * @param text 要加密的文本
   * @returns 加密后的数据
   */
  static encrypt(text: string): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(this.ALGORITHM, this.ENCRYPTION_KEY);
    
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    // 返回格式: iv:authTag:encryptedData
    return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
  }

  /**
   * 解密敏感数据
   * @param encryptedData 加密的数据
   * @returns 解密后的文本
   */
  static decrypt(encryptedData: string): string {
    try {
      const parts = encryptedData.split(':');
      if (parts.length !== 3) {
        throw new Error('Invalid encrypted data format');
      }

      const iv = Buffer.from(parts[0], 'hex');
      const authTag = Buffer.from(parts[1], 'hex');
      const encrypted = parts[2];

      const decipher = crypto.createDecipher(this.ALGORITHM, this.ENCRYPTION_KEY);
      decipher.setAuthTag(authTag);

      let decrypted = decipher.update(encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');

      return decrypted;
    } catch (error) {
      throw new Error('Failed to decrypt data: ' + error);
    }
  }

  /**
   * 生成随机密钥
   * @param length 密钥长度
   * @returns 随机密钥
   */
  static generateRandomKey(length: number = 32): string {
    return crypto.randomBytes(length).toString('hex');
  }

  /**
   * 生成安全的会话ID
   * @returns 会话ID
   */
  static generateSessionId(): string {
    return crypto.randomBytes(32).toString('hex');
  }

  /**
   * 创建数据签名
   * @param data 要签名的数据
   * @returns 签名
   */
  static createSignature(data: string): string {
    const hmac = crypto.createHmac('sha256', this.ENCRYPTION_KEY);
    hmac.update(data);
    return hmac.digest('hex');
  }

  /**
   * 验证数据签名
   * @param data 原始数据
   * @param signature 签名
   * @returns 验证结果
   */
  static verifySignature(data: string, signature: string): boolean {
    const expectedSignature = this.createSignature(data);
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    );
  }
}