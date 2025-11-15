"""
任务执行器 - 执行各种类型的定时任务
"""

import json
import asyncio
import re
from datetime import datetime, timezone
from typing import Tuple, Any, Dict, Optional
from sqlalchemy.orm import Session

from models.database import ScheduledTask, TaskExecutionLog, GitHubAccount, AccountBalanceSnapshot
from models.schemas import GitHubOAuthTaskParams
from utils.encryption import decrypt_data
from utils.browser_simulator import BrowserSimulator
from utils.task_scheduler import calculate_next_run_time
from utils.task_monitor import task_monitor, task_logger, AccountExecutionResult
from typing import Tuple, Dict


async def execute_task(task: ScheduledTask, db_session: Session) -> Tuple[bool, str]:
    """
    执行定时任务 - 增强版带监控
    
    Args:
        task: 定时任务对象
        db_session: 数据库会话
    
    Returns:
        (是否成功, 结果消息)
    """
    start_time = datetime.now(timezone.utc)
    execution_log = None
    
    # 使用监控器
    with task_monitor.monitor_task_execution(task.id, task.name) as metrics:
        try:
            # 创建执行日志
            execution_log = TaskExecutionLog(
                task_id=task.id,
                start_time=start_time,
                status="running"
            )
            db_session.add(execution_log)
            db_session.commit()
            
            # 标记任务为运行中
            from utils.task_scheduler import task_scheduler
            task_scheduler.mark_task_running(task.id)
            
            # 根据任务类型执行不同的逻辑
            if task.task_type == "github_oauth_login":
                success, result, execution_data = await execute_github_oauth_task(
                    task,
                    db_session,
                    execution_log=execution_log
                )
            else:
                success = False
                result = f"未知的任务类型: {task.task_type}"
                execution_data = {}
            
            # 记录执行结果
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            # 更新执行日志
            execution_log.end_time = end_time
            execution_log.duration = duration
            execution_log.status = "success" if success else "failed"
            execution_log.result_message = result
            execution_log.execution_data = json.dumps(execution_data) if execution_data else None
            
            if not success:
                execution_log.error_details = result
            
            # 更新任务统计信息
            task.run_count += 1
            if success:
                task.success_count += 1
            else:
                task.error_count += 1
            
            task.last_run_time = start_time
            task.last_result = result[:500]  # 限制结果长度
            
            # 计算下次执行时间
            try:
                next_run = calculate_next_run_time(task.cron_expression, task.timezone)
                task.next_run_time = next_run
            except Exception as e:
                print(f"计算下次执行时间失败: {e}")
            
            db_session.commit()
            
            return success, result
        
        except Exception as e:
            error_msg = f"任务执行异常: {str(e)}"
            
            if execution_log:
                # 更新执行日志
                end_time = datetime.now(timezone.utc)
                execution_log.end_time = end_time
                
                # 安全地计算持续时间
                try:
                    original_start = execution_log.start_time
                    if isinstance(original_start, str):
                        original_start = datetime.fromisoformat(original_start.replace('Z', '+00:00'))
                    if isinstance(original_start, datetime):
                        if original_start.tzinfo is None:
                            original_start = original_start.replace(tzinfo=timezone.utc)
                        execution_log.duration = (end_time - original_start).total_seconds()
                    else:
                        execution_log.duration = 0
                        print(f"⚠️ execution_log.start_time类型未知: {type(execution_log.start_time)}")
                except Exception as duration_error:
                    print(f"⚠️ 计算执行日志持续时间失败: {duration_error}")
                    execution_log.duration = 0
                execution_log.status = "failed"
                execution_log.result_message = error_msg
                execution_log.error_details = str(e)
                
                # 更新任务统计
                task.run_count += 1
                task.error_count += 1
                task.last_run_time = start_time
                task.last_result = error_msg[:500]
                
                db_session.commit()
            
            return False, error_msg
        
        finally:
            # 标记任务完成
            from utils.task_scheduler import task_scheduler
            task_scheduler.mark_task_completed(task.id)


