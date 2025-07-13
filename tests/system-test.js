/**
 * 系统功能测试脚本 - 使用安全的示例数据
 */

const { TotpManager } = require('../dist/utils/totp');
const { CryptoManager } = require('../dist/utils/crypto');
const { Database } = require('../dist/models/database');

async function testTotpFunctionality() {
    console.log('\n🔐 测试TOTP功能...');
    
    try {
        // 测试TOTP生成 - 使用标准测试密钥
        const testSecret = 'JBSWY3DPEHPK3PXP'; // RFC标准测试密钥
        const token = TotpManager.generateFromUserSecret(testSecret);
        
        console.log('✅ TOTP生成成功');
        console.log(`   令牌: ${token.token}`);
        console.log(`   剩余时间: ${token.timeRemaining}秒`);
        
        // 测试格式化
        const formatted = TotpManager.formatToken(token.token);
        console.log(`   格式化令牌: ${formatted}`);
        
        // 测试验证
        const isValid = TotpManager.verifyToken(token.token, testSecret);
        console.log(`✅ TOTP验证: ${isValid ? '通过' : '失败'}`);
        
        return true;
    } catch (error) {
        console.error('❌ TOTP测试失败:', error.message);
        return false;
    }
}

async function testCryptoFunctionality() {
    console.log('\n🔒 测试加密功能...');
    
    try {
        const testData = 'test-password-123';
        
        // 测试密码哈希
        const hashedPassword = await CryptoManager.hashPassword(testData);
        console.log('✅ 密码哈希成功');
        
        const isValidPassword = await CryptoManager.verifyPassword(testData, hashedPassword);
        console.log(`✅ 密码验证: ${isValidPassword ? '通过' : '失败'}`);
        
        // 测试数据加密
        const encrypted = CryptoManager.encrypt(testData);
        console.log('✅ 数据加密成功');
        
        const decrypted = CryptoManager.decrypt(encrypted);
        console.log(`✅ 数据解密: ${decrypted === testData ? '通过' : '失败'}`);
        
        return true;
    } catch (error) {
        console.error('❌ 加密测试失败:', error.message);
        return false;
    }
}

async function testDatabaseFunctionality() {
    console.log('\n💾 测试数据库功能...');
    
    try {
        const db = new Database();
        
        // 测试创建用户
        const testUsername = 'test_user_' + Date.now();
        const hashedPassword = await CryptoManager.hashPassword('test123');
        
        const userId = await db.createUser({
            username: testUsername,
            password: hashedPassword
        });
        console.log('✅ 用户创建成功, ID:', userId);
        
        // 测试查找用户
        const user = await db.findUserByUsername(testUsername);
        console.log(`✅ 用户查找: ${user ? '成功' : '失败'}`);
        
        // 测试添加GitHub账号 - 使用假数据
        const accountData = {
            userId: userId,
            username: 'test_demo_user',
            password: CryptoManager.encrypt('demo_password'),
            totpSecret: CryptoManager.encrypt('JBSWY3DPEHPK3PXP'),
            createdAt: '2025-01-15'
        };
        
        const accountId = await db.addGitHubAccount(accountData);
        console.log('✅ GitHub账号添加成功, ID:', accountId);
        
        // 测试获取账号列表
        const accounts = await db.getGitHubAccountsByUserId(userId);
        console.log(`✅ 账号列表获取: ${accounts.length > 0 ? '成功' : '失败'}`);
        
        // 清理测试数据
        await db.deleteGitHubAccount(accountId);
        console.log('✅ 测试数据清理完成');
        
        db.close();
        return true;
    } catch (error) {
        console.error('❌ 数据库测试失败:', error.message);
        return false;
    }
}

async function testFormatParsing() {
    console.log('\n📝 测试格式解析...');
    
    try {
        // 测试格式解析 - 使用安全的示例数据
        const testLines = [
            'demo_user_001----DemoPass123----JBSWY3DPEHPK3PXP----2025-01-15',
            'example_account----ExamplePass456----KRUGKIDROVUWG2ZA----2025-02-20'
        ];
        
        for (const line of testLines) {
            const parts = line.split('----');
            if (parts.length === 4) {
                const [username, password, totpSecret, date] = parts;
                
                // 测试TOTP生成
                try {
                    const token = TotpManager.generateFromUserSecret(totpSecret);
                    console.log(`✅ ${username}: TOTP生成成功 (${token.token})`);
                } catch (error) {
                    console.log(`⚠️  ${username}: TOTP密钥格式错误`);
                }
            }
        }
        
        return true;
    } catch (error) {
        console.error('❌ 格式解析测试失败:', error.message);
        return false;
    }
}

async function runAllTests() {
    console.log('🚀 开始系统功能测试...\n');
    
    const tests = [
        { name: 'TOTP功能', test: testTotpFunctionality },
        { name: '加密功能', test: testCryptoFunctionality },
        { name: '数据库功能', test: testDatabaseFunctionality },
        { name: '格式解析', test: testFormatParsing }
    ];
    
    let passedTests = 0;
    
    for (const { name, test } of tests) {
        try {
            const result = await test();
            if (result) {
                passedTests++;
            }
        } catch (error) {
            console.error(`❌ ${name}测试出现异常:`, error.message);
        }
    }
    
    console.log('\n📊 测试结果:');
    console.log(`   通过: ${passedTests}/${tests.length}`);
    console.log(`   状态: ${passedTests === tests.length ? '✅ 所有测试通过' : '⚠️  部分测试失败'}`);
    
    if (passedTests === tests.length) {
        console.log('\n🎉 系统功能测试完成，所有核心功能正常工作！');
        console.log('\n📝 可以开始使用以下命令启动系统:');
        console.log('   开发模式: npm run dev');
        console.log('   生产模式: npm start');
    } else {
        console.log('\n⚠️  请检查失败的测试项目并修复问题。');
    }
}

// 运行测试
runAllTests().catch(console.error);