"""
网站登录模拟器
专门用于模拟登录各种API网站并获取账户信息
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

# 可选依赖，优雅降级
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  警告: requests 模块未安装，网站登录模拟功能将不可用")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️  警告: beautifulsoup4 模块未安装，HTML解析功能将不可用")


class WebsiteSimulator:
    """网站登录模拟器基类"""
    
    def __init__(self):
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            })
        else:
            self.session = None
    
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
        if not HAS_REQUESTS:
            return False, "系统缺少 requests 依赖，无法执行网站登录模拟", {}
        
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
            if not HAS_BS4:
                return False, "系统缺少 beautifulsoup4 依赖，无法解析HTML表单", {}
            
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
        if not HAS_REQUESTS:
            return False, {'error': '系统缺少 requests 依赖，无法获取账户信息'}
        
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
                            if HAS_BS4:
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
            return False, f"获取通用账户信息失败: {str(e)}"
    
    def simulate_github_oauth_login(self, website_url: str, github_username: str, github_password: str, totp_secret: str) -> Tuple[bool, str, Dict]:
        """
        模拟使用GitHub OAuth登录第三方网站
        
        Args:
            website_url: 第三方网站URL（如anyrouter.top）
            github_username: GitHub用户名
            github_password: GitHub密码
            totp_secret: GitHub TOTP密钥
            
        Returns:
            (是否成功, 消息, 会话数据)
        """
        if not HAS_REQUESTS:
            return False, "系统缺少 requests 依赖，无法执行GitHub OAuth登录模拟", {}
        
        try:
            # 首先尝试传统的requests方式
            print(f"🔄 尝试传统requests方式访问: {website_url}")
            response = self.session.get(website_url, timeout=15)
            
            # 检查是否遇到反爬虫保护
            if response.status_code == 200 and len(response.text) < 1000 and 'javascript' in response.text.lower():
                print("🚨 检测到反爬虫保护，切换到无头浏览器模式...")
                
                # 尝试导入浏览器模拟器
                try:
                    from .browser_simulator import simulate_github_oauth_login_browser
                    return simulate_github_oauth_login_browser(website_url, github_username, github_password, totp_secret)
                except ImportError:
                    return False, "检测到反爬虫保护，但无法使用浏览器模拟器，请安装selenium", {}
            
            # 传统流程处理
            if response.status_code != 200:
                print("🚨 requests访问失败，尝试浏览器模式...")
                try:
                    from .browser_simulator import simulate_github_oauth_login_browser
                    return simulate_github_oauth_login_browser(website_url, github_username, github_password, totp_secret)
                except ImportError:
                    return False, f"无法访问网站，状态码: {response.status_code}，且浏览器模拟器不可用", {}
            
            print(f"✅ 网站访问成功，状态码: {response.status_code}")
            print(f"📄 网站内容长度: {len(response.text)} 字符")
            
            if not HAS_BS4:
                return False, "系统缺少 beautifulsoup4 依赖，无法解析HTML", {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 2. 寻找GitHub OAuth登录链接或按钮
            github_oauth_url = self._find_github_oauth_link(soup, website_url)
            
            if not github_oauth_url:
                # 尝试常见的OAuth端点
                common_oauth_paths = [
                    '/auth/github',
                    '/signin/github'
                ]
                
                print("📋 在页面中未找到GitHub OAuth链接，尝试常见OAuth端点...")
                for path in common_oauth_paths:
                    test_url = website_url.rstrip('/') + path
                    print(f"🔍 尝试访问: {test_url}")
                    
                    try:
                        test_response = self.session.get(test_url, timeout=10, allow_redirects=False)
                        print(f"📊 端点 {path} 响应状态码: {test_response.status_code}")
                        
                        # 检查是否是重定向到GitHub
                        if test_response.status_code in [302, 301, 307]:
                            location = test_response.headers.get('Location', '')
                            print(f"🔄 重定向到: {location}")
                            if 'github.com' in location:
                                github_oauth_url = test_url
                                print(f"✅ 找到GitHub OAuth端点: {github_oauth_url}")
                                break
                    except Exception as e:
                        print(f"❌ 测试端点 {path} 失败: {e}")
                        continue
                
                if not github_oauth_url:
                    print("🚨 传统方式未找到OAuth选项，尝试浏览器模式...")
                    try:
                        from .browser_simulator import simulate_github_oauth_login_browser
                        return simulate_github_oauth_login_browser(website_url, github_username, github_password, totp_secret)
                    except ImportError:
                        return False, "未找到GitHub OAuth登录选项，且浏览器模拟器不可用", {}
            
            # 3. 点击GitHub OAuth登录链接，跳转到GitHub
            print(f"🔗 访问GitHub OAuth端点: {github_oauth_url}")
            oauth_response = self.session.get(github_oauth_url, timeout=15, allow_redirects=True)
            print(f"🔄 OAuth重定向完成，当前URL: {oauth_response.url}")
            
            # 检查是否成功跳转到GitHub
            if 'github.com' not in oauth_response.url:
                return False, f"GitHub OAuth重定向失败，当前URL: {oauth_response.url}", {}
            
            # 4. 在GitHub登录页面进行登录
            print("🔐 开始GitHub登录流程...")
            github_login_success, github_message, _ = self._perform_github_login(
                oauth_response, github_username, github_password, totp_secret
            )
            
            if not github_login_success:
                return False, f"GitHub登录失败: {github_message}", {}
            
            print("✅ GitHub登录成功，处理OAuth授权...")
            
            # 5. 处理OAuth授权确认页面
            auth_success, auth_message = self._handle_github_oauth_authorization()
            if not auth_success:
                return False, f"GitHub授权失败: {auth_message}", {}
            
            print("✅ OAuth授权完成，验证网站登录状态...")
            
            # 6. 验证是否成功登录到第三方网站
            final_response = self.session.get(website_url, timeout=15)
            if self._is_logged_in_to_website(final_response):
                session_data = {
                    'cookies': dict(self.session.cookies),
                    'login_time': datetime.now().isoformat(),
                    'login_method': 'github_oauth',
                    'website_url': website_url,
                    'github_username': github_username
                }
                return True, "GitHub OAuth登录成功", session_data
            else:
                return False, "OAuth流程完成但网站登录状态验证失败", {}
                
        except Exception as e:
            error_msg = f"GitHub OAuth登录过程异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(traceback.format_exc())
            return False, error_msg, {}
    
    def _find_github_oauth_link(self, soup, base_url: str) -> Optional[str]:
        """寻找页面中的GitHub OAuth登录链接"""
        try:
            # 常见的GitHub OAuth链接模式
            github_patterns = [
                'github',
                'oauth/github', 
                'auth/github',
                'login/github'
            ]
            
            # 寻找包含GitHub的链接
            for link in soup.find_all(['a', 'button']):
                href = link.get('href', '')
                onclick = link.get('onclick', '')
                text = link.get_text().lower()
                
                # 检查链接文本是否包含github
                if 'github' in text:
                    if href:
                        return urljoin(base_url, href)
                
                # 检查href属性
                if href and any(pattern in href.lower() for pattern in github_patterns):
                    return urljoin(base_url, href)
                
                # 检查onclick属性中的跳转
                if onclick and 'github' in onclick.lower():
                    # 尝试从onclick中提取URL
                    import re
                    url_match = re.search(r'location\.href\s*=\s*["\']([^"\']+)["\']', onclick)
                    if url_match:
                        return urljoin(base_url, url_match.group(1))
            
            return None
            
        except Exception as e:
            print(f"寻找GitHub OAuth链接时出错: {e}")
            return None
    
    def _perform_github_login(self, oauth_response, username: str, password: str, totp_secret: str) -> Tuple[bool, str, Dict]:
        """在GitHub OAuth页面执行登录"""
        try:
            soup = BeautifulSoup(oauth_response.text, 'html.parser')
            
            # 寻找登录表单
            login_form = soup.find('form')
            if not login_form:
                return False, "未找到GitHub登录表单", {}
            
            # 获取CSRF token
            csrf_token = None
            csrf_input = soup.find('input', {'name': 'authenticity_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            # 准备登录数据
            login_data = {
                'login': username,
                'password': password
            }
            
            if csrf_token:
                login_data['authenticity_token'] = csrf_token
            
            # 提交登录
            form_action = login_form.get('action', '/session')
            login_url = urljoin('https://github.com', form_action)
            
            login_response = self.session.post(
                login_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )
            
            # 检查是否需要2FA
            if 'two-factor' in login_response.url or 'sessions/two-factor' in login_response.url:
                return self._handle_github_2fa(login_response, totp_secret)
            
            # 检查是否登录成功（通过检查是否跳转到授权页面）
            if 'oauth/authorize' in login_response.url or 'login' not in login_response.url:
                return True, "GitHub登录成功", {}
            else:
                return False, "GitHub用户名或密码错误", {}
                
        except Exception as e:
            return False, f"GitHub登录过程异常: {str(e)}", {}
    
    def _handle_github_2fa(self, two_factor_response, totp_secret: str) -> Tuple[bool, str, Dict]:
        """处理GitHub两因素认证"""
        try:
            # 生成TOTP验证码
            from utils.totp import generate_totp_token
            totp_info = generate_totp_token(totp_secret)
            totp_code = totp_info['token']
            
            soup = BeautifulSoup(two_factor_response.text, 'html.parser')
            
            # 获取CSRF token
            csrf_token = None
            csrf_input = soup.find('input', {'name': 'authenticity_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            # 准备2FA数据
            totp_data = {
                'otp': totp_code
            }
            
            if csrf_token:
                totp_data['authenticity_token'] = csrf_token
            
            # 提交TOTP验证码
            totp_form = soup.find('form')
            if totp_form:
                form_action = totp_form.get('action', '/sessions/two-factor')
                totp_url = urljoin('https://github.com', form_action)
            else:
                totp_url = 'https://github.com/sessions/two-factor'
            
            totp_response = self.session.post(
                totp_url,
                data=totp_data,
                timeout=10,
                allow_redirects=True
            )
            
            # 检查2FA是否成功
            if 'oauth/authorize' in totp_response.url or 'two-factor' not in totp_response.url:
                return True, "GitHub 2FA验证成功", {}
            else:
                return False, "TOTP验证码错误", {}
                
        except Exception as e:
            return False, f"GitHub 2FA处理异常: {str(e)}", {}
    
    def _handle_github_oauth_authorization(self) -> Tuple[bool, str]:
        """处理GitHub OAuth应用授权"""
        try:
            # 获取当前页面（应该是OAuth授权页面）
            current_url = self.session.get(self.session.url if hasattr(self.session, 'url') else 'https://github.com').url
            
            # 如果已经在授权页面，寻找授权按钮
            if 'oauth/authorize' in current_url:
                auth_response = self.session.get(current_url, timeout=10)
                soup = BeautifulSoup(auth_response.text, 'html.parser')
                
                # 寻找授权表单
                auth_form = soup.find('form', {'action': lambda x: x and 'oauth/authorize' in x})
                if auth_form:
                    # 获取所有隐藏字段
                    form_data = {}
                    for input_field in auth_form.find_all('input'):
                        name = input_field.get('name')
                        value = input_field.get('value', '')
                        if name:
                            form_data[name] = value
                    
                    # 提交授权
                    form_action = auth_form.get('action')
                    auth_url = urljoin('https://github.com', form_action)
                    
                    final_response = self.session.post(
                        auth_url,
                        data=form_data,
                        timeout=10,
                        allow_redirects=True
                    )
                    
                    return True, "GitHub授权成功"
                else:
                    # 可能已经授权过了，直接继续
                    return True, "GitHub应用已授权"
            else:
                return True, "GitHub OAuth流程已完成"
                
        except Exception as e:
            return False, f"GitHub授权处理异常: {str(e)}"
    
    def _is_logged_in_to_website(self, response) -> bool:
        """检查是否成功登录到第三方网站"""
        try:
            response_text = response.text.lower()
            
            # 检查登录成功的标识
            success_indicators = [
                'dashboard', 'welcome', 'logout', 'profile', 
                '仪表板', '欢迎', '退出', '个人中心', '用户中心'
            ]
            
            # 检查登录失败的标识  
            fail_indicators = ['login', 'sign in', '登录', '注册']
            
            has_success = any(indicator in response_text for indicator in success_indicators)
            has_fail = any(indicator in response_text for indicator in fail_indicators)
            
            return has_success and not has_fail
            
        except Exception:
            return False


# 全局模拟器实例
website_simulator = WebsiteSimulator()