import argparse
import json
import time
import sys
import os
from typing import Dict, Any, List, Optional

# --- 路径修复：确保可以导入 src 模块 ---
# 无论从哪个目录执行，都能找到 src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 核心逻辑导入 ---
from src.solver_utils import (
    generate_solution_chain,
    self_check_solution,
    is_solution_similar,
    parse_generated_solution,
    score_solution
)
from src.data_models import Question, SingleSolution # 导入 SingleSolution 用于构造最终结果

# ----------------------------------------------------
# 模型占位符 (与 API 中的 Mock 保持一致)
# ----------------------------------------------------
LLM_MODEL_INSTANCE = "Mock_LLM_Instance"


# ----------------------------------------------------
# 1. 命令行参数
# ----------------------------------------------------

def setup_arg_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Math-E-Rater Solver 命令行推理")
    parser.add_argument(
        "--question_json",
        type=str,
        required=True,
        help="包含题目信息的 JSON 字符串. "
             "示例: '{\"id\": \"q123\", \"type\": \"algebra\", \"text\": \"解方程 2x + 3 = 7\", \"known_facts\": [], \"unknowns\": [], \"constrains\": [], \"img_vec\": []}'"
    )
    parser.add_argument(
        "--model_weights",
        type=str,
        default="../weights/solver_best.pt",
        help="指向 LoRA 权重文件的路径"
    )
    return parser.parse_args()


# ----------------------------------------------------
# 2. 模型加载 (填充 LoRA 逻辑)
# ----------------------------------------------------

def initialize_model(weights_path: str):
    """
    加载模型和权重.
    TODO: 在这里实现你的 LLM 和 LoRA 权重加载逻辑（使用 PeftModel 和 AutoModelForCausalLM）
    """
    if weights_path != "../weights/solver_best.pt":
        print(f"--- ⚠️ 正在加载真实模型... (权重路径: {weights_path})")
        # 实际加载逻辑...
        pass

    print("--- 正在使用 Mock 模式或模型加载完成。---")
    return LLM_MODEL_INSTANCE


# ----------------------------------------------------
# 3. 核心求解逻辑
# ----------------------------------------------------

def solve_question(model_name: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    调用核心逻辑生成解答，并执行自检和评分。
    """
    print(f"--- 正在解答题目: {question_data.get('text')} ---")

    # 1. 格式化输入
    try:
        question = Question(**question_data)
    except Exception as e:
        return {"error": f"输入数据格式不符合 Question 模型规范: {e}"}

    # 设置需要生成的解答数量
    NUM_GENERATIONS = 3

    # 2. 调用 "生成链" (生成 3 个原始解)
    # generate_solution_chain 返回的是 LLM 原始输出的列表
    llm_outputs = generate_solution_chain(question.model_dump(), model_name, num_solutions=NUM_GENERATIONS)

    raw_solutions: List[SingleSolution] = []

    for i, output in enumerate(llm_outputs):
        parsed_data = parse_generated_solution(output, default_confidence=0.95 - (i * 0.03))

        steps = parsed_data['steps']
        answer = parsed_data['answer']
        confidence = parsed_data['confidence']
        solution_steps_string = " ".join(steps)

        if not steps or not answer or answer == '答案缺失':
            print(f"第 {i + 1} 次生成失败，跳过。")
            continue

        # 3. 自检/评分流程
        # (c) 调用自检链：检查逻辑错误
        check_result = self_check_solution(question.text, solution_steps_string, model_name)

        # 业务逻辑: 如果自检失败，降低该解的置信度
        if check_result.get('review_status') == 'FAIL':
            confidence *= 0.8

        # (d) 调用评分模型：获取精细化评分
        # score_solution 现在返回 Dict，包含 final_score 和 difficulty_vec
        score_data = score_solution(question.text, steps, model_name)
        final_score = score_data.get('final_score', 0.0)

        # 重新计算置信度（以评分模型为准）
        confidence = round(final_score / 5.0, 4)

        # 提取难度向量
        difficulty_vec = score_data.get('difficulty_vec', [])

        # 构造 SingleSolution 对象
        raw_solutions.append(
            SingleSolution(
                steps=steps,
                answer=answer,
                confidence=confidence,
                difficulty_vec=difficulty_vec
            )
        )

    # 4. 去重模型过滤
    sorted_raw_solutions = sorted(raw_solutions, key=lambda s: s.confidence, reverse=True)
    unique_solutions: List[SingleSolution] = []
    dedup_count = 0

    for new_solution in sorted_raw_solutions:
        is_duplicate = False

        for existing_solution in unique_solutions:
            # 使用 is_solution_similar 进行语义去重
            if is_solution_similar(new_solution.steps, existing_solution.steps, threshold=0.9):
                is_duplicate = True
                # 这里只计数，不 break，因为是基于整个 raw_solutions 列表
                # 只有当发现重复时，我们才将 new_solution 标记为 duplicate，并在外部计数
                break

        if not is_duplicate:
            unique_solutions.append(new_solution)
        else:
            # 只有当 new_solution 是重复的时候才计数
            dedup_count += 1

    return {
        "solutions": [sol.model_dump() for sol in unique_solutions],  # 转换为字典列表以便 JSON 输出
        "dedup_count": dedup_count,
    }


# ----------------------------------------------------
# 4. 主函数
# ----------------------------------------------------

def main():
    """主函数入口"""
    args = setup_arg_parser()

    # 1. 加载模型
    model_name = initialize_model(args.model_weights)

    # 2. 解析输入
    try:
        question_data = json.loads(args.question_json)
    except json.JSONDecodeError:
        print("错误: --question_json 参数不是一个有效的 JSON 字符串。")
        return
    except Exception as e:
        print(f"解析输入时发生未知错误: {e}")
        return

    # 3. 执行推理
    start_time = time.time()
    result = solve_question(model_name, question_data)
    end_time = time.time()

    # 4. 格式化输出
    print("\n--- 结果 ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n解答耗时: {end_time - start_time:.4f} 秒")


if __name__ == "__main__":
    # 提示：请在项目根目录运行此脚本：
    # python -m inference --question_json '{"id": "q1", "type": "algebra", "text": "解方程 2x + 3 = 7", "known_facts": ["2x+3=7"], "unknowns": ["x"], "constrains": ["x is integer"], "img_vec": []}'
    main()