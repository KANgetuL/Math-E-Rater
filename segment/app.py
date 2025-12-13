from flask import Flask, request, jsonify
from ultralytics import YOLO
import os

app = Flask(__name__)
# 加载训练好的模型
model = YOLO('runs/train/homework_question/weights/best.pt')
# 允许上传的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


# 检查文件格式
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 检测接口：接收上传的图片，返回题目坐标
@app.route('/detect_questions', methods=['POST'])
def detect_questions():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if file and allowed_file(file.filename):
        # 保存上传的图片
        img_path = 'uploaded_img.jpg'
        file.save(img_path)

        # 执行检测
        results = model(img_path)
        questions = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = round(float(box.conf[0]), 2)
            questions.append({
                'coordinates': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                'confidence': conf
            })

        # 返回检测结果（JSON格式）
        return jsonify({
            'status': 'success',
            'questions': questions
        })
    else:
        return jsonify({'error': '不支持的文件格式'}), 400


if __name__ == '__main__':
    app.run(debug=True)  # 启动服务，地址：http://127.0.0.1:5000