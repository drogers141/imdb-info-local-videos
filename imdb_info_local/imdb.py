import re
from dataclasses import dataclass
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def parse_html_for_url(url):
    r = requests.get(url)
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
    :return [IMDBFindTitleResult]
    """
    name_query = title.replace(' ', '+')
    url = f'https://www.imdb.com/find?q={name_query}'
    soup = parse_html_for_url(url)
    results_table = soup.find('table', class_='findList')
    titles = []
    if results_table:
        for tr in results_table.find_all('tr'):
            img_url = tr.td.img['src']
            relative_url = tr.find_all('td')[1].a['href']
            title_url = f'https://www.imdb.com{relative_url}'
            text = tr.find_all('td')[1].text.strip()
            titles.append(IMDBFindTitleResult(img_url, title_url, text))
    return titles


@dataclass
class IMDBTitleData:
    rating: str
    blurb: str

    def __str__(self):
        return f'{self.rating}\n{self.blurb}'


def imdb_title_data(title_url: str) -> IMDBTitleData:
    """Scrapes IMDB page for rating and title info.

    :param - title_url - url of IMDB's page for the title.
    :return IMDBTitleData - ie - rating and blurb (summary)
    """
    soup = parse_html_for_url(title_url)
    ratings_div = soup.find('div', class_=re.compile('^AggregateRatingButton__Rating.*'))
    rating = ratings_div.text if ratings_div else 'N/A'
    plot_p = soup.find('span', class_=re.compile('^GenresAndPlot__TextContainerBreakpointXL.*'))
    if plot_p and plot_p.text:
        blurb = plot_p.text
    else:
        blurb = f'No blurb for title_url: <a href="{title_url}">{title_url}</a>'
    if not blurb:
        logger.info(f'no blurb: title_url: {title_url}\n')
    return IMDBTitleData(rating, blurb)