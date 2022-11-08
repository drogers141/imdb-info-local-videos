from unittest import TestCase
from unittest.mock import patch, Mock
from pathlib import Path

from bs4 import BeautifulSoup

from imdb_info_local.imdb import (imdb_title_data, imdb_title_search_results, imdb_title_image_file,
                                  IMDBFindTitleResult, IMDBTitleData)
from imdb_info_local.utils import soup_from_local_file
from .nondb_fixtures import (archer_find_title_result, archer_title_data,
                             archer_find_title_alt_html_format_result)

DATA_DIR = Path(__file__).parent / 'data'



class IMDBScrapingTests(TestCase):

    @patch('imdb_info_local.imdb.parse_html_for_url')
    def test_imdb_title_search_results(self, mock_soup):
        mock_soup.return_value = soup_from_local_file(
            DATA_DIR.joinpath('imdb-search-archer.html')
        )
        title_search_results = imdb_title_search_results('Archer')
        self.assertEqual(len(title_search_results), 2)
        self.assertEqual(title_search_results[0], archer_find_title_result)

    @patch('imdb_info_local.imdb.parse_html_for_url')
    def test_imdb_title_search_no_results(self, mock_soup):
        """Test when there are no results in the search page."""
        mock_soup.return_value = soup_from_local_file(
            DATA_DIR.joinpath('imdb-search-looney-tunes-golden-collection.html')
        )
        title_search_results = imdb_title_search_results('Looney Tunes Golden Collection')
        self.assertEqual(len(title_search_results), 0)

    @patch('imdb_info_local.imdb.parse_html_for_url')
    def test_imdb_title_search_results_alt_html_format(self, mock_soup):
        mock_soup.return_value = soup_from_local_file(
            DATA_DIR.joinpath('imdb-search-archer-alt-html-format.html')
        )
        title_search_results = imdb_title_search_results('Archer')
        self.assertEqual(len(title_search_results), 5)
        self.assertEqual(title_search_results[0], archer_find_title_alt_html_format_result)


    @patch('imdb_info_local.imdb.imdb_title_image_file')
    @patch('imdb_info_local.imdb.parse_html_for_url')
    def test_imdb_title_data(self, mock_soup, mock_imdb_title_image_file):
        mock_soup.return_value = soup_from_local_file(
            DATA_DIR.joinpath('archer-title-page.html')
        )
        mock_imdb_title_image_file.return_value = Path('/tmp/archer.jpg')
        title_data = imdb_title_data('https://www.imdb.com/title/tt1486217/')
        self.assertEqual(title_data, archer_title_data)

    @patch('imdb_info_local.imdb.requests.get')
    def test_imdb_title_image_file(self, mock_get):
        mock_get.return_value = Mock(ok=True)
        test_image_path = DATA_DIR / 'archer.jpg'
        archer_html_soup = soup_from_local_file(
            DATA_DIR.joinpath('archer-title-page.html')
        )
        with open(test_image_path, 'rb') as img_fp:
            mock_get.return_value.content = img_fp.read()
            saved_image_path = imdb_title_image_file(archer_html_soup, 'archer')
            self.assertEqual(saved_image_path, Path('/tmp/archer.jpg'))
