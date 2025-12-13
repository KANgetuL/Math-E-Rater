"""
增强的文本公式转换模型 - 修复版
"""

import re
import sympy
from sympy import sympify, latex, symbols, simplify
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication,
    convert_xor,
    split_symbols,
    function_exponentiation,
    rationalize
)
from typing import Tuple, List, Dict, Any
import traceback


class EnhancedFormulaConverter:
    """增强的公式转换器"""

    def __init__(self):
        """初始化转换器"""
        # SymPy解析转换
        self.transformations = (
            standard_transformations +
            (split_symbols, implicit_multiplication, function_exponentiation, rationalize)
        )

        # 特殊函数映射
        self.function_map = {
            'sqrt': r'\sqrt',
            'log': r'\log',
            'ln': r'\ln',
            'lg': r'\log',
            'sin': r'\sin',
            'cos': r'\cos',
            'tan': r'\tan',
            'cot': r'\cot',
            'sec': r'\sec',
            'csc': r'\csc',
            'arcsin': r'\arcsin',
            'arccos': r'\arccos',
            'arctan': r'\arctan',
            'sinh': r'\sinh',
            'cosh': r'\cosh',
            'tanh': r'\tanh',
            'exp': r'\exp',
            'abs': r'|',
            'floor': r'\lfloor',
            'ceil': r'\lceil',
            'det': r'\det',
            'tr': r'\operatorname{tr}',
            'rank': r'\operatorname{rank}',
        }

        # 希腊字母映射
        self.greek_map = {
            'alpha': r'\alpha', 'beta': r'\beta', 'gamma': r'\gamma',
            'Gamma': r'\Gamma', 'delta': r'\delta', 'Delta': r'\Delta',
            'epsilon': r'\epsilon', 'varepsilon': r'\varepsilon',
            'zeta': r'\zeta', 'eta': r'\eta', 'theta': r'\theta',
            'Theta': r'\Theta', 'vartheta': r'\vartheta', 'iota': r'\iota',
            'kappa': r'\kappa', 'lambda': r'\lambda', 'Lambda': r'\Lambda',
            'mu': r'\mu', 'nu': r'\nu', 'xi': r'\xi', 'Xi': r'\Xi',
            'pi': r'\pi', 'Pi': r'\Pi', 'rho': r'\rho', 'varrho': r'\varrho',
            'sigma': r'\sigma', 'Sigma': r'\Sigma', 'tau': r'\tau',
            'upsilon': r'\upsilon', 'Upsilon': r'\Upsilon',
            'phi': r'\phi', 'Phi': r'\Phi', 'varphi': r'\varphi',
            'chi': r'\chi', 'psi': r'\psi', 'Psi': r'\Psi',
            'omega': r'\omega', 'Omega': r'\Omega'
        }

        # 操作符映射
        self.operator_map = {
            '**': '^',
            '*': r'\cdot ',
            '/': r'\frac{',
            '+-': r'\pm ',
            '-+': r'\mp ',
            '==': '=',
            '!=': r'\neq ',
            '<=': r'\leq ',
            '>=': r'\geq ',
            '<<': r'\ll ',
            '>>': r'\gg ',
            '->': r'\rightarrow ',
            '=>': r'\Rightarrow ',
            '<->': r'\leftrightarrow ',
            '<=>': r'\Leftrightarrow ',
            'inf': r'\infty',
            'infty': r'\infty',
            'forall': r'\forall ',
            'exists': r'\exists ',
            'in': r'\in ',
            'notin': r'\notin ',
            'subset': r'\subset ',
            'subseteq': r'\subseteq ',
            'supset': r'\supset ',
            'supseteq': r'\supseteq ',
            'cup': r'\cup ',
            'cap': r'\cap ',
            'emptyset': r'\emptyset',
            'nabla': r'\nabla ',
            'partial': r'\partial ',
            'sum': r'\sum',
            'prod': r'\prod',
            'int': r'\int',
            'oint': r'\oint',
            'lim': r'\lim',
        }

        # 预定义的公式模板
        self.formula_templates = {
            r'x\s*=\s*\(-b\s*±\s*sqrt\(b\^2\s*-\s*4ac\)\)\s*/\s*\(2a\)':
                r'x = \frac{-b \pm \sqrt{b^{2} - 4ac}}{2a}',

            r'a\^2\s*\+\s*b\^2\s*=\s*c\^2': r'a^{2} + b^{2} = c^{2}',

            r'E\s*=\s*mc\^2': r'E = mc^{2}',

            r'F\s*=\s*ma': r'F = ma',

            r'V\s*=\s*IR': r'V = IR',

            r'A\s*=\s*πr\^2': r'A = \pi r^{2}',

            r'V\s*=\s*\(4/3\)πr\^3': r'V = \frac{4}{3}\pi r^{3}',

            r'e\^\(iπ\)\s*\+\s*1\s*=\s*0': r'e^{i\pi} + 1 = 0',
        }

    def preprocess_text(self, text: str) -> str:
        """预处理输入文本"""
        if not text:
            return text

        # 移除多余空白
        text = re.sub(r'\s+', ' ', text.strip())

        # 替换特殊符号
        replacements = [
            (r'±', '+-'),
            (r'π', 'pi'),
            (r'∞', 'oo'),
            (r'α', 'alpha'),
            (r'β', 'beta'),
            (r'γ', 'gamma'),
            (r'δ', 'delta'),
            (r'ε', 'epsilon'),
            (r'θ', 'theta'),
            (r'λ', 'lambda'),
            (r'σ', 'sigma'),
            (r'φ', 'phi'),
            (r'ω', 'omega'),

            (r'sqrt\(([^)]+)\)', r'sqrt(\1)'),
            (r'√\(([^)]+)\)', r'sqrt(\1)'),
            (r'exp\(([^)]+)\)', r'exp(\1)'),
            (r'log\(([^)]+)\)', r'log(\1)'),
            (r'ln\(([^)]+)\)', r'log(\1)'),
            (r'sin\(([^)]+)\)', r'sin(\1)'),
            (r'cos\(([^)]+)\)', r'cos(\1)'),
            (r'tan\(([^)]+)\)', r'tan(\1)'),

            (r'(\w+)\^(\d+)', r'\1**\2'),
            (r'(\w+)\^\(([^)]+)\)', r'\1**(\2)'),

            (r'(\d+)/(\d+)', r'Rational(\1,\2)'),
            (r'\(([^)]+)\)/\(([^)]+)\)', r'(\1)/(\2)'),

            (r'(\d)([a-zA-Z])', r'\1*\2'),
            (r'([a-zA-Z])(\d)', r'\1*\2'),
            (r'\)([a-zA-Z0-9])', r')*\1'),
            (r'([a-zA-Z0-9])\(', r'\1*('),

            (r'\|([^|]+)\|', r'Abs(\1)'),
        ]

        processed = text
        for pattern, replacement in replacements:
            processed = re.sub(pattern, replacement, processed)

        return processed

    def convert_to_latex(self, text: str) -> Tuple[str, float]:
        """将文本公式转换为LaTeX格式"""
        if not text:
            return "", 0.0

        # 步骤1：检查是否匹配预定义模板
        for pattern, template in self.formula_templates.items():
            if re.match(pattern, text, re.IGNORECASE):
                return template, 0.98

        try:
            # 步骤2：尝试使用SymPy解析
            processed_text = self.preprocess_text(text)

            # 首先尝试直接解析整个表达式
            try:
                expr = parse_expr(processed_text, transformations=self.transformations)
                latex_output = latex(expr)
                confidence = 0.95
            except Exception as sympy_error:
                # 如果整个表达式解析失败，使用规则转换
                latex_output = self.rule_based_conversion(text)
                confidence = 0.7

            # 后处理LaTeX输出
            latex_output = self.postprocess_latex(latex_output)

            # 检查转换结果是否合理
            if self.is_valid_latex(latex_output):
                return latex_output, confidence
            else:
                # 如果转换结果不合理，返回文本格式
                return f"\\text{{{text}}}", 0.3

        except Exception as e:
            # 所有方法都失败，返回文本格式
            return f"\\text{{{text}}}", 0.2

    def rule_based_conversion(self, text: str) -> str:
        """基于规则的转换 - 修复版"""
        try:
            result = text

            # 使用安全的字符串替换，避免正则表达式问题
            replacements = [
                # 特殊符号
                ('±', r'\pm '),
                ('∓', r'\mp '),
                ('pi', r'\pi '),
                ('alpha', r'\alpha '),
                ('beta', r'\beta '),
                ('gamma', r'\gamma '),
                ('delta', r'\delta '),
                ('theta', r'\theta '),
                ('lambda', r'\lambda '),
                ('sigma', r'\sigma '),
                ('phi', r'\phi '),
                ('omega', r'\omega '),
                ('inf', r'\infty '),
                ('infty', r'\infty '),

                # 函数
                ('sin(', r'\sin('),
                ('cos(', r'\cos('),
                ('tan(', r'\tan('),
                ('log(', r'\log('),
                ('ln(', r'\ln('),
                ('exp(', r'\exp('),
                ('lim(', r'\lim('),
                ('sqrt(', r'\sqrt{'),

                # 操作符
                ('!=', r'\neq '),
                ('<=', r'\leq '),
                ('>=', r'\geq '),
                ('->', r'\rightarrow '),
                ('=>', r'\Rightarrow '),
            ]

            # 应用简单替换
            for old, new in replacements:
                result = result.replace(old, new)

            # 处理平方根闭合
            if r'\sqrt{' in result:
                # 在适当的位置添加闭合括号
                parts = result.split(r'\sqrt{')
                if len(parts) > 1:
                    for i in range(1, len(parts)):
                        if ')' in parts[i]:
                            # 替换第一个 ) 为 }
                            parts[i] = parts[i].replace(')', '}', 1)
                    result = ''.join(parts)

            # 处理分数
            if '/' in result:
                # 简单处理 a/b
                import re
                result = re.sub(r'(\d+)/(\d+)', r'\\frac{\1}{\2}', result)

            # 处理上标
            if '^' in result:
                # 简单处理 x^2
                parts = result.split('^')
                if len(parts) >= 2:
                    new_parts = []
                    for i, part in enumerate(parts):
                        if i == 0:
                            new_parts.append(part)
                        else:
                            # 假设上标是一个数字或简单表达式
                            if part and part[0].isdigit():
                                # 数字上标
                                new_parts.append('{' + part[0] + '}' + part[1:])
                            else:
                                new_parts.append(part)
                    result = '^'.join(new_parts)

            return result

        except Exception as e:
            print(f"规则转换错误: {e}")
            return text

    def postprocess_latex(self, latex_text: str) -> str:
        """后处理LaTeX输出"""
        if not latex_text:
            return latex_text

        result = latex_text

        # 修复SymPy输出中的问题
        replacements = [
            (r'\\operatorname\{sqrt\}', r'\\sqrt'),
            (r'\\operatorname\{log\}', r'\\log'),
            (r'\\operatorname\{ln\}', r'\\ln'),
            (r'\\operatorname\{sin\}', r'\\sin'),
            (r'\\operatorname\{cos\}', r'\\cos'),
            (r'\\operatorname\{tan\}', r'\\tan'),

            (r'\\frac\{(\d+)\}\{(\d+)\}', r'\\frac{\1}{\2}'),

            (r'\\left\(\\left\((.*?)\\right\)\\right\)', r'\\left(\1\\right)'),

            (r'\s+', ' '),
        ]

        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)

        return result.strip()

    def is_valid_latex(self, latex_text: str) -> bool:
        """检查LaTeX是否有效"""
        if not latex_text:
            return False

        # 检查是否包含LaTeX命令或数学符号
        has_latex_commands = bool(re.search(r'\\[a-zA-Z]+', latex_text))
        has_math_symbols = bool(re.search(r'[\^_\{\}\[\]\(\)]', latex_text))

        # 不应该只是纯文本
        is_plain_text = latex_text.startswith(r'\text{')

        return (has_latex_commands or has_math_symbols) and not is_plain_text

    def batch_convert(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量转换"""
        results = []
        for text in texts:
            try:
                latex_output, confidence = self.convert_to_latex(text)
                results.append({
                    'text': text,
                    'latex': latex_output,
                    'confidence': confidence,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'text': text,
                    'latex': f"\\text{{{text}}}",
                    'confidence': 0.0,
                    'success': False,
                    'error': str(e)
                })
        return results

    def validate_latex(self, latex_text: str) -> Tuple[bool, str]:
        """验证LaTeX语法"""
        if not latex_text:
            return False, "LaTeX字符串为空"

        # 检查括号匹配
        brackets = []
        for char in latex_text:
            if char in '([{':
                brackets.append(char)
            elif char in ')]}':
                if not brackets:
                    return False, f"多余的右括号: {char}"
                last = brackets.pop()
                if (last == '(' and char != ')') or \
                   (last == '[' and char != ']') or \
                   (last == '{' and char != '}'):
                    return False, f"括号不匹配: {last} 和 {char}"

        if brackets:
            return False, f"未闭合的左括号: {brackets}"

        # 检查基本的LaTeX命令语法
        if '\\' in latex_text:
            # 确保反斜杠后面有内容
            invalid_commands = re.findall(r'\\([^a-zA-Z{]|$)', latex_text)
            if invalid_commands:
                return False, "反斜杠后面没有有效的命令"

        return True, "LaTeX语法基本有效"


# 创建全局实例
_converter_instance = None

def get_converter():
    """获取转换器实例"""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = EnhancedFormulaConverter()
    return _converter_instance