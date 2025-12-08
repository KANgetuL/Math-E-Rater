FROM pytorch/pytorch:2.1.0-cuda11.8-runtime-ubuntu22.04
RUN apt update && apt install -y libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
CMD ["python", "serve.py"]