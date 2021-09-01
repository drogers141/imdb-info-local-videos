from pathlib import Path
from shutil import rmtree
from unittest.mock import patch, call

from django.test import TestCase, SimpleTestCase
from django.core.management import call_command
from django.conf import settings

from imdb_info_local.imdb import IMDBTitleData, IMDBFindTitleResult
from imdb_info_local.models import IMDBTitleSearchData, NON_EXISTENT_PATH
from imdb_info_local.management.commands.run_scraper import (
    IMDBTitleSearchResults, get_imdb_title_data, find_results_html,
    remove_title_data_for_deleted_files, process_directory
)
from .nondb_fixtures import archer_title_data, archer_find_title_result

DATA_DIR = Path(__file__).parent.joinpath('data')


class RunScraperNoDBTests(SimpleTestCase):

    @patch('imdb_info_local.management.commands.run_scraper.imdb_title_data')
    @patch('imdb_info_local.management.commands.run_scraper.imdb_title_search_results')
    def test_get_imdb_title_data(self, search_results_mock, title_data_mock):
        search_results_mock.return_value = [archer_find_title_result]
        title_data_mock.return_value = archer_title_data
        expected = IMDBTitleSearchResults(
            title='Archer',
            find_results=[archer_find_title_result],
            title_data=archer_title_data
        )
        actual = get_imdb_title_data('Archer')
        self.assertEqual(expected.title, actual.title)
        self.assertEqual(expected.find_results, actual.find_results)
        self.assertEqual(expected.title_data, actual.title_data)

    @patch('imdb_info_local.management.commands.run_scraper.imdb_title_data')
    @patch('imdb_info_local.management.commands.run_scraper.imdb_title_search_results')
    def test_get_imdb_title_data_for_title_not_found(self, search_results_mock, title_data_mock):
        """Test the results for a title search which produces no results."""
        search_results_mock.return_value = []
        expected = IMDBTitleSearchResults(
            title='Unknown Title',
            find_results=[],
            title_data=IMDBTitleData('N/A', 'No titles found in search', NON_EXISTENT_PATH)
        )
        actual = get_imdb_title_data('Unknown Title')
        self.assertEqual(expected.title, actual.title)
        self.assertEqual(expected.find_results, actual.find_results)
        self.assertEqual(expected.title_data, actual.title_data)
        self.assert_(not title_data_mock.called)

    def test_find_results_html(self):
        expected = '<ul><li><a href="https://www.imdb.com/title/tt1486217/">Archer (2009) (TV Series)</a></li>\n</ul>'
        self.assertEqual(find_results_html([archer_find_title_result]), expected)

    @patch('imdb_info_local.management.commands.run_scraper.remove_title_data_for_deleted_files')
    @patch('imdb_info_local.management.commands.run_scraper.process_directory')
    def test_command_call(self, process_directory_mock, remove_deleted_files_mock):
        """Ensure the commmand works"""
        call_command('run_scraper')
        self.assertSequenceEqual(remove_deleted_files_mock.call_args_list,
                         [call(Path(settings.MOVIE_DIRECTORY), 'movie'),
                          call(Path(settings.TV_DIRECTORY), 'tv'),])
        self.assertSequenceEqual(process_directory_mock.call_args_list,
                         [call(Path(settings.MOVIE_DIRECTORY), 'movie'),
                          call(Path(settings.TV_DIRECTORY), 'tv'),])


fleabag_search_results = [IMDBFindTitleResult(img_url='https://m.media-amazon.com/images/M/MV5BMjA4MzU5NzQxNV5BMl5BanBnXkFtZTgwOTg3MDA5NzM@._V1_UX32_CR0,0,32,44_AL_.jpg', title_url='https://www.imdb.com/title/tt5687612/', text='Fleabag (2016) (TV Series)'),
                          IMDBFindTitleResult(img_url='https://m.media-amazon.com/images/M/MV5BM2U4NTVlMTgtM2FiOS00MzczLWI4Y2EtMDk3ZjJkOTgyMGM0XkEyXkFqcGdeQXVyNjczMzgwMDg@._V1_UX32_CR0,0,32,44_AL_.jpg', title_url='https://www.imdb.com/title/tt10702760/', text='National Theatre Live: Fleabag (2019)'),
                          IMDBFindTitleResult(img_url='https://m.media-amazon.com/images/M/MV5BOTQzZTRlNjAtZjM5Mi00NDQ0LWIyYjUtY2ExNmQ5OGJlNGMyXkEyXkFqcGdeQXVyOTI2MTMwMDc@._V1_UY44_CR13,0,32,44_AL_.jpg', title_url='https://www.imdb.com/title/tt7305642/', text='Fleabag (2017) (TV Episode) - CBeebies Bedtime Story (2004) (TV Series)')]


class RunScraperTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.archer = IMDBTitleSearchData.objects.create(
            type='TV',
            title='Archer',
            rating='8.6/10',
            blurb='Covert black ops and espionage take a back seat to zany personalities and relationships between secret agents and drones.',
            find_results='<ul><li><a href="https://www.imdb.com//title/tt1486217/">Archer (2009) (TV Series)</a></li>\n<li><a href="https://www.imdb.com//title/tt0060490/">Harper (1966) aka "Archer"</a></li>\n</ul>',
            file_path='/Volumes/dr-wd-2/tv/Archer',
            file_mtime=1604372147,
            file_ctime=1604372147
        )

    def setUp(self):
        self.tv_dir = DATA_DIR.joinpath('tv')
        self.tv_dir.mkdir()

    def tearDown(self):
        if self.tv_dir.is_dir():
            rmtree(self.tv_dir)
        movie_dir = DATA_DIR.joinpath('movies')
        if movie_dir.is_dir():
            rmtree(movie_dir)

    def test_process_dir_tv_title_already_exists(self):
        """Ensure title is not inserted if we have same title and type."""
        # This system expects unique titles for each type - movies and tv
        # ie there can't be two movies with the same title
        # this is enforced easily by adding the year to the title which we expect
        # but is not necessary
        # note this is overkill - as the year is expected, but what the hell
        archer_dir = self.tv_dir.joinpath('Archer')
        archer_dir.mkdir()
        added = process_directory(self.tv_dir, 'tv')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 1)
        self.assertEqual(IMDBTitleSearchData.objects.filter(title='Archer')[0], self.archer)
        self.assertSequenceEqual(added, [])

    @patch('imdb_info_local.management.commands.run_scraper.get_imdb_title_data')
    def test_process_dir_tv_new_title(self, get_imdb_title_data_mock):
        get_imdb_title_data_mock.return_value = IMDBTitleSearchResults(
            title='Fleabag',
            find_results=fleabag_search_results,
            title_data=IMDBTitleData(
                rating='8.7/10',
                blurb='A comedy series adapted from the award-winning play about a young woman trying to cope with life in London whilst coming to terms with a recent tragedy.',
                image_file=Path('/tmp/archer.jpg')
            )
        )
        fleabag_dir = self.tv_dir.joinpath('Fleabag')
        fleabag_dir.mkdir()

        added = process_directory(self.tv_dir, 'tv')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 2)
        fleabag = IMDBTitleSearchData.objects.get(title='Fleabag')
        self.assertEqual(fleabag.title, 'Fleabag')
        self.assertEqual(fleabag.rating, '8.7/10')
        self.assertEqual(fleabag.blurb, 'A comedy series adapted from the award-winning play about a young woman trying to cope with life in London whilst coming to terms with a recent tragedy.')
        self.assertSequenceEqual(added, ['Fleabag'])

    @patch('imdb_info_local.management.commands.run_scraper.get_imdb_title_data')
    def test_process_dir_movie_where_title_exists_for_tv(self, get_imdb_title_data_mock):
        """Ensure we insert a movie if there is the same title, but tv series"""
        # it is fine for a movie and tv show to have the same name
        # again - this constraint is also down to my usage as consisting
        # of all movies in one dir and all tv in another dir
        # so there can't be a dup, and if we find one it is wrong
        get_imdb_title_data_mock.return_value = IMDBTitleSearchResults(
            title='Archer',
            # doesn't matter - reuse these results - can't be empty
            find_results=fleabag_search_results,
            title_data=IMDBTitleData(
                rating='8/10',
                blurb='There should be an Archer movie anyway.',
                image_file=Path('/tmp/archer.jpg')
            )
        )
        movie_dir = DATA_DIR.joinpath('movies')
        movie_dir.mkdir()
        archer_movie_dir = movie_dir.joinpath('Archer')
        archer_movie_dir.mkdir()

        added = process_directory(movie_dir, 'movie')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 2)
        self.assertEqual(IMDBTitleSearchData.objects.filter(title='Archer').count(), 2)
        self.assertEqual(IMDBTitleSearchData.objects.filter(title='Archer', type='TV').count(), 1)
        self.assertEqual(IMDBTitleSearchData.objects.filter(title='Archer', type='MO').count(), 1)
        self.assertSequenceEqual(added, ['Archer'])

    def test_remove_title_data_for_deleted_files_no_removal_needed(self):
        archer_dir = self.tv_dir.joinpath('Archer')
        archer_dir.mkdir()
        fleabag_dir = self.tv_dir.joinpath('Fleabag')
        fleabag_dir.mkdir()
        # print(f"before delete check: {[t.title for t in IMDBTitleSearchData.objects.all()]}")
        removed_titles = remove_title_data_for_deleted_files(self.tv_dir, 'tv')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 1)
        self.assertEqual(IMDBTitleSearchData.objects.filter(title='Archer', type='TV').count(), 1)
        self.assertSequenceEqual(removed_titles, [])

    def test_remove_title_data_for_deleted_files_removal_needed(self):
        fleabag_dir = self.tv_dir.joinpath('Fleabag')
        fleabag_dir.mkdir()
        removed = remove_title_data_for_deleted_files(self.tv_dir, 'tv')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 0)
        self.assertSequenceEqual(removed, ['Archer'])
