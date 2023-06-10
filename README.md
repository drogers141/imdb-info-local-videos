# IMdb Info for Local Videos

This is a website meant to work on a local machine where you have movies and tv series on disk or on 
the computer and want IMDb ratings and summaries available for them.  It is implemented as a Django
application, and is not secured for remote deployment.

## Storage of tracked videos

The site keeps track of a list of directories holding movies, and a list of directories holding tv
shows.  Each video being tracked must have its own directory, named with the title of the video using
title capitalization and delimited by dashes.  It is recommended that the title
ends with the year as shown in IMdb as it will help the algorithm pick the right title, but this
is not necessary.

For example, if you had the following directories holding collections of videos:
```
/path/to/movies-1
/path/to/movies-2
/path/to/tv-1
```
You could have tracked movies and tv shows in the following directories:
```
/path/to/movies-1/Black-Widow-2021
/path/to/movies-1/Blade-Runner-1982
/path/to/movies-2/Blade-Runner-2049-2017
...
/path/to/tv-1/Archer
/path/to/tv-1/Dead-Pixels-2019
/path/to/tv-1/Fleabag
```

### Syncing directories not configured

You can also run the management command ```run_scraper``` with an argument of an arbitrary 
directory and the type of title - tv or movie - to add videos to the database or to update.

## Setup
This is a Django application, so config is in a settings.py file.  In this case it is:
```
config/settings.py
```
Create a dictionary IMDB_INFO_LOCAL_VIDEO_DIRS containing a list of movie and tv directories.  
Following the above:
```
IMDB_INFO_LOCAL_VIDEO_DIRS = {
    'TV': [
        '/path/to/tv-1',
    ],
    'Movies': [
        '/path/to/movies-1',
        '/path/to/movies-2',
    ]
}
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

Run the scraper (update) or clear all data from scripts:
```
bin/imdb_info_local_update

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
