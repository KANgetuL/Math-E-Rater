"""
LaTeX转换工具函数
"""

import re
from typing import Dict, Any, Tuple


def extract_formula_from_text(text: str) -> Tuple[str, str]:
    """
    从文本中提取公式部分

    Args:
        text: 包含公式的文本

    Returns:
        Tuple[公式部分, 非公式部分]
    """
    # 常见的公式模式
    patterns = [
        # 包含等号的表达式
        r'([a-zA-Z0-9_]+)\s*=\s*([^。，！？；,\.!?;]+)',
        # 包含数学运算的表达式
        r'([a-zA-Z0-9_]+)\s*[\+\-\*/]\s*([a-zA-Z0-9_]+)',
        # 包含函数的表达式
        r'(sqrt|sin|cos|tan|log|ln|exp)\([^)]+\)',
        # 包含上标下标的表达式
        r'[a-zA-Z0-9_]+\^[a-zA-Z0-9_]+',
        r'[a-zA-Z0-9_]+_[a-zA-Z0-9_]+',
    ]

    formula_parts = []
    remaining_text = text

    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            formula_parts.append(match.group(0))

    if formula_parts:
        # 提取公式部分
        formula_text = ' '.join(formula_parts)

        # 从原始文本中移除公式部分
        for formula in formula_parts:
            remaining_text = remaining_text.replace(formula, '')

        return formula_text, remaining_text.strip()

    return '', text


def format_latex_for_display(latex_text: str) -> str:
    """
    格式化LaTeX用于显示

    Args:
        latex_text: 原始LaTeX

    Returns:
        格式化后的LaTeX
    """
    # 添加数学环境分隔符
    if not latex_text.startswith('$'):
        latex_text = f"${latex_text}$"

    # 确保有合适的换行
    latex_text = latex_text.replace(r'\\', r'\\[10pt]')

    return latex_text


def calculate_complexity(latex_text: str) -> float:
    """
    计算LaTeX公式的复杂度

    Args:
        latex_text: LaTeX公式

    Returns:
        复杂度分数 (0-1)
    """
    if not latex_text:
        return 0.0

    complexity = 0.0

    # 分数复杂度
    complexity += latex_text.count(r'\frac') * 0.3

    # 根号复杂度
    complexity += latex_text.count(r'\sqrt') * 0.2

    # 求和/积分复杂度
    if r'\sum' in latex_text or r'\int' in latex_text:
        complexity += 0.25

    # 上标下标复杂度
    complexity += (latex_text.count('^') + latex_text.count('_')) * 0.1

    # 长度复杂度
    length_factor = min(len(latex_text) / 100, 1.0)
    complexity += length_factor * 0.2

    return min(complexity, 1.0)