from collections import Counter
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Avg, Count
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


def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'role': user_role(user),
    }


def normalize_list_value(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or '').replace('，', ',').replace('、', ',').split(',') if item.strip()]


class StudentProfileViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = StudentProfile.objects.select_related('user').all()
    serializer_class = StudentProfileSerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return []
        return super().get_permissions()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class CounselorViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = Counselor.objects.all()
    serializer_class = CounselorSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class ArticleViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = Article.objects.filter(is_published=True)
    serializer_class = ArticleSerializer
    pagination_class = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class ExternalResourceSourceViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = ExternalResourceSource.objects.all()
    serializer_class = ExternalResourceSourceSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护外部资源源站。')


class ResourceFetchLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResourceFetchLog.objects.select_related('source').all()
    serializer_class = ResourceFetchLogSerializer


class AssessmentScaleViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = AssessmentScale.objects.all()
    serializer_class = AssessmentScaleSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class AssessmentRecordViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = AssessmentRecord.objects.select_related('student__user', 'scale').all()
    serializer_class = AssessmentRecordSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class MoodEntryViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = MoodEntry.objects.select_related('student__user').all()
    serializer_class = MoodEntrySerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class AppointmentViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = Appointment.objects.select_related('student__user', 'counselor').all()
    serializer_class = AppointmentSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        role = user_role(request.user)
        if request.method == 'PATCH' and role in [AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN]:
            return
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and role != AccountProfile.ROLE_ADMIN:
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
        if request.method in ['GET', 'HEAD', 'OPTIONS'] and role in [AccountProfile.ROLE_TEACHER, AccountProfile.ROLE_ADMIN]:
            return
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and role == AccountProfile.ROLE_ADMIN:
            return
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            self.permission_denied(request, message='只有教师和管理员可以查看预警数据。')
        else:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class TreeHolePostViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = TreeHolePost.objects.select_related('student__user').prefetch_related('replies').all()
    serializer_class = TreeHolePostSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


class TreeHoleReplyViewSet(viewsets.ModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = TreeHoleReply.objects.select_related('post').all()
    serializer_class = TreeHoleReplySerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ['GET', 'HEAD', 'OPTIONS'] and user_role(request.user) != AccountProfile.ROLE_ADMIN:
            self.permission_denied(request, message='只有管理员可以维护基础数据。')


def get_request_student(request):
    if request.user.is_authenticated and user_role(request.user) == AccountProfile.ROLE_STUDENT:
        profile, _ = StudentProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'student_no': request.user.username,
                'privacy_consent': True,
                'pressure_sources': [],
                'preferred_topics': [],
            },
        )
        return profile
    return StudentProfile.objects.select_related('user').first()


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
def module_center(request):
    role = user_role(request.user)
    student = get_request_student(request) if role == AccountProfile.ROLE_STUDENT else None
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

# Create your views here.
