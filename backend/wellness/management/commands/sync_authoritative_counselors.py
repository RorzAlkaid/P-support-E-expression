import re
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand
from django.utils import timezone

from wellness.models import Counselor


COUNSELOR_SOURCES = [
    {
        'name': 'Stanford CAPS',
        'url': 'https://caps.stanford.edu/people/counseling-and-psychological-services',
    },
    {
        'name': 'UT Dallas Student Counseling Center',
        'url': 'https://counseling.utdallas.edu/about/staff/',
    },
    {
        'name': 'Auburn Student Counseling & Psychological Services',
        'url': 'https://scps.auburn.edu/meet-the-staff/',
    },
]

TITLE_KEYWORDS = [
    'Psychologist',
    'Therapist',
    'Counselor',
    'Psychiatrist',
    'Clinical',
    'Director',
    'Social Worker',
    'Licensed',
    'Doctoral Intern',
    'Fellow',
]

BIOGRAPHY_MARKERS = [
    ' is ',
    ' has ',
    ' joined ',
    ' serves ',
    ' brings ',
    ' obtained ',
    ' received ',
    ' graduate ',
    ' originally ',
    ' calls ',
    ' training ',
]

SPECIALTY_KEYWORDS = {
    'Anxiety': '焦虑支持',
    'Depression': '抑郁情绪',
    'Stress': '压力管理',
    'Trauma': '创伤支持',
    'Sleep': '睡眠困扰',
    'Relationship': '人际关系',
    'Relationships': '人际关系',
    'Identity': '身份认同',
    'Grief': '哀伤辅导',
    'Eating': '进食与身体意象',
    'ADHD': '注意力支持',
    'Autism': '神经多样性支持',
    'LGBT': 'LGBTQ+支持',
    'Gender': '性别议题',
    'Crisis': '危机干预',
    'Substance': '成瘾与物质使用',
    'Mindfulness': '正念练习',
}

NAME_PATTERN = re.compile(
    r'^[A-Z][A-Za-z.\'-]+(?:\s+[A-Z][A-Za-z.\'-]+){1,4}(?:,\s*(?:Ph\.?D\.?|Psy\.?D\.?|MD|LMFT|LCSW|LPC|JD|MSW|M\.A\.|M\.S\.))*$'
)

NON_PERSON_WORDS = [
    'University',
    'Services',
    'Infographic',
    'Clinical Services',
    'Minutes',
    'Counseling',
    'Psychological',
    'Appointments',
    'Resources',
    'Health',
    'Contact',
    'Emergency',
    'Navigation',
    'Search',
    'Person',
    'Type',
    'Staff',
    'Therapist',
    'Psychiatrist',
    'Psychologist',
    'Administrative',
    'Associate',
    'Director',
    'Directors',
    'Support',
    'Interns',
    'Intern',
    'Fellow',
    'Practicum',
    'Contract',
    'Show',
    'All',
    'Emerging',
    'Adulthood',
    'Exploration',
    'Grief',
    'Wellness',
    'Theoretical',
    'Orientation',
    'Issues',
    'Coordinator',
    'Getting',
    'Started',
    'About',
    'Client',
    'Satisfaction',
    'Survey',
    'Select',
    'Page',
    'Board',
    'M.A.',
    'M.S.',
    'FAQ',
    'Outreach',
    'Programs',
    'Professional',
    'Training',
    'Talk',
    'Now',
    'Coping',
    'Traumatic',
    'Events',
    'Belonging',
    'Statement',
    'Frequently',
    'Questions',
    'Life',
    'Stage',
    'Transitions',
    'Trauma',
    'Recovery',
    'Gender',
    'Affirming',
    'Care',
    'Latine',
    'Students',
    'Family',
    'Parents',
    'Prevention',
    'Camp',
    'War',
    'Eagle',
    'Parent',
    'Run',
    'Suicide',
]


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []

    def handle_data(self, data):
        text = normalize(data)
        if text:
            self.texts.append(text)


