from pathlib import Path
import logging
import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.files import File

from rich.progress import track

from imdb_info_local.models import IMDBTitleSearchData, add_image_file, NON_EXISTENT_PATH
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
            title_data= IMDBTitleData('N/A', 'No titles found in search', NON_EXISTENT_PATH)
        )


def find_results_html(find_results: [IMDBFindTitleResult]) -> str:
    html = "<ul>"
    for result in find_results:
        html += f"""<li><a href="{result.title_url}">{result.text}</a></li>\n"""
    html += "</ul>"
    return html


def remove_title_data_for_deleted_files(directory: Path, type: str='movie') -> [str]:
    """Remove unneeded title data model objects

    :param directory - path to directory holding videos
    :param type - 'movie', or 'tv'
    :return - list of titles removed
    """
    video_title_dirs = directory.glob('*')
    video_titles = [t.name.replace('-', ' ') for t in video_title_dirs]
    # print(f"video title dirs:\n{[v for v in video_title_dirs]}")
    # print(f"video titles:\n{video_titles}")

    removed = []
    title_type = None
    if type == 'movie':
        title_type = IMDBTitleSearchData.MOVIE
    elif type == 'tv':
        title_type = IMDBTitleSearchData.TV
    else:
        raise Exception(f'type: {type} not movie or tv')

    for titleData in IMDBTitleSearchData.objects.filter(type=title_type):
        if titleData.title not in video_titles:
            logger.debug(f'titleData {titleData} not in directory: {directory} - removing')
            removed.append(titleData.title)
            titleData.delete()

    return removed


def process_directory(directory: Path, title_type: str = 'movie'):
    """Processes filepaths in directory.

    For each file:
    * gets file info
    * extracts title name
    * checks if the title is not already in the db (title and type (tv, movie) have to be
      the same to reject)
    * if not scrapes IMDB for rating and blurb
    * saves as Model into db.

    It is assumed that all titles in `directory` are of type `type`.
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
    and this is not meant to be robust in terms of the title that is displayed.
    It's more important to get the right IMdb info.

    :param directory - path to directory holding videos
    :param title_type - 'movie', or 'tv'
    :return - list of titles added
    """
    assert title_type in ('tv', 'movie'), 'title_type must be "movie" or "tv"'

    added = []
    title_subdirs = [d for d in directory.glob('*')]

    for subdir in track(title_subdirs, description=f'Processing {title_type} titles...'):
        try:
            logger.debug(f'processing: {subdir}')
            path = subdir.as_posix()
            type_ = IMDBTitleSearchData.TV if title_type == 'tv' else IMDBTitleSearchData.MOVIE
            mtime = int(subdir.stat().st_mtime)
            ctime = int(subdir.stat().st_ctime)
            logger.debug(f'path: {path}\nmtime: {mtime}, ctime: {ctime}')
            title = subdir.name.replace('-', ' ')

            if not IMDBTitleSearchData.objects.filter(title=title, type=type_):
                title_search_results = get_imdb_title_data(title)
                logger.debug(f'title data: {title_search_results}')
                title_data_instance = IMDBTitleSearchData(
                    title=title,
                    type=type_,
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
                logger.debug(f'title of same type exists: {title} type: {type_}')
        except Exception as e:
            logger.error(f'Exception handling dir: {subdir}')
            raise
    return added


class Command(BaseCommand):
    help = """Select movie or tv titles from filenames, scrape IMDB for data on each title.
    Then store as models."""

    def add_arguments(self, parser):
        parser.add_argument('-d', '--dir', help='Get titles from this directory.')
        parser.add_argument('-t', '--type', help='Use with -d, --dir, specify video type in ' +
                                                 'directory -- "tv" or "movie"')

    def handle(self, *args, **options):
        dir_ = options.get('dir')
        type_ = options.get('type')
        if dir_ or type_:
            if not (dir_ and type_):
                logger.error(f'Type must be specified with directory option: dir: {dir_}, type: {type_}')
                return

            added_movies = process_directory(Path(dir_), type_)
            if added_movies:
                logger.info(f'Added movies: {added_movies}')
            logger.info('No movies removed when called with arguments.')
            self.stdout.write('Also - as the program currently behaves, any titles in directories not in the standard tv ' +
                        'or movie directories (in settings.py) will be removed from the database when running the ' +
                        'standard run_scraper command with no arguments.')

        else:

            removed_movies = remove_title_data_for_deleted_files(Path(settings.MOVIE_DIRECTORY), 'movie')
            removed_tv = remove_title_data_for_deleted_files(Path(settings.TV_DIRECTORY), 'tv')

            added_movies = process_directory(Path(settings.MOVIE_DIRECTORY), 'movie')
            added_tv = process_directory(Path(settings.TV_DIRECTORY), 'tv')

            if removed_movies:
                logger.info(f'Removed movies: {removed_movies}')
            if removed_tv:
                logger.info(f'Removed tv: {removed_tv}')
            if added_movies:
                logger.info(f'Added movies: {added_movies}')
            if added_tv:
                logger.info(f'Added tv: {added_tv}')
            if not removed_movies or removed_tv or added_movies or added_tv:
                logger.info('No movie or tv titles added or removed')
