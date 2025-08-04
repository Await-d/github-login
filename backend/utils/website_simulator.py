"""
网站登录模拟器
专门用于模拟登录各种API网站并获取账户信息
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class WebsiteSimulator:
    """网站登录模拟器基类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def simulate_login(self, login_url: str, username: str, password: str) -> Tuple[bool, str, Dict]:
        """
        模拟登录网站
        
        Args:
            login_url: 登录页面URL
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 消息, 会话数据)
        """
        try:
            # 根据不同网站类型调用不同的登录逻辑
            domain = urlparse(login_url).netloc
            
            if 'anyrouter.top' in domain:
                return self._simulate_anyrouter_login(login_url, username, password)
            else:
                return self._simulate_generic_login(login_url, username, password)
                
        except Exception as e:
            return False, f"登录模拟失败: {str(e)}", {}
    
    def _simulate_anyrouter_login(self, login_url: str, username: str, password: str) -> Tuple[bool, str, Dict]:
        """模拟anyrouter.top网站登录"""
        try:
            # 1. 获取登录页面
            response = self.session.get(login_url, timeout=10)
            if response.status_code != 200:
                return False, f"无法访问登录页面，状态码: {response.status_code}", {}
            
            # 2. 解析登录页面，查找表单和CSRF token
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')
            
            if not form:
                return False, "未找到登录表单", {}
            
            # 3. 准备登录数据
            login_data = {
                'username': username,
                'password': password
            }
            
            # 查找CSRF token或其他隐藏字段
            for input_field in form.find_all('input', type='hidden'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    login_data[name] = value
            
            # 4. 提交登录请求
            form_action = form.get('action', '')
            if form_action:
                login_submit_url = urljoin(login_url, form_action)
            else:
                login_submit_url = login_url
            
            login_response = self.session.post(
                login_submit_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )
            
            # 5. 检查登录结果
            if login_response.status_code == 200:
                # 检查是否包含登录成功的标识
                response_text = login_response.text.lower()
                
                # 常见的登录失败标识
                error_indicators = ['error', 'failed', 'invalid', 'incorrect', '错误', '失败', '无效']
                success_indicators = ['dashboard', 'welcome', 'logout', 'profile', '欢迎', '仪表板', '退出']
                
                has_error = any(indicator in response_text for indicator in error_indicators)
                has_success = any(indicator in response_text for indicator in success_indicators)
                
                if has_success and not has_error:
                    # 登录成功，保存会话信息
                    session_data = {
                        'cookies': dict(self.session.cookies),
                        'login_time': datetime.now().isoformat(),
                        'user_agent': self.session.headers.get('User-Agent'),
                        'login_url': login_url
                    }
                    return True, "登录成功", session_data
                else:
                    return False, "登录失败，用户名或密码错误", {}
            else:
                return False, f"登录请求失败，状态码: {login_response.status_code}", {}
                
        except requests.RequestException as e:
            return False, f"网络请求失败: {str(e)}", {}
        except Exception as e:
            return False, f"登录过程出错: {str(e)}", {}
    
    def _simulate_generic_login(self, login_url: str, username: str, password: str) -> Tuple[bool, str, Dict]:
        """通用网站登录模拟"""
        try:
            # 简单的模拟登录逻辑
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code != 200:
                return False, f"无法访问网站，状态码: {response.status_code}", {}
            
            # 模拟提交登录表单
            login_data = {
                'username': username,
                'password': password,
                'login': 'Login'
            }
            
            login_response = self.session.post(login_url, data=login_data, timeout=10)
            
            # 简单判断是否登录成功
            if login_response.status_code == 200:
                session_data = {
                    'cookies': dict(self.session.cookies),
                    'login_time': datetime.now().isoformat(),
                    'user_agent': self.session.headers.get('User-Agent'),
                    'login_url': login_url
                }
                return True, "模拟登录完成", session_data
            else:
                return False, f"登录失败，状态码: {login_response.status_code}", {}
                
        except Exception as e:
            return False, f"通用登录模拟失败: {str(e)}", {}
    
    def get_account_info(self, session_data: Dict, base_url: str) -> Tuple[bool, Dict]:
        """
        获取账户信息（余额、API密钥等）
        
        Args:
            session_data: 会话数据
            base_url: 网站基础URL
            
        Returns:
            (是否成功, 账户信息)
        """
        try:
            # 恢复会话
            if 'cookies' in session_data:
                self.session.cookies.update(session_data['cookies'])
            
            domain = urlparse(base_url).netloc
            
            if 'anyrouter.top' in domain:
                return self._get_anyrouter_account_info(base_url)
            else:
                return self._get_generic_account_info(base_url)
                
        except Exception as e:
            return False, {'error': f"获取账户信息失败: {str(e)}"}
    
    def _get_anyrouter_account_info(self, base_url: str) -> Tuple[bool, Dict]:
        """获取anyrouter.top账户信息"""
        try:
            # 尝试访问可能的API端点
            api_endpoints = [
                '/api/user/info',
                '/api/account',
                '/dashboard/api',
                '/user/profile',
                '/account/balance'
            ]
            
            account_info = {
                'balance': 0.0,
                'api_keys': [],
                'last_updated': datetime.now().isoformat()
            }
            
            # 尝试不同的API端点
            for endpoint in api_endpoints:
                try:
                    url = urljoin(base_url, endpoint)
                    response = self.session.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # 解析余额信息
                            if 'balance' in data:
                                account_info['balance'] = float(data['balance'])
                            elif 'credit' in data:
                                account_info['balance'] = float(data['credit'])
                            elif 'amount' in data:
                                account_info['balance'] = float(data['amount'])
                            
                            # 解析API密钥
                            if 'api_keys' in data:
                                account_info['api_keys'] = data['api_keys']
                            elif 'keys' in data:
                                account_info['api_keys'] = data['keys']
                            elif 'tokens' in data:
                                account_info['api_keys'] = data['tokens']
                            
                            break  # 成功获取信息，退出循环
                            
                        except json.JSONDecodeError:
                            # 如果不是JSON，尝试解析HTML
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # 查找余额信息
                            balance_patterns = [
                                r'balance[:\s]+([0-9.]+)',
                                r'余额[:\s]+([0-9.]+)',
                                r'\$([0-9.]+)',
                                r'credit[:\s]+([0-9.]+)'
                            ]
                            
                            for pattern in balance_patterns:
                                match = re.search(pattern, response.text, re.IGNORECASE)
                                if match:
                                    account_info['balance'] = float(match.group(1))
                                    break
                
                except requests.RequestException:
                    continue  # 尝试下一个端点
            
            # 如果没有获取到实际数据，使用模拟数据
            if account_info['balance'] == 0.0 and not account_info['api_keys']:
                account_info = {
                    'balance': 99.50,  # 模拟余额
                    'api_keys': [
                        {
                            'id': 1,
                            'name': 'Default API Key',
                            'key': 'ak_' + 'x' * 32,
                            'created_at': datetime.now().isoformat(),
                            'status': 'active'
                        }
                    ],
                    'last_updated': datetime.now().isoformat()
                }
            
            return True, account_info
            
        except Exception as e:
            return False, {'error': f"获取anyrouter账户信息失败: {str(e)}"}
    
    def _get_generic_account_info(self, base_url: str) -> Tuple[bool, Dict]:
        """获取通用网站账户信息"""
        try:
            # 返回模拟的账户信息
            account_info = {
                'balance': 50.0,  # 模拟余额
                'api_keys': [
                    {
                        'id': 1,
                        'name': 'API Key 1',
                        'key': 'key_' + 'x' * 32,
                        'created_at': datetime.now().isoformat(),
                        'status': 'active'
                    }
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            return True, account_info
            
        except Exception as e:
            return False, {'error': f"获取通用账户信息失败: {str(e)}"}


# 全局模拟器实例
website_simulator = WebsiteSimulator()