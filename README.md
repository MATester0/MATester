# MATester

## About
This repository contains the source code of MATester, datasets and agents for the paper "A Study on the Issues of Multi-modal LLM-based Agents". MATester can automatically detect global level symptoms and locate functionality component level symptoms through analysis of inter-component formatted outputs. All the agents are initially cloned from their original repositories, and instrumented manually to ensure their output are in MATester-processable formats. The datasets are composed of tasks. They are collected from the agents' original datasets and mutated to generate new tasks.

## How to install

To run MATester, make sure you have `Python 3.8`. The agents that MATester runs require specific preparations, please refer to their README to install these dependencies.

Then clone this repo and install with `pip`:

```shell
cd MATester/MLLM_Tester
pip install -r requirements.txt
```


## How to use
1.  Prepare:
    + If the agent under test requires specific environment, such as Android system, please prepare an emulator connected to your host machine via `adb`.
    ```shell
	emulator -avd <emulator name>
    adb devices
    ```


    + Prepare an openAI API key. We use Azure openAI to query the GPT-4o, please deploy the GPT-4o on Azure in advance. Fullfill blanks in the "config_template.ini" under the MLLM_Tester folder and rename it as "config.ini". 

2. Start:
   ```shell
   cd MLLM_Tester
   python main.py -i <agent id> -t <task name> -a <apk name, required if the agents need to install apks on Android apps>  
   ```


## About agents

The 10 agents are stored in the agents folder. They are named as \<agent id\>-\<agent_name\>. Only the 10 agents listed here are available for testing.

## Note

- We thank a lot for the wonderful open source agents used in this repositories.
