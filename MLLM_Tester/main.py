import argparse
import logging
from runner import Runner
from analysis import Analysis

from management.runInfo import runTimeInfo

def arg_parse():
	pass

def intialize_and_dump_info():
	import os
	import re
	import util.constants as cs
	from datetime import datetime
	al = 2
	tn = "find a random music"
	eo = '''(node:14228) UnhandledPromiseRejectionWarning: TypeError: Cannot destructure property 'x' of 'label' as it is undefined.
    at executeAction (E:\IoT\7-Agent-Empirical\agents\2_ai-browser\ai-browser\main.js:161:15)
    at OpenAIChatController.<anonymous> (E:\IoT\7-Agent-Empirical\agents\2_ai-browser\ai-browser\main.js:250:27)
(Use `electron --trace-warnings ...` to show where the warning was created)
(node:14228) UnhandledPromiseRejectionWarning: Unhandled promise rejection. This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). To terminate the node process on unhandled promise rejection, use the CLI flag `--unhandled-rejections=strict` (see https://nodejs.org/api/cli.html#cli_unhandled_rejections_mode). (rejection id: 2)'''
	st = datetime(2025, 12, 2, 14, 35, 15)
	et = datetime(2025, 12, 2, 14, 45, 20)
	op = os.path.join(os.path.abspath(cs.OUTPUT_DIR), str(al), re.sub(r'[^a-zA-Z0-9]', '_', tn))
	runinfo = runTimeInfo()
	runinfo.intialize_and_dump_info(al, tn, eo, st, et, op)

def main():
	arg_parse()

	rn = Runner()
	an = Analysis()

	# analyze single case
	# run_info = rn.run(2, "find a random music", None, analyzing_existing=True)
	# run_info = rn.run(3, "search 'Clock' app and open it", "com.simplemobiletools.applauncher", analyzing_existing=True)
	# run_info = rn.run(6, "search 'Clock' app and open it", "com.simplemobiletools.applauncher", analyzing_existing=True)
	# run_info = rn.run(7, "search 'Clock' app and open it", "com.simplemobiletools.applauncher", analyzing_existing=True)
	run_info = rn.run(8, "search 'Clock' app and open it, set a 2-minute timer", None, analyzing_existing=False)
	# an.run(run_info, use_existing=True)

	# analyze multiple cases
	# run_info_1 = rn.run(2, "play a random music for me", None, analyzing_existing=True)
	# run_info_2 = rn.run(2, "play a random music for me", None, running_time=1, analyzing_existing=True)
	# an.run_multiple(run_info_1, run_info_2, use_existing=True)

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	main()
	# intialize_and_dump_info()