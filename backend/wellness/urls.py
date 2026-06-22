from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('students', views.StudentProfileViewSet)
router.register('counselors', views.CounselorViewSet)
router.register('articles', views.ArticleViewSet)
router.register('external-resource-sources', views.ExternalResourceSourceViewSet)
router.register('resource-fetch-logs', views.ResourceFetchLogViewSet)
router.register('assessment-scales', views.AssessmentScaleViewSet)
router.register('assessment-records', views.AssessmentRecordViewSet)
router.register('mood-entries', views.MoodEntryViewSet)
router.register('appointments', views.AppointmentViewSet)
router.register('crisis-alerts', views.CrisisAlertViewSet)
router.register('treehole-posts', views.TreeHolePostViewSet)
router.register('treehole-replies', views.TreeHoleReplyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/me/', views.current_user, name='current-user'),
    path('auth/register/', views.register_user, name='register-user'),
    path('auth/login/', views.login_user, name='login-user'),
    path('auth/logout/', views.logout_user, name='logout-user'),
    path('dashboard/', views.dashboard_summary, name='dashboard-summary'),
    path('modules/', views.module_center, name='module-center'),
    path('modules/moods/', views.submit_mood_entry, name='submit-mood-entry'),
    path('modules/assessments/', views.submit_assessment, name='submit-assessment'),
    path('modules/appointments/', views.create_appointment, name='create-appointment'),
    path('modules/treeholes/', views.publish_treehole, name='publish-treehole'),
    path('modules/treeholes/<int:post_id>/reply/', views.reply_treehole, name='reply-treehole'),
    path('mood-trend/', views.mood_trend, name='mood-trend'),
    path('pressure-distribution/', views.pressure_distribution, name='pressure-distribution'),
    path('recommendations/counselors/', views.counselor_recommendations, name='counselor-recommendations'),
    path('health/', views.health_check, name='health-check'),
]
