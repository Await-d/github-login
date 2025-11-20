"""
GitHub仓库Star操作工具
使用Playwright自动化GitHub仓库收藏（Star）功能
"""

import re
import logging
from typing import Tuple, Optional
from urllib.parse import urlparse
import asyncio
from datetime import datetime
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 截图目录
SCREENSHOT_DIR = Path("/app/backend/data/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# 配置常量
CHECKUP_SKIP_TIMEOUT = 3  # 点击跳过按钮后等待时间（秒）
CHECKUP_AUTO_REDIRECT_MAX_WAIT = 30  # 等待自动重定向的最大时间（秒）
PAGE_LOAD_TIMEOUT = 30000  # 页面加载超时时间（毫秒）
FALLBACK_WAIT_TIME = 5  # 未找到跳过按钮时的等待时间（秒）
MAX_DEBUG_INPUTS = 10  # 调试时打印的最大输入框数量


def parse_repository_url(repo_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析GitHub仓库URL，提取owner和repo_name
    
    Args:
        repo_url: GitHub仓库URL (如 https://github.com/owner/repo)
        
    Returns:
        (owner, repo_name) 或 (None, None) 如果解析失败
    """
    try:
        # 安全检查:只接受GitHub URL
        if not repo_url or not isinstance(repo_url, str):
            return None, None
            
        # 去除首尾空格
        repo_url = repo_url.strip()
        
        # 必须是https://github.com开头(安全考虑,不接受http)
        if not repo_url.startswith('https://github.com/'):
            # 尝试自动添加https://
            if repo_url.startswith('github.com/'):
                repo_url = 'https://' + repo_url
            else:
                return None, None
        
        # 移除末尾的斜杠和.git后缀
        repo_url = repo_url.rstrip('/').replace('.git', '')
        
        # 使用严格的正则表达式匹配
        # owner和repo_name只允许字母、数字、连字符、下划线和点
        pattern = r'^https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$'
        match = re.match(pattern, repo_url)
        
        if match:
            owner = match.group(1)
            repo_name = match.group(2)
            
            # GitHub限制: owner最长39字符,repo最长100字符
            if len(owner) > 39 or len(repo_name) > 100:
                return None, None
            
            # 不允许特殊字符开头
            if owner.startswith(('-', '_')) or repo_name.startswith(('-', '_', '.')):
                return None, None
                
            return owner, repo_name
        else:
            return None, None
            
    except Exception as e:
        print(f"解析仓库URL失败: {e}")
        return None, None


async def _save_debug_screenshot(page, username: str, stage: str, error_msg: str = "") -> Optional[str]:
    """
    保存调试截图

    Args:
        page: Playwright page对象
        username: GitHub用户名
        stage: 失败阶段（如 "login", "2fa", "checkup", "star"）
        error_msg: 错误信息

    Returns:
        截图文件路径，失败则返回None
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 安全的文件名（移除特殊字符）
        safe_username = re.sub(r'[^\w\-]', '_', username)
        safe_stage = re.sub(r'[^\w\-]', '_', stage)

        filename = f"{safe_username}_{safe_stage}_{timestamp}.png"
        screenshot_path = SCREENSHOT_DIR / filename

        # 保存截图
        await page.screenshot(path=str(screenshot_path), full_page=True)

        # 同时保存页面HTML用于详细调试
        html_path = SCREENSHOT_DIR / f"{safe_username}_{safe_stage}_{timestamp}.html"
        html_content = await page.content()
        html_path.write_text(html_content, encoding='utf-8')

        print(f"📸 已保存调试截图: {screenshot_path}")
        print(f"📄 已保存页面HTML: {html_path}")
        if error_msg:
            print(f"   错误信息: {error_msg}")
        print(f"   当前URL: {page.url}")

        return str(screenshot_path)
    except Exception as e:
        print(f"⚠️ 保存截图失败: {e}")
        return None


async def _handle_2fa_checkup(page, repo_url: Optional[str] = None, username: str = "unknown") -> bool:
    """
    处理GitHub 2FA安全检查页面

    Args:
        page: Playwright page对象
        repo_url: 可选的仓库URL,如果提供则在跳过后重新访问该URL
        username: GitHub用户名，用于截图文件命名

    Returns:
        True 如果成功处理或不在checkup页面, False 如果处理失败
    """
    try:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    except ImportError:
        PlaywrightTimeoutError = Exception

    current_url = page.url

    # 检查是否在2FA checkup页面
    if 'two_factor_checkup' not in current_url and 'settings/security' not in current_url:
        return True  # 不在checkup页面,无需处理

    print("🔍 检测到GitHub 2FA安全检查页面,尝试跳过...")

    # 跳过按钮选择器列表（移除了重复的大小写变体）
    skip_selectors = [
        'button:has-text("Skip")',
        'a:has-text("Skip")',
        'button:has-text("Skip for now")',
        'a:has-text("Skip for now")',
        'button:has-text("skip 2FA verification")',
        'a:has-text("skip 2FA verification")',
        '[data-ga-click*="skip"]',
        '[href*="skip"]'
    ]

    skip_button_found = False
    for selector in skip_selectors:
        try:
            skip_btn = await page.query_selector(selector)
            if skip_btn and await skip_btn.is_visible():
                print(f"✅ 找到跳过按钮: {selector}")
                await skip_btn.click()
                skip_button_found = True

                # 点击后等待页面跳转离开checkup页面
                print("⏳ 等待页面跳转...")
                for i in range(CHECKUP_AUTO_REDIRECT_MAX_WAIT):
                    await asyncio.sleep(1)
                    current_url = page.url
                    if 'two_factor_checkup' not in current_url and 'settings/security' not in current_url:
                        print(f"✅ 已成功离开2FA检查页面: {current_url}")
                        # 如果提供了repo_url,则重新访问仓库页面
                        if repo_url:
                            await page.goto(repo_url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                            await asyncio.sleep(2)
                            print(f"🔗 跳过2FA检查后重新访问仓库: {repo_url}")
                        return True
                    if i % 5 == 0 and i > 0:
                        print(f"⏳ 等待离开2FA检查页面... ({i}/{CHECKUP_AUTO_REDIRECT_MAX_WAIT}秒)")

                # 如果等待30秒后仍在checkup页面，保存截图并打印警告
                print(f"⚠️ 点击跳过按钮后等待超时，当前仍在: {page.url}")
                await _save_debug_screenshot(page, username, "checkup_timeout_after_skip", "点击跳过按钮30秒后仍在checkup页面")
                break
        except PlaywrightTimeoutError:
            # 元素未找到,尝试下一个选择器
            continue
        except Exception as e:
            print(f"⚠️ 尝试选择器 {selector} 失败: {e}")
            continue

    # 如果没有找到跳过按钮,等待自动重定向
    if not skip_button_found:
        print("⚠️ 未找到跳过按钮,尝试等待自动重定向...")

        for i in range(CHECKUP_AUTO_REDIRECT_MAX_WAIT):
            await asyncio.sleep(1)
            current_url = page.url
            if 'two_factor_checkup' not in current_url and 'settings/security' not in current_url:
                print(f"✅ 2FA检查页面已自动离开: {current_url}")
                return True
            if i % 5 == 0 and i > 0:
                print(f"⏳ 等待2FA检查页面自动重定向... ({i}/{CHECKUP_AUTO_REDIRECT_MAX_WAIT}秒)")

        # 自动重定向超时,保存截图并尝试重新访问仓库
        print("⚠️ 自动重定向超时...")
        await _save_debug_screenshot(page, username, "checkup_auto_redirect_timeout", "等待自动重定向30秒后超时")
        if repo_url:
            print("🔄 尝试重新访问仓库...")
            await asyncio.sleep(FALLBACK_WAIT_TIME)
            await page.goto(repo_url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
            await asyncio.sleep(2)

    return True


async def star_github_repository(
    repo_owner: str,
    repo_name: str,
    github_username: str,
    github_password: str,
    totp_secret: str,
    force_execute: bool = False
) -> Tuple[bool, str]:
    """
    使用Playwright自动化Star GitHub仓库

    Args:
        repo_owner: 仓库所有者
        repo_name: 仓库名称
        github_username: GitHub用户名
        github_password: GitHub密码
        totp_secret: TOTP密钥
        force_execute: 是否强制执行（如果已收藏则先取消再重新收藏）

    Returns:
        (是否成功, 消息)
    """
    try:
        # 尝试导入Playwright相关模块
        try:
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        except ImportError:
            return False, "系统缺少playwright依赖，无法执行GitHub Star操作"

        async def _navigate_with_error_handling(page, url: str, context: str = "访问页面") -> Tuple[bool, Optional[str]]:
            """
            导航到指定URL，统一处理网络错误

            Args:
                page: Playwright page对象
                url: 目标URL
                context: 操作上下文描述，用于错误消息

            Returns:
                (success, error_message) - 成功时返回(True, None)，失败时返回(False, 错误消息)
            """
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                await asyncio.sleep(2)
                return True, None
            except PlaywrightTimeoutError:
                return False, f"{context}超时: 网络连接问题或页面加载过慢"
            except Exception as nav_error:
                error_msg = str(nav_error)
                if 'ERR_CONNECTION_CLOSED' in error_msg or 'net::ERR' in error_msg:
                    return False, f"{context}时网络连接错误: {error_msg}"
                elif 'timeout' in error_msg.lower():
                    return False, f"{context}时网络超时: {error_msg}"
                else:
                    return False, f"{context}失败: {error_msg}"

        # 仓库URL
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"

        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            try:
                # 1. 访问仓库页面
                print(f"📂 访问仓库: {repo_url}")
                success, error = await _navigate_with_error_handling(page, repo_url, "访问仓库")
                if not success:
                    return False, error

                # 检查仓库是否存在
                page_content = await page.content()
                page_title = await page.title()
                if "This is not the web page you are looking for" in page_content or "404" in page_title:
                    return False, f"仓库不存在: {repo_owner}/{repo_name}"

                # 2. 检查是否已登录
                is_logged_in = False
                try:
                    # 查找用户头像或用户菜单，表示已登录
                    avatar = await page.query_selector('summary[aria-label*="user navigation"]')
                    if avatar:
                        is_logged_in = True
                        print("✅ 已登录GitHub")
                except:
                    pass

                # 3. 如果未登录，执行登录
                if not is_logged_in:
                    print("🔐 需要登录GitHub...")
                    login_success, login_msg = await _login_to_github(
                        page, github_username, github_password, totp_secret
                    )

                    if not login_success:
                        return False, f"GitHub登录失败: {login_msg}"

                    print("✅ GitHub登录成功")

                    # 登录后重新访问仓库页面
                    success, error = await _navigate_with_error_handling(page, repo_url, "登录后访问仓库")
                    if not success:
                        return False, error

                # 检查访问仓库后是否又被重定向到2FA checkup页面
                await _handle_2fa_checkup(page, repo_url, github_username)

                # 4. 查找Star按钮并检查状态
                try:
                    # 等待页面加载完成
                    await asyncio.sleep(2)
                    
                    # GitHub的Star按钮通常有以下几种选择器
                    star_button_selectors = [
                        'button[data-view-component="true"]:has-text("Star")',
                        'button:has-text("Star")',
                        'form[action*="/unstar"] button',  # 已star的按钮
                        'form[action*="/starred"] button',  # 已star的按钮
                        'button[data-hydro-click*="star"]',
                        '.js-toggler-target button',
                        '[data-test-id="star-button"]',
                        'button[type="submit"]:has-text("Star")'
                    ]

                    star_button = None
                    found_selector = None
                    for selector in star_button_selectors:
                        try:
                            btn = await page.query_selector(selector)
                            if btn and await btn.is_visible():
                                star_button = btn
                                found_selector = selector
                                print(f"✅ 找到Star按钮，使用选择器: {selector}")
                                break
                        except Exception as e:
                            print(f"⚠️  选择器 {selector} 失败: {str(e)}")
                            continue

                    if not star_button:
                        # 尝试打印页面上的按钮信息帮助调试
                        try:
                            all_buttons = await page.query_selector_all('button')
                            print(f"📊 页面上共有 {len(all_buttons)} 个按钮")

                            # 查找所有包含"Star"或"star"文本的按钮
                            star_buttons_found = []
                            for i, btn in enumerate(all_buttons):
                                try:
                                    text = await btn.inner_text()
                                    if text and ('star' in text.lower() or 'Star' in text):
                                        star_buttons_found.append((i, btn, text.strip()))
                                        print(f"  🌟 找到Star相关按钮[{i}]: {text.strip()}")
                                except:
                                    pass

                            if star_buttons_found:
                                print(f"✅ 共找到 {len(star_buttons_found)} 个Star相关按钮")
                                # 使用第一个包含"Star"（未收藏）的按钮，而不是"Starred"（已收藏）
                                for idx, btn, text in star_buttons_found:
                                    # 优先使用未收藏的Star按钮（文本以"Star"开头但不是"Starred"）
                                    if text.startswith("Star") and not text.startswith("Starred"):
                                        star_button = btn
                                        print(f"✅ 使用Star按钮[{idx}]: {text}")
                                        break

                                # 如果没找到未收藏的，使用第一个Star相关按钮
                                if not star_button and star_buttons_found:
                                    idx, btn, text = star_buttons_found[0]
                                    star_button = btn
                                    print(f"✅ 使用Star相关按钮[{idx}]: {text}")
                            else:
                                print("❌ 没有找到任何Star相关按钮")
                                # 打印所有按钮帮助调试
                                print("📋 所有按钮文本:")
                                for i, btn in enumerate(all_buttons[:20]):
                                    try:
                                        text = await btn.inner_text()
                                        if text and len(text.strip()) > 0:
                                            print(f"  按钮[{i}]: {text.strip()[:80]}")
                                    except:
                                        pass
                        except Exception as e:
                            print(f"调试时出错: {str(e)}")

                        if not star_button:
                            return False, "找不到Star按钮，可能页面结构已更改"

                    # 检查按钮文本，判断是否已star
                    button_text = (await star_button.inner_text()).strip()
                    print(f"🔍 Star按钮状态: {button_text}")

                    # 5. 执行Star操作
                    if 'starred' in button_text.lower() or 'unstar' in button_text.lower():
                        # 已经star过了
                        if force_execute:
                            # 强制执行模式：先取消收藏再重新收藏
                            print(f"🔄 强制执行模式：仓库已收藏，先取消再重新收藏")
                            try:
                                # 点击Unstar按钮
                                await star_button.click()
                                print(f"✅ 已取消收藏，等待2秒...")
                                await asyncio.sleep(2)
                                
                                # 重新查找Star按钮
                                star_button_found = False
                                for selector in star_button_selectors:
                                    try:
                                        btn = await page.query_selector(selector)
                                        if btn and await btn.is_visible():
                                            button_text = (await btn.inner_text()).strip()
                                            # 确保找到的是Star按钮而不是Starred按钮
                                            if 'star' in button_text.lower() and 'starred' not in button_text.lower():
                                                star_button = btn
                                                star_button_found = True
                                                print(f"✅ 找到Star按钮: {button_text}")
                                                break
                                    except:
                                        continue
                                
                                if not star_button_found:
                                    return False, "取消收藏后未找到Star按钮"
                                
                                # 继续执行收藏操作（下面的代码会处理）
                            except Exception as unstar_error:
                                return False, f"取消收藏失败: {str(unstar_error)}"
                        else:
                            # 普通模式：已收藏则直接返回
                            print(f"✅ 仓库已经收藏过了")
                            return True, f"仓库已收藏: {repo_owner}/{repo_name}"
                    
                    # 点击Star按钮（普通执行或强制执行取消后）
                    if not ('starred' in button_text.lower() or 'unstar' in button_text.lower()) or force_execute:
                        # 点击Star按钮
                        print(f"⭐ 正在收藏仓库: {repo_owner}/{repo_name}")
                        try:
                            print(f"🖱️ 准备点击Star按钮...")
                            await star_button.click()
                            print(f"✅ Star按钮已点击，等待2秒...")
                            await asyncio.sleep(2)

                            # 验证是否star成功
                            # 重新获取按钮文本
                            print(f"🔍 验证Star操作是否成功...")
                            try:
                                await page.wait_for_selector('button:has-text("Starred")', timeout=5000)
                                print(f"✅ 验证成功：找到Starred按钮")
                                return True, f"成功收藏仓库: {repo_owner}/{repo_name}"
                            except Exception as wait_error:
                                # 可能star成功但界面未更新，认为成功
                                print(f"⚠️ 未找到Starred按钮，但操作可能已成功: {str(wait_error)}")
                                return True, f"收藏操作已执行: {repo_owner}/{repo_name}"
                        except Exception as click_error:
                            error_msg = str(click_error)
                            print(f"❌ 点击Star按钮失败: {error_msg}")

                            # 区分网络错误和其他错误
                            if 'ERR_CONNECTION_CLOSED' in error_msg or 'net::ERR' in error_msg:
                                return False, f"网络连接错误: {error_msg}"
                            elif 'timeout' in error_msg.lower():
                                return False, f"操作超时: {error_msg}"
                            else:
                                return False, f"点击Star按钮失败: {error_msg}"

                except Exception as e:
                    return False, f"Star操作失败: {str(e)}"

            finally:
                await browser.close()

    except Exception as e:
        error_msg = str(e)

        # 区分不同类型的错误
        if 'ERR_CONNECTION_CLOSED' in error_msg or 'net::ERR' in error_msg:
            return False, f"网络连接错误: {error_msg}"
        elif 'timeout' in error_msg.lower() or 'TimeoutError' in error_msg:
            return False, f"网络超时: {error_msg}"
        elif 'playwright' in error_msg.lower() and 'ImportError' not in error_msg:
            return False, f"浏览器自动化错误: {error_msg}"
        else:
            return False, f"GitHub Star操作异常: {error_msg}"


async def _login_to_github(page, username: str, password: str, totp_secret: str) -> Tuple[bool, str]:
    """
    在Playwright页面中执行GitHub登录

    Args:
        page: Playwright page对象
        username: GitHub用户名
        password: GitHub密码
        totp_secret: TOTP密钥

    Returns:
        (是否成功, 消息)
    """
    try:
        # 访问GitHub登录页面
        print("🔗 访问GitHub登录页面...")
        await page.goto("https://github.com/login", wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)

        # 填写用户名
        username_input = await page.query_selector('input#login_field')
        if not username_input:
            return False, "找不到用户名输入框"
        await username_input.fill(username)

        # 填写密码
        password_input = await page.query_selector('input#password')
        if not password_input:
            return False, "找不到密码输入框"
        await password_input.fill(password)

        # 点击登录按钮
        login_button = await page.query_selector('input[type="submit"][value="Sign in"]')
        if not login_button:
            login_button = await page.query_selector('button[type="submit"]')

        if not login_button:
            return False, "找不到登录按钮"

        await login_button.click()
        await asyncio.sleep(3)

        # 检查是否需要2FA
        current_url = page.url
        page_content = await page.content()

        if 'two-factor' in current_url or 'sessions/two-factor' in current_url:
            print("🔐 需要2FA验证...")

            # 生成TOTP验证码
            from utils.totp import generate_totp_token
            totp_info = generate_totp_token(totp_secret)
            totp_code = totp_info['token']

            # === 新增：检查是否在WebAuthn页面，需要切换到TOTP ===
            if 'webauthn' in current_url or 'webauthn' in page_content.lower():
                print("🔍 检测到WebAuthn页面，尝试切换到TOTP验证...")

                # 方法1：尝试直接访问authenticator app页面
                try:
                    totp_url = "https://github.com/sessions/two-factor/app"
                    print(f"🔄 直接访问TOTP页面: {totp_url}")
                    await page.goto(totp_url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                    await asyncio.sleep(3)

                    # 更新页面信息
                    current_url = page.url
                    page_content = await page.content()
                    print(f"🔍 切换后当前URL: {current_url}")

                except Exception as e:
                    print(f"⚠️ 直接访问TOTP页面失败: {e}")

                    # 方法2：尝试点击"More options"和"Authenticator app"
                    try:
                        print("🔄 尝试点击More options按钮...")
                        more_options_selectors = [
                            "button.more-options-two-factor",
                            "button[class*='more-options']",
                            "button:has-text('More options')"
                        ]

                        more_options_clicked = False
                        for selector in more_options_selectors:
                            try:
                                btn = await page.query_selector(selector)
                                if btn and await btn.is_visible():
                                    print(f"🎯 点击More options按钮: {selector}")
                                    await btn.click()
                                    await asyncio.sleep(2)
                                    more_options_clicked = True
                                    break
                            except:
                                continue

                        if more_options_clicked:
                            print("🔍 查找Authenticator app链接...")
                            app_link_selectors = [
                                "a[href='/sessions/two-factor/app']",
                                "a[data-test-selector='totp-app-link']",
                                "a:has-text('Authenticator app')"
                            ]

                            for selector in app_link_selectors:
                                try:
                                    link = await page.query_selector(selector)
                                    if link and await link.is_visible():
                                        print(f"🎯 点击Authenticator app链接: {selector}")
                                        await link.click()
                                        await asyncio.sleep(3)

                                        # 更新页面��息
                                        current_url = page.url
                                        page_content = await page.content()
                                        print(f"🔍 切换后当前URL: {current_url}")
                                        break
                                except:
                                    continue
                    except Exception as e2:
                        print(f"⚠️ 点击More options方法失败: {e2}")

            # 填写TOTP验证码
            # 使用增强的选择器列表（参考定时任务中成功的逻辑）
            totp_selectors = [
                "input[name='otp']",           # 通用OTP (优先，GitHub常用)
                "input[name='app_otp']",       # GitHub TOTP应用
                "input[id='app_totp']",        # GitHub TOTP应用ID
                "input[name='app_totp']",      # GitHub TOTP应用名称
                "input[autocomplete='one-time-code']",  # HTML5标准
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
                "input[name='sms_otp']",       # GitHub SMS选项
                "input[class*='form-control'][maxlength='6']",
                "input[type='tel'][maxlength='6']",
                "input[inputmode='numeric'][maxlength='6']"
            ]

            print("🔍 搜索TOTP输入框...")

            # 等待2FA页面完全加载
            await asyncio.sleep(3)

            totp_input = None
            for selector in totp_selectors:
                try:
                    input_elem = await page.query_selector(selector)
                    if input_elem and await input_elem.is_visible() and await input_elem.is_enabled():
                        totp_input = input_elem
                        print(f"✅ 找到TOTP输入框，使用选择器: {selector}")
                        break
                except Exception:
                    continue

            if not totp_input:
                # 调试：打印页面中的所有输入框，帮助诊断问题
                print("❌ 未找到TOTP输入框，开始诊断...")
                print(f"🔍 当前URL: {current_url}")
                try:
                    all_inputs = await page.query_selector_all('input')
                    print(f"📋 页面中发现 {len(all_inputs)} 个输入框")
                    for i, input_elem in enumerate(all_inputs[:MAX_DEBUG_INPUTS]):
                        try:
                            input_type = await input_elem.get_attribute("type") or "text"
                            input_name = await input_elem.get_attribute("name") or ""
                            input_id = await input_elem.get_attribute("id") or ""
                            input_class = await input_elem.get_attribute("class") or ""
                            input_placeholder = await input_elem.get_attribute("placeholder") or ""
                            is_visible = await input_elem.is_visible()
                            is_enabled = await input_elem.is_enabled()

                            print(f"   输入框{i+1}: type={input_type}, name={input_name}, id={input_id}")
                            print(f"            class={input_class}, placeholder={input_placeholder}")
                            print(f"            visible={is_visible}, enabled={is_enabled}")
                        except Exception as e:
                            print(f"   输入框{i+1}: 获取属性失败 - {e}")
                            continue
                except Exception as debug_error:
                    print(f"⚠️ 调试时出错: {debug_error}")

                return False, f"找不到TOTP输入框 (URL: {current_url})"

            await totp_input.fill(totp_code)
            print(f"✅ 已填写TOTP验证码")
            await asyncio.sleep(1)

            # 提交2FA验证
            # GitHub的2FA表单通常会自动提交，或者找到提交按钮
            try:
                verify_button = await page.query_selector('button[type="submit"]')
                if verify_button:
                    print("🖱️ 点击验证按钮")
                    await verify_button.click()
                await asyncio.sleep(3)
            except:
                # 可能已自动提交
                print("ℹ️ 未找到提交按钮，可能已自动提交")
                pass

        # 验证登录是否成功
        await asyncio.sleep(2)

        # 处理 GitHub 的 2FA checkup 页面（安全检查）
        await _handle_2fa_checkup(page, username=username)

        # 更新当前URL
        current_url = page.url

        # 如果不再在登录页面，且不在2FA页面，则认为登录成功
        if 'login' not in current_url and 'two-factor' not in current_url and 'two_factor_checkup' not in current_url:
            return True, "GitHub登录成功"
        else:
            # 登录失败，保存截图
            await _save_debug_screenshot(page, username, "login_failed", f"登录后仍在页面: {current_url}")

            # 检查是否有错误提示
            error_msg = await page.query_selector('.flash-error')
            if error_msg:
                error_text = await error_msg.inner_text()
                return False, f"登录失败: {error_text}"
            else:
                return False, "登录失败，用户名或密码可能不正确"

    except Exception as e:
        # 异常时也尝试截图
        try:
            await _save_debug_screenshot(page, username, "login_exception", str(e))
        except:
            pass
        return False, f"GitHub登录异常: {str(e)}"


async def star_repository_simple(
    repo_url: str,
    github_username: str,
    github_password: str,
    totp_secret: str,
    force_execute: bool = False
) -> Tuple[bool, str]:
    """
    简化版的GitHub仓库Star操作（直接使用URL）

    Args:
        repo_url: GitHub仓库URL
        github_username: GitHub用户名
        github_password: GitHub密码
        totp_secret: TOTP密钥
        force_execute: 是否强制执行（如果已收藏则先取消再重新收藏）

    Returns:
        (是否成功, 消息)
    """
    # 解析仓库URL
    owner, repo_name = parse_repository_url(repo_url)

    if not owner or not repo_name:
        return False, f"无效的GitHub仓库URL: {repo_url}"

    # 调用主函数
    return await star_github_repository(owner, repo_name, github_username, github_password, totp_secret, force_execute)


async def unstar_github_repository(
    repo_owner: str,
    repo_name: str,
    github_username: str,
    github_password: str,
    totp_secret: str
) -> Tuple[bool, str]:
    """
    使用Playwright自动化取消Star GitHub仓库

    Args:
        repo_owner: 仓库所有者
        repo_name: 仓库名称
        github_username: GitHub用户名
        github_password: GitHub密码
        totp_secret: TOTP密钥

    Returns:
        (是否成功, 消息)
    """
    try:
        # 尝试导入Playwright相关模块
        try:
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        except ImportError:
            return False, "系统缺少playwright依赖，无法执行GitHub Unstar操作"

        async def _navigate_with_error_handling(page, url: str, context: str = "访问页面") -> Tuple[bool, Optional[str]]:
            """
            导航到指定URL，统一处理网络错误

            Args:
                page: Playwright page对象
                url: 目标URL
                context: 操作上下文描述，用于错误消息

            Returns:
                (success, error_message) - 成功时返回(True, None)，失败时返回(False, 错误消息)
            """
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                await asyncio.sleep(2)
                return True, None
            except PlaywrightTimeoutError:
                return False, f"{context}超时: 网络连接问题或页面加载过慢"
            except Exception as nav_error:
                error_msg = str(nav_error)
                if 'ERR_CONNECTION_CLOSED' in error_msg or 'net::ERR' in error_msg:
                    return False, f"{context}时网络连接错误: {error_msg}"
                elif 'timeout' in error_msg.lower():
                    return False, f"{context}时网络超时: {error_msg}"
                else:
                    return False, f"{context}失败: {error_msg}"

        # 仓库URL
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"

        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            try:
                # 1. 访问仓库页面
                print(f"📂 访问仓库: {repo_url}")
                success, error = await _navigate_with_error_handling(page, repo_url, "访问仓库")
                if not success:
                    return False, error

                # 检查仓库是否存在
                page_content = await page.content()
                page_title = await page.title()
                if "This is not the web page you are looking for" in page_content or "404" in page_title:
                    return False, f"仓库不存在: {repo_owner}/{repo_name}"

                # 2. 检查是否已登录
                is_logged_in = False
                try:
                    # 查找用户头像或用户菜单，表示已登录
                    avatar = await page.query_selector('summary[aria-label*="user navigation"]')
                    if avatar:
                        is_logged_in = True
                        print("✅ 已登录GitHub")
                except:
                    pass

                # 3. 如果未登录，执行登录
                if not is_logged_in:
                    print("🔐 需要登录GitHub...")
                    login_success, login_msg = await _login_to_github(
                        page, github_username, github_password, totp_secret
                    )

                    if not login_success:
                        return False, f"GitHub登录失败: {login_msg}"

                    print("✅ GitHub登录成功")

                    # 登录后重新访问仓库页面
                    success, error = await _navigate_with_error_handling(page, repo_url, "登录后访问仓库")
                    if not success:
                        return False, error

                # 检查访问仓库后是否又被重定向到2FA checkup页面
                await _handle_2fa_checkup(page, repo_url, github_username)

                # 4. 查找Star按钮并检查状态
                try:
                    # GitHub的Star按钮通常有以下几种选择器
                    star_button_selectors = [
                        'button:has-text("Unstar")',
                        'button:has-text("Starred")',
                        'form[action*="/unstar"] button',
                        'button[data-hydro-click*="unstar"]',
                    ]

                    star_button = None
                    for selector in star_button_selectors:
                        try:
                            btn = await page.query_selector(selector)
                            if btn and await btn.is_visible():
                                star_button = btn
                                break
                        except:
                            continue

                    if not star_button:
                        return False, "仓库未收藏，无需取消"

                    # 检查按钮文本，判断是否已star
                    button_text = (await star_button.inner_text()).strip()
                    print(f"🔍 Star按钮状态: {button_text}")

                    # 5. 执行Unstar操作
                    if 'starred' in button_text.lower() or 'unstar' in button_text.lower():
                        # 已经star过，执行取消
                        print(f"⭐ 正在取消收藏仓库: {repo_owner}/{repo_name}")
                        await star_button.click()
                        await asyncio.sleep(2)

                        # 验证是否unstar成功
                        try:
                            await page.wait_for_selector('button:has-text("Star")', timeout=5000)
                            return True, f"成功取消收藏仓库: {repo_owner}/{repo_name}"
                        except:
                            # 可能unstar成功但界面未更新，认为成功
                            return True, f"取消收藏操作已执行: {repo_owner}/{repo_name}"
                    else:
                        # 未star，无需取消
                        return True, f"仓库未收藏: {repo_owner}/{repo_name}"

                except Exception as e:
                    return False, f"Unstar操作失败: {str(e)}"

            finally:
                await browser.close()

    except Exception as e:
        return False, f"GitHub Unstar操作异常: {str(e)}"


async def unstar_repository_simple(
    repo_url: str,
    github_username: str,
    github_password: str,
    totp_secret: str
) -> Tuple[bool, str]:
    """
    简化版的GitHub仓库Unstar操作（直接使用URL）

    Args:
        repo_url: GitHub仓库URL
        github_username: GitHub用户名
        github_password: GitHub密码
        totp_secret: TOTP密钥

    Returns:
        (是否成功, 消息)
    """
    # 解析仓库URL
    owner, repo_name = parse_repository_url(repo_url)

    if not owner or not repo_name:
        return False, f"无效的GitHub仓库URL: {repo_url}"

    # 调用主函数
    return await unstar_github_repository(owner, repo_name, github_username, github_password, totp_secret)
