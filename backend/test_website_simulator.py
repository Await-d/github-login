#!/usr/bin/env python3
"""
测试网站模拟器功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.website_simulator import WebsiteSimulator

def test_simulator():
    """测试网站模拟器"""
    print("🧪 开始测试网站模拟器...")
    
    simulator = WebsiteSimulator()
    
    # 测试登录模拟
    print("\n1. 测试登录模拟...")
    success, message, session_data = simulator.simulate_login(
        "https://anyrouter.top/login",
        "test_user",
        "test_password"
    )
    
    print(f"   登录结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"   消息: {message}")
    if session_data:
        print(f"   会话数据: {list(session_data.keys())}")
    
    # 测试账户信息获取
    print("\n2. 测试账户信息获取...")
    if success and session_data:
        info_success, account_info = simulator.get_account_info(
            session_data,
            "https://anyrouter.top"
        )
        print(f"   获取结果: {'✅ 成功' if info_success else '❌ 失败'}")
        if info_success:
            print(f"   余额: ${account_info.get('balance', 0)}")
            print(f"   API密钥数量: {len(account_info.get('api_keys', []))}")
    else:
        # 使用模拟会话数据测试
        mock_session = {
            'cookies': {'session': 'mock_session_id'},
            'login_time': '2024-01-01T00:00:00',
            'user_agent': 'test-agent'
        }
        info_success, account_info = simulator.get_account_info(
            mock_session,
            "https://anyrouter.top"
        )
        print(f"   模拟获取结果: {'✅ 成功' if info_success else '❌ 失败'}")
        if info_success:
            print(f"   模拟余额: ${account_info.get('balance', 0)}")
            print(f"   模拟API密钥数量: {len(account_info.get('api_keys', []))}")
    
    print("\n✅ 网站模拟器测试完成!")

if __name__ == "__main__":
    test_simulator()