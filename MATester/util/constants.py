TEXT_EXT = [".txt"]
IMAGE_EXT = [".png", ".jpg"]
AUDIO_EXT = [".mp3"]
OUTPUT_DIR = "../output"
HANG_MAX_TIME = 60
MAX_INTERACTION_ROUND = 20
MAX_INTERACTION_MINUTE = 5
HARD_POSSIBILITY_LEVEL = 0.8
LOOSE_POSSIBILITY_LEVEL = 0.9

MAX_LLM_QUERY_TIMES = 3 # llm is queried successfully for MAX_LLM_QUERY_TIMES times, to calculate the average similarity
MAX_LLM_RETRY_TIMES = 10 # llm is queried at least MAX_LLM_RETRY_TIMES times, including failures

ENV_SNAP_COMP_PROMPT = '''Please help me identify if the user's summary of the interactive elements and in the appended picture is complete. The picture is a snapshot of the current environment. Some elements in the environment are interactive, so that users can call specific APIs to interact with the envirnonment. If the picture shows an app screenshot, interactive elements are widgets inside the launched activity. If the picture shows a highway, the interactive elements are all the vehicles and lanes.

Your output should be in the following json format:
        
{
	"Thought": <Show your thinking process and describe which interactive elements are missing in short words>,
	"Completeness": <Determine whether the summary is complete. The value should be boolean>
}

The user's summary is:
\'\'\'
%s
\'\'\'
'''

SNAP_LABEL_PROMPT = '''Please identify if the the interactive elements in the snapshot has been marked based on the original picture. If the snapshot is marked, please further judge the completeness of these marks. The first image is the original picture. At a certain point, a user takes a snapshot of the origin picture and maybe mark the interactive elements in circles and unique ids, which is shown in the second picture (the snapshot). To be complete, the marks should not miss any interactive elements. If the original picture shows an app screenshot, please ignore the interactive elements outside the launched activity.

Your output should be in the following json format:
        
{
	"Has Marks": <Decide whether the user has marked the snapshot. The value should be boolean>,
	"Completeness": <Determine whether the marks are complete. The value should be boolean>
}
'''

PROMPT_QUALITY_PROMPT = '''Please check the quality of a prompt. The prompt is used to guide an agent to complete a task. A good prompt should satisfy the following three rules. Please do not be too strict with these rules.
1. It is ok for prompts to contain phrases. However, if the prompt contains sentences, these sentences should be complete.
2. It mentions the task if the task is provided.
3. It mentions available tools to complete the task.
4. If the environment to conduct the task is provided, it should be mentioned in the prompt.

Your output should be in the following json format:
        
{
	"Thought": <Show your thinking process and describe which rules this prompt violates in short words>,
	"Good": <Determine whether this prompt is good. If any of the rules is violated, it is bad. The value should be boolean>
}

The prompt is:
\'\'\'
%s
\'\'\'

'''

PLAN_QUALITY_PROMPT = '''Please check the quality of a plan. The plan is used to guide an agent to gradually complete a task. The plan is generated based on a prompt. A good plan should satisfy the following two rules. 
1. It should satisfy the output format described in the prompt. 
2. It should not have internal conflict. For example, if the plan decides that the task has been completed, it should not generate another action. 

Your output should be in the following json format:
        
{
	"Thought": <Show your thinking process and describe which rules this plan violates in short words>,
	"Right Format": <Determine whether this plan satisfies the output format. The value should be boolean>,
	"No Conflict": <Determine whether this plan has no internal conflict. The value should be boolean>
}

The plan is:
\'\'\'
%s
\'\'\'

The prompt which this plan generated from is:
\'\'\'
%s
\'\'\'
'''

PLAN_SNAP_FIG_SATIS_PROMPT = '''Please check whether the plan is applicable to the environment. The image is a picture of the environment. The plan is used to conduct an action on an available interactive element in the environment. The interactive elements are mostly marked with unique ids. An applicable plan should satisfy the following two rules.
1. If the interactive elements are marked in ids, the plan should mention an id.
2. If the plan mentions an id, this id should be available in the environment picture. 

Your output should be in the following json format:
        
{
	"Thought": <Show your thinking process and describe which rules this plan violates in short words>,
	"Applicable": <Determine whether this plan is applicable to the environment. The value should be boolean>
}

The plan is:
\'\'\'
%s
\'\'\'
'''

PLAN_SNAP_TXT_SATIS_PROMPT = '''Please check whether the plan is conducted on an available interactive element. The interactive elements are summarized in text. An applicable plan should satisfy the following two rules.
1. If the interactive elements are marked in ids, the plan should mention an id.
2. If the plan mentions an id, this id should be a valid id of an interactive element. 

Your output should be in the following json format:
        
{
	"Thought": <Show your thinking process and describe which rules this plan violates in short words>,
	"Applicable": <Determine whether this plan is conducted on an available element. The value should be boolean>
}

The plan is:
\'\'\'
%s
\'\'\'

The interactive elemements are:
\'\'\'
%s
\'\'\'
'''

TASK_COMPLT_PROMPT = '''Please check whether the task has completed based on the status of the environment. The image shows a picture of the current environment. The environment could be an app screenshot, a virtual driving scenerio or a game screenshot. Be strict. Do not predict the completion of the task unless it is explictly shown in the environment.
Your output should be in the following json format:
        
{
	"Thought": <Show your thinking process in short words>,
	"Completion": <Determine whether the task has completed. The value should be boolean>
}

The task is:
\'\'\'
%s
\'\'\'
'''

PLAN_ENV_RELAT_PROMPT = '''Please predict whether the plan can promote the task based on the status of the environment. The image shows a picture of the current environment. The environment could be an app screenshot, a virtual driving scenerio or a game screenshot. The plan is used to conduct an action to the environment to gradually complete a task.

Your output should be in the following json format:

{
	"Thought": <Show your thinking process and describe why the plan can or cannot promote the task in short words>,
	"Promotion": <Determine whether the plan can promote the task. The value should be boolean>
}

The plan is:
\'\'\'
%s
\'\'\'

The task is:
\'\'\'
%s
\'\'\'
'''

PLAN_ENV_RELAT_PROMPT_NO_ENV = '''Please predict whether the plan can promote the task. The plan is used to conduct an action to gradually complete a task.

Your output should be in the following json format:

{
	"Thought": <Show your thinking process and describe why the plan can or cannot promote the task in short words>,
	"Promotion": <Determine whether the plan can promote the task. The value should be boolean>
}

The plan is:
\'\'\'
%s
\'\'\'

The task is:
\'\'\'
%s
\'\'\'
'''

PLAN_ACT_COMP_PROMPT = '''Please identify whether the action is related to the plan. The plan is a description of a step taken by the agent to complete a task. The plan is in natural language. The agent then calls a specific API to conduct that plan, which is represented by the action. A related action should satisfy the following two rules.
1. The API name called by the action has similar semantics as the plan.
2. If the action is an input action, the texts to be inputted as shown in the plan should be correctly transformed into a parameter in the action.

Your output should be in the following json format:

{
	"Thought": <Show your thinking process and describe which rules this plan violates in short words>,
	"Relation": <Determine whether the action is related. The value should be boolean>
}

The action is:
\'\'\'
%s
\'\'\'

The plan that this action generated from is:
\'\'\'
%s
\'\'\'
'''