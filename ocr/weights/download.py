import os
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

save_dir = 'weights/chinese_tr_ocr'
os.makedirs(save_dir, exist_ok=True)

# 用官方英文手写底模（已含中文预训练）
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')

processor.save_pretrained(save_dir)
model.save_pretrained(save_dir)

print('底模已保存到', save_dir)