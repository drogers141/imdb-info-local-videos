import requests
from bs4 import BeautifulSoup
from pathlib import Path
import os


def save_to_local_file(url, filename):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    with open(filename, "w") as outfile:
        outfile.write(str(soup))


def create_subdirs_from_title_list(title_list: Path, output_dir: Path):
    """Creates an empty subdir for each line in title_list in output_dir
    """
    if not output_dir.is_dir():
        output_dir.mkdir()
    for title in open(title_list):
        title = title.strip()
        if title:
            output_dir.joinpath(title).mkdir()
