import csv
import io
import json
import os
import re
import secrets
import string
import zipfile
from collections import Counter
from datetime import timedelta
from html import escape
from urllib import error as urlerror
from urllib import request as urlrequest

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Avg
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

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
from .serializers import (
    AppointmentSerializer,
    ArticleSerializer,
    AssessmentRecordSerializer,
    AssessmentScaleSerializer,
    CounselorSerializer,
    CrisisAlertSerializer,
    ExternalResourceSourceSerializer,
    MoodEntrySerializer,
    ResourceFetchLogSerializer,
    ResourceViewLogSerializer,
    StudentProfileSerializer,
    TagSerializer,
    TagSuggestionSerializer,
    TreeHolePostSerializer,
    TreeHoleReplySerializer,
)


RISK_KEYWORDS = ['自伤', '自杀', '不想活', '结束生命', '伤害自己', '活不下去']
PASSWORD_RULE = re.compile(r'^(?=.*[a-z])(?=.*[A-Z]).{8,}$')
FOUR_DIGIT_YEAR_RULE = re.compile(r'^\d{4}$')
INVITATION_CODE_LENGTH = 16
INVITATION_RANDOM_CHARS = string.ascii_letters + string.digits + string.punctuation
MAX_AI_CHAT_MESSAGES = 12
MAX_AI_CHAT_CONTENT_LENGTH = 1200
AI_CHAT_CONFIG_PATH = settings.BASE_DIR / 'ai_chat_config.json'
AI_CHAT_COMPLETION_PATH = '/chat/completions'
AI_CHAT_SYSTEM_PROMPT = """
你是大学生心理支持与情绪表达平台中的 AI 倾听助手。请用温和、尊重、简洁的中文回应学生。
你的目标是陪伴、澄清感受、帮助学生做短时情绪调节，并在合适时鼓励寻求学校心理中心、辅导员或专业咨询师帮助。
不要做医学诊断，不要承诺替代专业治疗。遇到自伤、自杀、伤害他人或现实紧急危险时，必须明确建议立刻联系身边可信任的人、学校心理中心、当地急救或紧急援助渠道。
回复结构尽量包含：先接住情绪，再给出一到三个可执行的小步骤，最后用一个开放问题邀请继续表达。
""".strip()


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session auth with CSRF exemption for API views.

    NOTE: CSRF protection is bypassed for API convenience during SPA development.
    In production with the frontend served from the same domain, ensure Django's
    CSRF middleware is properly configured and the frontend includes the CSRF token
    in request headers. Alternatively, switch to TokenAuthentication for API views.
    """
    def enforce_csrf(self, request):
        return


ROLE_MAP = {
    '学生': AccountProfile.ROLE_STUDENT,
    '心理老师': AccountProfile.ROLE_TEACHER,
    '教师': AccountProfile.ROLE_TEACHER,
    '管理员': AccountProfile.ROLE_ADMIN,
}

READ_METHODS = ('GET', 'HEAD', 'OPTIONS')
TEACHER_ADMIN_ROLES = (AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN)
INVITATION_ROLE_LABELS = {
    AccountProfile.ROLE_TEACHER: '教师',
    AccountProfile.ROLE_ADMIN: '管理员',
}
INSIGHT_EXPORT_HEADERS = ['section', 'student', 'mood', 'intensity', 'sleep_quality', 'pressure_sources', 'note', 'scale', 'score', 'risk_level', 'suggestion', 'counselor', 'topic', 'status', 'scheduled_at', 'confidential_note', 'level', 'trigger', 'handled', 'handler_note', 'created_at']
INSIGHT_EXCEL_HEADER_LABELS = {
    'section': '模块',
    'student': '学生',
    'mood': '情绪',
    'intensity': '情绪强度',
    'sleep_quality': '睡眠质量',
    'pressure_sources': '压力来源',
    'note': '日记',
    'scale': '量表',
    'score': '得分',
    'risk_level': '风险等级',
    'suggestion': '建议',
    'counselor': '咨询师',
    'topic': '咨询主题',
    'status': '预约状态',
    'scheduled_at': '预约时间',
    'confidential_note': '保密备注',
    'level': '预警等级',
    'trigger': '触发原因',
    'handled': '处理状态',
    'handler_note': '处理记录',
    'created_at': '创建时间',
}


def user_role(user):
    if not user.is_authenticated:
        return 'guest'
    if user.is_superuser or user.is_staff:
        return AccountProfile.ROLE_ADMIN
    profile = getattr(user, 'account_profile', None)
    return profile.role if profile else AccountProfile.ROLE_STUDENT


def normalize_role(value):
    return ROLE_MAP.get(value, value if value in [
        AccountProfile.ROLE_STUDENT,
        AccountProfile.ROLE_TEACHER,
        AccountProfile.ROLE_ADMIN,
    ] else AccountProfile.ROLE_STUDENT)


def allowed_invitation_targets(user):
    role = user_role(user)
    if role == AccountProfile.ROLE_ADMIN:
        return [AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN]
    if role == AccountProfile.ROLE_TEACHER:
        return [AccountProfile.ROLE_TEACHER]
    return []


def serialize_invitation_codes(user):
    targets = allowed_invitation_targets(user)
    if not targets:
        return []
    records = {
        item.target_role: item
        for item in InvitationCode.objects.filter(creator=user, target_role__in=targets)
    }
    return [
        {
            'target_role': target,
            'target_label': INVITATION_ROLE_LABELS[target],
            'code': records[target].code if target in records else '',
            'is_locked': bool(records[target].is_locked) if target in records else False,
            'is_used': bool(records[target].used_at) if target in records else False,
            'updated_at': records[target].updated_at if target in records else None,
        }
        for target in targets
    ]


def generate_invitation_code():
    while True:
        code = ''.join(secrets.choice(INVITATION_RANDOM_CHARS) for _ in range(INVITATION_CODE_LENGTH))
        if not InvitationCode.objects.filter(code=code).exists():
            return code


def validate_invitation_for_role(target_role, code):
    if target_role == AccountProfile.ROLE_STUDENT:
        return ''
    normalized_code = str(code or '').strip()
    role_label = INVITATION_ROLE_LABELS.get(target_role, '该身份')
    if not normalized_code:
        return f'注册{role_label}账号需要填写对应的邀请码。'
    if not InvitationCode.objects.filter(target_role=target_role, code=normalized_code, is_locked=True, used_at__isnull=True).exists():
        return f'{role_label}邀请码无效，请确认后重新输入。'
    return ''


def get_usable_invitation(target_role, code):
    if target_role == AccountProfile.ROLE_STUDENT:
        return None, ''
    normalized_code = str(code or '').strip()
    role_label = INVITATION_ROLE_LABELS.get(target_role, '该身份')
    if not normalized_code:
        return None, f'注册{role_label}账号需要填写对应的邀请码。'
    invitation = (
        InvitationCode.objects.select_for_update()
        .filter(target_role=target_role, code=normalized_code, is_locked=True, used_at__isnull=True)
        .first()
    )
    if not invitation:
        return None, f'{role_label}邀请码无效，请确认后重新输入。'
    return invitation, ''


def require_write_role(request, allow_admin=True):
    role = user_role(request.user)
    allowed = [AccountProfile.ROLE_STUDENT]
    if allow_admin:
        allowed.append(AccountProfile.ROLE_ADMIN)
    if role not in allowed:
        return Response({'detail': '当前角色只能浏览数据，不能新增或修改。'}, status=status.HTTP_403_FORBIDDEN)
    return None


def can_view_alert_details(user):
    return user_role(user) in TEACHER_ADMIN_ROLES


def can_view_insights(user):
    return True


def can_export_insights(user):
    return user_role(user) in TEACHER_ADMIN_ROLES


def ensure_teacher_counselor(user, **defaults):
    if user_role(user) != AccountProfile.ROLE_TEACHER:
        return None
    counselor_defaults = {
        'name': user.get_full_name() or user.username,
        'title': defaults.get('title') or '心理教师',
        'specialties': defaults.get('specialties') or [],
        'qualifications': defaults.get('qualifications') or '',
        'available_slots': defaults.get('available_slots') or [],
        'avatar_color': defaults.get('avatar_color') or '#d85d73',
        'source': '教师个人资料',
        'is_active': True,
    }
    counselor, created = Counselor.objects.get_or_create(user=user, defaults=counselor_defaults)
    if not created and not counselor.is_active:
        counselor.is_active = True
        counselor.save(update_fields=['is_active', 'updated_at'])
    return counselor


def serialize_user(user):
    counselor = ensure_teacher_counselor(user)
    return {
        'id': user.id,
        'username': user.username,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'role': user_role(user),
        'counselor_profile': CounselorSerializer(counselor).data if counselor else None,
    }


def normalize_list_value(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or '').replace('，', ',').replace('、', ',').split(',') if item.strip()]


def normalize_tag_name(value):
    return str(value or '').strip()[:30]


def normalize_tag_key(value):
    return normalize_tag_name(value).casefold()


def unique_tag_list(values):
    result = []
    seen = set()
    for value in normalize_list_value(values):
        name = normalize_tag_name(value)
        key = normalize_tag_key(name)
        if name and key not in seen:
            result.append(name)
            seen.add(key)
    return result


def append_unique_tag(values, tag_name):
    tags = unique_tag_list(values)
    key = normalize_tag_key(tag_name)
    if key and key not in {normalize_tag_key(item) for item in tags}:
        tags.append(normalize_tag_name(tag_name))
    return tags


def risk_level_tag(risk_level):
    return {
        AssessmentRecord.RISK_HIGH: '高风险',
        AssessmentRecord.RISK_MEDIUM: '中风险',
        AssessmentRecord.RISK_LOW: '低风险',
    }.get(risk_level, risk_level)


def student_tag_counter(student):
    counter = Counter()
    if not student:
        return counter
    for tag in list(student.pressure_sources or []) + list(student.preferred_topics or []):
        counter[normalize_tag_key(tag)] += 2
    for entry in MoodEntry.objects.filter(student=student)[:20]:
        for tag in list(entry.pressure_sources or []) + [entry.mood]:
            counter[normalize_tag_key(tag)] += 3
    for record in AssessmentRecord.objects.select_related('scale').filter(student=student)[:20]:
        for tag in list(record.result_tags or []) + list(getattr(record.scale, 'tags', []) or []) + [risk_level_tag(record.risk_level)]:
            counter[normalize_tag_key(tag)] += 2
    for post in TreeHolePost.objects.filter(student=student)[:20]:
        for tag in [post.mood_tag, post.category]:
            counter[normalize_tag_key(tag)] += 3
    for appointment in Appointment.objects.filter(student=student)[:20]:
        for tag in list(appointment.topic_tags or []) + [appointment.topic]:
            counter[normalize_tag_key(tag)] += 1
    counter.pop('', None)
    return counter


def score_related_tags(student_tags, target_tags):
    target_lookup = {}
    for tag in target_tags or []:
        key = normalize_tag_key(tag)
        if key:
            target_lookup[key] = normalize_tag_name(tag)
    related_keys = [key for key in target_lookup if key in student_tags]
    related_score = sum(student_tags[key] for key in related_keys)
    related_tags = [target_lookup[key] for key in sorted(related_keys, key=lambda item: student_tags[item], reverse=True)]
    return related_score, related_tags


def current_student_for_recommendation(request):
    if user_role(request.user) == AccountProfile.ROLE_STUDENT:
        return get_request_student(request)
    student_id = request.query_params.get('student')
    if student_id:
        return StudentProfile.objects.filter(id=student_id).first()
    return None


def matches_search(text_values, query):
    query = str(query or '').strip().casefold()
    if not query:
        return True
    return query in ' '.join(str(value or '') for value in text_values).casefold()


def attach_counselor_relation(counselor, student_tags):
    related_score, related_tags = score_related_tags(student_tags, counselor.specialties or [])
    counselor.related_score = related_score
    counselor.related_tags = related_tags
    counselor.match_score = min(72 + related_score * 8, 99)
    return counselor


def attach_article_relation(article, student_tags):
    related_score, related_tags = score_related_tags(student_tags, article.tags or [])
    article.related_score = related_score
    article.related_tags = related_tags
    return article


def apply_tag_to_target(target_type, target_id, tag_name):
    tag_name = normalize_tag_name(tag_name)
    if target_type == TagSuggestion.TARGET_ARTICLE:
        article = Article.objects.filter(id=target_id).first()
        if not article:
            return False
        article.tags = append_unique_tag(article.tags, tag_name)
        article.save(update_fields=['tags', 'updated_at'])
        return True
    if target_type == TagSuggestion.TARGET_COUNSELOR:
        counselor = Counselor.objects.filter(id=target_id).first()
        if not counselor:
            return False
        counselor.specialties = append_unique_tag(counselor.specialties, tag_name)
        counselor.save(update_fields=['specialties', 'updated_at'])
        return True
    return False


def validate_common_identity(username=None, name=None, email=None, password=None, student_no=None, grade=None, pressure_sources=None):
    if username is not None and len(username) > 20:
        return '账号不能超过20个字符。'
    if name is not None and len(name) > 12:
        return '姓名不能超过12个字符。'
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return '邮箱格式不正确。'
    if password is not None and not PASSWORD_RULE.match(password):
        return '密码至少8位，且必须同时包含大写字母和小写字母。'
    if student_no is not None and len(student_no) > 50:
        return '学号不能超过50个字符。'
    if grade is not None and grade and not FOUR_DIGIT_YEAR_RULE.match(grade):
        return '年级只能输入四位数字。'
    for item in pressure_sources or []:
        if len(item) > 20:
            return '压力来源每项不能超过20个字。'
    return ''


def parse_future_datetime(value):
    parsed = parse_datetime(str(value or ''))
    if not parsed:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def is_read_request(request):
    return request.method in READ_METHODS


class AdminManagedModelViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    admin_write_message = '只有管理员可以维护基础数据。'

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not is_read_request(request) and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message=self.admin_write_message)


class StudentProfileViewSet(AdminManagedModelViewSet):
    queryset = StudentProfile.objects.select_related('user').all()
    serializer_class = StudentProfileSerializer
    pagination_class = None

    def get_permissions(self):
        if is_read_request(self.request):
            return []
        return super().get_permissions()


class CounselorViewSet(AdminManagedModelViewSet):
    queryset = Counselor.objects.all()
    serializer_class = CounselorSerializer

    def list(self, request, *args, **kwargs):
        student_tags = student_tag_counter(current_student_for_recommendation(request))
        query = request.query_params.get('q', '')
        counselors = [
            attach_counselor_relation(counselor, student_tags)
            for counselor in Counselor.objects.filter(is_active=True)
            if matches_search([counselor.name, counselor.title, counselor.qualifications, counselor.specialties], query)
        ]
        counselors.sort(key=lambda item: (item.related_score, item.updated_at), reverse=True)
        return Response(CounselorSerializer(counselors, many=True).data)


class ArticleViewSet(AdminManagedModelViewSet):
    queryset = Article.objects.filter(is_published=True)
    serializer_class = ArticleSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        student_tags = student_tag_counter(current_student_for_recommendation(request))
        query = request.query_params.get('q', '')
        articles = [
            attach_article_relation(article, student_tags)
            for article in Article.objects.filter(is_published=True)
            if matches_search([article.title, article.source, article.category, article.summary, article.tags], query)
        ]
        articles.sort(key=lambda item: (item.related_score, item.updated_at), reverse=True)
        return Response(ArticleSerializer(articles, many=True).data)


class TagViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not is_read_request(request) and user_role(request.user) not in TEACHER_ADMIN_ROLES:
            self.permission_denied(request, message='只有教师和管理员可以维护标签。')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)


class TagSuggestionViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = TagSuggestion.objects.select_related('proposer', 'reviewer').all()
    serializer_class = TagSuggestionSerializer

    def list(self, request, *args, **kwargs):
        role = user_role(request.user)
        queryset = self.get_queryset()
        if role not in TEACHER_ADMIN_ROLES:
            if not request.user.is_authenticated:
                return Response([])
            queryset = queryset.filter(proposer=request.user)
        return Response(TagSuggestionSerializer(queryset, many=True).data)

    def create(self, request, *args, **kwargs):
        tag_name = normalize_tag_name(request.data.get('tag_name') or request.data.get('name'))
        target_type = request.data.get('target_type')
        target_id = request.data.get('target_id')
        if not tag_name or target_type not in [TagSuggestion.TARGET_ARTICLE, TagSuggestion.TARGET_COUNSELOR] or not target_id:
            return Response({'detail': '请填写标签名称、目标类型和目标编号。'}, status=status.HTTP_400_BAD_REQUEST)

        existing = Tag.objects.filter(name__iexact=tag_name, is_active=True).first()
        if existing or user_role(request.user) in TEACHER_ADMIN_ROLES:
            tag = existing or Tag.objects.create(name=tag_name, created_by=request.user if request.user.is_authenticated else None)
            if not apply_tag_to_target(target_type, target_id, tag.name):
                return Response({'detail': '目标不存在。'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'status': 'applied', 'tag': TagSerializer(tag).data})

        suggestion = TagSuggestion.objects.create(
            proposer=request.user if request.user.is_authenticated else None,
            tag_name=tag_name,
            target_type=target_type,
            target_id=target_id,
        )
        return Response(TagSuggestionSerializer(suggestion).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        if user_role(request.user) not in TEACHER_ADMIN_ROLES:
            return Response({'detail': '只有教师和管理员可以审核标签。'}, status=status.HTTP_403_FORBIDDEN)
        suggestion = self.get_object()
        next_status = request.data.get('status')
        if next_status not in [TagSuggestion.STATUS_APPROVED, TagSuggestion.STATUS_REJECTED]:
            return Response({'detail': '审核状态只能是 approved 或 rejected。'}, status=status.HTTP_400_BAD_REQUEST)
        suggestion.status = next_status
        suggestion.reviewer = request.user
        suggestion.review_note = request.data.get('review_note') or ''
        suggestion.reviewed_at = timezone.now()
        if next_status == TagSuggestion.STATUS_APPROVED:
            tag, _ = Tag.objects.get_or_create(
                name=suggestion.tag_name,
                defaults={'created_by': request.user if request.user.is_authenticated else None},
            )
            if not apply_tag_to_target(suggestion.target_type, suggestion.target_id, tag.name):
                return Response({'detail': '目标不存在。'}, status=status.HTTP_404_NOT_FOUND)
        suggestion.save()
        return Response(TagSuggestionSerializer(suggestion).data)


class ExternalResourceSourceViewSet(AdminManagedModelViewSet):
    admin_write_message = '只有管理员可以维护外部资源源站。'
    queryset = ExternalResourceSource.objects.all()
    serializer_class = ExternalResourceSourceSerializer


class ResourceFetchLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResourceFetchLog.objects.select_related('source').all()
    serializer_class = ResourceFetchLogSerializer


class AssessmentScaleViewSet(AdminManagedModelViewSet):
    queryset = AssessmentScale.objects.all()
    serializer_class = AssessmentScaleSerializer


class AssessmentRecordViewSet(AdminManagedModelViewSet):
    queryset = AssessmentRecord.objects.select_related('student__user', 'scale').all()
    serializer_class = AssessmentRecordSerializer


class MoodEntryViewSet(AdminManagedModelViewSet):
    queryset = MoodEntry.objects.select_related('student__user').all()
    serializer_class = MoodEntrySerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = Appointment.objects.select_related('student__user', 'counselor').all()
    serializer_class = AppointmentSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        role = user_role(request.user)
        if request.method == 'PATCH' and role in TEACHER_ADMIN_ROLES:
            return
        if not is_read_request(request) and role != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')

    def partial_update(self, request, *args, **kwargs):
        role = user_role(request.user)
        if role == AccountProfile.ROLE_TEACHER:
            status_value = request.data.get('status')
            allowed_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
            if set(request.data.keys()) != {'status'} or status_value not in allowed_statuses:
                return Response({'detail': '教师只能修改预约状态。'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)


class CrisisAlertViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = CrisisAlert.objects.select_related('student__user').all()
    serializer_class = CrisisAlertSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        role = user_role(request.user)
        if is_read_request(request) and role in TEACHER_ADMIN_ROLES:
            return
        if not is_read_request(request) and role == AccountProfile.ROLE_ADMIN:
            return
        if is_read_request(request):
            self.permission_denied(request, message='只有教师和管理员可以查看预警数据。')
        else:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class TreeHolePostViewSet(AdminManagedModelViewSet):
    queryset = TreeHolePost.objects.select_related('student__user').prefetch_related('replies').all()
    serializer_class = TreeHolePostSerializer


class TreeHoleReplyViewSet(AdminManagedModelViewSet):
    queryset = TreeHoleReply.objects.select_related('post').all()
    serializer_class = TreeHoleReplySerializer


def get_student_for_user(user):
    if user.is_authenticated and user_role(user) == AccountProfile.ROLE_STUDENT:
        profile, _ = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'student_no': user.username,
                'privacy_consent': True,
                'pressure_sources': [],
                'preferred_topics': [],
            },
        )
        return profile
    return StudentProfile.objects.select_related('user').first()


def get_request_student(request):
    return get_student_for_user(request.user)


def contains_risk_text(text):
    return any(keyword in (text or '') for keyword in RISK_KEYWORDS)


def create_alert_if_needed(student, trigger, text, level='warning'):
    if student and contains_risk_text(text):
        CrisisAlert.objects.create(
            student=student,
            level=level,
            trigger=trigger,
            handled=False,
        )


def normalize_ai_messages(raw_messages):
    if not isinstance(raw_messages, list):
        return []

    cleaned_messages = []
    for item in raw_messages[-MAX_AI_CHAT_MESSAGES:]:
        role = item.get('role') if isinstance(item, dict) else ''
        content = item.get('content') if isinstance(item, dict) else ''
        content = str(content or '').strip()
        if role not in ['user', 'assistant'] or not content:
            continue
        cleaned_messages.append({
            'role': role,
            'content': content[:MAX_AI_CHAT_CONTENT_LENGTH],
        })
    return cleaned_messages


def read_ai_chat_config():
    if not AI_CHAT_CONFIG_PATH.exists():
        return {}
    try:
        with AI_CHAT_CONFIG_PATH.open('r', encoding='utf-8') as config_file:
            config = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        return {}
    return config if isinstance(config, dict) else {}


def safe_ai_chat_timeout(value):
    try:
        return int(value or settings.AI_CHAT_TIMEOUT)
    except (TypeError, ValueError):
        return int(settings.AI_CHAT_TIMEOUT)


def parse_boolean(value, default=False):
    if value in [True, False]:
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in ['1', 'true', 'yes', 'on']:
        return True
    if normalized in ['0', 'false', 'no', 'off']:
        return False
    return default


def build_ai_chat_config_defaults(config):
    api_url = normalize_ai_chat_api_url(config.get('api_url') or settings.AI_CHAT_API_URL)
    provider_choices = {choice[0] for choice in AIChatConfig.PROVIDER_CHOICES}
    requested_provider = config.get('provider') or AIChatConfig.PROVIDER_AUTO
    if requested_provider not in provider_choices:
        requested_provider = AIChatConfig.PROVIDER_AUTO
    provider = (
        AIChatConfig.detect_provider(api_url)
        if requested_provider == AIChatConfig.PROVIDER_AUTO
        else requested_provider
    )
    defaults = {
        'enabled': parse_boolean(config.get('enabled'), True),
        'provider': provider,
        'api_url': api_url,
        'model': normalize_ai_chat_model(config.get('model') or settings.AI_CHAT_MODEL, api_url),
        'auto_detect_model': parse_boolean(config.get('auto_detect_model'), False),
        'timeout': safe_ai_chat_timeout(config.get('timeout')),
    }
    if config.get('api_key'):
        defaults['api_key'] = str(config['api_key']).strip()
    return defaults


def ensure_ai_chat_config_record():
    admin_config = AIChatConfig.objects.filter(singleton_key=1).first()
    if admin_config:
        return admin_config

    legacy_config = read_ai_chat_config()
    if not legacy_config:
        return None

    defaults = build_ai_chat_config_defaults(legacy_config)
    admin_config, _ = AIChatConfig.objects.update_or_create(
        singleton_key=1,
        defaults=defaults,
    )
    return admin_config


def write_ai_chat_config(config):
    defaults = build_ai_chat_config_defaults(config)
    AIChatConfig.objects.update_or_create(singleton_key=1, defaults=defaults)


def masked_api_key(value):
    value = str(value or '')
    if not value:
        return ''
    if len(value) <= 8:
        return '*' * len(value)
    return f'{value[:4]}****{value[-4:]}'


def normalize_ai_chat_api_url(api_url):
    return AIChatConfig.normalize_api_url(api_url or settings.AI_CHAT_API_URL)


def normalize_ai_chat_model(model, api_url):
    value = str(model or '').strip()
    provider = AIChatConfig.detect_provider(api_url)
    if value.lower() == 'auto':
        value = ''
    if provider == AIChatConfig.PROVIDER_DEEPSEEK and value == 'deepseek-v4':
        return AIChatConfig.default_model_for_provider(AIChatConfig.PROVIDER_DEEPSEEK)
    return value or AIChatConfig.default_model_for_provider(provider)


def effective_ai_chat_config():
    admin_config = ensure_ai_chat_config_record()
    if admin_config:
        api_url = normalize_ai_chat_api_url(admin_config.api_url)
        provider = admin_config.effective_provider
        model = admin_config.effective_model
        timeout = safe_ai_chat_timeout(admin_config.timeout)
        fallback_key = settings.AI_CHAT_API_KEY or os.environ.get('OPENAI_API_KEY', '')
        api_key = admin_config.api_key or fallback_key
        source = 'django_admin' if admin_config.api_key else ('env' if api_key else '')
        if not admin_config.enabled:
            source = 'disabled'
        enabled = bool(admin_config.enabled)
    else:
        api_key = settings.AI_CHAT_API_KEY or os.environ.get('OPENAI_API_KEY', '')
        api_url = normalize_ai_chat_api_url(settings.AI_CHAT_API_URL)
        model = normalize_ai_chat_model(settings.AI_CHAT_MODEL, api_url)
        timeout = safe_ai_chat_timeout(settings.AI_CHAT_TIMEOUT)
        provider = AIChatConfig.detect_provider(api_url)
        source = 'env' if api_key else ''
        enabled = True

    return {
        'enabled': enabled,
        'api_key': api_key,
        'api_url': api_url,
        'model': model,
        'timeout': timeout,
        'source': source,
        'provider': provider,
        'provider_label': dict(AIChatConfig.PROVIDER_CHOICES).get(provider, '自定义兼容接口'),
        'auto_detect_model': bool(admin_config.auto_detect_model) if admin_config else False,
    }


def serialize_ai_chat_config(config=None):
    config = config or effective_ai_chat_config()
    return {
        'enabled': bool(config.get('enabled', True)),
        'configured': bool(config.get('api_key')),
        'api_key_masked': masked_api_key(config.get('api_key')),
        'api_url': config.get('api_url') or settings.AI_CHAT_API_URL,
        'model': config.get('model') or settings.AI_CHAT_MODEL,
        'timeout': config.get('timeout') or settings.AI_CHAT_TIMEOUT,
        'source': config.get('source') or '',
        'provider': config.get('provider') or AIChatConfig.detect_provider(config.get('api_url')),
        'provider_label': config.get('provider_label') or '',
        'auto_detect_model': bool(config.get('auto_detect_model')),
    }


def call_ai_chat_completion(messages):
    config = effective_ai_chat_config()
    if not config.get('enabled', True):
        return None, 'AI 倾听服务已停用，请联系管理员开启后再使用。'

    api_key = config['api_key']
    if not api_key:
        return None, 'AI 对话服务未配置 API Key，请联系管理员在 AI 倾听页面完成配置。'

    payload = {
        'model': config['model'],
        'messages': [
            {'role': 'system', 'content': AI_CHAT_SYSTEM_PROMPT},
            *messages,
        ],
        'temperature': 0.7,
        'max_tokens': 800,
    }
    data = json.dumps(payload).encode('utf-8')
    request = urlrequest.Request(
        config['api_url'],
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urlrequest.urlopen(request, timeout=config['timeout']) as response:
            result = json.loads(response.read().decode('utf-8'))
    except urlerror.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')[:500]
        return None, f'AI 服务返回错误：{exc.code} {detail}'
    except (urlerror.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, f'AI 服务连接失败：{exc}'

    choices = result.get('choices') or []
    answer = choices[0].get('message', {}).get('content') if choices else ''
    answer = str(answer or '').strip()
    if not answer:
        return None, 'AI 服务没有返回有效内容，请稍后再试。'
    return answer, ''


@api_view(['GET', 'PATCH'])
@authentication_classes([CsrfExemptSessionAuthentication])
def ai_chat_config(request):
    if user_role(request.user) != AccountProfile.ROLE_ADMIN:
        return Response({'detail': '只有管理员可以配置 AI 对话 API Key。'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(serialize_ai_chat_config())

    current_config = effective_ai_chat_config()
    api_url = (request.data.get('api_url') or settings.AI_CHAT_API_URL).strip()
    model = (request.data.get('model') or settings.AI_CHAT_MODEL).strip()
    timeout_value = request.data.get('timeout') or settings.AI_CHAT_TIMEOUT
    api_key = (request.data.get('api_key') or '').strip()
    provider = request.data.get('provider') or current_config.get('provider') or AIChatConfig.PROVIDER_AUTO
    enabled = request.data.get('enabled', current_config.get('enabled', True))
    auto_detect_model = request.data.get('auto_detect_model', current_config.get('auto_detect_model', False))

    try:
        timeout_value = int(timeout_value)
    except (TypeError, ValueError):
        return Response({'detail': '超时时间必须是数字。'}, status=status.HTTP_400_BAD_REQUEST)

    if not api_url.startswith(('http://', 'https://')):
        return Response({'detail': 'API 地址必须以 http:// 或 https:// 开头。'}, status=status.HTTP_400_BAD_REQUEST)
    api_url = normalize_ai_chat_api_url(api_url)
    model = normalize_ai_chat_model(model, api_url)
    if not model:
        return Response({'detail': '请填写模型名称。'}, status=status.HTTP_400_BAD_REQUEST)
    if timeout_value < 5 or timeout_value > 120:
        return Response({'detail': '超时时间建议设置在 5 到 120 秒之间。'}, status=status.HTTP_400_BAD_REQUEST)

    next_config = {
        'enabled': enabled,
        'provider': provider,
        'api_url': api_url,
        'model': model,
        'auto_detect_model': auto_detect_model,
        'timeout': timeout_value,
    }
    if api_key:
        next_config['api_key'] = api_key
    elif current_config.get('api_key'):
        next_config['api_key'] = current_config['api_key']

    write_ai_chat_config(next_config)
    return Response({
        'detail': 'AI 对话配置已保存。',
        **serialize_ai_chat_config(),
    })


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def ai_chat(request):
    role = user_role(request.user)
    if role not in [AccountProfile.ROLE_STUDENT, AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN]:
        return Response({'detail': '请登录后再进入 AI 倾听对话。'}, status=status.HTTP_403_FORBIDDEN)

    messages = normalize_ai_messages(request.data.get('messages'))
    if not messages or messages[-1]['role'] != 'user':
        return Response({'detail': '请先输入想和 AI 倾听助手交流的内容。'}, status=status.HTTP_400_BAD_REQUEST)

    latest_text = messages[-1]['content']
    risk_detected = contains_risk_text(latest_text)
    if risk_detected:
        student = get_request_student(request) if role == AccountProfile.ROLE_STUDENT else None
        create_alert_if_needed(student, 'AI 倾听对话中出现高风险表达', latest_text, 'critical')

    answer, error_message = call_ai_chat_completion(messages)
    if error_message:
        return Response({'detail': error_message}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'reply': answer,
        'model': effective_ai_chat_config()['model'],
        'risk_detected': risk_detected,
        'created_at': timezone.localtime().isoformat(),
    })


@api_view(['GET'])
def dashboard_summary(request):
    latest_moods = MoodEntry.objects.select_related('student__user')[:8]
    alerts = CrisisAlert.objects.select_related('student__user').filter(handled=False)[:6]
    appointments = Appointment.objects.select_related('student__user', 'counselor')[:6]

    return Response({
        'stats': {
            'students': StudentProfile.objects.count(),
            'counselors': Counselor.objects.filter(is_active=True).count(),
            'articles': Article.objects.filter(is_published=True).count(),
            'unhandled_alerts': CrisisAlert.objects.filter(handled=False).count(),
            'avg_mood': round(MoodEntry.objects.aggregate(value=Avg('intensity'))['value'] or 0, 1),
            'high_risk_records': AssessmentRecord.objects.filter(risk_level='high').count(),
        },
        'latest_moods': MoodEntrySerializer(latest_moods, many=True).data,
        'alerts': CrisisAlertSerializer(alerts, many=True).data,
        'appointments': AppointmentSerializer(appointments, many=True).data,
    })


@api_view(['GET'])
def mood_trend(request):
    student_id = request.query_params.get('student')
    queryset = MoodEntry.objects.all()
    if student_id:
        queryset = queryset.filter(student_id=student_id)

    queryset = queryset.order_by('created_at')[:30]
    return Response([
        {
            'date': item.created_at.strftime('%m-%d'),
            'mood': item.mood,
            'intensity': item.intensity,
            'sleep_quality': item.sleep_quality,
        }
        for item in queryset
    ])


@api_view(['GET'])
def pressure_distribution(request):
    counter = Counter()
    for entry in MoodEntry.objects.all():
        counter.update(entry.pressure_sources or [])
    for profile in StudentProfile.objects.all():
        counter.update(profile.pressure_sources or [])

    return Response([
        {'name': name, 'value': value}
        for name, value in counter.most_common(8)
    ])


def risk_level_label(value):
    return {
        AssessmentRecord.RISK_LOW: '低',
        AssessmentRecord.RISK_MEDIUM: '中',
        AssessmentRecord.RISK_HIGH: '高',
    }.get(value, value or '未知')


def appointment_status_label(value):
    return {
        Appointment.STATUS_PENDING: '待确认',
        Appointment.STATUS_CONFIRMED: '已确认',
        Appointment.STATUS_FINISHED: '已完成',
        Appointment.STATUS_CANCELLED: '已取消',
    }.get(value, value or '未知')


def crisis_alert_level_label(value):
    return {
        CrisisAlert.LEVEL_NOTICE: '关注',
        CrisisAlert.LEVEL_WARNING: '预警',
        CrisisAlert.LEVEL_CRITICAL: '危机',
    }.get(value, value or '未知')


def build_insight_payload():
    mood_rows = MoodEntry.objects.select_related('student__user').order_by('-created_at')[:200]
    assessment_rows = AssessmentRecord.objects.select_related('student__user', 'scale').order_by('-created_at')[:200]
    appointment_rows = Appointment.objects.select_related('student__user', 'counselor').order_by('-scheduled_at')[:200]
    alert_rows = CrisisAlert.objects.select_related('student__user').order_by('handled', '-created_at')[:120]

    risk_counter = Counter(AssessmentRecord.objects.values_list('risk_level', flat=True))
    appointment_counter = Counter(Appointment.objects.values_list('status', flat=True))
    mood_average = MoodEntry.objects.aggregate(
        intensity=Avg('intensity'),
        sleep_quality=Avg('sleep_quality'),
    )

    pressure_counter = Counter()
    for entry in MoodEntry.objects.all():
        pressure_counter.update(entry.pressure_sources or [])
    for profile in StudentProfile.objects.all():
        pressure_counter.update(profile.pressure_sources or [])

    return {
        'summary': {
            'students': StudentProfile.objects.count(),
            'mood_entries': MoodEntry.objects.count(),
            'assessment_records': AssessmentRecord.objects.count(),
            'appointments': Appointment.objects.count(),
            'unhandled_alerts': CrisisAlert.objects.filter(handled=False).count(),
            'avg_mood': round(mood_average['intensity'] or 0, 1),
            'avg_sleep': round(mood_average['sleep_quality'] or 0, 1),
        },
        'pressure_distribution': [
            {'name': name, 'value': value}
            for name, value in pressure_counter.most_common(10)
        ],
        'risk_distribution': [
            {'name': risk_level_label(key), 'value': value}
            for key, value in risk_counter.items()
        ],
        'appointment_distribution': [
            {'name': appointment_status_label(key), 'value': value}
            for key, value in appointment_counter.items()
        ],
        'mood_rows': [
            {
                'student': item.student.user.get_full_name() or item.student.user.username,
                'mood': item.mood,
                'intensity': item.intensity,
                'sleep_quality': item.sleep_quality,
                'pressure_sources': '、'.join(item.pressure_sources or []),
                'note': item.note,
                'created_at': timezone.localtime(item.created_at).strftime('%Y-%m-%d %H:%M'),
            }
            for item in mood_rows
        ],
        'assessment_rows': [
            {
                'student': item.student.user.get_full_name() or item.student.user.username,
                'scale': item.scale.name,
                'score': item.score,
                'risk_level': risk_level_label(item.risk_level),
                'suggestion': item.suggestion,
                'created_at': timezone.localtime(item.created_at).strftime('%Y-%m-%d %H:%M'),
            }
            for item in assessment_rows
        ],
        'appointment_rows': [
            {
                'student': item.student.user.get_full_name() or item.student.user.username,
                'counselor': item.counselor.name,
                'topic': item.topic,
                'status': appointment_status_label(item.status),
                'scheduled_at': timezone.localtime(item.scheduled_at).strftime('%Y-%m-%d %H:%M'),
                'confidential_note': item.confidential_note,
            }
            for item in appointment_rows
        ],
        'alert_rows': [
            {
                'student': item.student.user.get_full_name() or item.student.user.username,
                'level': item.level,
                'trigger': item.trigger,
                'handled': '已处理' if item.handled else '待跟进',
                'handler_note': item.handler_note,
                'created_at': timezone.localtime(item.created_at).strftime('%Y-%m-%d %H:%M'),
            }
            for item in alert_rows
        ],
    }


def insight_export_rows(payload):
    rows = []
    sections = [
        ('情绪打卡', ['student', 'mood', 'intensity', 'sleep_quality', 'pressure_sources', 'note', 'created_at'], payload['mood_rows']),
        ('心理测评', ['student', 'scale', 'score', 'risk_level', 'suggestion', 'created_at'], payload['assessment_rows']),
        ('咨询预约', ['student', 'counselor', 'topic', 'status', 'scheduled_at', 'confidential_note'], payload['appointment_rows']),
        ('危机预警', ['student', 'level', 'trigger', 'handled', 'handler_note', 'created_at'], payload['alert_rows']),
    ]
    for section, fields, items in sections:
        for item in items:
            row = {'section': section}
            row.update({field: item.get(field, '') for field in fields})
            rows.append(row)
    return rows


def make_xlsx_response(rows, filename):
    def xlsx_cell_value(header, value):
        if header == 'level':
            return crisis_alert_level_label(value)
        return value

    def cell_ref(column_index, row_index):
        name = ''
        column_index += 1
        while column_index:
            column_index, remainder = divmod(column_index - 1, 26)
            name = chr(65 + remainder) + name
        return f'{name}{row_index}'

    sheet_rows = [
        [INSIGHT_EXCEL_HEADER_LABELS[header] for header in INSIGHT_EXPORT_HEADERS],
        *[[xlsx_cell_value(header, row.get(header, '')) for header in INSIGHT_EXPORT_HEADERS] for row in rows],
    ]
    xml_rows = []
    for row_index, row in enumerate(sheet_rows, start=1):
        cells = []
        for column_index, value in enumerate(row):
            cells.append(f'<c r="{cell_ref(column_index, row_index)}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="数据洞察" sheetId="1" r:id="rId1"/></sheets></workbook>'.encode('utf-8')
    rels = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    workbook_rels = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    content_types = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    worksheet = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(xml_rows)}</sheetData></worksheet>'.encode('utf-8')

    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', rels)
        archive.writestr('xl/workbook.xml', workbook)
        archive.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        archive.writestr('xl/worksheets/sheet1.xml', worksheet)

    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@api_view(['GET'])
def insights_dashboard(request):
    if not can_view_insights(request.user):
        return Response({'detail': '当前用户不能查看数据洞察。'}, status=status.HTTP_403_FORBIDDEN)
    return Response(build_insight_payload())


@api_view(['GET'])
def export_insights(request, file_format=None):
    if not can_export_insights(request.user):
        return Response({'detail': '只有教师和管理员可以导出数据洞察。'}, status=status.HTTP_403_FORBIDDEN)

    payload = build_insight_payload()
    rows = insight_export_rows(payload)
    export_format = (file_format or request.query_params.get('file_type') or 'csv').lower()
    filename_base = f'insights-{timezone.localdate():%Y%m%d}'

    if export_format in ['xlsx', 'excel']:
        return make_xlsx_response(rows, f'数据洞察-{timezone.localdate():%Y%m%d}.xlsx')

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.DictWriter(output, fieldnames=INSIGHT_EXPORT_HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename_base}.csv"'
    return response


@api_view(['GET'])
def counselor_recommendations(request):
    student_tags = student_tag_counter(current_student_for_recommendation(request))
    query = request.query_params.get('q', '')
    counselors = [
        attach_counselor_relation(counselor, student_tags)
        for counselor in Counselor.objects.filter(is_active=True)
        if matches_search([counselor.name, counselor.title, counselor.qualifications, counselor.specialties], query)
    ]
    counselors.sort(key=lambda item: (item.related_score, item.match_score, item.updated_at), reverse=True)
    return Response(CounselorSerializer(counselors[:12], many=True).data)


@api_view(['GET'])
def alert_student_detail(request, alert_id):
    if not can_view_alert_details(request.user):
        return Response({'detail': '只有教师和管理员可以查看预警学生详情。'}, status=status.HTTP_403_FORBIDDEN)

    alert = CrisisAlert.objects.select_related('student__user').filter(id=alert_id).first()
    if not alert:
        return Response({'detail': 'Alert not found.'}, status=status.HTTP_404_NOT_FOUND)

    student = alert.student
    moods = MoodEntry.objects.select_related('student__user').filter(student=student)[:30]
    treeholes = TreeHolePost.objects.select_related('student__user').prefetch_related('replies').filter(student=student)[:30]
    records = AssessmentRecord.objects.select_related('student__user', 'scale').filter(student=student)[:30]
    appointments = Appointment.objects.select_related('student__user', 'counselor').filter(student=student)[:30]
    resource_views = ResourceViewLog.objects.select_related('student__user', 'article').filter(student=student)[:30]
    alerts = CrisisAlert.objects.select_related('student__user').filter(student=student)[:30]

    return Response({
        'alert': CrisisAlertSerializer(alert).data,
        'student': StudentProfileSerializer(student).data,
        'moods': MoodEntrySerializer(moods, many=True).data,
        'treeholes': TreeHolePostSerializer(treeholes, many=True).data,
        'records': AssessmentRecordSerializer(records, many=True).data,
        'appointments': AppointmentSerializer(appointments, many=True).data,
        'resource_views': ResourceViewLogSerializer(resource_views, many=True).data,
        'alerts': CrisisAlertSerializer(alerts, many=True).data,
    })


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def record_resource_view(request, article_id):
    if user_role(request.user) != AccountProfile.ROLE_STUDENT:
        return Response({'recorded': False})

    student = get_request_student(request)
    article = Article.objects.filter(id=article_id, is_published=True).first()
    if not student or not article:
        return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

    log = ResourceViewLog.objects.create(
        student=student,
        article=article,
        article_title=article.title,
        article_source=article.source,
        article_category=article.category,
    )
    return Response(ResourceViewLogSerializer(log).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def module_center(request):
    role = user_role(request.user)
    student = get_request_student(request) if role == AccountProfile.ROLE_STUDENT else None
    teacher_counselor = ensure_teacher_counselor(request.user) if role == AccountProfile.ROLE_TEACHER else None
    mood_queryset = MoodEntry.objects.all() if not student else MoodEntry.objects.filter(student=student)
    record_queryset = AssessmentRecord.objects.all() if not student else AssessmentRecord.objects.filter(student=student)
    appointment_queryset = Appointment.objects.all()
    if role not in [AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN]:
        appointment_queryset = appointment_queryset.filter(status__in=[
            Appointment.STATUS_CONFIRMED,
            Appointment.STATUS_FINISHED,
        ])
    alert_queryset = CrisisAlert.objects.filter(handled=False) if role in [AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN] else CrisisAlert.objects.none()
    student_tags = student_tag_counter(student)
    recommended_counselors = [
        attach_counselor_relation(counselor, student_tags)
        for counselor in Counselor.objects.filter(is_active=True)
    ]
    recommended_counselors.sort(key=lambda item: (item.related_score, item.match_score, item.updated_at), reverse=True)
    return Response({
        'student': StudentProfileSerializer(student).data if student else None,
        'teacher_counselor': CounselorSerializer(teacher_counselor).data if teacher_counselor else None,
        'role': role,
        'moods': MoodEntrySerializer(mood_queryset[:12], many=True).data,
        'treeholes': TreeHolePostSerializer(TreeHolePost.objects.prefetch_related('replies')[:8], many=True).data,
        'scales': AssessmentScaleSerializer(AssessmentScale.objects.all(), many=True).data,
        'records': AssessmentRecordSerializer(record_queryset[:12], many=True).data,
        'appointments': AppointmentSerializer(appointment_queryset[:12], many=True).data,
        'counselors': CounselorSerializer(recommended_counselors, many=True).data,
        'alerts': CrisisAlertSerializer(alert_queryset[:6], many=True).data,
    })


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def submit_mood_entry(request):
    denied = require_write_role(request)
    if denied:
        return denied
    student = get_request_student(request)
    if not student:
        return Response({'detail': '请先创建学生账号。'}, status=status.HTTP_400_BAD_REQUEST)

    pressure_sources = normalize_list_value(request.data.get('pressure_sources'))
    validation_error = validate_common_identity(pressure_sources=pressure_sources)
    if validation_error:
        return Response({'detail': validation_error}, status=status.HTTP_400_BAD_REQUEST)

    entry = MoodEntry.objects.create(
        student=student,
        mood=request.data.get('mood') or '平静',
        intensity=int(request.data.get('intensity') or 5),
        sleep_quality=int(request.data.get('sleep_quality') or 5),
        pressure_sources=pressure_sources,
        note=request.data.get('note') or '',
        is_private=bool(request.data.get('is_private', True)),
    )
    create_alert_if_needed(student, '情绪日记中出现高风险表达', entry.note, 'critical')
    if entry.intensity <= 2:
        CrisisAlert.objects.create(student=student, level='notice', trigger='情绪强度低于 3，建议关注。')
    return Response(MoodEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def submit_assessment(request):
    denied = require_write_role(request)
    if denied:
        return denied
    student = get_request_student(request)
    scale = AssessmentScale.objects.filter(id=request.data.get('scale')).first() or AssessmentScale.objects.first()
    answers = request.data.get('answers') or []
    if not student or not scale:
        return Response({'detail': '缺少学生档案或量表。'}, status=status.HTTP_400_BAD_REQUEST)

    score = sum(int(item or 0) for item in answers)
    ratio = score / max(scale.max_score, 1)
    if ratio >= 0.65:
        risk_level = 'high'
        suggestion = '当前得分偏高，建议尽快预约心理老师，并持续记录情绪变化。'
    elif ratio >= 0.35:
        risk_level = 'medium'
        suggestion = '当前存在一定压力信号，建议尝试放松练习并观察一周。'
    else:
        risk_level = 'low'
        suggestion = '当前风险较低，可以继续保持规律作息和自我照顾。'

    record = AssessmentRecord.objects.create(
        student=student,
        scale=scale,
        score=score,
        risk_level=risk_level,
        answers=answers,
        suggestion=suggestion,
        result_tags=unique_tag_list(list(scale.tags or []) + [risk_level_tag(risk_level)]),
    )
    if risk_level == 'high':
        CrisisAlert.objects.create(student=student, level='warning', trigger=f'{scale.name} 得分较高，需要跟进。')
    return Response(AssessmentRecordSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def create_appointment(request):
    denied = require_write_role(request)
    if denied:
        return denied
    student = get_request_student(request)
    counselor = Counselor.objects.filter(id=request.data.get('counselor')).first()
    if not student or not counselor:
        return Response({'detail': '请选择咨询师。'}, status=status.HTTP_400_BAD_REQUEST)

    scheduled_at = request.data.get('scheduled_at')
    if not scheduled_at:
        scheduled_at = timezone.now() + timedelta(days=1)
    else:
        scheduled_at = parse_future_datetime(scheduled_at)
        if not scheduled_at:
            return Response({'detail': '预约时间格式不正确。'}, status=status.HTTP_400_BAD_REQUEST)
        if scheduled_at <= timezone.now():
            return Response({'detail': '预约时间不能早于当前时间。'}, status=status.HTTP_400_BAD_REQUEST)

    appointment = Appointment.objects.create(
        student=student,
        counselor=counselor,
        scheduled_at=scheduled_at,
        topic_tags=unique_tag_list(request.data.get('topic_tags') or request.data.get('topic')),
        topic=request.data.get('topic') or '心理支持预约',
        confidential_note=request.data.get('confidential_note') or '',
    )
    create_alert_if_needed(student, '预约备注中出现高风险表达', appointment.confidential_note, 'critical')
    return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def publish_treehole(request):
    if user_role(request.user) not in [AccountProfile.ROLE_STUDENT, AccountProfile.ROLE_ADMIN]:
        return Response({'detail': '只有学生和管理员可以发布匿名树洞。'}, status=status.HTTP_403_FORBIDDEN)
    student = get_request_student(request)
    content = request.data.get('content') or ''
    if not content.strip():
        return Response({'detail': '请填写想表达的内容。'}, status=status.HTTP_400_BAD_REQUEST)

    post = TreeHolePost.objects.create(
        student=student,
        category=request.data.get('category') or 'other',
        content=content,
        mood_tag=request.data.get('mood_tag') or '',
        is_anonymous=bool(request.data.get('is_anonymous', True)),
        risk_flag=contains_risk_text(content),
    )
    create_alert_if_needed(student, '匿名树洞中出现高风险表达', content, 'critical')
    return Response(TreeHolePostSerializer(post).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def reply_treehole(request, post_id):
    role = user_role(request.user)
    if role not in [AccountProfile.ROLE_STUDENT, AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN]:
        return Response({'detail': '只有学生、心理教师和管理员可以回复匿名树洞。'}, status=status.HTTP_403_FORBIDDEN)
    post = TreeHolePost.objects.filter(id=post_id).first()
    content = request.data.get('content') or ''
    if not post or not content.strip():
        return Response({'detail': '请选择树洞并填写回应。'}, status=status.HTTP_400_BAD_REQUEST)

    reply = TreeHoleReply.objects.create(
        post=post,
        responder_name=request.data.get('responder_name') or ('心理教师' if role == AccountProfile.ROLE_TEACHER else '同伴支持者'),
        content=content,
        is_counselor_reply=role == AccountProfile.ROLE_TEACHER,
    )
    return Response(TreeHoleReplySerializer(reply).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@authentication_classes([CsrfExemptSessionAuthentication])
def teacher_profile(request):
    if user_role(request.user) != AccountProfile.ROLE_TEACHER:
        return Response({'detail': '只有心理教师可以维护个人资料。'}, status=status.HTTP_403_FORBIDDEN)

    counselor = ensure_teacher_counselor(request.user)
    if request.method == 'PATCH':
        name = (request.data.get('name') or '').strip()
        title = (request.data.get('title') or '').strip()
        qualifications = (request.data.get('qualifications') or '').strip()
        specialties = normalize_list_value(request.data.get('specialties'))
        available_slots = normalize_list_value(request.data.get('available_slots'))
        validation_error = validate_common_identity(name=name)
        if validation_error:
            return Response({'detail': validation_error}, status=status.HTTP_400_BAD_REQUEST)

        if name:
            request.user.first_name = name
            request.user.last_name = ''
            request.user.save(update_fields=['first_name', 'last_name'])
            counselor.name = name
        if title:
            counselor.title = title
        counselor.qualifications = qualifications
        counselor.specialties = specialties
        counselor.available_slots = available_slots
        counselor.is_active = True
        counselor.source = '教师个人资料'
        counselor.save()

    return Response(CounselorSerializer(counselor).data)


def serialize_profile_payload(user):
    role = user_role(user)
    student = get_student_for_user(user) if role == AccountProfile.ROLE_STUDENT else None
    counselor = ensure_teacher_counselor(user) if role == AccountProfile.ROLE_TEACHER else None
    return {
        'user': serialize_user(user),
        'student': StudentProfileSerializer(student).data if student else None,
        'teacher_counselor': CounselorSerializer(counselor).data if counselor else None,
        'invitation_codes': serialize_invitation_codes(user),
    }


@api_view(['GET', 'PATCH'])
@authentication_classes([CsrfExemptSessionAuthentication])
def user_profile(request):
    if not request.user.is_authenticated:
        return Response({'detail': '请先登录后再编辑个人资料。'}, status=status.HTTP_403_FORBIDDEN)

    role = user_role(request.user)
    if request.method == 'PATCH':
        name = (request.data.get('name') or '').strip()
        email = (request.data.get('email') or '').strip()
        validation_error = validate_common_identity(name=name, email=email)
        if validation_error:
            return Response({'detail': validation_error}, status=status.HTTP_400_BAD_REQUEST)
        if name:
            request.user.first_name = name
            request.user.last_name = ''
        request.user.email = email
        request.user.save(update_fields=['first_name', 'last_name', 'email'])

        if role == AccountProfile.ROLE_STUDENT:
            student = get_request_student(request)
            grade = (request.data.get('grade') or '').strip()
            pressure_sources = normalize_list_value(request.data.get('pressure_sources'))
            validation_error = validate_common_identity(grade=grade, pressure_sources=pressure_sources)
            if validation_error:
                return Response({'detail': validation_error}, status=status.HTTP_400_BAD_REQUEST)
            student.college = (request.data.get('college') or '').strip()
            student.grade = grade
            student.privacy_consent = bool(request.data.get('privacy_consent', student.privacy_consent))
            student.pressure_sources = pressure_sources
            student.preferred_topics = normalize_list_value(request.data.get('preferred_topics'))
            student.save()
        elif role == AccountProfile.ROLE_TEACHER:
            counselor = ensure_teacher_counselor(request.user)
            title = (request.data.get('title') or '').strip()
            if name:
                counselor.name = name
            if title:
                counselor.title = title
            counselor.specialties = normalize_list_value(request.data.get('specialties'))
            counselor.qualifications = (request.data.get('qualifications') or '').strip()
            counselor.available_slots = normalize_list_value(request.data.get('available_slots'))
            counselor.is_active = True
            counselor.source = '教师个人资料'
            counselor.save()

    return Response(serialize_profile_payload(request.user))


@api_view(['GET', 'POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
def invitation_codes(request):
    if not request.user.is_authenticated:
        return Response({'detail': '请先登录后再维护邀请码。'}, status=status.HTTP_403_FORBIDDEN)

    targets = allowed_invitation_targets(request.user)
    if not targets:
        return Response({'detail': '当前身份不能制作邀请码。'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response({'invitation_codes': serialize_invitation_codes(request.user)})

    target_role = normalize_role(request.data.get('target_role'))
    if target_role not in targets:
        return Response({'detail': '当前身份不能制作该类型的邀请码。'}, status=status.HTTP_403_FORBIDDEN)

    lock_value = request.data.get('is_locked', True)
    if lock_value in [False, 'false', 'False', '0', 0]:
        InvitationCode.objects.filter(creator=request.user, target_role=target_role).update(is_locked=False)
        return Response({'invitation_codes': serialize_invitation_codes(request.user)})

    code = (request.data.get('code') or '').strip() or generate_invitation_code()

    existing = InvitationCode.objects.filter(code=code).exclude(creator=request.user, target_role=target_role).first()
    if existing:
        return Response({'detail': '该邀请码已被使用，请换一个。'}, status=status.HTTP_400_BAD_REQUEST)

    InvitationCode.objects.update_or_create(
        creator=request.user,
        target_role=target_role,
        defaults={
            'code': code,
            'is_locked': True,
            'used_at': None,
            'used_by': None,
        },
    )
    return Response({'invitation_codes': serialize_invitation_codes(request.user)})


@api_view(['GET'])
def current_user(request):
    if not request.user.is_authenticated:
        return Response({'authenticated': False})

    return Response({
        'authenticated': True,
        'user': serialize_user(request.user),
    })


@api_view(['POST'])
@authentication_classes([])
def register_user(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    confirm_password = request.data.get('confirm_password') or ''
    role = request.data.get('role') or '学生'
    target_role = normalize_role(role)
    invitation_code = (request.data.get('invitation_code') or '').strip()
    full_name = (request.data.get('name') or '').strip()
    email = (request.data.get('email') or '').strip()
    student_no = (request.data.get('student_no') or username).strip()
    college = (request.data.get('college') or '').strip()
    grade = (request.data.get('grade') or '').strip()
    privacy_consent = bool(request.data.get('privacy_consent', False))
    pressure_sources = normalize_list_value(request.data.get('pressure_sources'))
    preferred_topics = normalize_list_value(request.data.get('preferred_topics'))
    teacher_title = (request.data.get('teacher_title') or '心理教师').strip()
    teacher_specialties = normalize_list_value(request.data.get('teacher_specialties'))
    teacher_qualifications = (request.data.get('teacher_qualifications') or '').strip()

    if not username or not password:
        return Response({'detail': '请输入账号和密码。'}, status=status.HTTP_400_BAD_REQUEST)
    if password != confirm_password:
        return Response({'detail': '两次输入的密码不一致。'}, status=status.HTTP_400_BAD_REQUEST)
    validation_error = validate_common_identity(
        username=username,
        name=full_name,
        email=email,
        password=password,
        student_no=student_no if target_role == AccountProfile.ROLE_STUDENT else None,
        grade=grade if target_role == AccountProfile.ROLE_STUDENT else None,
        pressure_sources=pressure_sources if target_role == AccountProfile.ROLE_STUDENT else None,
    )
    if validation_error:
        return Response({'detail': validation_error}, status=status.HTTP_400_BAD_REQUEST)
    invitation_error = validate_invitation_for_role(target_role, invitation_code)
    if invitation_error:
        return Response({'detail': invitation_error}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'detail': '该账号已存在，请直接登录。'}, status=status.HTTP_400_BAD_REQUEST)
    if target_role == AccountProfile.ROLE_STUDENT and StudentProfile.objects.filter(student_no=student_no).exists():
        return Response({'detail': '该学号已存在，请检查后重新填写。'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        invitation = None
        if target_role != AccountProfile.ROLE_STUDENT:
            invitation, invitation_error = get_usable_invitation(target_role, invitation_code)
            if invitation_error:
                return Response({'detail': invitation_error}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password, email=email)
        user.first_name = full_name or username
        if target_role == AccountProfile.ROLE_ADMIN:
            user.is_staff = True
        user.save()
        AccountProfile.objects.create(user=user, role=target_role)

        if target_role == AccountProfile.ROLE_STUDENT:
            StudentProfile.objects.create(
                user=user,
                student_no=student_no,
                college=college,
                grade=grade,
                privacy_consent=privacy_consent,
                pressure_sources=pressure_sources,
                preferred_topics=preferred_topics,
            )
        elif target_role == AccountProfile.ROLE_TEACHER:
            ensure_teacher_counselor(
                user,
                title=teacher_title,
                specialties=teacher_specialties,
                qualifications=teacher_qualifications,
            )

        if invitation:
            invitation.used_at = timezone.now()
            invitation.used_by = user
            invitation.save(update_fields=['used_at', 'used_by', 'updated_at'])

    login(request, user)
    return Response({
        'detail': '注册成功，已自动登录。',
        'user': serialize_user(user),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([])
def login_user(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    requested_role = request.data.get('role')

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'detail': '账号或密码错误。'}, status=status.HTTP_400_BAD_REQUEST)
    if requested_role and user_role(user) != normalize_role(requested_role):
        return Response({'detail': '请使用对应身份入口登录该账号。'}, status=status.HTTP_400_BAD_REQUEST)

    login(request, user)
    return Response({
        'detail': '登录成功。',
        'user': serialize_user(user),
    })


@api_view(['POST'])
@authentication_classes([])
def logout_user(request):
    logout(request)
    return Response({'detail': '已退出登录。'})


@api_view(['GET'])
def health_check(request):
    return Response({
        'status': 'ok',
        'service': '大学生心理支持与情绪表达平台 API',
        'time': timezone.localtime().isoformat(),
    })
