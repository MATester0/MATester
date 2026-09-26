import json
from datetime import datetime
class Tools():
	
	@staticmethod
	def quoted_string(string: str, quote_char='"'):
		escaped_text = string.replace(quote_char, '\\' + quote_char)
		return f"{quote_char}{escaped_text}{quote_char}"
	
	@staticmethod
	def get_time():
		return datetime.now()
	
	@staticmethod
	def load_json(response:str) -> dict:
		begin_index = response.find("{")
		end_index = response.rfind("}")
		json_res = json.loads(response[begin_index: end_index + 1])
		return json_res