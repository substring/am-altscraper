"""FrontEnd basclass and children classes tests"""

import logging
import sys

from frontends.attractmode import AttractMode
from frontends.frontend import FrontEnd


def test_frontend():
    """Test the FrontEnd base class"""
    my_fe = FrontEnd(name='Test FE', system='Megadrive', cfgFile='tests/MAME.cfg', romsDir='/roms',
        extensions=['zip', '7z'], artworkPath='/medias')
    logging.debug("\n%s", my_fe)

def test_attractmode():
    """Test the AttractMode Frontend child class"""
    my_fe = AttractMode(system='arcade', cfgFile='tests/MAME.cfg')
    rom_list = my_fe.find_roms('tests/MAME.txt')
    logging.info("Foudn roms: %s", rom_list)
    logging.debug("\n%s", my_fe)

LOGGING_LEVEL = logging.DEBUG
if LOGGING_LEVEL == logging.DEBUG:
    logging.basicConfig(stream=sys.stdout, level=LOGGING_LEVEL, datefmt='%Y-%m-%d %H:%M:%S',
        format='[%(levelname)s] %(filename)s/%(funcName)s(%(lineno)d): %(message)s')
else:
    logging.basicConfig(stream=sys.stdout, level=LOGGING_LEVEL)

#test_frontend()
test_attractmode()
