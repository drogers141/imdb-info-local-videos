import requests
from bs4 import BeautifulSoup


def save_to_local_file(url, filename):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    with open(filename, "w") as outfile:
        outfile.write(str(soup))
