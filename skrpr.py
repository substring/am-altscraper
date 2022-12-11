#!/usr/bin/env python3
# am-altscraper.py
#
# An alternative scraper game info for Attract Mode using the screenscraper.fr API
#
# Copyright 2017 Alfonso Saavedra "Son Link" <sonlink.dourden@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import argparse
import glob
import os
import sys

import logging
import systems

from classes.rom import Rom
from classes.gameinfo import Asset
from frontends.frontend import FrontEnd
from frontends.attractmode import AttractMode
from scrapers.scraper import Scraper
from scrapers.screenscraper import ScreenScraper
from scrapers.hfsdb import HFSDB

from os import environ as env

import requests
from dotenv import load_dotenv

#reload(sys)
#sys.setdefaultencoding("utf-8")

langs = {
    'en': 'us',
    'es': 'sp',
    'fr': 'fr',
    'de': 'de'
}
regions = ['eu', 'us', 'jp']
folders = ['snap', 'wheel', 'flyer', 'video', 'marquee']
LOGGING_LEVELS = [
    logging.INFO,
    logging.DEBUG,
    logging.NOTSET
]

# Extensions should be done according to the http header of the website request
possibleMediaData = {'snap': 'png', 'video': 'mp4', 'marquee': 'png', 'wheel': 'png', 'box2d': 'png', 'box3d': 'png'}
specificMediaFolders = {'box2d': 'flyers', 'box3d': 'flyers'}

parser = argparse.ArgumentParser(description='A scraper for AttractMode', epilog="--system and --romsdir are mandatory if you don't use --emulator")
parser.add_argument("--box2d", help="Download box art (if avaliable)", action='store_true')
parser.add_argument("--box3d", help="Download 3D box art (if avaliable)", action='store_true')
parser.add_argument("--box-front", help="Download front box art (if avaliable)", action='store_true')
parser.add_argument("--box-side", help="Download side box art (if avaliable)", action='store_true')
parser.add_argument("--box-back", help="Download back box art (if avaliable)", action='store_true')
parser.add_argument("--marquee", help="Download marquee (if avaliable)", action='store_true')
parser.add_argument("--screenshot", help="Download a screenshot (if avaliable)", action='store_true')
parser.add_argument("--title", help="Download snap of the title screen", action='store_true')
parser.add_argument("--video", help="Download video (if avaliable)", action='store_true')
parser.add_argument("--wheel", help="Download wheel (if avaliable)", action='store_true')

parser.add_argument("--force", "-f", help="Force rescraping even if the scraped data is already present", action='store_true')
parser.add_argument("--lang", "-l", help="Lang for retrieve game info", default='en')
parser.add_argument("--region", help="Set region (eu for Europe, us for U.S.A and jp for Japan) for download some media, like wheels or box art. Default is eu", default='eu')

parser.add_argument("--frontend", help="Set the frontend. Only am is available for now", default='am')

parser.add_argument("--scraper", help="Scraping data source (screenscraper, hfsdb, tgdb)", default="screenscraper")
parser.add_argument("--scraperdir", help="Set the scraper base dir. Default is ~/.attract/scraper/<system>/", default=os.environ['HOME']+"/.attract/scraper")

parser.add_argument('--verbose', '-v', help='Verbose mode. Use multiple times for info/debug (-vv)', action='count', default=0)
parser.add_argument("--force-cache-systems", help="Force updating the systems cache", action='store_true')

parser.add_argument("--emulator", "-e", help="An AttractMode emulator configuration file")

parser.add_argument("--frontend-homedir", help="Set the emulator base directory", default=os.environ['HOME']+"/.attract/")
parser.add_argument("--romsdir", help="Set roms directories")
parser.add_argument("--romlistsdir", help="Set the gamelist folder. Default is ~/.attract/romlists", default=os.environ['HOME']+"/.attract/romlists")
parser.add_argument("--no-romlist-update", help="Don't update the romlist. Use this to scrape missing data, it will always query the website for game data", action='store_true')
parser.add_argument("--romlist-update", help="Update the romlist instead of overwriting it", action='store_true')
parser.add_argument("--romlist-file", help="A romlist file to parse if the name is different form the emulator")

parser.add_argument("--system", "-s", help="System name")

parser.add_argument("--listfile", help="Use specific gamelist file.")

parser.add_argument("--systems", help="Print available systems", action='store_true')
parser.add_argument("--langs", help="Print avaliable langs", action='store_true')

parser.add_argument("--user", "-u", help="Your screenScraper user.")
parser.add_argument("--password", "-p", help="Your screenScraper password.")
args = parser.parse_args()


