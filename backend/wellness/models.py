from django.contrib.auth.models import User
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True


class AccountProfile(TimeStampedModel):
    ROLE_STUDENT = 'student'
    ROLE_TEACHER = 'teacher'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_STUDENT, '学生'),
        (ROLE_TEACHER, '教师'),
        (ROLE_ADMIN, '管理员'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account_profile', verbose_name='用户')
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_STUDENT, verbose_name='角色')

    class Meta:
        verbose_name = '账号角色'
        verbose_name_plural = '账号角色'

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'


class StudentProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', verbose_name='用户')
    student_no = models.CharField(max_length=32, unique=True, verbose_name='学号')
    college = models.CharField(max_length=80, blank=True, verbose_name='学院')
    grade = models.CharField(max_length=30, blank=True, verbose_name='年级')
    privacy_consent = models.BooleanField(default=False, verbose_name='隐私授权')
    pressure_sources = models.JSONField(default=list, blank=True, verbose_name='压力来源')
    preferred_topics = models.JSONField(default=list, blank=True, verbose_name='偏好主题')

    class Meta:
        verbose_name = '学生档案'
        verbose_name_plural = '学生档案'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} - {self.student_no}'


class Counselor(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='counselor_profile', verbose_name='关联教师账号')
    name = models.CharField(max_length=40, verbose_name='姓名')
    title = models.CharField(max_length=80, verbose_name='职称')
    specialties = models.JSONField(default=list, verbose_name='擅长领域')
    qualifications = models.TextField(blank=True, verbose_name='资质说明')
    available_slots = models.JSONField(default=list, verbose_name='可预约时段')
    avatar_color = models.CharField(max_length=20, default='#d85d73', verbose_name='头像色')
    source = models.CharField(max_length=120, blank=True, verbose_name='来源')
    external_url = models.URLField(blank=True, verbose_name='外部链接')
    fetched_at = models.DateTimeField(null=True, blank=True, verbose_name='抓取时间')
    is_active = models.BooleanField(default=True, verbose_name='是否可预约')

    class Meta:
        verbose_name = '咨询师'
        verbose_name_plural = '咨询师'

    def __str__(self):
        return self.name


class Article(TimeStampedModel):
    title = models.CharField(max_length=120, verbose_name='标题')
    source = models.CharField(max_length=120, blank=True, verbose_name='来源')
    category = models.CharField(max_length=40, verbose_name='分类')
    summary = models.TextField(verbose_name='摘要')
    content = models.TextField(verbose_name='正文')
    tags = models.JSONField(default=list, blank=True, verbose_name='标签')
    external_url = models.URLField(blank=True, verbose_name='外部链接')
    fetched_at = models.DateTimeField(null=True, blank=True, verbose_name='抓取时间')
    is_published = models.BooleanField(default=True, verbose_name='是否发布')

    class Meta:
        verbose_name = '心理科普文章'
        verbose_name_plural = '心理科普文章'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class ExternalResourceSource(TimeStampedModel):
    name = models.CharField(max_length=120, verbose_name='源站名称')
    url = models.URLField(unique=True, verbose_name='源站地址')
    organization = models.CharField(max_length=120, blank=True, verbose_name='机构')
    category = models.CharField(max_length=40, default='心理科普', verbose_name='默认分类')
    tags = models.JSONField(default=list, blank=True, verbose_name='默认标签')
    enabled = models.BooleanField(default=True, verbose_name='启用')
    last_fetched_at = models.DateTimeField(null=True, blank=True, verbose_name='上次抓取时间')

    class Meta:
        verbose_name = '外部资源源站'
        verbose_name_plural = '外部资源源站'

    def __str__(self):
        return self.name


class ResourceFetchLog(TimeStampedModel):
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_SKIPPED = 'skipped'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, '成功'),
        (STATUS_FAILED, '失败'),
        (STATUS_SKIPPED, '跳过'),
    ]

    source = models.ForeignKey(ExternalResourceSource, on_delete=models.CASCADE, related_name='fetch_logs', verbose_name='源站')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, verbose_name='状态')
    message = models.TextField(blank=True, verbose_name='信息')
    articles_created = models.PositiveIntegerField(default=0, verbose_name='新增文章数')
    articles_updated = models.PositiveIntegerField(default=0, verbose_name='更新文章数')

    class Meta:
        verbose_name = '资源抓取记录'
        verbose_name_plural = '资源抓取记录'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.source.name} - {self.get_status_display()}'


class ResourceViewLog(TimeStampedModel):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='resource_view_logs', verbose_name='student')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='view_logs', verbose_name='article')
    article_title = models.CharField(max_length=120, verbose_name='article title')
    article_source = models.CharField(max_length=120, blank=True, verbose_name='article source')
    article_category = models.CharField(max_length=40, blank=True, verbose_name='article category')

    class Meta:
        verbose_name = 'resource view log'
        verbose_name_plural = 'resource view logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} viewed {self.article_title}'


class AssessmentScale(TimeStampedModel):
    name = models.CharField(max_length=80, verbose_name='量表名称')
    code = models.CharField(max_length=30, unique=True, verbose_name='量表编码')
    description = models.TextField(blank=True, verbose_name='说明')
    questions = models.JSONField(default=list, verbose_name='题目')
    max_score = models.PositiveIntegerField(default=100, verbose_name='最高分')

    class Meta:
        verbose_name = '心理量表'
        verbose_name_plural = '心理量表'

    def __str__(self):
        return self.name


