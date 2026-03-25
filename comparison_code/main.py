# ---------------------------------------------------------------------------- #
#                                    Moduli                                    #
# ---------------------------------------------------------------------------- #

# ----------------------------------- Cplex ---------------------------------- #
from docplex.cp.model import *
from docplex.cp.solver.cpo_callback import CpoCallback # --- https://github.com/IBMDecisionOptimization/docplex-examples/blob/master/examples/cp/basic/plant_location_with_cpo_callback.py
# ---------------------------------------------------------------------------- #

# -------------------------------- Named Tuple ------------------------------- #
from collections import namedtuple
# ---------------------------------------------------------------------------- #

# ----------------------------------- Plot ----------------------------------- #
import matplotlib as mpl
mpl.rcParams.update(mpl.rcParamsDefault)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator
from pylab import rcParams 
# ---------------------------------------------------------------------------- #

# ---------------------------------- Tkinter --------------------------------- #
import tkinter as tk
# ---------------------------------------------------------------------------- #

# ---------------------------------- Pathlib --------------------------------- #
import pathlib
# ---------------------------------------------------------------------------- #

# ----------------------------------- Json ----------------------------------- #
import json
# ---------------------------------------------------------------------------- #

# ----------------------------------- Copy ----------------------------------- #
import copy
# ---------------------------------------------------------------------------- #

# --------------------------------- Colorsys --------------------------------- #
import colorsys
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                               Global Parameters                              #
# ---------------------------------------------------------------------------- #

# ------------------------------ Data Structures ----------------------------- #
PATH = None
acquired_data = None
CASE_ID = 1
CASE_FOLDER = f"test_{CASE_ID}"
FORMATS = ["png","svg","eps","pdf"]
LLM = "gemini3_1" # ---"gemini3_1"
TIMES_and_TOKENS = [(54.4,6815),(41.0,5962),(43.6,5261),(40.8,6138),(37.1,5486),(45.9,6136),(44.8,6069),(37.5,5609),(42.1,5513),(39.2,5909),(0.0,0)]
LLM_TIME = TIMES_and_TOKENS[CASE_ID-1][0]
OUT_TOKENS = TIMES_and_TOKENS[CASE_ID-1][1]
# ---------------------------------------------------------------------------- #

# ----------------------------------- Path ----------------------------------- #
PATH = pathlib.Path(__file__).parent.resolve() # --- Current Folder
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #
def plan_converter(rawPlan_,resources_):
    # --------------------------------- Variables -------------------------------- #
    missions = {}

    # ----------------------------- Loop on subplans ----------------------------- #
    for subPlan_ in rawPlan_:
        # ---------------------------------- Objects --------------------------------- #
        objects = {}

        # ------------------------------------ ID ------------------------------------ #
        missions[subPlan_["cocktail"]] = {}

        # ----------------------------------- Steps ---------------------------------- #
        steps = {}

        # ------------------------------- Loop on steps ------------------------------ #
        for step_ in subPlan_["steps"]:

            # ------------------------------------ ID ------------------------------------ #
            stepID = step_["step"]
            steps[stepID] = {}

            # ---------------------------------- Action ---------------------------------- #
            steps[stepID]["action"] = {"type": step_["action"], "after": step_["after"]}

            # -------------------------- Objects: Field Creation ------------------------- #
            steps[stepID]["objects"] = []
            
            # -------------------------- Objects: Field Filling -------------------------- #
            for key_, value_ in step_["params"].items():

                # ---------------------------------- Append ---------------------------------- #
                steps[stepID]["objects"].append({"type": resources_[value_], "same_as_task": None if (key_ == "ingredient") | (value_ not in objects.keys()) else objects[value_]})

                # --------------------------------- Tracking --------------------------------- #
                if key_ != "ingredient" and value_ not in objects.keys():
                    objects[value_] = step_["step"]

            # ----------------------------------- Agent ---------------------------------- #
            steps[stepID]["agent"] = {"constraints": [{"type": "same_as_task", "task": step_["same_agent"]}]}
            
        # ----------------------------------- Save ----------------------------------- #
        missions[subPlan_["cocktail"]] = copy.deepcopy(steps)

    # ---------------------------------- Return ---------------------------------- #
    return missions

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                   Modelling                                  #
# ---------------------------------------------------------------------------- #

# ----------------------------- Global Parameters ---------------------------- #
NULL_DURATION = 1
MAX_DURATION = 0.0

# ------------------------- Actions: Load Description ------------------------ #
ACTION_DESCRIPTION = None
with open(file=f'{PATH}/action_des.json',mode='r') as f:
    ACTION_DESCRIPTION = json.load(fp=f)

# ------------------------ Actions: Adjust Description ----------------------- #
ACTION_DESCRIPTION = {action_des_["name"]: {"duration": action_des_["duration"], "params": {param_name_: param_id_ for param_id_, param_name_ in enumerate(action_des_["params"],start=0)} } for action_des_ in ACTION_DESCRIPTION}

# --------------------------- Actions: Create List --------------------------- #
ACTION_LIST = list(ACTION_DESCRIPTION.keys())

# --------------------- Actions: Extended List for Plots --------------------- #
ACTION_EXT_DESCRIPTION = None
with open(file=f'{PATH}/action_ext_list.json',mode='r') as f:
    ACTION_EXT_DESCRIPTION = json.load(fp=f)

# --------------------------- Actions: Refactoring --------------------------- #
ACTION_EXT_DESCRIPTION = {action_des_["id"]: {"action": action_des_["action"], "objects": action_des_["objects"]} for action_des_ in ACTION_EXT_DESCRIPTION}


# ------------------------- Agents: Load Description ------------------------- #
AGENT_DESCRIPTION = None
with open(file=f'{PATH}/agent_des.json',mode='r') as f:
    AGENT_DESCRIPTION = json.load(fp=f)

# ------------------------- Agent: Adjust Description ------------------------ #
AGENT_DESCRIPTION = {agent_["name"]: {"bimanual": agent_["bimanual"], "hand_dynamics": agent_["hand_dynamics"]} for agent_ in AGENT_DESCRIPTION}

# ---------------------------- Agents: Create List --------------------------- #
AGENT_LIST = list(AGENT_DESCRIPTION.keys())
AGENT_NB = len(AGENT_LIST)

