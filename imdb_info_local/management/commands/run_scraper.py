from pathlib import Path
import logging
import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.files import File

from rich.progress import track

from imdb_info_local.models import IMDBTitleSearchData, add_image_file, NONEXISTENT_PATH
from imdb_info_local.imdb import (imdb_title_search_results, imdb_title_data,
                                  IMDBTitleData, IMDBFindTitleResult)

logger = logging.getLogger(__name__)


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
    4 - scrape the title page for this candidate for rating, blurb and image

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
            title_data= IMDBTitleData('N/A', 'No titles found in search', NONEXISTENT_PATH)
        )


def find_results_html(find_results: [IMDBFindTitleResult]) -> str:
    html = "<ul>"
    for result in find_results:
        html += f"""<li><a href="{result.title_url}">{result.text}</a></li>\n"""
    html += "</ul>"
    return html


def remove_title_data_for_deleted_files(directory: Path, title_type: str='MO') -> [str]:
    """Remove unneeded title data model objects

    :param directory - path to directory holding videos
    :param title_type - 'MO' for movies, or 'TV' for tv shows
    :return - list of titles removed
    """
    if not directory.is_dir():
        logger.info(f'Not removing titles: directory does not exist: {str(directory.resolve())}')
        return []
    assert title_type in ('MO', 'TV'), 'wrong title type'

    video_title_dirs = [file for file in directory.iterdir() if file.is_dir()]
    removed = []

    title_paths_in_dir = set([str(title.resolve()) for title in video_title_dirs])
    paths_and_titles_in_db = {title_data.file_path: title_data
                              for title_data
                              in IMDBTitleSearchData.objects.filter(type=title_type)
                              if title_data.file_path.startswith(str(directory))}
    titles_in_db_not_in_dir = set(paths_and_titles_in_db.keys()) - title_paths_in_dir

    for title_path in titles_in_db_not_in_dir:
        paths_and_titles_in_db[title_path].delete()
        removed.append(paths_and_titles_in_db[title_path].title)

    return removed


def process_directory(directory: Path, title_type: str = 'MO'):
    """Processes filepaths in directory.

    For each file:
    * gets file info
    * extracts title name
    * checks if the title is not already in the db (title and type (tv, movie) have to be
      the same to reject)
    * if not, scrapes IMDB for rating and blurb
    * saves as Model into db.

    It is assumed that all titles in `directory` are of type `type`.
    It is assumed that each title - ie movie or tv series - is in its own
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
    and this is not meant to be robust in terms of the title that is displayed.
    It's more important to get the right IMdb info.

    :param directory - path to directory holding videos
    :param title_type - 'MO' for movies, or 'TV' for tv shows
    :return - list of titles added
    """
    if not directory.is_dir():
        logger.info(f'Not adding titles: directory does not exist: {str(directory.resolve())}')
        return []
    assert title_type in ('MO', 'TV'), 'wrong title type'

    added = []
    title_subdirs = [d for d in directory.iterdir() if d.is_dir()]

    for subdir in track(title_subdirs, description=f'Processing {title_type} titles...'):
        try:
            logger.debug(f'processing: {subdir}')
            path = subdir.resolve()
            mtime = int(subdir.stat().st_mtime)
            ctime = int(subdir.stat().st_ctime)
            logger.debug(f'path: {path}\nmtime: {mtime}, ctime: {ctime}')
            title = subdir.name.replace('-', ' ')

            if not IMDBTitleSearchData.objects.filter(title=title, type=title_type):
                title_search_results = get_imdb_title_data(title)
                logger.debug(f'title data: {title_search_results}')
                title_data_instance = IMDBTitleSearchData(
                    title=title,
                    type=title_type,
                    rating=title_search_results.title_data.rating,
                    blurb=title_search_results.title_data.blurb,
                    find_results=find_results_html(title_search_results.find_results),
                    file_path=path,
                    file_mtime=mtime,
                    file_ctime=ctime
                )
                add_image_file(title_data_instance, title_search_results.title_data.image_file)
                title_data_instance.save()
                added.append(title)
                time.sleep(1)
            else:
                logger.debug(f'title of same type exists: {title} type: {title_type}')
        except Exception as e:
            logger.error(f'Exception handling dir: {subdir}')
            raise
    return added


class Command(BaseCommand):
    help = """Select movie or tv titles from filenames, scrape IMDB for data on each title.
    Then store as models."""

    def add_arguments(self, parser):
        parser.add_argument('-d', '--dir', help='Get titles from this directory.')
        parser.add_argument('-t', '--type', help='Use with -d, --dir, specify video type in directory -- ' +
                                                 '"TV" for tv shows, or "MO" for movies')

    def handle(self, *args, **options):
        dir_ = options.get('dir')
        title_type = options.get('type')
        if dir_ or title_type:
            assert title_type in ('MO', 'TV'), 'wrong title type'
            if not (dir_ and title_type):
                logger.error(f'Type must be specified with directory option: dir: {dir_}, type: {title_type}')
                return

            added_movies = process_directory(Path(dir_), title_type)
            if added_movies:
                logger.info(f'Added movies: {added_movies}')
        else:

            removed_movies, removed_tv = [], []
            for movie_dir in settings.IMDB_INFO_LOCAL_VIDEO_DIRS['Movies']:
                removed_movies.extend(remove_title_data_for_deleted_files(Path(movie_dir), 'MO'))
            for tv_dir in settings.IMDB_INFO_LOCAL_VIDEO_DIRS['TV']:
                removed_tv.extend(remove_title_data_for_deleted_files(Path(tv_dir), 'TV'))

            added_movies, added_tv = [], []
            for movie_dir in settings.IMDB_INFO_LOCAL_VIDEO_DIRS['Movies']:
                added_movies.extend(process_directory(Path(movie_dir), 'MO'))
            for tv_dir in settings.IMDB_INFO_LOCAL_VIDEO_DIRS['TV']:
                added_tv.extend(process_directory(Path(tv_dir), 'TV'))

            if removed_movies:
                logger.info(f'Removed movies: {removed_movies}')
            if removed_tv:
                logger.info(f'Removed tv: {removed_tv}')
            if added_movies:
                logger.info(f'Added movies: {added_movies}')
            if added_tv:
                logger.info(f'Added tv: {added_tv}')
            if not (removed_movies or removed_tv or added_movies or added_tv):
                logger.info('No movie or tv titles added or removed')
