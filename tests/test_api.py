#!/usr/bin/env python
"""
医疗问答系统 API 测试脚本
用于测试系统的各种功能接口
"""

import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试系统健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/system/health/")
        data = response.json()
        print(f"   状态: {data.get('status', 'unknown')}")
        print(f"   数据库: {data.get('database', 'unknown')}")
        print(f"   搜索索引: {data.get('search_index', 'unknown')}")
        print(f"   文本处理: {data.get('text_processor', 'unknown')}")
        print("✅ 健康检查通过\n")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}\n")
        return False

def test_system_stats():
    """测试系统统计"""
    print("📊 测试系统统计...")
    try:
        response = requests.get(f"{BASE_URL}/system/stats/")
        data = response.json()
        stats = data.get('total_stats', {})
        print(f"   问答数据: {stats.get('qa_data', 0)}")
        print(f"   文档数量: {stats.get('documents', 0)}")
        print(f"   聊天会话: {stats.get('chat_sessions', 0)}")
        print(f"   消息总数: {stats.get('chat_messages', 0)}")
        print("✅ 系统统计获取成功\n")
        return True
    except Exception as e:
        print(f"❌ 系统统计失败: {e}\n")
        return False

def test_chat_text():
    """测试文本问答"""
    print("💬 测试文本问答...")
    test_questions = [
        "感冒了怎么办？",
        "高血压怎么治疗？",
        "糖尿病有什么症状？",
        "心脏病如何预防？"
    ]
    
    try:
        for question in test_questions:
            response = requests.post(f"{BASE_URL}/chat/text/", 
                                   json={"message": question},
                                   headers={"Content-Type": "application/json"})
            data = response.json()
            if data.get('response'):
                print(f"   Q: {question}")
                print(f"   A: {data['response'][:100]}...")
            else:
                print(f"   Q: {question} - 未找到答案")
        
        print("✅ 文本问答测试完成\n")
        return True
    except Exception as e:
        print(f"❌ 文本问答测试失败: {e}\n")
        return False

def test_chat_history():
    """测试聊天历史"""
    print("📝 测试聊天历史...")
    try:
        response = requests.get(f"{BASE_URL}/chat/history/")
        data = response.json()
        sessions = data.get('sessions', [])
        print(f"   会话数量: {len(sessions)}")
        if sessions:
            latest_session = sessions[0]
            messages = latest_session.get('messages', [])
            print(f"   最新会话消息数: {len(messages)}")
        print("✅ 聊天历史获取成功\n")
        return True
    except Exception as e:
        print(f"❌ 聊天历史测试失败: {e}\n")
        return False

def test_document_upload():
    """测试文档上传"""
    print("📄 测试文档上传...")
    try:
        # 创建测试文档
        test_content = """
        医疗知识测试文档
        
        感冒是常见的呼吸道疾病，主要症状包括鼻塞、流涕、咳嗽等。
        治疗方法包括多休息、多喝水、适当服用感冒药。
        预防感冒要注意勤洗手、戴口罩、避免接触病患。
        
        高血压是心血管疾病的重要危险因素。
        患者需要长期服药控制血压，同时注意低盐饮食。
        """
        
        # 创建临时文件
        with open("test_document.txt", "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # 上传文档
        with open("test_document.txt", "rb") as f:
            files = {"document": ("test_document.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/document/upload/", files=files)
        
        data = response.json()
        if data.get('id'):
            print(f"   文档ID: {data['id']}")
            print(f"   识别的实体: {len(data.get('entities', []))}")
            print(f"   摘要长度: {len(data.get('summary', ''))}")
            print("✅ 文档上传成功\n")
            
            # 清理临时文件
            os.remove("test_document.txt")
            return True
        else:
            print(f"❌ 文档上传失败: {data.get('error', 'Unknown error')}\n")
            return False
            
    except Exception as e:
        print(f"❌ 文档上传测试失败: {e}\n")
        # 清理临时文件
        if os.path.exists("test_document.txt"):
            os.remove("test_document.txt")
        return False

def test_text_mining():
    """测试文本挖掘"""
    print("🔍 测试文本挖掘...")
    try:
        # 运行文本挖掘
        response = requests.post(f"{BASE_URL}/mining/run/", 
                               json={
                                   "clustering_method": "kmeans",
                                   "n_clusters": 5
                               },
                               headers={"Content-Type": "application/json"})
        
        data = response.json()
        if data.get('result_id'):
            print(f"   挖掘结果ID: {data['result_id']}")
            print(f"   处理文档数: {data.get('n_documents', 0)}")
            print(f"   聚类数: {data.get('n_clusters', 0)}")
            print("✅ 文本挖掘成功\n")
            return True
        else:
            print(f"❌ 文本挖掘失败: {data.get('error', 'Unknown error')}\n")
            return False
            
    except Exception as e:
        print(f"❌ 文本挖掘测试失败: {e}\n")
        return False

def test_mining_results():
    """测试挖掘结果获取"""
    print("📊 测试挖掘结果获取...")
    try:
        response = requests.get(f"{BASE_URL}/mining/results/")
        data = response.json()
        results = data.get('results', [])
        print(f"   挖掘结果数量: {len(results)}")
        if results:
            latest_result = results[0]
            print(f"   最新结果ID: {latest_result.get('id')}")
            print(f"   数据集名称: {latest_result.get('dataset_name')}")
            print(f"   聚类方法: {latest_result.get('method')}")
        print("✅ 挖掘结果获取成功\n")
        return True
    except Exception as e:
        print(f"❌ 挖掘结果获取失败: {e}\n")
        return False

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("🏥 医疗问答系统 API 测试")
    print("=" * 50)
    
    tests = [
        ("系统健康检查", test_health_check),
        ("系统统计", test_system_stats),
        ("文本问答", test_chat_text),
        ("聊天历史", test_chat_history),
        ("文档上传", test_document_upload),
        ("文本挖掘", test_text_mining),
        ("挖掘结果", test_mining_results),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"运行测试: {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)  # 避免请求过快
    
    print("=" * 50)
    print(f"📋 测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！系统运行正常。")
    else:
        print("⚠️  部分测试失败，请检查系统状态。")
    
    print("=" * 50)

if __name__ == "__main__":
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            run_all_tests()
        else:
            print("❌ 服务器未正常响应，请确保Django服务器正在运行")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保Django服务器在 http://127.0.0.1:8000 运行")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}") 