class AssessmentRecord(TimeStampedModel):
    RISK_LOW = 'low'
    RISK_MEDIUM = 'medium'
    RISK_HIGH = 'high'
    RISK_CHOICES = [
        (RISK_LOW, '低'),
        (RISK_MEDIUM, '中'),
        (RISK_HIGH, '高'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assessment_records', verbose_name='学生')
    scale = models.ForeignKey(AssessmentScale, on_delete=models.PROTECT, related_name='records', verbose_name='量表')
    score = models.PositiveIntegerField(verbose_name='得分')
    risk_level = models.CharField(max_length=12, choices=RISK_CHOICES, default=RISK_LOW, verbose_name='风险等级')
    answers = models.JSONField(default=list, blank=True, verbose_name='答题记录')
    suggestion = models.TextField(blank=True, verbose_name='建议')

    class Meta:
        verbose_name = '量表记录'
        verbose_name_plural = '量表记录'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} {self.scale.code} {self.score}'


class MoodEntry(TimeStampedModel):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mood_entries', verbose_name='学生')
    mood = models.CharField(max_length=30, verbose_name='情绪')
    intensity = models.PositiveSmallIntegerField(default=5, verbose_name='强度')
    sleep_quality = models.PositiveSmallIntegerField(default=5, verbose_name='睡眠质量')
    pressure_sources = models.JSONField(default=list, blank=True, verbose_name='压力来源')
    note = models.TextField(blank=True, verbose_name='日记')
    is_private = models.BooleanField(default=True, verbose_name='是否私密')

    class Meta:
        verbose_name = '情绪日记'
        verbose_name_plural = '情绪日记'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} {self.mood} {self.intensity}'


class TreeHolePost(TimeStampedModel):
    CATEGORY_CHOICES = [
        ('study', '学业压力'),
        ('relationship', '人际关系'),
        ('family', '家庭关系'),
        ('growth', '自我成长'),
        ('other', '其他'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='treehole_posts', verbose_name='学生')
    category = models.CharField(max_length=24, choices=CATEGORY_CHOICES, default='other', verbose_name='分类')
    content = models.TextField(verbose_name='倾诉内容')
    mood_tag = models.CharField(max_length=30, blank=True, verbose_name='情绪标签')
    is_anonymous = models.BooleanField(default=True, verbose_name='是否匿名')
    support_count = models.PositiveIntegerField(default=0, verbose_name='支持数')
    risk_flag = models.BooleanField(default=False, verbose_name='风险标记')

    class Meta:
        verbose_name = '匿名树洞'
        verbose_name_plural = '匿名树洞'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_category_display()} - {self.content[:18]}'


class TreeHoleReply(TimeStampedModel):
    post = models.ForeignKey(TreeHolePost, on_delete=models.CASCADE, related_name='replies', verbose_name='树洞')
    responder_name = models.CharField(max_length=40, default='同伴支持者', verbose_name='回应者')
    content = models.TextField(verbose_name='回应内容')
    is_counselor_reply = models.BooleanField(default=False, verbose_name='咨询师回应')

    class Meta:
        verbose_name = '树洞回应'
        verbose_name_plural = '树洞回应'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.responder_name}: {self.content[:18]}'


class Appointment(TimeStampedModel):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_FINISHED = 'finished'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待确认'),
        (STATUS_CONFIRMED, '已确认'),
        (STATUS_FINISHED, '已完成'),
        (STATUS_CANCELLED, '已取消'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='appointments', verbose_name='学生')
    counselor = models.ForeignKey(Counselor, on_delete=models.PROTECT, related_name='appointments', verbose_name='咨询师')
    scheduled_at = models.DateTimeField(verbose_name='预约时间')
    topic = models.CharField(max_length=120, verbose_name='咨询主题')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='状态')
    confidential_note = models.TextField(blank=True, verbose_name='保密备注')

    class Meta:
        verbose_name = '咨询预约'
        verbose_name_plural = '咨询预约'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'{self.student} -> {self.counselor} {self.scheduled_at:%Y-%m-%d %H:%M}'


class CrisisAlert(TimeStampedModel):
    LEVEL_NOTICE = 'notice'
    LEVEL_WARNING = 'warning'
    LEVEL_CRITICAL = 'critical'
    LEVEL_CHOICES = [
        (LEVEL_NOTICE, '关注'),
        (LEVEL_WARNING, '预警'),
        (LEVEL_CRITICAL, '危机'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='crisis_alerts', verbose_name='学生')
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, default=LEVEL_NOTICE, verbose_name='等级')
    trigger = models.CharField(max_length=160, verbose_name='触发原因')
    handled = models.BooleanField(default=False, verbose_name='是否处理')
    handler_note = models.TextField(blank=True, verbose_name='处理记录')

    class Meta:
        verbose_name = '危机预警'
        verbose_name_plural = '危机预警'
        ordering = ['handled', '-created_at']

    def __str__(self):
        return f'{self.student} {self.level}'

# Create your models here.
