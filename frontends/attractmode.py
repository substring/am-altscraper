import logging
import os
from classes.gameinfo import GameInfo, Asset, FilteredGameInfo
from classes.rom import Rom
from frontends.frontend import FrontEnd

class AttractMode(FrontEnd):
    def __init__(self, cfgFile = '', romsDir = '', system = '', extensions = [], artworkPath = dict(), am_home_path = ''):
        super().__init__(name='AttractMode', cfgFile=cfgFile, romsDir=romsDir, system=system, extensions=extensions, artworkPath=artworkPath)
        if self.configurationFile:
            self.readEmulatorConfig()
            logging.debug(self.artworkPath)
        self.am_home_path = am_home_path

    def readEmulatorConfig(self):
        artworkPaths = dict()
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
                value = self.expandShellVariables(l[i: len(l)])
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
        """Takes a line like in a attract.cfg, extract the param and the value

        Args:
            line (str): the line to parse

        Returns:
            list: [param, value]
        """
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

    def find_rom(self, name: str) -> str:
        """
        Find a rom file based on its name and the emulator.cfg configuration

        Args:
            name (str): Rom name

        Returns:
            str: full path rom + extention
        """
        test_file = ''
        for path in self.romsDir:
            for extension in self.romexts:
                test_file = '%s/%s.%s' % (path, name, extension)
                if os.path.exists(test_file):
                    return test_file
        return test_file

    def find_roms(self, romlist_file: str) -> list:
        """
        Parse a romlist and return the list of rom files as an absolute path

        Keyword arguments:
        emulator_config_file -- an absolute path+name of a AM emulator config file
        """
        file_list = list()
        with open(romlist_file,'r') as f:
            rom_list = f.readlines()
        logging.debug(rom_list)
        if not rom_list:
            return []
        for line in rom_list:
            if line[0] == '#':
                continue
            file_name, *_ = line.split(';')
            absolute_path = self.find_rom(file_name)
            if absolute_path:
                file_list.append(absolute_path)
            else:
                logging.warn("Couldn't file the rom for: %s" % file_name)
        return file_list

    def make_romlist_line_from_rom_and_gameinfo(self, emuname: str, rom:Rom, rom_gameinfo:GameInfo):
        return '%s;%s;%s;;%s;%s;%s;%s;%s;;;;;;;;;;;;\n' % (
                    rom.romname,
                    rom_gameinfo['title'],
                    emuname,
                    rom_gameinfo['date'],
                    rom_gameinfo['developer'],
                    ','.join(rom_gameinfo['category']) if rom_gameinfo['category'] else '',
                    rom_gameinfo['players'],
                    rom_gameinfo['rotation'])

    def write_rom_list(self, romlist_file=''):
        emuname = os.path.splitext(os.path.basename(self.configurationFile))[0]
        # NOOOO ! the configurationFile is the emulator, not the romlist!!!
        if not romlist_file:
            romlist_file = self.am_home_path + '/romlists/' + emuname + '.cfg'
        with open(romlist_file, 'w') as f:
            f.write("#Name;Title;Emulator;CloneOf;Year;Manufacturer;Category;Players;Rotation;Control;Status;DisplayCount;DisplayType;AltRomname;AltTitle;Extra;Buttons;Series;Language;Region;Rating\n")
            for rom, rom_gameinfo in self.romlist.items():
                romlistEntry = self.make_romlist_line_from_rom_and_gameinfo(emuname, rom, rom_gameinfo)
                f.write(romlistEntry)

    def update_rom_list(self, romlist_file):
        # Load the romlist
        emuname = os.path.splitext(os.path.basename(self.configurationFile))[0]
        if not romlist_file:
            raise ValueError("%s doesn't exist, can't update it", romlist_file)

        # Turn the romlist into a key-sorted dict romlist
        with open(romlist_file, 'r') as f:
            romlist_lines = f.readlines()
        sorted_roms = dict()
        for l in romlist_lines:
            romname = l.split(';')[0]
            sorted_roms[romname] = l.split(';')[1:]

        # Now parse the romlist and update sorted_roms if necessary
        # Should make it look more pythonic ...
        for rom, rom_gameinfo in self.romlist.items():
            if rom.romname not in sorted_roms:
                logging.debug('New rom: %s', rom.romname)
                sorted_roms[rom.romname] = self.make_romlist_line_from_rom_and_gameinfo(emuname, rom, rom_gameinfo).split(';')[1:]

        # Now sort the dict and write the romlist file
        sorted_roms=dict(sorted(sorted_roms.items()))
        with open(romlist_file, 'w') as f:
            f.write("#Name;Title;Emulator;CloneOf;Year;Manufacturer;Category;Players;Rotation;Control;Status;DisplayCount;DisplayType;AltRomname;AltTitle;Extra;Buttons;Series;Language;Region;Rating\n")
            for rom, rest_of_csv in sorted_roms.items():
                if rom[0] == '#':
                    continue
                f.write("%s;%s" % (rom, ";".join(rest_of_csv)))