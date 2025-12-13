"""
修复的API测试
"""

import unittest
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from app import app


class TestFormulaAPI(unittest.TestCase):
    """测试公式API"""

    def setUp(self):
        """测试前设置"""
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        """测试健康检查接口"""
        response = self.app.get('/api/v1/formula/health')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 200)
        self.assertIn('data', data)
        self.assertIn('status', data['data'])

    def test_convert_formula_no_text(self):
        """测试无文本输入的公式转换"""
        response = self.app.post('/api/v1/formula/convert',
                                 json={})

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 400)

    def test_convert_formula_with_text(self):
        """测试带文本输入的公式转换"""
        request_data = {
            "text": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)"
        }

        response = self.app.post('/api/v1/formula/convert',
                                 json=request_data)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 200)
        self.assertIn('data', data)
        self.assertIn('latex', data['data'])
        self.assertIn('confidence', data['data'])

    def test_convert_formula_get(self):
        """测试GET方法的公式转换"""
        response = self.app.get('/api/v1/formula/convert')

        # GET方法应该返回200（提供示例或说明）
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('data', data)

    def test_validate_formula_valid(self):
        """测试有效公式验证"""
        request_data = {
            "text": "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}",
            "type": "latex"
        }

        response = self.app.post('/api/v1/formula/validate',
                                 json=request_data)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 200)
        self.assertIn('data', data)
        self.assertIn('is_valid', data['data'])

    def test_validate_formula_invalid(self):
        """测试无效公式验证"""
        request_data = {
            "text": "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a",  # 缺少闭合括号
            "type": "latex"
        }

        response = self.app.post('/api/v1/formula/validate',
                                 json=request_data)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 200)
        self.assertIn('data', data)
        self.assertIn('is_valid', data['data'])
        # 无效公式应该返回 False
        self.assertFalse(data['data']['is_valid'])

    def test_batch_convert_formula(self):
        """测试批量公式转换"""
        request_data = {
            "formulas": ["a^2 + b^2 = c^2", "E = mc^2"]
        }

        response = self.app.post('/api/v1/formula/batch_convert',
                                 json=request_data)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 200)
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
        self.assertEqual(len(data['data']), 2)

    def test_not_found_error(self):
        """测试404错误处理"""
        response = self.app.get('/api/v1/nonexistent')
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 404)

    def test_method_not_allowed(self):
        """测试405错误处理"""
        # 假设 /api/v1/formula/batch_convert 只支持POST
        response = self.app.get('/api/v1/formula/batch_convert')
        self.assertEqual(response.status_code, 405)

        data = json.loads(response.data)
        self.assertEqual(data['status_code'], 405)


if __name__ == '__main__':
    unittest.main(verbosity=2)