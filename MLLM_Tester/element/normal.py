from element.base import BaseFile
class NormalFile(BaseFile):
	def __init__(self, path):
		super().__init__(path)

	def get_round(self) -> str:
		if 'round_num' in self.__dict__:
			return self.round_num
		if not "_" in self.fileName:
			raise ValueError("The format of %s is wrong" % (self.file_path))
		begin_ind = self.fileName.find("_")
		end_ind = self.fileName.rfind(".")
		self.round_num = self.fileName[begin_ind + 1: end_ind]
		return self.round_num