"""
文本公式识别API服务 - 完整版
支持GET和POST方法
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.text_formula_model import get_converter

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB最大上传
app.config['DEBUG'] = True

# 全局转换器实例
converter = get_converter()


# ============ 辅助函数 ============
def create_response(data=None, status_code=200, msg="成功"):
    """
    创建统一格式的响应
    """
    return {
        "data": data,
        "status_code": status_code,
        "msg": msg
    }


def handle_exception(e, status_code=500):
    """
    处理异常，返回统一格式的错误响应
    """
    error_msg = str(e)

    # 在调试模式下返回详细的错误信息
    if app.config.get('DEBUG'):
        error_msg += f"\n{traceback.format_exc()}"

    return jsonify(create_response(
        data=None,
        status_code=status_code,
        msg=error_msg
    )), status_code


def format_latex_for_display(latex_text: str) -> str:
    """
    格式化LaTeX用于显示
    """
    if not latex_text:
        return ""

    # 添加数学环境分隔符（如果没有的话）
    if not latex_text.startswith('$') and not latex_text.startswith('\\['):
        latex_text = f"${latex_text}$"

    return latex_text


def calculate_complexity(latex_text: str) -> float:
    """
    计算LaTeX公式的复杂度
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


# ============ API路由 ============
@app.route('/api/v1/formula/convert', methods=['GET', 'POST'])
def convert_formula():
    """
    公式转换接口 - 支持GET和POST方法
    """
    try:
        # 获取输入文本
        text = ""

        if request.method == 'POST':
            # POST方法：从JSON获取数据
            data = request.get_json()
            if not data:
                return jsonify(create_response(
                    data=None,
                    status_code=400,
                    msg="请求体必须是JSON格式"
                )), 400

            if 'text' not in data:
                return jsonify(create_response(
                    data=None,
                    status_code=400,
                    msg="缺少必需字段: text"
                )), 400

            text = data['text'].strip()

        else:  # GET方法
            # GET方法：从查询参数获取数据
            text = request.args.get('text', '').strip()
            if not text:
                # 如果没有提供text参数，返回示例
                return jsonify(create_response(
                    data={
                        "example": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
                        "description": "请使用POST方法发送JSON数据，或GET方法添加text参数",
                        "post_example": {
                            "method": "POST",
                            "url": "/api/v1/formula/convert",
                            "body": {"text": "您的公式"}
                        },
                        "get_example": {
                            "method": "GET",
                            "url": "/api/v1/formula/convert?text=您的公式"
                        }
                    },
                    status_code=200,
                    msg="请提供公式文本"
                ))

        # 检查文本长度
        if len(text) > 1000:
            return jsonify(create_response(
                data=None,
                status_code=400,
                msg=f"输入文本过长，最大长度: 1000"
            )), 400

        # 转换公式
        latex_output, confidence = converter.convert_to_latex(text)

        # 格式化显示
        formatted_output = format_latex_for_display(latex_output)

        # 计算复杂度
        complexity = calculate_complexity(latex_output)

        # 验证LaTeX
        is_valid, validation_msg = converter.validate_latex(latex_output)

        # 构建响应数据
        response_data = {
            "original": text,
            "latex": latex_output,
            "formatted": formatted_output,
            "confidence": confidence,
            "complexity": round(complexity, 2),
            "is_valid": is_valid,
            "validation_msg": validation_msg if not is_valid else "LaTeX语法有效",
            "method_used": request.method
        }

        return jsonify(create_response(
            data=response_data,
            status_code=200,
            msg="公式转换成功"
        ))

    except Exception as e:
        return handle_exception(e)


