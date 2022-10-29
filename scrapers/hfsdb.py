import requests
from scraper import Scraper

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