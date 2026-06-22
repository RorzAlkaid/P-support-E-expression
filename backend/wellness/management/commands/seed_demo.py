from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from wellness.models import (
    Appointment,
    Article,
    AssessmentRecord,
    AssessmentScale,
    Counselor,
    CrisisAlert,
    MoodEntry,
    StudentProfile,
)


class Command(BaseCommand):
    help = '创建心理支持平台演示数据'

    def handle(self, *args, **options):
        user, _ = User.objects.update_or_create(
            username='student001',
            defaults={
                'first_name': '林',
                'last_name': '安',
                'email': 'student001@example.com',
            },
        )
        user.set_password('student001')
        user.save()

        student, _ = StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                'student_no': '2026001',
                'college': '信息学院',
                'grade': '大二',
                'privacy_consent': True,
                'pressure_sources': ['学业压力', '睡眠', '人际关系'],
                'preferred_topics': ['情绪调节', '压力管理'],
            },
        )

        counselors = [
            {
                'name': '周明雅',
                'title': '国家二级心理咨询师',
                'specialties': ['情绪调节', '压力管理', '睡眠'],
                'qualifications': '长期服务高校心理中心，擅长短程焦点咨询。',
                'available_slots': ['周一 14:00', '周三 10:00', '周五 16:00'],
                'avatar_color': '#d85d73',
            },
            {
                'name': '陈亦然',
                'title': '心理健康教育讲师',
                'specialties': ['人际关系', '自我认同', '生涯困惑'],
                'qualifications': '关注学生发展议题，擅长关系支持与成长陪伴。',
                'available_slots': ['周二 09:00', '周四 15:30'],
                'avatar_color': '#5f8fb9',
            },
            {
                'name': '许清和',
                'title': '临床心理方向督导师',
                'specialties': ['危机干预', '焦虑', '抑郁情绪'],
                'qualifications': '具备危机评估与转介经验，可处理较高风险个案。',
                'available_slots': ['周一 19:00', '周三 18:30'],
                'avatar_color': '#8f6bb8',
            },
        ]
        counselor_objects = []
        for item in counselors:
            counselor, _ = Counselor.objects.update_or_create(name=item['name'], defaults=item)
            counselor_objects.append(counselor)

        articles = [
            {
                'title': '当压力很满时，先把问题拆小',
                'source': '校园心理中心',
                'category': '压力管理',
                'summary': '用三步拆解法降低学业与生活压力的压迫感。',
                'content': '识别压力来源，区分可控与不可控，再为可控任务设置一个今天能完成的小动作。',
                'tags': ['压力管理', '自助练习'],
            },
            {
                'title': '睡前十分钟情绪整理',
                'source': '心理健康科普库',
                'category': '情绪调节',
                'summary': '通过呼吸、命名情绪和短句记录，帮助大脑结束一天。',
                'content': '睡前记录一个情绪词、一个身体感受和一个明天可以照顾自己的行动。',
                'tags': ['睡眠', '情绪调节'],
            },
            {
                'title': '什么时候应该主动求助',
                'source': '校园心理中心',
                'category': '求助指南',
                'summary': '当痛苦持续、功能受损或出现自伤想法时，应尽快联系专业支持。',
                'content': '求助不是软弱，而是把自己从单独承受中带出来。紧急风险请立即联系学校或当地援助渠道。',
                'tags': ['求助', '危机干预'],
            },
        ]
        for item in articles:
            Article.objects.update_or_create(title=item['title'], defaults=item)

        scale, _ = AssessmentScale.objects.update_or_create(
            code='SAS-DEMO',
            defaults={
                'name': '焦虑状态自评简表',
                'description': '用于演示的非诊断性量表，结果仅作为心理支持参考。',
                'questions': [
                    {'title': '最近一周我经常感到紧张', 'options': [0, 1, 2, 3]},
                    {'title': '我难以放松下来', 'options': [0, 1, 2, 3]},
                    {'title': '我担心事情会变糟', 'options': [0, 1, 2, 3]},
                ],
                'max_score': 30,
            },
        )

        now = timezone.now()
        moods = [
            ('平静', 6, 7, ['睡眠']),
            ('焦虑', 4, 5, ['学业压力']),
            ('疲惫', 3, 4, ['睡眠', '学业压力']),
            ('放松', 7, 7, ['人际关系']),
            ('低落', 4, 5, ['人际关系']),
            ('稳定', 6, 6, ['学业压力']),
            ('有力量', 8, 7, ['自我成长']),
        ]
        MoodEntry.objects.filter(student=student).delete()
        for index, (mood, intensity, sleep, sources) in enumerate(moods):
            entry = MoodEntry.objects.create(
                student=student,
                mood=mood,
                intensity=intensity,
                sleep_quality=sleep,
                pressure_sources=sources,
                note=f'第 {index + 1} 天情绪记录，用于趋势展示。',
                is_private=True,
            )
            MoodEntry.objects.filter(id=entry.id).update(created_at=now - timedelta(days=6 - index))

        AssessmentRecord.objects.update_or_create(
            student=student,
            scale=scale,
            defaults={
                'score': 18,
                'risk_level': 'medium',
                'answers': [2, 1, 2],
                'suggestion': '建议继续观察一周情绪变化，并预约一次支持性咨询。',
            },
        )

        Appointment.objects.update_or_create(
            student=student,
            counselor=counselor_objects[0],
            scheduled_at=now + timedelta(days=2, hours=3),
            defaults={
                'topic': '学业压力与睡眠调整',
                'status': 'confirmed',
                'confidential_note': '学生希望讨论近期备考压力。',
            },
        )

        CrisisAlert.objects.update_or_create(
            student=student,
            trigger='连续三天情绪强度低于 5，且量表风险为中',
            defaults={
                'level': 'warning',
                'handled': False,
                'handler_note': '',
            },
        )

        admin, created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
        if created:
            admin.set_password('admin123456')
            admin.save()

        self.stdout.write(self.style.SUCCESS('演示数据已创建：admin/admin123456，student001/student001'))
