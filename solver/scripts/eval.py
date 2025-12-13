import argparse
import json
import time
import os
import sys
from typing import List, Dict, Any, Tuple

# --- 路径修复：确保可以导入 src 模块 ---
# 无论从哪个目录执行，都能找到 src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.solver_utils import (
    generate_solution_chain,  # 现已在 solver_utils 中集中实现
    score_solution,  # 现已在 solver_utils 中实现复杂字典返回
    parse_generated_solution,
    call_llm_api  # 现已在 solver_utils 中集中实现
)
from src.data_models import Question

# ----------------------------------------------------
# 1. 设置模型和参数
# ----------------------------------------------------
# 使用一个占位符来模拟 LLM 实例
EVAL_LLM_MODEL = "Mock_LLM_Instance"


def setup_arg_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Math-E-Rater 评分模型评估脚本")

    parser.add_argument(
        "--model_path",
        type=str,
        default="../weights/solver_best.pt",
        help="指向 LoRA 权重文件的路径，用于加载模型。"
    )
    parser.add_argument(
        "--data_path",
        type=str,
        required=True,
        help="评估数据集路径，必须是 JSONL (每行一个 JSON 对象) 格式。"
    )

    return parser.parse_args()


# ----------------------------------------------------
# 2. 评估核心函数
# ----------------------------------------------------

def evaluate_model(model_path: str, data_path: str, model_instance: str) -> Dict[str, Any]:
    """
    遍历评估数据集，调用生成链和评分模型进行评估。
    """
    print(f"--- 🚀 正在初始化模型: {model_path} ---")
    time.sleep(1)
    print("模型初始化完成，开始评估。")

    # 1. 读取数据集
    try:
        data = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))

        total_samples = len(data)
        if total_samples == 0:
            return {"error": "评估数据集为空。", "total_samples": 0}

    except Exception as e:
        return {"error": f"读取或解析数据集失败: {e}"}

    print(f"成功加载 {total_samples} 个评估样本。")

    # 2. 评估循环
    total_score = 0.0
    correct_count = 0
    evaluated_count = 0

    for i, sample in enumerate(data):
        start_sample_time = time.time()

        try:
            # 将字典转换为 Question Pydantic 模型，确保数据规范
            question = Question(**sample)
        except Exception as e:
            print(f"样本 {i + 1} 数据格式错误，跳过: {e}")
            continue

        question_text = question.text

        # (a) 调用生成链：返回 LLM 原始输出列表 (这里只需要 1 个)
        llm_outputs = generate_solution_chain(question.model_dump(), model_instance, num_solutions=1)

        if not llm_outputs:
            print(f"样本 {i + 1}：生成失败，跳过评分。")
            continue

        llm_output = llm_outputs[0]
        parsed_data = parse_generated_solution(llm_output)

        steps = parsed_data['steps']

        if not steps:
            print(f"样本 {i + 1}：步骤为空，跳过评分。")
            continue

        # (b) 调用评分模型：score_solution 现在返回 Dict
        score_data = score_solution(question_text, steps, model_instance)
        final_score = score_data.get('final_score', 1.0)

        # 只有成功评分的样本才计入评估总数
        evaluated_count += 1
        total_score += final_score

        # 模拟“正确性”判断：如果答案正确性维度大于等于 4 分，视为通过
        correctness_score = score_data.get('dimensions', {}).get('correctness_score', 1)
        if correctness_score >= 4:
            correct_count += 1

        print(
            f"样本 {i + 1} | 评分: {final_score:.2f} | 正确性: {correctness_score}/5 | 耗时: {time.time() - start_sample_time:.2f}s | 通过: {'是' if correctness_score >= 4 else '否'}"
        )

    # 3. 计算最终指标
    avg_score = total_score / evaluated_count if evaluated_count > 0 else 0.0
    pass_rate = correct_count / evaluated_count if evaluated_count > 0 else 0.0

    return {
        "total_samples": total_samples,
        "total_evaluated": evaluated_count,
        "average_score": round(avg_score, 4),
        "correct_count": correct_count,
        "pass_rate": round(pass_rate, 4),
        "model_used": model_instance,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def main():
    """主函数入口"""
    args = setup_arg_parser()

    start_time = time.time()

    # 执行评估
    results = evaluate_model(args.model_path, args.data_path, EVAL_LLM_MODEL)

    end_time = time.time()

    # 格式化输出
    print("\n======================================")
    print("       🎉 评估结果摘要 🎉")
    print("======================================")
    print(json.dumps(results, indent=4, ensure_ascii=False))
    print(f"总评估耗时: {end_time - start_time:.2f} 秒")
    print("======================================")


if __name__ == "__main__":
    # 提示：请在项目根目录运行此脚本：
    # python -m eval --data_path data/mock_eval.jsonl
    main()