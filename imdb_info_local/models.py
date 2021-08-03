from django.db import models


class IMDBTitleSearchData(models.Model):
    """Data for one movie or tv series title

    The way the title data search happens:
    1 - get "title" from local filename - probably ends with year made
    2 - do a search for this title at IMDB
    3 - pick the first title found in that search
    4 - scrape for ratings and blurb at the url for that title

    Most are obvious.
    type - either movie or tv series
    title - as described above
    rating - imdb rating string - e.g. '7.5/10' - may be empty
    blurb - descriptive blurb about the title - may be empty
    imdb_title_url - url that was selected from the title search
        - this is saved to check if the title doesn't seem right
        - it is also available as the first url in find_results
    find_results - this is the list returned from the title search, saved as
        html (an unordered list).  This is kept in case the title
        retrieved is not correct, so this can be shown to the user to select a
        different title.
    file_* - file path and stat on the directory or file containing the tv series
        or movie
    """
    TV = "TV"
    MOVIE = "MO"
    title_type_choices = (
        ('TV', 'TV'),
        ('MO', 'Movie')
    )
    type = models.CharField(max_length=2, choices=title_type_choices)
    title = models.CharField(max_length=512)
    rating = models.CharField(max_length=32)
    blurb = models.TextField()
    imdb_title_url = models.CharField(max_length=256)
    find_results = models.TextField()
    file_path = models.CharField(max_length=512)
    file_mtime = models.BigIntegerField()
    file_ctime = models.BigIntegerField()

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    def verbose_str(self):
        return (f'{self.title}\nrating: {self.rating} - type: {self.type}\n{self.blurb}\n' +
                f'find_results:\n{self.find_results}')
