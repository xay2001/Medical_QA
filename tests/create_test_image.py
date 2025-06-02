from PIL import Image, ImageDraw, ImageFont
import os

# 创建白底图像（高度调大）
img = Image.new('RGB', (600, 900), color='white')
draw = ImageDraw.Draw(img)

# 中文医疗报告文本
text = """医疗检查报告

患者姓名：李明
性别：男  年龄：45岁

主要症状：
头痛、发热、咳嗽、乏力

检查项目：
血常规、尿常规、胸部X光
血压：140/90mmHg (高血压)
体温：38.2℃
心率：85次/分

诊断结果：
上呼吸道感染
高血压病

治疗方案：
阿莫西林 500mg 口服 3次/日
布洛芬 400mg 口服 疼痛时
降压药：氨氯地平 5mg 1次/日

注意事项：
多休息，多饮水
定期监测血压
如症状加重请及时就医"""

# 加载 STHeiti Medium 字体
font_path = '/System/Library/Fonts/STHeiti Medium.ttc'
font = ImageFont.truetype(font_path, 18)

# 自动换行函数
def draw_multiline(draw, text, font, max_width, start_pos, line_spacing=6):
    x, y = start_pos
    for line in text.split('\n'):
        current = ''
        for char in line:
            if draw.textlength(current + char, font=font) < max_width:
                current += char
            else:
                draw.text((x, y), current, font=font, fill='black')
                y += font.size + line_spacing
                current = char
        draw.text((x, y), current, font=font, fill='black')
        y += font.size + line_spacing

# 绘制文字
draw_multiline(draw, text, font, max_width=560, start_pos=(20, 20))

# 保存图像
os.makedirs('test_images', exist_ok=True)
img.save('test_images/medical_report.png')
print("✅ 中文图像已生成：test_images/medical_report.png")