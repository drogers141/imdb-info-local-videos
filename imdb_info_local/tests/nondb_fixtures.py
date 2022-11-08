from pathlib import Path

from imdb_info_local.imdb import IMDBTitleData, IMDBFindTitleResult

# goes with data/imdb-search-archer.html
archer_find_title_result = IMDBFindTitleResult(
    img_url='https://m.media-amazon.com/images/M/MV5BMTg3NTMwMzY2OF5BMl5BanBnXkFtZTgwMDcxMjQ0NDE@._V1_UX32_CR0,0,32,44_AL_.jpg',
    title_url='https://www.imdb.com/title/tt1486217/',
    text='Archer (2009) (TV Series)'
)

# goes with data/archer-title-page.html
archer_title_data = IMDBTitleData(
    rating='8.7/10',
    blurb='Covert black ops and espionage take a back seat to zany personalities and relationships between secret agents and drones.',
    image_file=Path('/tmp/archer.jpg')
)

archer_find_title_alt_html_format_result = IMDBFindTitleResult(
    img_url='https://m.media-amazon.com/images/M/MV5BMTg3NTMwMzY2OF5BMl5BanBnXkFtZTgwMDcxMjQ0NDE@._V1_QL75_UX100_CR0,1,100,148_.jpg',
    title_url='https://www.imdb.com/title/tt1486217/?ref_=fn_al_tt_0',
    text='Archer 2009– TV Series H. Jon Benjamin, Judy Greer'
)
