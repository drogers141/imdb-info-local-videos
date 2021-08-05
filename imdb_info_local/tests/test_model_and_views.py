from django.test import TestCase
from django.urls import reverse

from imdb_info_local.models import IMDBTitleSearchData


class IMDBTitleSearchDataTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.movie = IMDBTitleSearchData.objects.create(
            title='The Corporation 2003',
            rating='8.0/10',
            blurb='Documentary that looks at the concept of the corporation throughout recent history up to its present-day dominance.',
            type=IMDBTitleSearchData.MOVIE,
            find_results='<ul><li><a href="https://www.imdb.com//title/tt0379225/">The Corporation (2003)</a></li>\n<li><a href="https://www.imdb.com//title/tt5616634/">The Corporation (in development)</a></li>\n</ul>',
            file_path='/Volumes/dr-wd-2/movies/The-Corporation-2003',
            file_mtime=1625099099,
            file_ctime=1628018383
        )
        cls.tv = IMDBTitleSearchData.objects.create(
            title='Archer',
            rating='8.6/10',
            blurb='Covert black ops and espionage take a back seat to zany personalities and relationships between secret agents and drones.',
            type=IMDBTitleSearchData.TV,
            find_results='<ul><li><a href="https://www.imdb.com//title/tt1486217/">Archer (2009) (TV Series)</a></li>\n<li><a href="https://www.imdb.com//title/tt0060490/">Harper (1966) aka "Archer"</a></li>\n</ul>',
            file_path='/Volumes/dr-wd-2/tv/Archer',
            file_mtime=1604372147,
            file_ctime=1604372147,
        )

    def test_model(self):
        self.assertEqual(self.movie.verbose_str(),
                         'The Corporation 2003\nrating: 8.0/10 - type: MO\nDocumentary that looks at the concept of the corporation throughout recent history up to its present-day dominance.\nfind_results:\n<ul><li><a href="https://www.imdb.com//title/tt0379225/">The Corporation (2003)</a></li>\n<li><a href="https://www.imdb.com//title/tt5616634/">The Corporation (in development)</a></li>\n</ul>')
        self.assertEqual(self.movie.file_path, '/Volumes/dr-wd-2/movies/The-Corporation-2003')
        self.assertEqual(self.movie.file_mtime, 1625099099)
        self.assertEqual(self.movie.file_ctime, 1628018383)

    def test_movie_list(self):
        response = self.client.get(reverse('movie_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documentary that looks at the concept of the corporation')
        self.assertTemplateUsed(response, 'imdb_info_local/titles.html')

    def test_tv_list(self):
        response = self.client.get(reverse('tv_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Covert black ops and espionage take a back seat')
        self.assertTemplateUsed(response, 'imdb_info_local/titles.html')

    def test_movie_mtime_list(self):
        response = self.client.get(reverse('movie_mtime'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documentary that looks at the concept of the corporation')
        self.assertTemplateUsed(response, 'imdb_info_local/titles.html')

    def test_tv_mtime_list(self):
        response = self.client.get(reverse('tv_mtime'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Covert black ops and espionage take a back seat')
        self.assertTemplateUsed(response, 'imdb_info_local/titles.html')
        