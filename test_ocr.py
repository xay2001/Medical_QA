#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime

# 添加Django环境
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from image_recognition.medical_ocr import MedicalOCR

def test_medical_ocr():
    """测试医学OCR功能"""
    print("=" * 60)
    print("医学图像识别功能测试")
    print("=" * 60)
    
    try:
        # 初始化OCR
        print("1. 初始化PaddleOCR...")
        ocr = MedicalOCR()
        print("✓ PaddleOCR初始化成功")
        
        # 测试图像路径
        test_image_path = "test_images/medical_test.png"
        
        if not os.path.exists(test_image_path):
            print(f"✗ 测试图像不存在: {test_image_path}")
            return
        
        print(f"2. 处理测试图像: {test_image_path}")
        
        # 进行图像识别
        start_time = datetime.now()
        result = ocr.process_medical_image(test_image_path, "医疗测试图像")
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"✓ 图像处理完成，耗时: {processing_time:.2f}秒")
        
        # 显示结果
        print("\n" + "=" * 40)
        print("识别结果:")
        print("=" * 40)
        
        if result.get('success'):
            ocr_result = result.get('ocr_result', {})
            text_analysis = result.get('text_analysis', {})
            
            print(f"识别状态: 成功")
            print(f"识别文本长度: {len(ocr_result.get('text', ''))}")
            print(f"检测到的文本块数: {ocr_result.get('total_detections', 0)}")
            
            print(f"\n识别出的文本:")
            print("-" * 20)
            print(ocr_result.get('text', ''))
            
            print(f"\n文本分析结果:")
            print("-" * 20)
            print(f"分析状态: {text_analysis.get('analysis', '')}")
            print(f"关键词: {text_analysis.get('keywords', [])}")
            
            medical_entities = text_analysis.get('medical_entities', [])
            if medical_entities:
                print(f"\n医学实体识别:")
                for entity_group in medical_entities:
                    category = entity_group.get('category', '')
                    entities = entity_group.get('entities', [])
                    print(f"  {category}: {', '.join(entities)}")
            
            suggestions = text_analysis.get('suggestions', [])
            if suggestions:
                print(f"\n医疗建议:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
            
            # 显示OCR详细信息
            details = ocr_result.get('details', [])
            if details:
                print(f"\nOCR详细信息 (前5个):")
                print("-" * 30)
                for i, detail in enumerate(details[:5]):
                    print(f"  文本: '{detail.get('text', '')}' - 置信度: {detail.get('confidence', 0):.3f}")
            
            print(f"\n数据库记录ID: {result.get('result_id', 'N/A')}")
        else:
            print(f"识别失败: {result.get('error', '未知错误')}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_medical_ocr() 