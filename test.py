import json
import logging
import os
import sys
from dotenv import load_dotenv
from os import environ as env
from scrapers.scraper import Scraper
from scrapers.hfsdb import HFSDB
from scrapers.screenscraper import ScreenScraper
from scrapers.thegamesdb import TheGamesDb

#Ugly, don't use that
from classes.rom import Rom

def test_Scraper():
	myScraper = Scraper(name = 'ScraperTest',
				baseUrl = 'http://google.fr',
				baseUrlParams = 'lang=fr',
				apiKey = '4pIk3y',
				devUser = 'someUser',
				devPassword = 'somePass',
				user = 'anotherUser',
				password = 'anotherPass')
	# print(vars(myScraper))

def test_ScreenScraper():
	mySScraper = ScreenScraper(devUser = env['SS_DEVUSER'],
				devPassword = env['SS_DEVPASSWD'],
				user = env['SS_USER'],
				password = env['SS_PASSWD'])
	# print(vars(mySScraper))
	#Sonic2Rom = Rom('~/Téléchargements/Sonic The Hedgehog 2 (World).zip')
	Sonic2Rom = Rom('15353F104B97AB2A8F.zip')
	romInfo = mySScraper.getGameInfo(Sonic2Rom, 'megadrive')
	logging.debug(romInfo.filterOnLang('fr'))
	# print(mySScraper.download('ssuserInfos.php'))
	# print(mySScraper.downloadToFile('sonic2_ss.json', 'jeuInfos.php', {'crc': '24ab4c3a'}))
	# mySScraper.getPlatforms()

def test_TGDB():
	myTGDBcraper = TheGamesDb(apiKey = env['TGDB_APIKEY'])
	# print(vars(myTGDBcraper))
	print(myTGDBcraper.download('v1/Games/ByGameID', {'id': 7504, 'fields': 'players,publishers,genres,overview,last_updated,rating,platform,coop,youtube,os,processor,ram,hdd,video,sound,alternates'}))
	myTGDBcraper.downloadToFile('sonic2_tgdb.json', 'v1/Games/ByGameID', {'id': 7504, 'fields': 'players,publishers,genres,overview,last_updated,rating,platform,coop,youtube,os,processor,ram,hdd,video,sound,alternates'})

def test_HFSDB():
	myHFSDB = HFSDB(user = env['HFSDB_USER'], password = env['HFSDB_PASSWD'])
	print(myHFSDB.download('account'))
	#Sonic2Rom = Rom('~/Téléchargements/Sonic The Hedgehog 2 (World) (Rev A).zip')
	# romInfo = myHFSDB.getGameInfo(Sonic2Rom)
	myHFSDB.getPlatforms()
	# myHFSDB.downloadToFile('sonic2_hfsdb.json', 'games', {'medias__md5': '9feeb724052c39982d432a7851c98d3e'})
	# with open('sonic2_hfsdb.pretty.json', 'w') as f:
		# json.dump(json.loads(myHFSDB.download('games', {'medias__md5': '9feeb724052c39982d432a7851c98d3e'})['content']), f, indent=4)

loggingLevel = logging.DEBUG
if loggingLevel == logging.DEBUG:
	logging.basicConfig(stream=sys.stdout, level=loggingLevel, datefmt='%Y-%m-%d %H:%M:%S',
		format='[%(levelname)s] %(filename)s/%(funcName)s(%(lineno)d): %(message)s')
else:
	logging.basicConfig(stream=sys.stdout, level=loggingLevel)

if not load_dotenv(verbose=True):
	logging.warn("Couldn't load_dotenv()")

test_Scraper()
# test_ScreenScraper()
# test_TGDB()
test_HFSDB()

#####NEED TO TEST ARCADE AND CONSOLE ROM
