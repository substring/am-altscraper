#import json
import logging
#import os
#import requests
#import sys
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