# ------------------------ Resources: Load Description ----------------------- #
RESOURCE_DESCRIPTION = None
with open(file=f'{PATH}/resource_des.json',mode='r') as f:
    RESOURCE_DESCRIPTION = json.load(fp=f)

RESOURCES = {resource_["id"]: resource_["type"] for resource_ in RESOURCE_DESCRIPTION}

# --------------------------- Plan: Read from file --------------------------- #
RAW_PLAN = None
with open(file=f'{PATH}/{LLM}/{CASE_FOLDER}/generated_plan.json',mode='r') as fp:
    RAW_PLAN = json.load(fp)

# ----------------------------- Plan: Conversion ----------------------------- #
MISSIONS = plan_converter(rawPlan_=RAW_PLAN,resources_=RESOURCES)
NB_COCKTAILS = len(MISSIONS.keys())
MISSIONS_IDs = {value_: id_ for id_, value_ in enumerate(MISSIONS.keys())}


# -------------------------- Tools: Load Description ------------------------- #
RAW_TOOL_DESCRIPTION = None
with open(file=f'{PATH}/tool_des.json',mode='r') as f:
    RAW_TOOL_DESCRIPTION = json.load(fp=f)

# ------------------------- Tools: Adjust Description ------------------------ #
TOOL_DESCRIPTION = {}

for resource_id_, resource_type_ in RESOURCES.items():
    for tool_ in RAW_TOOL_DESCRIPTION:
        if resource_type_ == tool_["resource_type"]:
            TOOL_DESCRIPTION[resource_id_] = {"resource_type": resource_type_, "constraining_policy": tool_["constraining_policy"], "state": tool_["state"]}

            # -------------- Per ogni stato, lista di azioni che lo alterano ------------- #
            for tool_state_id_, tool_state_des_ in enumerate(TOOL_DESCRIPTION[resource_id_]["state"]):
                TOOL_DESCRIPTION[resource_id_]["state"][tool_state_id_]["related_actions"] = [state_action_["action"] for state_action_ in tool_state_des_["dynamics"] if state_action_["action"] != tool_state_des_["reset_action"]]
            break

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                    Solver                                    #
# ---------------------------------------------------------------------------- #

# ----------------------------------- Model ---------------------------------- #
model = CpoModel(name="optimizer")
# ---------------------------------------------------------------------------- #

# ------------------------------- Configuration ------------------------------ #
params = CpoParameters()
# params.TimeLimit = 30
# params.RandomSeed = 123
# params.Workers = 20
# params.FailureDirectedSearch = "On"
# params.FailureDirectedSearchEmphasis = 10
# params.FailureDirectedSearchMaxMemory = 1000000000
# params.RestartFailLimit = 1000
# params.RestartGrowthFactor = 1.3

params.TimeLimit = 180
params.RandomSeed = 123
params.Workers = 12

params.FailureDirectedSearch = "On"
params.FailureDirectedSearchEmphasis = 4
params.FailureDirectedSearchMaxMemory = 1000000000

params.RestartFailLimit = 5000
params.RestartGrowthFactor = 1.15

params.OptimalityTolerance = 10e-6
params.RelativeOptimalityTolerance = 10e-6
params.LogVerbosity = "Terse"
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                              Decision Variables                              #
# ---------------------------------------------------------------------------- #

# --------------------------------- Makespan --------------------------------- #
makespan = integer_var(min=0,name="makespan")

# ------------------------- Tasks: Interval Variables ------------------------ #
task_intervals = {}

for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        # ---------------------------- Interval Variables ---------------------------- #
        action_type = task_value_["action"]["type"]
        task_length = (NULL_DURATION,ACTION_DESCRIPTION[action_type]["duration"]["base_value"]) if ACTION_DESCRIPTION[action_type]["duration"]["type"] != "fixed" else ACTION_DESCRIPTION[action_type]["duration"]["base_value"]
        task_intervals[task_id_] = interval_var(start=(0,INTERVAL_MAX),end=(0,INTERVAL_MAX),length=task_length,name=f'{mission_id_}_task#{task_id_}_{action_type}')

# --------------------------------- Missions --------------------------------- #
mission_end_times = {}

for mission_id_, mission_des_ in MISSIONS.items():
    mission_end_times[mission_id_] = integer_var(name=f'mission_id_')
    
# ------------------------ Agents: Interval Variables ------------------------ #
agents = {agent_id_: {"interval_vars": {}, "hands": step_at(t=0,h=2) if agent_des_["bimanual"] else step_at(t=0,h=1)} for agent_id_, agent_des_ in AGENT_DESCRIPTION.items()}

for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        for agent_ in AGENT_LIST:
            # ---------------------------- Interval Variables ---------------------------- #
            agents[agent_]["interval_vars"][task_id_] = interval_var(optional=True,name=f'{agent_}_{mission_id_}_task#{task_id_}_{task_value_["action"]["type"]}')

            # ----------------------- Cumulative Expression: Hands ----------------------- #
            for action_ in AGENT_DESCRIPTION[agent_]["hand_dynamics"]:
                if action_["action"] == task_value_["action"]["type"]:
                    if action_["effect"]["op"] == "minus":
                        if action_["when"] == "start":
                            agents[agent_]["hands"] = agents[agent_]["hands"] - step_at_start(interval=agents[agent_]["interval_vars"][task_id_],height=action_["effect"]["value"])
                        elif action_["when"] == "end":
                            agents[agent_]["hands"] = agents[agent_]["hands"] - step_at_end(interval=agents[agent_]["interval_vars"][task_id_],height=action_["effect"]["value"])
                    elif action_["effect"]["op"] == "plus":
                        if action_["when"] == "start":
                            agents[agent_]["hands"] = agents[agent_]["hands"] + step_at_start(interval=agents[agent_]["interval_vars"][task_id_],height=action_["effect"]["value"])
                        elif action_["when"] == "end":
                            agents[agent_]["hands"] = agents[agent_]["hands"] + step_at_end(interval=agents[agent_]["interval_vars"][task_id_],height=action_["effect"]["value"])
# ---------------------------------------------------------------------------- #

