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
from urllib.error import ContentTooShortError
from urllib.request import urlretrieve
import json, base64

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
folders = ['snap', 'wheel', 'flyer']

parser = argparse.ArgumentParser(epilog='--system and --romsdir are mandatory')
parser.add_argument("--system", help="System name")
parser.add_argument("--systems", help="Print avaliable systems", action='store_true')
parser.add_argument("--lang", help="Lang for retrieve game info", default='en')
parser.add_argument("--langs", help="Print avaliable langs", action='store_true')
parser.add_argument("--romsdir", help="Set roms directories")
parser.add_argument("--romlistsdir", help="Set the gamelist folder. Default is ~/.attract/romlists", default=os.environ['HOME']+"/.attract/romlists")
parser.add_argument("--video", help="Download video (if avaliable)", action='store_true')
parser.add_argument("--wheels", help="Download video (if avaliable)", action='store_true')
parser.add_argument("--boxs2d", help="Download box art (if avaliable)", action='store_true')
parser.add_argument("--boxs3d", help="Download 3D box art (if avaliable)", action='store_true')
parser.add_argument("--region", help="Set region (eu for Europe, us for U.S.A and jp for Japan) for download some media, like wheels or box art. Default is eu", default='eu')
parser.add_argument("--scraperdir", help="Set the scraper base dir. Default is ~/.attract/scraper/system/", default=os.environ['HOME']+"/.attract/scraper")
parser.add_argument("--listfile", help="Use specific gamelist file.")
parser.add_argument("--user", help="Your screenScraper user.")
parser.add_argument("--password", help="Your screenScraper password.")

args = parser.parse_args()

