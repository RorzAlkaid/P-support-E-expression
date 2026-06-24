from django import forms
from django.contrib import admin

from .models import (
    AccountProfile,
    AIChatConfig,
    Appointment,
    Article,
    AssessmentRecord,
    AssessmentScale,
    Counselor,
    CrisisAlert,
    ExternalResourceSource,
    InvitationCode,
    MoodEntry,
    ResourceFetchLog,
    ResourceViewLog,
    StudentProfile,
    TreeHolePost,
    TreeHoleReply,
)

admin.site.site_header = '大学生心理支持与情绪表达平台后台管理'
admin.site.site_title = '心理支持平台后台'
admin.site.index_title = '数据管理中心'


class AIChatConfigAdminForm(forms.ModelForm):
    api_key = forms.CharField(
        label='API Key',
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='新增或更换 Key 时填写；编辑已有配置时留空会保留原 Key。',
    )

    class Meta:
        model = AIChatConfig
        fields = '__all__'

    def clean_api_key(self):
        value = self.cleaned_data.get('api_key', '').strip()
        if value:
            return value
        if self.instance and self.instance.pk:
            return self.instance.api_key
        return ''


@admin.register(AIChatConfig)
class AIChatConfigAdmin(admin.ModelAdmin):
    form = AIChatConfigAdminForm
    list_display = (
        'enabled',
        'configured_status',
        'provider_summary',
        'api_url',
        'model',
        'timeout',
        'auto_detect_model',
        'updated_at',
    )
    readonly_fields = (
        'configured_status',
        'api_key_masked',
        'provider_summary',
        'effective_model_preview',
        'normalized_api_url_preview',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('运行状态', {
            'fields': (
                'enabled',
                'configured_status',
                'api_key_masked',
                'provider_summary',
                'effective_model_preview',
                'normalized_api_url_preview',
            )
        }),
        ('连接配置', {
            'fields': (
                'provider',
                'api_key',
                'api_url',
                'auto_detect_model',
                'model',
                'timeout',
            ),
            'description': '服务商选择“自动检测”时，后台会根据 API 地址识别 OpenAI、DeepSeek 或自定义兼容接口；启用自动检测模型时会自动填入该服务商的默认模型。',
        }),
        ('记录时间', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_queryset(self, request):
        from .views import ensure_ai_chat_config_record

        ensure_ai_chat_config_record()
        return super().get_queryset(request)

    def has_add_permission(self, request):
        from .views import ensure_ai_chat_config_record

        ensure_ai_chat_config_record()
        if AIChatConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    @admin.display(description='配置状态')
    def configured_status(self, obj):
        if not obj:
            return '未保存'
        if not obj.enabled:
            return '已停用'
        return '已配置 API Key' if obj.api_key else '未配置 API Key'

    @admin.display(description='脱敏 API Key')
    def api_key_masked(self, obj):
        return obj.masked_api_key or '未填写'

    @admin.display(description='识别服务商')
    def provider_summary(self, obj):
        if not obj:
            return '未保存'
        return obj.get_effective_provider_display()

    @admin.display(description='生效模型')
    def effective_model_preview(self, obj):
        return obj.effective_model if obj else '未保存'

    @admin.display(description='规范化 API 地址')
    def normalized_api_url_preview(self, obj):
        return obj.api_url if obj else '未保存'


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ('creator', 'target_role', 'code', 'is_locked', 'used_by', 'used_at', 'updated_at')
    list_filter = ('target_role', 'is_locked')
    search_fields = ('creator__username', 'creator__first_name', 'code')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_no', 'user', 'college', 'grade', 'privacy_consent', 'created_at')
    list_filter = ('college', 'grade', 'privacy_consent')
    search_fields = ('student_no', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(Counselor)
class CounselorAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'source', 'is_active', 'fetched_at', 'updated_at')
    list_filter = ('is_active', 'source')
    search_fields = ('name', 'title', 'specialties', 'source', 'external_url')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'source', 'is_published', 'fetched_at', 'updated_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'summary', 'tags', 'external_url')


@admin.register(ExternalResourceSource)
class ExternalResourceSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'category', 'enabled', 'last_fetched_at')
    list_filter = ('enabled', 'organization', 'category')
    search_fields = ('name', 'url', 'organization')


@admin.register(ResourceFetchLog)
class ResourceFetchLogAdmin(admin.ModelAdmin):
    list_display = ('source', 'status', 'articles_created', 'articles_updated', 'created_at')
    list_filter = ('status', 'source')
    search_fields = ('source__name', 'message')


@admin.register(ResourceViewLog)
class ResourceViewLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'article_title', 'article_category', 'article_source', 'created_at')
    list_filter = ('article_category', 'article_source')
    search_fields = ('student__student_no', 'student__user__username', 'article_title', 'article_source')


@admin.register(AssessmentScale)
class AssessmentScaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'max_score', 'updated_at')
    search_fields = ('name', 'code')


@admin.register(AssessmentRecord)
class AssessmentRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'scale', 'score', 'risk_level', 'created_at')
    list_filter = ('risk_level', 'scale')
    search_fields = ('student__student_no', 'student__user__username', 'scale__name')


@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ('student', 'mood', 'intensity', 'sleep_quality', 'is_private', 'created_at')
    list_filter = ('mood', 'is_private')
    search_fields = ('student__student_no', 'note', 'pressure_sources')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'counselor', 'scheduled_at', 'topic', 'status')
    list_filter = ('status', 'counselor')
    search_fields = ('student__student_no', 'counselor__name', 'topic')


@admin.register(CrisisAlert)
class CrisisAlertAdmin(admin.ModelAdmin):
    list_display = ('student', 'level', 'trigger', 'handled', 'created_at')
    list_filter = ('level', 'handled')
    search_fields = ('student__student_no', 'trigger', 'handler_note')


class TreeHoleReplyInline(admin.TabularInline):
    model = TreeHoleReply
    extra = 0


@admin.register(TreeHolePost)
class TreeHolePostAdmin(admin.ModelAdmin):
    list_display = ('category', 'student', 'mood_tag', 'is_anonymous', 'risk_flag', 'support_count', 'created_at')
    list_filter = ('category', 'is_anonymous', 'risk_flag')
    search_fields = ('content', 'mood_tag', 'student__student_no', 'student__user__username')
    inlines = [TreeHoleReplyInline]


@admin.register(TreeHoleReply)
class TreeHoleReplyAdmin(admin.ModelAdmin):
    list_display = ('post', 'responder_name', 'is_counselor_reply', 'created_at')
    list_filter = ('is_counselor_reply',)
    search_fields = ('content', 'responder_name')
