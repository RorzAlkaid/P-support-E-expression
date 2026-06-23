import csv
import io
import zipfile
from collections import Counter
from datetime import timedelta
from html import escape

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Avg
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

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
    TreeHolePostSerializer,
    TreeHoleReplySerializer,
)


RISK_KEYWORDS = ['自伤', '自杀', '不想活', '结束生命', '伤害自己', '活不下去']


class CsrfExemptSessionAuthentication(SessionAuthentication):
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

    def get_permissions(self):
        if is_read_request(self.request):
            return []
        return super().get_permissions()


class CounselorViewSet(AdminManagedModelViewSet):
    queryset = Counselor.objects.all()
    serializer_class = CounselorSerializer


class ArticleViewSet(AdminManagedModelViewSet):
    queryset = Article.objects.filter(is_published=True)
    serializer_class = ArticleSerializer
    pagination_class = None


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
    student_id = request.query_params.get('student')
    student_topics = []
    if student_id:
        student = StudentProfile.objects.filter(id=student_id).first()
        if student:
            student_topics = list(student.pressure_sources or []) + list(student.preferred_topics or [])

    counselors = []
    for counselor in Counselor.objects.filter(is_active=True):
        overlap = set(student_topics) & set(counselor.specialties or [])
        base_score = 72 + len(overlap) * 8
        counselors.append((min(base_score, 98), counselor))

    counselors.sort(key=lambda item: item[0], reverse=True)
    data = []
    for score, counselor in counselors[:6]:
        item = CounselorSerializer(counselor).data
        item['match_score'] = score
        data.append(item)

    return Response(data)


@api_view(['GET'])
def alert_student_detail(request, alert_id):
    if not can_view_alert_details(request.user):
        return Response({'detail': 'Only teachers and admins can view alert student details.'}, status=status.HTTP_403_FORBIDDEN)

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
    return Response({
        'student': StudentProfileSerializer(student).data if student else None,
        'teacher_counselor': CounselorSerializer(teacher_counselor).data if teacher_counselor else None,
        'role': role,
        'moods': MoodEntrySerializer(mood_queryset[:12], many=True).data,
        'treeholes': TreeHolePostSerializer(TreeHolePost.objects.prefetch_related('replies')[:8], many=True).data,
        'scales': AssessmentScaleSerializer(AssessmentScale.objects.all(), many=True).data,
        'records': AssessmentRecordSerializer(record_queryset[:12], many=True).data,
        'appointments': AppointmentSerializer(appointment_queryset[:12], many=True).data,
        'counselors': CounselorSerializer(Counselor.objects.filter(is_active=True), many=True).data,
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

    entry = MoodEntry.objects.create(
        student=student,
        mood=request.data.get('mood') or '平静',
        intensity=int(request.data.get('intensity') or 5),
        sleep_quality=int(request.data.get('sleep_quality') or 5),
        pressure_sources=request.data.get('pressure_sources') or [],
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

    appointment = Appointment.objects.create(
        student=student,
        counselor=counselor,
        scheduled_at=scheduled_at,
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
        if name:
            request.user.first_name = name
            request.user.last_name = ''
        request.user.email = email
        request.user.save(update_fields=['first_name', 'last_name', 'email'])

        if role == AccountProfile.ROLE_STUDENT:
            student = get_request_student(request)
            student.college = (request.data.get('college') or '').strip()
            student.grade = (request.data.get('grade') or '').strip()
            student.privacy_consent = bool(request.data.get('privacy_consent', student.privacy_consent))
            student.pressure_sources = normalize_list_value(request.data.get('pressure_sources'))
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
    if User.objects.filter(username=username).exists():
        return Response({'detail': '该账号已存在，请直接登录。'}, status=status.HTTP_400_BAD_REQUEST)
    if role == '学生' and StudentProfile.objects.filter(student_no=student_no).exists():
        return Response({'detail': '该学号已存在，请检查后重新填写。'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email)
    user.first_name = full_name or username
    if role == '管理员':
        user.is_staff = True
    user.save()
    AccountProfile.objects.create(user=user, role=ROLE_MAP.get(role, AccountProfile.ROLE_STUDENT))

    if role == '学生':
        StudentProfile.objects.create(
            user=user,
            student_no=student_no,
            college=college,
            grade=grade,
            privacy_consent=privacy_consent,
            pressure_sources=pressure_sources,
            preferred_topics=preferred_topics,
        )
    elif ROLE_MAP.get(role) == AccountProfile.ROLE_TEACHER:
        ensure_teacher_counselor(
            user,
            title=teacher_title,
            specialties=teacher_specialties,
            qualifications=teacher_qualifications,
        )

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

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'detail': '账号或密码错误。'}, status=status.HTTP_400_BAD_REQUEST)

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
