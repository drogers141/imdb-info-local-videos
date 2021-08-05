from django.core.management.base import BaseCommand
from django.utils import timezone, dateparse

from imdb_info_local.models import IMDBTitleSearchData


class Command(BaseCommand):
    help = """Convenience command for deleting all IMDBTitleSearchData objects"""

    def handle(self, *args, **options):
        _time = timezone.now().strftime("%Y-%m-%d %X %Z")
        self.stdout.write("Django time: {}".format(_time))
        IMDBTitleSearchData.objects.all().delete()