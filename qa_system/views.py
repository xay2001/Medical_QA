from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
import json
import uuid
import os
import base64
from PIL import Image
import io
from datetime import datetime
import traceback
import time

from .models import QAData, ChatSession, ChatMessage, Document, TextMiningResult, ImageRecognitionResult
from data_processing.text_processor import TextProcessor

# 全局变量存储索引
text_processor = TextProcessor()
search_index = None

def index(request):
    """主页"""
    return render(request, 'index.html')

def dashboard(request):
    """监控仪表板"""
    return render(request, 'dashboard.html')

@csrf_exempt
@require_http_methods(["POST"])
def chat_text(request):
    """文本问答接口"""
    global search_index
    
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        session_id = data.get('session_id')
        
        if not question:
            return JsonResponse({'error': '问题不能为空'}, status=400)
        
        # 获取或创建会话
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(session_id=session_id)
        else:
            session_id = str(uuid.uuid4())
            session = ChatSession.objects.create(session_id=session_id)
        
        # 保存用户消息
        ChatMessage.objects.create(
            session=session,
            sender_type='user',
            message_type='text',
            content=question
        )
        
        # 构建搜索索引（如果还没有）
        if search_index is None:
            search_index = text_processor.build_index()
        
        # 搜索相似问答
        if search_index:
            similar_results = text_processor.search_similar_qa(question, search_index, top_k=3)
            
            if similar_results and similar_results[0]['similarity'] > 0.1:
                # 找到相似问题，返回答案
                best_match = similar_results[0]['qa']
                answer = best_match.answer
                
                # 如果相似度不够高，添加提醒
                if similar_results[0]['similarity'] < 0.4:
                    answer = f"根据您的问题，我找到了相关信息：\n\n{answer}\n\n注意：以上回答是基于相似问题的建议，建议您咨询专业医生获得准确诊断。"
            else:
                # 没有找到相似问题，返回通用回答
                answer = """很抱歉，我无法找到与您问题完全匹配的答案。

建议您：
1. 尝试用更具体的词汇重新描述您的问题
2. 咨询专业医生获得准确的医疗建议
3. 如果是紧急情况，请及时就医

请注意：本系统提供的信息仅供参考，不能替代专业医疗诊断。"""
        else:
            answer = "系统正在初始化，请稍后再试。"
        
        # 保存机器人回复
        ChatMessage.objects.create(
            session=session,
            sender_type='bot',
            message_type='text',
            content=answer
        )
        
        return JsonResponse({
            'answer': answer,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"文本问答错误: {e}")
        traceback.print_exc()
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def chat_image(request):
    """图像问答接口"""
    try:
        # 获取会话信息
        session_id = request.POST.get('session_id')
        question = request.POST.get('question', '').strip()
        image_file = request.FILES.get('image')
        
        if not image_file:
            return JsonResponse({'error': '请上传图像'}, status=400)
        
        # 获取或创建会话
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(session_id=session_id)
        else:
            session_id = str(uuid.uuid4())
            session = ChatSession.objects.create(session_id=session_id)
        
        # 保存图像
        image_path = default_storage.save(f'chat_images/{uuid.uuid4()}.jpg', image_file)
        
        # 保存用户消息
        ChatMessage.objects.create(
            session=session,
            sender_type='user',
            message_type='image',
            content=question or '用户上传了一张图片',
            image=image_path
        )
        
        # 图像识别（这里使用模拟功能，实际可以集成飞桨API）
        image_description = analyze_medical_image(image_file)
        
        # 基于图像描述和问题生成回答
        if question:
            combined_query = f"{question} {image_description}"
        else:
            combined_query = image_description
        
        # 搜索相关医疗信息
        global search_index
        if search_index is None:
            search_index = text_processor.build_index()
        
        answer = f"图像分析结果：{image_description}\n\n"
        
        if search_index:
            similar_results = text_processor.search_similar_qa(combined_query, search_index, top_k=2)
            if similar_results and similar_results[0]['similarity'] > 0.2:
                answer += f"相关医疗信息：\n{similar_results[0]['qa'].answer}\n\n"
        
        answer += "注意：图像分析结果仅供参考，请咨询专业医生获得准确诊断。"
        
        # 保存机器人回复
        ChatMessage.objects.create(
            session=session,
            sender_type='bot',
            message_type='text',
            content=answer
        )
        
        return JsonResponse({
            'answer': answer,
            'image_description': image_description,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"图像问答错误: {e}")
        traceback.print_exc()
        return JsonResponse({'error': '服务器内部错误'}, status=500)

def analyze_medical_image(image_file):
    """分析医疗图像（模拟功能）"""
    try:
        # 这里可以集成飞桨的图像识别API
        # 目前使用模拟功能
        
        image = Image.open(image_file)
        width, height = image.size
        
        # 基于图像尺寸和格式的简单判断（模拟）
        if width > 1000 or height > 1000:
            return "这是一张高分辨率的医疗影像，可能是X光片、CT或MRI图像。建议由专业医生进行诊断。"
        else:
            return "这是一张医疗相关图像。由于无法进行详细的医学影像分析，建议您咨询专业医生。"
            
    except Exception as e:
        return f"图像分析失败，请确保上传的是有效的图像文件。"

@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    """文档上传接口"""
    try:
        document_file = request.FILES.get('document')
        title = request.POST.get('title', '').strip()
        
        if not document_file:
            return JsonResponse({'error': '请选择文档文件'}, status=400)
        
        if not title:
            title = document_file.name
        
        # 读取文档内容
        content = extract_document_content(document_file)
        
        if not content:
            return JsonResponse({'error': '无法读取文档内容'}, status=400)
        
        # 保存文档
        document = Document.objects.create(
            title=title,
            content=content,
            file_type=document_file.content_type,
        )
        
        # 文本分析
        analysis_result = analyze_document(document)
        
        return JsonResponse({
            'document_id': document.id,
            'title': document.title,
            'analysis': analysis_result,
            'message': '文档上传并分析完成'
        })
        
    except Exception as e:
        print(f"文档上传错误: {e}")
        traceback.print_exc()
        return JsonResponse({'error': '服务器内部错误'}, status=500)

def extract_document_content(document_file):
    """提取文档内容"""
    try:
        content = ""
        
        if document_file.content_type == 'text/plain':
            content = document_file.read().decode('utf-8')
        elif document_file.content_type == 'application/pdf':
            # 使用PyPDF2处理PDF
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(document_file)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n"
            except Exception as e:
                print(f"PDF读取错误: {e}")
                content = "PDF文档内容提取失败"
        elif document_file.content_type.startswith('application/vnd.openxmlformats') or document_file.name.endswith('.docx'):
            # 使用python-docx处理Word文档
            try:
                from docx import Document
                doc = Document(document_file)
                content = ""
                for paragraph in doc.paragraphs:
                    content += paragraph.text + "\n"
            except Exception as e:
                print(f"Word文档读取错误: {e}")
                content = "Word文档内容提取失败"
        else:
            # 尝试作为文本文件读取
            try:
                content = document_file.read().decode('utf-8', errors='ignore')
            except:
                content = "无法识别的文件格式"
        
        return content[:10000]  # 限制长度
        
    except Exception as e:
        print(f"文档内容提取错误: {e}")
        return None

def analyze_document(document):
    """分析文档"""
    try:
        content = document.content
        
        # 词性标注（简化版）
        words = text_processor.segment_text(content)
        pos_tags = words[:20]  # 取前20个词作为示例
        
        # 实体识别（简化版）
        entities = extract_medical_entities(content)
        
        # 文档摘要
        summary = generate_summary(content)
        
        # 保存分析结果
        document.pos_tags = json.dumps(pos_tags, ensure_ascii=False)
        document.entities = json.dumps(entities, ensure_ascii=False)
        document.summary = summary
        document.save()
        
        return {
            'pos_tags': pos_tags,
            'entities': entities,
            'summary': summary
        }
        
    except Exception as e:
        print(f"文档分析错误: {e}")
        return {}

def extract_medical_entities(text):
    """提取医疗实体（简化版）"""
    # 医疗实体关键词
    medical_entities = {
        '疾病': ['感冒', '发烧', '咳嗽', '头痛', '胃痛', '高血压', '糖尿病', '心脏病'],
        '症状': ['疼痛', '发热', '乏力', '恶心', '呕吐', '腹泻', '失眠', '头晕'],
        '药物': ['阿司匹林', '布洛芬', '抗生素', '胰岛素', '降压药', '维生素'],
        '检查': ['血常规', '尿常规', 'B超', 'CT', 'MRI', 'X光', '心电图']
    }
    
    found_entities = {}
    
    for category, keywords in medical_entities.items():
        found = []
        for keyword in keywords:
            if keyword in text:
                found.append(keyword)
        if found:
            found_entities[category] = found
    
    return found_entities

def generate_summary(text):
    """生成文档摘要（简化版）"""
    if len(text) <= 200:
        return text
    
    # 简单的摘要方法：取前100个字符
    summary = text[:100] + "..."
    
    return summary

@csrf_exempt
@require_http_methods(["POST"])
def download_analysis_result(request):
    """下载分析结果"""
    try:
        data = json.loads(request.body)
        document_id = data.get('document_id')
        
        document = Document.objects.get(id=document_id)
        
        # 生成分析结果文件内容
        result_content = f"""文档分析结果

文档标题：{document.title}
分析时间：{document.created_at}

词性标注结果：
{document.pos_tags}

实体识别结果：
{document.entities}

文档摘要：
{document.summary}
"""
        
        return JsonResponse({
            'filename': f"{document.title}_分析结果.txt",
            'content': result_content
        })
        
    except Exception as e:
        print(f"下载分析结果错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_chat_history(request):
    """获取聊天历史"""
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': '会话ID不能为空'}, status=400)
        
        try:
            session = ChatSession.objects.get(session_id=session_id)
            messages = session.messages.all()
            
            chat_history = []
            for msg in messages:
                message_data = {
                    'sender_type': msg.sender_type,
                    'message_type': msg.message_type,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat()
                }
                
                if msg.image:
                    message_data['image_url'] = msg.image.url
                
                chat_history.append(message_data)
            
            return JsonResponse({
                'session_id': session_id,
                'messages': chat_history
            })
            
        except ChatSession.DoesNotExist:
            return JsonResponse({
                'session_id': session_id,
                'messages': []
            })
        
    except Exception as e:
        print(f"获取聊天历史错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def start_crawler(request):
    """启动爬虫"""
    try:
        data = json.loads(request.body)
        target_count = data.get('target_count', 1000)
        
        # 这里可以异步启动爬虫任务
        # 目前直接导入并运行
        from crawler.dingxiang_crawler import DingXiangCrawler
        
        crawler = DingXiangCrawler()
        success_count = crawler.crawl_qa_data(target_count)
        
        # 重新构建索引
        global search_index
        search_index = text_processor.build_index()
        
        return JsonResponse({
            'message': f'爬虫任务完成，成功获取 {success_count} 条数据',
            'success_count': success_count
        })
        
    except Exception as e:
        print(f"启动爬虫错误: {e}")
        traceback.print_exc()
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_dataset(request):
    """上传数据集进行文本挖掘"""
    try:
        dataset_file = request.FILES.get('dataset')
        dataset_name = request.POST.get('dataset_name', '').strip()
        clustering_method = request.POST.get('clustering_method', 'kmeans')
        n_clusters = int(request.POST.get('n_clusters', 5))
        
        if not dataset_file:
            return JsonResponse({'error': '请选择数据集文件'}, status=400)
        
        if not dataset_name:
            dataset_name = f"数据集_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 处理上传的文件
        import zipfile
        import tempfile
        import shutil
        
        texts = []
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存上传的文件
            temp_file_path = os.path.join(temp_dir, dataset_file.name)
            with open(temp_file_path, 'wb+') as destination:
                for chunk in dataset_file.chunks():
                    destination.write(chunk)
            
            # 解压ZIP文件
            if dataset_file.name.endswith('.zip'):
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # 读取所有txt文件
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.txt') and not file.startswith('.'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()
                                    if content:
                                        # 按行分割，每行作为一个文档
                                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                                        texts.extend(lines)
                            except Exception as e:
                                print(f"读取文件 {file_path} 出错: {e}")
                                continue
            else:
                return JsonResponse({'error': '仅支持ZIP格式的数据集文件'}, status=400)
        
        if not texts:
            return JsonResponse({'error': '数据集中没有找到有效的文本数据'}, status=400)
        
        print(f"成功读取 {len(texts)} 条文本数据")
        
        # 导入文本挖掘分析器
        from text_mining.text_mining_analyzer import TextMiningAnalyzer
        
        analyzer = TextMiningAnalyzer()
        
        # 运行分析（使用上传的数据）
        result = analyzer.run_complete_analysis_with_texts(
            texts=texts,
            dataset_name=dataset_name,
            clustering_method=clustering_method,
            n_clusters=n_clusters
        )
        
        return JsonResponse({
            'result_id': result['result_id'],
            'message': '数据集分析完成',
            'summary': result['summary'],
            'tsne_image': result['tsne_image'],
            'wordclouds': result['wordclouds'],
            'clustering_info': result['clustering']['cluster_info']
        })
        
    except Exception as e:
        print(f"数据集上传和分析错误: {e}")
        traceback.print_exc()
        return JsonResponse({'error': f'服务器内部错误: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def run_text_mining(request):
    """运行文本挖掘分析（使用现有问答数据）"""
    try:
        data = json.loads(request.body)
        clustering_method = data.get('clustering_method', 'kmeans')
        n_clusters = int(data.get('n_clusters', 5))
        dataset_name = data.get('dataset_name', f"医疗问答数据挖掘_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # 导入文本挖掘分析器
        from text_mining.text_mining_analyzer import TextMiningAnalyzer
        
        analyzer = TextMiningAnalyzer()
        
        # 运行分析
        result = analyzer.run_complete_analysis(
            dataset_name=dataset_name,
            clustering_method=clustering_method,
            n_clusters=n_clusters
        )
        
        return JsonResponse({
            'result_id': result['result_id'],
            'message': '文本挖掘分析完成',
            'summary': result['summary'],
            'tsne_image': result['tsne_image'],
            'wordclouds': result['wordclouds'],
            'clustering_info': result['clustering']['cluster_info']
        })
        
    except Exception as e:
        print(f"文本挖掘分析错误: {e}")
        traceback.print_exc()
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_mining_result(request, result_id):
    """获取文本挖掘结果"""
    try:
        result = TextMiningResult.objects.get(id=result_id)
        
        # 解析存储的结果
        clustering_result = json.loads(result.clustering_result) if result.clustering_result else {}
        wordcloud_plots = json.loads(result.wordcloud_plots) if result.wordcloud_plots else {}
        
        return JsonResponse({
            'result_id': result.id,
            'dataset_name': result.dataset_name,
            'created_at': result.created_at.isoformat(),
            'clustering_result': clustering_result,
            'tsne_image': wordcloud_plots.get('tsne_image', ''),
            'wordclouds': wordcloud_plots.get('wordclouds', {}),
        })
        
    except TextMiningResult.DoesNotExist:
        return JsonResponse({'error': '结果不存在'}, status=404)
    except Exception as e:
        print(f"获取挖掘结果错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_mining_results(request):
    """列出所有文本挖掘结果"""
    try:
        results = TextMiningResult.objects.all().order_by('-created_at')
        
        results_data = []
        for result in results:
            clustering_result = json.loads(result.clustering_result) if result.clustering_result else {}
            
            results_data.append({
                'id': result.id,
                'dataset_name': result.dataset_name,
                'created_at': result.created_at.isoformat(),
                'n_clusters': clustering_result.get('n_clusters', 0),
                'method': clustering_result.get('method', ''),
            })
        
        return JsonResponse({
            'results': results_data,
            'total_count': len(results_data)
        })
        
    except Exception as e:
        print(f"列出挖掘结果错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def system_stats(request):
    """获取系统统计信息"""
    try:
        # 统计各类数据
        total_qa = QAData.objects.count()
        total_documents = Document.objects.count()
        total_sessions = ChatSession.objects.count()
        total_messages = ChatMessage.objects.count()
        total_mining_results = TextMiningResult.objects.count()
        
        # 按类别统计问答数据
        category_stats = {}
        categories = QAData.objects.values_list('category', flat=True).distinct()
        for category in categories:
            if category:
                category_stats[category] = QAData.objects.filter(category=category).count()
        
        # 最近7天的数据统计
        from datetime import timedelta
        recent_date = datetime.now() - timedelta(days=7)
        recent_qa = QAData.objects.filter(created_at__gte=recent_date).count()
        recent_documents = Document.objects.filter(created_at__gte=recent_date).count()
        recent_sessions = ChatSession.objects.filter(created_at__gte=recent_date).count()
        
        # 消息类型统计
        text_messages = ChatMessage.objects.filter(message_type='text').count()
        image_messages = ChatMessage.objects.filter(message_type='image').count()
        
        return JsonResponse({
            'total_stats': {
                'qa_data': total_qa,
                'documents': total_documents,
                'chat_sessions': total_sessions,
                'chat_messages': total_messages,
                'text_mining_results': total_mining_results
            },
            'category_stats': category_stats,
            'recent_stats': {
                'qa_data': recent_qa,
                'documents': recent_documents,
                'chat_sessions': recent_sessions
            },
            'message_stats': {
                'text_messages': text_messages,
                'image_messages': image_messages
            },
            'system_status': 'running',
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"获取系统统计错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """健康检查接口"""
    try:
        # 检查数据库连接
        qa_count = QAData.objects.count()
        session_count = ChatSession.objects.count()
        
        # 检查存储空间
        import shutil
        disk_usage = shutil.disk_usage('/')
        disk_free_gb = disk_usage.free / (1024**3)
        
        # 检查索引状态
        global search_index
        index_ready = search_index is not None
        
        status = "healthy" if disk_free_gb > 1 and qa_count > 0 else "warning"
        
        return JsonResponse({
            'status': status,
            'database': {
                'qa_data_count': qa_count,
                'session_count': session_count,
                'connection': 'ok'
            },
            'storage': {
                'disk_free_gb': round(disk_free_gb, 2),
                'status': 'ok' if disk_free_gb > 1 else 'warning'
            },
            'search_index': {
                'ready': index_ready,
                'status': 'ok' if index_ready else 'not_built'
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"健康检查错误: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_data(request):
    """数据处理接口"""
    global search_index
    
    try:
        start_time = time.time()
        
        # 处理数据
        processed_count = text_processor.process_qa_data()
        
        # 重新构建索引
        search_index = text_processor.build_index()
        
        # 计算处理时间
        process_time = round(time.time() - start_time, 2)
        
        # 获取索引信息
        index_documents = len(search_index) if search_index else 0
        
        return JsonResponse({
            'message': '数据处理完成',
            'processed_count': processed_count,
            'process_time': f"{process_time} 秒",
            'index_built': search_index is not None,
            'index_documents': index_documents,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"数据处理错误: {e}")
        traceback.print_exc()
        return JsonResponse({
            'error': f'数据处理失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_data_stats(request):
    """获取数据统计接口"""
    try:
        from django.db.models import Count
        from collections import Counter
        
        # 基础统计
        total_qa = QAData.objects.count()
        processed_qa = QAData.objects.exclude(processed_question='').count()
        unprocessed_qa = total_qa - processed_qa
        
        # 分类统计
        categories = list(QAData.objects.values_list('category', flat=True))
        category_stats = dict(Counter(categories))
        
        # 其他统计
        session_count = ChatSession.objects.count()
        message_count = ChatMessage.objects.count()
        document_count = Document.objects.count()
        mining_result_count = TextMiningResult.objects.count()
        
        # 索引状态
        global search_index
        index_ready = search_index is not None
        
        # 最后更新时间（使用最新的QA数据时间）
        latest_qa = QAData.objects.order_by('-id').first()
        last_updated = latest_qa.created_at.isoformat() if latest_qa and hasattr(latest_qa, 'created_at') else '未知'
        
        return JsonResponse({
            'total_qa': total_qa,
            'processed_qa': processed_qa,
            'unprocessed_qa': unprocessed_qa,
            'categories': category_stats,
            'sessions': session_count,
            'messages': message_count,
            'documents': document_count,
            'mining_results': mining_result_count,
            'index_ready': index_ready,
            'last_updated': last_updated,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"获取统计错误: {e}")
        traceback.print_exc()
        return JsonResponse({
            'error': f'获取统计失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def clear_all_data(request):
    """清除所有数据接口"""
    global search_index
    
    try:
        # 统计要删除的数据
        qa_count = QAData.objects.count()
        session_count = ChatSession.objects.count()
        message_count = ChatMessage.objects.count()
        document_count = Document.objects.count()
        mining_count = TextMiningResult.objects.count()
        
        # 删除数据（使用级联删除）
        QAData.objects.all().delete()
        ChatSession.objects.all().delete()  # 这会自动删除相关的消息
        Document.objects.all().delete()
        TextMiningResult.objects.all().delete()
        
        # 清除索引
        search_index = None
        
        # 清理媒体文件（可选）
        import shutil
        import os
        media_dirs = ['chat_images', 'documents', 'mining_results']
        for dir_name in media_dirs:
            dir_path = os.path.join(settings.MEDIA_ROOT, dir_name)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    print(f"清理目录 {dir_name} 失败: {e}")
        
        return JsonResponse({
            'message': '数据清除完成',
            'deleted_count': qa_count,
            'deleted_sessions': session_count,
            'deleted_messages': message_count,
            'deleted_documents': document_count,
            'deleted_mining_results': mining_count,
            'index_cleared': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"数据清除错误: {e}")
        traceback.print_exc()
        return JsonResponse({
            'error': f'数据清除失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, status=500)

# ==================== 图像识别相关视图 ====================

@csrf_exempt
@require_http_methods(["POST"])
def upload_medical_image(request):
    """上传医学图像进行OCR识别"""
    try:
        # 检查是否有文件上传
        if 'image' not in request.FILES:
            return JsonResponse({'error': '请选择图像文件'}, status=400)
        
        image_file = request.FILES['image']
        image_name = request.POST.get('image_name', image_file.name)
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff']
        if image_file.content_type not in allowed_types:
            return JsonResponse({'error': '仅支持 JPEG、PNG、BMP、TIFF 格式的图像'}, status=400)
        
        # 验证文件大小（限制为10MB）
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': '图像文件大小不能超过10MB'}, status=400)
        
        print(f"开始处理图像: {image_name}, 大小: {image_file.size} bytes")
        
        # 导入图像识别模块
        try:
            from image_recognition.medical_ocr import MedicalOCR
        except ImportError as e:
            return JsonResponse({'error': f'图像识别模块未正确安装: {str(e)}'}, status=500)
        
        # 初始化OCR识别器
        start_time = time.time()
        try:
            ocr = MedicalOCR()
        except Exception as e:
            return JsonResponse({'error': f'OCR初始化失败: {str(e)}'}, status=500)
        
        # 进行图像识别
        result = ocr.process_medical_image(image_file, image_name)
        processing_time = time.time() - start_time
        
        # 计算平均置信度
        avg_confidence = 0.0
        if result.get('ocr_result', {}).get('details'):
            confidences = [detail['confidence'] for detail in result['ocr_result']['details']]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
        
        # 保存图像文件（如果识别成功）
        if result.get('success'):
            try:
                # 更新数据库记录，保存图像文件
                if result.get('result_id'):
                    recognition_result = ImageRecognitionResult.objects.get(id=result['result_id'])
                    recognition_result.image_file = image_file
                    recognition_result.processing_time = processing_time
                    recognition_result.confidence_score = avg_confidence
                    recognition_result.save()
            except Exception as db_error:
                print(f"保存图像文件错误: {db_error}")
        
        # 返回识别结果
        response_data = {
            'success': result.get('success', False),
            'result_id': result.get('result_id'),
            'extracted_text': result.get('ocr_result', {}).get('text', ''),
            'total_detections': result.get('ocr_result', {}).get('total_detections', 0),
            'confidence_score': round(avg_confidence, 3),
            'processing_time': round(processing_time, 2),
            'analysis': result.get('text_analysis', {}),
            'message': '图像识别完成' if result.get('success') else '图像识别失败'
        }
        
        # 如果有错误，添加错误信息
        if 'error' in result:
            response_data['error'] = result['error']
        
        print(f"图像识别完成: {image_name}, 识别文本长度: {len(response_data['extracted_text'])}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"图像上传和识别错误: {e}")
        traceback.print_exc()
        return JsonResponse({'error': f'服务器内部错误: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_recognition_result(request, result_id):
    """获取图像识别结果详情"""
    try:
        result = ImageRecognitionResult.objects.get(id=result_id)
        
        # 解析JSON字段
        recognition_details = result.get_recognition_details()
        analysis_result = result.get_analysis_result()
        
        return JsonResponse({
            'result_id': result.id,
            'image_name': result.image_name,
            'extracted_text': result.extracted_text,
            'recognition_details': recognition_details,
            'analysis_result': analysis_result,
            'processing_time': result.processing_time,
            'confidence_score': result.confidence_score,
            'created_at': result.created_at.isoformat(),
            'image_url': result.image_file.url if result.image_file else None
        })
        
    except ImageRecognitionResult.DoesNotExist:
        return JsonResponse({'error': '识别结果不存在'}, status=404)
    except Exception as e:
        print(f"获取识别结果错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_recognition_results(request):
    """列出所有图像识别结果"""
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询结果
        total_count = ImageRecognitionResult.objects.count()
        results = ImageRecognitionResult.objects.all()[offset:offset + page_size]
        
        results_data = []
        for result in results:
            results_data.append({
                'id': result.id,
                'image_name': result.image_name,
                'extracted_text_preview': result.extracted_text[:100] + '...' if len(result.extracted_text) > 100 else result.extracted_text,
                'confidence_score': result.confidence_score,
                'processing_time': result.processing_time,
                'created_at': result.created_at.isoformat(),
                'has_image': bool(result.image_file)
            })
        
        return JsonResponse({
            'results': results_data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
        
    except Exception as e:
        print(f"列出识别结果错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reanalyze_extracted_text(request):
    """重新分析已识别的文本"""
    try:
        data = json.loads(request.body)
        result_id = data.get('result_id')
        
        if not result_id:
            return JsonResponse({'error': '缺少result_id参数'}, status=400)
        
        # 获取识别结果
        recognition_result = ImageRecognitionResult.objects.get(id=result_id)
        
        if not recognition_result.extracted_text:
            return JsonResponse({'error': '没有可分析的文本'}, status=400)
        
        # 重新分析文本
        from image_recognition.medical_ocr import MedicalOCR
        ocr = MedicalOCR()
        
        analysis = ocr.analyze_medical_text(recognition_result.extracted_text)
        
        # 更新分析结果
        recognition_result.analysis_result = json.dumps(analysis, ensure_ascii=False)
        recognition_result.save()
        
        return JsonResponse({
            'success': True,
            'message': '文本重新分析完成',
            'analysis_result': analysis
        })
        
    except ImageRecognitionResult.DoesNotExist:
        return JsonResponse({'error': '识别结果不存在'}, status=404)
    except Exception as e:
        print(f"重新分析文本错误: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)
