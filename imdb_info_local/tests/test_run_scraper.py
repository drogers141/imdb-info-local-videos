import shutil
from pathlib import Path
from shutil import rmtree
from unittest.mock import patch, call, Mock
import os

from django.test import TestCase, SimpleTestCase
from django.core.management import call_command
from django.conf import settings

from imdb_info_local.imdb import IMDBTitleData, IMDBFindTitleResult
from imdb_info_local.models import IMDBTitleSearchData, NONEXISTENT_PATH
from imdb_info_local.management.commands.run_scraper import (
    IMDBTitleSearchResults, get_imdb_title_data, find_results_html,
    remove_title_data_for_deleted_files, process_directory
)
from .nondb_fixtures import (
    archer_title_data, archer_find_title_result,
)

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
            title_data=IMDBTitleData(None, 'No titles found in search', NONEXISTENT_PATH)
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
        video_dirs_settings = {
            'TV': ['/path/to/tv'],
            'Movies': ['/path/to/movies']
        }
        with self.settings(IMDB_INFO_LOCAL_VIDEO_DIRS=video_dirs_settings):
            call_command('run_scraper')
            self.assertSequenceEqual(remove_deleted_files_mock.call_args_list,
                             [call(Path(settings.IMDB_INFO_LOCAL_VIDEO_DIRS['Movies'][0]), 'MO'),
                              call(Path(settings.IMDB_INFO_LOCAL_VIDEO_DIRS['TV'][0]), 'TV')])
            self.assertSequenceEqual(process_directory_mock.call_args_list,
                                     [call(Path(settings.IMDB_INFO_LOCAL_VIDEO_DIRS['Movies'][0]), 'MO'),
                                      call(Path(settings.IMDB_INFO_LOCAL_VIDEO_DIRS['TV'][0]), 'TV')])


fleabag_search_results = [IMDBFindTitleResult(img_url='https://m.media-amazon.com/images/M/MV5BMjA4MzU5NzQxNV5BMl5BanBnXkFtZTgwOTg3MDA5NzM@._V1_UX32_CR0,0,32,44_AL_.jpg', title_url='https://www.imdb.com/title/tt5687612/', text='Fleabag (2016) (TV Series)'),
                          IMDBFindTitleResult(img_url='https://m.media-amazon.com/images/M/MV5BM2U4NTVlMTgtM2FiOS00MzczLWI4Y2EtMDk3ZjJkOTgyMGM0XkEyXkFqcGdeQXVyNjczMzgwMDg@._V1_UX32_CR0,0,32,44_AL_.jpg', title_url='https://www.imdb.com/title/tt10702760/', text='National Theatre Live: Fleabag (2019)'),
                          IMDBFindTitleResult(img_url='https://m.media-amazon.com/images/M/MV5BOTQzZTRlNjAtZjM5Mi00NDQ0LWIyYjUtY2ExNmQ5OGJlNGMyXkEyXkFqcGdeQXVyOTI2MTMwMDc@._V1_UY44_CR13,0,32,44_AL_.jpg', title_url='https://www.imdb.com/title/tt7305642/', text='Fleabag (2017) (TV Episode) - CBeebies Bedtime Story (2004) (TV Series)')]