@app.route('/api/v1/formula/validate', methods=['GET', 'POST'])
def validate_formula():
    """
    公式验证接口 - 支持GET和POST方法
    """
    try:
        # 获取输入
        latex_text = ""
        input_type = "latex"

        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify(create_response(
                    data=None,
                    status_code=400,
                    msg="请求体必须是JSON格式"
                )), 400

            if 'text' not in data:
                return jsonify(create_response(
                    data=None,
                    status_code=400,
                    msg="缺少必需字段: text"
                )), 400

            latex_text = data['text'].strip()
            input_type = data.get('type', 'latex')

        else:  # GET方法
            latex_text = request.args.get('text', '').strip()
            input_type = request.args.get('type', 'latex')

        if not latex_text:
            return jsonify(create_response(
                data=None,
                status_code=400,
                msg="请输入要验证的文本"
            )), 400

        if input_type not in ['text', 'latex']:
            return jsonify(create_response(
                data=None,
                status_code=400,
                msg="type参数必须是 'text' 或 'latex'"
            )), 400

        # 如果是文本输入，先转换为LaTeX
        if input_type == 'text':
            latex_output, confidence = converter.convert_to_latex(latex_text)
            is_valid, validation_msg = converter.validate_latex(latex_output)

            response_data = {
                "input_type": "text",
                "original_text": latex_text,
                "latex": latex_output,
                "confidence": confidence,
                "is_valid": is_valid,
                "validation_msg": validation_msg
            }
        else:
            # 直接验证LaTeX
            is_valid, validation_msg = converter.validate_latex(latex_text)

            response_data = {
                "input_type": "latex",
                "latex": latex_text,
                "is_valid": is_valid,
                "validation_msg": validation_msg
            }

        return jsonify(create_response(
            data=response_data,
            status_code=200,
            msg="公式验证完成"
        ))

    except Exception as e:
        return handle_exception(e)


@app.route('/api/v1/formula/batch_convert', methods=['POST'])
def batch_convert_formula():
    """
    批量公式转换接口 - 仅支持POST方法
    """
    try:
        # 获取请求数据
        data = request.get_json()

        if not data:
            return jsonify(create_response(
                data=None,
                status_code=400,
                msg="请求体必须是JSON格式"
            )), 400

        # 检查必需字段
        if 'formulas' not in data:
            return jsonify(create_response(
                data=None,
                status_code=400,
                msg="缺少必需字段: formulas"
            )), 400

        formulas = data['formulas']

        if not isinstance(formulas, list):
            return jsonify(create_response(
                data=None,
                status_code=400,
                msg="formulas必须是列表"
            )), 400

        # 检查列表长度
        if len(formulas) > 100:
            return jsonify(create_response(
                data=None,
                status_code=400,
                msg="一次最多处理100个公式"
            )), 400

        # 批量转换
        results = converter.batch_convert(formulas)

        # 统计成功/失败数量
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)

        return jsonify(create_response(
            data=results,
            status_code=200,
            msg=f"批量转换完成，成功 {successful}/{total}"
        ))

    except Exception as e:
        return handle_exception(e)