def normalize(value):
    return ' '.join((value or '').replace('\xa0', ' ').split())


def fetch_html(url):
    request = Request(
        url,
        headers={
            'User-Agent': 'P-support-E-expression academic demo crawler/1.0',
            'Accept': 'text/html,application/xhtml+xml',
        },
    )
    with urlopen(request, timeout=25) as response:
        return response.read().decode('utf-8', errors='ignore')


def is_name(text):
    if len(text) > 80 or len(text) < 5:
        return False
    lowered = text.lower()
    if any(skip in lowered for skip in ['skip', 'navigation', 'search', 'filter', 'home']):
        return False
    if any(word.lower() in lowered for word in NON_PERSON_WORDS):
        return False
    return bool(NAME_PATTERN.match(text))


def infer_title(window):
    for text in window:
        lowered = f' {text.lower()} '
        if len(text) > 90 or any(marker in lowered for marker in BIOGRAPHY_MARKERS):
            continue
        if any(keyword.lower() in lowered for keyword in TITLE_KEYWORDS):
            return text[:80]
    return '心理咨询服务人员'


def infer_specialties(window):
    joined = ' '.join(window)
    results = []
    for key, value in SPECIALTY_KEYWORDS.items():
        if key.lower() in joined.lower() and value not in results:
            results.append(value)
    return results[:6] or ['大学生心理支持', '情绪调节']


def parse_counselors(html):
    parser = TextParser()
    parser.feed(html)
    counselors = []
    seen = set()
    for index, text in enumerate(parser.texts):
        if not is_name(text):
            continue
        name = text[:40]
        if name in seen:
            continue
        seen.add(name)
        window = parser.texts[index + 1:index + 16]
        title = infer_title(window)
        has_credential = bool(re.search(r'(Ph\.?D\.?|Psy\.?D\.?|MD|LMFT|LCSW|LPC|MSW|M\.A\.|M\.S\.)', name))
        if title == '心理咨询服务人员' and not has_credential:
            continue
        counselors.append({
            'name': name,
            'title': title,
            'specialties': infer_specialties(window),
            'qualifications': '',
            'available_slots': [],
            'source': '',
            'external_url': '',
            'fetched_at': None,
            'is_active': True,
        })
        if len(counselors) >= 12:
            break
    return counselors


class Command(BaseCommand):
    help = '从公开高校心理咨询中心页面抓取咨询师姓名、职称和专长，并更新咨询师模块。默认每天每个命令只更新一次。'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='忽略每日一次限制，强制抓取。')

    def handle(self, *args, **options):
        today = timezone.localdate()
        if not options['force'] and Counselor.objects.filter(updated_at__date=today, qualifications='').exists():
            self.stdout.write('跳过：今日已更新咨询师数据')
            return

        total_created = 0
        total_updated = 0

        for source in COUNSELOR_SOURCES:
            try:
                html = fetch_html(source['url'])
                counselors = parse_counselors(html)
                if 'Auburn' in source['name']:
                    counselors = counselors[:8]
                if not counselors:
                    self.stderr.write(self.style.WARNING(f'未解析到咨询师：{source["name"]}'))
                    continue

                created_count = 0
                updated_count = 0
                for item in counselors:
                    _, created = Counselor.objects.update_or_create(
                        name=item['name'],
                        defaults=item,
                    )
                    created_count += int(created)
                    updated_count += int(not created)
                total_created += created_count
                total_updated += updated_count
                self.stdout.write(self.style.SUCCESS(f'完成：{source["name"]}，新增 {created_count}，更新 {updated_count}'))
            except (URLError, TimeoutError, ValueError, OSError) as exc:
                self.stderr.write(self.style.ERROR(f'失败：{source["name"]}，{exc}'))

        self.stdout.write(self.style.SUCCESS(f'咨询师同步完成：新增 {total_created}，更新 {total_updated}'))
