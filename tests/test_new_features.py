#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新添加的数据管理功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """测试新的API功能"""
    
    print("🧪 测试新添加的数据管理功能")
    print("=" * 50)
    
    # 1. 测试数据统计
    print("\n1. 测试数据统计功能...")
    try:
        response = requests.get(f"{BASE_URL}/data/stats/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 数据统计成功")
            print(f"   📊 总数据量: {data['total_qa']} 条")
            print(f"   📊 已处理: {data['processed_qa']} 条")
            print(f"   📊 未处理: {data['unprocessed_qa']} 条")
            print(f"   📊 分类数量: {len(data['categories'])} 种")
            print(f"   📊 索引状态: {'已构建' if data['index_ready'] else '未构建'}")
        else:
            print(f"   ❌ 数据统计失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 数据统计异常: {e}")
    
    # 2. 测试数据处理
    print("\n2. 测试数据处理功能...")
    try:
        response = requests.post(f"{BASE_URL}/data/process/", 
                               headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 数据处理成功")
            print(f"   ⚙️ 处理数量: {data['processed_count']} 条")
            print(f"   ⏱️ 处理时间: {data['process_time']}")
            print(f"   📚 索引文档: {data['index_documents']} 个")
        else:
            print(f"   ❌ 数据处理失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 数据处理异常: {e}")
    
    # 3. 测试智能问答（验证处理后的效果）
    print("\n3. 测试智能问答功能...")
    test_questions = [
        "感冒发烧怎么办",
        "高血压患者饮食注意什么",
        "咳嗽有痰怎么治疗"
    ]
    
    for i, question in enumerate(test_questions, 1):
        try:
            response = requests.post(f"{BASE_URL}/chat/text/", 
                                   headers={"Content-Type": "application/json"},
                                   json={"question": question, "session_id": f"test_session_{i}"})
            if response.status_code == 200:
                data = response.json()
                answer = data['answer']
                if "很抱歉，我无法找到" not in answer:
                    print(f"   ✅ 问题{i}: {question} - 找到相关答案")
                else:
                    print(f"   ⚠️ 问题{i}: {question} - 未找到匹配答案")
            else:
                print(f"   ❌ 问题{i}失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 问题{i}异常: {e}")
    
    # 4. 获取处理后的统计
    print("\n4. 获取处理后的数据统计...")
    try:
        response = requests.get(f"{BASE_URL}/data/stats/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 更新后统计:")
            print(f"   📊 会话数: {data['sessions']}")
            print(f"   📊 消息数: {data['messages']}")
            print(f"   📊 文档数: {data['documents']}")
            print(f"   📊 挖掘结果: {data['mining_results']}")
        else:
            print(f"   ❌ 统计失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 统计异常: {e}")
    
    print("\n" + "=" * 50)
    print("✨ 新功能测试完成！")
    
    # 提示用户可以测试的功能
    print("\n🎯 您现在可以在浏览器中测试以下功能：")
    print("   1. 访问 http://localhost:8000")
    print("   2. 进入'数据爬取与管理'选项卡")
    print("   3. 点击'数据统计'查看详细统计")
    print("   4. 点击'处理数据'重新处理数据")
    print("   5. 在智能问答中测试医疗问题")
    print("   6. 如需清除数据，可使用'清除所有数据'按钮（谨慎操作）")

if __name__ == "__main__":
    test_api() 