"""Tests for possible scrapers
"""
import json
import logging
import os
import sys
from os import environ as env

import requests
from dotenv import load_dotenv

from classes.rom import Rom
from classes.gameinfo import Asset
from scrapers.hfsdb import HFSDB
from scrapers.scraper import Scraper
from scrapers.screenscraper import ScreenScraper
from scrapers.thegamesdb import TheGamesDb

zips = [['Sonic The Hedgehog 2 (World) (Rev A).7z', 'megadrive', 'https://edgeemu.net/down.php?id=12698'],
        [ 'alienar.zip', 'arcade', 'https://www.mamedev.org/roms/alienar/alienar.zip']]

def download_zips():
    """Downloads various romfiles for testing"""

    for f, system, url in zips:
        if os.path.exists('tests/' + f):
            continue
        r = requests.get(url, allow_redirects=True, timeout=15)
        if not r.status_code == 200:
            logging.warning("Couldn't download %s", f)
            continue
        open('tests/' + f, 'wb').write(r.content)

def test_scraper():
    """Test the Scraper base class"""
    my_scraper = Scraper(name = 'ScraperTest',
                baseUrl = 'http://google.fr',
                baseUrlParams = 'lang=fr',
                apiKey = '4pIk3y',
                devUser = 'someUser',
                devPassword = 'somePass',
                user = 'anotherUser',
                password = 'anotherPass')
    logging.info(vars(my_scraper))

def test_screenscraper():
    """Test the ScreenScraper Scraper class"""
    my_sscraper = ScreenScraper(devUser = env['SS_DEVUSER'],
                devPassword = env['SS_DEVPASSWD'],
                user = env['SS_USER'],
                password = env['SS_PASSWD'])
    # print(vars(my_sscraper))
    sonic2_rom = Rom('tests/Sonic The Hedgehog 2 (World) (Rev A).7z')
    rom_info = my_sscraper.getGameInfo(sonic2_rom, 'megadrive')
    if rom_info:
        logging.debug(rom_info.filterOnLang('fr'))
        logging.info(rom_info.getAssetMedia(Asset.TITLE))
        my_sscraper.downloadGameAsset(rom_info.getAssetMedia(Asset.TITLE), 'tests/sonic2_title.' + rom_info.getAssetMedia(Asset.TITLE).extension)

    # print(my_sscraper.download('ssuserInfos.php'))
    # print(my_sscraper.downloadToFile('tests/sonic2_ss.json', 'jeuInfos.php', {'crc': '24ab4c3a'}))
    # my_sscraper.getPlatforms()

def test_tgdb():
    """Test the TGDB Scraper class"""
    my_tgdbcraper = TheGamesDb(apiKey = env['TGDB_APIKEY'])
    # print(vars(my_tgdbcraper))
    print(my_tgdbcraper.download('v1/Games/ByGameID',
    {
        'id': 7504, 
        'fields': 'players,publishers,genres,overview,rating,platform,coop,video,alternates'
    }))
    my_tgdbcraper.downloadToFile('tests/sonic2_tgdb.json', 'v1/Games/ByGameID',
    {
        'id': 7504,
        'fields': 'players,publishers,genres,overview,rating,platform,coop,video,alternates'
    })

def test_hfsdb():
    """ Test the HFSDB Scraper class"""
    my_hfsdb = HFSDB(user = env['HFSDB_USER'], password = env['HFSDB_PASSWD'])
    print(my_hfsdb.download('account'))
    sonic2_rom = Rom('tests/Sonic The Hedgehog 2 (World) (Rev A).7z')
    rom_info = my_hfsdb.getGameInfo(sonic2_rom)
    if rom_info:
        logging.debug("Filtered som:\n%s", rom_info.filterOnLang('fr'))
    # my_hfsdb.getPlatforms()
    my_hfsdb.downloadToFile('tests/sonic2_hfsdb.json', 'games', {'medias__md5': sonic2_rom.md5sum})

    for rom_file, system, url in zips:
        param = ''
        rom = Rom('tests/' + rom_file)
        file_name_no_ext = os.path.splitext(rom_file)[0]
        json_filename = 'tests/{}_{}.json'.format(file_name_no_ext, my_hfsdb.name)
        if system == 'arcade':
            param = {'medias__description': file_name_no_ext}
        else:
            param = {'medias__md5': rom.md5}
        with open(json_filename, 'w', encoding="utf8") as f:
            json.dump(json.loads(my_hfsdb.download('games', param)['content']), f, indent=4)
        my_hfsdb.downloadGameAsset(rom_info.getAssetMedia(Asset.VIDEO), rom.romname + '_title.' + rom_info.getAssetMedia(Asset.VIDEO).extension)

LOGGING_LEVEL = logging.DEBUG
if LOGGING_LEVEL == logging.DEBUG:
    logging.basicConfig(stream=sys.stdout, level=LOGGING_LEVEL, datefmt='%Y-%m-%d %H:%M:%S',
        format='[%(levelname)s] %(filename)s/%(funcName)s(%(lineno)d): %(message)s')
else:
    logging.basicConfig(stream=sys.stdout, level=LOGGING_LEVEL)

if not load_dotenv(verbose=True):
    logging.warning("Couldn't load_dotenv()")

download_zips()
test_scraper()
# test_screenscraper()
# test_tgdb()
test_hfsdb()

#####NEED TO TEST ARCADE AND CONSOLE ROM
