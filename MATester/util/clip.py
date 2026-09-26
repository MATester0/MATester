import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from transformers import CLIPModel, CLIPProcessor, CLIPTokenizer

from element.base import BaseFile

from util.log import LogManager

class Clip():
	def __init__(self, model_name="openai/clip-vit-base-patch16", device=None):
		if device is None:
			self.device = "cuda" if torch.cuda.is_available() else "cpu"
		else:
			self.device = device
		logger = LogManager.get_logger()
		try:
			# load complete model
			self.model = CLIPModel.from_pretrained(model_name).to(self.device)
			
			# load processers（including tokenizer and image processor）
			self.processor = CLIPProcessor.from_pretrained(model_name)
			self.tokenizer = CLIPTokenizer.from_pretrained(model_name)
			
			# acquire text model and visual model (optional)
			self.text_model = self.model.text_model
			self.vision_model = self.model.vision_model
			
			# acquire logit_scale (for simularity calculation)
			self.logit_scale = self.model.logit_scale
			
			logger.info("%s is loaded successfully!" % (model_name))
			
		except Exception as e:
			logger.error(f"model fails to be loaded: {e}")
			raise
	
	def __encode_text(self, text, normalize=True):
		# ensure that the model is in the evaluation mode
		self.model.eval()
		
		# if the input is a string, change it to a list
		if not isinstance(text, list):
			text = [text]
		
		# use processor to handle the text
		inputs = self.processor(text=text, return_tensors="pt", padding=True)
		inputs = {k: v.to(self.device) for k, v in inputs.items()}
		
		with torch.no_grad():
			# use CLIPModel to acquire text features
			outputs = self.model.get_text_features(**inputs)
			
			# if required, conduct L2 normalization
			if normalize:
				outputs = F.normalize(outputs, p=2, dim=-1)
		
		# change the output to numpy
		outputs = outputs.cpu().numpy()
		
		# if there is only a single string, return a single vector
		if len(text) == 1:
			return outputs[0]
		else:
			return outputs
	
	def __encode_image(self, image, normalize=True):
		self.model.eval()
		
		# if the input is an image, change it to a list
		if not isinstance(image, list):
			image = [image]
		
		# use processor to handle the image
		inputs = self.processor(images=image, return_tensors="pt")
		inputs = {k: v.to(self.device) for k, v in inputs.items()}
		
		with torch.no_grad():
			# acquire visual features
			image_features = self.model.get_image_features(**inputs)
			
			# if required, conduct L2 normalization
			if normalize:
				image_features = F.normalize(image_features, p=2, dim=-1)
		
		# change the output to numpy
		image_features = image_features.cpu().numpy()
		
		# if there is only a single image, return a single vector
		if len(image) == 1:
			return image_features[0]
		else:
			return image_features

	def get_embedding(self, file: BaseFile):
		if file.is_text():
			text = open(file.get_file_path()).read()
			return self.__encode_text(text)
		if file.is_image():
			image = Image.open(file.get_file_path())
			return self.__encode_image(image)
		raise ValueError("the file type of %s is not supported" % (file.get_file_path()))

	@staticmethod
	@LogManager.log_input_and_output()
	def get_similarity(embedding1, embedding2):
		similarity = round(np.dot(embedding1, embedding2).item(), 3)
		return similarity