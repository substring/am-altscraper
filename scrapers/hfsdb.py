import html
import json
import logging
import requests
#from .scraper import Scraper, GameInfo, Asset, Media, Regions
from scrapers.scraper import Scraper
from classes.gameinfo import GameInfo, Asset, Media, Regions

HFSMedia = ['screenshot', 'video', 'cover2d', 'cover3d', 'cover2d', 'None', 'cover2d', 'logo', 'screenshot', 'wheel']
screenshottype = {'title': Asset.TITLE.value, 'in game': Asset.SCREENSHOT.value}
cover2dtype = {'full': Asset.BOX2D.value, 'front': Asset.FRONT.value, 'back': Asset.BACK.value}
HFSRegions = {'PAL': 'eu', 'US': 'us', 'JPN': 'jp', 'WORLD': 'wor'}

class HFSDB(Scraper):
	def __init__(self, user=None, password=None):
		super().__init__(name='HFSDB', user = user, password = password
			, baseUrl = 'https://db.hfsplay.fr/api/v1')
		self.session = requests.session()
		# self.dburl = "https://db.hfsplay.fr/"
		self.appstate = {'token': None, 'username': user}
		self.login()
		if self.appstate['token']:
			self.session.headers.update({'Authorization': 'Token ' + self.appstate['token']})
		self.meta_cache = {}

	def getPlatforms(self):
		# A single call isn't enough, itera while results['next'] isn't empty
		ret = json.loads(self.download('systems')['content'])
		tmpCache = html.unescape(ret['results'])
		nextUrlParams = dict()
		while ret['next']:
			nextUrl = ret['next']
			# logging.debug(nextUrl)
			# Strip https://db.hfsplay.fr/api/v1/systems? from the URL
			qPos = nextUrl.find('?') + 1
			params = nextUrl[qPos:]
			for p in params.split('&'):
				k, v = p.split('=')
				nextUrlParams[k] = v
			# logging.debug(nextUrlParams)
			ret = json.loads(self.download('systems', nextUrlParams)['content'])
			# print(ret)
			tmpCache.append(html.unescape(ret['results']))
			# logging.debug(ret['next'])
		self.platformCache = tmpCache
		self.savePlatformsCache()

	def login(self, user='', pwd=''):
		if self.appstate['token']:
			return self.appstate
		res = self.session.post(self.baseUrl + '/auth/token', {'username': self.user, 'password': self.password})
		data = res.json()
		if 'token' not in data:
			return False
		self.appstate['token'] = data['token']
		self.appstate['username'] = user
		self.session.headers.update({'Authorization': 'Token ' + data['token']})
		return self.appstate

	def queryGameInfo(self, rom, system = None):
		# Query by name on arcade systems
		if not system in ['mame', 'arcade', 'mame-libretro', 'mame4all', 'fba']:
			ret = self.download('games', {'medias__md5': rom.md5})
			if ret['status_code'] == 200:
				logging.debug(rom.romfile + ': URL returned status code ' + str(ret['status_code']))
				jsData = json.loads(ret['content'])
			else:
				logging.error(rom.romfile + ': URL returned status code ' + str(ret['status_code']))
		else:
			ret = self.download('games', {'medias__description': rom.romname})
			if ret['status_code'] == 200:
				logging.debug(rom.romfile + ': URL returned status code ' + str(ret['status_code']))
				jsData = json.loads(ret['content'])
			else:
				logging.error(rom.romfile + ': URL returned status code ' + str(ret['status_code']))
		return jsData

	def filterDataByLang(self, key: str, jsData):
		result = dict()
		for k in Regions:
			regionKey = '{}_{}'.format(key, k)
			if regionKey not in jsData:
				continue
			if jsData[regionKey]:
				result[k] = jsData[regionKey]
		return result

	def findMetaDataValue(self, key: str, jsData) -> str:
		for i in jsData:
			if i['name'] == key:
				return i['value']

	def getAssetType(self, mediaType: str, metadata: str) -> int:
		if mediaType == 'cover2d':
			if metadata[0]['value'] in cover2dtype:
				return cover2dtype[metadata[0]['value']]
		if mediaType == 'screenshot':
			if metadata[0]['value'] in screenshottype:
				return screenshottype[metadata[0]['value']]
		return HFSMedia.index(mediaType)

	def getMediaValue(self, jsData) -> str:
		gameMediaList = list()
		for i in jsData:
			if not i['type']:
				continue
			if i['type'] in HFSMedia:
				gameMedia = Media()
				# GameMedia.
				gameMedia.type = self.getAssetType(i['type'], i['metadata'])
				gameMedia.hashes = {'crc32': i['crc32'], 'md5': i['md5'], 'sha1': i['sha1']}
				gameMedia.url = i['file']
				gameMedia.extension = i['extension']
				gameMedia.region = HFSRegions[i['region']]
				gameMedia.scraperMediaType = i['type']
				gameMediaList.append(gameMedia)
		return gameMediaList

	def getGameInfo(self, rom, system = None):
		jsData = self.queryGameInfo(rom, system)
		if jsData['count'] > 1:
			logging.warn("HFSDB didn't return a single rom info for " + rom.rompathname)
			return None
		if jsData['count'] == 0:
			logging.error('HFSDB has no result for rom')
			return None
		if 'results' not in jsData:
			logging.warn('Got no data for rom')
			return None
		gameData = jsData['results'][0]
		myGameInfo = GameInfo()
		myGameInfo.title = self.filterDataByLang('name', gameData)
		myGameInfo.description = self.filterDataByLang('description', gameData)
		for r in HFSRegions:
			k = 'released_at_' + r
			if gameData[k]:
				myGameInfo.date[HFSRegions[r]] = gameData[k]
		myGameInfo.category['fr'] = self.findMetaDataValue('genre', gameData['metadata'])
		myGameInfo.developer = self.findMetaDataValue('developer', gameData['metadata'])
		myGameInfo.publisher = self.findMetaDataValue('editor', gameData['metadata'])
		myGameInfo.players = self.findMetaDataValue('players', gameData['metadata'])
		myGameInfo.cloneof = gameData['clone_of']
		ret = self.getMediaValue(gameData['medias'])
		if ret:
			myGameInfo.medias = ret
		logging.debug(myGameInfo)