# ---------------------- Resources: Dictionary Creation ---------------------- #
resources = {resource_["id"]: {"interval_vars": {}, "mission_lock": None, "avail": step_at(t=0,h=1), "type": resource_["type"], "state": {}} for resource_ in RESOURCE_DESCRIPTION}

# ----------------------- Resources: Tools Description ----------------------- #
for tool_id_, tool_des_ in TOOL_DESCRIPTION.items():
    # ----------------------------------- Lock ----------------------------------- #
    resources[tool_id_]["mission_lock"] = {} if tool_des_["constraining_policy"] == "mission" else None

    for tool_state_ in tool_des_["state"]:
        # ------------------------ State: Cumulative Function ------------------------ #
        resources[tool_id_]["state"][tool_state_["name"]] = step_at(t=0,h=tool_state_["initial_value"])

        # ---------------------- State: Interval Variables Field --------------------- #
        field_name = f'{tool_state_["name"]}_{min(tool_state_["values"])}_{max(tool_state_["values"])}_interval_vars'
        resources[tool_id_]["state"][field_name] = {}

        # ----------- State: Interval Variables Field (Saturation Handling) ---------- #
        if tool_state_["type"] == "boolean":
            field_name = f'{tool_state_["name"]}_sat_lvl_interval_vars' # --- Campo della variabile intervallo per gestire saturazione
            resources[tool_id_]["state"][field_name] = {}

            field_name = f'{tool_state_["name"]}_no_sat_lvl_interval_vars' # --- Campo della variabile intervallo per gestire saturazione
            resources[tool_id_]["state"][field_name] = {}

