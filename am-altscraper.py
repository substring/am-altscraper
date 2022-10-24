#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#	am-altscraper.py
#
#	A alternative scraper game info for Attract Mode using the screenscraper.fr API
#
#  Copyright 2017 Alfonso Saavedra "Son Link" <sonlink.dourden@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import sys, os, hashlib
import json, binascii, requests, argparse, collections, glob
import systems, importlib
import requests
import json, base64
import subprocess
import zipfile
import py7zr
import logging
from classes import Rom

#reload(sys)
#sys.setdefaultencoding("utf-8")

def CRC32_from_file(filename):
	buf = open(filename,'rb').read()
	buf = (binascii.crc32(buf) & 0xFFFFFFFF)
	return "%08X" % buf

def md5sum(filename):
	return hashlib.md5(open(filename,'rb').read()).hexdigest()

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

parser = argparse.ArgumentParser(epilog="--system and --romsdir are mandatory if you don't use --emulator")
parser.add_argument("-s", "--system", help="System name")
parser.add_argument("--systems", help="Print available systems", action='store_true')
parser.add_argument("-l", "--lang", help="Lang for retrieve game info", default='en')
parser.add_argument("--langs", help="Print avaliable langs", action='store_true')
parser.add_argument("--romsdir", help="Set roms directories")
parser.add_argument("--romlistsdir", help="Set the gamelist folder. Default is ~/.attract/romlists", default=os.environ['HOME']+"/.attract/romlists")
parser.add_argument("--video", help="Download video (if avaliable)", action='store_true')
parser.add_argument("--wheels", help="Download video (if avaliable)", action='store_true')
parser.add_argument("--boxs2d", help="Download box art (if avaliable)", action='store_true')
parser.add_argument("--boxs3d", help="Download 3D box art (if avaliable)", action='store_true')
parser.add_argument("--marquee", help="Download marquee (if avaliable)", action='store_true')
parser.add_argument("--region", help="Set region (eu for Europe, us for U.S.A and jp for Japan) for download some media, like wheels or box art. Default is eu", default='eu')
parser.add_argument("--scraperdir", help="Set the scraper base dir. Default is ~/.attract/scraper/system/", default=os.environ['HOME']+"/.attract/scraper")
parser.add_argument("--listfile", help="Use specific gamelist file.")
parser.add_argument("-u", "--user", help="Your screenScraper user.")
parser.add_argument("-p", "--password", help="Your screenScraper password.")
parser.add_argument("-e", "--emulator", help="An AttractMode emulator configuration file")
parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbose mode. Use multiple times for info/debug (-vv)')
args = parser.parse_args()