class RunScraperTests(TestCase):

    tv_dir = DATA_DIR.joinpath('tv')

    @classmethod
    def setUpTestData(cls):
        cls.archer = IMDBTitleSearchData.objects.create(
            type='TV',
            title='Archer',
            rating=8.6,
            blurb='Covert black ops and espionage take a back seat to zany personalities and relationships between secret agents and drones.',
            find_results='<ul><li><a href="https://www.imdb.com//title/tt1486217/">Archer (2009) (TV Series)</a></li>\n<li><a href="https://www.imdb.com//title/tt0060490/">Harper (1966) aka "Archer"</a></li>\n</ul>',
            file_path=str((cls.tv_dir / 'Archer').resolve()),
            file_mtime=1604372147,
            file_ctime=1604372147
        )

    def setUp(self):
        self.tv_dir.mkdir()

    def tearDown(self):
        if self.tv_dir.is_dir():
            rmtree(self.tv_dir)
        movie_dir = DATA_DIR.joinpath('movies')
        if movie_dir.is_dir():
            rmtree(movie_dir)

    @patch('imdb_info_local.management.commands.run_scraper.time.sleep')
    def test_process_dir_tv_title_already_exists(self, time_sleep_mock):
        """Ensure title is not inserted if we have same title and type."""
        # This system expects unique titles for each type - movies and tv
        # ie there can't be two movies with the same title
        # this is enforced easily by adding the year to the title which we expect
        # but is not necessary
        # note this is overkill - as the year is expected, but what the hell
        archer_dir = self.tv_dir.joinpath('Archer')
        archer_dir.mkdir()
        added = process_directory(self.tv_dir, 'TV')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 1)
        self.assertEqual(IMDBTitleSearchData.objects.filter(title='Archer')[0], self.archer)
        self.assertSequenceEqual(added, [])

    @patch('imdb_info_local.management.commands.run_scraper.time.sleep')
    @patch('imdb_info_local.management.commands.run_scraper.get_imdb_title_data')
    def test_process_dir_tv_new_title(self, get_imdb_title_data_mock, time_sleep_mock):
        get_imdb_title_data_mock.return_value = IMDBTitleSearchResults(
            title='Fleabag',
            find_results=fleabag_search_results,
            title_data=IMDBTitleData(
                rating=8.7,
                blurb='A comedy series adapted from the award-winning play about a young woman trying to cope with life in London whilst coming to terms with a recent tragedy.',
                image_file=Path('/tmp/archer.jpg')
            )
        )
        fleabag_dir = self.tv_dir.joinpath('Fleabag')
        fleabag_dir.mkdir()

        added = process_directory(self.tv_dir, 'TV')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 2)
        fleabag = IMDBTitleSearchData.objects.get(title='Fleabag')
        self.assertEqual(fleabag.title, 'Fleabag')
        self.assertEqual(fleabag.rating, 8.7)
        self.assertEqual(fleabag.blurb, 'A comedy series adapted from the award-winning play about a young woman trying to cope with life in London whilst coming to terms with a recent tragedy.')
        self.assertSequenceEqual(added, ['Fleabag'])

    @patch('imdb_info_local.management.commands.run_scraper.time.sleep')
    @patch('imdb_info_local.management.commands.run_scraper.get_imdb_title_data')
    def test_process_dir_movie_where_title_exists_for_tv(self, get_imdb_title_data_mock, time_sleep_mock):
        """Ensure we insert a movie if there is the same title tv show,
        but we do not insert a tv show if there is one with the same name
        """
        # it is fine for a movie and tv show to have the same name
        # again - this constraint is also down to my usage as consisting
        # of all movies in one dir and all tv in another dir
        # so there can't be a dup, and if we find one it is wrong
        get_imdb_title_data_mock.return_value = IMDBTitleSearchResults(
            title='Archer',
            # doesn't matter - reuse these results - can't be empty
            find_results=fleabag_search_results,
            title_data=IMDBTitleData(
                rating=8.0,
                blurb='There should be an Archer movie anyway.',
                image_file=Path('/tmp/archer.jpg')
            )
        )
        movie_dir = DATA_DIR.joinpath('movies')
        movie_dir.mkdir()
        archer_movie_dir = movie_dir.joinpath('Archer')
        archer_movie_dir.mkdir()

        added = process_directory(movie_dir, 'MO')
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
        removed_titles = remove_title_data_for_deleted_files(self.tv_dir, 'TV')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 1)
        self.assertEqual(IMDBTitleSearchData.objects.filter(title='Archer', type='TV').count(), 1)
        self.assertSequenceEqual(removed_titles, [])

    def test_remove_title_data_for_deleted_files_removal_needed(self):
        fleabag_dir = self.tv_dir.joinpath('Fleabag')
        fleabag_dir.mkdir()
        removed = remove_title_data_for_deleted_files(self.tv_dir, 'TV')
        self.assertEqual(IMDBTitleSearchData.objects.count(), 0)
        self.assertSequenceEqual(removed, ['Archer'])


class MultipleDirectoriesTestNoDB(SimpleTestCase):
    """Directory structure created for this test:

├── movie-dir-1
│   ├── A-Girl-Walks-Home-Alone-At-Night-2014
│   └── Absolutely-Fabulous-the-Movie-2016
├── tv-dir-1
│   ├── American-Dad
│   └── Archer
└── tv-dir-2
    ├── Avenue-5-2020
    └── Awkwafina-Is-Nora-From-Queens
    """

    tempdir = DATA_DIR / 'temp'
    tv_dir_1, tv_dir_2, movie_dir_1 = tempdir / 'tv-dir-1', tempdir / 'tv-dir-2', tempdir / 'movie-dir-1'
    video_dirs_settings = {
        'TV': [str(tv_dir_1), str(tv_dir_2)],
        'Movies': [str(movie_dir_1)]
    }
    movie_dir_names = [
        'A-Girl-Walks-Home-Alone-At-Night-2014',
        'Absolutely-Fabulous-the-Movie-2016',
    ]
    tv_dir_names = [
        'American-Dad',
        'Archer',
        'Avenue-5-2020',
        'Awkwafina-Is-Nora-From-Queens',
    ]

    def setUp(self) -> None:
        for dirpath in (self.tv_dir_1, self.tv_dir_2, self.movie_dir_1):
            dirpath.mkdir(parents=True)
        for name in self.tv_dir_names[:2]:
            (self.tv_dir_1 / name).mkdir()
        for name in self.tv_dir_names[2:]:
            (self.tv_dir_2 / name).mkdir()
        for name in self.movie_dir_names:
            (self.movie_dir_1 / name).mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    @patch('imdb_info_local.management.commands.run_scraper.time.sleep')
    @patch('imdb_info_local.management.commands.run_scraper.get_imdb_title_data')
    @patch('imdb_info_local.management.commands.run_scraper.add_image_file')
    @patch('imdb_info_local.management.commands.run_scraper.IMDBTitleSearchData')
    def test_process_directory_w_multiple_titles(self, TitleSearchDataMock, add_image_file_mock, get_imdb_title_data_mock,
               time_sleep_mock):
        # os.system(f'find {self.tempdir} -print')
        # os.system(f'tree {self.tempdir}')
        with self.settings(IMDB_INFO_LOCAL_VIDEO_DIRS=self.video_dirs_settings):
            # print(f'IMDB_INFO_LOCAL_VIDEO_DIRS:\n{settings.IMDB_INFO_LOCAL_VIDEO_DIRS}')
            TitleSearchDataMock.mock_add_spec(IMDBTitleSearchData)
            TitleSearchDataMock.objects.filter.return_value = False
            added_titles = process_directory(self.movie_dir_1)
            self.assertSequenceEqual(added_titles,
                                     ['A Girl Walks Home Alone At Night 2014', 'Absolutely Fabulous the Movie 2016'])
            # call_args will only contain the args from the last call of the mock
            self.assert_(TitleSearchDataMock.call_args.kwargs['title'] == 'Absolutely Fabulous the Movie 2016')