def go_and_scrape(medias_to_scrape: list):
    # Initialize the right front end class
    rom_list_file = ''
    roms_lists_directory = args.romlistsdir
    if args.emulator:
        emulator_no_ext = os.path.splitext(os.path.basename(args.emulator))[0]
        rom_list_file = args.romlist_file if args.romlist_file else '%s/%s.txt' % (roms_lists_directory, emulator_no_ext)
    my_fe = FrontEnd()
    my_scraper = Scraper()

    if args.frontend == 'am':
        my_fe = AttractMode(cfgFile=args.emulator, am_home_path=args.frontend_homedir)

    if args.scraper == 'screenscraper':
        my_scraper = ScreenScraper(devUser = env['SS_DEVUSER'],
                devPassword = env['SS_DEVPASSWD'],
                user = args.user,
                password = args.password)

    if args.scraper == 'hfsdb':
        my_scraper = HFSDB(user = env['HFSDB_USER'], password = env['HFSDB_PASSWD'])

    logging.info('Scrape source: %s', my_scraper.name)

    # Get roms
    files = []
    if args.no_romlist_update:
        files = my_fe.find_roms(rom_list_file)
    else:
        for r in my_fe.romsDir:
            for e in my_fe.romexts:
                logging.debug('Scanning romdir ' + r + ' with extension .' + e)
                files.extend(glob.glob(r + '/*.' + e))
    logging.debug(files)
    if not files:
        logging.critical('No roms found')
        return 1

    # Start scraping
    for file in sorted(files):
        # Get game info
        # According to parameters, download the right data
        current_rom = Rom(file)
        logging.info('Scraping %s as system %s ...' % (current_rom.romfile, my_fe.system))
        rom_info = my_scraper.getGameInfo(current_rom, my_fe.system)
        # if rom_info:
            # logging.debug("Filtered som:\n%s", rom_info.filterOnLang('fr'))
        if not rom_info:
            logging.warning('No data found for rom')
            continue
        my_fe.romlist[current_rom] = rom_info.filterOnLang(args.lang)
        for media in medias_to_scrape:
            if not my_fe.artworkPath[media.value]:
                logging.error('Frontend has no dir set for media type %s, skipping', media)
                continue
            if not media.value in my_fe.artworkPath:
                logging.error('Media value %s is not handled by the FrontEnd, skipping', media)
                continue
            media_asset = rom_info.getAssetMedia(media)
            if not media_asset:
                logging.error('Media %s is not available for the rom, slipping', media)
                continue
            dest_dir = ''
            # This is absolutely lame, really ...
            logging.debug(my_fe.artworkPath[media.value])
            # for folder_path in my_fe.artworkPath[media.value]:
            #     if os.access(folder_path, os.W_OK):
            #         dest_dir = folder_path
            #         break
            dest_dir = my_fe.artworkPath[media.value][0]
            # getAssetMedia can return None, this code is not safe
            media_destination_file = '%s/%s.%s' % (dest_dir,
                current_rom.romname,
                media_asset.extension)
            my_scraper.downloadGameAsset(media_asset, media_destination_file, True, args.force)

    # Time to take care of romlist update
    if args.romlist_update:
        logging.info("Updating romlist...")
        my_fe.update_rom_list(rom_list_file)
    elif not args.no_romlist_update:
        # Write the whole romlist
        loging.info('Writing the romlist...')
        my_fe.write_rom_list(rom_list_file)



if __name__ == '__main__':
    if args.systems:
        systems = collections.OrderedDict(sorted(systems.systems.items()))
        for k, v in systems.items():
            print(k+': '+v['name'])
        exit()

    if args.langs:
        for l in sorted(langs):
            print(l)
        exit()

    loggingLevel = logging.NOTSET
    # Set log level according to wanted verbosity
    loggingLevel = LOGGING_LEVELS[args.verbose -1]
    if loggingLevel == logging.INFO or loggingLevel == logging.WARN:
        logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loggingLevel)
    elif loggingLevel == logging.DEBUG:
        logging.basicConfig(stream=sys.stdout, level=loggingLevel, datefmt='%Y-%m-%d %H:%M:%S',
            format='%(asctime)s [%(levelname)s] %(filename)s/%(funcName)s(%(lineno)d): %(message)s')
    # We don't want the full URLs to be printed'
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.debug(args)
    logging.debug(vars(args))

    # Need a consistency check on --no-romlist-update and --romlist-update, can't set both
    if args.no_romlist_update and args.romlist_update:
        logging.error("You can't set --no-romlist-update and --romlist-update" )
        exit()

    # Find which media has to be scraped
    medias_to_scrape = []
    if args.box2d:
        medias_to_scrape.append(Asset.BOX2D)
    if args.box3d:
        medias_to_scrape.append(Asset.BOX3D)
    if args.box_front:
        medias_to_scrape.append(Asset.FRONT)
    if args.box_side:
        medias_to_scrape.append(Asset.SIDE)
    if args.box_back:
        medias_to_scrape.append(Asset.BACK)
    if args.marquee:
        medias_to_scrape.append(Asset.MARQUEE)
    if args.screenshot:
        medias_to_scrape.append(Asset.SCREENSHOT)
    if args.video:
        medias_to_scrape.append(Asset.VIDEO)
    if args.wheel:
        medias_to_scrape.append(Asset.WHEEL)
    logging.debug("Medias to scrape: \n%s", medias_to_scrape)

    if not load_dotenv(verbose=True):
        logging.warning("Couldn't load_dotenv()")

    if args.emulator or (args.system and args.romsdir):
        # Scrapper()
        go_and_scrape(medias_to_scrape)
        logging.info('Scraping over!')
    else:
        parser.print_help()
