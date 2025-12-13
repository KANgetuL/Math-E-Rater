from ultralytics import YOLO

# 1. 加载YOLOv8n模型（n=轻量化，适合小白训练快，效果也够）
model = YOLO('yolov8n.pt')  # yolov8n.pt是预训练权重，会自动下载

# 2. 开始训练
results = model.train(
    data=r'C:\Users\28620\Desktop\dataset_homework\dataset.yaml',  # 替换成你的dataset.yaml绝对路径
    epochs=30,  # 训练轮数（零基础先训30轮，不够再加）
    batch=4,    # 批次大小（电脑内存小就改2，大可以改8）
    imgsz=640,  # 训练图片分辨率（固定640即可）
    device='cpu',  # 没有GPU就用cpu，有GPU写0（比如NVIDIA显卡）
    patience=5,    # 5轮没提升就停止，避免无效训练
    save=True,     # 保存训练好的模型
    project='runs/train',  # 训练结果保存路径
    name='homework_question'  # 模型名称
)

# 训练完成后，模型会保存在 runs/train/homework_question/weights/best.pt
print("训练完成！最佳模型路径：", results.save_dir + "/weights/best.pt")