from pydantic import BaseModel, Field
from typing import List, Optional, Generic, TypeVar

# ----------------------------------------------------------------------------------
# 1. 输入数据模型 (Question)
# ----------------------------------------------------------------------------------

class Question(BaseModel):
    """
    用户输入的问题结构，包含所有必要的信息。
    """
    id: str = Field(..., description="问题的唯一标识符。")
    type: str = Field(..., description="问题的类型（如 'algebra', 'geometry', 'application'）。")
    text: str = Field(..., description="问题的自然语言描述或数学表达式。")
    known_facts: List[str] = Field(default_factory=list, description="已知条件或事实列表。")
    unknowns: List[str] = Field(default_factory=list, description="要求解的未知数或目标。")
    constrains: List[str] = Field(default_factory=list, description="问题的额外约束条件。")
    img_vec: List[float] = Field(default_factory=list, description="图像特征向量（如果适用）。")


# ----------------------------------------------------------------------------------
# 2. 输出数据模型 (Solutions)
# ----------------------------------------------------------------------------------

class SingleSolution(BaseModel):
    """
    单个解法模型，包含详细步骤、答案、置信度及难度向量。
    """
    steps: List[str] = Field(..., description="解题步骤的列表。")
    answer: str = Field(..., description="最终答案。")
    confidence: float = Field(..., description="该解法的置信度（0.0到1.0）。")
    # 难度向量：包含多个维度（如概念难度、计算复杂度等）
    difficulty_vec: List[float] = Field(..., description="难度特征向量（必须是 float 列表）。")

# ----------------------------------------------------------------------------------
# 3. 响应数据模型 (Response Structure)
# ----------------------------------------------------------------------------------

class SolutionResponseData(BaseModel):
    """
    /api/v1/solver/solve 接口返回的数据体 (data) 内容。
    """
    solutions: List[SingleSolution] = Field(..., description="去重并排序后的唯一解法列表。")
    dedup_count: int = Field(..., description="去重过程中移除的重复解法数量。")

# 泛型类型变量
T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """
    统一的 API 响应结构，使用泛型支持不同的数据体。
    """
    code: int = Field(..., description="业务状态码 (0表示成功)。")
    msg: str = Field(..., description="业务消息。")
    data: T = Field(..., description="具体的响应数据体。")
    confidence: float = Field(..., description="所有解法中最高的置信度。")