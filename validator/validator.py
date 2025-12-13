import sys
import os

# 获取当前文件（validator.py）的绝对路径
current_file_path = os.path.abspath(__file__)
# 导航到项目根目录（假设 validator 目录与 src 目录同级，都在 solver 目录下）
# 例如：Math-E-Rater/solver/validator/validator.py -> Math-E-Rater/solver/
project_root = os.path.dirname(os.path.dirname(current_file_path))
# 将项目根目录添加到 Python 路径中
sys.path.insert(0, project_root)

from typing import Dict, Any, Tuple
from src.solver_utils import Question, Solution  # 复用现有数据模型

# 允许的题目类型
ALLOWED_QUESTION_TYPES = {"algebra", "geometry"}


def validate_question(question_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证题目数据是否符合规范
    :param question_data: 题目字典数据
    :return: (是否有效, 错误信息)
    """
    try:
        # 1. 验证基本结构（依赖Pydantic模型的字段检查）
        question = Question(**question_data)
    except Exception as e:
        return False, f"字段格式错误: {str(e)}"

    # 2. 业务规则验证
    if not question.text or question.text.strip() == "":
        return False, "题目文本（text）不能为空"

    if question.type not in ALLOWED_QUESTION_TYPES:
        return False, f"题目类型（type）必须为 {ALLOWED_QUESTION_TYPES}"

    if not isinstance(question.img_vec, list):
        return False, "图像向量（img_vec）必须为列表类型"

    # 3. 检查向量元素是否为数值（若存在）
    for idx, val in enumerate(question.img_vec):
        if not isinstance(val, (int, float)):
            return False, f"图像向量（img_vec）第 {idx+1} 个元素必须为数值"

    return True, ""


def validate_solution(solution_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证解答数据是否符合规范
    :param solution_data: 解答字典数据
    :return: (是否有效, 错误信息)
    """
    try:
        # 1. 验证基本结构
        solution = Solution(** solution_data)
    except Exception as e:
        return False, f"字段格式错误: {str(e)}"

    # 2. 业务规则验证
    if not solution.answer or solution.answer.strip() == "":
        return False, "答案（answer）不能为空"

    if not (0 <= solution.confidence <= 1):
        return False, "置信度（confidence）必须在 [0, 1] 范围内"

    if not (0 <= solution.rating <= 1):
        return False, "评分（rating）必须在 [0, 1] 范围内"

    # 3. 验证步骤连续性（step_index必须从1开始递增）
    step_indices = [step.step_index for step in solution.steps]
    for i in range(len(step_indices)):
        if step_indices[i] != i + 1:
            return False, f"步骤索引不连续，第 {i+1} 步应为 {i+1}"

    # 4. 验证难度向量元素是否为数值
    for idx, val in enumerate(solution.difficulty_vec):
        if not isinstance(val, (int, float)):
            return False, f"难度向量（difficulty_vec）第 {idx+1} 个元素必须为数值"

    return True, ""


def run_validation_tests(cases_path: str = "configs/cases.json") -> None:
    """
    运行配置文件中的验证测试用例
    :param cases_path: 用例配置文件路径
    """
    import json
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # 测试题目验证
    print("=== 开始题目验证测试 ===")
    for case in cases["question_validation_cases"]:
        is_valid, error_msg = validate_question(case["input"])
        assert is_valid == case["expected"]["is_valid"], \
            f"用例 {case['case_id']} 失败: 预期 {'有效' if case['expected']['is_valid'] else '无效'}，实际 {'有效' if is_valid else '无效'}"
        assert error_msg == case["expected"]["error_msg"], \
            f"用例 {case['case_id']} 错误信息不匹配: 预期 '{case['expected']['error_msg']}'，实际 '{error_msg}'"
        print(f"用例 {case['case_id']}: 成功")

    # 测试解答验证
    print("\n=== 开始解答验证测试 ===")
    for case in cases["solution_validation_cases"]:
        is_valid, error_msg = validate_solution(case["input"])
        assert is_valid == case["expected"]["is_valid"], \
            f"用例 {case['case_id']} 失败: 预期 {'有效' if case['expected']['is_valid'] else '无效'}，实际 {'有效' if is_valid else '无效'}"
        assert error_msg == case["expected"]["error_msg"], \
            f"用例 {case['case_id']} 错误信息不匹配: 预期 '{case['expected']['error_msg']}'，实际 '{error_msg}'"
        print(f"用例 {case['case_id']}: 成功")

    print("\n=== 所有验证测试通过 ===")


if __name__ == "__main__":
    run_validation_tests()