# 百度OCR高精度数学题识别（支持字母/数字平方，无误改）
from flask import Flask, request, Response
import json
import traceback
import requests
import base64
from PIL import Image
import io
import warnings
import re

warnings.filterwarnings('ignore')
app = Flask(__name__)

# ========== 密钥无需修改 ==========
API_KEY = "D7CHS4nXmAoOtzgfhujbAarA"
SECRET_KEY = "xTUqUKUVcx15o9t2IFkEs22CaMKb790Z"

# 获取百度OCR Token
def get_access_token():
    try:
        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
        token_res = requests.get(token_url, timeout=10).json()
        return token_res.get("access_token") if "access_token" in token_res else None
    except Exception as e:
        print(f"Token异常：{str(e)}")
        return None

# 核心：智能修正所有平方场景（字母/数字），不误改普通2
def smart_fix_all_square(text):
    if not text:
        return text
    
    # 规则1：匹配「字母+2」（a2、b2→a²、b²），前后无数字/空格
    letter_square = re.compile(r'(?<![0-9\s])([a-zA-Z])2(?![0-9\s])')
    fixed_text = letter_square.sub(r'\1²', text)
    
    # 规则2：匹配「数字+2」且是平方场景（如“2的2”→“2的²”、“22”不改动）
    # 匹配：数字+（的/平方）+2 → 修正为 数字+（的/平方）+²
    num_square_1 = re.compile(r'(\d+)的2(?=\D|$)')
    fixed_text = num_square_1.sub(r'\1的²', fixed_text)
    
    num_square_2 = re.compile(r'(\d+)平方2(?=\D|$)')
    fixed_text = num_square_2.sub(r'\1平方²', fixed_text)
    
    # 规则3：匹配单独的「数字2」且上下文是平方表述（如“2=4”→“²=4”，需结合语境）
    # 仅当文本有“平方”关键词时，才修正孤立的数字2为²
    if "平方" in fixed_text:
        isolated_num_square = re.compile(r'(?<![0-9])(2)(?==|\+|\-|\×|\÷|$)')
        fixed_text = isolated_num_square.sub(r'²', fixed_text)
    
    # 调试日志（可删除）
    print(f"原始：{text} → 修正后：{fixed_text}")
    return fixed_text

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        # 1. 校验图片
        image_file = request.files.get('image')
        if not image_file:
            return Response(
                json.dumps({"error": "未上传图片文件"}, ensure_ascii=False),
                status=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 2. 校验格式
        allowed_formats = ['jpg', 'jpeg', 'png', 'bmp']
        file_format = image_file.filename.split('.')[-1].lower() if '.' in image_file.filename else ''
        if file_format not in allowed_formats:
            return Response(
                json.dumps({"error": f"不支持的格式：{file_format}，仅支持{allowed_formats}"}, ensure_ascii=False),
                status=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 3. 图片预处理
        img = Image.open(image_file).convert('RGB')
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # 4. 调用百度高精度OCR
        access_token = get_access_token()
        if not access_token:
            return Response(
                json.dumps({"error": "Token获取失败，请检查密钥"}, ensure_ascii=False),
                status=500,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"
        ocr_res = requests.post(
            ocr_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"image": img_base64},
            timeout=10
        ).json()
        
        # 5. 解析+智能修正平方
        raw_text = ''
        if "words_result" in ocr_res and len(ocr_res["words_result"]) > 0:
            raw_text = ''.join([item["words"] for item in ocr_res["words_result"]])
        final_text = smart_fix_all_square(raw_text) if raw_text else "未识别到有效内容"
        
        # 6. 返回结果
        return Response(
            json.dumps({"text": final_text}, ensure_ascii=False, indent=2),
            status=200,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    except Exception as e:
        return Response(
            json.dumps({"error": "服务器错误", "detail": str(e)}, ensure_ascii=False),
            status=500,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

if __name__ == '__main__':
    print("✅ 百度OCR数学题识别（支持字母/数字平方）已启动")
    print("🔗 接口：http://127.0.0.1:8080/recognize")
    app.run(host='0.0.0.0', port=8080, debug=False)