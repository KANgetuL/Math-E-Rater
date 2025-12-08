#### 前提条件
- 电脑已安装 Python 3.7+（若未安装，需先从官网下载：https://www.python.org/downloads/，安装时勾选“Add Python to PATH”）；
- 电脑能联网（百度OCR接口需要联网调用）；
- 已完成百度智能云实名认证（若未完成，需用自己的百度账号登录百度智能云，按提示完成实名认证）。

#### 具体操作（共5步，10分钟搞定）
1. **安装依赖包**  
   打开终端（Windows按 `Win+R` 输入 `cmd` 打开命令提示符，macOS打开「终端」），执行以下命令安装所需依赖（复制粘贴直接运行）：
   ```bash
   pip install flask requests pillow numpy
   ```
   - 若提示 `pip不是内部命令`：说明安装Python时未勾选“Add Python to PATH”，需重新安装Python并勾选该选项。

2. **替换百度密钥**
   可按以下步骤替换自己的密钥：

   - 登录百度智能云 → 搜索「文字识别」→ 进入产品页 → 实名认证 → 「应用列表」→ 「创建应用」（填写名称/描述，勾选文字识别服务）；

   - 打开 `math_ocr/serve.py` 文件，找到以下两行，替换为自己的 `API Key` 和 `Secret Key`：
     ```python
     API_KEY = "D7CHS4nXmAoOtzgfhujbAarA"  # 替换为组长自己的API Key
     SECRET_KEY = "xTUqUKUVcx15o9t2IFkEs22CaMKb790Z"  # 替换为组长自己的Secret Key
     ```

3. **启动识别服务**  
   终端切换到 `math_ocr` 文件夹路径

   然后执行命令启动服务（后台运行，避免误关闭）：
   ```bash
   # Windows系统
   start python serve.py
   # macOS/Linux系统
   python3 serve.py &
   ```
   - 启动成功后，会弹出新终端窗口，显示：百度OCR数学题识别（支持字母/数字平方）已启动`，且接口地址为 `http://127.0.0.1:8080/recognize`。

4. **测试接口连通性（验证是否能正常运行）**  
   保持服务窗口开启，在原终端执行测试命令（替换为文件夹内任意图片路径，示例用 `test.png`）：
   ```bash
   # Windows系统
   python -c "import requests; img_path='C:/Users/用户名/Desktop/math_ocr/weights/data_synth/images/test.png'; res=requests.post('http://127.0.0.1:8080/recognize', files={'image': open(img_path, 'rb')}); print('识别结果：', res.json())"
   # macOS/Linux系统
   python3 -c "import requests; img_path='/Users/用户名/Desktop/math_ocr/weights/data_synth/images/test.png'; res=requests.post('http://127.0.0.1:8080/recognize', files={'image': open(img_path, 'rb')}); print('识别结果：', res.json())"
   ```
   - 正常输出示例：`识别结果： {'text': '如果a²=a+1,b²=b+1,且a≠b,那么a²+b²='}`，说明接口已正常运行。


### 三、关键事项，保障稳定运行
1. **服务运行期间**：启动服务的终端窗口不能关闭（关闭则服务停止），若不小心关闭，重新执行步骤4的启动命令即可。
2. **图片路径要求**：调用接口时，`img_path` 必须是电脑内真实存在的图片路径（支持jpg/jpeg/png/bmp），路径无中文/空格。
3. **接口调用方式**：除了终端测试，也可通过其他程序（如Java、Python、前端）调用接口，调用格式为：
   - 请求方式：POST
   - 接口地址：`http://127.0.0.1:8080/recognize`
   - 请求体：form-data 格式，key为 `image`，value为图片文件流。
4. **常见问题排查**：
   - 报 `FileNotFoundError`：图片路径错误，核对路径是否正确；
   - 报 `Token获取失败`：密钥错误或网络不通，检查密钥和网络；
   - 识别结果乱码：图片模糊/潦草，优化图片清晰度或开启手写体优化（见下方补充）；
   - 端口被占用（报错 `Address already in use`）：打开 `serve.py`，把 `port=8080` 改为其他端口（如 `port=8081`），重启服务。
