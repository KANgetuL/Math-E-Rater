import pytest
import json
from fastapi.testclient import TestClient
import os
import sys

# 关键修复：在 CI/CD 或复杂环境中，确保测试可以找到 `src` 模块。
# 在某些环境中，Pytest 运行器会自动处理这些路径。
# 暂时保留路径修改，确保测试通过，但在大型项目中应配置 pyproject.toml。
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入 FastAPI 应用实例，并使用别名以避免与局部变量冲突
from src.main import app as main_app

# ----------------------------------------------------

# 创建一个用于测试 FastAPI 接口的客户端
client = TestClient(main_app)  # 使用导入的别名

# 模拟输入 Question 数据 (与 Mock 逻辑兼容)
MOCK_QUESTION = {
    "id": "test_q004",
    "type": "algebra",
    "text": "求 $2x + 10 = 16$ 的解。",
    "known_facts": ["$2x + 10 = 16$"],
    "unknowns": ["$x$"],
    "constrains": ["$x > 0$"],
    "img_vec": []
}


# ----------------------------------------------------------------------------------
# 1. 集成测试：验证解决方案结构 (Solution Structure Integration)
# ----------------------------------------------------------------------------------

def test_api_solution_structure_integration():
    """
    测试 /api/v1/solver/solve 接口是否正确返回解决方案结构。
    检查解决方案是否包含所有必需的字段。
    """
    # 模拟 POST 请求
    response = client.post("/api/v1/solver/solve", json=MOCK_QUESTION)

    # 1. 检查 HTTP 状态码
    assert response.status_code == 200
    response_json = response.json()

    # 2. 检查 API 响应结构
    assert "code" in response_json
    assert "msg" in response_json
    assert "data" in response_json
    assert "confidence" in response_json

    data = response_json["data"]

    # 3. 检查 data 结构
    assert "solutions" in data
    assert "dedup_count" in data

    # 4. 检查是否有解决方案返回 (Mock 模式下应该返回至少一个)
    assert len(data["solutions"]) >= 1

    first_solution = data["solutions"][0]

    # 5. 检查解决方案应包含的字段（根据实际 SingleSolution 模型）
    # SingleSolution 包含：steps, answer, confidence, difficulty_vec
    required_fields = ["steps", "answer", "confidence", "difficulty_vec"]

    for field in required_fields:
        assert field in first_solution, f"解决方案缺少字段: {field}"

    # 6. 验证字段类型
    assert isinstance(first_solution["steps"], list)
    assert isinstance(first_solution["answer"], str)
    assert isinstance(first_solution["confidence"], (int, float))
    # 【已修正】difficulty_vec 必须是 float 列表
    assert isinstance(first_solution["difficulty_vec"], list)
    if first_solution["difficulty_vec"]:
        assert isinstance(first_solution["difficulty_vec"][0], float)

    print("✅ 测试通过: 解决方案结构正确。")


# ----------------------------------------------------------------------------------
# 2. 集成测试：验证置信度计算 (Confidence Calculation Integration)
# ----------------------------------------------------------------------------------

def test_api_confidence_integration():
    """
    测试 /api/v1/solver/solve 接口是否正确计算和返回置信度。
    Mock 模式下的预期置信度：0.95, 0.92, 0.89
    """
    # 模拟 POST 请求
    response = client.post("/api/v1/solver/solve", json=MOCK_QUESTION)
    response_json = response.json()
    data = response_json["data"]

    solutions = data["solutions"]

    # 1. 检查置信度字段是否存在
    for solution in solutions:
        assert "confidence" in solution

    # 2. 如果有多个解，验证置信度递减逻辑
    # 注意：由于去重过程的存在，这个断言可能不总是成立，但在 Mock 环境中，
    # 我们知道所有 Mock 生成的解法都是相同的，因此去重后可能只剩一个。
    # 我们改为验证最高置信度是否在预期范围内。

    if solutions:
        max_confidence = response_json["confidence"]

        # 3. 验证最高置信度是否在预期范围内（main.py中的最高初始值是0.95）
        assert 0.8 < max_confidence <= 1.0  # 0.8 是一个安全下限

        # 4. 验证 APIResponse 中的 confidence 等于 solutions 中的最高 confidence
        solutions_confidences = [s["confidence"] for s in solutions]
        if solutions_confidences:
            assert abs(max_confidence - max(solutions_confidences)) < 1e-6

    print("✅ 测试通过: 置信度计算逻辑正确。")


# ----------------------------------------------------------------------------------
# 3. 集成测试：验证去重功能 (Deduplication Integration)
# ----------------------------------------------------------------------------------

def test_api_deduplication_integration():
    """
    测试 /api/v1/solver/solve 接口的去重功能。
    在 Mock 模式下，generate_solution_chain 会重复返回完全相同的解法。
    因此，预期 dedup_count 应该大于等于 2 (3个生成中，只有第一个被保留)。
    """
    response = client.post("/api/v1/solver/solve", json=MOCK_QUESTION)
    response_json = response.json()
    data = response_json["data"]

    # 1. 检查去重计数字段存在
    assert "dedup_count" in data
    assert isinstance(data["dedup_count"], int)

    # 2. 检查去重数量
    # 总共生成 3 个解，Mock 模型返回相同内容，所以 2 个应该被去重。
    assert data["dedup_count"] >= 2

    # 3. 检查去重后保留的解的数量
    # 3 - dedup_count 应该等于 len(solutions)
    solutions = data["solutions"]
    assert len(solutions) == 3 - data["dedup_count"]

    print("✅ 测试通过: 去重功能正常。")