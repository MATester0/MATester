import os
import base64
import configparser
from PIL import Image
from openai import AzureOpenAI
from typing import Dict, Any, List

from util.log import LogManager

class LLM():
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
			required_sections = ['azure_openai']
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
				azure_endpoint=self.config['azure_openai']['endpoint'],
				api_key=self.config['azure_openai']['api_key'],
				api_version=self.config['azure_openai']['api_version']
			)
			self.logger.info("Azure OpenAI client is initialized successfully")
			return client
		except Exception as e:
			self.logger.error(f"Azure OpenAI client fails to initialize: {e}")
				
	def __encode_image_to_base64(self, image_path: str) -> str:
		try:
			# validate that existence of image_path
			if not os.path.exists(image_path):
				FileNotFoundError(f"the image file does not exist: {image_path}")
			
			# open and validate the completeness of the image file
			with Image.open(image_path) as img:
				img.verify()
			
			# read the image file and encode
			with open(image_path, "rb") as image_file:
				encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
			
			# determine the mime type according to the file extension
			ext = os.path.splitext(image_path)[1].lower()
			mime_types = {
				'.jpg': 'image/jpeg',
				'.png': 'image/png'
			}
			
			mime_type = mime_types.get(ext, 'image/jpeg')
			
			return f"data:{mime_type};base64,{encoded_string}"
			
		except Exception as e:
			self.logger.error(f"the file encodes error: {e}")
				
	def __get_generation_parameters(self) -> Dict[str, Any]:
		# acquire parameters
		params = {
			'temperature': float(self.config['generation_parameters'].get('temperature', '0.2')),
			'max_tokens': int(self.config['generation_parameters'].get('max_tokens', '100'))
		}
		return params

	@LogManager.log_input_and_output("prompt")
	def infer(self, prompt: str, image_paths: List[str], system_prompt: str = "You are a helpful assistant that is good at finding the confict within a text, and the minor differences and mistakes between two text, two images or a text and a image."):
		try:
			# construct the message list
			messages = []
			
			# add system prompt
			messages.append({
				"role": "system",
				"content": system_prompt
			})
			
			# generate prompts
			user_content = []
			
			# if there are images, add image prompt
			for image_path in image_paths:
				try:
					base64_image = self.__encode_image_to_base64(image_path)
					user_content.append({
						"type": "image_url",
						"image_url": {
							"url": base64_image
						}
					})
				except Exception as e:
					self.logger.error(f"the image fails to be appendeded, only use text prompt : {e}")
			
			# add text prompt
			user_content.append({
				"type": "text",
				"text": prompt
			})
			
			# add prompts to the messages
			messages.append({
				"role": "user",
				"content": user_content
			})
			
			# acquire other parameters....
			generation_params = self.__get_generation_parameters()
			
			# ask for Azure OpenAI API
			response = self.client.chat.completions.create(
				model=self.config['azure_openai']['deployment_name'],
				messages=messages,
				**generation_params
			)
			
			# extract response
			reply = response.choices[0].message.content
			
			return reply
			
		except Exception as e:
			self.logger.error(f"fails to generate response: {e}")
			raise