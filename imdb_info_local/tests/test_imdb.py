from unittest import TestCase
from unittest.mock import patch
from pathlib import Path

from bs4 import BeautifulSoup

from imdb_info_local.imdb import (imdb_title_data, imdb_title_search_results,
                                  IMDBFindTitleResult, IMDBTitleData)
from .nondb_fixtures import archer_find_title_result, archer_title_data

DATA_DIR = Path(__file__).parent.joinpath('data')


def soup_from_local_file(path):
    return BeautifulSoup(open(path).read(), 'html.parser')


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
    def test_imdb_title_data(self, mock_soup):
        mock_soup.return_value = soup_from_local_file(
            DATA_DIR.joinpath('archer-title-page.html')
        )
        title_data = imdb_title_data('https://www.imdb.com/title/tt1486217/')
        self.assertEqual(title_data, archer_title_data)
