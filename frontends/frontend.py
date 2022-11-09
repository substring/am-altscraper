import subprocess

class FrontEnd():
	def __init__(self, name = None, cfgFile = None, romsDir = None, system = None, extensions = None, artworkPath = dict()):
		self.name = name # the frontend name
		self.configurationFile = cfgFile # the configuration file to parse
		if romsDir:
			if isinstance(romsDir, list):
				self.romsDir = romsDir # where roms are located. In case, frontends already store that value
			else:
				self.romsDir = [romsDir]
		else:
			self.romsDir = []
		self.romexts = extensions # Possible rom extensions, a list with extensions without the heading dot
		self.system = system # the system we focus on. AM will get it from the emulator.cfg, ES needs it
		self.artwokerPath = artworkPath

	def __str__(self):
		str  = "FE Name            : {}\n".format(self.name)
		str += "System             : {}\n".format(self.system)
		str += "Configuration file : {}\n".format(self.configurationFile)
		str += "Roms dir           : {}\n".format(self.romsDir)
		str += "Roms extensions    : {}\n".format(self.romexts)
		str += "Artwork path       : {}\n".format(self.artwokerPath)
		return str

	# Read a configuration file
	def parseConfigFile(self):
		raise NotImplementedError()

	# Use an existing romlist, read it to get the list of roms to scrape
	def readRomList(self):
		raise NotImplementedError()

	def updateRomList(self):
		# Not so sure yet how this should be managed ... get a complete romlist in params and write/update the romlist file ? make it iterative per rom ?
		raise NotImplementedError()

	def interpretShellVariables(self, varname: str) -> str:
		CMD = 'echo "%s"' % varname
		p = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
		value = p.stdout.readlines()[0].strip().decode()
		return value