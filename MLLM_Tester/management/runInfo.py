import os
import re
import pickle
from datetime import datetime
from util.tool import Tools
class runTimeInfo:
	def __init__(self):
		self.clear()

	def __lt__(self, other):
        # define "<" logic
		if not isinstance(other, runTimeInfo) or self.agent_label != other.agent_label:
			return NotImplemented  # cannot compare
		self.get_running_times()
		other.get_running_times()
		return self.task_name < other.task_name or self.task_name == other.task_name and self.times < other.times

	def record_agent_label(self, agent_label):
		self.agent_label = agent_label

	def record_task_name(self, task_name):
		self.task_name = task_name

	def record_start_time(self):
		self.start_time = Tools.get_time()

	def record_end_time(self):
		self.end_time = Tools.get_time()
		if self.start_time == None:
			raise ValueError("start time is not set!")
		self.running_time = self.end_time - self.start_time

	def record_error_output(self, err_output: str):
		self.error_output = err_output

	def record_output_path(self, output_path: str):
		self.output_path = output_path

	def record_apk_id(self, apk_id: str):
		self.apk_id = apk_id

	def dump_info(self):
		with open(os.path.join(self.output_path, "runtime_data.pkl"), "wb") as f:
			pickle.dump(self, f)

	def intialize_and_dump_info(self, al: int, tn: str, eo: str, st: datetime, et: datetime, op: str):
		self.agent_label = al
		self.task_name = tn
		self.error_output = eo
		self.start_time = st
		self.end_time = et
		self.running_time = self.end_time - self.start_time
		self.output_path = op
		self.times = -1
		self.get_running_times()
		self.dump_info()

	def get_agent_label(self):
		if self.agent_label == "":
			raise ValueError("agent label is not set!")
		return self.agent_label

	def get_task_name(self):
		if self.task_name == "":
			raise ValueError("task name is not set!")
		return self.task_name

	def get_end_time(self) -> datetime:
		if self.end_time == None:
			raise ValueError("start time is not set!")
		return self.end_time
	
	def get_running_time(self) -> datetime:
		if self.running_time == None:
			raise ValueError("running time is not calculated!")
		return self.running_time

	def is_error(self):
		if self.error_output == None:
			raise ValueError("error output is not set!!")
		if self.error_output.replace("\n", "").strip() != "":
			return True
		return False

	def get_error_info(self):
		if self.error_output != None:
			return self.error_output
		raise ValueError("error output is not set!!")
	
	def get_output_path(self):
		if self.output_path == "":
			raise ValueError("output path is not set!!")
		return self.output_path
	
	def get_apk_id(self):
		if not 'apk_id' in self.__dict__ or self.apk_id == "":
			return ""
		return self.apk_id
	
	def get_running_times(self):
		if self.times != -1:
			return self.times
		output_path = self.get_output_path()
		nums = re.findall(r'\_(\d+)$', output_path)
		if len(nums) == 0:
			self.times = 0
		else:
			self.times = int(nums[-1])
		return self.times
	
	@staticmethod
	def get_info(output_path: str):
		with open(os.path.join(output_path, "runtime_data.pkl"), "rb") as f:
			instance = pickle.load(f)
		if not isinstance(instance, runTimeInfo):
			raise TypeError(f"The class is not runTimeInfo, it is {type(instance)}")
		instance.times = -1
		instance.get_running_times()
		return instance
	
	def clear(self):
		self.agent_label = -1
		self.task_name = ""
		self.error_output = None
		self.start_time = None
		self.end_time = None
		self.running_time = None
		self.output_path = None
		self.times = -1
		if 'apk_id' in self.__dict__:
			self.apk_id = ""