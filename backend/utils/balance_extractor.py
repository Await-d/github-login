"""
优化版余额提取器
专门针对 anyrouter.top 的余额提取功能
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from selenium.webdriver.common.by import By


CURRENCY_SYMBOL_MAP = {
    "$": "USD",
    "＄": "USD",
    "US$": "USD",
    "CN¥": "CNY",
    "¥": "CNY",
    "￥": "CNY",
    "€": "EUR",
    "£": "GBP"
}

CURRENCY_CODES = {"USD", "CNY", "EUR", "GBP"}


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
        
        # 专门针对 anyrouter.top 的选择器，基于实际测试的HTML结构
        selectors = [
            # anyrouter.top 特定结构：查找"Current balance"文本后的兄弟元素
            ("xpath", "//*[contains(text(), 'Current balance')]/following-sibling::*[1]"),
            ("xpath", "//*[contains(text(), '当前余额')]/following-sibling::*[1]"),
            # anyrouter.top：通过父元素查找
            ("xpath", "//*[text()='Current balance']/parent::*/following-sibling::*"),
            ("xpath", "//*[text()='当前余额']/parent::*/following-sibling::*"),
            # 最高优先级：通过上下文定位余额
            # 查找包含"当前余额"或"balance"文字的父元素下的金额
            ("xpath", "//div[contains(., '当前余额') or contains(., 'balance') or contains(., 'Balance')]//*[@class='text-lg font-semibold']"),
            ("xpath", "//div[contains(., '当前余额') or contains(., 'balance') or contains(., 'Balance')]//div[contains(@class, 'font-semibold')]"),
            ("xpath", "//*[contains(text(), '当前余额')]/following::*[contains(@class, 'font-semibold')][1]"),
            ("xpath", "//*[contains(text(), '当前余额')]/following::div[contains(@class, 'text-lg')][1]"),
            # 次优先级：直接CSS选择器
            ("css", "div.text-xl.font-semibold"),
            ("css", ".text-xl.font-semibold"),
            ("css", "div.text-lg.font-semibold"),
            ("css", ".text-lg.font-semibold"),
            ("css", "*[class*='font-semibold']"),
            ("css", "*[class*='text-lg']"),
            # 通用余额相关选择器
            ("css", "*[class*='balance']"),
            ("css", "*[class*='amount']"), 
            ("css", "*[class*='money']"),
            ("css", "*[class*='price']"),
            ("css", "*[class*='credit']"),
            ("css", "*[class*='fund']")
        ]
        
        for selector_type, selector in selectors:
            try:
                if selector_type == "xpath":
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    try:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and self._is_balance_text(text):
                                # 检查是否是真正的余额（通过上下文）
                                parent_text = self._get_parent_context(element)
                                if self._is_balance_context(parent_text):
                                    balance_value, currency = self._parse_balance_text(text)
                                    if balance_value is not None:
                                        print(f"✅ CSS选择器找到余额: {text} (值: {balance_value} {currency})")
                                        print(f"   上下文: {parent_text[:100]}")
                                        return {
                                            "success": True,
                                            "balance": str(balance_value),
                                            "currency": currency,
                                            "raw_text": text,
                                            "extraction_method": f"{selector_type}_{selector[:50]}"
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

            # 先在包含余额关键词的上下文中定位金额
            keyword_pattern = re.compile(
                r'(.{0,160}(?:当前余额|账户余额|可用余额|current balance|available balance|wallet).{0,160})',
                re.IGNORECASE | re.DOTALL
            )
            keyword_sections = keyword_pattern.findall(page_source)

            for section in keyword_sections:
                candidate = self._select_amount_candidate(section)
                if candidate:
                    balance_value = candidate['value']
                    currency = candidate['currency']
                    raw_text = candidate['raw']
                    print(f"✅ 正则表达式（上下文）找到余额: {raw_text} (值: {balance_value} {currency})")
                    return {
                        "success": True,
                        "balance": str(balance_value),
                        "currency": currency,
                        "raw_text": raw_text,
                        "extraction_method": "regex_with_context"
                    }

            # 如果关键词上下文未命中，回退到全局搜索
            fallback_candidate = self._select_amount_candidate(page_source, prefer_smaller=True)
            if fallback_candidate:
                balance_value = fallback_candidate['value']
                currency = fallback_candidate['currency']
                raw_text = fallback_candidate['raw']
                print(f"✅ 正则表达式找到余额: {raw_text} (值: {balance_value} {currency})")
                return {
                    "success": True,
                    "balance": str(balance_value),
                    "currency": currency,
                    "raw_text": raw_text,
                    "extraction_method": "regex_fallback"
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
            
            balance_candidates = []
            
            for element in elements:
                try:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text and self._is_balance_text(text):
                            # 获取上下文
                            parent_text = self._get_parent_context(element)
                            
                            # 检查是否是余额相关的上下文
                            if self._is_balance_context(parent_text):
                                balance_value, currency = self._parse_balance_text(text)
                                if balance_value is not None:
                                    balance_candidates.append({
                                        'value': balance_value,
                                        'currency': currency,
                                        'text': text,
                                        'context': parent_text,
                                        'priority': self._calculate_priority(parent_text, balance_value)
                                    })
                except Exception as e:
                    continue
            
            if balance_candidates:
                # 按优先级排序，选择最高优先级的
                balance_candidates.sort(key=lambda x: x['priority'], reverse=True)
                best = balance_candidates[0]
                
                print(f"✅ 全文搜索找到余额: {best['text']} (值: {best['value']} {best['currency']})")
                print(f"   上下文: {best['context'][:100]}")
                return {
                    "success": True,
                    "balance": str(best['value']),
                    "currency": best['currency'],
                    "raw_text": best['text'],
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
            candidates = self._extract_amount_candidates(text)
            if not candidates:
                return None, None

            for candidate in candidates:
                if candidate['has_explicit_currency']:
                    return candidate['value'], candidate['currency']

            best = candidates[0]
            return best['value'], best['currency']

        except Exception as e:
            print(f"⚠️ 解析余额文本失败: {str(e)}")
            return None, None

    def _extract_amount_candidates(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取金额候选"""
        if not text:
            return []

        amount_pattern = re.compile(
            r'(?P<prefix_code>USD|CNY|EUR|GBP)?\s*'
            r'(?P<symbol>US\$|CN¥|[$¥€£￥＄])?\s*'
            r'(?P<value>-?\d{1,3}(?:,\d{3})*(?:\.\d{1,4})?)\s*'
            r'(?P<suffix_code>USD|CNY|EUR|GBP)?',
            re.IGNORECASE
        )

        candidates: List[Dict[str, Any]] = []

        for match in amount_pattern.finditer(text):
            raw_text = match.group(0).strip()
            value_str = match.group('value')
            if not value_str:
                continue

            clean_value = value_str.replace(',', '')
            try:
                value = float(clean_value)
            except ValueError:
                continue

            prefix_code = match.group('prefix_code')
            suffix_code = match.group('suffix_code')
            symbol = match.group('symbol')

            currency = self._determine_currency(symbol, prefix_code, suffix_code)

            candidates.append({
                'value': value,
                'currency': currency,
                'raw': raw_text,
                'has_explicit_currency': bool(symbol) or bool(prefix_code) or bool(suffix_code) or (currency is not None and currency != 'USD')
            })

        for candidate in candidates:
            if candidate['currency'] is None:
                candidate['currency'] = 'USD'
                candidate['has_explicit_currency'] = False

        return candidates

    def _determine_currency(self, symbol: Optional[str], prefix_code: Optional[str], suffix_code: Optional[str]) -> Optional[str]:
        """根据符号或代码确定货币类型"""
        if prefix_code:
            code = prefix_code.upper()
            if code in CURRENCY_CODES:
                return code

        if suffix_code:
            code = suffix_code.upper()
            if code in CURRENCY_CODES:
                return code

        if symbol:
            normalized_symbol = symbol.strip()
            if normalized_symbol in CURRENCY_SYMBOL_MAP:
                return CURRENCY_SYMBOL_MAP[normalized_symbol]
            upper_symbol = normalized_symbol.upper()
            if upper_symbol in CURRENCY_SYMBOL_MAP:
                return CURRENCY_SYMBOL_MAP[upper_symbol]

        return None

    def _select_amount_candidate(self, text: str, prefer_smaller: bool = False) -> Optional[Dict[str, Any]]:
        """从文本中选择最合适的金额候选"""
        candidates = self._extract_amount_candidates(text)
        if not candidates:
            return None

        explicit_candidates = [c for c in candidates if c['has_explicit_currency']]
        candidates_to_consider = explicit_candidates or candidates

        if prefer_smaller:
            candidates_to_consider = sorted(candidates_to_consider, key=lambda c: abs(c['value']))

        return candidates_to_consider[0]
    
    def _get_parent_context(self, element) -> str:
        """获取元素的父级上下文"""
        try:
            parent = element.find_element(By.XPATH, "..")
            parent_parent = parent.find_element(By.XPATH, "..")
            context = parent_parent.text[:500] if parent_parent else parent.text[:500]
            return context
        except Exception:
            try:
                return element.text[:500]
            except Exception:
                return ""
    
    def _is_balance_context(self, context: str) -> bool:
        """判断上下文是否与余额相关"""
        if not context:
            return True  # 如果没有上下文，默认为True
        
        context_lower = context.lower()
        
        # 正向关键词（包含这些词说明是余额）
        positive_keywords = [
            '当前余额', 'balance', '账户余额', '可用余额', 
            'available', 'current', 'wallet', '钱包'
        ]
        
        # 负向关键词（包含这些词说明不是余额）
        negative_keywords = [
            '历史', 'history', '消耗', 'consumed', 'usage', '使用',
            '统计', 'statistics', 'total', '总计'
        ]
        
        # 检查负向关键词
        for keyword in negative_keywords:
            if keyword in context_lower:
                return False
        
        # 检查正向关键词
        for keyword in positive_keywords:
            if keyword in context_lower:
                return True
        
        # 如果没有明确的关键词，默认为True
        return True
    
    def _calculate_priority(self, context: str, balance_value: float) -> int:
        """计算余额候选的优先级"""
        priority = 0
        context_lower = context.lower()
        
        # 正向关键词加分
        if '当前余额' in context_lower or 'current balance' in context_lower:
            priority += 100
        elif 'balance' in context_lower or '余额' in context_lower:
            priority += 50
        elif 'available' in context_lower or '可用' in context_lower:
            priority += 40
        
        # 负向关键词减分
        if '历史' in context_lower or 'history' in context_lower:
            priority -= 80
        if '消耗' in context_lower or 'consumed' in context_lower:
            priority -= 80
        if '统计' in context_lower or 'statistics' in context_lower:
            priority -= 60
        
        # 较小的金额更可能是剩余余额（加分）
        if balance_value < 100:
            priority += 30
        elif balance_value > 1000:
            priority -= 20
        
        return priority