class MultipleDirectoriesTest(TestCase):
    """Integration test - scrapes IMDB for 2 titles - so could fail due to network issues, etc.

    Directory structure created for these tests:

    ├── movie-dir-1
    │   ├── A-Girl-Walks-Home-Alone-At-Night-2014
    │   └── Absolutely-Fabulous-the-Movie-2016
    ├── tv-dir-1
    │   ├── American-Dad
    │   └── Archer
    └── tv-dir-2
    ├── Avenue-5-2020
    └── Awkwafina-Is-Nora-From-Queens
    """
    tempdir = DATA_DIR / 'temp'
    tv_dir_1, tv_dir_2, movie_dir_1 = tempdir / 'tv-dir-1', tempdir / 'tv-dir-2', tempdir / 'movie-dir-1'
    video_dirs_settings = {
        'TV': [str(tv_dir_1), str(tv_dir_2)],
        'Movies': [str(movie_dir_1)]
    }
    movie_dir_names = [
        'A-Girl-Walks-Home-Alone-At-Night-2014',
        'Absolutely-Fabulous-the-Movie-2016',
    ]
    tv_dir_names = [
        'American-Dad',
        'Archer',
        'Avenue-5-2020',
        'Awkwafina-Is-Nora-From-Queens',
    ]
    fixtures = ['imdb_info_local_one_tv_dir.yaml']

    def setUp(self) -> None:
        for dirpath in (self.tv_dir_1, self.tv_dir_2, self.movie_dir_1):
            dirpath.mkdir(parents=True)
        for name in self.tv_dir_names[:2]:
            (self.tv_dir_1 / name).mkdir()
        for name in self.tv_dir_names[2:]:
            (self.tv_dir_2 / name).mkdir()
        for name in self.movie_dir_names:
            (self.movie_dir_1 / name).mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_run_scraper_adds_titles_correctly_from_one_dir_only(self):
        """In a scenario where there are 2 tv directories with the titles from
        one in the db and the other not in the db, add the correct titles to the db.
        Also, don't remove any titles.  In this case there is a movie dir with titles
        in the db as well."""
        titles = [obj.title for obj in IMDBTitleSearchData.objects.all()]
        self.assertSetEqual(
            set(titles),
            {'A Girl Walks Home Alone At Night 2014', 'Absolutely Fabulous the Movie 2016', 'American Dad', 'Archer'}
        )
        with self.settings(IMDB_INFO_LOCAL_VIDEO_DIRS=self.video_dirs_settings):
            call_command('run_scraper')
            titles = [obj.title for obj in IMDBTitleSearchData.objects.all()]
            self.assertSetEqual(
                set(titles),
                {'A Girl Walks Home Alone At Night 2014', 'Absolutely Fabulous the Movie 2016', 'American Dad',
                 'Archer', 'Avenue 5 2020', 'Awkwafina Is Nora From Queens'}
            )

    def test_run_scraper_does_not_remove_titles_when_dir_is_not_available(self):
        """In a scenario where there is one tv dir with titles in the db but the dir does not
        exist (e.g. a disk is not mounted), make sure titles in that dir are not deleted"""
        titles = [obj.title for obj in IMDBTitleSearchData.objects.all()]
        self.assertSetEqual(
            set(titles),
            {'A Girl Walks Home Alone At Night 2014', 'Absolutely Fabulous the Movie 2016', 'American Dad', 'Archer'}
        )
        shutil.rmtree(self.tv_dir_1)
        shutil.rmtree(self.tv_dir_2)
        with self.settings(IMDB_INFO_LOCAL_VIDEO_DIRS=self.video_dirs_settings):
            call_command('run_scraper')
            titles = [obj.title for obj in IMDBTitleSearchData.objects.all()]
            self.assertSetEqual(
                set(titles),
                {'A Girl Walks Home Alone At Night 2014', 'Absolutely Fabulous the Movie 2016', 'American Dad',
                 'Archer'}
            )