async def execute_github_oauth_task(
    task: ScheduledTask,
    db_session: Session,
    execution_log: Optional[TaskExecutionLog] = None
) -> Tuple[bool, str, Dict]:
    """
    执行GitHub OAuth登录任务 - 增强版带监控和日志
    
    Args:
        task: 任务对象
        db_session: 数据库会话
    
    Returns:
        (是否成功, 结果消息, 执行数据)
    """
    try:
        # 解析任务参数
        task_params = GitHubOAuthTaskParams.model_validate(json.loads(task.task_params))
        
        # 获取GitHub账号信息
        github_accounts = db_session.query(GitHubAccount).filter(
            GitHubAccount.id.in_(task_params.github_account_ids),
            GitHubAccount.user_id == task.user_id
        ).all()
        
        if not github_accounts:
            return False, "未找到有效的GitHub账号", {}

        results = []
        success_count = 0
        total_count = len(github_accounts)

        # 批量查询所有账号的上一次余额记录（优化性能，避免N+1查询）
        account_ids = [acc.id for acc in github_accounts]
        previous_snapshots_query = db_session.query(AccountBalanceSnapshot).filter(
            AccountBalanceSnapshot.account_id.in_(account_ids)
        ).order_by(
            AccountBalanceSnapshot.account_id,
            AccountBalanceSnapshot.snapshot_time.desc()
        ).all()

        # 为每个账号保留最新的快照（已按时间倒序排序）
        previous_snapshot_map = {}
        for snapshot in previous_snapshots_query:
            if snapshot.account_id not in previous_snapshot_map:
                previous_snapshot_map[snapshot.account_id] = snapshot

        # 记录任务开始
        task_logger.log_task_start(task.id, task.name, total_count)
        
        for account in github_accounts:
            account_start_time = datetime.now(timezone.utc)

            try:
                # 解密账号信息
                username = account.username
                password = decrypt_data(account.encrypted_password)
                totp_secret = decrypt_data(account.encrypted_totp_secret)
                
                # 记录账户开始处理
                task_logger.log_account_start(task.id, account.id, username)
                
                # 执行OAuth登录带重试机制
                login_success, message, session_data = await execute_oauth_with_retry(
                    task_params,
                    username,
                    password,
                    totp_secret,
                    task.id  # 传递task_id用于监控
                )
                
                # 计算处理时间
                account_end_time = datetime.now(timezone.utc)
                account_duration = (account_end_time - account_start_time).total_seconds()
                
                # 创建账户执行结果
                account_execution_result = AccountExecutionResult(
                    account_id=account.id,
                    username=username,
                    status="success" if login_success else "failed",
                    start_time=account_start_time,
                    end_time=account_end_time,
                    duration=account_duration,
                    message=message,
                    error_type=session_data.get('error_type') if not login_success else None,
                    retry_count=session_data.get('retry_count', 0),
                    final_url=session_data.get('final_url'),
                    cookies_count=len(session_data.get('cookies', {}))
                )
                
                # 记录账户结果
                task_logger.log_account_result(task.id, account_execution_result)
                
                # 更新监控指标
                task_monitor.update_account_metrics(task.id, account_execution_result)
                
                # 构建结果数据
                account_result = {
                    "account_id": account.id,
                    "username": username,
                    "success": login_success,
                    "message": message,
                    "duration": account_duration,
                    "login_time": account_start_time.isoformat() if login_success else None,
                    "session_cookies": len(session_data.get('cookies', {})) if login_success else 0,
                    "error_details": session_data.get('error_details') if not login_success else None,
                    "retry_count": session_data.get('retry_count', 0),
                    # 添加余额信息
                    "balance": session_data.get('balance'),
                    "balance_currency": session_data.get('balance_currency'),
                    "balance_raw_text": session_data.get('balance_raw_text'),
                    "balance_extraction_error": session_data.get('balance_extraction_error')
                }

                results.append(account_result)

                if login_success:
                    success_count += 1
                else:
                    # 记录错误类型
                    account_execution_result.error_type = 确定错误类型(message)

                _record_account_balance_snapshot(
                    db_session,
                    task,
                    execution_log,
                    account,
                    account_result,
                    previous_snapshot_map.get(account.id)  # 从预加载的map中获取
                )

            except Exception as e:
                # 计算处理时间
                account_end_time = datetime.now(timezone.utc)
                account_duration = (account_end_time - account_start_time).total_seconds()
                
                # 创建异常结果
                account_execution_result = AccountExecutionResult(
                    account_id=account.id,
                    username=account.username,
                    status="failed",
                    start_time=account_start_time,
                    end_time=account_end_time,
                    duration=account_duration,
                    message=f"执行异常: {str(e)}",
                    error_type="system_exception"
                )
                
                # 记录账户结果
                task_logger.log_account_result(task.id, account_execution_result)
                
                # 更新监控指标
                task_monitor.update_account_metrics(task.id, account_execution_result)
                
                account_result = {
                    "account_id": account.id,
                    "username": account.username,
                    "success": False,
                    "message": f"执行异常: {str(e)}",
                    "duration": account_duration,
                    "error": str(e),
                    "error_type": "system_exception"
                }
                results.append(account_result)

                _record_account_balance_snapshot(
                    db_session,
                    task,
                    execution_log,
                    account,
                    account_result,
                    previous_snapshot_map.get(account.id)  # 从预加载的map中获取
                )
        
        # 记录任务完成
        # 安全地计算任务持续时间
        task_duration = 0
        try:
            if task_logger.log_entries:
                # 查找任务开始时间
                start_time_entry = next((log for log in task_logger.log_entries if log["event"] == "task_start" and log["task_id"] == task.id), None)
                if start_time_entry:
                    start_timestamp = start_time_entry["timestamp"]
                    
                    # 处理不同类型的时间戳
                    if isinstance(start_timestamp, str):
                        # 字符串时间戳，需要解析
                        start_time = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
                    elif isinstance(start_timestamp, datetime):
                        # 已经是datetime对象
                        start_time = start_timestamp
                    else:
                        # 其他类型，尝试转换
                        start_time = datetime.fromisoformat(str(start_timestamp))
                    
                    # 计算持续时间
                    task_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                else:
                    print("⚠️ 未找到任务开始时间记录，使用默认值")
                    task_duration = 0
            else:
                print("⚠️ 没有日志条目，使用默认持续时间")
                task_duration = 0
        except Exception as e:
            print(f"⚠️ 计算任务持续时间失败: {e}")
            task_duration = 0
        
        task_logger.log_task_complete(task.id, success_count, total_count, task_duration)
        
        # 构建详细的结果消息
        result_lines = [f"GitHub OAuth登录任务完成: {success_count}/{total_count} 成功"]
        
        # 添加每个账户的详细信息
        for result in results:
            username = result.get('username', 'N/A')
            if result.get('success'):
                duration = result.get('duration', 0)
                # 添加余额信息（如果有）
                balance_info = ""
                if result.get('balance') and result.get('balance_currency'):
                    balance_info = f" | 余额: {result.get('balance')} {result.get('balance_currency')}"
                result_lines.append(f"  ✅ {username}: 登录成功 ({duration:.1f}s){balance_info}")
            else:
                error_details = result.get('error_details', result.get('message', '未知错误'))
                result_lines.append(f"  ❌ {username}: {error_details}")
        
        result_message = "\n".join(result_lines)
        
        execution_data = {
            "target_website": task_params.target_website,
            "total_accounts": total_count,
            "success_count": success_count,
            "failed_count": total_count - success_count,
            "results": results,
            "task_params": task_params.model_dump()
        }
        
        # 如果全部失败，认为任务失败
        overall_success = success_count > 0
        
        return overall_success, result_message, execution_data
    
    except Exception as e:
        return False, f"GitHub OAuth任务执行失败: {str(e)}", {"error": str(e)}


