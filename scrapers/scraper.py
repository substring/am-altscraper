import json
import logging
import os
import requests
import sys
from enum import IntEnum, auto

# Listed in descending search order for scrapers that don't support regions
# or when the expected language doesn't exist
Regions = ['wor', 'jp', 'eu', 'us', 'en', 'ss', 'fr', 'de', 'it', 'es', 'pt', 'au', 'br', 'asi', 'kr', 'ss']
# May be useful to set a different default order depending on countries
# For example:
# fr would go : fr, eu, wor ...
# us would go : us, wor, jp ...

# Scraper child classes will have to translate that to the name of the type used by the media DB
class Asset(IntEnum):
	SCREENSHOT = 0
	VIDEO = 1
	BOX2D = 2 # The full box: back + side + front
	BOX3D = 3
	FRONT = 4
	SIDE = 5
	BACK = 6
	MARQUEE = 7
	TITLE = 8


class Media:
	def __init__(self):
		self.type = None # Asset type, see the Asset enum class
		self.hashes = {'crc32': None, 'md5': None, 'sha1': None}
		self.url = ""
		self.extension = '' # png, jpg, mp4 ...
		self.region = None
		self.scraperMediaType = None

	def __str__(self):
		return "Media:\n  Type: {}\n  URL: {}\n  Extension: {}\n  Region: {}\n  Hashes: {}\n  Media type: {}\n".format(Asset(self.type).name, self.url, self.extension, self.region, self.hashes, self.scraperMediaType)

	def __repr__(self):
		return "Media:\n  Type: {}\n  URL: {}\n  Extension: {}\n  Region: {}\n  Hashes: {}\n  Media type: {}\n".format(Asset(self.type).name, self.url, self.extension, self.region, self.hashes, self.scraperMediaType)


class GameInfo:
	def __init__(self):
		# The next dicts are region: value
		self.title = dict()
		self.description = dict()
		self.date = dict()
		self.category = dict()
		self.medias = list()
		self.cloneof = None
		self.developer = None
		self.publisher = None
		self.players = None
		self.resolution = None # Should be a list, but no :(
		self.rotation = None

	def __str__(self):
		return "GameInfo:\nTitle:{}\nDescription: {}\nDate: {}\nCategory:{}\nCloneOf: {}\nMedia: {}\n".format(self.title, self.description, self.date, self.category, self.cloneof, str(self.medias))

	def filterDictOnLang(self, lang, dataDict):
		if lang in dataDict:
			return dataDict[lang]
		# lang doesn't exist, Regions was organised as an order of default values
		for k in Regions:
			if k in dataDict:
				return dataDict[k]
		# We should never fall here
		print(dataDict)
		raise ValueError("Data has no language {}".format(lang, Regions))

	def mediasHaveAsset(self, medias, asset):
		for m in medias:
			if m.type == asset:
				return True

	def filterMediaOnLang(self, lang, medias):
		filteredMedias = list()
		for m in medias:
			print(m)
			if m.region == lang:
				filteredMedias.append(m)
		# Not all media exist for the required language, so let's look for a default one
		for name, member in Asset.__members__.items():
			a = member.value
			if not self.mediasHaveAsset(medias, a):
				continue
			logging.debug('Media {} not yet found'.format(name))
			for r in Regions:
				foundMedia = False
				logging.debug('Looking for media {} of region {}'.format(name, r))
				for m in medias:
					if m.type == a and m.region == r:
						logging.debug('Found media {} for region {} when region {} was expected'.format(name, r, lang))
						foundMedia = True
						filteredMedias.append(m)
						break
				if foundMedia:
					break
		return filteredMedias

	# Returns a dict with all data filtered on the language
	def filterOnLang(self, lang: str):
		if lang not in Regions:
			raise ValueError("Language '{}' is not in {}".format(lang, Regions))
		filteredGameInfo = dict()
		filteredGameInfo['cloneof'] = self.cloneof
		filteredGameInfo['developer'] = self.developer
		filteredGameInfo['publisher'] = self.publisher
		filteredGameInfo['players'] = self.players
		filteredGameInfo['resolution'] = self.resolution
		filteredGameInfo['rotation'] = self.rotation
		filteredGameInfo['title'] = self.filterDictOnLang(lang, self.title)
		filteredGameInfo['description'] = self.filterDictOnLang(lang, self.description)
		filteredGameInfo['date'] = self.filterDictOnLang(lang, self.date)
		filteredGameInfo['category'] = self.filterDictOnLang(lang, self.category)
		filteredGameInfo['medias'] = self.filterMediaOnLang(lang, self.medias)
		return filteredGameInfo