# ----------------------- Resources: Interval Variables ---------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        for task_object_des_ in task_value_["objects"]:
            # ----------------------------- Loop on resources ---------------------------- #
            for resource_ in RESOURCE_DESCRIPTION:
                # ------------------------------ Action Details ------------------------------ #
                action_type = task_value_["action"]["type"]
                action_objects = task_value_["objects"]

                # ----------------------------- Resource Details ----------------------------- #
                resource_id = resource_["id"]
                resource_type = resource_["type"]

                if task_object_des_["type"] == resource_type:
                    # ------------------ Interval Variable - Resource Allocation ----------------- #
                    resources[resource_id]["interval_vars"][task_id_] = interval_var(optional=True, name=f'{resource_id}_{mission_id_}_task#{task_id_}_{action_type}')

                    # ------------------------------- Availability ------------------------------- #
                    temp_bloc_action_type = resource_["blocking_action"]["temporarly"]["name"]
                    temp_bloc_action_param = resource_["blocking_action"]["temporarly"]["on_param"]
                    temp_bloc_action_instant = resource_["blocking_action"]["temporarly"]["when"]


                    if resource_["blocking_action"]["permanently"] is not None:
                        perm_bloc_action_type = resource_["blocking_action"]["permanently"]["name"]
                        perm_bloc_action_param = resource_["blocking_action"]["permanently"]["on_param"]
                        perm_bloc_action_instant = resource_["blocking_action"]["permanently"]["when"]
                    else:
                        perm_bloc_action_type = None


                    release_bloc_action_type = resource_["release_action"]["name"]
                    release_bloc_action_param = resource_["release_action"]["on_param"]
                    release_bloc_action_instant = resource_["release_action"]["when"]

                    
                    if action_type == temp_bloc_action_type and action_objects[ACTION_DESCRIPTION[temp_bloc_action_type]["params"][temp_bloc_action_param]]["type"] == resource_type:
                        if temp_bloc_action_instant == "start":
                            resources[resource_id]["avail"] = resources[resource_id]["avail"] - step_at_start(interval=resources[resource_id]["interval_vars"][task_id_],height=1)
                        else:
                            resources[resource_id]["avail"] = resources[resource_id]["avail"] - step_at_end(interval=resources[resource_id]["interval_vars"][task_id_],height=1)

                    if perm_bloc_action_type is not None and action_type == perm_bloc_action_type and action_objects[ACTION_DESCRIPTION[perm_bloc_action_type]["params"][perm_bloc_action_param]]["type"] == resource_type:
                        if perm_bloc_action_instant == "start":
                            resources[resource_id]["avail"] = resources[resource_id]["avail"] - step_at_start(interval=resources[resource_id]["interval_vars"][task_id_],height=1)
                        else:
                            resources[resource_id]["avail"] = resources[resource_id]["avail"] - step_at_end(interval=resources[resource_id]["interval_vars"][task_id_],height=1)

                    if action_type == release_bloc_action_type and action_objects[ACTION_DESCRIPTION[release_bloc_action_type]["params"][release_bloc_action_param]]["type"] == resource_type:
                        if release_bloc_action_instant == "start":
                            resources[resource_id]["avail"] = resources[resource_id]["avail"] + step_at_start(interval=resources[resource_id]["interval_vars"][task_id_],height=1)
                        else:
                            resources[resource_id]["avail"] = resources[resource_id]["avail"] + step_at_end(interval=resources[resource_id]["interval_vars"][task_id_],height=1)

                    # ------------------- Interval Variable - State Description ------------------ #
                    if resource_id in TOOL_DESCRIPTION.keys():
                        for state_ in TOOL_DESCRIPTION[resource_id]["state"]: # --- Scorro gli stati

                            # -------------------------------- Field Name -------------------------------- #
                            field_name = f'{state_["name"]}_{min(state_["values"])}_{max(state_["values"])}_interval_vars' # --- Campo delle variabili intervallo relative allo stato

                            # -------------------------------- Base Value -------------------------------- #
                            initial_value = state_["initial_value"]

                            for state_value_ in range(min(state_["values"]),max(state_["values"])+1):
                                # --------------------------------- Duration --------------------------------- #
                                task_length = ACTION_DESCRIPTION[action_type]["duration"]["base_value"] if state_value_ != initial_value else NULL_DURATION

                                # --------------------------------- Variable --------------------------------- #
                                resources[resource_id]["state"][field_name][(state_value_,task_id_)] = interval_var(optional=True,length=task_length,name=f'{resource_id}_{state_["name"]}_{state_value_}_{mission_id_}_task#{task_id_}_{action_type}')

                            # -------------------------------- Saturation -------------------------------- #
                            if state_["type"] == "boolean" and action_type != state_["reset_action"]:
                                for state_action_ in state_["dynamics"]:
                                    if state_action_["action"] == action_type and action_objects[ACTION_DESCRIPTION[state_action_["action"]]["params"][state_action_["on_param"]]]["type"] == resource_type:
                                        # -------------------------------- Field Name -------------------------------- #
                                        field_name = f'{state_["name"]}_sat_lvl_interval_vars' # --- Campo della variabile intervallo per gestire saturazione

                                        # ----------------------------- Saturation Value ----------------------------- #
                                        sat_value = 1 - state_["initial_value"]

                                        # ----------------------------- Interval Variable ---------------------------- #
                                        resources[resource_id]["state"][field_name][(sat_value,task_id_)] = interval_var(optional=True,name=f'{resource_id}_{state_["name"]}_sat_{mission_id_}_task#{task_id_}_{action_type}')

                                        # -------------------------------- Field Name -------------------------------- #
                                        field_name = f'{state_["name"]}_no_sat_lvl_interval_vars' # --- Campo della variabile intervallo per gestire saturazione

                                        # ----------------------------- Saturation Value ----------------------------- #
                                        no_sat_value = state_["initial_value"]

                                        # ----------------------------- Interval Variable ---------------------------- #
                                        resources[resource_id]["state"][field_name][(no_sat_value,task_id_)] = interval_var(optional=True,name=f'{resource_id}_{state_["name"]}_not_sat_{mission_id_}_task#{task_id_}_{action_type}')

                                                            
                        # --------------------------------- Dynamics --------------------------------- #
                        for state_ in TOOL_DESCRIPTION[resource_id]["state"]: # --- Scorro gli stati
                            for state_action_ in state_["dynamics"]: # --- Scorro le azioni che influenzano lo stato
                                # -------------------------------- Field Name -------------------------------- #
                                field_name = f'{state_["name"]}_sat_lvl_interval_vars' # --- Campo della variabile intervallo per gestire saturazione

                                # ----------------------------- Saturation Value ----------------------------- #
                                sat_value = 1 - state_["initial_value"]
                                
                                if action_type != state_["reset_action"] and action_type == state_action_["action"] and action_objects[ACTION_DESCRIPTION[state_action_["action"]]["params"][state_action_["on_param"]]]["type"] == resource_type: # --- Verifico la compatibilità
                                    if state_action_["when"] == "start":
                                        if state_action_["effect"]["op"] == "minus":
                                            if state_["type"] == "boolean":
                                                # ---------------------- Variation in case of Saturation --------------------- #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] - step_at_start(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"]) + step_at_start(interval=resources[resource_id]["state"][field_name][(sat_value,task_id_)],height=state_action_["effect"]["value"])
                                            else:
                                                # ------------------------------ Base Variation ------------------------------ #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] - step_at_start(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"])
                                        elif state_action_["effect"]["op"] == "plus":
                                            if state_["type"] == "boolean":
                                                # ---------------------- Variation in case of Saturation --------------------- #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] + step_at_start(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"]) - step_at_start(interval=resources[resource_id]["state"][field_name][(sat_value,task_id_)],height=state_action_["effect"]["value"])
                                            else:
                                                # ------------------------------ Base Variation ------------------------------ #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] + step_at_start(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"])

                                    elif state_action_["when"] == "end":
                                        if state_action_["effect"]["op"] == "minus":
                                            if state_["type"] == "boolean":
                                                # ---------------------- Variation in case of Saturation --------------------- #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] - step_at_end(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"]) + step_at_end(interval=resources[resource_id]["state"][field_name][(sat_value,task_id_)],height=state_action_["effect"]["value"])
                                            else:
                                                # ------------------------------ Base Variation ------------------------------ #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] - step_at_end(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"])
                                        elif state_action_["effect"]["op"] == "plus":
                                            if state_["type"] == "boolean":
                                                # ---------------------- Variation in case of Saturation --------------------- #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] + step_at_end(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"]) - step_at_end(interval=resources[resource_id]["state"][field_name][(sat_value,task_id_)],height=state_action_["effect"]["value"])
                                            else:
                                                # ------------------------------ Base Variation ------------------------------ #
                                                resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] + step_at_end(interval=resources[resource_id]["interval_vars"][task_id_],height=state_action_["effect"]["value"])

                        # ----------------------------------- Reset ---------------------------------- #
                        for state_ in TOOL_DESCRIPTION[resource_id]["state"]: # --- Scorro gli stati
                            # -------------------------------- Field Name -------------------------------- #
                            field_name = f'{state_["name"]}_{min(state_["values"])}_{max(state_["values"])}_interval_vars' # --- Campo delle variabili intervallo relative allo stato

                            # -------------------------------- Base Value -------------------------------- #
                            initial_value = state_["initial_value"]

                            # --------------------------------- Dynamics --------------------------------- #
                            for state_action_ in state_["dynamics"]: # --- Scorro le azioni che influenzano lo stato
                                if action_type == state_["reset_action"] and action_type == state_action_["action"] and action_objects[ACTION_DESCRIPTION[state_action_["action"]]["params"][state_action_["on_param"]]]["type"] == resource_type: # --- Verifico la compatibilità
                                    # ----------------------------------- Value ---------------------------------- #
                                    effect_value = state_action_["effect"]["value"]
                                    
                                    if state_action_["when"] == "start":
                                        if state_action_["effect"]["op"] == "minus":
                                            # ------------------------------ Reset Interval ------------------------------ #
                                            interval_id = initial_value + effect_value

                                            # ---------------------------------- Update ---------------------------------- #
                                            resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] - step_at_start(interval=resources[resource_id]["state"][field_name][(interval_id,task_id_)],height=state_action_["effect"]["value"])
                                        elif state_action_["effect"]["op"] == "plus":
                                            # ------------------------------ Reset Interval ------------------------------ #
                                            interval_id = initial_value - effect_value

                                            # ---------------------------------- Update ---------------------------------- #
                                            resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] + step_at_start(interval=resources[resource_id]["state"][field_name][(interval_id,task_id_)],height=state_action_["effect"]["value"])
                                    elif state_action_["when"] == "end":
                                        if state_action_["effect"]["op"] == "minus":
                                            # ------------------------------ Reset Interval ------------------------------ #
                                            interval_id = initial_value + effect_value

                                            # ---------------------------------- Update ---------------------------------- #
                                            resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] - step_at_end(interval=resources[resource_id]["state"][field_name][(interval_id,task_id_)],height=state_action_["effect"]["value"])
                                        elif state_action_["effect"]["op"] == "plus":
                                            # ------------------------------ Reset Interval ------------------------------ #
                                            interval_id = initial_value - effect_value

                                            # ---------------------------------- Update ---------------------------------- #
                                            resources[resource_id]["state"][state_["name"]] = resources[resource_id]["state"][state_["name"]] + step_at_end(interval=resources[resource_id]["state"][field_name][(interval_id,task_id_)],height=state_action_["effect"]["value"])                                         

