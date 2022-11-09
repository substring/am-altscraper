import logging
import os
from classes.gameinfo import Asset
from frontends.frontend import FrontEnd

class AttractMode(FrontEnd):
	def __init__(self, cfgFile = None, romsDir = None, system = None, extensions = None, artworkPath = dict()):
		super().__init__(name='AttractMode', cfgFile=cfgFile, romsDir=romsDir, system=system, extensions=extensions, artworkPath=artworkPath)
		if self.configurationFile:
			self.readEmulatorConfig()

	def readEmulatorConfig(self):
		artworkPaths = dict()
		if not os.path.isfile(self.configurationFile):
			logging.error("The emulator configuration file {} doesn't exist".format(self.configurationFile))
			exit(1)
		with open(self.configurationFile) as f:
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
					artparam, artvalue = self.splitParamFromValue(value)
					artworkPaths[artparam] = artvalue.split(';')
				elif p == 'romext':
					self.romexts = [ v[1:] for v in value.split(';') ]
				elif p == 'system':
					self.system = value
				elif p == 'rompath':
					self.romsDir = value.split(';')

		if artworkPaths:
			for p, v in artworkPaths.items():
				if p == 'flyer':
					self.artwokerPath[Asset.BOX2D.value] = v
					self.artwokerPath[Asset.BOX3D.value] = v
					self.artwokerPath[Asset.FRONT.value] = v
					self.artwokerPath[Asset.SIDE.value] = v
					self.artwokerPath[Asset.BACK.value] = v
				if p == 'marquee':
					self.artwokerPath[Asset.MARQUEE.value] = v
				if p == 'snap':
					self.artwokerPath[Asset.SCREENSHOT.value] = v
					self.artwokerPath[Asset.TITLE.value] = v
					self.artwokerPath[Asset.VIDEO.value] = v
				if p == 'wheel':
					self.artwokerPath[Asset.WHEEL.value] = v

		# self.artwokerPath = os.path.dirname(os.path.commonpath(artwork_path))
		# If no common path was found, fallback to another value
		# if self.artwokerPath and os.path.basename(self.artwokerPath) == self.system:
		# 	self.artwokerPath = self.scraperdir[0:len(self.scraperdir) - len(self.system)]

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