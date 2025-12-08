import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SYNTH_OUT = 'data_synth/images'
LABEL_FILE = 'data_synth/labels.txt'
FONTS_DIR = 'data_synth/fonts'
os.makedirs(SYNTH_OUT, exist_ok=True)

TEMPLATES = [
    "计算：{a}+{b}=？",
    "如图，已知△ABC中，AB={c}cm，∠A={d}°，求AC的长。",
    "解方程：{e}x+{f}=0",
    "一个圆的半径为{r}cm，面积是多少？（π取3.14）",
    "把{g}化成最简分数。",
] * 10000   # 扩到 500 条模板

def rand_text():
    t = random.choice(TEMPLATES)
    return t.format(a=random.randint(1,99), b=random.randint(1,99),
                    c=random.randint(1,20), d=random.randint(10,90),
                    e=random.randint(1,9), f=random.randint(1,20),
                    r=random.randint(1,10), g=random.randint(10,99))

def generate_one(idx):
    text = rand_text()
    font_size = random.randint(18, 40)
    font_path = random.choice([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf','.ttc'))])
    font = ImageFont.truetype(os.path.join(FONTS_DIR, font_path), font_size)
    w, h = font.getbbox(text)[2:4]  # Pillow 10+ 新接口
    canvas = Image.new('RGB', (w+40, h+40), (255,255,255))
    draw = ImageDraw.Draw(canvas)
    draw.text((20,20), text, fill=(0,0,0), font=font)
    if random.random()<0.4:
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5,1.5)))
    if random.random()<0.5:
        canvas = canvas.rotate(random.uniform(-15,15), fillcolor=(255,255,255))
    canvas.save(f'{SYNTH_OUT}/{idx:06d}.jpg', quality=95)
    with open(LABEL_FILE, 'a', encoding='utf8') as f:
        f.write(f'{idx:06d}.jpg\t{text}\n')

if __name__ == '__main__':
    open(LABEL_FILE, 'w').close()
    for i in range(50000):
        generate_one(i)
    print('50000 张图生成完毕')