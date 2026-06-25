from django import forms
from django.contrib import admin
from django.utils import timezone

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
    Tag,
    TagSuggestion,
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

    PROVIDER_MODELS = [
        ('OpenAI', [
            ('gpt-4o', 'gpt-4o'),
            ('gpt-4o-mini', 'gpt-4o-mini'),
            ('gpt-4-turbo', 'gpt-4-turbo'),
            ('gpt-4', 'gpt-4'),
            ('gpt-3.5-turbo', 'gpt-3.5-turbo'),
        ]),
        ('DeepSeek', [
            ('deepseek-chat', 'deepseek-chat'),
            ('deepseek-v4-flash', 'deepseek-v4-flash'),
            ('deepseek-reasoner', 'deepseek-reasoner'),
            ('deepseek-v4', 'deepseek-v4'),
        ]),
        ('自定义', [
            ('__custom__', '自定义模型...'),
        ]),
    ]

    model_select = forms.ChoiceField(
        label='模型选择',
        required=False,
        choices=[(v, l) for _, opts in PROVIDER_MODELS for v, l in opts],
        help_text='从预设列表中选择模型，或选择"自定义模型..."手动输入。',
    )
    model_custom = forms.CharField(
        label='自定义模型名称',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '输入自定义模型名称'}),
        help_text='仅在选择"自定义模型..."时需要填写。',
    )

    class Meta:
        model = AIChatConfig
        exclude = ('model', 'singleton_key')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化 model 相关字段
        if self.instance and self.instance.pk:
            current_model = self.instance.model or ''
            known_models = [v for _, opts in self.PROVIDER_MODELS for v, _ in opts if v != '__custom__']
            if current_model in known_models:
                self.fields['model_select'].initial = current_model
                self.fields['model_custom'].initial = ''
            else:
                self.fields['model_select'].initial = '__custom__'
                self.fields['model_custom'].initial = current_model
        # provider 已经是带 choices 的字段，直接渲染为下拉框

    def clean_api_key(self):
        value = self.cleaned_data.get('api_key', '').strip()
        if value:
            return value
        if self.instance and self.instance.pk:
            return self.instance.api_key
        return ''

    def clean(self):
        cleaned = super().clean()
        model_select = cleaned.get('model_select', '')
        model_custom = cleaned.get('model_custom', '').strip()

        if model_select == '__custom__':
            if not model_custom:
                self.add_error('model_custom', '请输入自定义模型名称。')
            cleaned['model'] = model_custom
        elif model_select:
            cleaned['model'] = model_select
        else:
            cleaned['model'] = ''
        return cleaned

    class Media:
        js = ('admin/js/ai_chat_model_switcher.js',)


@admin.register(AIChatConfig)
class AIChatConfigAdmin(admin.ModelAdmin):
    form = AIChatConfigAdminForm
    list_display = (
        'id',
        'enabled',
        'configured_status',
        'provider_summary',
        'effective_model_preview',
        'api_url',
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
                'model_select',
                'model_custom',
                'timeout',
            ),
            'description': (
                '选择服务商后可从预设模型中选取；选择”自定义模型...”可手动输入。'
                '启用「自动检测模型」将根据服务商自动选择默认模型，忽略手动选择。'
            ),
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
        return True

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # 当 auto_detect_model 启用时，模型选择字段变灰提示
        return form

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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_preview', 'is_active', 'usage_count', 'created_by', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'is_active'),
            'description': '标签名称需简洁明了，用于文章、咨询师等内容的分类与检索。',
        }),
        ('关联信息', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )
    actions = ['activate_tags', 'deactivate_tags']

    @admin.display(description='描述')
    def description_preview(self, obj):
        if not obj.description:
            return '-'
        return obj.description[:40] + '…' if len(obj.description) > 40 else obj.description

    @admin.display(description='引用次数')
    def usage_count(self, obj):
        from .models import Article, Counselor
        total = 0
        try:
            total += Article.objects.filter(tags__icontains=obj.name).count()
        except Exception:
            pass
        try:
            total += Counselor.objects.filter(specialties__icontains=obj.name).count()
        except Exception:
            pass
        return total

    @admin.action(description='批量启用所选标签')
    def activate_tags(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'已成功启用 {updated} 个标签。')

    @admin.action(description='批量停用所选标签')
    def deactivate_tags(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'已成功停用 {updated} 个标签。')


@admin.register(TagSuggestion)
class TagSuggestionAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'target_type', 'target_id', 'status', 'proposer', 'reviewer', 'created_at', 'reviewed_at')
    list_filter = ('status', 'target_type')
    search_fields = ('tag_name', 'proposer__username', 'reviewer__username', 'review_note')
    readonly_fields = ('created_at', 'reviewed_at')
    fieldsets = (
        ('提议信息', {
            'fields': ('tag_name', 'target_type', 'target_id', 'proposer'),
            'description': '用户提交的标签提议，审核通过后将自动添加到对应目标。',
        }),
        ('审核信息', {
            'fields': ('status', 'reviewer', 'review_note', 'reviewed_at'),
        }),
        ('时间信息', {
            'fields': ('created_at',),
        }),
    )
    actions = ['approve_suggestions', 'reject_suggestions']

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == TagSuggestion.STATUS_APPROVED:
                obj.reviewer = request.user
                obj.reviewed_at = timezone.now()
                Tag.objects.get_or_create(
                    name=obj.tag_name,
                    defaults={'created_by': obj.proposer or request.user},
                )
                from .views import apply_tag_to_target
                apply_tag_to_target(obj.target_type, obj.target_id, obj.tag_name)
            elif obj.status == TagSuggestion.STATUS_REJECTED:
                obj.reviewer = request.user
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.action(description='批量通过所选提议')
    def approve_suggestions(self, request, queryset):
        from .views import apply_tag_to_target
        count = 0
        for suggestion in queryset.filter(status=TagSuggestion.STATUS_PENDING):
            suggestion.status = TagSuggestion.STATUS_APPROVED
            suggestion.reviewer = request.user
            suggestion.reviewed_at = timezone.now()
            suggestion.save()
            Tag.objects.get_or_create(
                name=suggestion.tag_name,
                defaults={'created_by': suggestion.proposer or request.user},
            )
            apply_tag_to_target(suggestion.target_type, suggestion.target_id, suggestion.tag_name)
            count += 1
        self.message_user(request, f'已通过 {count} 条标签提议，对应标签已添加到目标。')

    @admin.action(description='批量驳回所选提议')
    def reject_suggestions(self, request, queryset):
        updated = queryset.filter(status=TagSuggestion.STATUS_PENDING).update(
            status=TagSuggestion.STATUS_REJECTED,
            reviewer=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f'已驳回 {updated} 条标签提议。')


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
