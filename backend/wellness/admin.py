from django.contrib import admin

from .models import (
    Appointment,
    Article,
    AssessmentRecord,
    AssessmentScale,
    Counselor,
    CrisisAlert,
    MoodEntry,
    StudentProfile,
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_no', 'user', 'college', 'grade', 'privacy_consent', 'created_at')
    list_filter = ('college', 'grade', 'privacy_consent')
    search_fields = ('student_no', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(Counselor)
class CounselorAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'title', 'specialties')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'source', 'is_published', 'updated_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'summary', 'tags')


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

# Register your models here.
