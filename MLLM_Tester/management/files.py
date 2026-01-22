import os
import re
from typing import Optional, List
from datetime import datetime
from util.constants import HANG_MAX_TIME
from management.runInfo import runTimeInfo
from management.errorType import ErrorType
from element.base import BaseFile
from element.normal import NormalFile
from element.environment import EnvironmentFile
from element.snapshot import SnapshotFile
from element.prompt import PromptFile
from element.plan import PlanFile
from element.action import ActionFile
from element.reflect import ReflectFile
from element.summary import SummaryFile

class FileManagement():
	def __init__(self):
		self.clear()

	def acquire_files(self, runInfo: runTimeInfo):
		self.clear()
		self.runtime_info = runInfo
		dir = self.runtime_info.get_output_path()
		with os.scandir(dir) as entries:
			for entry in entries:
				if entry.is_file() and entry.name != "runtime_data.pkl" and entry.name != "app.log":
					file = self.__make_file(entry)
					if file != None:
						self.__add_file(file)
		if self.summary_file == None:
			self.__create_summary()
					
	@staticmethod
	def __make_file(entry) -> BaseFile:
		file_path = entry.path
		file_name = entry.name
		file_name_woext = file_name[:file_name.rfind(".")]
		if "_" in file_name_woext:
			file_label = file_name_woext[:file_name_woext.find("_")]
		else:
			file_label = file_name_woext
		if file_label == "environment":
			file = EnvironmentFile(file_path)
		elif file_label == "snapshot":
			file = SnapshotFile(file_path)
		elif file_label == "prompt":
			file = PromptFile(file_path)
		elif file_label == "plan":
			file = PlanFile(file_path)
		elif file_label == "action":
			file = ActionFile(file_path)
		elif file_label == "reflect":
			file = ReflectFile(file_path)
		elif file_label == "summary":
			file = SummaryFile(file_path)
		else:
			# raise TypeError(file_path + " is not supported")
			return None
		return file

	def __add_file(self, file: BaseFile):
		if isinstance(file, NormalFile):
			round_ = file.get_round()
			if round_ == "-1":
				return
			if round_ not in self.files_dict:
				self.files_dict[round_] = [file]
			else:
				self.files_dict[round_].append(file)
		elif isinstance(file, SummaryFile):
			self.summary_file = file
		else:
			raise TypeError(file.get_file_path() + " is not supported")

	def get_max_round(self):
		if self.max_round != -1:
			return self.max_round
		for round_str in self.files_dict.keys():
			round_nums = re.findall(r'^([0-9]*)', round_str)
			if len(round_nums) and round_nums[0] != '':
				round_num = int(round_nums[0])
				if round_num > self.max_round:
					self.max_round = round_num
		return self.max_round

	def __get_last_time(self) -> datetime:
		if self.last_time != None:
			return self.last_time
		if self.max_round == -1:
			self.get_max_round()
		files = self.get_files_by_round_int(self.max_round)
		for file in files:
			time = file.get_time()
			if self.last_time == None or time > self.last_time:
				self.last_time = time
		return self.last_time

	def __create_summary(self):
		summary_file_path = os.path.join(self.runtime_info.get_output_path(), "summary.txt")
		if not os.path.exists(summary_file_path):
			with open(summary_file_path, 'w', encoding="utf-8") as f:
				if self.runtime_info.is_error():
					error_info = self.runtime_info.get_error_info()
					f.write("ERROR: %s" % (error_info))
				else:
					end_time = self.runtime_info.get_end_time()
					stop_running_time = self.__get_last_time()
					time_difference = end_time - stop_running_time
					if time_difference.total_seconds() >= HANG_MAX_TIME: # 1 minute and no response
						f.write("timeout: hang")
					else:
						# only if the task is not executed in time, will timeout happen
						if self.runtime_info.task_name != None:
							f.write("timeout: out of time")
						else:
							f.write("finish")
		self.summary_file = SummaryFile(summary_file_path)

	def get_error_type(self) -> ErrorType:
		if self.summary_file == None:
			raise FileNotFoundError("summary.txt file is not found!")
		label = self.summary_file.get_label()
		if label == "finish":
			return ErrorType.finish
		if label == "error":
			return ErrorType.error
		if label == "ERROR":
			return ErrorType.ERROR
		if label == "timeout":
			description = self.summary_file.get_description()
			if description == "out of time":
				return ErrorType.timeout
			if description == "out of round":
				return ErrorType.roundout
			if description == "hang":
				return ErrorType.hang
		raise ValueError("the label %s and description %s in the file %s are invalid" % (label, description, self.summary_file.get_file_path()))

	def get_file_by_round_str_and_name(self, round: str, name: str) -> Optional[NormalFile]:
		files = self.get_files_by_round_str(round)
		for file in files:
			if file.get_file_name().startswith(name):
				return file
		return None
	
	def get_file_by_round_int_and_name(self, round: str, name: int) -> Optional[NormalFile]:
		files = self.get_files_by_round_int(round)
		for file in files:
			if file.get_file_name().startswith(name):
				return file
		return None

	def get_files_by_round_str(self, round: str) -> List[NormalFile]:
		if round not in self.files_dict:
			raise KeyError("%s is not in %s" % (round, self.files_dict))
		files = self.files_dict[round]
		return files

	def get_files_by_round_int(self, round: int) -> List[NormalFile]:
		key = "%s(2)" % (round)
		if key not in self.files_dict:
			key = "%s" % (round)
			if key not in self.files_dict:
				raise KeyError("%s is not in the %s" % (key, self.files_dict))
		files = self.files_dict[key]
		return files

	def clear(self):
		self.max_round = -1
		self.last_time = None
		self.files_dict = {}
		self.runtime_info = None
		self.summary_file = None