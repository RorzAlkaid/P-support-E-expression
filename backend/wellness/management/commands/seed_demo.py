from datetime import timedelta
from random import choice, randint

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from wellness.models import (
    AccountProfile,
    Appointment,
    Article,
    AssessmentRecord,
    AssessmentScale,
    Counselor,
    CrisisAlert,
    ExternalResourceSource,
    MoodEntry,
    StudentProfile,
    Tag,
    TreeHolePost,
    TreeHoleReply,
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
        AccountProfile.objects.update_or_create(user=user, defaults={'role': 'student'})

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

        teacher, _ = User.objects.update_or_create(
            username='teacher001',
            defaults={'first_name': '心理', 'last_name': '老师', 'email': 'teacher001@example.com'},
        )
        teacher.set_password('teacher001')
        teacher.save()
        AccountProfile.objects.update_or_create(user=teacher, defaults={'role': 'teacher'})

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

        extra_articles = [
            ('考试周如何安排睡眠', '睡眠支持', ['睡眠', '考试周']),
            ('关系冲突后的自我安顿', '人际关系', ['人际关系', '沟通']),
            ('三分钟呼吸放松练习', '情绪调节', ['呼吸练习', '自助']),
        ]
        for title, category, tags in extra_articles:
            Article.objects.update_or_create(
                title=title,
                defaults={
                    'source': '校园心理中心',
                    'category': category,
                    'summary': f'{title} 的简明自助建议。',
                    'content': '先觉察身体感受，再选择一个可以完成的小行动，必要时主动求助。',
                    'tags': tags,
                },
            )

        external_sources = [
            {
                'name': 'NIMH 心理健康主题',
                'url': 'https://www.nimh.nih.gov/health/topics',
                'organization': 'National Institute of Mental Health',
                'category': '权威科普',
                'tags': ['NIMH', '心理健康', '精神健康'],
            },
            {
                'name': 'CDC 心理健康',
                'url': 'https://www.cdc.gov/mental-health/index.html',
                'organization': 'Centers for Disease Control and Prevention',
                'category': '权威科普',
                'tags': ['CDC', '心理健康', '公共卫生'],
            },
            {
                'name': 'APA 心理主题',
                'url': 'https://www.apa.org/topics',
                'organization': 'American Psychological Association',
                'category': '权威科普',
                'tags': ['APA', '心理学', '心理科普'],
            },
        ]
        for item in external_sources:
            ExternalResourceSource.objects.update_or_create(url=item['url'], defaults=item)

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
        sleep_scale, _ = AssessmentScale.objects.update_or_create(
            code='SLEEP-DEMO',
            defaults={
                'name': '睡眠状态自评简表',
                'description': '用于了解近期睡眠质量的非诊断性量表。',
                'questions': [
                    {'title': '最近我入睡比较困难', 'options': [0, 1, 2, 3]},
                    {'title': '夜间醒来后难以再次入睡', 'options': [0, 1, 2, 3]},
                    {'title': '白天经常感到困倦', 'options': [0, 1, 2, 3]},
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
        for idx, target_scale in enumerate([scale, sleep_scale]):
            AssessmentRecord.objects.update_or_create(
                student=student,
                scale=target_scale,
                score=12 + idx * 5,
                defaults={
                    'risk_level': 'medium' if idx == 0 else 'low',
                    'answers': [randint(1, 5), randint(1, 5), randint(1, 5)],
                    'suggestion': '建议结合情绪日记继续观察，并在需要时预约咨询。',
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
        for idx, counselor in enumerate(counselor_objects[1:], start=1):
            Appointment.objects.update_or_create(
                student=student,
                counselor=counselor,
                scheduled_at=now + timedelta(days=idx + 3, hours=idx),
                defaults={
                    'topic': choice(['人际关系支持', '睡眠与压力调整', '自我成长困惑']),
                    'status': choice(['pending', 'confirmed']),
                    'confidential_note': '演示预约数据。',
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

        treehole, _ = TreeHolePost.objects.update_or_create(
            student=student,
            content='最近课程和项目堆在一起，有点担心自己处理不好。',
            defaults={
                'category': 'study',
                'mood_tag': '焦虑',
                'is_anonymous': True,
                'support_count': 6,
                'risk_flag': False,
            },
        )
        TreeHoleReply.objects.update_or_create(
            post=treehole,
            responder_name='同伴支持者',
            content='可以先把最急的一件事写下来，今晚只处理一个小步骤。',
            defaults={'is_counselor_reply': False},
        )
        samples = [
            ('relationship', '委屈', '和室友沟通不太顺利，不知道怎么开口比较好。'),
            ('growth', '迷茫', '最近对未来方向有点不确定，想慢慢理清自己真正想要什么。'),
            ('study', '疲惫', '连续几天赶作业，感觉脑子一直停不下来。'),
        ]
        for category, mood_tag, content in samples:
            post, _ = TreeHolePost.objects.update_or_create(
                student=student,
                content=content,
                defaults={
                    'category': category,
                    'mood_tag': mood_tag,
                    'is_anonymous': True,
                    'support_count': randint(2, 12),
                    'risk_flag': False,
                },
            )
            TreeHoleReply.objects.update_or_create(
                post=post,
                responder_name=choice(['同伴支持者', '值班老师', '心理委员']),
                content=choice(['谢谢你愿意说出来，可以先照顾好今晚的休息。', '这件事听起来不容易，建议把它拆成一个小步骤。', '如果这种感受持续，可以预约老师一起聊聊。']),
                defaults={'is_counselor_reply': False},
            )

        admin, created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
        if created:
            admin.set_password('admin123456')
            admin.save()
        AccountProfile.objects.update_or_create(user=admin, defaults={'role': 'admin'})

        all_tag_names = set()
        for article in Article.objects.all():
            for tag in (article.tags or []):
                all_tag_names.add(str(tag).strip())
        for counselor in Counselor.objects.all():
            for tag in (counselor.specialties or []):
                all_tag_names.add(str(tag).strip())
        for name in all_tag_names:
            Tag.objects.get_or_create(name=name, defaults={'description': '', 'is_active': True})

        self.stdout.write(self.style.SUCCESS('演示数据已创建：admin/admin123456，student001/student001，teacher001/teacher001'))
