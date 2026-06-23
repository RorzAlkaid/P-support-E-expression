from django.contrib import admin

from .models import (
    AccountProfile,
    Appointment,
    Article,
    AssessmentRecord,
    AssessmentScale,
    Counselor,
    CrisisAlert,
    ExternalResourceSource,
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


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


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
