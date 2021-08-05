from pathlib import Path
import logging
import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from imdb_info_local.models import IMDBTitleSearchData
from imdb_info_local.imdb import (imdb_title_search_results, imdb_title_data,
                                  IMDBTitleData, IMDBFindTitleResult)

# logger = logging.getLogger(__name__)


class IMDBTitleSearchResults:
    def __init__(self, title: str,
                 find_results: [IMDBFindTitleResult],
                 title_data: IMDBTitleData):
        self.title = title
        self.find_results = find_results
        self.title_data = title_data

    def __str__(self):
        return f"{self.title}\n{self.title_data}"


def get_imdb_title_data(title: str) -> IMDBTitleSearchResults:
    """Searches IMDB for title and scrapes for info.

    The algorithm:
    1 - get IMDB search page for title
    2 - scrape the page for a list of candidate titles
    3 - pick the first candidate
    4 - scrape the title page for this candidate for rating and blurb

    The find results from step 2 are saved so they can be presented to the
    user in case the wrong title is picked.

    :return IMDBTitleSearchResults
    """
    search_results = imdb_title_search_results(title)
    if search_results:
        target = search_results[0]
        title_data = imdb_title_data(target.title_url)
        return IMDBTitleSearchResults(title, search_results, title_data)
    else:
        return IMDBTitleSearchResults(
            title=title,
            find_results=search_results,
            title_data= IMDBTitleData('N/A', 'No titles found in search')
        )


def find_results_html(find_results: [IMDBFindTitleResult]) -> str:
    html = "<ul>"
    for result in find_results:
        html += f"""<li><a href="{result.title_url}">{result.text}</a></li>\n"""
    html += "</ul>"
    return html


def remove_title_data_for_deleted_files(directory: Path, type: str='movie'):
    """Remove unneeded title data model objects

    :param directory - path to directory holding videos
    :param type - 'movie', or 'tv'
    """
    video_title_dirs = directory.glob('*')
    video_titles = [t.name.replace('-', ' ') for t in video_title_dirs]
    # print(f"video title dirs:\n{[v for v in video_title_dirs]}")
    # print(f"video titles:\n{video_titles}")

    title_type = None
    if type == 'movie':
        title_type = IMDBTitleSearchData.MOVIE
    elif type == 'tv':
        title_type = IMDBTitleSearchData.TV
    else:
        raise Exception(f'type: {type} not movie or tv')

    for titleData in IMDBTitleSearchData.objects.filter(type=title_type):
        if titleData.title not in video_titles:
            print(f'titleData {titleData} not in directory: {directory} - removing')
            titleData.delete()


def process_directory(directory: Path, type: str = 'movie'):
    """Processes filepaths in directory.

    For each file: gets file info, extracts title name, scrapes IMDB, saves as
    Model.

    It is assumed that each title - ie movie or tv series - is in it's own
    directory, with hyphen delimited names.  And best to end with the year.
    Examples:
    Star-Trek-Beyond-2016
    The-Big-Lebowski
    The-Bourne-Legacy-2012
    American-Gods-2017
    Babylon-5-1993
    Tosh.0

    This was required to make it easy to parse the title without worrying about
    file extensions.  So the parsing is just replacing '-' in the title
    directory name with ' ' to create the title.  In particular, names with
    periods would be problematic - e.g. Tosh.0
    Of course this will incorrectly parse hyphenated names, but that is rare,
    and this is a fast and dirty project.

    :param directory - path to directory holding videos
    :param type - 'movie', or 'tv'
    """
    for subdir in directory.glob('*'):
        try:
            print(f'processing: {subdir}')
            path = subdir.as_posix()
            type_ = IMDBTitleSearchData.TV if type == 'tv' else IMDBTitleSearchData.MOVIE
            mtime = int(subdir.stat().st_mtime)
            ctime = int(subdir.stat().st_ctime)
            print(f'path: {path}\nmtime: {mtime}, ctime: {ctime}')
            title = subdir.name.replace('-', ' ')

            if not IMDBTitleSearchData.objects.filter(title=title, type=type_):
                title_search_results = get_imdb_title_data(title)
                print(f'title data: {title_search_results}')
                IMDBTitleSearchData.objects.create(
                    title=title,
                    type=type_,
                    rating=title_search_results.title_data.rating,
                    blurb=title_search_results.title_data.blurb,
                    find_results=find_results_html(title_search_results.find_results),
                    file_path=path,
                    file_mtime=mtime,
                    file_ctime=ctime
                )
                time.sleep(1)
            else:
                print(f'title of same type exists: {title} type: {type_}')
        except Exception as e:
            print(f'Exception handling dir: {subdir}')
            raise


class Command(BaseCommand):
    help = """Select movie or tv titles from filenames, scrape IMDB for data on each title.
    Then store as models."""

    def handle(self, *args, **options):
        remove_title_data_for_deleted_files(Path(settings.MOVIE_DIRECTORY), 'movie')
        remove_title_data_for_deleted_files(Path(settings.MOVIE_DIRECTORY), 'tv')

        process_directory(Path(settings.MOVIE_DIRECTORY), 'movie')
        process_directory(Path(settings.TV_DIRECTORY), 'tv')

