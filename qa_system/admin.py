from django.contrib import admin
from .models import QAData, Document, ChatSession, ChatMessage, TextMiningResult, CrawlerLog

@admin.register(QAData)
class QADataAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_preview', 'source', 'category', 'created_at')
    list_filter = ('source', 'category', 'created_at')
    search_fields = ('question', 'answer', 'category')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50
    
    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = '问题预览'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'file_type', 'uploaded_by', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at',)
    
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'user', 'created_at', 'message_count')
    list_filter = ('created_at',)
    search_fields = ('session_id',)
    readonly_fields = ('created_at', 'updated_at')
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = '消息数量'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender_type', 'message_type', 'content_preview', 'timestamp')
    list_filter = ('sender_type', 'message_type', 'timestamp')
    search_fields = ('content',)
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:30] + "..." if len(obj.content) > 30 else obj.content
    content_preview.short_description = '内容预览'

@admin.register(TextMiningResult)
class TextMiningResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'dataset_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('dataset_name',)
    readonly_fields = ('created_at',)

@admin.register(CrawlerLog)
class CrawlerLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'status', 'total_count', 'success_count', 'start_time', 'end_time')
    list_filter = ('status', 'start_time')
    search_fields = ('task_name',)
    readonly_fields = ('start_time', 'end_time')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑现有对象
            return self.readonly_fields + ('task_name',)
        return self.readonly_fields
