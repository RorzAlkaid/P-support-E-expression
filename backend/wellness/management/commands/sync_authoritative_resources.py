from datetime import timedelta
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand
from django.utils import timezone

from wellness.models import Article, ExternalResourceSource, ResourceFetchLog


DEFAULT_SOURCES = [
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


class ResourceHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ''
        self.meta_description = ''
        self.links = []
        self.paragraphs = []
        self._capture_title = False
        self._capture_p = False
        self._current_link = None
        self._current_link_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self._capture_title = True
        elif tag == 'meta' and attrs.get('name', '').lower() == 'description':
            self.meta_description = attrs.get('content', '').strip()
        elif tag == 'p':
            self._capture_p = True
        elif tag == 'a' and attrs.get('href'):
            self._current_link = attrs.get('href')
            self._current_link_text = []

    def handle_endtag(self, tag):
        if tag == 'title':
            self._capture_title = False
        elif tag == 'p':
            self._capture_p = False
        elif tag == 'a' and self._current_link:
            text = ' '.join(''.join(self._current_link_text).split())
            if text and len(text) >= 4:
                self.links.append((text, self._current_link))
            self._current_link = None
            self._current_link_text = []

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._capture_title:
            self.title += text
        if self._capture_p and len(text) > 30:
            self.paragraphs.append(text)
        if self._current_link:
            self._current_link_text.append(text)


def fetch_html(url):
    request = Request(
        url,
        headers={
            'User-Agent': 'P-support-E-expression academic demo crawler/1.0',
            'Accept': 'text/html,application/xhtml+xml',
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode('utf-8', errors='ignore')


def clean_text(value, limit=280):
    text = ' '.join((value or '').split())
    return text[:limit]


def relevant_links(source, parser):
    keywords = [
        'mental',
        'health',
        'anxiety',
        'depression',
        'stress',
        'suicide',
        'trauma',
        'sleep',
        '心理',
        '焦虑',
        '抑郁',
        '压力',
    ]
    results = []
    seen = set()
    for title, href in parser.links:
        normalized = title.lower()
        if not any(keyword in normalized for keyword in keywords):
            continue
        full_url = urljoin(source.url, href)
        if full_url in seen:
            continue
        seen.add(full_url)
        results.append((title[:120], full_url))
        if len(results) >= 6:
            break
    return results


class Command(BaseCommand):
    help = '从权威心理健康网站抓取心理科普资源，并写入文章库。默认每天每个源站只更新一次。'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='忽略每日一次限制，强制抓取。')
        parser.add_argument('--seed-sources', action='store_true', help='创建默认权威源站。')

    def handle(self, *args, **options):
        if options['seed_sources'] or not ExternalResourceSource.objects.exists():
            for item in DEFAULT_SOURCES:
                ExternalResourceSource.objects.update_or_create(url=item['url'], defaults=item)

        today = timezone.localdate()
        for source in ExternalResourceSource.objects.filter(enabled=True):
            if source.last_fetched_at and source.last_fetched_at.date() == today and not options['force']:
                ResourceFetchLog.objects.create(source=source, status='skipped', message='今日已更新，跳过。')
                self.stdout.write(f'跳过：{source.name}')
                continue

            created_count = 0
            updated_count = 0
            try:
                html = fetch_html(source.url)
                parser = ResourceHTMLParser()
                parser.feed(html)

                summary = clean_text(parser.meta_description or ' '.join(parser.paragraphs[:2]), 360)
                content = '\n\n'.join(clean_text(paragraph, 600) for paragraph in parser.paragraphs[:8])
                if not content:
                    content = summary or f'来源：{source.url}'

                article, created = Article.objects.update_or_create(
                    external_url=source.url,
                    defaults={
                        'title': clean_text(parser.title or source.name, 120),
                        'source': source.organization or source.name,
                        'category': source.category,
                        'summary': summary or source.name,
                        'content': content,
                        'tags': source.tags,
                        'fetched_at': timezone.now(),
                        'is_published': True,
                    },
                )
                created_count += int(created)
                updated_count += int(not created)

                for title, link in relevant_links(source, parser):
                    child_article, child_created = Article.objects.update_or_create(
                        external_url=link,
                        defaults={
                            'title': title,
                            'source': source.organization or source.name,
                            'category': source.category,
                            'summary': f'来自 {source.name} 的权威心理健康主题链接。',
                            'content': f'该条资源来自 {source.organization or source.name}。\n\n请通过外部链接查看完整权威内容：{link}',
                            'tags': source.tags,
                            'fetched_at': timezone.now(),
                            'is_published': True,
                        },
                    )
                    created_count += int(child_created)
                    updated_count += int(not child_created)

                source.last_fetched_at = timezone.now()
                source.save(update_fields=['last_fetched_at', 'updated_at'])
                ResourceFetchLog.objects.create(
                    source=source,
                    status='success',
                    message='抓取完成。',
                    articles_created=created_count,
                    articles_updated=updated_count,
                )
                self.stdout.write(self.style.SUCCESS(f'完成：{source.name}，新增 {created_count}，更新 {updated_count}'))
            except (URLError, TimeoutError, ValueError, OSError) as exc:
                ResourceFetchLog.objects.create(source=source, status='failed', message=str(exc))
                self.stderr.write(self.style.ERROR(f'失败：{source.name}：{exc}'))
