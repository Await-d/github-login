/**
 * 测试权限修复脚本
 * 模拟Docker容器环境测试数据库初始化
 */

const fs = require('fs');
const path = require('path');

// 模拟不同的权限场景
const testScenarios = [
    {
        name: '正常权限',
        setup: () => {
            process.env.DATABASE_DIR = './test-data-normal';
            const dir = process.env.DATABASE_DIR;
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        },
        cleanup: () => {
            if (fs.existsSync('./test-data-normal')) {
                fs.rmSync('./test-data-normal', { recursive: true });
            }
        }
    },
    {
        name: '权限不足(模拟)',
        setup: () => {
            process.env.DATABASE_DIR = '/nonexistent/readonly/path';
        },
        cleanup: () => {
            delete process.env.DATABASE_DIR;
        }
    },
    {
        name: '无环境变量',
        setup: () => {
            delete process.env.DATABASE_DIR;
        },
        cleanup: () => {}
    }
];

async function testScenario(scenario) {
    console.log(`\n🧪 测试场景: ${scenario.name}`);
    console.log('='.repeat(50));
    
    try {
        scenario.setup();
        
        // 动态导入数据库模块(避免缓存)
        delete require.cache[require.resolve('./dist/models/database.js')];
        const { Database } = require('./dist/models/database.js');
        
        // 创建数据库实例
        const db = new Database();
        console.log('✅ 数据库初始化成功');
        
        // 清理
        db.close();
        scenario.cleanup();
        
        return true;
    } catch (error) {
        console.error('❌ 测试失败:', error.message);
        scenario.cleanup();
        return false;
    }
}

async function runAllTests() {
    console.log('🚀 开始权限修复测试');
    console.log('测试数据库在不同权限场景下的回退机制\n');
    
    let passCount = 0;
    
    for (const scenario of testScenarios) {
        const success = await testScenario(scenario);
        if (success) passCount++;
        
        // 等待一下避免模块缓存问题
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log('\n📊 测试结果:');
    console.log(`通过: ${passCount}/${testScenarios.length}`);
    
    if (passCount === testScenarios.length) {
        console.log('✅ 所有权限场景测试通过！');
        console.log('🎉 数据库回退机制正常工作');
    } else {
        console.log('⚠️  部分测试失败，需要检查回退逻辑');
    }
    
    // 清理临时文件
    ['/tmp/github-manager-data'].forEach(dir => {
        if (fs.existsSync(dir)) {
            try {
                fs.rmSync(dir, { recursive: true });
                console.log(`🧹 清理临时目录: ${dir}`);
            } catch (e) {
                console.log(`⚠️  无法清理: ${dir}`);
            }
        }
    });
}

// 运行测试
runAllTests().catch(console.error);