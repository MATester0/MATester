import re
import os
import json
from typing import List

from util.llm import LLM
from util.clip import Clip
from util.tool import Tools
from util.encoder import TextEmbedder
from util.log import LogManager
from util.constants import HARD_POSSIBILITY_LEVEL, LOOSE_POSSIBILITY_LEVEL, ENV_SNAP_COMP_PROMPT, SNAP_LABEL_PROMPT, PROMPT_QUALITY_PROMPT, PLAN_QUALITY_PROMPT, PLAN_SNAP_FIG_SATIS_PROMPT, PLAN_SNAP_TXT_SATIS_PROMPT, TASK_COMPLT_PROMPT, PLAN_ENV_RELAT_PROMPT, PLAN_ACT_COMP_PROMPT, MAX_LLM_QUERY_TIMES, MAX_LLM_RETRY_TIMES

from management.errorType import ErrorType
from management.runInfo import runTimeInfo
from management.files import FileManagement

from element.normal import NormalFile
from element.environment import EnvironmentFile
from element.snapshot import SnapshotFile
from element.prompt import PromptFile
from element.plan import PlanFile
from element.action import ActionFile
from element.reflect import ReflectFile
from element.type import FileType

class Analysis():
	def __init__(self, check_loose: bool = False):
		self.check_loose = check_loose
		self.files = FileManagement()
		self.clip_embedder = Clip()
		self.text_embedder = TextEmbedder()
		self.llm = LLM()
		self.logger = LogManager.get_logger()
		self.symptom_dict = {
			1: "report error and crash",
			2: "hang",
			3: "stop without completing the task",
			4: "incorrect behavior (but do not crash)",
			5: "inconsistent behavior under the same setting",
			6: "unfriendly user interface"
		}

	# only support testing non-consistent errors
	def run(self, runtime_info: runTimeInfo, use_existing: bool = True, change_logger: bool = True):
		self.runtime = runtime_info
		output_path = self.runtime.get_output_path()
		if change_logger:
			self.logger = LogManager.get_file_logger(os.path.join(output_path, "app.log"))
		if use_existing:
			symptom_label, locations = self.__get_record(runtime_info)
			if symptom_label != None and locations != None:
				return symptom_label, locations
		self.files.acquire_files(self.runtime)
		symptom_label = self.__get_symtom()
		if symptom_label != -1:
			locations = self.__get_location(symptom_label)
		else:
			locations = []
		self.__record(symptom_label, locations)
		return symptom_label, locations

	@LogManager.log_input_and_output()
	def __get_symtom(self):
		self.error_type = self.files.get_error_type()
		error_type = self.error_type
		symptom = -1
		if error_type == ErrorType.ERROR:
			symptom = 1
		elif error_type == ErrorType.hang:
			symptom = 2
		elif error_type == ErrorType.timeout or error_type == ErrorType.roundout or error_type == ErrorType.error:
			symptom = 4
		elif error_type == ErrorType.finish:
			# only considers termination if the task is available
			if self.runtime.get_task_name() != None:
				max_round = self.files.get_max_round()
				environment_file = self.files.get_file_by_round_int_and_name(max_round, "environment")
				if environment_file == None and max_round >= 1:
					# raise FileNotFoundError("the environment file does not exist: environment_%s.png" % (max_round))
					environment_file = self.files.get_file_by_round_int_and_name(max_round - 1, "environment")
				if environment_file != None and not self.__check_task_completion(environment_file, self.runtime, problematic_value = False):
					symptom = 3
		else:
			raise ValueError("the value type of " + error_type + " cannot be recognized")
		return symptom
	
	def __record(self, label, locations):
		filename = "result.json"
		try:
			with open(filename, "r", encoding="utf-8") as f:
				existing_result = json.load(f)  # read existing data
				if not isinstance(existing_result, list):
					# if existing data is not a lit
					existing_result = [existing_result]
		except (FileNotFoundError, json.JSONDecodeError):
			# if file does not exist, create new file
			existing_result = []
		
		# prepare results
		if label in self.symptom_dict:
			symptom_str = self.symptom_dict[label]
		elif label == -1:
			symptom_str = ""
		else:
			raise ValueError("the symtom id %s is not valid" % (label))

		task = self.runtime.get_task_name()
		if task != None:
			result = {"agent id": self.runtime.get_agent_label(), "times": self.runtime.get_running_times(), "task name": task, "symptom": label, "locations": locations}
		else:
			result = {"agent id": self.runtime.get_agent_label(), "times": self.runtime.get_running_times(), "symptom": label, "locations": locations}
		
		# append result to existing data
		existing_result.append(result)
		
		# write back to the original file
		with open(filename, "w", encoding="utf-8") as f:
			json.dump(existing_result, f, indent=2, ensure_ascii=False)

	@staticmethod
	@LogManager.log_input_and_output()
	def __get_record(runtime_info: runTimeInfo):
		filename = "result.json"
		try:
			with open(filename, "r", encoding="utf-8") as f:
				existing_result = json.load(f)  # read existing data
				if not isinstance(existing_result, list):
					# if existing data is not a lit
					existing_result = [existing_result]
		except (FileNotFoundError, json.JSONDecodeError):
			# if file does not exist, return
			return None, None
		for result in existing_result:
			task_name = runtime_info.get_task_name()
			if task_name != None:
				if result["agent id"] == runtime_info.get_agent_label() and result["task name"] == task_name and result["times"] == runtime_info.get_running_times():
					return result["symptom"], result["locations"]
			else:
				if result["agent id"] == runtime_info.get_agent_label() and result["times"] == runtime_info.get_running_times():
					return result["symptom"], result["locations"]
		return None, None

	@LogManager.log_input_and_output()
	def __get_location(self, symptom_label: int):
		self.locations = []
		# check Perception:
		perception_locs = self.__check_Perception()
		if len(perception_locs) != 0:
			self.locations.extend(perception_locs)
			planner_locs = []
			if symptom_label == 3:
				planner_locs.append("2.3.2")
				self.locations.extend(planner_locs)
		else:
			# check Planner if there is no problem in Perception or symptom == 3
			planner_locs = self.__check_Planner()
			if len(planner_locs) != 0:
				self.locations.extend(planner_locs)
		# check Executor if:
				# 1. there are no problems in Perception and Planner
				# 2. there is no problem in Perception, and Planner has only functionality problem (only 2.6 causes errors), but the result reports errors
				# 3. there is problem with perception, plan exists (which means at least there is no error with Perception and Planner), but the result reports errors
		if (len(perception_locs) == 0 and len(planner_locs) == 0) or (len(perception_locs) == 0 and len(planner_locs) != 0 and "2.6" not in planner_locs and self.error_type in [ErrorType.ERROR, ErrorType.error, ErrorType.hang]) or (len(perception_locs) != 0 and self.files.get_file_by_round_int_and_name(self.files.get_max_round(), "plan") != None and self.error_type in [ErrorType.ERROR, ErrorType.error, ErrorType.hang]):
			# check Executor
			executor_locs = self.__check_Executor()
			self.locations.extend(executor_locs)
		return self.locations

	@LogManager.log_input_and_output()
	def __check_Perception(self):
		locations = []
		# 1.4: snapshot does not exist
		max_round = self.files.get_max_round()
		snapshot_file = self.files.get_file_by_round_int_and_name(max_round, "snapshot")
		if max_round >= 1:
			last_snapshot_file = self.files.get_file_by_round_int_and_name(max_round - 1, "snapshot")
			if snapshot_file == None and last_snapshot_file != None:
				locations.append("1.4")
				return locations
		else:
			if snapshot_file == None:
				locations.append("1.4")
				return locations
		if snapshot_file == None:
			return locations
		
		if not isinstance(snapshot_file, SnapshotFile):
			raise TypeError("the snapshot file %s is not of the correct type" % (snapshot_file.get_file_path()))

		# 1.3: snapshot has wrong format
		try:
			c = snapshot_file.get_content()
			if snapshot_file.is_text() and c.replace("\n", '').strip() == "":
				locations.append("1.4")
				return locations
		except TypeError as e:
			raise e
		except Exception:
			locations.append("1.3")
			return locations
		

		environment_file = self.files.get_file_by_round_int_and_name(max_round, "environment")
		if environment_file == None:
			self.logger.info("the environment file environment_%s.png does not exist" % (max_round))
			return locations
		
		# 1.1: snapshot is wrong or incomplete compared with the environment
		if environment_file.get_type() == snapshot_file.get_type():
			# if all images or all texts, using clip
			env_emd = self.clip_embedder.get_embedding(environment_file)
			snp_emd = self.clip_embedder.get_embedding(snapshot_file)
			similarity = self.clip_embedder.get_similarity(env_emd, snp_emd)
			if (self.check_loose and similarity < LOOSE_POSSIBILITY_LEVEL) or (not self.check_loose and similarity < HARD_POSSIBILITY_LEVEL):
				completeness = False
			else:
				completeness = True
		else:
			# if multi-modal, use llm
			completeness = self.__get_cross_modal_perception_similarity(environment_file, snapshot_file)
		if not completeness:
			# 1.1.1: snapshot and environment have the same modality, but different content
			if environment_file.get_type() == snapshot_file.get_type():
				locations.append("1.1.1")
			# 1.1.2: snapshot and environment have different modalities, but different content
			else:
				locations.append("1.1.2")
		# 1.1.3: snapshot is labeled, but labels are wrong or incomplete
		if snapshot_file.is_image():
			correctness = self.__check_label_correctness(environment_file, snapshot_file)
			if correctness == -1:
				snapshot_file.set_label(False)
				locations.append("1.1.3")
				return locations
			else:
				snapshot_file.set_label(True)
				if correctness == False:
					locations.append("1.1.3")
					return locations
		return locations

	@LogManager.log_input_and_output()
	def __get_cross_modal_perception_similarity(self, src_file: NormalFile, tgt_file: SnapshotFile):
		# currently, we only observe environment in image form and snapshot in text form, there might be other cases...
		if not tgt_file.is_text() or not src_file.is_image():
			raise TypeError("the snapshot file should be text, and the environment file should be a image")
		prompt = ENV_SNAP_COMP_PROMPT % (tgt_file.get_content())
		query_times = 0
		max_retry_time = 0
		completeness_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				response = self.llm.infer(prompt, [src_file.get_file_path()])
				response_dict = Tools.load_json(response)
				compt = response_dict["Completeness"]
				completeness_count[bool(compt)] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		return completeness_count[True] > completeness_count[False] or (not self.check_loose and completeness_count[True] == completeness_count[False])

	@LogManager.log_input_and_output()
	def __check_label_correctness(self, src_file: NormalFile, tgt_file: SnapshotFile):
		if not src_file.is_image() and not tgt_file.is_image():
			raise TypeError("the environment and snapshot file should be images to check its label correctness")
		prompt = SNAP_LABEL_PROMPT
		query_times = 0
		max_retry_time = 0
		decision_count = {"has mark": 0, "no mark": 0}
		completeness_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				response = self.llm.infer(prompt, [src_file.get_file_path(), tgt_file.get_file_path()], system_prompt="You are a helpful assistant that is good at determining the existence and completeness of marks on a picture.")
				response_dict = Tools.load_json(response)
				has_mark = response_dict["Has Marks"]
				# only count scores if there are marks
				if has_mark:
					decision_count["has mark"] += 1
					compt = response_dict["Completeness"]
					completeness_count[bool(compt)] += 1
				else:
					decision_count["no mark"] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		
		# acquire voting results
		has_mark_count = decision_count["has mark"]
		no_mark_count = decision_count["no mark"]
		# has marks win
		if has_mark_count > no_mark_count:
			return completeness_count[True] > completeness_count[False] or (not self.check_loose and completeness_count[True] == completeness_count[False])
		# no marks win
		elif no_mark_count > has_mark_count:
			return -1
		# reach a draw
		# check loose, count more problems
		if self.check_loose: 
			return completeness_count[True] > completeness_count[False]
		# check hard, count fewer problems
		return -1

	@LogManager.log_input_and_output()
	def __check_Planner(self):
		locations = []
		# 2.6: models are not loaded correctly or plan does not exist
		max_round = self.files.get_max_round()
		prompt_file = self.files.get_file_by_round_int_and_name(max_round, "prompt")
		plan_file = self.files.get_file_by_round_int_and_name(max_round, "plan")
		if plan_file == None and prompt_file != None:
			locations.append("2.6")
			return locations
		
		if plan_file == None and prompt_file == None:
			return locations
		
		if not isinstance(prompt_file, PromptFile) or not isinstance(plan_file, PlanFile):
			raise TypeError("the prompt file %s or plan file are not of the correct type" % (prompt_file.get_file_path(), plan_file.get_file_path()))
		
		if plan_file.get_content().replace('\n', '').strip() == '':
			locations.append("2.6")
			return locations
		
		# 2.7: prompts are not generated correctly
		if prompt_file.get_content().replace("\n", "") == "" or not self.__check_prompt_quality(prompt_file, self.runtime):
			locations.append("2.7")
			return locations
		
		# 2.4: plan has wrong format, 2.1: plan is internally contradictory
		if plan_file.get_content().replace("\n", "") == "":
			locations.append("2.4")
			return locations
		right_format, no_conflict = self.__check_plan_format_and_confict(prompt_file, plan_file)
		if not right_format:
			locations.append("2.4")
		if not no_conflict:
			locations.append("2.1")

		# 2.2: plan does not satisfy the constraints given by the snapshot 
		snapshot_file = self.files.get_file_by_round_int_and_name(max_round, "snapshot")
		assert(snapshot_file != None)
		if not self.__check_plan_satisfy_snapshot(plan_file, snapshot_file):
			# 2.2.1: plan and snapshot have the same modality, but plan does not meet the requirements
			if plan_file.get_type() == snapshot_file.get_type():
				locations.append("2.2.1")
			# 2.2.2: plan and snapshot have different modalities, but plan does not meet the requirements
			else:
				locations.append("2.2.2")

		# 2.3: plan is not related to the task
		if self.error_type == ErrorType.finish:
			# 2.3.2: task is not over, but plan decides differently
			locations.append("2.3.2")
		else:
			# 2.3.1: task is over, but plan decides differently
			# check if the task is completed
			environment_file = self.files.get_file_by_round_int_and_name(max_round, "environment")
			if environment_file == None:
				# max_round < 1, task cannot be over, so 2.3.1 cannot exist
				
				if max_round >= 1:
					# max_round >= 1, get last environment file to judge the completion of the task
					environment_file = self.files.get_file_by_round_int_and_name(max_round - 1, "environment")
					if environment_file == None:
						raise FileNotFoundError("the environment file environment_%s.png does not exist" % (max_round - 1))
			
			if self.error_type == ErrorType.timeout or self.error_type == ErrorType.roundout:
					
				if environment_file != None and self.__check_task_completion(environment_file, self.runtime, problematic_value=True):
					locations.append("2.3.1")
					return locations
			
			# 2.3.3: plan cannot promote the task
			task_name = self.runtime.get_task_name()
			if environment_file != None and task_name != None and not self.__check_plan_relation(environment_file, plan_file, task_name):
				locations.append("2.3.3")
		return locations

	@LogManager.log_input_and_output()
	def __check_prompt_quality(self, prompt_file: PromptFile, runTime: runTimeInfo) -> bool:
		# good: true, bad: false
		if not prompt_file.is_text():
			raise TypeError("the prompt file should be text")
		task = runTime.get_task_name()
		prompt = PROMPT_QUALITY_PROMPT % (prompt_file.get_content())
		if task != None:
			prompt += f"The task that this prompt should describe is:\n'''\n{task}\n'''"
		apk_id = runTime.get_apk_id()
		if apk_id != "" and runTime.get_agent_label() == 6:
			# the 6th agent provides app name specifically in the inputs, so the app name is also added to the task
			prompt += "\nThe task should be conducted in the app: %s.\n" % (apk_id)
		query_times = 0
		max_retry_time = 0
		decision_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				response = self.llm.infer(prompt, [], system_prompt="You are a helpful assistant that is good at determining the quality of a prompt.")
				response_dict = Tools.load_json(response)
				decision = response_dict["Good"]
				decision_count[bool(decision)] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		
		# acquire voting results
		# if reaching a draw: check loose, count more problems; check hard, count fewer problems
		return decision_count[True] > decision_count[False] or (not self.check_loose and decision_count[True] == decision_count[False])

	@LogManager.log_input_and_output()
	def __check_plan_format_and_confict(self, prompt_file: PromptFile, plan_file: PlanFile) -> List[bool]:
		# good: true, bad: false
		if not prompt_file.is_text() and not plan_file.is_text():
			raise TypeError("the prompt and plan file should be text")
		prompt = PLAN_QUALITY_PROMPT % (plan_file.get_content(), prompt_file.get_content())
		query_times = 0
		max_retry_time = 0
		format_decision_count = {True: 0, False: 0}
		conflict_decision_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				response = self.llm.infer(prompt, [], system_prompt="You are a helpful assistant that is good at determining the format correctness and internal logic of a plan.")
				response_dict = Tools.load_json(response)
				format_decision = response_dict["Right Format"]
				format_decision_count[bool(format_decision)] += 1
				conflict_decision = response_dict["No Conflict"]
				conflict_decision_count[bool(conflict_decision)] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		
		# acquire voting results
		format_quality = format_decision_count[True] > format_decision_count[False] or (not self.check_loose and format_decision_count[True] == format_decision_count[False])
		conflict_quality = conflict_decision_count[True] > conflict_decision_count[False] or (not self.check_loose and conflict_decision_count[True] == conflict_decision_count[False])
		return format_quality, conflict_quality

	@LogManager.log_input_and_output()
	def __check_plan_satisfy_snapshot(self, plan_file: PlanFile, snapshot_file: SnapshotFile) -> bool:
		# good: true, bad: false
		if not plan_file.is_text() and not snapshot_file.is_text() and not snapshot_file.is_image():
			raise TypeError("the plan file should be text, and snapshot should be text or image")
		if snapshot_file.is_image() and not snapshot_file.get_label():
			return True
		if snapshot_file.is_image():
			prompt = PLAN_SNAP_FIG_SATIS_PROMPT % (plan_file.get_content())
		else:
			prompt = PLAN_SNAP_TXT_SATIS_PROMPT % (plan_file.get_content(), snapshot_file.get_content())
		query_times = 0
		max_retry_time = 0
		decision_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				if snapshot_file.is_image():
					response = self.llm.infer(prompt, [snapshot_file.get_file_path()], system_prompt="You are a helpful assistant that is good at determining the applicability of a plan.")
				else:
					response = self.llm.infer(prompt, [], system_prompt="You are a helpful assistant that is good at determining the applicability of a plan.")
				response_dict = Tools.load_json(response)
				decision = response_dict["Applicable"]
				decision_count[bool(decision)] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		
		# acquire voting results
		return decision_count[True] > decision_count[False] or (not self.check_loose and decision_count[True] == decision_count[False])

	@LogManager.log_input_and_output()
	def __check_task_completion(self, environment_file: EnvironmentFile, runTime: runTimeInfo, problematic_value = True) -> bool:
		# complete: true, not complete: false
		if not environment_file.is_image():
			raise TypeError("the environment file should be image")
		task = runTime.get_task_name()
		prompt = TASK_COMPLT_PROMPT % (task)
		apk_id = runTime.get_apk_id()
		if apk_id != "" and runTime.get_agent_label() == 6:
			# the 6th agent provides app name specifically in the inputs, so the app name is also added to the task
			prompt += "The task should be conducted in the app: %s.\n" % (apk_id)
		query_times = 0
		max_retry_time = 0
		decision_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				response = self.llm.infer(prompt, [environment_file.get_file_path()], system_prompt="You are a helpful assistant that is good at determining the completion of a task.")
				response_dict = Tools.load_json(response)
				decision = response_dict["Completion"]
				decision_count[bool(decision)] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		
		# acquire voting results
		good = decision_count[True]
		bad = decision_count[False]
		# good win
		if good > bad:
			return True
		# bad win
		elif bad > good:
			return False
		# reach a draw
		else:
			# check loose, count more problems
			if self.check_loose: 
				return problematic_value
			# check hard, count fewer problems
			else:
				return (not problematic_value)

	@LogManager.log_input_and_output()
	def __check_plan_relation(self, environment_file: EnvironmentFile, plan_file: PlanFile, task: str) -> bool:
		# complete: true, not complete: false
		if not environment_file.is_image() and not plan_file.is_text():
			raise TypeError("the environment file should be image and the plan file should be text")
		prompt = PLAN_ENV_RELAT_PROMPT % (plan_file.get_content(), task)
		query_times = 0
		max_retry_time = 0
		decision_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				response = self.llm.infer(prompt, [environment_file.get_file_path()], system_prompt="You are a helpful assistant that is good at determining whether the plan can promote the task.")
				response_dict = Tools.load_json(response)
				decision = response_dict["Promotion"]
				decision_count[bool(decision)] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		
		# acquire voting results
		return decision_count[True] > decision_count[False] or (not self.check_loose and decision_count[True] == decision_count[False])

	@LogManager.log_input_and_output()
	def __check_Executor(self):
		locations = []
		# 3.4: action does not exist
		max_round = self.files.get_max_round()
		plan_file = self.files.get_file_by_round_int_and_name(max_round, "plan")
		action_file = self.files.get_file_by_round_int_and_name(max_round, "action")
		reflect_file = self.files.get_file_by_round_int_and_name(max_round, "reflect")
		# assert(plan_file != None)

		
		if action_file == None and reflect_file == None:
			locations.append("3.4")
			return locations

		if action_file != None:
			if not isinstance(action_file, ActionFile):
				raise TypeError("the action file %s is not of the correct type" % (action_file.get_file_path()))
			
			if action_file.get_content().replace("\n", "").strip() == "":
				locations.append("3.4")
				return locations
			
			# 3.1: action is different from the plan
			if plan_file != None and not self.__check_action_relation(plan_file, action_file):
				locations.append("3.1")
				return locations
		
		# 3.3: reflection of the action's execution results is wrong
		# reflect_file = self.files.get_file_by_round_int_and_name(max_round, "reflect")
		if reflect_file != None:
			if not isinstance(reflect_file, ReflectFile):
				raise TypeError("the reflect file %s is not of the correct type" % (reflect_file.get_file_path()))
			if reflect_file.get_content().replace("\n", "").strip() == "":
				locations.append("3.3")

		if action_file != None:
			# 3.2: action is not applicable to the environment
			if len(self.locations) != 0:
				# 3.2.1: plan is wrong but the corresponding action is directly generated without extra checking
				locations.append("3.2.1")
				return locations
			
			# remove all other reasons, the only reason is that the API is wrong
			if self.error_type in [ErrorType.ERROR, ErrorType.error, ErrorType.hang]:
				# 3.2.2: API called by the action is implemented wrong
				locations.append("3.2.2")
				return locations
		return locations
	
	@LogManager.log_input_and_output()
	def __check_action_relation(self, plan_file: PlanFile, action_file: ActionFile):
		# currently, we only observe plan and action in text form, there might be other cases...
		if not plan_file.is_text() or not action_file.is_text():
			raise TypeError("the plan and action files should be text")
		prompt = PLAN_ACT_COMP_PROMPT % (action_file.get_content(), plan_file.get_content())
		query_times = 0
		max_retry_time = 0
		relation_count = {True: 0, False: 0}
		while query_times < MAX_LLM_QUERY_TIMES and max_retry_time < MAX_LLM_RETRY_TIMES:
			try:
				response = self.llm.infer(prompt, [], system_prompt="You are a helpful assistant that is good at determining the relativeness of an action based on the original plan.")
				response_dict = Tools.load_json(response)
				relt = response_dict["Relation"]
				relation_count[bool(relt)] += 1
				query_times += 1
				max_retry_time += 1
			except Exception as e:
				max_retry_time += 1
				if max_retry_time >= MAX_LLM_RETRY_TIMES:
					raise e
				continue
		return relation_count[True] > relation_count[False] or (not self.check_loose and relation_count[True] == relation_count[False])
	
	# only support testing non-consistent errors
	def run_multiple(self, runtime_info_1: runTimeInfo, runtime_info_2: runTimeInfo, use_existing: bool = True):
		output_path_1 = runtime_info_1.get_output_path()
		output_path_2 = runtime_info_2.get_output_path()
		self.logger = LogManager.get_file_logger(os.path.join(output_path_2, "app.log"))
		self.logger = LogManager.add_file_logger(os.path.join(output_path_1, "app.log"))
		
		if runtime_info_1.get_agent_label() != runtime_info_2.get_agent_label():
			self.logger.error("Cannot compare the consistency when running different agents!")
			return None, None
		
		if use_existing:
			symptom_label, locations = self.__get_record_multiple(runtime_info_1, runtime_info_2)
			if symptom_label != None and locations != None:
				return symptom_label, locations
		
		files1 = FileManagement()
		files2 = FileManagement()
		files1.acquire_files(runtime_info_1)
		files2.acquire_files(runtime_info_2)

		symptom_label = self.__get_symtom_multiple(files1, files2)
		if symptom_label != -1:
			locations = self.__get_location_multiple(files1, files2, runtime_info_1, runtime_info_2)
		else:
			locations = []
		if len(locations) == 0:
			symptom_label = -1
		self.__record_multiple(runtime_info_1, runtime_info_2, symptom_label, locations)
		
		return symptom_label, locations
	
	def __record_multiple(self, runtime_info_1: runTimeInfo, runtime_info_2: runTimeInfo, label, locations):
		# agent label must be the same!!
		assert(runtime_info_1.get_agent_label() == runtime_info_2.get_agent_label())

		filename = "result_consistency.json"
		try:
			with open(filename, "r", encoding="utf-8") as f:
				existing_result = json.load(f)  # read existing data
				if not isinstance(existing_result, list):
					# if existing data is not a lit
					existing_result = [existing_result]
		except (FileNotFoundError, json.JSONDecodeError):
			# if file does not exist, create new file
			existing_result = []
		
		# prepare results
		if label not in self.symptom_dict and label != -1:
			raise ValueError("the symtom id %s is not valid" % (label))
		if label != -1:
			symptom_str = self.symptom_dict[label]


		if runtime_info_1 < runtime_info_2:
			firt, secd = runtime_info_1, runtime_info_2
		else:
			firt, secd = runtime_info_2, runtime_info_1
		
		task1 = firt.get_task_name()
		task2 = secd.get_task_name()
		if task1 == None or task2 == None:
			result = {
				"agent id": firt.get_agent_label(), 
				"run info": [
					{"times": firt.get_running_times()}, 
					{"times": secd.get_running_times()}
				], 
				"symptom": label, 
				"locations": locations
			}
		else:
			result = {
				"agent id": firt.get_agent_label(), 
				"run info": [
					{"times": firt.get_running_times(), "task name": task1}, 
					{"times": secd.get_running_times(), "task name": task2}
				], 
				"symptom": label, 
				"locations": locations
			}
		
		# append result to existing data
		existing_result.append(result)
		
		# write back to the original file
		with open(filename, "w", encoding="utf-8") as f:
			json.dump(existing_result, f, indent=2, ensure_ascii=False)

	@staticmethod
	@LogManager.log_input_and_output()
	def __get_record_multiple(runtime_info_1: runTimeInfo, runtime_info_2: runTimeInfo):
		# agent label must be the same!!
		assert(runtime_info_1.get_agent_label() == runtime_info_2.get_agent_label())
		
		filename = "result_consistency.json"
		try:
			with open(filename, "r", encoding="utf-8") as f:
				existing_result = json.load(f)  # read existing data
				if not isinstance(existing_result, list):
					# if existing data is not a lit
					existing_result = [existing_result]
		except (FileNotFoundError, json.JSONDecodeError):
			# if file does not exist, return
			return None, None
		
		for result in existing_result:
			label = runtime_info_1.get_agent_label()
			if runtime_info_1 < runtime_info_2:
				firt, secd = runtime_info_1, runtime_info_2
			else:
				firt, secd = runtime_info_2, runtime_info_1
			
			run_infos = result["run info"]
			
			task1 = firt.get_task_name()
			task2 = secd.get_task_name()
			if task1 != None and task2 != None:
				if result["agent id"] == label and run_infos[0]["task name"] == task1 and run_infos[0]["times"] == firt.get_running_times() and run_infos[1]["task name"] == task2 and run_infos[1]["times"] == secd.get_running_times():
					return result["symptom"], result["locations"]
			else:
				if result["agent id"] == label and run_infos[0]["times"] == firt.get_running_times() and run_infos[1]["times"] == secd.get_running_times():
					return result["symptom"], result["locations"]
		
		return None, None
	
	@LogManager.log_input_and_output()
	def __get_symtom_multiple(self, files1: FileManagement, files2: FileManagement):
		error_type_1 = files1.get_error_type()
		error_type_2 = files2.get_error_type()
		symptom = -1
		if error_type_1 != error_type_2 and not (error_type_1 in [ErrorType.timeout, ErrorType.roundout] and error_type_2 in [ErrorType.timeout, ErrorType.roundout]):
			symptom = 5
		return symptom
	
	@LogManager.log_input_and_output()
	def __get_location_multiple(self, files1: FileManagement, files2: FileManagement, run_info_1: runTimeInfo, run_info_2: runTimeInfo):
		locations = []

		_, locations1 = self.run(run_info_1, use_existing=True, change_logger=False)
		_, locations2 = self.run(run_info_2, use_existing=True, change_logger=False)
		
		# check Perception:
		perception_locs = self.__check_Perception_multiple(files1, files2, locations1, locations2)
		locations.extend(perception_locs)
		
		# check Planner:
		planner_locs = self.__check_Planner_multiple(files1, files2, locations1, locations2)
		locations.extend(planner_locs)
		
		return locations
	
	@LogManager.log_input_and_output()
	def __check_Perception_multiple(self, files1: FileManagement, files2: FileManagement, locations1: List[str], locations2: List[str]):
		locations = []

		perception_wrong_1 = self.__has_problem_type("1.", locations1)
		perception_wrong_2 = self.__has_problem_type("1.", locations2)
		if perception_wrong_1 == perception_wrong_2:
			return locations
		if perception_wrong_1:
			err_file = files1
			err_locs = locations1
			rit_file = files2
		else:
			err_file = files2
			err_locs = locations2
			rit_file = files1

		# before comparing contents, ensure snapshots exist and have correct format 
		if "1.4" in err_locs or "1.3" in err_locs:
			return locations
		
		# 1.2: two environments are nearly the same, but their snapshots are different

		max_round = err_file.get_max_round()
		snapshot_file = err_file.get_file_by_round_int_and_name(max_round, "snapshot")
		environment_file = err_file.get_file_by_round_int_and_name(max_round, "environment")
		
		assert(environment_file != None) # environment file cannot be None, otherwise there should be no problem
		assert(snapshot_file != None) # snapshot file cannot be None, otherwise problem is 1.4

		environment_file_embedding = self.clip_embedder.get_embedding(environment_file)
		if snapshot_file.is_image():
			snapshot_file_embedding = self.clip_embedder.get_embedding(snapshot_file)
		else:
			snapshot_file_embedding = self.text_embedder.get_embedding(snapshot_file)

		for r in range(rit_file.get_max_round() + 1):
			comp_env_file = rit_file.get_file_by_round_int_and_name(r, "environment")
			comp_snp_file = rit_file.get_file_by_round_int_and_name(r, "snapshot")
			if comp_env_file != None and comp_snp_file != None:
				comp_env_file_embedding = self.clip_embedder.get_embedding(comp_env_file)
				sim = self.clip_embedder.get_similarity(environment_file_embedding, comp_env_file_embedding)
				if sim >= LOOSE_POSSIBILITY_LEVEL: # find two similar environment files:
					if comp_snp_file.is_image():
						comp_snp_file_embedding = self.clip_embedder.get_embedding(comp_snp_file)
						sim_snp = self.clip_embedder.get_similarity(snapshot_file_embedding, comp_snp_file_embedding)
					else:
						comp_snp_file_embedding = self.text_embedder.get_embedding(comp_snp_file)
						sim_snp = self.text_embedder.get_similarity(snapshot_file_embedding, comp_snp_file_embedding)
					if sim_snp < HARD_POSSIBILITY_LEVEL:
						# their snapshots are different!
						# 1.2.1: snapshots and environments have the same modality, but different content
						if environment_file.get_type() == snapshot_file.get_type():
							locations.append("1.2.1")
						# 1.2.2: snapshots and environments have different modalities, but different content
						else:
							locations.append("1.2.2")
						return locations
			else:
				break
		return locations
	
	@LogManager.log_input_and_output()
	def __check_Planner_multiple(self, files1: FileManagement, files2: FileManagement, locations1: List[str], locations2: List[str]):
		locations = []

		planner_wrong_1 = self.__has_problem_type("2.", locations1)
		planner_wrong_2 = self.__has_problem_type("2.", locations2)
		if planner_wrong_1 == planner_wrong_2:
			return locations
		if planner_wrong_1:
			err_file = files1
			err_locs = locations1
			rit_file = files2
		else:
			err_file = files2
			err_locs = locations2
			rit_file = files1

		# before comparing contents, ensure prompts and plans exist
		if "2.6" in err_locs or "2.7" in err_locs:
			return locations
		
		# 2.5: tasks, snapshots and prompts are the same, but their plans are different and finally result in different execution results

		max_round = err_file.get_max_round()
		prompt_file = err_file.get_file_by_round_int_and_name(max_round, "prompt")
		plan_file = err_file.get_file_by_round_int_and_name(max_round, "plan")
		snapshot_file = err_file.get_file_by_round_int_and_name(max_round, "snapshot")
		
		assert(prompt_file != None) # prompt file cannot be None, otherwise there should be no problem
		assert(plan_file != None) # plan file cannot be None, otherwise problem is 2.6
		assert(snapshot_file != None) # snapshot file cannot be None, otherwise there should be no problem

		# prompt_file_embedding = self.clip_embedder.get_embedding(prompt_file)
		plan_file_embedding = self.text_embedder.get_embedding(plan_file)
		if snapshot_file.is_image():
			snapshot_file_embedding = self.clip_embedder.get_embedding(snapshot_file)
		else:
			snapshot_file_embedding = self.text_embedder.get_embedding(snapshot_file)


		#  maybe prompt similarity is not necessary? they all use templates
		for r in range(rit_file.get_max_round() + 1):
			# comp_prmp_file = rit_file.get_file_by_round_int_and_name(r, "prompt")
			comp_snp_file = rit_file.get_file_by_round_int_and_name(r, "snapshot")
			comp_plan_file = rit_file.get_file_by_round_int_and_name(r, "plan")
			
			# if comp_prmp_file != None and comp_snp_file != None:
			if comp_snp_file != None and comp_plan_file != None:
				
				# comp_prmp_file_embedding = self.clip_embedder.get_embedding(comp_prmp_file)
				# sim_prmp = self.clip_embedder.get_similarity(prompt_file_embedding, comp_prmp_file_embedding)
				
				if comp_snp_file.is_image():
					comp_snp_file_embedding = self.clip_embedder.get_embedding(comp_snp_file)
					sim_snp = self.clip_embedder.get_similarity(snapshot_file_embedding, comp_snp_file_embedding)
				else:
					comp_snp_file_embedding = self.text_embedder.get_embedding(comp_snp_file)
					sim_snp = self.text_embedder.get_similarity(snapshot_file_embedding, comp_snp_file_embedding)
				
				# if sim_prmp >= LOOSE_POSSIBILITY_LEVEL and sim_snp >= LOOSE_POSSIBILITY_LEVEL: # find two similar prompts and snapshots:
				if sim_snp >= LOOSE_POSSIBILITY_LEVEL: # find two similar snapshots -> means similar prompts:
					
					comp_plan_file_embedding = self.text_embedder.get_embedding(comp_plan_file)
					sim_plan = self.text_embedder.get_similarity(plan_file_embedding, comp_plan_file_embedding)
					
					if sim_plan < HARD_POSSIBILITY_LEVEL:
						# their plans are different!
						# 2.5.1: plans and snapshots have the same modality, but plans are different
						if plan_file.get_type() == snapshot_file.get_type():
							locations.append("2.5.1")
						# 2.5.2: plans and snapshots have different modalities, but plans are different
						else:
							locations.append("2.5.2")
						return locations
			else:
				break
		return locations
	
	@staticmethod
	def __has_problem_type(begin_ind: str, locations: List[str]):
		for loc in locations:
			if loc.startswith(begin_ind):
				return True
		return False
