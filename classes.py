import binascii
import hashlib
import os
import py7zr
import zipfile

class Rom:
	# rom must be a fullpath to an existing rom file
	def __init__(self, rom: str, crc = None, filecrc = None):
		if not os.path.exists(rom):
			raise Exception(rom + " doesn't exist")
		self.rompathname = rom
		self.rompath = os.path.dirname(rom)
		self.romfile = os.path.basename(rom)
		self.romname = os.path.splitext(rom)[0]
		self.romext = os.path.splitext(rom)[1][1:]
		self.crc = crc
		self.filecrc = filecrc

	def getCRCFromZip(self) -> str:
		with zipfile.ZipFile(self.rompathname) as romzip:
			zipinfodata = romzip.infolist()
			# We need only one file in the archive, useless otherwise
			if len(zipinfodata) > 1:
				return None
			decimalCRC = romzip.getinfo(zipinfodata[0].filename).CRC
			# Return the HEX value of the CRC, as getinfo returns a decimal value
			return f'{decimalCRC:x}'

	def getCRCFrom7z(self) -> str:
		with py7zr.SevenZipFile(self.rompathname, 'r') as romzip:
			zipinfodata = romzip.list()
			if len(zipinfodata) > 1:
				return None
			decimalCRC = zipinfodata[0].crc32
			# Return the HEX value of the CRC, as getinfo returns a decimal value
			return f'{decimalCRC:x}'

	def getCRC(self) -> str:
		if self.crc:
			return self.crc
		if self.romext == 'zip':
			self.crc = self.getCRCFromZip()
		if self.romext == '7z':
			self.crc = self.getCRCFrom7z()
		return self.crc

	def fileCRC(self) -> str:
		buf = open(self.rompathname, 'rb').read()
		buf = (binascii.crc32(buf) & 0xFFFFFFFF)
		self.filecrc = "%08X" % buf
		return self.filecrc

	def __repr__(self):
		return "Rom({}, crc = {}, filecrc = {})".format(self.rompathname, self.crc, self.filecrc)