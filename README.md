# MATester

## About
This repository contains the source code of MATester, test cases and agents for the paper "A Comprehensive Study of Bugs in Multi-modal Agents". MATester can automatically detect global level symptoms and locate functionality component level symptoms through analysis of inter-component outputs. All the agents under test are initially cloned from their original repositories, and instrumented manually to ensure their output are in expected formats. The test cases are composed of tasks collected from the agents' original datasets and mutated ones.

## How to install

To run MATester, make sure you have `Python 3.8`. 

Then clone this repo and install the dependencies with `pip`:

```shell
cd MATester/MLLM_Tester
pip install -r requirements.txt
```

## About test cases and agents

### Test cases
The test cases are available in the `dataset` directory. The `apks` directory stored the installed apk files for GUI automated M-agents. The "datasets.xlsx" file stores the tasks in 4 different scenarios.

### Agents
The 7 agents are avaiable [here](https://drive.google.com/file/d/1fJqGcPe79_x-LtI3ssMGoFtDl0EzZBss/view?usp=drive_link). Please download them and put them in the `agents` folder. They are named as \<agent id\>-\<agent_name\>. Only the 7 agents listed here are instrumented and available for testing.

## How to use
1.  Prepare:
    + Before testing an agent, please refer to its README file to install the dependencies and prepare the environments. For example, if the agent runs on the Android system, please prepare an emulator connected to your host machine via `adb`.
    ```shell
	emulator -avd <emulator name>
    adb devices
    ```


    + Prepare an openAI API key. We use Azure openAI to query the GPT-4o, please deploy the GPT-4o on Azure in advance. Fullfill blanks in the "config_template.ini" file under the `MLLM_Tester`` folder and rename it as "config.ini". 

2. Start:

	To test a given agent in a specific task, call:
   ```shell
   cd MLLM_Tester
   python main.py -i <agent id> -t <task name> (required if it is a task-oriented agent) -a <apk name, required if the agent needs to install apks on Android systems>
   ```

   To run all the test cases of a specific agent, call:
   ```shell
   cd MLLM_Tester
   python run_dataset.py -i <agent id>
   ```

3. MATester will directly call the corresponding shell scripts under the `shell_scripts` directory to run the given agent. It will wait the termination of the agent to analyze its output files and locate symptoms. The output symptoms are shown in the "result_consistency.json" and "result.json" files under the `MLLM_Tester` directory. 

## Note

- We thank a lot for the wonderful open source agents used in this repositories.