@app.route('/api/v1/formula/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    try:
        health_data = {
            "status": "healthy",
            "service": "enhanced-formula-converter",
            "version": "2.0.0",
            "endpoints": {
                "convert": {
                    "url": "/api/v1/formula/convert",
                    "methods": ["GET", "POST"],
                    "description": "公式转换"
                },
                "validate": {
                    "url": "/api/v1/formula/validate",
                    "methods": ["GET", "POST"],
                    "description": "公式验证"
                },
                "batch_convert": {
                    "url": "/api/v1/formula/batch_convert",
                    "methods": ["POST"],
                    "description": "批量转换"
                }
            },
            "supported_features": [
                "文本公式转LaTeX",
                "LaTeX语法验证",
                "批量处理",
                "GET/POST方法支持"
            ]
        }

        return jsonify(create_response(
            data=health_data,
            status_code=200,
            msg="服务运行正常"
        ))

    except Exception as e:
        return jsonify(create_response(
            data={"status": "unhealthy", "error": str(e)},
            status_code=503,
            msg="服务异常"
        )), 503


@app.route('/')
def index():
    """首页 - 提供API测试界面"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>增强公式转换API</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f5f7fa;
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .container {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
                padding: 30px;
                margin-bottom: 30px;
            }
            
            h1 {
                color: #2c3e50;
                margin-bottom: 20px;
                text-align: center;
            }
            
            h2 {
                color: #3498db;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #eee;
            }
            
            h3 {
                color: #7f8c8d;
                margin: 15px 0 10px 0;
            }
            
            .endpoint {
                background-color: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 0 5px 5px 0;
            }
            
            .method {
                display: inline-block;
                background-color: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
            }
            
            .method.get {
                background-color: #2ecc71;
            }
            
            .method.post {
                background-color: #f39c12;
            }
            
            .url {
                font-family: 'Courier New', monospace;
                font-size: 16px;
                color: #2c3e50;
            }
            
            .demo-section {
                margin-bottom: 25px;
                padding: 20px;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2c3e50;
            }
            
            textarea, input[type="text"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
                font-family: 'Courier New', monospace;
            }
            
            textarea:focus, input[type="text"]:focus {
                border-color: #3498db;
                outline: none;
            }
            
            textarea {
                min-height: 100px;
                resize: vertical;
            }
            
            .button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: background-color 0.3s;
                margin-right: 10px;
                margin-top: 10px;
            }
            
            .button:hover {
                background-color: #2980b9;
            }
            
            .button.secondary {
                background-color: #95a5a6;
            }
            
            .button.secondary:hover {
                background-color: #7f8c8d;
            }
            
            .response {
                margin-top: 20px;
                padding: 15px;
                border-radius: 6px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                max-height: 400px;
                overflow-y: auto;
            }
            
            pre {
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .success {
                color: #27ae60;
            }
            
            .error {
                color: #e74c3c;
            }
            
            .example-formula {
                background-color: #e8f4f8;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .example-formula:hover {
                background-color: #d4eaf0;
            }
            
            .tab {
                display: flex;
                margin-bottom: 20px;
                border-bottom: 2px solid #eee;
            }
            
            .tab-button {
                padding: 10px 20px;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 16px;
                color: #7f8c8d;
                border-bottom: 3px solid transparent;
                transition: all 0.3s;
            }
            
            .tab-button.active {
                color: #3498db;
                border-bottom: 3px solid #3498db;
                font-weight: 600;
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            @media (max-width: 768px) {
                body {
                    padding: 10px;
                }
                
                .container {
                    padding: 20px;
                }
                
                .button {
                    width: 100%;
                    margin-bottom: 10px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>增强公式转换API</h1>
            <p>将纯文本数学公式转换为LaTeX格式，支持GET和POST方法。</p>
            
            <div class="tab">
                <button class="tab-button active" onclick="switchTab('demo')">在线测试</button>
                <button class="tab-button" onclick="switchTab('docs')">API文档</button>
                <button class="tab-button" onclick="switchTab('examples')">示例</button>
            </div>
            
            <!-- 演示标签页 -->
            <div id="demo-tab" class="tab-content active">
                <div class="demo-section">
                    <h3>公式转换测试</h3>
                    <p>输入文本公式，转换为LaTeX格式：</p>
                    
                    <div class="example-formulas">
                        <p>示例公式（点击使用）：</p>
                        <div class="example-formula" onclick="setExample('quadratic')">二次方程求根公式: x = (-b ± sqrt(b^2 - 4ac)) / (2a)</div>
                        <div class="example-formula" onclick="setExample('pythagorean')">勾股定理: a^2 + b^2 = c^2</div>
                        <div class="example-formula" onclick="setExample('emc2')">质能方程: E = mc^2</div>
                        <div class="example-formula" onclick="setExample('circle')">圆的面积: A = πr^2</div>
                    </div>
                    
                    <label for="formulaInput">输入公式：</label>
                    <textarea id="formulaInput" placeholder="输入文本公式，例如: x = (-b ± sqrt(b^2 - 4ac)) / (2a)"></textarea>
                    
                    <div>
                        <button class="button" onclick="testConvert('GET')">使用GET方法测试</button>
                        <button class="button post" onclick="testConvert('POST')">使用POST方法测试</button>
                        <button class="button secondary" onclick="clearResult()">清空结果</button>
                    </div>
                    
                    <div class="response">
                        <h4>响应结果：</h4>
                        <div id="convertResult">
                            点击上方按钮测试...
                        </div>
                        <div id="latexPreview" style="margin-top: 15px; display: none;">
                            <h4>LaTeX预览：</h4>
                            <div id="latexRendering"></div>
                        </div>
                    </div>
                </div>
                
                <div class="demo-section">
                    <h3>健康检查</h3>
                    <button class="button" onclick="testHealth()">测试健康检查</button>
                    <div class="response">
                        <div id="healthResult">点击按钮测试...</div>
                    </div>
                </div>
            </div>
            
            <!-- 文档标签页 -->
            <div id="docs-tab" class="tab-content">
                <h2>API文档</h2>
                
                <div class="endpoint">
                    <span class="method get">GET</span><span class="method post">POST</span> 
                    <span class="url">/api/v1/formula/convert</span>
                    <p><strong>公式转换接口</strong></p>
                    <p>将文本公式转换为LaTeX格式。</p>
                    
                    <h4>GET方法参数：</h4>
                    <pre>?text=公式文本</pre>
                    
                    <h4>POST方法请求体：</h4>
                    <pre>{"text": "公式文本"}</pre>
                    
                    <h4>响应示例：</h4>
                    <pre>{
    "data": {
        "original": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
        "latex": "x = \\frac{-b \\pm \\sqrt{b^{2} - 4ac}}{2a}",
        "formatted": "$x = \\frac{-b \\pm \\sqrt{b^{2} - 4ac}}{2a}$",
        "confidence": 0.95,
        "complexity": 0.45,
        "is_valid": true,
        "validation_msg": "LaTeX语法有效"
    },
    "msg": "公式转换成功",
    "status_code": 200
}</pre>
                </div>
                
                <div class="endpoint">
                    <span class="method get">GET</span><span class="method post">POST</span> 
                    <span class="url">/api/v1/formula/validate</span>
                    <p><strong>公式验证接口</strong></p>
                    <p>验证公式或LaTeX语法的有效性。</p>
                    
                    <h4>参数：</h4>
                    <pre>text=要验证的文本
type=text 或 latex (默认: latex)</pre>
                </div>
                
                <div class="endpoint">
                    <span class="method post">POST</span> 
                    <span class="url">/api/v1/formula/batch_convert</span>
                    <p><strong>批量转换接口</strong></p>
                    <p>批量转换多个公式。</p>
                    
                    <h4>请求体：</h4>
                    <pre>{"formulas": ["公式1", "公式2", ...]}</pre>
                </div>
                
                <div class="endpoint">
                    <span class="method get">GET</span> 
                    <span class="url">/api/v1/formula/health</span>
                    <p><strong>健康检查接口</strong></p>
                    <p>检查服务运行状态。</p>
                </div>
            </div>
            
            <!-- 示例标签页 -->
            <div id="examples-tab" class="tab-content">
                <h2>示例公式</h2>
                
                <div class="example-formulas">
                    <h3>常用数学公式</h3>
                    <div class="example-formula" onclick="setExample('quadratic')">
                        <strong>二次方程求根公式：</strong><br>
                        输入: x = (-b ± sqrt(b^2 - 4ac)) / (2a)<br>
                        输出: x = \frac{-b \pm \sqrt{b^{2} - 4ac}}{2a}
                    </div>
                    
                    <div class="example-formula" onclick="setExample('pythagorean')">
                        <strong>勾股定理：</strong><br>
                        输入: a^2 + b^2 = c^2<br>
                        输出: a^{2} + b^{2} = c^{2}
                    </div>
                    
                    <div class="example-formula" onclick="setExample('emc2')">
                        <strong>质能方程：</strong><br>
                        输入: E = mc^2<br>
                        输出: E = mc^{2}
                    </div>
                    
                    <div class="example-formula" onclick="setExample('newton')">
                        <strong>牛顿第二定律：</strong><br>
                        输入: F = ma<br>
                        输出: F = ma
                    </div>
                    
                    <div class="example-formula" onclick="setExample('ohm')">
                        <strong>欧姆定律：</strong><br>
                        输入: V = IR<br>
                        输出: V = IR
                    </div>
                    
                    <div class="example-formula" onclick="setExample('circle')">
                        <strong>圆的面积：</strong><br>
                        输入: A = πr^2<br>
                        输出: A = \pi r^{2}
                    </div>
                    
                    <div class="example-formula" onclick="setExample('sphere')">
                        <strong>球的体积：</strong><br>
                        输入: V = (4/3)πr^3<br>
                        输出: V = \frac{4}{3}\pi r^{3}
                    </div>
                    
                    <div class="example-formula" onclick="setExample('euler')">
                        <strong>欧拉公式：</strong><br>
                        输入: e^(iπ) + 1 = 0<br>
                        输出: e^{i\pi} + 1 = 0
                    </div>
                    
                    <div class="example-formula" onclick="setExample('normal')">
                        <strong>正态分布：</strong><br>
                        输入: f(x) = 1/(sqrt(2π)) * e^(-x^2/2)<br>
                        输出: f(x) = \frac{1}{\sqrt{2\pi}} e^{-\frac{x^{2}}{2}}
                    </div>
                    
                    <div class="example-formula" onclick="setExample('trig')">
                        <strong>三角函数恒等式：</strong><br>
                        输入: sin(x)^2 + cos(x)^2 = 1<br>
                        输出: \sin^{2}x + \cos^{2}x = 1
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // 示例公式
            const examples = {
                quadratic: "x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
                pythagorean: "a^2 + b^2 = c^2",
                emc2: "E = mc^2",
                newton: "F = ma",
                ohm: "V = IR",
                circle: "A = πr^2",
                sphere: "V = (4/3)πr^3",
                euler: "e^(iπ) + 1 = 0",
                normal: "f(x) = 1/(sqrt(2π)) * e^(-x^2/2)",
                trig: "sin(x)^2 + cos(x)^2 = 1"
            };
            
            // 标签页切换
            function switchTab(tabName) {
                // 移除所有标签页的active类
                document.querySelectorAll('.tab-button').forEach(button => {
                    button.classList.remove('active');
                });
                
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // 激活选中的标签页
                document.querySelector(`button[onclick="switchTab('${tabName}')"]`).classList.add('active');
                document.getElementById(`${tabName}-tab`).classList.add('active');
            }
            
            // 设置示例公式
            function setExample(type) {
                document.getElementById('formulaInput').value = examples[type];
            }
            
            // 测试公式转换
            async function testConvert(method) {
                const formulaInput = document.getElementById('formulaInput').value.trim();
                const resultDiv = document.getElementById('convertResult');
                const previewDiv = document.getElementById('latexPreview');
                const renderingDiv = document.getElementById('latexRendering');
                
                if (!formulaInput) {
                    resultDiv.innerHTML = '<span class="error">请输入公式</span>';
                    return;
                }
                
                resultDiv.innerHTML = '正在转换...';
                previewDiv.style.display = 'none';
                
                try {
                    let response;
                    
                    if (method === 'GET') {
                        // GET方法
                        const encodedText = encodeURIComponent(formulaInput);
                        response = await fetch(`/api/v1/formula/convert?text=${encodedText}`);
                    } else {
                        // POST方法
                        response = await fetch('/api/v1/formula/convert', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({text: formulaInput})
                        });
                    }
                    
                    const data = await response.json();
                    
                    // 格式化显示
                    let resultHtml = '';
                    
                    if (data.status_code === 200) {
                        resultHtml = `
                            <p><strong>方法:</strong> ${method}</p>
                            <p><strong>原始公式:</strong> ${data.data.original}</p>
                            <p><strong>LaTeX:</strong> ${data.data.latex}</p>
                            <p><strong>置信度:</strong> ${data.data.confidence}</p>
                            <p><strong>复杂度:</strong> ${data.data.complexity}</p>
                            <p><strong>有效性:</strong> ${data.data.is_valid ? '有效' : '无效'}</p>
                            ${!data.data.is_valid ? `<p><strong>验证信息:</strong> ${data.data.validation_msg}</p>` : ''}
                        `;
                        
                        resultDiv.innerHTML = resultHtml;
                        
                        // 显示预览
                        if (data.data.latex && data.data.latex !== '\\text{' + data.data.original + '}') {
                            previewDiv.style.display = 'block';
                            renderingDiv.innerHTML = `$$${data.data.latex}$$`;
                            
                            // 尝试使用MathJax渲染
                            if (window.MathJax) {
                                MathJax.typesetPromise([renderingDiv]).catch(err => {
                                    console.log('MathJax渲染错误:', err);
                                });
                            }
                        }
                    } else {
                        resultDiv.innerHTML = `<span class="error">错误: ${data.msg}</span>`;
                    }
                    
                } catch (error) {
                    resultDiv.innerHTML = `<span class="error">请求失败: ${error.message}</span>`;
                }
            }
            
            // 测试健康检查
            async function testHealth() {
                const resultDiv = document.getElementById('healthResult');
                resultDiv.innerHTML = '正在检查...';
                
                try {
                    const response = await fetch('/api/v1/formula/health');
                    const data = await response.json();
                    
                    if (data.status_code === 200) {
                        let html = `<p><strong>状态:</strong> ${data.data.status}</p>`;
                        html += `<p><strong>服务:</strong> ${data.data.service}</p>`;
                        html += `<p><strong>版本:</strong> ${data.data.version}</p>`;
                        
                        html += '<h4>可用端点:</h4><ul>';
                        for (const [name, endpoint] of Object.entries(data.data.endpoints)) {
                            html += `<li><strong>${name}:</strong> ${endpoint.url} (${endpoint.methods.join(', ')})</li>`;
                        }
                        html += '</ul>';
                        
                        resultDiv.innerHTML = html;
                    } else {
                        resultDiv.innerHTML = `<span class="error">服务异常: ${data.msg}</span>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<span class="error">请求失败: ${error.message}</span>`;
                }
            }
            
            // 清空结果
            function clearResult() {
                document.getElementById('convertResult').innerHTML = '点击上方按钮测试...';
                document.getElementById('latexPreview').style.display = 'none';
                document.getElementById('formulaInput').value = '';
            }
            
            // 页面加载时初始化
            window.onload = function() {
                // 设置默认示例
                setExample('quadratic');
            };
        </script>
        
        <!-- MathJax用于LaTeX渲染 -->
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    </body>
    </html>
    '''


# ============ 错误处理器 ============
@app.errorhandler(404)
def not_found_error(error):
    """处理404错误"""
    return jsonify(create_response(
        data=None,
        status_code=404,
        msg="请求的资源不存在"
    )), 404


@app.errorhandler(405)
def method_not_allowed_error(error):
    """处理405错误"""
    return jsonify(create_response(
        data=None,
        status_code=405,
        msg="请求方法不允许"
    )), 405


@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify(create_response(
        data=None,
        status_code=500,
        msg="服务器内部错误"
    )), 500


# ============ 启动应用 ============
if __name__ == '__main__':
    print("=" * 60)
    print("增强公式转换API服务")
    print(f"版本: 2.0.0")
    print(f"调试模式: {app.config.get('DEBUG')}")
    print("=" * 60)
    print("可用的API端点:")
    print("  GET/POST /api/v1/formula/convert    - 公式转换")
    print("  GET/POST /api/v1/formula/validate   - 公式验证")
    print("  POST     /api/v1/formula/batch_convert - 批量转换")
    print("  GET      /api/v1/formula/health     - 健康检查")
    print("=" * 60)
    print("服务启动中...")
    print("访问 http://127.0.0.1:5000 进行测试")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(
        host='127.0.0.1',  # 只监听本地
        port=5000,
        debug=app.config.get('DEBUG')
    )