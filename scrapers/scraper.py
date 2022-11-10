import json
import logging
import os
import requests
import sys
from classes.gameinfo import GameInfo


class Scraper(object):
	def __init__(self, name = '', baseUrl = '', baseUrlParams = '', apiKey = '', devUser = '', devPassword = '', user = '', password = ''):
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
