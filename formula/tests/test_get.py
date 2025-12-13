# test_get_app.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/formula/convert', methods=['GET'])
def convert_formula_get():
    """GET方法测试接口"""
    return jsonify({
        "data": {
            "original": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
            "latex": "x = \\frac{-b \\pm \\sqrt{b^{2} - 4ac}}{2a}",
            "confidence": 0.95
        },
        "status_code": 200,
        "msg": "这是一个测试响应，请使用POST方法发送请求"
    })

@app.route('/api/v1/formula/health', methods=['GET'])
def health_check():
    return jsonify({
        "data": {"status": "healthy"},
        "status_code": 200,
        "msg": "服务运行正常"
    })

@app.route('/')
def index():
    return '''
    <h1>✅ 服务正常运行！</h1>
    <p>测试链接：</p>
    <ul>
        <li><a href="/api/v1/formula/health">健康检查</a></li>
        <li><a href="/api/v1/formula/convert">公式转换（GET测试）</a></li>
    </ul>
    '''

if __name__ == '__main__':
    print("启动测试应用...")
    app.run(debug=True, port=5000)