# ------------------------------ Resources: Lock ----------------------------- #
lock_variables = {}

for resource_id_, resource_des_ in resources.items():
    if resource_des_["mission_lock"] is not None:
        lock_variables[resource_id_] = {}
        for mission_id_, mission_des_ in MISSIONS.items():
            lock_variables[resource_id_][mission_id_] = interval_var(optional=True,name=f'lock_interval_var_{resource_id_}_{mission_id_}')
                    
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                  Constraints                                 #
# ---------------------------------------------------------------------------- #

# --------------------------------- Missions --------------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    task_ids = list(mission_des_.keys())
    end_times = [end_of(task_var) for task_id_, task_var in task_intervals.items() if task_id_ in list(mission_des_.keys())]
    model.add(mission_end_times[mission_id_] == max_of(end_times))

# ------------------------------ Resources: Lock ----------------------------- #
for resource_id_, resource_des_ in resources.items():
    if resource_des_["mission_lock"] is not None:
        all_lock_vars = []
        for mission_id_, mission_des_ in MISSIONS.items():
            e1=any_of([presence_of(interval=res_task_var_) == True for res_task_id_, res_task_var_ in resource_des_["interval_vars"].items() if res_task_id_ in mission_des_.keys()]) == True
            model.add(if_then(e1=e1,e2=presence_of(interval=lock_variables[resource_id_][mission_id_]) == True))
            model.add(span(interval=lock_variables[resource_id_][mission_id_],array=[res_task_var_ for res_task_id_, res_task_var_ in resource_des_["interval_vars"].items() if res_task_id_ in mission_des_.keys()]))
            
            all_lock_vars.append(lock_variables[resource_id_][mission_id_])
        model.add(no_overlap(all_lock_vars))

# --------------------------------- Makespan --------------------------------- #
model.add(makespan == max_of([end_of(task_intervals[task_key_]) for task_key_ in task_intervals.keys()]))

# -------------------------- Tasks: Execution Order -------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_after_id_, task_i_des_ in mission_des_.items():
        for task_before_id_ in task_i_des_["action"]["after"]:
            # ----------------------------- Task Interessati ----------------------------- #
            task_before = task_intervals[task_before_id_]
            task_after = task_intervals[task_after_id_]

            # ---------------------------------- Vincolo --------------------------------- #
            model.add(end_before_start(a=task_before,b=task_after))

# ------------------------------ Tasks: Duration ----------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        # -------------------------------- Task Action ------------------------------- #
        action_type = task_value_["action"]["type"]
        if ACTION_DESCRIPTION[action_type]["duration"]["type"] == "variable":

            # ---------------------------- Loop sulle Risorse ---------------------------- #
            for resource_id_, resource_vars_ in resources.items():

                # ---------------- Verifica della compatibilità: Task-Risorsa ---------------- #
                if resource_id_ in TOOL_DESCRIPTION.keys() and task_id_ in resource_vars_["interval_vars"].keys():

                    # ------------- Loop sugli Stati: Inviduare lo Stato interessato ------------- #
                    for state_ in TOOL_DESCRIPTION[resource_id_]["state"]:
                        if action_type == state_["reset_action"]:
                            # ---------------------- State: Interval Variables Field --------------------- #
                            field_name = f'{state_["name"]}_{min(state_["values"])}_{max(state_["values"])}_interval_vars'
                            
                            # -------------------------------- Alternative ------------------------------- #
                            model.add(alternative(resource_vars_["interval_vars"][task_id_],[resource_vars_["state"][field_name][key_] for key_ in resource_vars_["state"][field_name].keys() if key_[1] == task_id_]))

                            # ---------------------------------- Vincolo --------------------------------- #
                            for key_ in resource_vars_["state"][field_name].keys():
                                if key_[1] == task_id_:
                                    model.add(always_in(function=resource_vars_["state"][state_["name"]],interval=resource_vars_["state"][field_name][(key_)],min=key_[0],max=key_[0]))

# ---------------------------- Agents: Allocation ---------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_des_ in mission_des_.items():

        # -------------------- Agenti in grado di eseguire il task ------------------- #
        agent_list = [value_ for agent_vars_ in agents.values() for key_, value_ in agent_vars_["interval_vars"].items() if key_ == task_id_]

        # ---------------------------------- Vincolo --------------------------------- #
        model.add(alternative(interval=task_intervals[task_id_],array=agent_list))

# -------------------------- Agents: Allocation PT2 -------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_des_ in mission_des_.items():
        for constraint_ in task_des_["agent"]["constraints"]:
            # --------- Pre-Condizione: Agente che esegue X deve eseguire anche Y -------- #
            if constraint_["type"] == "same_as_task" and constraint_["task"] is not None:
                # ----------------------------- Loop sugli agenti ---------------------------- #
                for agent_vars_ in agents.values():
                    if task_id_ in agent_vars_["interval_vars"].keys():
                        # ----------- Interval Variables di Allocazione dell'Agente al Task ---------- #
                        current_task = agent_vars_["interval_vars"][task_id_]
                        required_task = agent_vars_["interval_vars"][constraint_["task"]]

                        # ---------------------------------- Vincolo --------------------------------- #
                        model.add(if_then(e1=presence_of(interval=required_task),e2=presence_of(interval=current_task)))

# ---------------------- Agents: NoOverlap - LimitUsage ---------------------- #
for worker_ in AGENT_LIST:
    # -------------------------------- Constraint -------------------------------- #
    if len(agents[worker_]["interval_vars"].keys()) > 0:
        model.add(no_overlap(sequence=agents[worker_]["interval_vars"].values()))

    # ---------------------- Vincolo sulle capacità di presa --------------------- #
    model.add(cumul_range(function=agents[worker_]["hands"],min=0,max=2))

