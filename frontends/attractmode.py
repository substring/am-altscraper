import logging
import os
from frontends.frontend import FrontEnd
from classes.gameinfo import Asset

class AttractMode(FrontEnd):
	def __init__(self, cfgFile = None, romsDir = None, system = None, extensions = None, artworkPath = None):
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
			# for p, v in artworkPaths.items():
			# 	artwork_path.extend(v)
			pass
		# self.artwokerPath = os.path.dirname(os.path.commonpath(artwork_path))
		# If no common path was found, fallback to another value
		if self.artwokerPath and os.path.basename(self.artwokerPath) == self.system:
			self.artwokerPath = self.scraperdir[0:len(self.scraperdir) - len(self.system)]

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