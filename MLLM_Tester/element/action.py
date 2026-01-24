import re
from element.normal import NormalFile
class ActionFile(NormalFile):
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

	def get_api_name(self) -> str:
		if 'api_name' in self.__dict__:
			return self.api_name
		if not 'content' in self.__dict__:
			return self.get_content()
		api_name_raw = re.findall(r'(.*?)\(', self.content)
		if len(api_name_raw) == 0:
			self.api_name = ""
		else:
			self.api_name = api_name_raw[0]
		return self.api_name

	def get_parameters(self) -> list:
		if 'parameters' in self.__dict__:
			return self.parameters
		if not 'content' in self.__dict__:
			return self.get_content()
		parameters_raw = re.findall(r'\((.*?)\)', self.content)
		if len(parameters_raw) == 0:
			self.parameters = []
		else:
			parameters_str = parameters_raw[0]
			if parameters_str.strip() == "":
				self.parameters = []
			else:
				parameter_list = parameters_str.split(",")
				self.parameters = [para.strip() for para in parameter_list]
		return self.parameters