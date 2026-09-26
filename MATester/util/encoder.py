import os
import configparser
from openai import AzureOpenAI

import numpy as np
from numpy.linalg import norm

from util.log import LogManager
from element.base import BaseFile

class TextEmbedder():
	def __init__(self, config_path: str = "config.ini"):
		self.config_path = config_path
		self.logger = LogManager.get_logger()
		self.config = self.__load_config()
		self.client = self.__init_client()
	
	def __load_config(self) -> configparser.ConfigParser:
		config = configparser.ConfigParser()
		
		if not os.path.exists(self.config_path):
			FileNotFoundError("the %s file is not found" % (self.config_path))
		try:
			config.read(self.config_path, encoding='utf-8')
			
			# validate necessary configurations
			required_sections = ['azure_openai_text']
			required_keys = ['endpoint', 'api_key', 'api_version', 'deployment_name']
			
			for section in required_sections:
				if section not in config:
					ValueError(f"the configuration file lacks necessary sections: [{section}]")
				
				for key in required_keys:
					if key not in config[section]:
						ValueError(f"the configuration file lacks necessary keys: [{section}] -> {key}")
			
			return config
			
		except Exception as e:
			self.logger.error(f"the configuration file fails to load: {e}")
	
	def __init_client(self) -> AzureOpenAI:
		try:
			client = AzureOpenAI(
				api_key=self.config['azure_openai_text']['api_key'],
				api_version=self.config['azure_openai_text']['api_version'],
				azure_endpoint=self.config['azure_openai_text']['endpoint']
			)
			self.logger.info("Azure OpenAI client for text_embedding is initialized successfully")
			return client
		except Exception as e:
			self.logger.error(f"Azure OpenAI client for text_embedding fails to initialize: {e}")
				
	def __encode_text(self, text):
		response = self.client.embeddings.create(
			input=[text],
			model=self.config['azure_openai_text']['deployment_name']
		)
		return response.data[0].embedding
	
	def get_embedding(self, file: BaseFile):
		if file.is_text():
			text = open(file.get_file_path()).read()
			return self.__encode_text(text)
		raise ValueError("the file type of %s is not supported" % (file.get_file_path()))
	
	@staticmethod
	@LogManager.log_input_and_output()
	def get_similarity(vec_a, vec_b):
		a = np.array(vec_a)
		b = np.array(vec_b)
		return np.dot(a, b) / (norm(a) * norm(b))
