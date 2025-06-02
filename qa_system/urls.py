from django.urls import path
from . import views

app_name = 'qa_system'

urlpatterns = [
    # 主页
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 聊天接口
    path('chat/text/', views.chat_text, name='chat_text'),
    path('chat/image/', views.chat_image, name='chat_image'),
    path('chat/history/', views.get_chat_history, name='chat_history'),
    
    # 文档处理
    path('document/upload/', views.upload_document, name='upload_document'),
    path('document/download/', views.download_analysis_result, name='download_analysis'),
    
    # 爬虫
    path('crawler/start/', views.start_crawler, name='start_crawler'),
    
    # 数据管理
    path('data/process/', views.process_data, name='process_data'),
    path('data/stats/', views.get_data_stats, name='get_data_stats'),
    path('data/clear/', views.clear_all_data, name='clear_all_data'),
    
    # 文本挖掘相关URL
    path('mining/upload/', views.upload_dataset, name='upload_dataset'),
    path('mining/run/', views.run_text_mining, name='run_text_mining'),
    path('mining/result/<int:result_id>/', views.get_mining_result, name='get_mining_result'),
    path('mining/results/', views.list_mining_results, name='list_mining_results'),
    
    # 图像识别相关URL
    path('image/upload/', views.upload_medical_image, name='upload_medical_image'),
    path('image/result/<int:result_id>/', views.get_recognition_result, name='get_recognition_result'),
    path('image/results/', views.list_recognition_results, name='list_recognition_results'),
    path('image/reanalyze/', views.reanalyze_extracted_text, name='reanalyze_extracted_text'),
    
    # 系统监控相关URL
    path('system/stats/', views.system_stats, name='system_stats'),
    path('system/health/', views.health_check, name='health_check'),
] 