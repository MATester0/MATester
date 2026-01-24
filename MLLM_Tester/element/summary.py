from element.base import BaseFile
class SummaryFile(BaseFile):
	def __init__(self, path):
		super().__init__(path)

	def get_content(self) -> str:
		if 'content' in self.__dict__:
			return self.content
		if self.is_text():
			self.content = open(self.file_path, encoding="utf-8").read()
		else:
			raise TypeError("this tester does not support getting the content of " + self.file_path)
		return self.content
	
	def __acquire_label_and_description(self):
		if not 'content' in self.__dict__:
			self.get_content()
		if self.content.startswith("finish"):
			self.label = "finish"
			self.description = ""
		elif not ":" in self.content:
			raise ValueError("the summary file " + self.file_path + " is not in the form of <label>:<description>")
		else:
			ind = self.content.find(":")
			self.label = self.content[:ind]
			self.description = self.content[ind + 1:].replace("\n", "").strip()

	def get_label(self) -> str:
		if 'label' in self.__dict__:
			return self.label
		self.__acquire_label_and_description()
		return self.label

	def get_description(self) -> str:
		if 'description' in self.__dict__:
			return self.description
		self.__acquire_label_and_description()
		return self.description