class Scraper(object):
	def __init__(self, name = None, baseUrl = None, baseUrlParams = None, apiKey = None, devUser = None, devPassword = None, user = None, password = None):
		self.name = name
		self.baseUrl = baseUrl
		self.baseUrlParams = baseUrlParams
		self.apiKey = apiKey
		self.devUser = devUser
		self.devPassword = devPassword
		self.user = user
		self.password = password
		self.cacheDir = self.cacheFolder()
		self.platformCacheFile= self.cacheDir + '/' + self.name + '_platforms.cache'
		self.platformCache = self.loadPlatformsCache()
		self.session = None # If we need to handle a HTTP session

	# def __del__(self):
		# self.savePlatformsCache()

	def cacheFolder(self) -> str:
		cacheDir = ''
		if sys.platform == 'win32':
			cacheDir = os.path.expanduser('%LOCALAPPDATA%')
		# Common Linux/MacOS
		else:
			cacheDir = os.path.expanduser('~')
		cacheDir += '/.cache/altscraper'
		if not os.path.exists(cacheDir):
			logging.debug('Creating cache folder ' + cacheDir)
			os.mkdir(cacheDir)
		return cacheDir

	def download(self, endpoint: str, params: dict = None) -> dict:
		"""Basic downloading"""
		# First build up the url
		isFirstParam = True
		targetUrl = self.baseUrl + '/' + endpoint
		if self.baseUrlParams:
			targetUrl += '?' + self.baseUrlParams
			isFirstParam = False
		if params:
			for k, v in params.items():
				if isFirstParam:
					targetUrl += '?{}={}'.format(k, v)
					isFirstParam = False
				else:
					targetUrl += '&{}={}'.format(k, v)
		# print(targetUrl)
		try:
			if self.session:
				r = self.session.get(targetUrl)
			else:
				r = requests.get(targetUrl)
			# return {'status_code': r.status_code, 'content': r.content, 'text': r.text}
			return {'status_code': r.status_code, 'content': r.content}
		except:
			logging.error("An error ocurred on request to " + endpoint)
		return None

	def downloadToFile(self, destinationFile:str, endpoint: str, params: dict = None) -> bool:
		"""Downloads a file to disk
		If you need to retrieve json or xml, don't use that
		"""
		logging.debug('Trying to download to "%s"' % destinationFile)
		httpdata = self.download(endpoint, params)
		if not httpdata['status_code'] == 200:
			return False
		# Should go try/catch when writing the file
		with open(destinationFile,'wb') as f:
			f.write(httpdata['content'])
		return True

	# The following methods MUST be implemented in the child class
	# Gets the complete data for a game and fill the GameInfo object
	def getGameInfo(self, rom) -> GameInfo:
		raise NotImplementedError()
	def getGameAsset(self, rom, assetType: str):
		raise NotImplementedError()
	# Get the platforms + their ids from the scraping site. Up to the child
	# to call it, since the user may want to force a refresh from cmdline
	def getPlatforms(self):
		raise NotImplementedError()

	# Need to implement some cache for scrapers regarding known platforms + their id
	def loadPlatformsCache(self):
		logging.debug('Loading platforms cache data from ' + self.platformCacheFile)
		if not os.path.exists(self.platformCacheFile):
			logging.info('No platforms cache available')
			return None
		with open(self.platformCacheFile) as f:
			data = json.load(f)
		return data

	def savePlatformsCache(self):
		logging.debug('Saving platforms cache data to ' + self.platformCacheFile)
		if not self.platformCache:
			return
		with open(self.platformCacheFile, 'w') as f:
			json.dump(self.platformCache, f, indent=4)
