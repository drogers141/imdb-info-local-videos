import requests
from bs4 import BeautifulSoup
from pathlib import Path
import os

__all__ = ('parse_html_for_url', 'save_to_local_file', 'create_subdirs_from_title_list',
           'soup_from_local_file')

# Oct 26, 2022 - may need to update
# Use this user agent to ensure the page we scrape is roughly as expected
FIREFOX_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:106.0) Gecko/20100101 Firefox/106.0'


def parse_html_for_url(url):
    r = requests.get(
        url,
        headers={'User-Agent': FIREFOX_USER_AGENT}
    )
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup


def save_to_local_file(url, filename):
    page = parse_html_for_url(url)
    soup = BeautifulSoup(page.content, "html.parser")
    with open(filename, "w") as outfile:
        outfile.write(str(soup))


def soup_from_local_file(path):
    with open(path) as instream:
        return BeautifulSoup(instream.read(), 'html.parser')


def save_soup_to_local_file(soup, filename):
    with open(filename, 'w') as outstream:
        outstream.write(soup.prettify())


def create_subdirs_from_title_list(title_list: str, output_dir: str):
    """Creates an empty subdir for each line in title_list in output_dir
    """
    output_dir_path = Path(output_dir)
    if not output_dir_path.is_dir():
        output_dir_path.mkdir()
    for title in open(title_list):
        title = title.strip()
        if title:
            output_dir_path.joinpath(title).mkdir()
