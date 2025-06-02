import os
import sys
import cv2
import numpy as np
from PIL import Image
import json
from datetime import datetime
import base64
from io import BytesIO

# 添加Django环境
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from qa_system.models import ImageRecognitionResult
from data_processing.text_processor import TextProcessor

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("PaddleOCR未安装，请运行: pip install paddleocr")
    PaddleOCR = None

class MedicalOCR:
    def __init__(self):
        """初始化医学OCR识别器"""
        if PaddleOCR is None:
            raise ImportError("PaddleOCR未安装")
        
        # 初始化PaddleOCR，支持中英文（使用新的参数名）
        self.ocr = PaddleOCR(use_textline_orientation=True, lang='ch')
        self.text_processor = TextProcessor()
        
    def preprocess_image(self, image_path):
        """预处理图像以提高OCR效果"""
        try:
            # 读取图像
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
            else:
                # 如果是文件对象，先保存为临时文件
                image = cv2.imdecode(np.frombuffer(image_path.read(), np.uint8), cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("无法读取图像文件")
            
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 降噪
            denoised = cv2.medianBlur(gray, 3)
            
            # 自适应阈值化
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 形态学操作去除噪点
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            print(f"图像预处理错误: {e}")
            return None
    
    def extract_text_from_image(self, image_path):
        """从图像中提取文字"""
        try:
            # 预处理图像
            processed_image = self.preprocess_image(image_path)
            
            # 直接使用原图像，因为PaddleOCR 3.0有更好的预处理
            if isinstance(image_path, str):
                result = self.ocr.ocr(image_path)
            else:
                image_path.seek(0)
                image_array = np.frombuffer(image_path.read(), np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                result = self.ocr.ocr(image)
            
            # 提取文字内容 - 适配PaddleOCR 3.0新格式
            extracted_text = ""
            detection_results = []
            
            if result and len(result) > 0:
                ocr_result = result[0]  # 获取第一页的结果
                
                # 检查新的数据结构
                if isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
                    rec_texts = ocr_result.get('rec_texts', [])
                    rec_scores = ocr_result.get('rec_scores', [])
                    rec_polys = ocr_result.get('rec_polys', [])
                    
                    for i, text in enumerate(rec_texts):
                        if i < len(rec_scores):
                            confidence = rec_scores[i]
                            # 只保留置信度较高的文字
                            if confidence > 0.5:
                                extracted_text += text + " "
                                bbox = rec_polys[i] if i < len(rec_polys) else []
                                detection_results.append({
                                    'text': text,
                                    'confidence': confidence,
                                    'bbox': bbox.tolist() if hasattr(bbox, 'tolist') else bbox
                                })
                else:
                    # 兼容旧格式（如果还有的话）
                    if isinstance(ocr_result, list):
                        for line in ocr_result:
                            if line and len(line) >= 2:
                                bbox = line[0]
                                text_info = line[1]
                                
                                if text_info and len(text_info) >= 2:
                                    text = text_info[0]
                                    confidence = text_info[1]
                                    
                                    if confidence > 0.5:
                                        extracted_text += text + " "
                                        detection_results.append({
                                            'text': text,
                                            'confidence': confidence,
                                            'bbox': bbox
                                        })
            
            return {
                'text': extracted_text.strip(),
                'details': detection_results,
                'total_detections': len(detection_results)
            }
            
        except Exception as e:
            print(f"OCR识别错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                'text': "",
                'details': [],
                'total_detections': 0,
                'error': str(e)
            }
    
    def analyze_medical_text(self, extracted_text):
        """分析识别出的医疗文本"""
        if not extracted_text or not extracted_text.strip():
            return {
                'analysis': '未能识别出有效文本',
                'keywords': [],
                'medical_entities': [],
                'suggestions': []
            }
        
        try:
            # 使用文本处理器进行分析
            words = self.text_processor.segment_text(extracted_text)
            keywords = self.text_processor.extract_keywords(extracted_text, num_keywords=10)
            
            # 简单的医学实体识别
            medical_entities = self.extract_medical_entities(extracted_text)
            
            # 生成建议
            suggestions = self.generate_suggestions(extracted_text, medical_entities)
            
            return {
                'analysis': f'成功识别出 {len(words)} 个词语',
                'keywords': keywords,
                'medical_entities': medical_entities,
                'suggestions': suggestions
            }
            
        except Exception as e:
            print(f"文本分析错误: {e}")
            return {
                'analysis': f'文本分析出错: {str(e)}',
                'keywords': [],
                'medical_entities': [],
                'suggestions': []
            }
    
    def extract_medical_entities(self, text):
        """提取医学实体（简单实现）"""
        medical_entities = []
        
        # 常见医学术语
        medical_terms = {
            '疾病': ['感冒', '发烧', '咳嗽', '头痛', '胸痛', '腹痛', '高血压', '糖尿病', '心脏病', '肺炎'],
            '症状': ['疼痛', '发热', '恶心', '呕吐', '腹泻', '便秘', '失眠', '头晕', '乏力', '食欲不振'],
            '药物': ['阿司匹林', '青霉素', '布洛芬', '对乙酰氨基酚', '甲硝唑', '氨氯地平', '二甲双胍'],
            '检查': ['血常规', 'X光', 'CT', 'MRI', 'B超', '心电图', '血压', '血糖', '尿常规'],
            '治疗': ['手术', '化疗', '放疗', '物理治疗', '针灸', '按摩', '康复训练']
        }
        
        for category, terms in medical_terms.items():
            found_terms = []
            for term in terms:
                if term in text:
                    found_terms.append(term)
            
            if found_terms:
                medical_entities.append({
                    'category': category,
                    'entities': found_terms
                })
        
        return medical_entities
    
    def generate_suggestions(self, text, medical_entities):
        """根据识别的内容生成建议"""
        suggestions = []
        
        # 基于识别的医学实体生成建议
        for entity_group in medical_entities:
            category = entity_group['category']
            entities = entity_group['entities']
            
            if category == '疾病' and entities:
                suggestions.append(f"检测到疾病相关内容：{', '.join(entities)}。建议咨询专业医生进行诊断。")
            
            elif category == '症状' and entities:
                suggestions.append(f"检测到症状：{', '.join(entities)}。建议记录症状持续时间和严重程度。")
            
            elif category == '药物' and entities:
                suggestions.append(f"检测到药物：{', '.join(entities)}。请遵医嘱使用，注意用法用量。")
            
            elif category == '检查' and entities:
                suggestions.append(f"检测到检查项目：{', '.join(entities)}。建议定期复查，关注指标变化。")
        
        # 通用建议
        if not suggestions:
            suggestions.append("请将识别的文本内容咨询专业医生，获取准确的医疗建议。")
        
        suggestions.append("注意：图像识别结果仅供参考，不能替代专业医疗诊断。")
        
        return suggestions
    
    def process_medical_image(self, image_file, image_name="医学图像"):
        """完整的医学图像处理流程"""
        try:
            # 1. OCR文字识别
            ocr_result = self.extract_text_from_image(image_file)
            
            # 2. 文本分析
            if ocr_result['text']:
                text_analysis = self.analyze_medical_text(ocr_result['text'])
            else:
                text_analysis = {
                    'analysis': '未能识别出文本内容',
                    'keywords': [],
                    'medical_entities': [],
                    'suggestions': ['图像可能不包含文字，或文字不够清晰']
                }
            
            # 3. 生成结果摘要
            result = {
                'image_name': image_name,
                'ocr_result': ocr_result,
                'text_analysis': text_analysis,
                'processing_time': datetime.now().isoformat(),
                'success': len(ocr_result['text']) > 0
            }
            
            # 4. 保存到数据库
            try:
                recognition_result = ImageRecognitionResult.objects.create(
                    image_name=image_name,
                    extracted_text=ocr_result['text'],
                    recognition_details=json.dumps(ocr_result),
                    analysis_result=json.dumps(text_analysis)
                )
                result['result_id'] = recognition_result.id
            except Exception as db_error:
                print(f"数据库保存错误: {db_error}")
                result['result_id'] = None
            
            return result
            
        except Exception as e:
            print(f"图像处理错误: {e}")
            return {
                'image_name': image_name,
                'error': str(e),
                'success': False,
                'processing_time': datetime.now().isoformat()
            }

def main():
    """测试函数"""
    try:
        ocr = MedicalOCR()
        print("医学OCR识别器初始化成功")
        
        # 这里可以添加测试代码
        # result = ocr.process_medical_image("test_image.jpg")
        # print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"初始化失败: {e}")

if __name__ == "__main__":
    main() 