"""
优化版余额提取器
专门针对 anyrouter.top 的余额提取功能
"""

import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from selenium.webdriver.common.by import By


class BalanceExtractor:
    """余额信息提取器"""
    
    def __init__(self, driver):
        """
        初始化余额提取器
        
        Args:
            driver: Selenium WebDriver 实例
        """
        self.driver = driver
    
    def extract_balance(self, console_url: str = None) -> Dict[str, Any]:
        """
        提取余额信息的主方法
        
        Args:
            console_url: 控制台页面URL，如果提供会先访问
            
        Returns:
            包含余额信息的字典
        """
        try:
            extraction_time = datetime.now().isoformat()
            current_url = self.driver.current_url if self.driver else "unknown"
            
            # 如果提供了控制台URL且当前不在该页面，先访问
            if console_url and current_url != console_url:
                print(f"🌐 访问控制台页面: {console_url}")
                self.driver.get(console_url)
                current_url = console_url
            
            print(f"🔍 当前页面URL: {current_url}")
            
            # 策略1: 优先使用CSS选择器（最准确）
            result = self._extract_by_css_selectors()
            if result["success"]:
                result.update({
                    "extraction_time": extraction_time,
                    "page_url": current_url
                })
                return result
            
            # 策略2: 使用正则表达式搜索（作为备选）
            result = self._extract_by_regex_patterns()
            if result["success"]:
                result.update({
                    "extraction_time": extraction_time,
                    "page_url": current_url
                })
                return result
            
            # 策略3: 全文搜索（最后的备选方案）
            result = self._extract_by_full_text_search()
            if result["success"]:
                result.update({
                    "extraction_time": extraction_time,
                    "page_url": current_url
                })
                return result
            
            print("⚠️ 未找到余额信息")
            return {
                "success": False,
                "error": "未找到余额信息",
                "extraction_time": extraction_time,
                "page_url": current_url,
                "balance": None,
                "currency": None,
                "raw_text": None
            }
            
        except Exception as e:
            error_msg = f"提取余额信息异常: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "extraction_time": datetime.now().isoformat(),
                "page_url": self.driver.current_url if self.driver else "unknown",
                "balance": None,
                "currency": None,
                "raw_text": None
            }
    
    def _extract_by_css_selectors(self) -> Dict[str, Any]:
        """通过CSS选择器提取余额"""
        print("🔍 使用CSS选择器搜索余额...")
        
        # 专门针对 anyrouter.top 的选择器，基于用户提供的HTML结构
        selectors = [
            # 最高优先级：用户提供的确切结构
            "div.text-lg.font-semibold",  # <div class="text-lg font-semibold">$57.10</div>
            ".text-lg.font-semibold",     # 更宽泛的匹配
            # 其他可能的变体
            "*[class*='font-semibold']",  # 字体加粗的元素
            "*[class*='text-lg']",        # 大字体的元素
            # 通用余额相关选择器
            "*[class*='balance']",
            "*[class*='amount']", 
            "*[class*='money']",
            "*[class*='price']",
            "*[class*='credit']",
            "*[class*='fund']"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    try:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and self._is_balance_text(text):
                                balance_value, currency = self._parse_balance_text(text)
                                if balance_value is not None:
                                    print(f"✅ CSS选择器找到余额: {text} (值: {balance_value} {currency})")
                                    return {
                                        "success": True,
                                        "balance": str(balance_value),
                                        "currency": currency,
                                        "raw_text": text,
                                        "extraction_method": f"css_selector_{selector}"
                                    }
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        return {"success": False}
    
    def _extract_by_regex_patterns(self) -> Dict[str, Any]:
        """通过正则表达式搜索页面源码提取余额"""
        print("🔍 使用正则表达式搜索页面源码...")
        
        try:
            page_source = self.driver.page_source
            
            # 优化的货币格式正则表达式 - 按优先级排序
            currency_patterns = [
                # 高优先级：带美元符号的格式
                r'\$(\d+\.\d{2})',        # $57.10
                r'\$(\d+)',               # $57
                # 其他货币符号
                r'¥(\d+\.\d{2})',         # ¥60.86
                r'€(\d+\.\d{2})',         # €60.86
                r'£(\d+\.\d{2})',         # £60.86
                # 货币代码格式
                r'(\d+\.\d{2})\s*USD',    # 60.86 USD
                r'(\d+\.\d{2})\s*CNY',    # 60.86 CNY
            ]
            
            for pattern in currency_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    # 选择最大的金额（更可能是账户余额）
                    best_match = None
                    best_value = 0
                    
                    for match in matches:
                        value = float(match) if isinstance(match, str) else float(match)
                        if value > best_value:
                            best_match = match
                            best_value = value
                    
                    if best_match:
                        # 重建原始文本
                        if '$' in pattern:
                            raw_text = f"${best_match}"
                            currency = "USD"
                        elif '¥' in pattern:
                            raw_text = f"¥{best_match}"
                            currency = "CNY"
                        elif '€' in pattern:
                            raw_text = f"€{best_match}"
                            currency = "EUR"
                        elif '£' in pattern:
                            raw_text = f"£{best_match}"
                            currency = "GBP"
                        elif 'USD' in pattern:
                            raw_text = f"{best_match} USD"
                            currency = "USD"
                        elif 'CNY' in pattern:
                            raw_text = f"{best_match} CNY"
                            currency = "CNY"
                        else:
                            raw_text = str(best_match)
                            currency = "USD"  # 默认
                        
                        print(f"✅ 正则表达式找到余额: {raw_text} (值: {best_value} {currency})")
                        return {
                            "success": True,
                            "balance": str(best_value),
                            "currency": currency,
                            "raw_text": raw_text,
                            "extraction_method": "regex_patterns"
                        }
            
            return {"success": False}
            
        except Exception as e:
            print(f"❌ 正则表达式搜索异常: {str(e)}")
            return {"success": False}
    
    def _extract_by_full_text_search(self) -> Dict[str, Any]:
        """通过全文搜索提取余额"""
        print("🔍 使用全文搜索...")
        
        try:
            # 获取所有可见元素的文本
            elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            
            best_match = None
            best_value = 0
            best_raw_text = None
            
            for element in elements:
                try:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text and self._is_balance_text(text):
                            balance_value, currency = self._parse_balance_text(text)
                            if balance_value is not None and balance_value > best_value:
                                best_match = (balance_value, currency)
                                best_value = balance_value
                                best_raw_text = text
                except Exception as e:
                    continue
            
            if best_match:
                balance_value, currency = best_match
                print(f"✅ 全文搜索找到余额: {best_raw_text} (值: {balance_value} {currency})")
                return {
                    "success": True,
                    "balance": str(balance_value),
                    "currency": currency,
                    "raw_text": best_raw_text,
                    "extraction_method": "full_text_search"
                }
            
            return {"success": False}
            
        except Exception as e:
            print(f"❌ 全文搜索异常: {str(e)}")
            return {"success": False}
    
    def _is_balance_text(self, text: str) -> bool:
        """判断文本是否可能是余额信息"""
        if not text or len(text) > 50:  # 排除过长的文本
            return False
            
        # 检查是否包含货币符号和数字
        currency_patterns = [
            r'\$\d',                    # 包含$和数字
            r'¥\d',                     # 包含¥和数字  
            r'€\d',                     # 包含€和数字
            r'£\d',                     # 包含£和数字
            r'\d+\.\d{1,2}',            # 数字.一到两位小数
            r'USD|CNY|EUR|GBP',         # 货币代码
        ]
        
        for pattern in currency_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _parse_balance_text(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """解析余额文本，提取数值和货币类型"""
        try:
            # 货币符号映射
            currency_map = {
                '$': 'USD',
                '¥': 'CNY',
                '€': 'EUR',
                '£': 'GBP',
                '￥': 'CNY',  # 全角人民币符号
                '＄': 'USD'   # 全角美元符号
            }
            
            # 提取货币符号
            currency = "USD"  # 默认货币
            for symbol, code in currency_map.items():
                if symbol in text:
                    currency = code
                    break
            
            # 检查货币代码
            if 'USD' in text:
                currency = 'USD'
            elif 'CNY' in text:
                currency = 'CNY'
            elif 'EUR' in text:
                currency = 'EUR'
            elif 'GBP' in text:
                currency = 'GBP'
            
            # 提取数字
            number_pattern = r'(\d+(?:,\d{3})*(?:\.\d{1,2})?)'
            matches = re.findall(number_pattern, text)
            
            if matches:
                # 取最大的数字（更可能是主要金额）
                amounts = []
                for match in matches:
                    clean_amount = match.replace(',', '')
                    try:
                        amount = float(clean_amount)
                        amounts.append(amount)
                    except ValueError:
                        continue
                
                if amounts:
                    balance_value = max(amounts)  # 选择最大的金额
                    return balance_value, currency
            
            return None, None
            
        except Exception as e:
            print(f"⚠️ 解析余额文本失败: {str(e)}")
            return None, None