import os
import re
import subprocess
from util.log import LogManager
from util.constants import OUTPUT_DIR, MAX_INTERACTION_ROUND, MAX_INTERACTION_MINUTE

from management.runInfo import runTimeInfo

class Runner():
	def __init__(self):
		self.runtime = runTimeInfo()
		self.git_bash_path = "D:\\Git\\bin\\bash.exe"

	def run(self, agent_label: int, task: str, apk_id: str, running_times: int = 0, analyzing_existing = True):
		self.runtime = runTimeInfo()
		if task == None:
			task_name = "run"
		else:
			task_name = task
		if running_times == 0:
			output_path = os.path.join(os.path.abspath(OUTPUT_DIR), str(agent_label), re.sub(r'[^a-zA-Z0-9]', '_', task_name))
		else:
			output_path = os.path.join(os.path.abspath(OUTPUT_DIR), str(agent_label), re.sub(r'[^a-zA-Z0-9]', '_', task_name) + "_%s" % (running_times))
		if os.path.exists(os.path.join(output_path, "runtime_data.pkl")) and analyzing_existing:
			self.output_path = output_path
			self.logger = LogManager.get_file_logger(os.path.join(self.output_path, "app.log"))
			self.runtime = runTimeInfo.get_info(self.output_path)
		else:
			output_path = os.path.join(os.path.abspath(OUTPUT_DIR), str(agent_label), re.sub(r'[^a-zA-Z0-9]', '_', task_name))
			self.output_path = self.__get_empty_path(output_path)
			if not os.path.exists(self.output_path):
				os.makedirs(self.output_path)
			self.logger = LogManager.get_file_logger(os.path.join(self.output_path, "app.log"))
			err_warning = self.__execute_shell(agent_label, task, apk_id)
			error_info = self.__remove_warning(err_warning)
			self.runtime.record_error_output(error_info)
			self.runtime.dump_info()
		runtime = self.runtime
		return runtime

	@staticmethod
	def __get_empty_path(output_path):
		if os.path.exists(output_path) and len(os.listdir(output_path)) != 0:
			dir = os.path.dirname(output_path)
			name = os.path.basename(output_path)
			label = 1
			while True:
				new_name = name + "_%s" % (label)
				output_path = os.path.join(dir, new_name)
				if not os.path.exists(output_path) or len(os.listdir(output_path)) == 0:
					break
				label += 1
		return output_path

	def get_runtime(self):
		return self.runtime
	
	def __search_for_script(self, agent_label: int):
		script_base_path = os.path.abspath("../shell_scripts")
		script_path = None
		with os.scandir(script_base_path) as entries:
			for entry in entries:
				if entry.is_file() and entry.name.startswith("%s_" % (agent_label)):
					script_path = entry.path
					break
		if not os.path.exists(script_path):
			raise FileNotFoundError(script_path + " does not exist")
		return script_path

	def __execute_shell(self, agent_label: int, task_name: str, apk_id: str = None):
		self.runtime.clear()

		self.logger.debug("output directory is %s", self.output_path)

		script_path = self.__search_for_script(agent_label)
		self.logger.info("executing script in %s", script_path)

		if task_name != None:
			task_name = task_name.replace('"', "'")
			self.logger.info("executing task %s", task_name)

		working_dir = os.path.abspath(".")
		self.logger.debug("working directory %s", working_dir)

		self.runtime.record_agent_label(agent_label)
		self.runtime.record_task_name(task_name)
		self.runtime.record_output_path(self.output_path)
		if apk_id != None:
			self.runtime.record_apk_id(apk_id)
		self.runtime.record_start_time()
		try:
			if apk_id == None:
				if task_name == None:
					result = subprocess.run(
						[self.git_bash_path, script_path, self.output_path, str(MAX_INTERACTION_ROUND), str(MAX_INTERACTION_MINUTE)],
						shell=True,		  # do not use shell for safety
						check=True,           # if return 0 then throw execption
						capture_output=True,  # catch outputs
						text=True,            # return textual format
						encoding='utf-8',
						errors='replace',
						cwd= working_dir# working directory
					)
				else:
					result = subprocess.run(
						[self.git_bash_path, script_path, self.output_path, task_name, str(MAX_INTERACTION_ROUND), str(MAX_INTERACTION_MINUTE)],
						shell=True,
						check=True,           # if return 0 then throw execption
						capture_output=True,  # catch outputs
						text=True,            # return textual format
						encoding='utf-8',
						errors='replace',
						cwd= working_dir# working directory
					)
			else:
				assert(task_name != None)
				result = subprocess.run(
					[self.git_bash_path, script_path, self.output_path, task_name, str(MAX_INTERACTION_ROUND), str(MAX_INTERACTION_MINUTE), apk_id],
					shell=True,		  # do not use shell for safety
					check=True,           # if return 0 then throw execption
					capture_output=True,  # catch outputs
					text=True,            # return textual format
					encoding='utf-8',
					errors='replace',
					cwd= working_dir# working directory
				)	
		except subprocess.CalledProcessError as e:
			if e.returncode == 124:
				self.logger.info("execution timeout!")
				self.runtime.record_end_time()
				self.logger.info("running info:\n%s", e.stdout)
				self.logger.error("running error:\n%s", e.stderr)
				return e.stderr
			else:
				self.logger.info("execution wrong!")
				self.runtime.record_end_time()
				self.logger.info("running info:\n%s", e.stdout)
				self.logger.error("running error:\n%s", e.stderr)
				return e.stderr
		
		self.runtime.record_end_time()
		self.logger.info("running info:\n%s", result.stdout)
		self.logger.error("running error:\n%s", result.stderr)
		return result.stderr
	
	@staticmethod
	def __remove_warning(info: str):
		# currently, only support python and js
		error = ""
		append = False
		for line in info.splitlines():
			line_lower = line.lower()
			if append:
				error += line
			# keyword
			elif 'error' in line_lower or 'fatal' in line_lower or 'failed' in line_lower:
				error += line
				append = True
			# specific prefix
			elif re.match(r'^(npm ERR|Traceback)', line, re.IGNORECASE):
				error += line
				append = True
		return error