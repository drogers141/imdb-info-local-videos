# IMdb Info for Local Videos

This is a website meant to work on a local machine where you have movies and tv series on disk or on 
the computer and want IMdb ratings and summaries available for them.  It is implemented as a Django
application, and is not secured for remote deployment.

## Requirements

The site works best if there is one directory containing movie videos, and one directory containing tv 
series.  Within each directory each title must have its video or series of videos in a directory with
the title in title capitalization with dashes delimiting each word.  It is recommended that the title
ends with the year as shown in IMdb as it will help the algorithm pick the right title, but this
is not necessary.
```
/path/to/movies/Black-Widow-2021
/path/to/movies/Blade-Runner-1982
/path/to/movies/Blade-Runner-2049-2017
...
/path/to/tv/Archer
/path/to/tv/Dead-Pixels-2019
/path/to/tv/Fleabag
```

### Update to above

Now you can run the management command ```run_scraper``` with an argument of any directory and the type
of title - tv or movie.  However, if you stick to the config method above - and the instructions below,
running the scraper will sync the website to the movie and tv directories' contents.  That is it removes
any titles from the database that are no longer in the directory.

## Setup
This is a Django application, so config is in a settings.py file.  In this case it is:
```
config/settings.py
```
Set the tv and movie directory variables to your needs:
```
# Directories where tv and movie files are located
TV_DIRECTORY = '/Volumes/dr-wd-2/tv'
MOVIE_DIRECTORY = '/Volumes/dr-wd-2/movies'

```

For now this is not dockerized, so a postgresql database needs to be installed and you must have access 
to a psql shell as a superuser.  To create the database follow instructions in:
```
create_db
```
You can also change the database settings in the settings.py of course if you know how.

The project uses pipenv to manage python dependencies. So from the root directory run:
```
# install pipenv in your system (see pipenv docs)
pip install --user pipenv

# create virtual environment and install deps
pipenv install 
```

## Running
There are scripts in the bin/ directory to run the scraper, the webserver, and clearing all data from
the system, so add the bin/ directory to your PATH.

Run the scraper or clear all data from scripts:
```
bin/imdb_info_local_run_scraper

bin/imdb_info_local_clear_data
```

You can also run the django management commands directly from the root dir:
```
# see options for scraper
pipenv run python manage.py run_scraper -h

# clear data is straightforward
pipenv run python manage.py clear_data

```
Run the scraper any time videos are added or removed from the specified directories to remain in sync.
Or run it with params to add videos from other dirs.

Run the website:
```
# script runs on localhost:8002
bin/imdb_info_local_runserver

# or directly
pipenv python manage.py runserver [port]
```

Navigation at the top right of the page shows pages available:

- Movies - movies ordered alphabetically
- TV - tv series ordered alphabetically
- Movies mtime - movies ordered by most recently added (file mtime of the directory holding the movie)
- TV mtime - tv series ordered by most recently added

The website allows you to correct the rating and summary for a title if the wrong one was chosen by the
algorithm.  If you click the ratings/title area for a title, the list of titles
found in the title search will be shown. You can update with one of
the listed title urls or enter a title url in the bottom to update the info.
