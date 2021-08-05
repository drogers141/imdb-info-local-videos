from django.core.management.base import BaseCommand

from imdb_info_local.models import IMDBTitleSearchData


class Command(BaseCommand):
    help = """Convenience command for deleting all IMDBTitleSearchData objects"""

    def handle(self, *args, **options):
        IMDBTitleSearchData.objects.all().delete()