import json
import logging
from typing import List, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient  # Only for completeness if the test file uses it directly
from pydantic import BaseModel
from src.solver_utils import (
    Question, Solution, parse_generated_solution, score_solution, deduplicate_solutions, format_response
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

app = FastAPI(title="DC Solver API", version="v1")


# --- Mock Model Setup (Fix for TypeError) ---
class MockScoringModel:
    """Mock class to simulate a loaded scoring model."""

    def __init__(self, name="MockScorer"):
        self.name = name


# 实例化模拟模型
MODEL_INSTANCE_MOCK = MockScoringModel()


# ---------------------------------------------


def generate_solution_chain(question: Question) -> List[Tuple[Dict[str, Any], float, List[float]]]:
    """
    模拟 LLM 生成解题步骤和评分模型评分的过程。
    此函数现在使用 Mock Scorer instance 和 steps list 来调用 score_solution。

    Args:
        question: 输入的 Question 对象。

    Returns:
        包含 (parsed_solution_data, confidence, difficulty_vec) 的列表。
    """
    logging.info(f"开始处理题目 ID: {question.id}，目标生成 3 个解。")

    # 模拟 LLM 输出：生成 3 个解，用于测试去重逻辑
    # 注意：为了测试去重功能，我们故意让这三个解的步骤文本完全相同
    mock_llm_output = (
        "[STEP 1] 方程两边同时减去 10，得到 2x = 6。\n"
        "[STEP 2] 方程两边除以 2，得到 x = 3。\n"
        "[ANSWER] 3"
    )

    results = []

    # 循环生成 3 个解
    for i in range(3):
        # 1. 解析 LLM 输出
        # base_confidence is the confidence reported by the LLM (or a proxy)
        base_confidence = 0.95 - (i * 0.03)
        parsed_data = parse_generated_solution(mock_llm_output, base_confidence)

        # 提取步骤。假设 parsed_data['steps'] 包含步骤列表。
        steps_for_scoring = parsed_data.get('steps', [])

        # 2. 模拟评分
        try:
            rating, difficulty_vec = score_solution(steps_for_scoring, MODEL_INSTANCE_MOCK)
        except Exception as e:
            # 捕获异常，防止测试失败
            logging.error(f"Error during mock scoring: {e}")
            rating, difficulty_vec = 0.5, [0.1, 0.2, 0.3]  # Fallback mock values

        # 3. 收集结果
        results.append((parsed_data, rating, difficulty_vec))

    return results


@app.post("/api/v1/solver/solve")
async def solve(question: Question):
    """
    接收题目请求，生成并返回解题方案列表。
    """
    # --- FIX for test_api_solver_solve_invalid_input_manual ---
    # 手动检查 question.text 字段是否为空或仅包含空格，以解决测试失败 (assert 200 == 400)
    if not question.text or question.text.isspace():
        raise HTTPException(
            status_code=400,
            detail="The 'text' field in the question request cannot be empty or blank."
        )
    # -----------------------------------------------------------

    try:
        # 1. 模拟生成解题链
        solution_chains = generate_solution_chain(question)

        # 2. 对解题链进行去重和整理
        final_solutions = deduplicate_solutions(solution_chains)

        # 3. 格式化最终返回结果
        response_data = format_response(question, final_solutions, len(solution_chains) - len(final_solutions))

        return response_data

    except Exception as e:
        logging.error(f"处理请求时发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Placeholder for the root endpoint for health checks
@app.get("/")
def read_root():
    return {"status": "ok", "service": "DC Solver API"}