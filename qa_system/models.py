from django.db import models
from django.contrib.auth.models import User
import json

class QAData(models.Model):
    """问答数据模型"""
    question = models.TextField(verbose_name="问题")
    answer = models.TextField(verbose_name="答案")
    source = models.CharField(max_length=100, verbose_name="来源", default="丁香医生")
    category = models.CharField(max_length=100, verbose_name="分类", blank=True)
    keywords = models.TextField(verbose_name="关键词", blank=True, help_text="JSON格式存储")
    processed_question = models.TextField(verbose_name="处理后的问题", blank=True)
    processed_answer = models.TextField(verbose_name="处理后的答案", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'qa_data'
        verbose_name = '问答数据'
        verbose_name_plural = '问答数据'
        
    def __str__(self):
        return f"{self.question[:50]}..."
    
    def get_keywords_list(self):
        """获取关键词列表"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except:
                return []
        return []
    
    def set_keywords_list(self, keywords_list):
        """设置关键词列表"""
        self.keywords = json.dumps(keywords_list, ensure_ascii=False)

class Document(models.Model):
    """文档模型"""
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    file_path = models.FileField(upload_to='documents/', verbose_name="文件路径", blank=True)
    file_type = models.CharField(max_length=50, verbose_name="文件类型", blank=True)
    pos_tags = models.TextField(verbose_name="词性标注结果", blank=True)
    entities = models.TextField(verbose_name="实体识别结果", blank=True)
    summary = models.TextField(verbose_name="文档摘要", blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="上传者", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'documents'
        verbose_name = '文档'
        verbose_name_plural = '文档'
        
    def __str__(self):
        return self.title

class ChatSession(models.Model):
    """聊天会话模型"""
    session_id = models.CharField(max_length=100, unique=True, verbose_name="会话ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'chat_sessions'
        verbose_name = '聊天会话'
        verbose_name_plural = '聊天会话'
        
    def __str__(self):
        return f"会话 {self.session_id}"

class ChatMessage(models.Model):
    """聊天消息模型"""
    MESSAGE_TYPES = [
        ('text', '文本'),
        ('image', '图像'),
    ]
    
    SENDER_TYPES = [
        ('user', '用户'),
        ('bot', '机器人'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, verbose_name="会话", related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES, verbose_name="发送者类型")
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, verbose_name="消息类型", default='text')
    content = models.TextField(verbose_name="消息内容")
    image = models.ImageField(upload_to='chat_images/', verbose_name="图像", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="时间戳")
    
    class Meta:
        db_table = 'chat_messages'
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'
        ordering = ['timestamp']
        
    def __str__(self):
        return f"{self.sender_type}: {self.content[:30]}..."

class TextMiningResult(models.Model):
    """文本挖掘结果模型"""
    dataset_name = models.CharField(max_length=200, verbose_name="数据集名称")
    file_path = models.FileField(upload_to='datasets/', verbose_name="数据集文件")
    clustering_result = models.TextField(verbose_name="聚类结果", blank=True)
    tsne_plot = models.ImageField(upload_to='plots/', verbose_name="t-SNE图", blank=True, null=True)
    wordcloud_plots = models.TextField(verbose_name="词云图路径", blank=True, help_text="JSON格式存储多个词云图路径")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'text_mining_results'
        verbose_name = '文本挖掘结果'
        verbose_name_plural = '文本挖掘结果'
        
    def __str__(self):
        return self.dataset_name

class CrawlerLog(models.Model):
    """爬虫日志模型"""
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    task_name = models.CharField(max_length=100, verbose_name="任务名称")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="状态", default='running')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    total_count = models.IntegerField(default=0, verbose_name="总数量")
    success_count = models.IntegerField(default=0, verbose_name="成功数量")
    error_log = models.TextField(blank=True, verbose_name="错误日志")
    
    class Meta:
        db_table = 'crawler_logs'
        verbose_name = '爬虫日志'
        verbose_name_plural = '爬虫日志'
        
    def __str__(self):
        return f"{self.task_name} - {self.status}"

class ImageRecognitionResult(models.Model):
    """图像识别结果模型"""
    image_name = models.CharField(max_length=200, verbose_name="图像名称")
    image_file = models.ImageField(upload_to='recognition_images/', verbose_name="图像文件", blank=True, null=True)
    extracted_text = models.TextField(verbose_name="识别出的文本", blank=True)
    recognition_details = models.TextField(verbose_name="识别详情", blank=True, help_text="JSON格式存储OCR详细结果")
    analysis_result = models.TextField(verbose_name="分析结果", blank=True, help_text="JSON格式存储文本分析结果")
    processing_time = models.FloatField(verbose_name="处理时间(秒)", default=0.0)
    confidence_score = models.FloatField(verbose_name="平均置信度", default=0.0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'image_recognition_results'
        verbose_name = '图像识别结果'
        verbose_name_plural = '图像识别结果'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.image_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_recognition_details(self):
        """获取识别详情"""
        if self.recognition_details:
            try:
                return json.loads(self.recognition_details)
            except:
                return {}
        return {}
    
    def get_analysis_result(self):
        """获取分析结果"""
        if self.analysis_result:
            try:
                return json.loads(self.analysis_result)
            except:
                return {}
        return {}
