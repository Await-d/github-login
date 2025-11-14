"""
GitHub仓库Star操作工具
使用Playwright自动化GitHub仓库收藏（Star）功能
"""

import re
from typing import Tuple, Optional
from urllib.parse import urlparse
import asyncio


def parse_repository_url(repo_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析GitHub仓库URL，提取owner和repo_name
    
    Args:
        repo_url: GitHub仓库URL (如 https://github.com/owner/repo)
        
    Returns:
        (owner, repo_name) 或 (None, None) 如果解析失败
    """
    try:
        # 移除末尾的斜杠和.git后缀
        repo_url = repo_url.rstrip('/').replace('.git', '')
        
        # 使用正则表达式匹配GitHub仓库URL
        # 支持格式: https://github.com/owner/repo 或 github.com/owner/repo
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, repo_url)
        
        if match:
            owner = match.group(1)
            repo_name = match.group(2)
            return owner, repo_name
        else:
            return None, None
            
    except Exception as e:
        print(f"解析仓库URL失败: {e}")
        return None, None


async def star_github_repository(
    repo_owner: str,
    repo_name: str,
    github_username: str,
    github_password: str,
    totp_secret: str
) -> Tuple[bool, str]:
    """
    使用Playwright自动化Star GitHub仓库

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
            return False, "系统缺少playwright依赖，无法执行GitHub Star操作"

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
                await page.goto(repo_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)
                
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
                    await page.goto(repo_url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(2)
                
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
                        print(f"✅ 仓库已经收藏过了")
                        return True, f"仓库已收藏: {repo_owner}/{repo_name}"
                    else:
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
                            print(f"❌ 点击Star按钮失败: {str(click_error)}")
                            return False, f"点击Star按钮失败: {str(click_error)}"

                except Exception as e:
                    return False, f"Star操作失败: {str(e)}"

            finally:
                await browser.close()
                
    except Exception as e:
        return False, f"GitHub Star操作异常: {str(e)}"


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
        if 'two-factor' in current_url or 'sessions/two-factor' in current_url:
            print("🔐 需要2FA验证...")

            # 生成TOTP验证码
            from utils.totp import generate_totp_token
            totp_info = generate_totp_token(totp_secret)
            totp_code = totp_info['token']

            # 填写TOTP验证码
            # 使用正确的选择器顺序，与定时任务登录保持一致
            totp_input = await page.query_selector('input[name="app_otp"]')
            if not totp_input:
                totp_input = await page.query_selector('input#app_totp')
            if not totp_input:
                totp_input = await page.query_selector('input[name="app_totp"]')

            if not totp_input:
                return False, "找不到TOTP输入框"

            await totp_input.fill(totp_code)
            await asyncio.sleep(1)

            # 提交2FA验证
            # GitHub的2FA表单通常会自动提交，或者找到提交按钮
            try:
                verify_button = await page.query_selector('button[type="submit"]')
                if verify_button:
                    await verify_button.click()
                await asyncio.sleep(3)
            except:
                # 可能已自动提交
                pass

        # 验证登录是否成功
        await asyncio.sleep(2)
        current_url = page.url

        # 如果不再在登录页面，且不在2FA页面，则认为登录成功
        if 'login' not in current_url and 'two-factor' not in current_url:
            return True, "GitHub登录成功"
        else:
            # 检查是否有错误提示
            error_msg = await page.query_selector('.flash-error')
            if error_msg:
                error_text = await error_msg.inner_text()
                return False, f"登录失败: {error_text}"
            else:
                return False, "登录失败，用户名或密码可能不正确"
        
    except Exception as e:
        return False, f"GitHub登录异常: {str(e)}"


async def star_repository_simple(
    repo_url: str,
    github_username: str,
    github_password: str,
    totp_secret: str
) -> Tuple[bool, str]:
    """
    简化版的GitHub仓库Star操作（直接使用URL）

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
    return await star_github_repository(owner, repo_name, github_username, github_password, totp_secret)


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
                await page.goto(repo_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)

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
                    await page.goto(repo_url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(2)

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
