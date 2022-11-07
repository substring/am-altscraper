#from .scraper import Scraper
from scrapers.scraper import Scraper

class TheGamesDb(Scraper):
	def __init__(self, apiKey = None):
		urlParams = 'apikey={}'.format(apiKey)
		super().__init__(name='TheGamesDB', apiKey = apiKey
				, baseUrl = 'https://api.thegamesdb.net'
				, baseUrlParams = urlParams)
