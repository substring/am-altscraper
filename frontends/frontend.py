import errno
import os
import logging
# import subprocess

from classes.gameinfo import GameInfo
from classes.rom import Rom

class FrontEnd():
    romlist: dict[Rom: GameInfo]

    def __init__(self, name = '', cfgFile = '', romsDir = '', system = '', extensions = [], artworkPath = dict()):
        self.name = name # the frontend name
        self.configurationFile = cfgFile # the configuration file to parse
        if self.configurationFile and not os.path.isfile(self.configurationFile):
            logging.error("The emulator configuration file {} doesn't exist".format(self.configurationFile))
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.configurationFile)
        if romsDir:
            if isinstance(romsDir, list):
                self.romsDir = romsDir # where roms are located. In case, frontends already store that value
            else:
                self.romsDir = [romsDir]
        else:
            self.romsDir = []
        self.romexts = extensions # Possible rom extensions, a list with extensions without the heading dot
        self.system = system # the system we focus on. AM will get it from the emulator.cfg, ES needs it
        self.artworkPath = artworkPath # Index is Asset.value
        self.romlist = dict() # This is a Rom: GameInfo list to set or update the romlist

    def __str__(self):
        str  = "FE Name            : {}\n".format(self.name)
        str += "System             : {}\n".format(self.system)
        str += "Configuration file : {}\n".format(self.configurationFile)
        str += "Roms dir           : {}\n".format(self.romsDir)
        str += "Roms extensions    : {}\n".format(self.romexts)
        str += "Artwork path       : {}\n".format(self.artworkPath)
        return str

    # Read a configuration file
    def find_roms(self, romlist_file: str) -> list:
        raise NotImplementedError()

    # Use an existing romlist, read it to get the list of roms to scrape
    def readRomList(self):
        raise NotImplementedError()

    def write_rom_list(self, romlist_file):
        raise NotImplementedError()

    def update_rom_list(self, romlist_file):
        # Not so sure yet how this should be managed ... get a complete romlist in params and write/update the romlist file ? make it iterative per rom ?
        raise NotImplementedError()

    def expandShellVariables(self, varname: str) -> str:
        return os.path.expandvars(varname)
        # CMD = 'echo "%s"' % varname
        # p = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        # value = p.stdout.readlines()[0].strip().decode()
        # return value
