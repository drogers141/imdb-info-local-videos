from pathlib import Path
import os

from django.db import models
from django.core.files import File


class IMDBTitleSearchData(models.Model):
    """Data for one movie or tv series title

    The way the title data search happens:
    1 - get "title" from local filename - probably ends with year made
    2 - do a search for this title at IMDB
    3 - pick the first title found in that search
    4 - scrape for ratings, blurb and image at the url for that title

    Most are obvious.
    type - either movie or tv series
    title - as described above
    rating - imdb rating string - e.g. '7.5/10' - may be empty
    blurb - descriptive blurb about the title - may be empty
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
    image = models.ImageField(upload_to='title-images/', blank=True)
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


def add_image_file(title_data_model: IMDBTitleSearchData, image_path: Path):
    """Add the image file to the model

    :param image_path - path to locally saved image file
    """
    with open(image_path, 'rb') as fp:
        django_file = File(fp)
        title_data_model.image.save(str(image_path.name), django_file, save=True)


def update_image_file(title_data_model: IMDBTitleSearchData, image_path: Path):
    """Update the image file for the model

    :param image_path - path to locally saved image file
    """
    with open(image_path, 'rb') as fp:
        print(f'image_path: {image_path}')
        django_file = File(fp)
        if Path(title_data_model.image.path).exists():
            print(f'deleting: {title_data_model.image.path}')
            os.remove(title_data_model.image.path)
            print(f'saving: {str(image_path.name)}')
            title_data_model.image.save(str(image_path.name), django_file, save=True)
