from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('students', views.StudentProfileViewSet)
router.register('counselors', views.CounselorViewSet)
router.register('articles', views.ArticleViewSet)
router.register('assessment-scales', views.AssessmentScaleViewSet)
router.register('assessment-records', views.AssessmentRecordViewSet)
router.register('mood-entries', views.MoodEntryViewSet)
router.register('appointments', views.AppointmentViewSet)
router.register('crisis-alerts', views.CrisisAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/me/', views.current_user, name='current-user'),
    path('auth/register/', views.register_user, name='register-user'),
    path('auth/login/', views.login_user, name='login-user'),
    path('auth/logout/', views.logout_user, name='logout-user'),
    path('dashboard/', views.dashboard_summary, name='dashboard-summary'),
    path('mood-trend/', views.mood_trend, name='mood-trend'),
    path('pressure-distribution/', views.pressure_distribution, name='pressure-distribution'),
    path('recommendations/counselors/', views.counselor_recommendations, name='counselor-recommendations'),
    path('health/', views.health_check, name='health-check'),
]