class Scrapper:

	def __init__(self):
		if args.emulator:
			self.emcfg_data = self.readEmulatorConfig(args.emulator)

		if not args.emulator and not args.system in systems.systems:
			exit('The system %s is not avaliable' % args.system)

		if not args.lang in langs:
			exit("The language %s it's not avaliable" % args.lang)

		if not args.region in regions:
			exit("The region %s it's not supported or avaliable" % args.region)

		if self.emcfg_data:
			self.system = self.emcfg_data['system']
			self.romsdir = self.emcfg_data['rompath']
			self.longsystem = os.path.splitext(os.path.basename(args.emulator))[0]
			# This one is a very dangerous assumption, where all media folders are in the same subfolder
			artwork_path = []
			if self.emcfg_data['artwork']:
				for p, v in self.emcfg_data['artwork'].items():
					artwork_path.extend(v)
			self.scraperdir = os.path.dirname(os.path.commonpath(artwork_path))
			if os.path.basename(self.scraperdir) == self.system:
				self.scraperdir = self.scraperdir[0:len(self.scraperdir) - len(self.system)]
			self.exts = self.emcfg_data['romext']
		else:
			self.longsystem = self.system = args.system
			self.romsdir = [ args.romsdir ]
			self.scraperdir = args.scraperdir
			self.exts = self.systems[args.system]['exts']
		for f in folders:
			pathdir = self.scraperdir+'/'+self.system+'/'+f
			if not os.path.exists(pathdir):
				logging.info('Creating dir ' + pathdir)
				os.makedirs(pathdir)

		logging.info('System: %s' % self.system)
		logging.info('Roms path: %s' % ' '.join(self.romsdir))
		logging.info('Roms extensions: %s' % ' '.join(self.exts))
		logging.info('Emulator.cfg name: %s' % self.longsystem)
		logging.info('Scraped data main dir: %s' % self.scraperdir)
		if os.path.exists(self.scraperdir) and os.path.isdir(self.scraperdir) and os.access(self.scraperdir, os.W_OK):
			self.systems = systems.systems
			self.scandir()
		else:
			logging.critical("The dir %s doesn't exists, is not a dir or you don't have permission to write" % self.scraperdir)
			exit()

	def interpretShellVariables(self, varname: str) -> str:
		CMD = 'echo "%s"' % varname
		p = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
		value = p.stdout.readlines()[0].strip().decode()
		return value

	def splitParamFromValue(self, line: str) -> list:
		i = 0
		while i < len(line):
			if line[i] == ' ':
				break
			i += 1
		param = line[0:i]
		i += 1
		while i < len(line):
			if line[i] != ' ':
				break
			i += 1
		value = line[i: len(line)]
		return [param, value]

	def readEmulatorConfig(self, emcfgfile):
		emcfg_data = dict()
		if not os.path.isfile(emcfgfile) :
			exit("The emulator configuration file %s doesn't exist' % emcfgfile")
		with open(emcfgfile) as f:
			lines = [line.rstrip() for line in f]
		for l in lines:
			for p in ['system', 'rompath', 'romext', 'artwork']:
				if l[0: len(p)] != p:
					continue
				i = len(p)
				while i < len(l):
					if l[i] != ' ':
						break
					i += 1
				value = self.interpretShellVariables(l[i: len(l)])
				if p == 'artwork':
					if p not in emcfg_data:
						emcfg_data[p] = dict()
					artparam, artvalue = self.splitParamFromValue(value)
					emcfg_data[p][artparam] = artvalue.split(';')
				elif p == 'romext':
					emcfg_data[p] = [ v[1:len(v)] for v in  value.split(';') ]
				elif p == 'system':
					emcfg_data[p] = value
				else:
					emcfg_data[p] =  value.split(';')
		logging.debug('Data read from the emulator .cfg: {}'.format(emcfg_data))
		return emcfg_data

	def scandir(self):
		files = []
		f = None
		emuname = None

		if args.listfile:
			base = os.path.basename(args.listfile)
			emuname = os.path.splitext(base)[0]
			f = open(args.listfile, 'w')
		else:
			emuname = self.longsystem
			f = open(args.romlistsdir+'/'+self.longsystem+'.txt', 'w')

		for r in self.romsdir:
			for e in self.exts:
				files.extend(glob.glob(r + '/*.' + e))
		if not files:
			logging.critical('No roms found')
			return 1

		logging.info('Found %d roms' % len(files))
		f.write("#Name;Title;Emulator;CloneOf;Year;Manufacturer;Category;Players;Rotation;Control;Status;DisplayCount;DisplayType;AltRomname;AltTitle;Extra;Buttons\n")
		for rom in sorted(files):
			logging.info('Getting info for ' + rom)
			base = os.path.basename(rom)
			name = os.path.splitext(base)[0]
			romobj = Rom(rom)
			romobj.getCRC()
			data = self.getGameInfo(romobj)
			print(str(repr(romobj)))

			if data:
				f.write('%s;%s;%s;;%s;%s;%s;%s;%s;;;;;;;;\n' % (name, data['title'], emuname, data['year'], data['manufacturer'], data['cat'], data['players'], data['rotation']))
				# Download the snapshot
				if data['snap']:
					logging.info('Downloading snapshot')
					self.download(data['snap'], '%s/%s/snap/%s.png' % (self.scraperdir, self.system, name))
				if args.video and data['video']:
					logging.info('Downloading video')
					self.download(data['video'], '%s/%s/video/%s.mp4' % (self.scraperdir, self.system, name))
				if args.wheels and data['wheel']:
					logging.info('Downloading wheel')
					self.download(data['wheel'], '%s/%s/wheel/%s.png' % (self.scraperdir, self.system, name))
				if args.boxs2d and data['box2d']:
					logging.info('Downloading 2D box')
					self.download(data['box2d'], '%s/%s/flyer/%s.png' % (self.scraperdir, self.system, name))
				if args.boxs3d and data['box3d']:
					logging.info('Downloading 3D box')
					self.download(data['box3d'], '%s/%s/flyer/%s_3d.png' % (self.scraperdir, self.system, name))
				if args.marquee and data['marquee']:
					logging.info('Downloading marquee')
					self.download(data['marquee'], '%s/%s/marquee/%s.png' % (self.scraperdir, self.system, name))
			else:
				f.write('%s;%s;%s;;;;;;;;;;;;;;\n' % (name, name, emuname))
		f.close()

	def scanTupleForValue(self, ttuple, tkey, tvalue, tfinalKey):
		for k in ttuple:
			if tkey in k and k[tkey] == tvalue:
				return k[tfinalKey]
		return None

	def getValueFromTupleRes(self, ttuple, tlang, criteriakey = 'region', valuekey = 'text'):
		for k in [tlang, 'wor', 'us', 'en', 'jp', 'ss']:
			val = self.scanTupleForValue(ttuple, criteriakey, k, valuekey)
			if val:
				return val
		return None

	def scanTupleForValueWith2Criteria(self, ttuple, tkey1, tvalue1, tkey2, tvalue2, tfinalKey):
		for k in ttuple:
			if tkey1 in k and \
			   tkey2 in k and \
			   k[tkey1] == tvalue1 and \
			   k[tkey2] == tvalue2:
				return k[tfinalKey]
		return None

	def getMediaValue(self, ttuple, tlang, mediatype, key):
		for k in [tlang, 'wor', 'us', 'en', 'jp', 'ss']:
			val = self.scanTupleForValueWith2Criteria(ttuple, 'type', mediatype, 'region', k, key)
			if val:
				return val
		# Not all media types have a region, so go for a simple check on type=mediatype
		val = self.scanTupleForValue(ttuple, 'type', mediatype, key)
		if val:
			return val
		return None

	def getGameInfo(self, rom):
		root = None
		root = self.getData(rom)
		data = {
			'title': '',
			'year': '',
			'manufacturer': '',
			'cat': '',
			'players': '',
			'rotation': 0,
			'snap': None,
			'video': None,
			'box2d': None,
			'box3d': None,
			'wheel': None
		}

		if root:
			# logging.debug(root)
			game = root['response']['jeu']
			# logging.debug(game)

			if 'editeur' in game:
				data['manufacturer'] = game['editeur']['text']
			if 'noms' in game:
				data['title'] = self.getValueFromTupleRes(game['noms'], args.lang)
			if 'year' in game:
				data['year'] = self.getValueFromTupleRes(game['dates'], args.lang).split('-')[0]
			if 'genres' in game:
				data['cat'] = self.getValueFromTupleRes(game['genres'][0]['noms'], args.lang, 'langue')
			if 'joueurs' in game:
				data['players'] = game['joueurs']['text']
			if 'rotation' in game:
				data['rotation'] = game['rotation']

			if 'medias' in game:
				data['snap'] = self.getMediaValue(game['medias'], args.lang, 'ss', 'url')
				data['video'] = self.getMediaValue(game['medias'], args.lang, 'video-normalized', 'url')
				if not data['video'] :
					data['video'] = self.getMediaValue(game['medias'], args.lang, 'video', 'url')
				data['wheel'] = self.getMediaValue(game['medias'], args.lang, 'wheel', 'url')
				data['box2d'] = self.getMediaValue(game['medias'], args.lang, 'box-2D', 'url')
				data['box3d'] = self.getMediaValue(game['medias'], args.lang, 'box-3D', 'url')
				data['marquee'] = self.getMediaValue(game['medias'], args.lang, 'marquee', 'url')
				if not data['marquee'] :
					data['marquee'] = self.getMediaValue(game['medias'], args.lang, 'screenmarquee', 'url')
				if not data['marquee'] :
					data['marquee'] = self.getMediaValue(game['medias'], args.lang, 'screenmarqueesmall', 'url')
				data['wheel'] = self.getMediaValue(game['medias'], args.lang, 'wheel', 'url')

			return(data)

	def getData(self, rom: Rom):
		root = None
		md5 = md5sum(rom.rompathname) # Not better than hashing an archive ...
		logging.debug('rom CRC: %s' % rom.crc)
		logging.debug('rom md5: %s' % md5)
		url = 'https://www.screenscraper.fr/api2/jeuInfos.php?devid=substring&devpassword=' + base64.b64decode('aE9YdDJXYUJJM2Y=').decode('ascii','strict') + '&softname=GroovyScrape&output=json'
		if args.user and args.password:
			url += '&ssid={}&sspassword={}'.format(args.user, args.password)
		if not args.system in ['mame', 'arcade', 'mame-libretro', 'mame4all', 'fba']:
			for req_type in [ 'crc', 'md5', 'romnom']:
				if req_type == 'crc': req_val = rom.crc
				if req_type == 'md5': req_val = md5
				if req_type == 'romnom': req_val = rom.romfile
				specific_url = url + '&{}={}'.format(req_type, req_val)
				r = requests.get(specific_url)
				if r.status_code == 200:
					root = json.loads(r.text)
					break
				else:
					logging.error('URL returned status code ' + str(r.status_code))
		else:
			# Force system id to 75 (MAME/arcade)
			url += '&systemeid=75&romnom=' + rom.romfile  # This should be someday improved
			r = requests.get(url)
			if r.status_code == 200:
				root = json.loads(r.text)
		return root

	def download(self, url, dest):
		logging.debug('About to download "%s"' % dest)
		try:
			if not os.path.exists(dest):
				r = requests.get(url)
				with open(dest,'wb') as f:
					f.write(r.content)
			else:
				logging.debug("+-- File already exists, skipping download")

		except:
			logging.error("An error ocurred to download " + dest)


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
			format='%(asctime)s %(levelname)s %(filename)s/%(funcName)s(%(lineno)d): %(message)s')
	# We don't want the full URLs to be printed'
	logging.getLogger("urllib3").setLevel(logging.INFO) # requests is built on urllib3

	if args.emulator or (args.system and args.romsdir):
		Scrapper()
	else:
		parser.print_help()

