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
		self.archiveContent = None

	def __repr__(self):
		return "Rom({}, crc = {}, filecrc = {})".format(self.rompathname, self.crc, self.filecrc)

	def getCRC(self) -> str:
		if self.crc:
			return self.crc
		self.listArchive()
		if len(self.archiveContent) == 1:
			self.crc = list(self.archiveContent[0].values())[0]
		else:
			self.crc = None
		return self.crc

	def fileCRC(self) -> str:
		buf = open(self.rompathname, 'rb').read()
		buf = (binascii.crc32(buf) & 0xFFFFFFFF)
		self.filecrc = "%08X" % buf
		return self.filecrc

	def listArchiveFromZip(self) -> list:
		filesList = []
		with zipfile.ZipFile(self.rompathname) as romzip:
			zipinfodata = romzip.infolist()
			for f in zipinfodata:
				decimalCRC = romzip.getinfo(f.filename).CRC
				filesList.append({f.filename: f'{decimalCRC:x}'})
		return filesList

	def listArchiveFrom7z(self) -> str:
		filesList = []
		with py7zr.SevenZipFile(self.rompathname, 'r') as romzip:
			zipinfodata = romzip.list()
			for f in zipinfodata:
				decimalCRC = zipinfodata[0].crc32
				filesList.append({f.filename: f'{decimalCRC:x}'})
		return filesList

	def listArchive(self) -> list:
		if self.romext not in ['7z', 'zip']:
			return None
		if self.romext == 'zip':
			self.archiveContent = self.listArchiveFromZip()
		if self.romext == '7z':
			self.archiveContent = self.listArchiveFrom7z()
		print(self.archiveContent)

	def extractRom(self, path='/tmp'):
		if self.romext == 'zip':
			pass
