import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from imdb_info_local.models import IMDBTitleSearchData, IMAGE_SUBDIRECTORY


class Command(BaseCommand):
    help = """Deletes all IMDBTitleSearchData objects from the database and all
    title images from media storage."""

    def handle(self, *args, **options):
        IMDBTitleSearchData.objects.all().delete()
        for filename in Path(settings.MEDIA_ROOT).joinpath(IMAGE_SUBDIRECTORY).glob('*'):
            if filename.name != '.gitignore':
                os.remove(filename)