# --------------------------- Resources: Allocation -------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_des_ in mission_des_.items():
        for task_object_des_ in task_des_["objects"]:
            # ---------------------------- Risorse Allocabili ---------------------------- #
            resource_list = [value_ for resource_vars_ in resources.values() for key_, value_ in resource_vars_["interval_vars"].items() if key_ == task_id_ and resource_vars_["type"] == task_object_des_["type"]]

            # ---------------------------------- Vincolo --------------------------------- #
            model.add(alternative(interval=task_intervals[task_id_],array=resource_list))

            # ------- Pre-Condizione: Risorsa Usata sul Task X da usare anche su Y ------- #
            if task_object_des_["same_as_task"] is not None:
                for resource_vars_ in resources.values():
                    if resource_vars_["type"] == task_object_des_["type"] and task_id_ in resource_vars_["interval_vars"].keys() and task_object_des_["same_as_task"] in resource_vars_["interval_vars"].keys():
                        # -------------------------------- Intervalli -------------------------------- #
                        e1_interval = resource_vars_["interval_vars"][task_id_]
                        e2_interval = resource_vars_["interval_vars"][task_object_des_["same_as_task"]]

                        # ---------------------------------- Vincolo --------------------------------- #
                        model.add(if_then(e1=presence_of(interval=e2_interval) == False, e2=presence_of(interval=e1_interval) == False))

# ----------------------- Resources: States Saturation ----------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_des_ in mission_des_.items():
        for resource_id_, resource_des_ in resources.items():
            if task_id_ in resource_des_["interval_vars"].keys() and  resource_id_ in TOOL_DESCRIPTION.keys():
                for state_ in TOOL_DESCRIPTION[resource_id_]["state"]:
                    # ------------------------------- Interval List ------------------------------ #
                    alternative_list = []

                    # ----------------------------------- Loop ----------------------------------- #
                    if state_["type"] == "boolean" and task_des_["action"]["type"] != state_["reset_action"]:
                        for state_action_ in state_["dynamics"]:
                            if state_action_["action"] == task_des_["action"]["type"] and task_des_["objects"][ACTION_DESCRIPTION[state_action_["action"]]["params"][state_action_["on_param"]]]["type"] == resource_des_["type"]:
            
                                # -------------------------------- Field Name -------------------------------- #
                                field_name = f'{state_["name"]}_sat_lvl_interval_vars'

                                # ----------------------------- Saturation Value ----------------------------- #
                                sat_value = 1 - state_["initial_value"]

                                # -------------------------------- Update List ------------------------------- #
                                alternative_list.append(resources[resource_id_]["state"][field_name][(sat_value,task_id_)])

                                # ------------------------------- Pre-condition ------------------------------ #
                                model.add(always_in(function=resource_des_["state"][state_["name"]],interval=resources[resource_id_]["state"][field_name][(sat_value,task_id_)],min=sat_value,max=sat_value))

                                # -------------------------------- Field Name -------------------------------- #
                                field_name = f'{state_["name"]}_no_sat_lvl_interval_vars'

                                # ----------------------------- Saturation Value ----------------------------- #
                                no_sat_value = state_["initial_value"]

                                # -------------------------------- Update List ------------------------------- #
                                alternative_list.append(resources[resource_id_]["state"][field_name][(no_sat_value,task_id_)])

                                # ------------------------------- Pre-condition ------------------------------ #
                                model.add(always_in(function=resource_des_["state"][state_["name"]],interval=resources[resource_id_]["state"][field_name][(no_sat_value,task_id_)],min=no_sat_value,max=no_sat_value))


                    # ---------------------------------- Vincolo --------------------------------- #
                    if len(alternative_list) > 0:
                        model.add(alternative(interval=resource_des_["interval_vars"][task_id_],array=alternative_list))

# --------------------- Resources: NoOverlap - LimitUsage -------------------- #
for resource_id_, resource_vars_ in resources.items():
    # --------------------------------- NoOverlap -------------------------------- #
    if len(resource_vars_["interval_vars"].values()) > 0:
        model.add(no_overlap(sequence=list(resource_vars_["interval_vars"].values())))

    # -------------------------------- Limit Usage ------------------------------- #
    model.add(cumul_range(function=resource_vars_["avail"],min=0,max=1))

    # ------------------------------ Limit on State ------------------------------ #
    if resource_id_ in TOOL_DESCRIPTION.keys():
        # ------------------------------ Loop on States ------------------------------ #
        for state_ in TOOL_DESCRIPTION[resource_id_]["state"]:
            model.add(cumul_range(function=resource_vars_["state"][state_["name"]],min=min(state_["values"]),max=max(state_["values"])))
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                     Solve                                    #
# ---------------------------------------------------------------------------- #

# --------------------------------- Objective -------------------------------- #
model.add(minimize(makespan))
# ---------------------------------------------------------------------------- #

# --------------------------------- Solution --------------------------------- #
solution = model.solve(params=params)
solution.print_solution()
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                 Show Solution                                #
# ---------------------------------------------------------------------------- #

# --------------------------------- Functions -------------------------------- #
def get_screen_figsize(default=(30,4)):
    try:
        root = tk.Tk()
        root.withdraw()
        width_px = root.winfo_screenwidth()
        height_px = root.winfo_screenheight()
        root.destroy()
        dpi = mpl.rcParams.get("figure.dpi", 300)
        return (width_px / dpi, height_px / dpi)
    except Exception:
        return default

def get_contrasting_text_color(background_color): # --- Genera automaticamente il colore del testo (nero o bianco) in base al colore di sfondo della barra.
    # ---------------------------- Conversione in RGB ---------------------------- #
    r, g, b = mpl.colors.to_rgb(background_color)

    # -------------------------- Calcolo della luminanza ------------------------- #
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # ------------------------------ Set del Colore ------------------------------ #
    return "#111111" if luminance > 0.6 else "#f5f5f5"

def pastel_colors(n, sat=0.35, val=0.95):
    return [colorsys.hsv_to_rgb(i / n, sat, val) for i in range(n)]

# ---------------------------------------------------------------------------- #

