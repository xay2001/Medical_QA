from PIL import Image, ImageDraw, ImageFont
import os
import platform

# 创建图像
img = Image.new('RGB', (600, 400), color='white')
draw = ImageDraw.Draw(img)

# 医疗报告内容
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

# 自动选择支持中文的字体路径
def get_font_path():
    system = platform.system()
    if system == 'Darwin':  # macOS
        return '/System/Library/Fonts/STHeiti Medium.ttc'
    elif system == 'Windows':
        return 'C:/Windows/Fonts/simfang.ttf'
    elif system == 'Linux':
        return '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'  # 中文字体（如已安装）
    else:
        return None

# 加载字体
font_path = get_font_path()
try:
    font = ImageFont.truetype(font_path, 16)
except Exception as e:
    print("字体加载失败，使用默认字体：", e)
    font = ImageFont.load_default()

# 自动换行处理
def draw_multiline_text(draw, text, position, font, line_height, max_width):
    x, y = position
    for line in text.split('\n'):
        words = ''
        for char in line:
            if draw.textlength(words + char, font=font) < max_width:
                words += char
            else:
                draw.text((x, y), words, fill='black', font=font)
                y += line_height
                words = char
        draw.text((x, y), words, fill='black', font=font)
        y += line_height

# 画出文字
draw_multiline_text(draw, text, position=(20, 20), font=font, line_height=22, max_width=560)

# 保存图像
os.makedirs('test_images', exist_ok=True)
img.save('test_images/medical_report.png')
print("✅ 医疗报告图像已生成：test_images/medical_report.png")