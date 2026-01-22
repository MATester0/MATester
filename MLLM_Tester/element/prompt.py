from element.normal import NormalFile
class PromptFile(NormalFile):
	def __init__(self, path):
		super().__init__(path)

	def get_content(self) -> str:
		if 'content' in self.__dict__:
			return self.content
		if self.is_text():
			self.content = open(self.file_path).read()
		else:
			raise TypeError("this tester does not support getting the content of " + self.file_path)
		return self.content