# -------------------------------- Parameters -------------------------------- #
FIGSIZE_FULLSCREEN = get_screen_figsize()

# ---------------------------- Plot: Configuration --------------------------- #
fig, ax = plt.subplots(nrows=4,ncols=1,sharex=True,figsize=(14,11))

bar_height = 0.40
label_fontsize = 8
title_fontsize = 18
tick_fontsize = 13

colors = plt.cm.Set3.colors
task_colors = {name: colors[num % len(colors)] for num, name in enumerate(ACTION_LIST)}

colors = plt.cm.tab20.colors
task_colors_v2 = {name: colors[num % len(colors)] for num, name in enumerate(ACTION_EXT_DESCRIPTION.keys())}

# colors = pastel_colors(len(ACTION_EXT_DESCRIPTION.keys()))  # 40 colori pastello
# task_colors_v2 = {name: colors[num % len(colors)] for num, name in enumerate(ACTION_EXT_DESCRIPTION.keys())}

cocktail_tick = {cocktail_: cocktail_id_ for cocktail_id_, cocktail_ in enumerate(MISSIONS.keys())}
ax[1].set_yticks(list(cocktail_tick.values()))
ax[1].set_yticklabels(list(cocktail_tick.keys()))
ax[1].grid(True, axis='x', linestyle='--', alpha=0.5)
ax[1].xaxis.set_major_locator(MultipleLocator(10))
ax[1].tick_params(axis='x', labelsize=tick_fontsize)
ax[1].tick_params(axis='y', labelsize=tick_fontsize)
ax[1].set_title("Cocktails' Timeline", fontsize=title_fontsize)
ax[1].set_xlim(0,200)

worker_tick = {worker_: worker_id_ for worker_id_, worker_ in enumerate(AGENT_LIST)}
ax[0].set_yticks(list(worker_tick.values()))
ax[0].set_yticklabels(list(worker_tick.keys()))
ax[0].set_ylim(-0.5, len(list(worker_tick.keys())) - 0.5) # --- Visualizzazione di tutti gli elementi
ax[0].grid(True, axis='x', linestyle='--', alpha=0.5)
ax[0].xaxis.set_major_locator(MultipleLocator(10))
ax[0].tick_params(axis='x', labelsize=tick_fontsize)
ax[0].tick_params(axis='y', labelsize=tick_fontsize)
ax[0].set_title("Agents' Timeline", fontsize=title_fontsize)
ax[0].set_xlim(0,200)

shots_tick = {shot_: shot_id_ for shot_id_, shot_ in enumerate([key_ for key_, value_ in resources.items() if value_["type"] == "shot"])}
ax[2].set_yticks(list(shots_tick.values()))
ax[2].set_yticklabels(list(shots_tick.keys()))
ax[2].set_ylim(-0.5, len(list(shots_tick.keys())) - 0.5) # --- Visualizzazione di tutti gli elementi
ax[2].grid(True, axis='x', linestyle='--', alpha=0.5)
ax[2].xaxis.set_major_locator(MultipleLocator(10))
ax[2].tick_params(axis='x', labelsize=tick_fontsize)
ax[2].tick_params(axis='y', labelsize=tick_fontsize)
ax[2].set_title("Shot Glasses' Timeline", fontsize=title_fontsize)
ax[2].set_xlim(0,200)

shakers_tick = {shaker_: shaker_id_ for shaker_id_, shaker_ in enumerate([key_ for key_, value_ in resources.items() if value_["type"] == "shaker"])}
ax[3].set_yticks(list(shakers_tick.values()))
ax[3].set_yticklabels(list(shakers_tick.keys()))
ax[3].set_ylim(-0.5, len(list(shakers_tick.keys())) - 0.5) # --- Visualizzazione di tutti gli elementi
ax[3].grid(True, axis='x', linestyle='--', alpha=0.5)
ax[3].xaxis.set_major_locator(MultipleLocator(10))
ax[3].tick_params(axis='x', labelsize=tick_fontsize)
ax[3].tick_params(axis='y', labelsize=tick_fontsize)
ax[3].set_title("Shakers' Timeline", fontsize=title_fontsize)
ax[3].set_xlabel("Time", fontsize=13)
ax[3].set_xlim(0,200)
# ---------------------------------------------------------------------------- #

# ----------------------------------- Tasks ---------------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():

        # ----------------------------------- Times ---------------------------------- #
        var_sol = solution.get_var_solution(name=task_intervals[task_id_]) 
        start_time = var_sol.get_start()
        end_time = var_sol.get_end()

        # ------------------------------- Find Color ID ------------------------------ #
        for action_id_, action_des_ in ACTION_EXT_DESCRIPTION.items():
            if action_des_["action"] == task_value_["action"]["type"] and action_des_["objects"] == [task_object_["type"] for task_object_ in task_value_["objects"]]:
                color_id = action_id_
                break

        color = task_colors_v2[color_id]
        # color = task_colors[task_value_["action"]["type"]]
        # ----------------------------------- Plot ----------------------------------- #
        ax[1].barh(cocktail_tick[mission_id_], end_time - start_time, left=start_time, color=color, height=bar_height, edgecolor='black', linewidth=0.3, zorder=3)
        ax[1].text(start_time + (end_time - start_time) / 2.0, cocktail_tick[mission_id_], f'{task_id_}', va='center', ha='center', color=get_contrasting_text_color(color), fontsize=label_fontsize, fontweight='bold', clip_on=True)
# ---------------------------------------------------------------------------- #

# ---------------------------------- Workers --------------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        for worker_ in AGENT_LIST:
            var_sol = solution.get_var_solution(agents[worker_]["interval_vars"][task_id_]) 
            if var_sol.is_present():
                # ----------------------------------- Times ---------------------------------- #
                start_time = var_sol.get_start()
                end_time = var_sol.get_end()

                # ------------------------------- Find Color ID ------------------------------ #
                for action_id_, action_des_ in ACTION_EXT_DESCRIPTION.items():
                    if action_des_["action"] == task_value_["action"]["type"] and action_des_["objects"] == [task_object_["type"] for task_object_ in task_value_["objects"]]:
                        color_id = action_id_
                        break

                color = task_colors_v2[color_id]
                # color = task_colors[task_value_["action"]["type"]]

                # ----------------------------------- Plots ---------------------------------- #
                ax[0].barh(worker_tick[worker_], end_time - start_time, left=start_time, color=color, height=bar_height, edgecolor='black', linewidth=0.3, zorder=3)
                ax[0].text(start_time + (end_time - start_time) / 2.0, worker_tick[worker_], f'{task_id_}', va='center', ha='center', color=get_contrasting_text_color(color), fontsize=label_fontsize, fontweight='bold', clip_on=True)
