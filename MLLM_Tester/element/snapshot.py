from PIL import Image
from element.normal import NormalFile
class SnapshotFile(NormalFile):
	def __init__(self, path):
		super().__init__(path)

	def get_content(self):
		if 'content' in self.__dict__:
			return self.content
		if self.is_text():
			self.content = open(self.file_path).read()
		elif self.is_image():
			self.content = Image.open(self.file_path) 
			self.content.verify()  # verify the completeness of the file
		else:
			raise TypeError("this tester does not support getting the content of " + self.file_path)
		return self.content
	
	def set_label(self, has_label):
		self.has_label = has_label

	def get_label(self) -> bool:
		if 'has_label' in self.__dict__:
			return self.has_label
		else:
			raise AttributeError("has_label is not set in the snapshot file:" + self.file_path)