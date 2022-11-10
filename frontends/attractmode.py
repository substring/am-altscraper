import logging
import os
from classes.gameinfo import Asset
from frontends.frontend import FrontEnd

class AttractMode(FrontEnd):
	def __init__(self, cfgFile = '', romsDir = '', system = '', extensions = [], artworkPath = dict()):
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
				# Look for the value of the parameter
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
					self.artworkPath[Asset.BOX2D.value] = v
					self.artworkPath[Asset.BOX3D.value] = v
					self.artworkPath[Asset.FRONT.value] = v
					self.artworkPath[Asset.SIDE.value] = v
					self.artworkPath[Asset.BACK.value] = v
				if p == 'marquee':
					self.artworkPath[Asset.MARQUEE.value] = v
				if p == 'snap':
					self.artworkPath[Asset.SCREENSHOT.value] = v
					self.artworkPath[Asset.TITLE.value] = v
					self.artworkPath[Asset.VIDEO.value] = v
				if p == 'wheel':
					self.artworkPath[Asset.WHEEL.value] = v

		# self.artworkPath = os.path.dirname(os.path.commonpath(artwork_path))
		# If no common path was found, fallback to another value
		# if self.artworkPath and os.path.basename(self.artworkPath) == self.system:
		# 	self.artworkPath = self.scraperdir[0:len(self.scraperdir) - len(self.system)]

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