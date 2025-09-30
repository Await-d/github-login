#!/usr/bin/env python3
"""
基于Selenium无头浏览器的网站自动化模拟器
用于处理JavaScript反爬虫保护和OAuth登录流程
"""

import time
import pyotp
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse, urljoin

# 导入余额提取器
try:
    from .balance_extractor import BalanceExtractor
except ImportError:
    from balance_extractor import BalanceExtractor

# 条件导入依赖
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

class BrowserSimulator:
    """基于Selenium的浏览器自动化模拟器"""
    
    def __init__(self, browser_type: str = "chrome", headless: bool = True, enable_screenshots: bool = False):
        """
        初始化浏览器模拟器
        
        Args:
            browser_type: 浏览器类型 ("chrome" 或 "firefox")
            headless: 是否使用无头模式
            enable_screenshots: 是否启用截图功能（默认关闭以提高性能）
        """
        if not HAS_SELENIUM:
            raise ImportError("缺少Selenium依赖，请安装: pip install selenium webdriver-manager")
        
        self.browser_type = browser_type
        self.headless = headless
        self.driver = None
        self.enable_screenshots = enable_screenshots  # 新增：截图控制开关
        
        # 设置截图目录
        if self.enable_screenshots:
            self.screenshot_dir = "backend/screenshots"
            self._setup_screenshot_dir()
        else:
            self.screenshot_dir = None
        
        self._setup_driver()
    
    def _setup_screenshot_dir(self):
        """设置截图目录"""
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            print(f"📁 创建截图目录: {self.screenshot_dir}")
        else:
            print(f"📁 使用截图目录: {self.screenshot_dir}")
    
    def take_screenshot(self, step_name: str, description: str = "") -> str:
        """
        截取当前页面截图
        
        Args:
            step_name: 步骤名称，用于文件命名
            description: 截图描述
            
        Returns:
            截图文件路径
        """
        # 如果截图功能被禁用，直接返回空字符串
        if not self.enable_screenshots or not self.screenshot_dir:
            return ""
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{step_name}.png"
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            
            # 截图
            self.driver.save_screenshot(screenshot_path)
            
            # 获取当前URL和页面标题
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            print(f"📸 截图已保存: {screenshot_path}")
            print(f"   描述: {description}")
            print(f"   URL: {current_url}")
            print(f"   标题: {page_title}")
            
            return screenshot_path
            
        except Exception as e:
            print(f"❌ 截图失败: {e}")
            return ""
    
    def _setup_driver(self):
        """设置WebDriver"""
        try:
            if self.browser_type.lower() == "chrome":
                self._setup_chrome_driver()
            elif self.browser_type.lower() == "firefox":
                self._setup_firefox_driver()
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
                
            print(f"✅ {self.browser_type.title()} WebDriver 初始化成功")
            
        except Exception as e:
            print(f"❌ WebDriver 初始化失败: {e}")
            raise
    
    def _setup_chrome_driver(self):
        """设置Chrome WebDriver"""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        # 反检测选项
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        # 反爬虫检测
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 用户代理
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 窗口大小
        options.add_argument("--window-size=1920,1080")
        
        # 解决用户数据目录冲突 - 使用更安全的临时目录
        import tempfile
        import uuid
        import shutil
        
        # 清理可能存在的旧临时目录
        temp_base_dir = tempfile.gettempdir()
        old_chrome_dirs = [d for d in os.listdir(temp_base_dir) if d.startswith('chrome_selenium_')]
        for old_dir in old_chrome_dirs:
            old_path = os.path.join(temp_base_dir, old_dir)
            try:
                shutil.rmtree(old_path, ignore_errors=True)
            except:
                pass
        
        # 创建新的唯一用户数据目录
        user_data_dir = os.path.join(temp_base_dir, f"chrome_selenium_{uuid.uuid4().hex}_{int(time.time())}")
        os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # 增强弹出窗口配置（关键修复！）
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor,TranslateUI,BlinkGenPropertyTrees")
        
        # 专门针对OAuth弹出窗口的配置
        options.add_argument("--disable-extensions-except=''")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-javascript-harmony-shipping")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-background-networking")
        
        # 强制允许特定操作
        options.add_argument("--allow-insecure-localhost")
        options.add_argument("--allow-cross-origin-auth-prompt")
        options.add_argument("--disable-site-isolation-trials")
        
        # OAuth和GitHub专用弹出窗口配置
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-domain-reliability")
        options.add_argument("--disable-component-extensions-with-background-pages")
        
        # 预设允许的弹出窗口域名
        allowed_popup_domains = [
            "github.com",
            "*.github.com", 
            "anyrouter.top",
            "*.anyrouter.top",
            "localhost",
            "127.0.0.1"
        ]
        
        # 添加弹出窗口白名单
        popup_whitelist = ",".join(allowed_popup_domains)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.popups": 1,
            "profile.managed_default_content_settings.popups": 1,
            "profile.content_settings.exceptions.popups": {
                "https://github.com,*": {"setting": 1},
                "https://*.github.com,*": {"setting": 1},
                "https://anyrouter.top,*": {"setting": 1},
                "https://*.anyrouter.top,*": {"setting": 1}
            }
        })
        
        try:
            # 优先使用系统安装的 chromedriver
            chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

            if os.path.exists(chromedriver_path):
                print(f"✅ 使用系统 ChromeDriver: {chromedriver_path}")
                service = ChromeService(executable_path=chromedriver_path)
            else:
                print("⚠️ 系统 ChromeDriver 不存在，使用 webdriver-manager 下载")
                service = ChromeService(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=options)

            # 执行JavaScript来隐藏webdriver属性
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        except Exception as e:
            print(f"Chrome driver设置失败: {e}")
            raise
    
    def _setup_firefox_driver(self):
        """设置Firefox WebDriver"""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Firefox特定选项
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference('useAutomationExtension', False)
        options.set_preference("general.useragent.override", 
                             "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0")
        
        try:
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
            
        except Exception as e:
            print(f"Firefox driver设置失败: {e}")
            raise
    
    def wait_and_find_element(self, by, value: str, timeout: int = 10) -> Optional[object]:
        """等待并查找元素"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def wait_and_find_clickable_element(self, by, value: str, timeout: int = 10) -> Optional[object]:
        """等待并查找可点击的元素"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def _wait_for_network_idle(self, timeout=30):
        """等待网络空闲 - 模拟Playwright的networkidle行为"""
        try:
            print("⏳ 等待网络活动减少...")
            
            # 监控网络请求
            stable_count = 0
            required_stable_seconds = 3  # 需要3秒没有新请求
            
            for i in range(timeout):
                time.sleep(1)
                
                # 检查是否有活跃的网络请求
                try:
                    # 获取性能日志
                    logs = self.driver.get_log('performance')
                    recent_requests = 0
                    
                    current_time = time.time() * 1000  # 转换为毫秒
                    
                    for log in logs[-10:]:  # 检查最近10个日志
                        try:
                            message = json.loads(log.get('message', '{}'))
                            timestamp = message.get('params', {}).get('timestamp', 0) * 1000
                            
                            # 如果是最近1秒内的网络请求
                            if current_time - timestamp < 1000:
                                if message.get('method') in ['Network.requestWillBeSent', 'Network.responseReceived']:
                                    recent_requests += 1
                        except:
                            continue
                    
                    if recent_requests == 0:
                        stable_count += 1
                        if stable_count >= required_stable_seconds:
                            print(f"✅ 网络空闲检测完成 ({stable_count}秒稳定)")
                            return True
                    else:
                        stable_count = 0
                        
                except Exception as e:
                    # 如果无法获取性能日志，使用简单的延迟
                    time.sleep(0.5)
                    stable_count += 1
                    if stable_count >= required_stable_seconds * 2:
                        return True
            
            print(f"⚠️ 网络空闲等待超时，继续执行")
            return True
            
        except Exception as e:
            print(f"⚠️ 网络空闲检测失败: {e}")
            return True

    def safe_click(self, element) -> bool:
        """增强的安全点击元素 - 支持React组件"""
        try:
            print("🎯 执行增强的元素点击...")
            
            # 步骤1: 确保元素在视图中并获得焦点
            self.driver.execute_script("""
                var element = arguments[0];
                element.scrollIntoView({behavior: 'smooth', block: 'center'});
                element.focus();
            """, element)
            time.sleep(0.3)
            
            # 步骤2: 检查是否为React组件
            is_react_component = self.driver.execute_script("""
                var button = arguments[0];
                
                // 查找React fiber节点
                var fiberKey = Object.keys(button).find(key => 
                    key.startsWith('__reactFiber') || key.startsWith('__reactInternalInstance')
                );
                
                if (fiberKey) {
                    var fiber = button[fiberKey];
                    // 检查是否有React onClick处理器
                    if (fiber.memoizedProps && fiber.memoizedProps.onClick) {
                        return true;
                    }
                }
                return false;
            """, element)
            
            if is_react_component:
                print("🔬 检测到React组件，使用React专用触发方法")
                
                # React专用方法: 直接调用React onClick处理器（最有效的方法）
                try:
                    onclick_result = self.driver.execute_script("""
                        var button = arguments[0];
                        var fiberKey = Object.keys(button).find(key => 
                            key.startsWith('__reactFiber') || key.startsWith('__reactInternalInstance')
                        );
                        
                        if (fiberKey) {
                            var fiber = button[fiberKey];
                            if (fiber.memoizedProps && fiber.memoizedProps.onClick) {
                                try {
                                    console.log('直接调用React onClick处理器');
                                    
                                    // 创建模拟事件对象
                                    var mockEvent = {
                                        type: 'click',
                                        target: button,
                                        currentTarget: button,
                                        preventDefault: function() { console.log('preventDefault called'); },
                                        stopPropagation: function() { console.log('stopPropagation called'); }
                                    };
                                    
                                    // 直接调用React onClick处理器
                                    var result = fiber.memoizedProps.onClick.call(button, mockEvent);
                                    console.log('React onClick处理器调用完成');
                                    
                                    return {success: true, result: result};
                                } catch (e) {
                                    console.error('React onClick处理器调用失败:', e);
                                    return {success: false, error: e.message, stack: e.stack};
                                }
                            }
                        }
                        
                        return {success: false, error: 'No React onClick handler found'};
                    """, element)
                    
                    if onclick_result.get('success'):
                        print("✅ React onClick处理器直接调用成功")
                        return True
                    else:
                        print(f"⚠️ React onClick直接调用失败: {onclick_result.get('error', 'Unknown error')}")
                        # 继续尝试其他方法
                    
                except Exception as e_react:
                    print(f"⚠️ React SyntheticEvent失败: {e_react}")
                    # 继续尝试其他方法
            
            # 步骤3: 设置用户交互状态
            self.driver.execute_script("""
                // 确保页面可见性状态正确
                Object.defineProperty(document, 'visibilityState', {
                    value: 'visible',
                    writable: false
                });
                
                // 触发焦点事件
                window.focus();
                document.body.focus();
                
                // 设置准备状态
                window.__enhanced_click_ready = true;
            """)
            
            # 步骤4: 尝试Actions链式点击（最接近Playwright）
            try:
                from selenium.webdriver import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.pause(0.1)
                actions.click(element)
                actions.perform()
                print("✅ Actions链式点击成功")
                return True
                
            except Exception as e1:
                print(f"⚠️ Actions点击失败: {e1}")
                
                # 步骤5: JavaScript增强点击事件
                try:
                    self.driver.execute_script("""
                        var element = arguments[0];
                        
                        // 获取元素位置
                        var rect = element.getBoundingClientRect();
                        var centerX = rect.left + rect.width / 2;
                        var centerY = rect.top + rect.height / 2;
                        
                        // 创建完整的鼠标事件序列
                        var events = [
                            new MouseEvent('mouseenter', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: centerX, clientY: centerY
                            }),
                            new MouseEvent('mouseover', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: centerX, clientY: centerY
                            }),
                            new MouseEvent('mousedown', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: centerX, clientY: centerY, button: 0, buttons: 1
                            }),
                            new FocusEvent('focus', { bubbles: true }),
                            new MouseEvent('mouseup', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: centerX, clientY: centerY, button: 0, buttons: 0
                            }),
                            new MouseEvent('click', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: centerX, clientY: centerY, button: 0, buttons: 0, detail: 1
                            })
                        ];
                        
                        // 依次触发事件
                        for (var i = 0; i < events.length; i++) {
                            element.dispatchEvent(events[i]);
                        }
                        
                        console.log('Enhanced JavaScript click completed');
                    """, element)
                    print("✅ JavaScript增强点击成功")
                    return True
                    
                except Exception as e2:
                    print(f"⚠️ JavaScript增强点击失败: {e2}")
                    
                    # 步骤6: 标准点击作为后备
                    try:
                        element.click()
                        print("✅ 标准点击成功")
                        return True
                    except Exception as e3:
                        print(f"❌ 所有点击方法都失败: {e3}")
                        return False
                        
        except Exception as e:
            print(f"❌ 安全点击处理异常: {e}")
            return False
    
    def handle_github_oauth_flow(self) -> Tuple[bool, str]:
        """
        处理GitHub OAuth登录流程的完整解决方案
        基于综合测试中发现的成功方法
        
        Returns:
            (是否成功, 详细信息)
        """
        try:
            print("🚀 开始GitHub OAuth流程处理")
            
            # 步骤1: 截图记录初始状态
            self.take_screenshot("01_oauth_flow_start", "开始GitHub OAuth流程处理")
            
            # 步骤2: 关闭模态框
            print("🎭 处理可能存在的模态框...")
            self._close_modals_if_present()
            
            # 步骤2a: 关闭模态框后截图
            self.take_screenshot("02_after_close_modals", "关闭模态框后的状态")
            
            # 步骤3: 刷新页面使GitHub按钮可见
            print("🔄 刷新页面使GitHub按钮可见")
            self.driver.refresh()
            time.sleep(8)  # 等待页面完全加载
            
            # 步骤3a: 刷新页面后截图
            self.take_screenshot("03_after_page_refresh", "刷新页面后等待GitHub按钮")
            
            # 步骤3: 查找GitHub按钮
            print("🔍 查找GitHub按钮")
            github_element = self.driver.execute_script("""
                var buttons = document.querySelectorAll('button, [role="button"]');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var text = (btn.textContent || btn.innerText || '').toLowerCase();
                    if (text.includes('github') && btn.offsetParent !== null && !btn.disabled) {
                        return btn;
                    }
                }
                return null;
            """)
            
            if not github_element:
                return False, "未找到可点击的GitHub按钮"
            
            # 获取按钮文本
            button_text = self.driver.execute_script("return arguments[0].textContent.trim();", github_element)
            print(f"🎯 找到GitHub按钮: '{button_text}'")
            
            # 步骤4: 找到GitHub按钮后截图
            self.take_screenshot("04_github_button_found", f"找到GitHub按钮: {button_text}")
            
            # 步骤4: 记录点击前的窗口状态
            handles_before = self.driver.window_handles
            print(f"📊 点击前窗口数: {len(handles_before)}")
            
            # 步骤5: 执行点击操作（使用增强的safe_click方法）
            print("🖱️ 执行GitHub按钮点击")
            click_success = self.safe_click(github_element)
            
            if not click_success:
                return False, "GitHub按钮点击失败"
            
            # 步骤5a: 点击GitHub按钮后截图
            self.take_screenshot("05_after_github_click", "点击GitHub按钮后的状态")
            
            # 步骤6: 等待并检测新窗口
            print("⏳ 等待OAuth新窗口打开...")
            time.sleep(5)  # 给OAuth窗口足够的打开时间
            
            handles_after = self.driver.window_handles
            print(f"📊 点击后窗口数: {len(handles_after)}")
            
            if len(handles_after) > len(handles_before):
                # 检查新窗口
                new_handles = [h for h in handles_after if h not in handles_before]
                self.driver.switch_to.window(new_handles[0])
                new_url = self.driver.current_url
                new_title = self.driver.title
                
                print(f"🆕 新窗口URL: {new_url}")
                print(f"🆕 新窗口标题: {new_title}")
                
                # 步骤6: 新窗口打开后截图
                self.take_screenshot("06_new_oauth_window", f"GitHub OAuth新窗口已打开: {new_title}")
                
                if 'github.com' in new_url:
                    return True, f"成功打开GitHub OAuth页面: {new_url}"
                else:
                    return True, f"打开了新窗口，但不是GitHub页面: {new_url}"
            else:
                return False, "没有检测到新窗口打开"
                
        except Exception as e:
            error_msg = f"GitHub OAuth流程处理异常: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def perform_github_login_in_oauth_window(self, username: str, password: str, totp_secret: str) -> Tuple[bool, str, Dict]:
        """
        在GitHub OAuth窗口中执行登录
        这是对handle_github_oauth_flow的补充，处理实际的GitHub登录过程
        
        Args:
            username: GitHub用户名
            password: GitHub密码
            totp_secret: TOTP密钥
            
        Returns:
            (是否成功, 消息, 会话数据)
        """
        try:
            print("🔐 在GitHub OAuth窗口中执行登录")
            
            # 确保我们在GitHub登录页面
            current_url = self.driver.current_url
            if 'github.com' not in current_url:
                return False, f"当前不在GitHub页面: {current_url}", {}
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 查找用户名输入框
            username_selectors = [
                "input[name='login']",
                "input[id='login_field']", 
                "input[type='text'][name='login']",
                "input[type='email']"
            ]
            
            username_element = None
            for selector in username_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            username_element = elem
                            break
                    if username_element:
                        break
                except:
                    continue
            
            if not username_element:
                return False, "未找到GitHub用户名输入框", {}
            
            # 输入用户名
            print(f"📝 输入用户名: {username}")
            username_element.clear()
            username_element.send_keys(username)
            time.sleep(1)
            
            # 查找密码输入框
            password_element = None
            try:
                password_element = self.driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password']")
                if not (password_element.is_displayed() and password_element.is_enabled()):
                    password_element = None
            except:
                pass
            
            if not password_element:
                return False, "未找到GitHub密码输入框", {}
            
            # 输入密码
            print("🔑 输入密码")
            password_element.clear()
            password_element.send_keys(password)
            time.sleep(1)
            
            # 查找并点击登录按钮
            login_button = None
            login_button_selectors = [
                "input[type='submit'][value*='Sign in']",
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Sign in')"
            ]
            
            for selector in login_button_selectors:
                try:
                    if selector.startswith("button:contains"):
                        # 使用XPath查找包含特定文本的按钮
                        elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign in')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            login_button = elem
                            break
                    if login_button:
                        break
                except:
                    continue
            
            if not login_button:
                return False, "未找到GitHub登录按钮", {}
            
            print("🖱️ 点击登录按钮")
            self.safe_click(login_button)
            
            # 等待登录响应
            time.sleep(5)
            
            # 检查是否需要2FA验证
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            if 'two-factor' in current_url or 'two_factor' in current_url or '2fa' in page_source:
                print("🔐 检测到2FA验证要求")
                
                if not totp_secret:
                    return False, "需要2FA验证但未提供TOTP密钥", {}
                
                # 生成TOTP验证码
                try:
                    import pyotp
                    totp = pyotp.TOTP(totp_secret)
                    verification_code = totp.now()
                    print(f"🔑 生成2FA验证码: {verification_code}")
                except Exception as e:
                    return False, f"生成2FA验证码失败: {str(e)}", {}
                
                # 检查是否在WebAuthn页面，需要切换到TOTP
                if 'webauthn' in current_url or 'webauthn' in page_source.lower():
                    print("🔍 检测到WebAuthn页面，尝试切换到TOTP验证...")
                    
                    # 方法1：尝试直接访问authenticator app页面
                    try:
                        base_url = "https://github.com"
                        totp_url = f"{base_url}/sessions/two-factor/app"
                        print(f"🔄 直接访问TOTP页面: {totp_url}")
                        self.driver.get(totp_url)
                        time.sleep(3)
                        
                        # 更新页面信息
                        current_url = self.driver.current_url
                        page_source = self.driver.page_source.lower()
                        print(f"🔍 切换后当前URL: {current_url}")
                        
                    except Exception as e:
                        print(f"⚠️ 直接访问TOTP页面失败: {e}")
                        
                        # 方法2：尝试点击"More options"和"Authenticator app"
                        try:
                            print("🔄 尝试点击More options按钮...")
                            more_options_selectors = [
                                "button.more-options-two-factor",
                                "button[class*='more-options']",
                                "button:contains('More options')"
                            ]
                            
                            more_options_clicked = False
                            for selector in more_options_selectors:
                                try:
                                    if selector.startswith("button:contains"):
                                        # 使用XPath查找包含特定文本的按钮
                                        elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'More options')]")
                                    else:
                                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    
                                    for elem in elements:
                                        if elem.is_displayed() and elem.is_enabled():
                                            print(f"🎯 点击More options按钮: {selector}")
                                            self.safe_click(elem)
                                            time.sleep(2)
                                            more_options_clicked = True
                                            break
                                    if more_options_clicked:
                                        break
                                except:
                                    continue
                            
                            if more_options_clicked:
                                print("🔍 查找Authenticator app链接...")
                                app_link_selectors = [
                                    "a[href='/sessions/two-factor/app']",
                                    "a[data-test-selector='totp-app-link']",
                                    "a:contains('Authenticator app')"
                                ]
                                
                                for selector in app_link_selectors:
                                    try:
                                        if selector.startswith("a:contains"):
                                            elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Authenticator app')]")
                                        else:
                                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                        
                                        for elem in elements:
                                            if elem.is_displayed() and elem.is_enabled():
                                                print(f"🎯 点击Authenticator app链接: {selector}")
                                                self.safe_click(elem)
                                                time.sleep(3)
                                                
                                                # 更新页面信息
                                                current_url = self.driver.current_url
                                                page_source = self.driver.page_source.lower()
                                                print(f"🔍 切换后当前URL: {current_url}")
                                                break
                                        break
                                    except:
                                        continue
                        except Exception as e2:
                            print(f"⚠️ 点击More options方法失败: {e2}")
                
                # 查找验证码输入框 - 增强版选择器
                totp_element = None
                totp_selectors = [
                    "input[name='otp']",
                    "input[autocomplete='one-time-code']", 
                    "input[type='text'][autocomplete*='code']",
                    "input[id='otp']",
                    "input[class*='otp']",
                    "input[class*='two-factor']",
                    "input[class*='2fa']", 
                    "input[placeholder*='code']",
                    "input[placeholder*='verification']",
                    "input[type='text'][maxlength='6']",
                    "input[type='text'][pattern*='[0-9]']",
                    "input[data-testid*='otp']",
                    "input[aria-label*='code']",
                    "input[aria-label*='verification']",
                    "input[name='app_otp']",  # GitHub特定
                    "input[name='sms_otp']",  # GitHub SMS选项
                    "input[id='app_totp']",   # GitHub TOTP应用
                    "input[class*='form-control'][maxlength='6']",  # GitHub表单控件
                    "input[type='tel'][maxlength='6']",  # 电话号码类型输入框
                    "input[inputmode='numeric'][maxlength='6']"  # 数字输入模式
                ]
                
                print("🔍 搜索2FA验证码输入框...")
                
                # 等待2FA页面完全加载
                time.sleep(3)
                
                # 调试：分析页面中的所有输入框
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                print(f"📋 页面中发现 {len(all_inputs)} 个输入框")
                
                for i, input_elem in enumerate(all_inputs[:10]):  # 只显示前10个
                    try:
                        input_type = input_elem.get_attribute("type") or "text"
                        input_name = input_elem.get_attribute("name") or ""
                        input_id = input_elem.get_attribute("id") or ""
                        input_class = input_elem.get_attribute("class") or ""
                        input_placeholder = input_elem.get_attribute("placeholder") or ""
                        is_visible = input_elem.is_displayed()
                        is_enabled = input_elem.is_enabled()
                        
                        print(f"   输入框{i+1}: type={input_type}, name={input_name}, id={input_id}, visible={is_visible}, enabled={is_enabled}")
                        if input_class: print(f"      class={input_class}")
                        if input_placeholder: print(f"      placeholder={input_placeholder}")
                    except:
                        continue
                
                # 尝试每个选择器
                for i, selector in enumerate(totp_selectors):
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        print(f"🧪 测试选择器 {i+1}/{len(totp_selectors)}: {selector} - 找到{len(elements)}个元素")
                        
                        for j, elem in enumerate(elements):
                            try:
                                if elem.is_displayed() and elem.is_enabled():
                                    totp_element = elem
                                    print(f"✅ 选择器 '{selector}' 匹配成功 (元素{j+1})")
                                    break
                                else:
                                    print(f"   元素{j+1}: displayed={elem.is_displayed()}, enabled={elem.is_enabled()}")
                            except Exception as e:
                                print(f"   元素{j+1}检查失败: {e}")
                        
                        if totp_element:
                            break
                    except Exception as e:
                        print(f"❌ 选择器 '{selector}' 测试失败: {e}")
                        continue
                
                if not totp_element:
                    # 尝试通用方法：查找所有可能是验证码输入框的元素
                    print("🔍 尝试通用方法查找2FA输入框...")
                    
                    possible_inputs = self.driver.find_elements(By.XPATH, 
                        "//input[@type='text' or @type='tel' or @type='number']")
                    
                    for input_elem in possible_inputs:
                        try:
                            if not (input_elem.is_displayed() and input_elem.is_enabled()):
                                continue
                                
                            # 检查各种属性是否表明这是2FA输入框
                            attrs = {
                                'name': input_elem.get_attribute("name") or "",
                                'id': input_elem.get_attribute("id") or "", 
                                'class': input_elem.get_attribute("class") or "",
                                'placeholder': input_elem.get_attribute("placeholder") or "",
                                'maxlength': input_elem.get_attribute("maxlength") or "",
                                'pattern': input_elem.get_attribute("pattern") or "",
                                'autocomplete': input_elem.get_attribute("autocomplete") or ""
                            }
                            
                            # 检查是否包含2FA相关关键词
                            all_attrs = " ".join(attrs.values()).lower()
                            keywords = ['otp', '2fa', 'totp', 'code', 'verification', 'two-factor', 'app_otp', 'sms_otp']
                            
                            if any(keyword in all_attrs for keyword in keywords) or attrs['maxlength'] == '6':
                                totp_element = input_elem
                                print(f"✅ 通用方法找到可能的2FA输入框: {attrs}")
                                break
                                
                        except Exception as e:
                            continue
                
                if not totp_element:
                    # 最后尝试：保存页面源码用于调试
                    with open("debug_2fa_failed.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print("💾 2FA页面源码已保存到 debug_2fa_failed.html 用于调试")
                    return False, "未找到2FA验证码输入框", {}
                
                # 输入验证码
                print("📱 输入2FA验证码")
                totp_element.clear()
                totp_element.send_keys(verification_code)
                time.sleep(1)
                
                # 查找并点击验证按钮
                verify_button = None
                
                # 方法1: 使用JavaScript查找按钮（最可靠）
                try:
                    verify_button = self.driver.execute_script("""
                        var buttons = document.querySelectorAll('button, input[type="submit"]');
                        for (var i = 0; i < buttons.length; i++) {
                            var btn = buttons[i];
                            var text = (btn.textContent || btn.innerText || btn.value || '').trim().toLowerCase();
                            if ((text.includes('verify') || text.includes('submit') || text.includes('continue')) 
                                && btn.offsetParent !== null) {
                                return btn;
                            }
                        }
                        return null;
                    """)
                    if verify_button:
                        print("✅ 找到2FA验证按钮 (JavaScript)")
                except Exception as e:
                    print(f"⚠️ JavaScript查找失败: {str(e)[:50]}")
                
                # 方法2: 如果JavaScript失败，使用传统选择器
                if not verify_button:
                    verify_selectors = [
                        "button[type='submit']",
                        "input[type='submit']",
                        "button:contains('Verify')",
                        "button:contains('Submit')", 
                        "button:contains('Continue')",
                        "input[value*='Verify']",
                        "button.btn-primary",
                        "button[class*='btn-primary']"
                    ]
                    
                    for selector in verify_selectors:
                        try:
                            if ':contains(' in selector:
                                # 使用XPath处理包含文本的选择器
                                text = selector.split("'")[1]
                                xpath_selector = f"//button[contains(text(),'{text}')]"
                                elements = self.driver.find_elements(By.XPATH, xpath_selector)
                            else:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                
                            for elem in elements:
                                if elem.is_displayed() and elem.is_enabled():
                                    verify_button = elem
                                    print(f"✅ 找到2FA验证按钮: {selector}")
                                    break
                            if verify_button:
                                break
                        except Exception as e:
                            # 只打印非预期的错误
                            if "invalid selector" not in str(e).lower() and "xpath" not in str(e).lower():
                                print(f"⚠️ 选择器测试失败 '{selector}'")
                            continue
                
                if verify_button:
                    print("✅ 点击2FA验证按钮")
                    self.safe_click(verify_button)
                    time.sleep(5)
                else:
                    print("⚠️ 未找到2FA验证按钮，但验证码已输入，等待页面自动处理")
                    time.sleep(5)
            
            # 等待OAuth授权页面或重定向
            print("⏳ 等待OAuth授权或重定向...")
            time.sleep(8)
            
            current_url = self.driver.current_url
            print(f"🔍 登录后当前URL: {current_url}")
            
            # 检查登录是否成功
            if 'github.com' in current_url:
                if '/login' in current_url:
                    # 仍在登录页面，说明登录失败
                    return False, "GitHub登录失败，仍在登录页面", {}
                elif 'oauth/authorize' in current_url or 'authorize' in current_url:
                    # 到达OAuth授权页面
                    print("✅ 成功到达OAuth授权页面")
                    
                    # 查找授权按钮并点击
                    authorize_button = None
                    authorize_selectors = [
                        "button[type='submit'][name='authorize']",
                        "input[type='submit'][value*='Authorize']",
                        "button:contains('Authorize')"
                    ]
                    
                    for selector in authorize_selectors:
                        try:
                            if "contains" in selector:
                                elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Authorize')]")
                            else:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            for elem in elements:
                                if elem.is_displayed() and elem.is_enabled():
                                    authorize_button = elem
                                    break
                            if authorize_button:
                                break
                        except:
                            continue
                    
                    if authorize_button:
                        print("🚀 点击OAuth授权按钮")
                        self.safe_click(authorize_button)
                        time.sleep(5)
                    else:
                        print("ℹ️ 未找到明显的授权按钮，可能已自动授权")
                    
                    # 等待重定向回原网站
                    print("⏳ 等待重定向回原网站...")
                    for i in range(30):  # 等待30秒
                        time.sleep(1)
                        current_url = self.driver.current_url
                        
                        if 'github.com' not in current_url:
                            print(f"✅ 成功重定向回原网站: {current_url}")
                            
                            # 收集会话数据
                            session_data = {
                                "final_url": current_url,
                                "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                "login_time": datetime.now().isoformat(),
                                "oauth_completed": True
                            }
                            
                            # 检查是否成功登录（不在登录页面）
                            if '/login' not in current_url:
                                return True, "GitHub OAuth登录成功", session_data
                            else:
                                return False, "OAuth完成但仍在登录页面", session_data
                    
                    return False, "OAuth授权后未成功重定向", {}
                elif '/settings/two_factor_checkup' in current_url or '/settings' in current_url:
                    # 在2FA设置检查页面，这是正常的中间步骤
                    print("🔍 检测到GitHub 2FA设置检查页面，等待自动重定向...")
                    
                    # 步骤7: 2FA设置检查页面截图 - 这是关键问题所在！
                    self.take_screenshot("07_2fa_checkup_page", "到达GitHub 2FA设置检查页面 - 需要分析此页面")
                    
                    # 首先尝试主动跳过2FA设置检查
                    print("🔧 尝试主动跳过2FA设置检查...")
                    try:
                        # 查找跳过、继续或完成按钮
                        skip_selectors = [
                            "button:contains('Skip')",
                            "a:contains('Skip')", 
                            "button:contains('Continue')",
                            "a:contains('Continue')",
                            "button:contains('Done')",
                            "a:contains('Done')",
                            "button:contains('Skip for now')",
                            "a:contains('Skip for now')",
                            ".btn-outline",
                            "[data-ga-click*='skip']",
                            "[href*='skip']"
                        ]
                        
                        skip_button = None
                        for selector in skip_selectors:
                            try:
                                if ':contains(' in selector:
                                    # 使用xpath处理contains
                                    text = selector.split("'")[1]
                                    if selector.startswith('button'):
                                        xpath_selector = f"//button[contains(text(),'{text}')]"
                                    else:
                                        xpath_selector = f"//a[contains(text(),'{text}')]"
                                    elements = self.driver.find_elements(By.XPATH, xpath_selector)
                                else:
                                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    
                                if elements and elements[0].is_displayed():
                                    skip_button = elements[0]
                                    print(f"✅ 找到跳过按钮: {selector}")
                                    break
                            except:
                                continue
                        
                        if skip_button:
                            # 步骤7a: 找到跳过按钮后截图
                            self.take_screenshot("07a_skip_button_found", "找到2FA设置检查跳过按钮")
                            
                            print("🖱️ 点击跳过2FA设置检查")
                            skip_button.click()
                            time.sleep(3)
                            
                            # 步骤7b: 点击跳过按钮后截图
                            self.take_screenshot("07b_after_skip_click", "点击跳过2FA设置检查后")
                            
                            current_url = self.driver.current_url
                            if 'github.com' not in current_url:
                                print(f"✅ 成功跳过2FA检查，重定向到: {current_url}")
                                
                                # 步骤8: 成功跳过2FA后截图
                                self.take_screenshot("08_skip_2fa_success", f"成功跳过2FA设置检查，重定向到: {current_url}")
                                session_data = {
                                    "final_url": current_url,
                                    "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                    "login_time": datetime.now().isoformat(),
                                    "oauth_completed": True,
                                    "via_2fa_skip": True
                                }
                                return True, "跳过2FA设置检查成功", session_data
                            else:
                                print(f"⚠️ 点击跳过后仍在GitHub: {current_url}")
                        else:
                            print("⚠️ 未找到跳过按钮，分析页面内容...")
                            
                            # 步骤7c: 未找到跳过按钮时的页面分析截图
                            self.take_screenshot("07c_no_skip_button_analysis", "未找到跳过按钮，进行页面分析")
                            
                            # 分析页面内容，查找可能的操作元素
                            try:
                                page_source = self.driver.page_source
                                print(f"📄 页面内容长度: {len(page_source)} 字符")
                                
                                # 查找所有可点击元素
                                clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='submit'], input[type='button']")
                                print(f"🔘 找到 {len(clickable_elements)} 个可点击元素")
                                
                                for i, element in enumerate(clickable_elements[:10]):  # 只检查前10个
                                    try:
                                        if element.is_displayed():
                                            text = element.text.strip()
                                            tag = element.tag_name
                                            classes = element.get_attribute('class') or ''
                                            href = element.get_attribute('href') or ''
                                            print(f"  {i+1}. {tag}: '{text}' class='{classes}' href='{href}'")
                                    except:
                                        continue
                                
                                # 查找可能的继续按钮或链接
                                continue_patterns = [
                                    'continue', 'proceed', 'next', 'done', 'skip', 'finish', 
                                    'later', 'remind', 'maybe', 'not now', 'cancel'
                                ]
                                
                                for element in clickable_elements:
                                    try:
                                        if not element.is_displayed():
                                            continue
                                            
                                        text = (element.text or '').lower()
                                        href = (element.get_attribute('href') or '').lower()
                                        classes = (element.get_attribute('class') or '').lower()
                                        
                                        for pattern in continue_patterns:
                                            if pattern in text or pattern in href or pattern in classes:
                                                print(f"🎯 找到可能的继续元素: '{element.text}' (匹配: {pattern})")
                                                element.click()
                                                time.sleep(3)
                                                
                                                current_url = self.driver.current_url
                                                if 'github.com' not in current_url:
                                                    print(f"✅ 成功通过2FA检查页面: {current_url}")
                                                    session_data = {
                                                        "final_url": current_url,
                                                        "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                                        "login_time": datetime.now().isoformat(),
                                                        "oauth_completed": True,
                                                        "via_2fa_continue": True
                                                    }
                                                    return True, "通过2FA检查页面继续按钮成功", session_data
                                                else:
                                                    print(f"⚠️ 点击继续按钮后仍在GitHub: {current_url}")
                                                    break
                                    except:
                                        continue
                                        
                            except Exception as e:
                                print(f"⚠️ 页面分析出错: {e}")
                            
                            print("⚠️ 未找到有效的继续机制，尝试2FA验证处理...")
                            
                            # 检查是否是2FA验证页面（需要输入验证码）
                            try:
                                # 查找验证码输入框
                                verification_input = None
                                verification_selectors = [
                                    "input[placeholder*='XXX']",
                                    "input[type='text'][maxlength='6']",
                                    "input.form-control",
                                    "input[name*='otp']",
                                    "input[autocomplete*='code']"
                                ]
                                
                                for selector in verification_selectors:
                                    try:
                                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                        for elem in elements:
                                            if elem.is_displayed() and elem.is_enabled():
                                                verification_input = elem
                                                print(f"✅ 找到2FA验证输入框: {selector}")
                                                break
                                        if verification_input:
                                            break
                                    except:
                                        continue
                                
                                if verification_input:
                                    # 生成新的TOTP验证码
                                    import pyotp
                                    totp = pyotp.TOTP(totp_secret)
                                    verification_code = totp.now()
                                    print(f"🔑 生成2FA设置验证码: {verification_code}")
                                    
                                    # 输入验证码
                                    verification_input.clear()
                                    verification_input.send_keys(verification_code)
                                    print("📱 输入2FA设置验证码")
                                    
                                    # 步骤7d: 输入验证码后截图
                                    self.take_screenshot("07d_verification_code_entered", "输入2FA设置验证码")
                                    
                                    # 查找并点击验证按钮 - 使用更可靠的方法
                                    verify_button = None

                                    # 方法1: 使用JavaScript查找Verify按钮
                                    try:
                                        verify_button = self.driver.execute_script("""
                                            var buttons = document.querySelectorAll('button, input[type="submit"]');
                                            for (var i = 0; i < buttons.length; i++) {
                                                var btn = buttons[i];
                                                var text = (btn.textContent || btn.innerText || btn.value || '').trim();
                                                if (text.toLowerCase().includes('verify') && btn.offsetParent !== null) {
                                                    return btn;
                                                }
                                            }
                                            return null;
                                        """)
                                        if verify_button:
                                            print("✅ 找到验证按钮: Verify (JavaScript查找)")
                                    except Exception as e:
                                        print(f"⚠️ JavaScript查找按钮失败: {e}")

                                    # 方法2: 如果JavaScript失败，使用传统选择器
                                    if not verify_button:
                                        verify_selectors = [
                                            "//button[contains(text(), 'Verify')]",
                                            "//button[contains(., 'Verify')]",
                                            "//input[@type='submit' and contains(@value, 'Verify')]",
                                            ".btn-primary",
                                            "button.btn-primary"
                                        ]

                                        for selector in verify_selectors:
                                            try:
                                                if selector.startswith('//'):
                                                    elements = self.driver.find_elements(By.XPATH, selector)
                                                else:
                                                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                                                for elem in elements:
                                                    if elem.is_displayed() and elem.is_enabled():
                                                        verify_button = elem
                                                        print(f"✅ 找到验证按钮: {selector}")
                                                        break
                                                if verify_button:
                                                    break
                                            except:
                                                continue
                                    
                                    if verify_button:
                                        print("🖱️ 点击2FA设置验证按钮")
                                        verify_button.click()
                                        time.sleep(3)
                                        
                                        # 步骤7e: 点击验证按钮后截图
                                        self.take_screenshot("07e_after_verify_click", "点击2FA设置验证按钮后")
                                        
                                        # 等待页面响应
                                        time.sleep(2)
                                        
                                        # 检查是否出现了2FA验证成功页面（带Done按钮）
                                        current_url = self.driver.current_url
                                        page_source = self.driver.page_source.lower()
                                        
                                        if '2fa verification successful' in page_source or 'verification successful' in page_source:
                                            print("🎉 检测到2FA验证成功页面，查找Done按钮...")
                                            
                                            # 步骤7f: 2FA验证成功页面截图
                                            self.take_screenshot("07f_2fa_success_page", "2FA验证成功页面，需要点击Done按钮")
                                            
                                            # 查找Done按钮
                                            done_button = None
                                            done_selectors = [
                                                "button:contains('Done')",
                                                "input[type='submit'][value*='Done']",
                                                "button[class*='btn-primary']",
                                                "button.btn-primary",
                                                "input[value='Done']",
                                                "a:contains('Done')"
                                            ]
                                            for selector in done_selectors:
                                                try:
                                                    if ':contains(' in selector:
                                                        text = selector.split("'")[1]
                                                        if selector.startswith('button'):
                                                            xpath_selector = f"//button[contains(text(),'{text}')]"
                                                        else:
                                                            xpath_selector = f"//a[contains(text(),'{text}')]"
                                                        elements = self.driver.find_elements(By.XPATH, xpath_selector)
                                                    else:
                                                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                                        
                                                    for elem in elements:
                                                        if elem.is_displayed() and elem.is_enabled():
                                                            done_button = elem
                                                            print(f"✅ 找到Done按钮: {selector}")
                                                            break
                                                    if done_button:
                                                        break
                                                except:
                                                    continue
                                            
                                            if done_button:
                                                print("🖱️ 点击Done按钮完成2FA验证流程")
                                                done_button.click()
                                                time.sleep(3)
                                                
                                                # 步骤7g: 点击Done按钮后截图
                                                self.take_screenshot("07g_after_done_click", "点击Done按钮后")
                                                
                                                # 再次检查是否成功重定向
                                                current_url = self.driver.current_url
                                                print(f"🔍 点击Done后的URL: {current_url}")
                                            else:
                                                print("⚠️ 未找到Done按钮，尝试其他方式继续...")
                                                # 尝试按回车键
                                                try:
                                                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.RETURN)
                                                    time.sleep(2)
                                                except:
                                                    pass
                                        
                                        # 最终检查重定向结果
                                        current_url = self.driver.current_url
                                        if 'github.com' not in current_url:
                                            print(f"✅ 2FA设置验证成功，重定向到: {current_url}")
                                            
                                            # 步骤8: 2FA验证成功后截图
                                            self.take_screenshot("08_2fa_verify_success", f"2FA设置验证成功，重定向到: {current_url}")
                                            
                                            session_data = {
                                                "final_url": current_url,
                                                "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                                "login_time": datetime.now().isoformat(),
                                                "oauth_completed": True,
                                                "via_2fa_checkup": True
                                            }
                                            return True, "2FA设置验证成功", session_data
                                        else:
                                            print(f"⚠️ 验证后仍在GitHub: {current_url}")
                                    else:
                                        print("⚠️ 未找到验证按钮")
                                else:
                                    print("⚠️ 未找到2FA验证输入框")
                                    
                            except Exception as e_2fa:
                                print(f"⚠️ 2FA验证处理出错: {e_2fa}")
                            
                    except Exception as e:
                        print(f"⚠️ 跳过2FA检查处理出错: {e}")
                    
                    # 等待页面自动处理和重定向 - 最多等待20秒
                    for i in range(20):  # 等待20秒
                        time.sleep(1)
                        current_url = self.driver.current_url

                        # 每5秒输出一次等待状态
                        if i > 0 and i % 5 == 0:
                            print(f"⏳ 等待2FA设置检查自动重定向... ({i}/20秒)")
                        
                        if 'github.com' not in current_url:
                            print(f"✅ 从2FA设置页面成功重定向回原网站: {current_url}")

                            # 收集会话数据
                            session_data = {
                                "final_url": current_url,
                                "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                "login_time": datetime.now().isoformat(),
                                "oauth_completed": True,
                                "via_2fa_checkup": True
                            }

                            # 提取余额信息
                            try:
                                print("🔍 开始提取账户余额信息...")
                                balance_extractor = BalanceExtractor(self.driver)
                                balance_result = balance_extractor.extract_balance()

                                if balance_result['success']:
                                    session_data['balance'] = balance_result['balance']
                                    session_data['balance_currency'] = balance_result['currency']
                                    session_data['balance_raw_text'] = balance_result['raw_text']
                                    print(f"✅ 成功提取余额信息: {balance_result['balance']} {balance_result['currency']}")
                                else:
                                    session_data['balance'] = None
                                    session_data['balance_extraction_error'] = balance_result.get('error', '未知错误')
                                    print(f"⚠️ 余额提取失败: {balance_result.get('error', '未知错误')}")

                            except Exception as balance_error:
                                session_data['balance'] = None
                                session_data['balance_extraction_error'] = str(balance_error)
                                print(f"❌ 余额提取异常: {str(balance_error)}")

                            # 检查是否成功登录（不在登录页面）
                            if '/login' not in current_url:
                                return True, "GitHub OAuth登录成功（经由2FA设置检查）", session_data
                            else:
                                return False, "2FA设置检查完成但仍在登录页面", session_data
                        elif 'oauth/authorize' in current_url or 'authorize' in current_url:
                            # 重定向到了OAuth授权页面
                            print("✅ 从2FA设置检查重定向到OAuth授权页面")
                            break
                    
                    # 如果仍在GitHub但已进入OAuth授权流程
                    if 'oauth/authorize' in current_url or 'authorize' in current_url:
                        print("🔄 继续处理OAuth授权...")
                        # 递归调用自己来处理授权页面（通过等待处理）
                        time.sleep(2)
                        current_url = self.driver.current_url
                        # 让代码继续到OAuth授权处理部分
                    else:
                        # 最后一次尝试：主动绕过2FA设置检查
                        print("🔍 2FA设置检查等待超时，尝试主动绕过...")
                        
                        # 策略1: 尝试直接访问原始OAuth授权URL
                        try:
                            print("🚀 策略1: 尝试重新访问OAuth授权URL")
                            
                            # 从当前URL获取原始OAuth参数
                            import urllib.parse as urlparse
                            parsed = urlparse.urlparse(self.driver.current_url)
                            query_params = urlparse.parse_qs(parsed.query)
                            
                            # 查找OAuth相关参数或直接构造
                            oauth_url = "https://github.com/login/oauth/authorize"
                            if 'client_id' in query_params:
                                oauth_url += f"?client_id={query_params['client_id'][0]}&scope=user:email"
                            else:
                                # 使用anyrouter的client_id
                                oauth_url += "?client_id=Ov23liOwlnIiYoF3bUqw&scope=user:email"
                            
                            print(f"🌐 访问OAuth授权URL: {oauth_url}")
                            self.driver.get(oauth_url)
                            time.sleep(3)
                            
                            current_url = self.driver.current_url
                            print(f"🔍 OAuth重定向后URL: {current_url}")
                            
                            if 'github.com' not in current_url:
                                print("✅ 成功绕过2FA检查，直接完成OAuth!")
                                session_data = {
                                    "final_url": current_url,
                                    "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                    "login_time": datetime.now().isoformat(),
                                    "oauth_completed": True,
                                    "via_oauth_bypass": True
                                }
                                return True, "绕过2FA设置检查成功完成OAuth", session_data
                            elif 'oauth/authorize' in current_url:
                                print("🔧 到达OAuth授权页面，尝试自动授权...")
                                try:
                                    # 查找授权按钮
                                    authorize_selectors = [
                                        "button[name='authorize']",
                                        "input[name='authorize']", 
                                        "button[type='submit']",
                                        "input[value='Authorize']",
                                        "button:contains('Authorize')",
                                        ".btn-primary",
                                        "[data-octo-click='oauth_application_authorization']"
                                    ]
                                    
                                    authorize_button = None
                                    for selector in authorize_selectors:
                                        try:
                                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                            if elements and elements[0].is_displayed():
                                                authorize_button = elements[0]
                                                print(f"✅ 找到授权按钮: {selector}")
                                                break
                                        except:
                                            continue
                                    
                                    if authorize_button:
                                        print("🖱️ 点击OAuth授权按钮")
                                        authorize_button.click()
                                        time.sleep(3)
                                        
                                        # 检查是否成功跳转
                                        final_url = self.driver.current_url
                                        if 'github.com' not in final_url:
                                            print(f"✅ OAuth授权成功！重定向到: {final_url}")
                                            session_data = {
                                                "final_url": final_url,
                                                "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                                "login_time": datetime.now().isoformat(),
                                                "oauth_completed": True,
                                                "via_oauth_authorize": True
                                            }

                                            # 提取余额信息
                                            try:
                                                print("🔍 开始提取账户余额信息...")
                                                balance_extractor = BalanceExtractor(self.driver)
                                                balance_result = balance_extractor.extract_balance()

                                                if balance_result['success']:
                                                    session_data['balance'] = balance_result['balance']
                                                    session_data['balance_currency'] = balance_result['currency']
                                                    session_data['balance_raw_text'] = balance_result['raw_text']
                                                    print(f"✅ 成功提取余额信息: {balance_result['balance']} {balance_result['currency']}")
                                                else:
                                                    session_data['balance'] = None
                                                    session_data['balance_extraction_error'] = balance_result.get('error', '未知错误')
                                                    print(f"⚠️ 余额提取失败: {balance_result.get('error', '未知错误')}")

                                            except Exception as balance_error:
                                                session_data['balance'] = None
                                                session_data['balance_extraction_error'] = str(balance_error)
                                                print(f"❌ 余额提取异常: {str(balance_error)}")

                                            return True, "OAuth授权成功完成", session_data
                                        else:
                                            print(f"⚠️ 授权后仍在GitHub: {final_url}")
                                    else:
                                        print("⚠️ 未找到OAuth授权按钮")
                                        
                                except Exception as auth_e:
                                    print(f"⚠️ OAuth授权处理出错: {auth_e}")
                            else:
                                print(f"🔍 OAuth访问结果: {current_url}")
                                
                        except Exception as e:
                            print(f"⚠️ OAuth绕过策略失败: {e}")
                        
                        # 策略2: 如果还在GitHub，尝试刷新页面
                        try:
                            print("🔄 策略2: 刷新页面尝试触发重定向")
                            self.driver.refresh()
                            time.sleep(5)
                            current_url = self.driver.current_url
                            
                            if 'github.com' not in current_url:
                                print(f"✅ 刷新后成功重定向: {current_url}")
                                session_data = {
                                    "final_url": current_url,
                                    "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                                    "login_time": datetime.now().isoformat(),
                                    "oauth_completed": True,
                                    "via_2fa_checkup": True
                                }
                                return True, "2FA设置检查后刷新成功重定向", session_data
                            else:
                                print(f"⚠️ 刷新后仍停留在: {current_url}")
                        except Exception as e:
                            print(f"⚠️ 刷新页面时出错: {e}")
                        
                        return False, f"2FA设置检查后停留在: {current_url}", {}
                else:
                    return False, f"登录后停留在未预期的GitHub页面: {current_url}", {}
            else:
                # 已经离开GitHub，可能直接重定向了
                session_data = {
                    "final_url": current_url,
                    "cookies": {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                    "login_time": datetime.now().isoformat(),
                    "oauth_completed": True
                }
                
                # 提取余额信息
                try:
                    print("🔍 开始提取账户余额信息...")
                    balance_extractor = BalanceExtractor(self.driver)
                    balance_result = balance_extractor.extract_balance()
                    
                    if balance_result['success']:
                        session_data['balance'] = balance_result['balance']
                        session_data['balance_currency'] = balance_result['currency']
                        session_data['balance_raw_text'] = balance_result['raw_text']
                        print(f"✅ 成功提取余额信息: {balance_result['balance']} {balance_result['currency']}")
                    else:
                        session_data['balance'] = None
                        session_data['balance_extraction_error'] = balance_result.get('error', '未知错误')
                        print(f"⚠️ 余额提取失败: {balance_result.get('error', '未知错误')}")
                        
                except Exception as balance_error:
                    session_data['balance'] = None
                    session_data['balance_extraction_error'] = str(balance_error)
                    print(f"❌ 余额提取异常: {str(balance_error)}")
                
                if '/login' not in current_url:
                    return True, "GitHub OAuth登录成功并已重定向", session_data
                else:
                    return False, "重定向后仍在登录页面", session_data
        
        except Exception as e:
            error_msg = f"GitHub登录过程异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(traceback.format_exc())
            return False, error_msg, {}
    
    def visit_website(self, url: str, wait_time: int = 5) -> Tuple[bool, str]:
        """
        访问网站并处理反爬虫保护
        
        Args:
            url: 网站URL
            wait_time: 等待时间(秒)
            
        Returns:
            (是否成功, 消息)
        """
        try:
            print(f"🌐 访问网站: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(wait_time)
            
            # 等待网络空闲 
            self._wait_for_network_idle(timeout=10)
            
            # 检查是否有反爬虫JavaScript
            page_source = self.driver.page_source
            if len(page_source) < 1000 and 'javascript' in page_source.lower():
                print("🔄 检测到反爬虫JavaScript，等待执行...")
                time.sleep(5)  # 等待JavaScript执行
                
                # 尝试刷新页面或等待重定向
                current_url = self.driver.current_url
                if current_url == url:
                    print("🔄 页面未重定向，尝试手动刷新...")
                    self.driver.refresh()
                    time.sleep(wait_time)
            
            # 再次获取页面内容
            page_source = self.driver.page_source
            current_url = self.driver.current_url
            
            print(f"✅ 页面加载完成")
            print(f"   当前URL: {current_url}")
            print(f"   页面内容长度: {len(page_source)} 字符")
            
            # 检查页面内容
            if len(page_source) > 1000:
                return True, f"网站访问成功，内容长度: {len(page_source)}"
            else:
                return False, "页面内容过少，可能仍被反爬虫保护"
                
        except Exception as e:
            error_msg = f"访问网站失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def analyze_page_for_oauth(self) -> Dict[str, List[str]]:
        """
        分析页面寻找OAuth登录选项
        
        Returns:
            包含各种登录选项的字典
        """
        oauth_info = {
            'github_links': [],
            'oauth_buttons': [],
            'login_forms': [],
            'auth_links': []
        }
        
        try:
            # 查找GitHub相关链接和按钮
            github_selectors = [
                "//*[contains(text(), 'GitHub') or contains(text(), 'github')]",
                "//*[contains(text(), 'GitHub 继续') or contains(text(), 'github 继续')]",
                "//*[contains(@href, 'github')]",
                "//button[contains(text(), 'GitHub')]",
                "//a[contains(text(), 'GitHub')]"
            ]
            
            for selector in github_selectors:
                try:
                    github_elements = self.driver.find_elements(By.XPATH, selector)
                    for element in github_elements:
                        text = element.text.strip()
                        href = element.get_attribute('href') or ''
                        tag = element.tag_name
                        is_visible = element.is_displayed()
                        is_clickable = element.is_enabled()
                        
                        if text or href:
                            oauth_info['github_links'].append({
                                'text': text,
                                'href': href,
                                'tag': tag,
                                'visible': is_visible,
                                'clickable': is_clickable
                            })
                except:
                    continue
            
            # 查找OAuth按钮
            oauth_selectors = [
                "button[contains(text(), 'OAuth')]",
                "a[contains(text(), 'OAuth')]",
                "*[contains(@class, 'oauth')]",
                "*[contains(@id, 'oauth')]"
            ]
            
            for selector in oauth_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        oauth_info['oauth_buttons'].append({
                            'text': element.text.strip(),
                            'href': element.get_attribute('href') or '',
                            'class': element.get_attribute('class') or ''
                        })
                except:
                    continue
            
            # 查找登录表单
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            for form in forms:
                action = form.get_attribute('action') or ''
                method = form.get_attribute('method') or 'GET'
                inputs = form.find_elements(By.TAG_NAME, 'input')
                
                input_info = []
                for inp in inputs:
                    input_info.append({
                        'type': inp.get_attribute('type') or 'text',
                        'name': inp.get_attribute('name') or '',
                        'placeholder': inp.get_attribute('placeholder') or ''
                    })
                
                oauth_info['login_forms'].append({
                    'action': action,
                    'method': method,
                    'inputs': input_info
                })
            
            # 查找认证相关链接
            auth_keywords = ['login', 'signin', 'sign-in', 'auth', 'authenticate', '登录', '登入']
            for keyword in auth_keywords:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                for element in elements:
                    text = element.text.strip()
                    href = element.get_attribute('href') or ''
                    if text or href:
                        oauth_info['auth_links'].append({
                            'text': text,
                            'href': href,
                            'keyword': keyword
                        })
            
            return oauth_info
            
        except Exception as e:
            print(f"❌ 页面OAuth分析失败: {e}")
            return oauth_info
    
    def _find_github_button_with_refresh(self, max_refresh_attempts: int = 2) -> Tuple[Optional[object], str]:
        """
        查找GitHub登录按钮，如果找不到则尝试刷新页面
        根据Playwright测试结果优化：首次访问需要刷新才能显示GitHub按钮
        
        Args:
            max_refresh_attempts: 最大刷新次数
            
        Returns:
            (GitHub按钮元素, 状态消息)
        """
        github_continue_selectors = [
            "//button[contains(., '使用 GitHub 继续')]",
            "//button[contains(.//span, '使用 GitHub 继续')]", 
            "//button[.//span[text()='使用 GitHub 继续']]",
            "//button[contains(@aria-label, 'github_logo')]",
            "//button[contains(@class, 'semi-button') and contains(., 'GitHub')]",
            "//button[contains(text(), 'GitHub')]",
            "//button[contains(., 'GitHub')]",
            "//a[contains(text(), '使用 GitHub 继续')]",
            "//a[contains(text(), 'GitHub 继续')]",
            "//button[contains(text(), 'Continue with GitHub')]",
            "//a[contains(text(), 'Continue with GitHub')]"
        ]
        
        for refresh_attempt in range(max_refresh_attempts + 1):
            if refresh_attempt > 0:
                print(f"🔄 第{refresh_attempt}次刷新页面以加载GitHub按钮...")
                self.driver.refresh()
                
                # 等待页面加载完成
                print("⏳ 等待页面完全加载...")
                time.sleep(4)
                
                # 等待React应用渲染完成（检查骨架屏）
                skeleton_wait_time = 0
                max_skeleton_wait = 10
                while skeleton_wait_time < max_skeleton_wait:
                    try:
                        skeleton_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[class*='semi-skeleton']"))
                        if skeleton_count == 0:
                            print("✅ React应用加载完成")
                            break
                        print(f"⏳ 等待React渲染完成...({skeleton_count}个骨架元素)")
                        time.sleep(1)
                        skeleton_wait_time += 1
                    except:
                        break
                
                # 刷新后关闭模态框（关键！）
                print("🔍 检查并关闭可能的系统公告模态框...")
                self._close_modals_if_present()
                time.sleep(2)
            else:
                # 首次访问也要关闭模态框
                print("🔍 首次访问，检查并关闭模态框...")
                self._close_modals_if_present()
                time.sleep(1)
            
            # 查找GitHub按钮
            print(f"🔍 第{refresh_attempt + 1}次搜索GitHub按钮...")
            for i, selector in enumerate(github_continue_selectors):
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # 验证按钮是否真的包含GitHub相关文本
                            button_text = element.text.strip()
                            if 'github' in button_text.lower() or 'GitHub' in button_text:
                                message = f"✅ 找到GitHub登录按钮: '{button_text}'" + (f" (刷新{refresh_attempt}次)" if refresh_attempt > 0 else "")
                                print(f"🎯 使用选择器 {i+1}: {selector}")
                                return element, message
                except Exception as e:
                    continue
            
            # 检查页面是否只有传统登录表单（用户名密码）
            try:
                traditional_login = self.driver.find_elements(By.XPATH, "//input[@type='text' or @placeholder='用户名' or @placeholder='用户名或邮箱']")
                if traditional_login and refresh_attempt < max_refresh_attempts:
                    print("📝 检测到传统用户名密码登录表单，需要刷新以显示OAuth选项")
                    continue
            except:
                pass
            
            if refresh_attempt < max_refresh_attempts:
                print(f"⚠️ 第{refresh_attempt + 1}次尝试未找到GitHub按钮，准备刷新页面...")
        
        return None, f"❌ 经过{max_refresh_attempts}次刷新仍未找到GitHub按钮"

    def attempt_github_oauth_login(self, github_username: str, github_password: str, totp_secret: str) -> Tuple[bool, str, Dict]:
        """
        尝试GitHub OAuth登录流程
        
        Args:
            github_username: GitHub用户名
            github_password: GitHub密码
            totp_secret: TOTP密钥
            
        Returns:
            (是否成功, 消息, 会话数据)
        """
        print(f"🔐 开始GitHub OAuth登录流程: {github_username}")
        
        # 步骤1: 截图记录初始登录页面状态
        self.take_screenshot("01_initial_login_page", "开始OAuth登录流程 - 初始登录页面")
        
        try:
            # 先关闭可能的模态框
            self._close_modals_if_present()
            time.sleep(2)
            
            # 步骤2: 关闭模态框后截图
            self.take_screenshot("02_after_close_modals", "关闭模态框后的页面状态")
            
            # 使用带刷新功能的GitHub按钮查找
            github_element, button_message = self._find_github_button_with_refresh()
            print(button_message)
            
            github_link = None
            if not github_element:
                # 如果仍然找不到GitHub按钮，分析页面寻找其他OAuth选项
                print("🔍 未找到GitHub按钮，分析页面其他OAuth选项...")
                oauth_info = self.analyze_page_for_oauth()
                
                # 尝试从oauth_info中查找链接
                for link_info in oauth_info['github_links']:
                    if link_info.get('visible') and link_info.get('clickable'):
                        text = link_info['text']
                        href = link_info['href']
                        if ('github' in text.lower() or 'github' in href.lower()):
                            github_link = href
                            print(f"找到GitHub OAuth链接: {github_link}")
                            break
            
            if not github_element and not github_link:
                # 尝试常见的GitHub OAuth端点
                base_url = f"{urlparse(self.driver.current_url).scheme}://{urlparse(self.driver.current_url).netloc}"
                oauth_endpoints = [
                    '/auth/github',
                    '/oauth/github', 
                    '/login/github',
                ]
                
                print("未在页面中找到GitHub链接，尝试常见OAuth端点...")
                for endpoint in oauth_endpoints:
                    test_url = base_url + endpoint
                    print(f"尝试访问: {test_url}")
                    
                    try:
                        self.driver.get(test_url)
                        time.sleep(3)
                        
                        current_url = self.driver.current_url
                        if 'github.com' in current_url:
                            print(f"✅ 成功重定向到GitHub: {current_url}")
                            github_link = test_url
                            break
                        else:
                            print(f"❌ 端点无效或未重定向到GitHub: {current_url}")
                    except Exception as e:
                        print(f"❌ 测试端点失败: {e}")
                        continue
            
            # 执行点击或访问操作
            if github_element or github_link:
                try:
                    if github_element:
                        # 步骤3: 找到GitHub按钮后截图
                        self.take_screenshot("03_github_button_found", "找到GitHub登录按钮")
                        
                        # 点击GitHub登录按钮
                        print(f"🔘 点击GitHub登录按钮...")
                        
                        # 获取按钮详细信息用于调试
                        button_text = github_element.text.strip()
                        button_class = github_element.get_attribute('class')
                        button_href = github_element.get_attribute('href')
                        print(f"   按钮文本: {button_text}")
                        print(f"   按钮class: {button_class}")
                        print(f"   按钮href: {button_href}")
                        
                        # 使用增强的safe_click方法（支持React组件）
                        click_success = self.safe_click(github_element)
                        
                        if not click_success:
                            return False, "GitHub按钮点击失败", {}
                        
                        print("✅ GitHub按钮点击成功")
                        
                        # 步骤4: 点击GitHub按钮后截图
                        self.take_screenshot("04_after_github_click", "点击GitHub按钮后的页面状态")
                        
                        # 添加延迟并执行诊断检查
                        print("🔍 执行点击后诊断检查...")
                        time.sleep(1)  # 短暂延迟让点击效果生效
                        
                        # 诊断弹出窗口阻止状态
                        try:
                            popup_diagnostic = self.driver.execute_script("""
                                var diagnostics = {
                                    popupBlocked: false,
                                    userActivated: false,
                                    consoleErrors: [],
                                    windowCount: window.length || 'unknown',
                                    hasWindowOpen: typeof window.open === 'function',
                                    documentState: document.readyState,
                                    visibilityState: document.visibilityState
                                };
                                
                                // 检查用户激活状态
                                try {
                                    diagnostics.userActivated = window.navigator.userActivation ? 
                                        window.navigator.userActivation.isActive : 'unknown';
                                } catch (e) {
                                    diagnostics.userActivated = 'unknown';
                                }
                                
                                // 尝试测试弹出窗口
                                try {
                                    var testWindow = window.open('', '_blank', 'width=1,height=1');
                                    if (testWindow) {
                                        testWindow.close();
                                        diagnostics.popupBlocked = false;
                                    } else {
                                        diagnostics.popupBlocked = true;
                                    }
                                } catch (e) {
                                    diagnostics.popupBlocked = true;
                                    diagnostics.consoleErrors.push(e.message);
                                }
                                
                                return diagnostics;
                            """)
                            
                            print(f"📊 弹出窗口诊断结果:")
                            print(f"   弹出窗口被阻止: {popup_diagnostic.get('popupBlocked', 'unknown')}")
                            print(f"   用户激活状态: {popup_diagnostic.get('userActivated', 'unknown')}")
                            print(f"   文档状态: {popup_diagnostic.get('documentState', 'unknown')}")
                            print(f"   页面可见性: {popup_diagnostic.get('visibilityState', 'unknown')}")
                            print(f"   window.open可用: {popup_diagnostic.get('hasWindowOpen', 'unknown')}")
                            
                            if popup_diagnostic.get('consoleErrors'):
                                print(f"   JavaScript错误: {popup_diagnostic['consoleErrors']}")
                            
                            # 如果弹出窗口被阻止，尝试修复
                            if popup_diagnostic.get('popupBlocked', False):
                                print("🛠️ 检测到弹出窗口被阻止，尝试修复...")
                                self.driver.execute_script("""
                                    // 尝试重新激活用户交互
                                    document.dispatchEvent(new MouseEvent('click', {
                                        bubbles: true, cancelable: true, view: window
                                    }));
                                    
                                    // 触发焦点事件
                                    window.focus();
                                    document.body.focus();
                                """)
                                time.sleep(0.5)
                            
                        except Exception as e:
                            print(f"⚠️ 弹出窗口诊断失败: {e}")
                        
                        # 添加延迟让JavaScript充分初始化
                        print("⏳ 等待JavaScript充分初始化...")
                        time.sleep(2)
                        
                        # 增强的新标签页检测逻辑 - 模拟Playwright行为
                        print("⏳ 等待GitHub OAuth标签页打开...")
                        max_wait_time = 45  # 优化等待时间
                        oauth_window_opened = False
                        original_windows = set(self.driver.window_handles)
                        
                        # 更频繁的检测间隔，模拟Playwright的检测方式
                        check_interval = 0.5  # 每0.5秒检测一次
                        max_checks = int(max_wait_time / check_interval)
                        
                        for i in range(max_checks):
                            time.sleep(check_interval)
                            elapsed = (i + 1) * check_interval
                            
                            try:
                                # 获取当前所有窗口句柄
                                current_windows = self.driver.window_handles
                                current_count = len(current_windows)
                                original_count = len(original_windows)
                                
                                # 检查窗口数量变化
                                if current_count > original_count:
                                    print(f"🎉 检测到新标签页! ({original_count} -> {current_count}) 用时{elapsed:.1f}秒")
                                    
                                    # 找出新的窗口句柄
                                    new_windows = [w for w in current_windows if w not in original_windows]
                                    
                                    if new_windows:
                                        new_window = new_windows[0]
                                        print(f"📋 切换到新标签页...")
                                        
                                        # 切换到新标签页
                                        self.driver.switch_to.window(new_window)
                                        
                                        # 等待新页面加载（模拟networkidle）
                                        print("⏳ 等待新标签页加载...")
                                        self._wait_for_network_idle(timeout=10)
                                        
                                        # 使用WebDriverWait确保页面元素加载
                                        try:
                                            WebDriverWait(self.driver, 10).until(
                                                lambda driver: driver.execute_script("return document.readyState") == "complete"
                                            )
                                            print("✅ 新标签页加载状态: 完成")
                                        except:
                                            print("⚠️ 新标签页加载状态检查超时，继续执行")
                                        
                                        # 获取新标签页信息
                                        new_window_url = self.driver.current_url
                                        print(f"📍 新标签页URL: {new_window_url}")
                                        
                                        # 验证是否为GitHub页面
                                        if 'github.com' in new_window_url:
                                            print("🎉 成功! 新标签页是GitHub OAuth页面")
                                            oauth_window_opened = True
                                            break
                                        else:
                                            print(f"⚠️ 新标签页不是GitHub页面，继续监控...")
                                    
                                    break  # 找到新窗口就跳出，无论是否为GitHub
                                
                                # 检查当前页面是否直接跳转到GitHub（无新窗口的情况）
                                elif i > 4:  # 前2秒让页面稳定
                                    current_url = self.driver.current_url
                                    if 'github.com' in current_url:
                                        print(f"🎉 当前页面直接跳转到GitHub: {current_url}")
                                        oauth_window_opened = True
                                        break
                                
                                # 每5秒输出一次状态
                                if int(elapsed) % 5 == 0 and elapsed >= 5:
                                    print(f"⏳ 等待新标签页... ({elapsed:.0f}/{max_wait_time}秒)")
                            
                            except Exception as e:
                                print(f"⚠️ 标签页检测出错: {e}")
                                continue
                        
                        # 检查最终状态并进行深度诊断
                        final_url = self.driver.current_url
                        if not oauth_window_opened and 'github.com' not in final_url:
                            print("🔍 执行深度诊断...")
                            
                            # 检查按钮状态
                            try:
                                github_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'GitHub')]")
                                for btn in github_buttons:
                                    if btn.is_displayed():
                                        btn_class = btn.get_attribute('class') or ''
                                        btn_disabled = btn.get_attribute('disabled')
                                        btn_aria_disabled = btn.get_attribute('aria-disabled')
                                        
                                        print(f"🔘 GitHub按钮状态:")
                                        print(f"   class: {btn_class}")
                                        print(f"   disabled: {btn_disabled}")
                                        print(f"   aria-disabled: {btn_aria_disabled}")
                                        
                                        if 'loading' in btn_class:
                                            print(f"⚠️ GitHub按钮仍处于加载状态")
                                            print("💡 这可能表示OAuth请求正在进行但遇到网络问题")
                                        elif 'error' in btn_class:
                                            print(f"❌ GitHub按钮显示错误状态")
                            except Exception as e:
                                print(f"⚠️ 按钮状态检查失败: {e}")
                            
                            # 获取浏览器控制台日志
                            try:
                                console_logs = self.driver.get_log('browser')
                                if console_logs:
                                    print("📝 浏览器控制台日志:")
                                    for log in console_logs[-10:]:  # 显示最后10条日志
                                        level = log.get('level', 'INFO')
                                        message = log.get('message', '')
                                        if any(keyword in message.lower() for keyword in ['error', 'blocked', 'popup', 'oauth', 'github']):
                                            print(f"   [{level}] {message}")
                            except Exception as e:
                                print(f"⚠️ 无法获取控制台日志: {e}")
                            
                            # 检查网络请求
                            try:
                                network_logs = self.driver.get_log('performance')
                                oauth_requests = []
                                for log in network_logs[-20:]:  # 检查最后20个网络事件
                                    message = json.loads(log.get('message', '{}'))
                                    if message.get('method') == 'Network.requestWillBeSent':
                                        url = message.get('params', {}).get('request', {}).get('url', '')
                                        if 'github.com' in url or 'oauth' in url:
                                            oauth_requests.append(url)
                                
                                if oauth_requests:
                                    print("🌐 检测到的OAuth相关网络请求:")
                                    for req in oauth_requests:
                                        print(f"   {req}")
                                else:
                                    print("⚠️ 未检测到任何OAuth网络请求，可能请求被阻止")
                            except Exception as e:
                                print(f"⚠️ 网络日志检查失败: {e}")
                            
                            # 执行最后的弹出窗口测试
                            try:
                                print("🧪 执行最后的弹出窗口测试...")
                                test_result = self.driver.execute_script("""
                                    try {
                                        var popup = window.open('https://google.com', '_blank', 'width=300,height=200');
                                        if (popup) {
                                            popup.close();
                                            return 'popup_allowed';
                                        } else {
                                            return 'popup_blocked';
                                        }
                                    } catch (e) {
                                        return 'popup_error: ' + e.message;
                                    }
                                """)
                                print(f"🧪 弹出窗口测试结果: {test_result}")
                            except Exception as e:
                                print(f"⚠️ 弹出窗口测试失败: {e}")
                            
                            # 保存调试信息
                            debug_filename = f'oauth_debug_{int(time.time())}.html'
                            try:
                                with open(debug_filename, 'w', encoding='utf-8') as f:
                                    f.write(self.driver.page_source)
                                print(f"📄 调试页面已保存: {debug_filename}")
                            except Exception as e:
                                print(f"⚠️ 保存调试页面失败: {e}")
                            
                            return False, f"GitHub OAuth窗口未打开 (已执行深度诊断)，当前URL: {final_url}", {}
                        
                        # 如果没有新窗口但当前页面是GitHub，也继续处理
                        if not oauth_window_opened and 'github.com' in final_url:
                            print("ℹ️  当前页面已在GitHub，继续OAuth流程")
                        
                        time.sleep(2)  # 额外等待确保页面稳定
                    elif github_link:
                        # 访问GitHub OAuth链接
                        print(f"🔗 访问GitHub OAuth链接: {github_link}")
                        if github_link.startswith('http'):
                            self.driver.get(github_link)
                        else:
                            # 相对链接
                            base_url = f"{urlparse(self.driver.current_url).scheme}://{urlparse(self.driver.current_url).netloc}"
                            full_url = urljoin(base_url, github_link)
                            self.driver.get(full_url)
                        time.sleep(3)
                except Exception as e:
                    print(f"❌ 执行GitHub OAuth操作失败: {e}")
                    return False, f"执行GitHub OAuth操作失败: {e}", {}
            else:
                return False, "未找到GitHub OAuth登录选项", {}
            
            # 检查是否到达GitHub登录页面
            current_url = self.driver.current_url
            if 'github.com' not in current_url:
                return False, f"未成功重定向到GitHub，当前URL: {current_url}", {}
            
            print(f"✅ 成功到达GitHub页面: {current_url}")
            
            # 执行GitHub登录
            github_login_result = self._perform_github_login_steps(github_username, github_password, totp_secret)
            
            # 如果是新窗口OAuth，需要处理窗口切换和重定向监控
            if oauth_window_opened:
                print("🔄 OAuth完成，开始监控重定向...")
                try:
                    # 使用增强的OAuth完成监控
                    oauth_success = self._monitor_oauth_completion_and_redirect(
                        original_window, self.driver.current_window_handle
                    )
                    
                    if oauth_success:
                        return True, "GitHub OAuth新窗口登录成功", github_login_result[2] if github_login_result[0] else {}
                    else:
                        return False, "OAuth重定向监控失败", {}
                            
                except Exception as e:
                    print(f"⚠️ 处理OAuth窗口切换时出错: {e}")
                    try:
                        # 确保切换回可用窗口
                        current_windows = self.driver.window_handles
                        if current_windows:
                            self.driver.switch_to.window(current_windows[0])
                    except:
                        pass
                    return False, f"OAuth窗口处理异常: {e}", {}
            
            return github_login_result
            
        except Exception as e:
            error_msg = f"GitHub OAuth登录异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(traceback.format_exc())
            return False, error_msg, {}
    
    def _perform_github_login_steps(self, username: str, password: str, totp_secret: str) -> Tuple[bool, str, Dict]:
        """执行GitHub登录步骤 - 增强版本支持完整OAuth流程"""
        try:
            print("🔑 开始GitHub登录步骤...")
            current_url = self.driver.current_url
            
            # 登录流程
            if 'login' in current_url:
                print("🔐 执行GitHub登录...")
                
                # 等待并输入凭据
                username_field = self.wait_and_find_element(By.ID, "login_field", timeout=10)
                if not username_field:
                    username_field = self.wait_and_find_element(By.NAME, "login", timeout=5)
                
                if not username_field:
                    return False, "未找到GitHub用户名输入框", {}
                
                password_field = self.wait_and_find_element(By.ID, "password", timeout=5)
                if not password_field:
                    password_field = self.wait_and_find_element(By.NAME, "password", timeout=5)
                
                if not password_field:
                    return False, "未找到GitHub密码输入框", {}
                
                # 输入用户名和密码
                print("📝 输入GitHub凭据...")
                username_field.clear()
                username_field.send_keys(username)
                
                password_field.clear() 
                password_field.send_keys(password)
                
                # 查找并点击登录按钮
                login_button = self.wait_and_find_clickable_element(By.CSS_SELECTOR, "input[type='submit'][value*='Sign in']", timeout=5)
                if not login_button:
                    login_button = self.wait_and_find_clickable_element(By.CSS_SELECTOR, "button[type='submit']", timeout=5)
                
                if not login_button:
                    return False, "未找到GitHub登录按钮", {}
                
                print("🔘 点击登录按钮...")
                if not self.safe_click(login_button):
                    return False, "点击登录按钮失败", {}
                
                # 等待页面响应
                time.sleep(3)
            
            # 处理2FA认证
            current_url = self.driver.current_url
            if 'two-factor' in current_url:
                print("🔐 处理2FA验证...")
                
                # 如果是webauthn页面，导航到TOTP页面
                if 'webauthn' in current_url:
                    totp_url = "https://github.com/sessions/two-factor/app"
                    self.driver.get(totp_url)
                    time.sleep(3)
                
                # 生成并输入TOTP
                totp = pyotp.TOTP(totp_secret)
                verification_code = totp.now()
                print(f"📱 生成的TOTP验证码: {verification_code}")
                
                # 查找TOTP输入框 - 使用更准确的选择器
                totp_field = self.wait_and_find_element(By.NAME, "app_otp", timeout=10)
                if not totp_field:
                    totp_field = self.wait_and_find_element(By.ID, "app_totp", timeout=5)
                
                if not totp_field:
                    return False, "未找到2FA验证码输入框", {}
                
                # 输入验证码
                totp_field.clear()
                totp_field.send_keys(verification_code)
                
                # 查找并点击验证按钮
                verify_button = self.wait_and_find_clickable_element(By.CSS_SELECTOR, "button[type='submit']", timeout=5)
                if verify_button:
                    print("✅ 提交2FA验证码...")
                    if not self.safe_click(verify_button):
                        return False, "点击2FA验证按钮失败", {}
                else:
                    # 尝试按回车提交
                    totp_field.send_keys(Keys.RETURN)
                
                # 等待2FA验证完成
                time.sleep(5)
            
            # 处理OAuth授权或2FA checkup重定向
            current_url = self.driver.current_url
            print(f"🔍 2FA后URL: {current_url}")
            
            # 处理OAuth授权页面
            if 'authorize' in current_url:
                print("📋 处理OAuth授权...")
                
                try:
                    authorize_button = self.wait_and_find_clickable_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']", timeout=5)
                    if authorize_button:
                        if not self.safe_click(authorize_button):
                            return False, "点击授权按钮失败", {}
                        print("✅ OAuth授权完成")
                    else:
                        print("⚠️ 未找到授权按钮，可能已自动授权")
                except TimeoutException:
                    print("⚠️ 授权按钮超时，可能已自动授权")
                    
                time.sleep(3)
                
            # 处理two_factor_checkup页面的自动重定向
            elif 'two_factor_checkup' in current_url:
                print("🔄 处理2FA checkup页面自动重定向...")
                print("💡 two_factor_checkup页面会自动处理OAuth回调，需要耐心等待")
                
                # 步骤5: 到达2FA checkup页面时截图
                self.take_screenshot("05_2fa_checkup_page", "到达GitHub 2FA设置检查页面")
                
                # 等待自动重定向完成
                checkup_start_time = time.time()
                max_checkup_wait = 90  # two_factor_checkup页面最多等待90秒
                
                while time.time() - checkup_start_time < max_checkup_wait:
                    time.sleep(2)
                    try:
                        current_url = self.driver.current_url
                        
                        # 检查是否已经离开checkup页面
                        if 'two_factor_checkup' not in current_url:
                            print(f"✅ 已离开two_factor_checkup页面: {current_url}")
                            
                            # 步骤6: 离开2FA checkup页面后截图
                            self.take_screenshot("06_after_2fa_checkup", "离开2FA checkup页面后的状态")
                            
                            # 如果重定向到目标网站，说明OAuth成功
                            if 'github.com' not in current_url:
                                print("✅ two_factor_checkup自动重定向到目标网站成功!")
                                # 步骤7: 成功重定向到目标网站截图
                                self.take_screenshot("07_oauth_success_redirect", "OAuth成功重定向到目标网站")
                                break
                            else:
                                print(f"🔍 two_factor_checkup重定向到: {current_url}")
                                break
                        
                        elapsed = int(time.time() - checkup_start_time)
                        if elapsed % 10 == 0:  # 每10秒输出一次状态
                            print(f"⏳ two_factor_checkup等待中... ({elapsed}/{max_checkup_wait}秒)")
                        
                    except Exception as e:
                        print(f"⚠️ 检查two_factor_checkup状态时出错: {e}")
                        break
            
            # 检查最终登录状态
            final_url = self.driver.current_url
            print(f"🏁 最终URL: {final_url}")
            
            # 步骤8: 最终状态截图
            self.take_screenshot("08_final_status", f"OAuth流程最终状态 - URL: {final_url}")
            
            # 获取cookies作为会话数据
            cookies = self.driver.get_cookies()
            session_data = {
                'cookies': {cookie['name']: cookie['value'] for cookie in cookies},
                'final_url': final_url,
                'login_time': datetime.now().isoformat(),
                'login_method': 'github_oauth_selenium_enhanced',
                'username': username
            }
            
            # 增强判断登录成功的逻辑
            if 'github.com' not in final_url:
                # 已经离开GitHub，检查重定向目标
                parsed_url = urlparse(final_url)
                domain = parsed_url.netloc
                path = parsed_url.path
                
                # 检查是否重定向到目标网站的登录成功页面
                if domain and '/login' not in path:
                    print(f"✅ GitHub OAuth登录成功，已重定向到: {domain}{path}")
                    if '/console' in path:
                        return True, "GitHub OAuth登录成功(控制台)", session_data
                    else:
                        return True, "GitHub OAuth登录成功", session_data
                else:
                    print(f"⚠️ 重定向异常，仍在登录相关页面: {final_url}")
                    return False, f"OAuth重定向异常: {final_url}", {}
            else:
                # 仍在GitHub，检查具体状态
                if 'two_factor_checkup' in final_url:
                    print("⚠️ OAuth流程停留在two_factor_checkup页面")
                    return False, "OAuth流程停留在two_factor_checkup页面", {}
                else:
                    # 检查是否还在登录页面
                    page_source = self.driver.page_source.lower()
                    if 'sign in' in page_source and 'password' in page_source:
                        return False, "GitHub登录失败，仍在登录页面", {}
                    else:
                        print("✅ GitHub认证完成，等待OAuth回调")
                        return True, "GitHub OAuth认证完成", session_data
                    
        except Exception as e:
            error_msg = f"GitHub登录步骤执行异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(traceback.format_exc())
            return False, error_msg, {}
    
    def _monitor_oauth_completion_and_redirect(self, original_tab: str, oauth_tab: str) -> bool:
        """
        监控OAuth完成和重定向处理
        基于成功测试的逻辑实现
        """
        try:
            print("🔍 监控OAuth回调和重定向...")
            
            # 等待OAuth回调完成
            callback_completed = False
            redirected_to_home = False
            
            for i in range(120):  # 等待120秒
                time.sleep(1)
                
                try:
                    current_url = self.driver.current_url
                    
                    # 检查是否重定向回目标网站(非GitHub)
                    if 'github.com' not in current_url:
                        print(f"✅ OAuth标签页重定向回目标网站: {current_url}")
                        
                        # 检查是否是首页（不是登录页）
                        if '/login' not in current_url:
                            print("🎉 OAuth标签页直接跳转到首页!")
                            redirected_to_home = True
                            callback_completed = True
                            break
                        else:
                            print("⚠️ OAuth标签页重定向到登录页，继续等待...")
                    
                    elif 'two_factor_checkup' in current_url and i > 30:
                        # 如果OAuth授权后仍在checkup页面超过30秒，检查其他标签页
                        print(f"⚠️ 第{i+1}秒仍在checkup页面，检查其他标签页...")
                        
                        current_tabs = self.driver.window_handles
                        print(f"📋 当前标签页数量: {len(current_tabs)}")
                        
                        # 检查所有标签页
                        for tab_index, tab in enumerate(current_tabs):
                            try:
                                self.driver.switch_to.window(tab)
                                tab_url = self.driver.current_url
                                tab_title = self.driver.title
                                
                                print(f"  标签页{tab_index + 1}: {tab_url[:50]}... | {tab_title[:30]}...")
                                
                                # 检查是否找到已登录的标签页
                                if 'github.com' not in tab_url and '/login' not in tab_url:
                                    print(f"✅ 发现已登录的标签页: {tab_url}")
                                    callback_completed = True
                                    redirected_to_home = True
                                    break
                                    
                            except Exception as e:
                                print(f"  标签页{tab_index + 1}检查失败: {e}")
                                continue
                        
                        if callback_completed:
                            break
                        
                        # 切换回OAuth标签页继续监控
                        if oauth_tab in current_tabs:
                            self.driver.switch_to.window(oauth_tab)
                    
                    elif i % 10 == 0:  # 每10秒输出状态
                        print(f"  第{i+1}秒等待OAuth回调: {current_url[:60]}...")
                        
                except Exception as e:
                    print(f"⚠️ 检查OAuth标签页状态出错: {e}")
                    # 可能标签页已关闭，检查其他标签页
                    current_tabs = self.driver.window_handles
                    if len(current_tabs) == 1:
                        # 只剩一个标签页，切换过去检查
                        self.driver.switch_to.window(current_tabs[0])
                        try:
                            current_url = self.driver.current_url
                            if 'github.com' not in current_url and '/login' not in current_url:
                                print("✅ OAuth完成，剩余标签页已登录到首页!")
                                callback_completed = True
                                redirected_to_home = True
                                break
                        except:
                            pass
            
            if not callback_completed:
                print("❌ OAuth回调超时")
                return False
            
            print("📍 验证最终登录状态")
            
            # 验证登录状态
            if redirected_to_home:
                # OAuth标签页已经是首页，无需额外操作
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                print(f"🎉 登录成功!")
                print(f"📍 最终URL: {current_url}")
                print(f"📋 页面标题: {page_title}")
                
                return True
            else:
                # 需要检查剩余标签页状态
                current_tabs = self.driver.window_handles
                
                for tab in current_tabs:
                    try:
                        self.driver.switch_to.window(tab)
                        tab_url = self.driver.current_url
                        
                        if 'github.com' not in tab_url and '/login' not in tab_url:
                            print(f"✅ 找到已登录的标签页: {tab_url}")
                            return True
                            
                    except Exception:
                        continue
                
                print("⚠️ 未找到已登录的标签页")
                return False
            
        except Exception as e:
            print(f"❌ 监控OAuth完成出错: {e}")
            return False
    
    def _close_modals_if_present(self):
        """检查并关闭页面上的模态框，特别针对anyrouter.top的系统公告"""
        try:
            modals_closed = 0
            
            # 首先检查是否有系统公告对话框（根据Playwright测试发现）
            system_announcement_selectors = [
                # 系统公告对话框
                "//dialog[@aria-label='系统公告' or contains(@class, 'semi-modal')]",
                "//div[@role='dialog' and .//h5[text()='系统公告']]",
                "*[role='dialog']:has(h5:contains('系统公告'))"
            ]
            
            # 检查系统公告关闭按钮
            announcement_close_selectors = [
                "//button[text()='关闭公告']",
                "//button[text()='今日关闭']", 
                "//button[contains(@class, 'semi-button') and text()='关闭公告']",
                "//dialog//button[contains(., '关闭')]"
            ]
            
            print("🔍 检查系统公告模态框...")
            for selector in announcement_close_selectors:
                try:
                    close_buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in close_buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"🔘 找到系统公告关闭按钮，点击关闭...")
                            self.safe_click(button)
                            modals_closed += 1
                            time.sleep(1)
                            break
                    if modals_closed > 0:
                        break
                except Exception as e:
                    continue
            
            # 查找其他通用模态框关闭按钮
            close_selectors = [
                # Semi UI 模态框关闭按钮
                ".semi-modal-close",
                "button[aria-label='close']",
                "button[aria-label='关闭']",
                # 通用模态框关闭按钮
                ".modal-close",
                ".close",
                "[data-dismiss='modal']",
                "button.close",
                # 包含关闭文本的按钮
                "//button[contains(text(), '关闭')]",
                "//button[contains(text(), '取消')]", 
                "//button[contains(text(), 'Close')]",
                "//button[contains(text(), 'Cancel')]",
                # X 按钮图标
                "//button[contains(@class, 'semi-button') and .//svg]"
            ]
            
            for selector in close_selectors:
                try:
                    if selector.startswith('//'):
                        # XPath 选择器
                        close_buttons = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS 选择器
                        close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in close_buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"🔘 找到模态框关闭按钮，点击关闭...")
                            if self.safe_click(button):
                                modals_closed += 1
                                time.sleep(1)  # 等待模态框关闭动画
                                break  # 关闭一个就够了
                
                except Exception:
                    continue
                    
                if modals_closed > 0:
                    break
            
            if modals_closed > 0:
                print(f"✅ 成功关闭了 {modals_closed} 个模态框")
                time.sleep(2)  # 等待页面稳定
            else:
                print("ℹ️  未发现需要关闭的模态框")
                
        except Exception as e:
            print(f"⚠️ 关闭模态框时出错: {e}")
    
    def get_page_info(self) -> Dict:
        """获取当前页面信息"""
        try:
            return {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'page_source_length': len(self.driver.page_source),
                'cookies_count': len(self.driver.get_cookies())
            }
        except Exception as e:
            return {'error': str(e)}
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ 浏览器已关闭")
            except Exception as e:
                print(f"⚠️ 关闭浏览器时出错: {e}")