class Scrapper:

	def __init__(self):

		if not args.system in systems.systems:
			exit('The system %s is not avaliable' % args.system)

		if not args.lang in langs:
			exit("The language %s it's not avaliable" % args.lang)

		if not args.region in regions:
			exit("The region %s it's not supported or avaliable" % args.region)

		for f in folders:
			if not os.path.exists(args.scraperdir+'/'+args.system+'/'+f):
				os.makedirs(args.scraperdir+'/'+args.system+'/'+f)

		if os.path.exists(args.scraperdir) and os.path.isdir(args.scraperdir) and os.access(args.scraperdir, os.W_OK):
			self.systems = systems.systems
			self.scandir()
		else:
			exit("The dir %s don't exists, is not a dir or you don't have permission to write" % args.scraperdir)

	def scandir(self):
		files = []
		f = None
		emuname = None

		if args.listfile:
			base = os.path.basename(args.listfile)
			emuname = os.path.splitext(base)[0]
			f = open(args.listfile, 'w')
		else:
			f = open(args.romlistsdir+'/'+args.system+'.txt', 'w')
			emuname = args.system

		for e in self.systems[args.system]['exts']:
			files.extend(glob.glob(args.romsdir+'/*.'+e))

		f.write("#Name;Title;Emulator;CloneOf;Year;Manufacturer;Category;Players;Rotation;Control;Status;DisplayCount;DisplayType;AltRomname;AltTitle;Extra;Buttons\n")
		for rom in sorted(files):
			print('Getting info for '+rom)
			base = os.path.basename(rom)
			name = os.path.splitext(base)[0]
			data = self.getGameInfo(rom)

			if data:
				f.write('%s;%s;%s;;%s;%s;%s;%s;%s;;;;;;;;\n' % (name, data['title'], emuname, data['year'], data['manufacturer'], data['cat'], data['players'], data['rotation']))
				# Download the snapshot
				if data['snap']:
					print('Downloading snapshoot')
					self.download(data['snap'], '%s/%s/snap/%s.png' % (args.scraperdir, args.system, name))
				if args.video and data['video']:
					print('Downloading video')
					self.download(data['video'], '%s/%s/video/%s.mp4' % (args.scraperdir, args.system, name))
				if args.wheels and data['wheel']:
					print('Downloading wheel')
					self.download(data['wheel'], '%s/%s/wheel/%s.png' % (args.scraperdir, args.system, name))
				if args.boxs2d and data['box2d']:
					print('Downloading 2D box')
					self.download(data['box2d'], '%s/%s/flyer/%s.png' % (args.scraperdir, args.system, name))
				if args.boxs3d and data['box3d']:
					print('Downloading 3D box')
					self.download(data['box3d'], '%s/%s/flyer/%s_3d.png' % (args.scraperdir, args.system, name))
			else:
				f.write('%s;%s;%s;;;;;;;;;;;;;;\n' % (name, name, emuname))
		f.close()

	def scanTupleForValue(self, ttuple, tkey, tvalue, tfinalKey):
		for k in ttuple:
			if k[tkey] == tvalue:
				return k[tfinalKey]

	def getGameInfo(self, rom):
		root = None
		crc = CRC32_from_file(rom)
		md5 = md5sum(rom)
		root = self.getData(crc, md5, os.path.basename(rom))
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
			print(root)
			game = root['Data']['jeu']

			if 'editeur' in game:
				data['manufacturer'] = game['editeur']
			print(data)
			nom_l = 'nom_' + args.lang
			if nom_l in game['noms']:
				data['title'] = game['noms'][nom_l]
			elif 'nom_us' in game['noms']:
				data['title'] = game['noms']['nom_us']
			else:
				data['title'] = game['nom']

			date_l = 'date_'+args.lang
			if 'dates' in game:
				if date_l in game['dates']:
					year = game['dates'][date_l].split('-')[0]
					data['year'] = year
				elif 'date_us' in game['dates']:
					year = game['dates']['date_us'].split('-')[0]
					data['year'] = year
				elif 'date_jp' in game['dates']:
					year = game['dates']['date_jp'].split('-')[0]
					data['year'] = year

			if 'genres' in game:
				if 'genres_'+args.lang in game['genres']:
					cats = game['genres']['genres_'+args.lang]['genre_'+args.lang]
					if type(cats) == str:
						data['cat'] = cats
					elif type(cats) == list:
						data['cat'] = cats[0] + ' / '+cats[1]

			if 'joueurs' in game:
				data['players'] = game['joueurs']

			if 'rotation' in game:
				data['rotation'] = game['rotation']

			if 'medias' in game:
				if 'media_screenshot' in game['medias']:
					data['snap'] = game['medias']['media_screenshot']

				if 'media_video' in game['medias']:
					data['video'] = game['medias']['media_video']

				if 'media_wheels' in game['medias']:
					wheels = game['medias']['media_wheels']
					if 'media_wheel_'+args.region in wheels:
						data['wheel'] = wheels['media_wheel_'+args.region]
					elif 'media_wheel_us' in wheels:
						data['wheel'] = wheels['media_wheel_us']
					elif 'media_wheel_jp' in wheels:
						data['wheel'] = wheels['media_wheel_jp']

				if 'media_boxs' in game['medias']:
					boxs = game['medias']['media_boxs']
					if 'media_boxs2d' in boxs:
						if 'media_box2d_'+args.region in boxs['media_boxs2d']:
							data['box2d'] = boxs['media_boxs2d']['media_box2d_'+args.region]
						elif 'media_box2d_us' in boxs['media_boxs2d']:
							data['box2d'] = boxs['media_boxs2d']['media_box2d_us']
						elif 'media_box2d_jp' in boxs['media_boxs2d']:
							data['box2d'] = boxs['media_boxs2d']['media_box2d_jp']

					if 'media_boxs3d' in boxs:
						if 'media_box3d_'+args.region in boxs['media_boxs3d']:
							data['box3d'] = boxs['media_boxs3d']['media_box3d_'+args.region]
						elif 'media_box3d_us' in boxs['media_boxs3d']:
							data['box3d'] = boxs['media_boxs3d']['media_box3d_us']
						elif 'media_box3d_jp' in boxs['media_boxs3d']:
							data['box3d'] = boxs['media_boxs3d']['media_box3d_jp']

			return(data)

	def getData(self, crc, md5, rom):
		root = None
		url = 'https://www.screenscraper.fr/api2/jeuInfos.php?devid=substring&devpassword=' + base64.b64decode('aE9YdDJXYUJJM2Y=').decode('ascii','strict') + '&softname=GroovyScrape&output=json'
		if args.user and args.password:
			url += '&ssid={}&sspassword={}'.format(args.user, args.password)
		if not args.system in ['arcade', 'mame-libretro', 'mame4all', 'fba']:
			for req_type in [ 'crc', 'md5', 'romnom']:
				if req_type == 'crc': req_val = crc
				if req_type == 'md5': req_val = md5
				if req_type == 'romnom': req_val = rom
				specific_url = url + '&{}={}'.format(req_type, req_val)
				r = requests.get(specific_url)
				if r.status_code != 404:
					root = json.loads(r.text)
					break
		else:
			url += '&romnom=' + rom
			r = requests.get(url)
			if r.status_code != 404:
				root = json.loads(r.text)
		return root

	def download(self, url, dest):
		try:
			if not os.path.exists(dest):
				urlretrieve(url, dest)

		except:
			print("An error ocurred to download " + dest)

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

	if args.system and args.romsdir:
		Scrapper()
	else:
		parser.print_help()