# ---------------------------------------------------------------------------- #

# ----------------------------------- Shots ---------------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        for resource_, resource_vars_ in resources.items():
            if resource_vars_["type"] == "shot":
                for key_, interval_ in resource_vars_["interval_vars"].items():
                    if task_id_ == key_:
                        var_sol = solution.get_var_solution(interval_) 
                        if var_sol.is_present():
                            # ----------------------------------- Times ---------------------------------- #
                            start_time = var_sol.get_start()
                            end_time = var_sol.get_end()
                            
                            # ------------------------------- Find Color ID ------------------------------ #
                            for action_id_, action_des_ in ACTION_EXT_DESCRIPTION.items():
                                if action_des_["action"] == task_value_["action"]["type"] and action_des_["objects"] == [task_object_["type"] for task_object_ in task_value_["objects"]]:
                                    color_id = action_id_
                                    break

                            color = task_colors_v2[color_id]
                            # color = task_colors[task_value_["action"]["type"]]

                            # ----------------------------------- Plots ---------------------------------- #
                            ax[2].barh(shots_tick[resource_], end_time - start_time, left=start_time, color=color, height=bar_height, edgecolor='black', linewidth=0.3, zorder=3)
                            ax[2].text(start_time + (end_time - start_time) / 2.0, shots_tick[resource_], f'{task_id_}', va='center', ha='center', color=get_contrasting_text_color(color), fontsize=label_fontsize, fontweight='bold', clip_on=True)
# ---------------------------------------------------------------------------- #

# ---------------------------------- Shakers --------------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        for resource_, resource_vars_ in resources.items():
            if resource_vars_["type"] == "shaker":
                for key_, interval_ in resource_vars_["interval_vars"].items():
                    if task_id_ == key_:
                        var_sol = solution.get_var_solution(interval_) 
                        if var_sol.is_present():
                            # ----------------------------------- Times ---------------------------------- #
                            start_time = var_sol.get_start()
                            end_time = var_sol.get_end()

                            # ------------------------------- Find Color ID ------------------------------ #
                            for action_id_, action_des_ in ACTION_EXT_DESCRIPTION.items():
                                if action_des_["action"] == task_value_["action"]["type"] and action_des_["objects"] == [task_object_["type"] for task_object_ in task_value_["objects"]]:
                                    color_id = action_id_
                                    break

                            color = task_colors_v2[color_id]
                            # color = task_colors[task_value_["action"]["type"]]
                            
                            # ----------------------------------- Plots ---------------------------------- #
                            ax[3].barh(shakers_tick[resource_], end_time - start_time, left=start_time, color=color, height=bar_height, edgecolor='black', linewidth=0.3, zorder=3)
                            ax[3].text(start_time + (end_time - start_time) / 2.0, shakers_tick[resource_], f'{task_id_}', va='center', ha='center', color=get_contrasting_text_color(color), fontsize=label_fontsize, fontweight='bold', clip_on=True)
# ---------------------------------------------------------------------------- #

# ----------------------------------- Show ----------------------------------- #
legend_handles = [mpatches.Patch(color=task_colors_v2[action_], label=action_) for action_ in ACTION_EXT_DESCRIPTION.keys()]
# fig.legend(handles=legend_handles, loc="lower center", ncol=min(len(ACTION_LIST), 7), frameon=True, fontsize=9)

leg = ax[3].legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.35), ncol=min(len(ACTION_EXT_DESCRIPTION.keys()), 5), frameon=True, fontsize=11)
leg.set_in_layout(True)

# fig.legend(handles=legend_handles, loc="lower center", ncol=min(len(ACTION_EXT_DESCRIPTION.keys()), 7), frameon=True, fontsize=9)
# plt.show()

for format_ in FORMATS:
    plt.savefig(f'{PATH}/{LLM}/{CASE_FOLDER}/resulting_plan.{format_}', bbox_inches='tight', dpi=300)
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                                  Final Logs                                  #
# ---------------------------------------------------------------------------- #


# ------------------------------ Numero di Task ------------------------------ #
N_TASKS = len(task_intervals)

# ------------------------------- Max Duration ------------------------------- #
for mission_id_, mission_des_ in MISSIONS.items():
    for task_id_, task_value_ in mission_des_.items():
        var_sol = solution.get_var_solution(name=task_intervals[task_id_]) 
        task_duration = var_sol.get_length()
        MAX_DURATION = MAX_DURATION if MAX_DURATION >= task_duration else task_duration

# --------------------------- Normalization Factor --------------------------- #
T_MAX = N_TASKS*MAX_DURATION

# ----------------------------------- Data ----------------------------------- #
results = {}
results["solve_time"] = solution.get_solve_time()
results["llm_time"] = LLM_TIME
results["n_tokens"] = OUT_TOKENS
results["feasibility"] = 1
results["makespan"] = solution.get_value(makespan)
results["cost_norm"] = solution.get_value(makespan)/T_MAX
results["solve_status"] = solution.get_solve_status()      # Feasible, Optimal, Infeasible, ...
results["has_solution"] = solution.is_solution()
results["is_optimal"] = solution.is_solution_optimal()
results["objective_value"] = solution.get_objective_value()
results["objective_bound"] = solution.get_objective_bound()
results["objective_gap"] = solution.get_objective_gap()
results["stop_cause"] = solution.get_stop_cause()
results["search_status"] = solution.get_search_status()


# ----------------------------------- Save ----------------------------------- #
try:
    with open(f"{PATH}/{LLM}/{CASE_FOLDER}/{LLM}_outputs.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    data = []  # se il file non esiste, inizia con lista vuota
data.extend([results])

with open(f"{PATH}/{LLM}/{CASE_FOLDER}/{LLM}_outputs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
# ---------------------------------------------------------------------------- #