class TaskExecutor:
    """任务执行器类"""
    
    def __init__(self):
        self.running_tasks = {}  # task_id -> asyncio.Task
    
    async def execute_task_async(self, task: ScheduledTask, db_session: Session):
        """异步执行任务"""
        task_id = task.id
        
        if task_id in self.running_tasks:
            print(f"任务 {task_id} 已在运行中，跳过")
            return
        
        try:
            # 创建异步任务
            async_task = asyncio.create_task(execute_task(task, db_session))
            self.running_tasks[task_id] = async_task
            
            # 等待任务完成
            success, result = await async_task
            
            print(f"任务 {task_id} 执行完成: {'成功' if success else '失败'} - {result}")
            
        except Exception as e:
            print(f"任务 {task_id} 执行异常: {e}")
        
        finally:
            # 清理运行记录
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def is_task_running(self, task_id: int) -> bool:
        """检查任务是否正在运行"""
        return task_id in self.running_tasks
    
    def get_running_task_count(self) -> int:
        """获取正在运行的任务数量"""
        return len(self.running_tasks)
    
    async def stop_task(self, task_id: int):
        """停止正在运行的任务"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                del self.running_tasks[task_id]
                print(f"任务 {task_id} 已停止")


def 确定错误类型(error_message: str) -> str:
    """根据错误消息确定错误类型"""
    error_lower = error_message.lower()
    
    if "未找到github" in error_lower or "github账号" in error_lower:
        return "account_not_found"
    elif "登录失败" in error_lower or "仍在登录页面" in error_lower:
        return "login_failed"
    elif "未找到" in error_lower and "输入框" in error_lower:
        return "ui_element_missing"
    elif "2fa" in error_lower or "验证码" in error_lower:
        return "2fa_failed"
    elif "oauth" in error_lower:
        return "oauth_failed"
    elif "网络" in error_lower or "timeout" in error_lower:
        return "network_error"
    elif "异常" in error_lower or "exception" in error_lower:
        return "system_exception"
    else:
        return "unknown_error"


async def execute_oauth_with_retry(
    task_params,
    username: str,
    password: str, 
    totp_secret: str,
    task_id: int = None
) -> Tuple[bool, str, Dict]:
    """
    带重试机制的OAuth登录执行
    """
    max_retries = max(1, task_params.retry_count)
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                if task_id:
                    task_logger.log_retry_attempt(task_id, 0, username, attempt + 1, max_retries, last_error or "未知错误")
                else:
                    print(f"🔄 第{attempt + 1}次重试 (/{max_retries}) - 账户: {username}")
                # 重试前等待一段时间
                await asyncio.sleep(5 + attempt * 2)  # 递增等待时间
            
            success, message, session_data = await asyncio.to_thread(
                execute_github_oauth_with_browser_simulator,
                task_params.target_website,
                username,
                password,
                totp_secret
            )
            
            if success:
                if attempt > 0 and task_id:
                    task_logger.log_browser_event(task_id, 0, f"重试成功 (第{attempt + 1}次尝试)")
                elif attempt > 0:
                    print(f"✅ 第{attempt + 1}次重试成功 - 账户: {username}")
                
                # 为会话数据添加重试信息
                session_data["retry_count"] = attempt
                session_data["error_type"] = None
                
                return success, message, session_data
            else:
                last_error = message
                # 判断是否值得重试
                if not should_retry_oauth_error(message) or attempt == max_retries - 1:
                    break
                    
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ 第{attempt + 1}次尝试异常: {e}")
            
            if attempt == max_retries - 1:
                break
    
    # 添加失败的详细信息
    failure_data = {
        "error_details": last_error,
        "retry_count": max_retries,
        "error_type": determine_error_type(last_error or "")
    }
    
    return False, f"重试{max_retries}次后仍失败: {last_error}", failure_data


def determine_error_type(error_message: str) -> str:
    """
    根据错误消息确定错误类型
    """
    error_msg = error_message.lower()

    # 定义错误关键词列表，提高可读性
    if "2fa" in error_msg or "两个因子" in error_msg or "验证码" in error_msg:
        return "2fa_failed"
    elif "登录" in error_msg or "login" in error_msg:
        return "login_failed"

    # 网络相关错误关键词
    network_keywords = ["网络", "network", "timeout", "超时", "connection", "err_connection"]
    if any(keyword in error_msg for keyword in network_keywords):
        return "network_error"

    # UI元素缺失关键词
    missing_keywords = ["未找到", "not found", "找不到"]
    if any(keyword in error_msg for keyword in missing_keywords):
        return "ui_element_missing"

    elif "webdriver" in error_msg or "browser" in error_msg:
        return "browser_error"
    else:
        return "unknown_error"


def should_retry_oauth_error(error_message: str) -> bool:
    """
    判断错误是否值得重试
    """
    # 不值得重试的错误类型
    non_retryable_errors = [
        "未找到GitHub账户",
        "GitHub登录失败，仍在登录页面",
        "未找到GitHub用户名输入框",
        "未找到GitHub密码输入框",
        "未找到2FA验证码输入框",
        "找不到TOTP输入框",  # TOTP验证码输入框
        "未找到GitHub OAuth登录选项"
    ]
    
    error_lower = error_message.lower()
    
    for non_retryable in non_retryable_errors:
        if non_retryable.lower() in error_lower:
            return False
    
    # 可重试的错误类型
    retryable_errors = [
        "网络",
        "超时",
        "timeout",
        "connection",
        "ERR_CONNECTION_CLOSED",  # 网络连接关闭
        "net::ERR",  # Chrome网络错误
        "webdriver",
        "异常",
        "OAuth窗口未打开",
        "OAuth重定向监控失败",
        "OAuth流程停留"
    ]
    
    for retryable in retryable_errors:
        if retryable.lower() in error_lower:
            return True
    
    # 默认不重试未知错误
    return False


def execute_github_oauth_with_browser_simulator(
    target_website: str, 
    github_username: str, 
    github_password: str, 
    totp_secret: str
) -> Tuple[bool, str, Dict]:
    """
    使用增强版浏览器模拟器执行GitHub OAuth登录
    
    Args:
        target_website: 目标网站URL
        github_username: GitHub用户名
        github_password: GitHub密码
        totp_secret: TOTP密钥
        
    Returns:
        (is_success, message, session_data)
    """
    browser = None
    try:
        print(f"🚀 开始使用增强版浏览器模拟器执行GitHub OAuth登录")
        print(f"🎯 目标网站: {target_website}")
        print(f"👤 GitHub账户: {github_username}")
        
        # 创建浏览器实例
        browser = BrowserSimulator(browser_type="chrome", headless=True)
        
        # 访问目标网站
        success, message = browser.visit_website(target_website)
        if not success:
            return False, f"访问网站失败: {message}", {}
        
        # 如果当前不在登录页面，尝试访问登录页面
        current_url = browser.driver.current_url
        if '/login' not in current_url:
            print("🔄 当前不在登录页面，尝试访问登录页面...")
            login_url = target_website.rstrip('/') + '/login'
            login_success, login_message = browser.visit_website(login_url)
            if not login_success:
                print(f"⚠️ 访问登录页面失败: {login_message}")
        
        # 使用新的集成OAuth解决方案
        print("🚀 使用集成的GitHub OAuth流程处理器...")
        oauth_success, oauth_message = browser.handle_github_oauth_flow()
        
        if oauth_success:
            # OAuth窗口成功打开，现在需要在新窗口中进行登录
            print("✅ GitHub OAuth窗口已打开，开始登录流程...")
            
            # 在OAuth窗口中执行登录
            login_success, login_message, session_data = browser.perform_github_login_in_oauth_window(
                github_username, github_password, totp_secret, target_website
            )
            
            return login_success, login_message, session_data
        else:
            return False, f"OAuth窗口打开失败: {oauth_message}", {}
        
    except Exception as e:
        error_msg = f"浏览器模拟器异常: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(traceback.format_exc())
        return False, error_msg, {}
    finally:
        if browser:
            try:
                browser.close()
            except Exception as e:
                print(f"⚠️ 关闭浏览器时出错: {e}")


# 全局任务执行器实例
task_executor = TaskExecutor()


def _record_account_balance_snapshot(
    db_session: Session,
    task: ScheduledTask,
    execution_log: Optional[TaskExecutionLog],
    account: GitHubAccount,
    account_result: Dict[str, Any],
    previous_snapshot: Optional[AccountBalanceSnapshot] = None
) -> None:
    """将账户余额信息持久化为快照

    Args:
        db_session: 数据库会话
        task: 任务对象
        execution_log: 执行日志（可选）
        account: GitHub账号
        account_result: 账号执行结果
        previous_snapshot: 上一次余额快照（可选，用于避免重复查询）
    """
    balance_value = account_result.get("balance")
    parsed_balance = _parse_balance_value(balance_value)

    # 格式化上一次余额为字符串
    previous_balance_text = None
    if previous_snapshot and previous_snapshot.balance is not None:
        currency = previous_snapshot.currency or ''
        previous_balance_text = f"{previous_snapshot.balance:.2f}{' ' + currency if currency else ''}"

    snapshot = AccountBalanceSnapshot(
        task_id=task.id,
        execution_log_id=execution_log.id if execution_log else None,
        account_id=account.id,
        snapshot_time=datetime.now(timezone.utc),
        balance=parsed_balance,
        currency=account_result.get("balance_currency"),
        raw_text=previous_balance_text,  # 保存上一次的余额记录
        extraction_error=account_result.get("balance_extraction_error") or account_result.get("error")
    )
    db_session.add(snapshot)
    try:
        db_session.flush()
        db_session.commit()
    except Exception as commit_error:
        db_session.rollback()
        print(f"⚠️ 保存余额快照失败: {commit_error}")


def _parse_balance_value(value: Any) -> Optional[float]:
    """尽可能将余额值转为浮点数"""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None

    return None
