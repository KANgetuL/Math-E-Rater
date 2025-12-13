\1.   下载Anaconda

\2.   打开Anaconda Prompt（开始菜单搜）执行

conda create -n homework_detect python=3.8 -y

conda activate homework_detect

\3.   执行

pip install ultralytics

pip install opencv-python pillow matplotlib

pip install labelImg

4.找 10-30 张不同类型的作业图片（手写 / 打印、语文 / 数学都可以，数量越多模型越准，零基础先从 10 张起步）；

图片格式：JPG/PNG，

5.在电脑里新建一个文件夹（比如dataset_homework）(已经建好了，在压缩包里)，按以下结构整理：

dataset_homework/

├─ images/     # 存放所有图片

│ ├─ train/    # 训练集（80%的图片，比如8张）

│ └─ val/     # 验证集（20%的图片，比如2张）

└─ labels/     # 存放标注文件（自动生成）

  ├─ train/    # 训练集图片对应的标注文件

  └─ val/     # 验证集图片对应的标注文件

把收集的图片按 8:2 的比例分别放到images/train和images/val里；

示例：如果有 10 张图，8 张放 train，2 张放 val。

6.执行

LabelImg

用labeling标注题目区域

7.在dataset_homework文件夹里新建一个dataset.yaml文件(已经建好了，在压缩包里)

8.在电脑里新建一个`train.py`文件（在压缩包里）

·    打开 Anaconda Prompt，激活环境：conda activate homework_detect；

·    切换到train.py所在目录（比如桌面：cd Desktop）；

·    执行训练：python train.py。

#### 训练过程说明：

·    第一次运行会自动下载 YOLOv8n 预训练权重（几百 MB，耐心等）；

·    训练中会显示损失值（loss），损失值逐渐降低就是正常的；

·    训练完成后，在`runs/train/homework_question/weights/`里会生成`best.pt`（最佳模型）和`last.pt`（最后一轮模型），后续用`best.pt`。

9.新建detect.py文件（在压缩包里）

·    确保 Anaconda 环境激活：`conda activate homework_detect`；

·    切换到`detect.py`所在目录：`cd Desktop`；

·    执行：`python detect.py`

#### 输出结果说明：

·    控制台会打印每道题的坐标（比如`左上角(50,100)，右下角(750,250)`），这就是你需要的 “定位结果”；

·    会弹出图片窗口，显示画了蓝色框的题目区域；

·    自动裁剪的题目图片会保存到`cropped_questions/`文件夹。

10.执行pip install flask

11.新建app.py（在压缩包里）

运行：python app.py，服务启动在http://127.0.0.1:5000

12.打开一个新的Anaconda Prompt（菜单搜）

执行curl -X POST -F "file=@你的图片路径" http://127.0.0.1:5000/detect_questions

最后返回题目区域坐标（以json数组形式）