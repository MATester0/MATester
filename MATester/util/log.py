import os
import time
import inspect
import logging
from pathlib import Path
from functools import wraps

class LogManager:
	
	@staticmethod
	def get_logger(name="MLLM_Tester"):
		return logging.getLogger(name or __name__)
	
	# add log_file_path to the current logger
	@staticmethod
	def add_file_logger(log_file_path='app.log'):
		logger = LogManager.get_logger()
		log_path = Path(log_file_path).resolve()
		
		file_handler = logging.FileHandler(
			filename=log_path,
			mode='a',
			encoding='utf-8'
		)
		file_handler.setLevel(logging.INFO)  # only record INFO or higher level

		formatter = logging.Formatter(
			'%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
			datefmt='%Y-%m-%d %H:%M:%S'
		)
		file_handler.setFormatter(formatter)

		logger.addHandler(file_handler)
		logger.info(f'the logger path is added: {log_path}')
		return logger

	@staticmethod
	def remove_file_logger(log_file_path='app.log'):
		logger = LogManager.get_logger()
		if logger.handlers:
			logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.FileHandler) or h.baseFilename != os.path.abspath(log_file_path)]
		return logger


	# remove other file loggers, only add log_file_path
	@staticmethod
	def get_file_logger(log_file_path='app.log'):
		logger = LogManager.get_logger()
		has_file = False
		if logger.handlers:
			for handler in logger.handlers:
				if isinstance(handler, logging.FileHandler):
					if handler.baseFilename == os.path.abspath(log_file_path):
						has_file = True
						break
			# remove all other file loggers, only retain log_file_path
			logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.FileHandler) or h.baseFilename == os.path.abspath(log_file_path)]
			if has_file:
				return logger
		
		LogManager.add_file_logger(log_file_path)
		
		# log_path = Path(log_file_path).resolve()
		# logger.info(f'the logger path is initialized: {log_path}')
		return logger

	
	@staticmethod
	def log_execution_time(func):
		"""the decorator to record execution time of a function"""
		@wraps(func)
		def wrapper(*args, **kwargs):
			logger = LogManager.get_logger()
			start = time.time()
			try:
				result = func(*args, **kwargs)
				duration = time.time() - start
				logger.info(f"Function {func.__name__} executes for: {duration:.3f} seconds")
				return result
			except Exception as e:
				logger.error(f"Function {func.__name__} executes failed: {e}", exc_info=True)
				raise
		return wrapper
	
	@staticmethod
	def log_input_and_output(param_name: str = ""):
		def decorator(func):
			# the decorator to print input and output of a function
			
			@wraps(func)
			def wrapper(*args, **kwargs):
				logger = LogManager.get_logger()
				# record input
				sig = inspect.signature(func)
				bound_args = sig.bind(*args, **kwargs)
				bound_args.apply_defaults()
				
				# find param_name
				if param_name != "":
					param_value = None
					for name, value in bound_args.arguments.items():
						if name == param_name:
							param_value = value
							break
					
					# record param_value
					if param_value is not None:
						value_str = str(param_value)
						logger.info(f"{func.__name__} - {param_name}:\n{value_str}\n")
				
				try:
					# execute function
					result = func(*args, **kwargs)
					# record output
					logger.info(f"{func.__name__} - return:\n{result}\n")
					return result
				except Exception as e:
					# record exception
					logger.error(f"{func.__name__} exception: {e}", exc_info=True)
					raise
			return wrapper
		return decorator
	

# D:\\Git\\bin\\bash.exe E:\\IoT\\7-Agent-Empirical\\agents\\shell_scripts\\3_Autodroid.sh E:\\IoT\\7-Agent-Empirical\\agents\\output\\3\\search__Clock__app_and_open_it_1 "search 'Clock' app and open it" 20 5 com.simplemobiletools.applauncher_51.apk