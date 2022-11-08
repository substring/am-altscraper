import json
import logging
import os
import sys
#from scraper import Scraper
#from screenscraper import ScreenScraper
#from thegamesdb import TheGamesDb
#from hfsdb import HFSDB
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
	mySScraper = ScreenScraper(devUser = os.environ['SS_DEVUSER'],
				devPassword = os.environ['SS_DEVPASSWD'],
				user = os.environ['SS_USER'],
				password = os.environ['SS_PASSWD'])
	# print(vars(mySScraper))
	Sonic2Rom = Rom('/home/subs/Téléchargements/Sonic The Hedgehog 2 (World).zip')
	romInfo = mySScraper.getGameInfo(Sonic2Rom, 'megadrive')
	logging.debug(romInfo.filterOnLang('fr'))
	# print(mySScraper.download('ssuserInfos.php'))
	# print(mySScraper.downloadToFile('sonic2_ss.json', 'jeuInfos.php', {'crc': '24ab4c3a'}))
	# mySScraper.getPlatforms()

def test_TGDB():
	myTGDBcraper = TheGamesDb(apiKey = os.environ['TGDB_APIKEY'])
	# print(vars(myTGDBcraper))
	print(myTGDBcraper.download('v1/Games/ByGameID', {'id': 7504, 'fields': 'players,publishers,genres,overview,last_updated,rating,platform,coop,youtube,os,processor,ram,hdd,video,sound,alternates'}))
	myTGDBcraper.downloadToFile('sonic2_tgdb.json', 'v1/Games/ByGameID', {'id': 7504, 'fields': 'players,publishers,genres,overview,last_updated,rating,platform,coop,youtube,os,processor,ram,hdd,video,sound,alternates'})

def test_HFSDB():
	myHFSDB = HFSDB(user = os.environ['HFSDB_USER'], password = os.environ['HFSDB_PASSWD'])
	print(myHFSDB.download('account'))
	Sonic2Rom = Rom('/home/subs/Téléchargements/Sonic The Hedgehog 2 (World) (Rev A).zip')
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
# test_Scraper()
# test_ScreenScraper()
# test_TGDB()
test_HFSDB()

#####NEED TO TEST ARCADE AND CONSOLE ROM
