import os
import time
from datetime import datetime
from element.type import FileType
from util.constants import TEXT_EXT, IMAGE_EXT, AUDIO_EXT
class BaseFile():
	def __init__(self, path_: str):
		if not os.path.exists(path_):
			raise FileNotFoundError(path_ + " does not exist!")
		self.file_path = path_
		self.fileName = os.path.basename(path_)

	def get_file_name(self) -> str:
		return self.fileName

	def get_file_path(self) -> str:
		return self.file_path

	def get_type(self) -> FileType:
		if 'type' in self.__dict__:
			return self.type
		file_extension = os.path.splitext(self.fileName)[-1]
		if file_extension in TEXT_EXT:
			self.type = FileType.TEXT
			return self.type
		if file_extension in IMAGE_EXT:
			self.type = FileType.IMAGE
			return self.type
		if file_extension in AUDIO_EXT:
			self.type = FileType.AUDIO
			return self.type
		raise TypeError("this tester does not support the extension of " + self.file_path)
	
	def is_text(self) -> bool:
		if 'type' not in self.__dict__:
			self.get_type()
		return self.type == FileType.TEXT
	
	def is_image(self) -> bool:
		if 'type' not in self.__dict__:
			self.get_type()
		return self.type == FileType.IMAGE
	
	def is_audio(self) -> bool:
		if 'type' not in self.__dict__:
			self.get_type()
		return self.type == FileType.AUDIO

	def get_time(self) -> datetime:
		if 'time' in self.__dict__:
			return self.time
		filemt = time.localtime(os.stat(self.file_path).st_mtime)
		self.time = datetime(filemt.tm_year, filemt.tm_mon, filemt.tm_mday, filemt.tm_hour, filemt.tm_min, filemt.tm_sec)
		return self.time