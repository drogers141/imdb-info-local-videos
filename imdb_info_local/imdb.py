import re
from dataclasses import dataclass
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

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


@dataclass
class IMDBFindTitleResult:
    img_url: str
    title_url: str
    text: str

    def __str__(self):
        return self.text


def imdb_title_search_results(title: str) -> [IMDBFindTitleResult]:
    """Searches for a title.

    Uses IMDB's search page to query for title and scrapes the results page.
    Returns list of candidates in order.

    As of Oct 26, 2022, the html page returned from requests may have an
    alternate html format.  This is handled by _title_search_results_alternate_html.

    :return [IMDBFindTitleResult]
    """
    name_query = title.replace(' ', '+')
    url = f'https://www.imdb.com/find?q={name_query}'
    soup = parse_html_for_url(url)
    results_table = soup.find('table', class_='findList')
    titles = []
    if results_table:
        rows = results_table.find_all('tr')
        logger.info(f'{title} - results table found -- {len(rows)} rows')
        for tr in rows:
            img_url = tr.td.img['src']
            relative_url = tr.find_all('td')[1].a['href']
            title_url = f'https://www.imdb.com{relative_url}'
            text = tr.find_all('td')[1].text.strip()
            titles.append(IMDBFindTitleResult(img_url, title_url, text))
    else:
        results_section = soup.find('section', attrs={'data-testid':'find-results-section-title'})
        if results_section:
            titles = _title_search_results_alternate_html(title, results_section)
    return titles


def _title_search_results_alternate_html(title: str, section_soup) -> [IMDBFindTitleResult]:
    """Updated Oct 2022 - requests scraper returns a different html format
     - sometimes (even with Firefox user agent)
    """
    titles = []
    li_tags = [tag for tag in section_soup.find('ul').children if tag.name == 'li']
    logger.info(f'{title} - results section found - {len(li_tags)} li_tags')
    for li_tag in li_tags:
        img_url = _largest_image_from_img_tag(li_tag.find('img'))
        if not img_url:
            continue
        title_url = _title_url_from_li_tag(li_tag)
        text = re.sub(r'\s\s+', ' ', li_tag.text).strip()
        # text = li_tag.text.replace('\n', '')
        titles.append(IMDBFindTitleResult(img_url=img_url, title_url=title_url, text=text))
    return titles

def _largest_image_from_img_tag(img_tag: BeautifulSoup) -> str:
    img_urls = re.findall(r'https[^ ]+', img_tag['srcset']) if img_tag else None
    return img_urls[-1] if img_urls else None

def _title_url_from_li_tag(li_soup):
    a_tag = li_soup.find('a', href=re.compile('/title/.*'))
    relative_url = a_tag['href']
    return f'https://www.imdb.com{relative_url}'


@dataclass
class IMDBTitleData:
    rating: str
    blurb: str
    image_file: Path

    def __str__(self):
        return f'{self.rating}\n{self.blurb}'


def filename_stem_from_title_url(title_url: str) -> str:
    parse_result = urlparse(title_url)
    m = re.match('/title/([^/]+)/', parse_result.path)
    if m:
        return m.groups()[0]


def imdb_title_data(title_url: str) -> IMDBTitleData:
    """Scrapes IMDB page for rating and title info.

    :param - title_url - url of IMDB's page for the title.
    :return IMDBTitleData - ie - rating and blurb (summary)
    """
    soup = parse_html_for_url(title_url)
    ratings_div = soup.find('div', attrs={'data-testid': "hero-rating-bar__aggregate-rating__score"})
    rating = ratings_div.text if ratings_div else 'N/A'
    plot_p = soup.find('span', attrs={'data-testid': 'plot-l'})
    if plot_p and plot_p.text:
        blurb = plot_p.text
    else:
        blurb = f'No blurb for title_url: <a href="{title_url}">{title_url}</a>'
    if not blurb:
        logger.info(f'no blurb: title_url: {title_url}\n')
    image_filename_stem = filename_stem_from_title_url(title_url)
    image_file = imdb_title_image_file(soup, image_filename_stem)
    return IMDBTitleData(rating, blurb, image_file)


def imdb_title_image_file(html_soup: BeautifulSoup, filename_stem: str) -> Path:
    """Parses html for image url, downloads and stores image locally.

    :param html_soup - Beautiful soup parsed html
    :param filename_stem - base filename for image file without extension
    :return Path to local image file or None
    """
    img_list = html_soup.select('img.ipc-image')
    if img_list:
        img_url = img_list[0]['src']
        filename = filename_stem + Path(urlparse(img_url).path).suffix
        local_file = f'/tmp/{filename}'
        r = requests.get(img_url)
        with open(local_file, 'wb') as f:
            f.write(r.content)

        return Path(local_file)
