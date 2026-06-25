from django.core.management.base import BaseCommand

from wellness.models import Article, Counselor, Tag


class Command(BaseCommand):
    help = '将所有文章标签和咨询师擅长领域同步到 Tag 表'

    def handle(self, *args, **options):
        tag_names = set()

        for article in Article.objects.all():
            for tag in (article.tags or []):
                name = str(tag).strip()
                if name:
                    tag_names.add(name)

        for counselor in Counselor.objects.all():
            for tag in (counselor.specialties or []):
                name = str(tag).strip()
                if name:
                    tag_names.add(name)

        created = 0
        for name in sorted(tag_names):
            _, is_new = Tag.objects.get_or_create(
                name=name,
                defaults={'description': '', 'is_active': True},
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  已创建标签: {name}'))
            else:
                self.stdout.write(f'  已存在: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\n标签同步完成：共 {len(tag_names)} 个标签，本次新增 {created} 个。'
        ))
