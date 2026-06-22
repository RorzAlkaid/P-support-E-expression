from rest_framework import serializers

from .models import (
    Appointment,
    Article,
    AssessmentRecord,
    AssessmentScale,
    Counselor,
    CrisisAlert,
    ExternalResourceSource,
    MoodEntry,
    ResourceFetchLog,
    StudentProfile,
    TreeHolePost,
    TreeHoleReply,
)


class StudentProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'name',
            'username',
            'student_no',
            'college',
            'grade',
            'privacy_consent',
            'pressure_sources',
            'preferred_topics',
            'created_at',
        ]


class CounselorSerializer(serializers.ModelSerializer):
    match_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = Counselor
        fields = [
            'id',
            'name',
            'title',
            'specialties',
            'qualifications',
            'available_slots',
            'avatar_color',
            'source',
            'external_url',
            'fetched_at',
            'is_active',
            'match_score',
        ]


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'source',
            'category',
            'summary',
            'content',
            'tags',
            'external_url',
            'fetched_at',
            'is_published',
            'updated_at',
        ]


class ExternalResourceSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalResourceSource
        fields = ['id', 'name', 'url', 'organization', 'category', 'tags', 'enabled', 'last_fetched_at']


class ResourceFetchLogSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)

    class Meta:
        model = ResourceFetchLog
        fields = ['id', 'source', 'source_name', 'status', 'message', 'articles_created', 'articles_updated', 'created_at']


class AssessmentScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentScale
        fields = ['id', 'name', 'code', 'description', 'questions', 'max_score']


class AssessmentRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    scale_name = serializers.CharField(source='scale.name', read_only=True)

    class Meta:
        model = AssessmentRecord
        fields = [
            'id',
            'student',
            'student_name',
            'scale',
            'scale_name',
            'score',
            'risk_level',
            'answers',
            'suggestion',
            'created_at',
        ]


class MoodEntrySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)

    class Meta:
        model = MoodEntry
        fields = [
            'id',
            'student',
            'student_name',
            'mood',
            'intensity',
            'sleep_quality',
            'pressure_sources',
            'note',
            'is_private',
            'created_at',
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    counselor_name = serializers.CharField(source='counselor.name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'student',
            'student_name',
            'counselor',
            'counselor_name',
            'scheduled_at',
            'topic',
            'status',
            'confidential_note',
            'created_at',
        ]


class CrisisAlertSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)

    class Meta:
        model = CrisisAlert
        fields = [
            'id',
            'student',
            'student_name',
            'level',
            'trigger',
            'handled',
            'handler_note',
            'created_at',
        ]


class TreeHoleReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeHoleReply
        fields = ['id', 'post', 'responder_name', 'content', 'is_counselor_reply', 'created_at']


class TreeHolePostSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    replies = TreeHoleReplySerializer(many=True, read_only=True)

    class Meta:
        model = TreeHolePost
        fields = [
            'id',
            'student',
            'student_name',
            'category',
            'content',
            'mood_tag',
            'is_anonymous',
            'support_count',
            'risk_flag',
            'replies',
            'created_at',
        ]

    def get_student_name(self, obj):
        if obj.is_anonymous or not obj.student:
            return '匿名同学'
        return obj.student.user.get_full_name() or obj.student.user.username
