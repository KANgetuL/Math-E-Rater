from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt

# 1. 加载训练好的模型（替换成你的best.pt路径）
model = YOLO('runs/train/homework_question/weights/best.pt')

# 2. 加载要检测的作业图片（替换成你的图片路径，比如测试集的图片）
img_path = r'C:\Users\28620\Desktop\dataset_homework\images\val\8a4f13bf993e503a07bc450c1fe6bc7c.jpg'
img = cv2.imread(img_path)
# 转换颜色空间（OpenCV默认BGR，Matplotlib显示需要RGB）
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# 3. 执行检测
results = model(img_path)  # results里包含所有检测到的题目区域

# 4. 解析检测结果并可视化
for result in results:
    # 遍历每一个检测到的目标（题目）
    for box in result.boxes:
        # 获取题目区域的坐标（xyxy：左上角x,y，右下角x,y）
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        # 获取置信度（模型对这个框是题目的置信度，越高越准）
        conf = round(float(box.conf[0]), 2)
        # 获取类别名（这里是question）
        cls = result.names[int(box.cls[0])]

        # 在图片上画框+标注信息
        cv2.rectangle(img_rgb, (x1, y1), (x2, y2), (255, 0, 0), 2)  # 蓝色框
        cv2.putText(img_rgb, f'{cls} {conf}', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # 打印每道题的坐标（供后续模块使用）
        print(f"题目区域：左上角({x1},{y1})，右下角({x2},{y2})，置信度：{conf}")

# 5. 显示检测后的图片
plt.figure(figsize=(12, 8))
plt.imshow(img_rgb)
plt.axis('off')
plt.show()

# 6. 可选：裁剪每道题的区域并保存
save_dir = 'cropped_questions/'
import os

os.makedirs(save_dir, exist_ok=True)
for i, box in enumerate(results[0].boxes):
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    cropped = img[y1:y2, x1:x2]  # 裁剪题目区域
    cv2.imwrite(f'{save_dir}/question_{i + 1}.jpg', cropped)
print(f"裁剪的题目已保存到：{save_dir}")