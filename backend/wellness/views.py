from collections import Counter

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

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
from .serializers import (
    AppointmentSerializer,
    ArticleSerializer,
    AssessmentRecordSerializer,
    AssessmentScaleSerializer,
    CounselorSerializer,
    CrisisAlertSerializer,
    MoodEntrySerializer,
    StudentProfileSerializer,
)


def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'is_staff': user.is_staff,
    }


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related('user').all()
    serializer_class = StudentProfileSerializer


class CounselorViewSet(viewsets.ModelViewSet):
    queryset = Counselor.objects.all()
    serializer_class = CounselorSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(is_published=True)
    serializer_class = ArticleSerializer


class AssessmentScaleViewSet(viewsets.ModelViewSet):
    queryset = AssessmentScale.objects.all()
    serializer_class = AssessmentScaleSerializer


class AssessmentRecordViewSet(viewsets.ModelViewSet):
    queryset = AssessmentRecord.objects.select_related('student__user', 'scale').all()
    serializer_class = AssessmentRecordSerializer


class MoodEntryViewSet(viewsets.ModelViewSet):
    queryset = MoodEntry.objects.select_related('student__user').all()
    serializer_class = MoodEntrySerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related('student__user', 'counselor').all()
    serializer_class = AppointmentSerializer


class CrisisAlertViewSet(viewsets.ModelViewSet):
    queryset = CrisisAlert.objects.select_related('student__user').all()
    serializer_class = CrisisAlertSerializer


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

    if not username or not password:
        return Response({'detail': '请输入账号和密码。'}, status=status.HTTP_400_BAD_REQUEST)
    if password != confirm_password:
        return Response({'detail': '两次输入的密码不一致。'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'detail': '该账号已存在，请直接登录。'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    user.first_name = username
    user.save()

    if role == '学生':
        StudentProfile.objects.create(
            user=user,
            student_no=username,
            privacy_consent=True,
            pressure_sources=[],
            preferred_topics=[],
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
