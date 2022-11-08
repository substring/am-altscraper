import logging
import sys

from frontends.frontend import FrontEnd
from frontends.attractmode import AttractMode


def test_FrontEnd():
	myFE = FrontEnd(name='Test FE', system='Megadrive', cfgFile='test/MAME.cfg', romsDir='/roms', extensions=['zip', '7z'], artworkPath='/medias')
	logging.debug('\n' + str(myFE))

def test_AttractMode():
	myFE = AttractMode(system='arcade', cfgFile='tests/MAME.cfg')
	logging.debug('\n' + str(myFE))

loggingLevel = logging.DEBUG
if loggingLevel == logging.DEBUG:
	logging.basicConfig(stream=sys.stdout, level=loggingLevel, datefmt='%Y-%m-%d %H:%M:%S',
		format='[%(levelname)s] %(filename)s/%(funcName)s(%(lineno)d): %(message)s')
else:
	logging.basicConfig(stream=sys.stdout, level=loggingLevel)

test_FrontEnd()
test_AttractMode()