# 创建全局实例
browser_simulator = None

def get_browser_simulator(browser_type: str = "chrome", headless: bool = True) -> BrowserSimulator:
    """获取浏览器模拟器实例"""
    global browser_simulator
    
    if browser_simulator is None:
        browser_simulator = BrowserSimulator(browser_type, headless)
    
    return browser_simulator

def close_browser_simulator():
    """关闭全局浏览器模拟器实例"""
    global browser_simulator
    
    if browser_simulator:
        browser_simulator.close()
        browser_simulator = None

# 向后兼容的函数
def simulate_github_oauth_login_browser(website_url: str, github_username: str, github_password: str, totp_secret: str) -> Tuple[bool, str, Dict]:
    """
    使用浏览器模拟器进行GitHub OAuth登录
    
    Args:
        website_url: 目标网站URL
        github_username: GitHub用户名
        github_password: GitHub密码
        totp_secret: TOTP密钥
        
    Returns:
        (是否成功, 消息, 会话数据)
    """
    browser = None
    try:
        browser = BrowserSimulator()
        
        # 访问目标网站
        success, message = browser.visit_website(website_url)
        if not success:
            return False, f"访问网站失败: {message}", {}
        
        # 如果当前不在登录页面，尝试访问登录页面
        current_url = browser.driver.current_url
        if '/login' not in current_url:
            print("🔄 当前不在登录页面，尝试访问登录页面...")
            login_url = website_url.rstrip('/') + '/login'
            login_success, login_message = browser.visit_website(login_url)
            if not login_success:
                print(f"⚠️ 访问登录页面失败: {login_message}")
        
        # 检查并关闭可能的模态框
        print("🔍 检查是否有模态框需要关闭...")
        browser._close_modals_if_present()
        
        # 执行GitHub OAuth登录
        return browser.attempt_github_oauth_login(github_username, github_password, totp_secret)
        
    except Exception as e:
        return False, f"浏览器模拟器异常: {str(e)}", {}
    finally:
        if browser:
            browser.close()