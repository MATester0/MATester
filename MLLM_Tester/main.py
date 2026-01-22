import os
import logging
import argparse
import textwrap
from runner import Runner
from analysis import Analysis

from management.runInfo import runTimeInfo

def validate_id_exists(value):
	"""
	check the existence of id
	"""
	try:
		id = int(value)
		if id not in [2, 3, 6, 7, 8]:
			raise argparse.ArgumentTypeError(f"agent id {id} is not available")
		return id
	except ValueError:
		raise argparse.ArgumentTypeError(f"agent id {id} is not an interger")
	
def check_args_logics(args):
	id = args.agent_id
	task = args.task_name
	apk = args.apk_name
	if id in [2, 8] and not task:
		return False
	if id in [3, 6, 7] and (not task or not apk):
		return False
	return True

def arg_parse():
	"""
	parse args
	"""
	parser = argparse.ArgumentParser(
	description='Automatic tester on M-agents',
	formatter_class=argparse.RawDescriptionHelpFormatter,
	epilog=textwrap.dedent('''
	example:
	# base usage: identify agent id and task name
	python script.py -i 2 -t "play a random music"

	# specific usage: require installation of APKs
	python script.py -i 3/6/7 -t "search for the 'clock' app and open it" -a "com.simplemobiletools.applauncher"
	''')
	)

    # add necessary parameters
	required_group = parser.add_argument_group('necessary args')
	required_group.add_argument(
	    '-i', '--agent-id',
		dest="agent_id",
	    type=validate_id_exists,
	    required=True,
	    help='Agent\'s unique id, should be available in agents folder'
	)

    # optional parameters
	parser.add_argument(
	    '-t', '--task',
	    dest='task_name',  # save in args.task_name
		type=str,
	    help='The task to conduct'
	)
	parser.add_argument(
	    '-a', '--apk',
	    dest='apk_name',
	    type=str,
	    help='APK id, no suffix, should be available in dataset/apks'
	)
	parser.add_argument(
        '-m', '--multiple',
        action='store_false',
        help='test multiple times'
    )

    # parse args
	args = parser.parse_args()	
	# additional checks
	if args.apk_name:
	    # existence of apk file
		apk_path = os.path.join(os.path.abspath("../dataset"), "apks", "{args.apk_name}.apk")
		if not os.path.exists(apk_path):
			raise FileNotFoundError("file {args.apk_name}.apk is not available")

	if not check_args_logics(args):
		raise argparse.ArgumentError("the args are not compatible.")
	return args

# def intialize_and_dump_info():
# 	import os
# 	import re
# 	import util.constants as cs
# 	from datetime import datetime
# 	al = 2
# 	tn = "find a random music"
# 	eo = '''(node:14228) UnhandledPromiseRejectionWarning: TypeError: Cannot destructure property 'x' of 'label' as it is undefined.
#     at executeAction (E:\IoT\7-Agent-Empirical\agents\2_ai-browser\ai-browser\main.js:161:15)
#     at OpenAIChatController.<anonymous> (E:\IoT\7-Agent-Empirical\agents\2_ai-browser\ai-browser\main.js:250:27)
# (Use `electron --trace-warnings ...` to show where the warning was created)
# (node:14228) UnhandledPromiseRejectionWarning: Unhandled promise rejection. This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). To terminate the node process on unhandled promise rejection, use the CLI flag `--unhandled-rejections=strict` (see https://nodejs.org/api/cli.html#cli_unhandled_rejections_mode). (rejection id: 2)'''
# 	st = datetime(2025, 12, 2, 14, 35, 15)
# 	et = datetime(2025, 12, 2, 14, 45, 20)
# 	op = os.path.join(os.path.abspath(cs.OUTPUT_DIR), str(al), re.sub(r'[^a-zA-Z0-9]', '_', tn))
# 	runinfo = runTimeInfo()
# 	runinfo.intialize_and_dump_info(al, tn, eo, st, et, op)

def main():
	""" examples:
		run_info = rn.run(2, "find a random music", None, analyzing_existing=True)
		run_info = rn.run(3, "search 'Clock' app and open it", "com.simplemobiletools.applauncher", analyzing_existing=True)
		run_info = rn.run(6, "search 'Clock' app and open it", "com.simplemobiletools.applauncher", analyzing_existing=True)
		run_info = rn.run(7, "search 'Clock' app and open it", "com.simplemobiletools.applauncher", analyzing_existing=True)
		run_info = rn.run(8, "search 'Clock' app and open it, set a 2-minute timer", None, analyzing_existing=False)
	"""
	args = arg_parse()

	rn = Runner()
	an = Analysis()

	# analyze single case
	run_info = rn.run(args.agent_id, args.task_name, args.apk_name, analyzing_existing=True)
	an.run(run_info, use_existing=True)

	if args.multiple:
		# analyze multiple cases
		if args.task_name != None:
			run_info_2 = rn.run(args.agent_id, args.task_name, args.apk_name, running_time=1, analyzing_existing=True)
			an.run(run_info_2, use_existing=True)
			an.run_multiple(run_info, run_info_2, use_existing=True)
		else:
			run_infos = [run_info]
			for id in range(1, 10): # run 9 times
				run_info_id = rn.run(args.agent_id, args.task_name, args.apk_name, running_time=id, analyzing_existing=True)
				an.run(run_info_id, use_existing=True)
				run_infos.append(run_info_id)
			# check each pair of them
			for id in range(10):
				run_info = 

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	main()