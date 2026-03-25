#!/usr/bin/env python3.8

# ---------------------------------------------------------------------------- #
#                                    MODULES                                   #
# ---------------------------------------------------------------------------- #

# ---------------------------- ROS Client Library ---------------------------- #
import rospy
# ---------------------------------------------------------------------------- #

# --------------------------------- Messages --------------------------------- #
from std_msgs.msg import Empty
from std_srvs.srv import Trigger, TriggerRequest, TriggerResponse
from geometry_msgs.msg import Point
# ---------------------------------------------------------------------------- #

# ------------------------------ Custom Messages ----------------------------- #
from hr_task_allocation.msg import Step, Plan
# ---------------------------------------------------------------------------- #

# ---------------------------------- System ---------------------------------- #
import sys
# ---------------------------------------------------------------------------- #

# ----------------------------------- Time ----------------------------------- #
import time as timer
# ---------------------------------------------------------------------------- #

# ----------------------------------- Math ----------------------------------- #
import math
# ---------------------------------------------------------------------------- #

# ----------------------------------- Numpy ---------------------------------- #
import numpy as np
# ---------------------------------------------------------------------------- #

# ---------------------------------- Product --------------------------------- #
from itertools import product
# ---------------------------------------------------------------------------- #

# ---------------------------------- Random ---------------------------------- #
import random
# ---------------------------------------------------------------------------- #

# ----------------------------------- Path ----------------------------------- #
from pathlib import Path
# ---------------------------------------------------------------------------- #

# --------------------------------- Warnings --------------------------------- #
import warnings
# ---------------------------------------------------------------------------- #

# ----------------------------------- CPLEX ---------------------------------- #
from docplex.cp.model import *
import docplex.cp.utils_visu as visu
# ---------------------------------------------------------------------------- #

# --------------------------------- Date Time -------------------------------- #
import datetime
# ---------------------------------------------------------------------------- #

# ----------------------------------- Plot ----------------------------------- #
import matplotlib as mpl
mpl.rcParams.update(mpl.rcParamsDefault)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator
from pylab import rcParams 
# ---------------------------------------------------------------------------- #

# ---------------------------------- Pprint ---------------------------------- #
import pprint
# ---------------------------------------------------------------------------- #

# --------------------------------- Colorsys --------------------------------- #
import colorsys
# ---------------------------------------------------------------------------- #

# ---------------------------------- Tkinter --------------------------------- #
import tkinter as tk
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                                OptimierEngine                                #
# ---------------------------------------------------------------------------- #
class OptimizerEngine:
    
    # ---------------------------------------------------------------------------- #
    #                                  Constructor                                 #
    # ---------------------------------------------------------------------------- #
    def __init__(self):
        # ----------------------------------- Init ----------------------------------- #
        self.init_control_variables()
        self.init_problem_description()
        self.init_batch_strategy()
        self.init_cp_solver()
        # ---------------------------------------------------------------------------- #
        
        # ------------------------------------ ROS ----------------------------------- #
        self.init_ros_publishers()
        self.init_ros_subscribers()
        self.init_ros_services()
        # ---------------------------------------------------------------------------- #
        
        # ----------------------------------- Solve ---------------------------------- #
        self.solve()
        # ---------------------------------------------------------------------------- #
        
        # ---------------------------------- Timers ---------------------------------- #
        
        # ---------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------- #
    
    # ---------------------------------------------------------------------------- #
    #                                 Init Methods                                 #
    # ---------------------------------------------------------------------------- #
    def init_ros_publishers(self):
        self.plan_publisher = rospy.Publisher(f'~{rospy.get_name()}/generated_plan',Plan,queue_size=10)
    
    def init_ros_subscribers(self):
        pass
    
    def init_ros_services(self):
        self.reset_trigger_srv = rospy.Service(f'~{rospy.get_name()}/reset_model',Trigger,self.reset_trigger_srv_CB)
        self.solving_trigger_srv = rospy.Service(f'~{rospy.get_name()}/solve_problem',Trigger,self.solving_trigger_srv_CB)
        self.show_solution_srv = rospy.Service(f'~{rospy.get_name()}/show_solution',Trigger,self.show_solution_srv_CB)
    
    def init_problem_description(self):
        # ----------------------------------- Time ----------------------------------- #
        self.SOLVE_TIME = 0.0
        # ---------------------------------------------------------------------------- #

        # ----------------------------------- Scale ---------------------------------- #
        self.SCALE_FACTOR = 1
        # ---------------------------------------------------------------------------- #

        # ----------------------------------- Path ----------------------------------- #
        self.PATH = Path(__file__).resolve().parent.parent
        # ---------------------------------------------------------------------------- #

        # ------------------------------------ Box ----------------------------------- #
        self.BOXES = None
        FILENAME = "boxes.json"

        with open(f"{self.PATH}/config/json_files/{FILENAME}","r",encoding="utf-8") as file:
            self.BOXES = json.load(file)
        # ---------------------------------------------------------------------------- #

        # ----------------------------------- Grid ----------------------------------- #
        self.GRID = None
        FILENAME = "grid.json"

        with open(f"{self.PATH}/config/json_files/{FILENAME}","r",encoding="utf-8") as file:
            self.GRID = json.load(file)[0]
        # ---------------------------------------------------------------------------- #

        # ---------------------------- Objects: Read Table --------------------------- #
        ACQUIRED_DATA = None
        FILENAME = "objects.json"

        with open(f"{self.PATH}/config/json_files/{FILENAME}","r",encoding="utf-8") as file:
            ACQUIRED_DATA = json.load(file)
        # ---------------------------------------------------------------------------- #

        # ----------------------- Objects: Build Data Structure ---------------------- #
        self.OBJECTS = []
        self.OBJECTS_NAME = []
        self.WEIGHT_MIN = INFINITY
        self.ALPHA = 0.01

        for item_ in ACQUIRED_DATA:
            # -------------------------------- Description ------------------------------- #
            self.OBJECTS.append({"name": item_["id"], "type": item_["type"], "color": item_["color"], "coords": item_["position"], "weight": item_["weight"]})
            # ---------------------------------------------------------------------------- #
            
            # ----------------------------------- Name ----------------------------------- #
            self.OBJECTS_NAME.append(item_["id"])
            # ---------------------------------------------------------------------------- #
            
            # -------------------------------- Weight Min -------------------------------- #
            if self.WEIGHT_MIN > item_["weight"]:
                self.WEIGHT_MIN = item_["weight"]
            # ---------------------------------------------------------------------------- #    
        # ---------------------------------------------------------------------------- #

        # ---------------------------- Agents: Read Table ---------------------------- #
        ACQUIRED_DATA = None
        FILENAME = "agents.json"

        with open(f"{self.PATH}/config/json_files/{FILENAME}","r",encoding="utf-8") as file:
            ACQUIRED_DATA = json.load(file)
        # ---------------------------------------------------------------------------- #

        # ----------------------- Agents: Build Data Structure ----------------------- #
        self.AGENTS = []
        self.AGENTS_NAME = []
        self.AGENTS_AVAILABILITY = {}
        self.NULL_VEL = 10e-7
        self.WORKLOAD = {"robot": 1, "human": 1}
        self.THRESHOLD = 0.05
        self.FIX_VELOCITIES = False

        for item_ in ACQUIRED_DATA:
            # ------------------------------ Workspace Size ------------------------------ #
            if item_["workspace"] is not None:
                workspace = item_["workspace"]
            else:
                workspace = INT_MAX
            # ---------------------------------------------------------------------------- #
                
            # -------------------------------- Description ------------------------------- #
            self.AGENTS.append({"name": item_["id"], "type": item_["type"], "vel": {"min": item_["min_vel"]/self.SCALE_FACTOR, "max": item_["max_vel"]/self.SCALE_FACTOR}, "coords": item_["position"], "actions": item_["actions"],"workspace": workspace, "durations": {"pick": item_["pick"]*self.SCALE_FACTOR, "place": item_["place"]*self.SCALE_FACTOR, "extra": item_["extra"]*self.SCALE_FACTOR}})
            # ---------------------------------------------------------------------------- #
            
            # ----------------------------------- Name ----------------------------------- #
            self.AGENTS_NAME.append(item_["id"])
            # ---------------------------------------------------------------------------- #
            
            # ------------------------------- Availability ------------------------------- #
            self.AGENTS_AVAILABILITY[item_["id"]] = 0
            # ---------------------------------------------------------------------------- #
        # ---------------------------------------------------------------------------- #

        # ------------------------------ Task: Read Plan ----------------------------- #
        self.PLAN = None
        FILENAME = f"plan.json"

        with open(f"{self.PATH}/config/json_files/{FILENAME}","r",encoding="utf-8") as file:
            self.PLAN = json.load(file)
        # ---------------------------------------------------------------------------- #

        # --------------------------------- Refining --------------------------------- #
        if "box" in self.PLAN[0].keys():
            for action_id_ in range(len(self.PLAN)):
                # -------------------------------- Coordinates ------------------------------- #
                box_description_ = self.get_box_description(self.PLAN[action_id_]["box"])
                self.PLAN[action_id_]["desiredPosition"] = box_description_["position"]
                # ---------------------------------------------------------------------------- #
        # ---------------------------------------------------------------------------- #

        # ----------------------------- Task: Format Plan ---------------------------- #
        self.TASKS = [{"name": "letter", "description": []}]
        self.N_SUBTASKS = 0

        for subtask_ in self.PLAN:
            # ----------------------------- Object and Action ---------------------------- #
            if subtask_["actionName"] == "PickAndPlace":
                action_type_ = "PaP"
                object_type_ = subtask_["objectShape"]
            elif subtask_["actionName"] == "CloseBox":
                action_type_ = "CloseBox"
                object_type_ = "closureLid"
            elif subtask_["actionName"] == "OpenBox":
                action_type_ = "OpenBox"
                object_type_ = "openingLid"
            # ---------------------------------------------------------------------------- #

            # ---------------------------------- Append ---------------------------------- #
            self.TASKS[0]["description"].append({
                "object_type": object_type_, "object_color": subtask_["objectColor"], "action_type": action_type_, "action_order": subtask_["actionOrder"], "coords": subtask_["desiredPosition"]
            })
            # ---------------------------------------------------------------------------- #
        
            # ---------------------------------------------------------------------------- #
            
        self.N_TASKS = len(self.TASKS)
        self.N_SUBTASKS = len(self.TASKS[0]["description"])
        # ---------------------------------------------------------------------------- #

        # ---------------------------- Task: Grid 2 World ---------------------------- #
        for task_ in range(self.N_TASKS):
            self.N_SUBTASKS = len(self.TASKS[task_]['description'])
            for subtask_ in range(self.N_SUBTASKS):
                
                # ----------------------------- Position Analysis ---------------------------- #
                if isinstance(self.TASKS[task_]['description'][subtask_]["coords"],dict):
                    start_position = self.TASKS[task_]['description'][subtask_]["coords"]["start"]
                    end_position = self.TASKS[task_]['description'][subtask_]["coords"]["end"]
                    
                    if start_position != end_position:
                        if start_position[0] == end_position[0]: # Il blocco si estende lungo una riga
                            self.TASKS[task_]['description'][subtask_]["coords"] = [start_position[0],end_position[1] - math.trunc((abs(end_position[1] - start_position[1]) + 1)/2)]
                        elif start_position[1] == end_position[1]: # Il blocco si estende lungo una colonna
                            self.TASKS[task_]['description'][subtask_]["coords"] = [end_position[0] - math.trunc((abs(end_position[0] - start_position[0]) + 1)/2),start_position[1]]
                    else:
                        self.TASKS[task_]['description'][subtask_]["coords"] = start_position
                # ---------------------------------------------------------------------------- #
                
                # -------------------------------- Conversion -------------------------------- #
                self.TASKS[task_]['description'][subtask_]["grid_coords"] = self.TASKS[task_]['description'][subtask_]["coords"]
                self.TASKS[task_]['description'][subtask_]["coords"] = self.grid_2_world(self.GRID,self.TASKS[task_]['description'][subtask_]["coords"])
                # ---------------------------------------------------------------------------- #
        # ---------------------------------------------------------------------------- #

        # ------------------------- Normalization Parameters ------------------------- #
        self.V_MIN_HUMANS = INT_MAX # 1 cm/s
        self.V_MIN_ROBOTS = INT_MAX # 1 cm/s
        self.V_MAX_HUMANS = INT_MIN
        self.V_MAX_ROBOTS = INT_MIN
        for agent_ in self.AGENTS:
            if agent_["type"] == "human":
                self.V_MIN_HUMANS = min(agent_["vel"]["min"],self.V_MIN_HUMANS)
                self.V_MAX_HUMANS = max(agent_["vel"]["max"],self.V_MAX_HUMANS)
            elif agent_["type"] == "robot":
                self.V_MIN_ROBOTS = min(agent_["vel"]["min"],self.V_MIN_ROBOTS)
                self.V_MAX_ROBOTS = max(agent_["vel"]["max"],self.V_MAX_ROBOTS)
            
        self.PICK_MAX = 0
        for agent_ in self.AGENTS:
            self.PICK_MAX = max(agent_["durations"]["pick"],self.PICK_MAX)

        self.PLACE_MAX = 0
        for agent_ in self.AGENTS:
            self.PLACE_MAX = max(agent_["durations"]["place"],self.PLACE_MAX)

        self.EXTRA_MAX = 0
        for agent_ in self.AGENTS:
            self.EXTRA_MAX = max(agent_["durations"]["extra"],self.EXTRA_MAX)
            
        self.OBJ_AGT_DISTANCES = []
        for agent_ in self.AGENTS:
            for object_ in self.OBJECTS:
                self.OBJ_AGT_DISTANCES.append(self.euclidean_distance(object_["coords"],agent_["coords"]))

        self.CUM_DISTANCES = []    
        self.WEIGHTED_DISTANCES = [] 
        for agent_id_, agent_des_ in enumerate(self.AGENTS):
            for object_id_, object_des_ in enumerate(self.OBJECTS):
                obj_agt_distance_ = self.OBJ_AGT_DISTANCES[object_id_ + agent_id_*len(self.OBJECTS)]
                for row_ in range(1,self.GRID["rows"] + 1):
                    for col_ in range(1,self.GRID["cols"] + 1):
                        obj_cell_distance_ = self.euclidean_distance(object_des_["coords"],self.grid_2_world(self.GRID,[row_,col_]))
                        self.CUM_DISTANCES.append(obj_agt_distance_ + obj_cell_distance_)
                        self.WEIGHTED_DISTANCES.append(object_des_["weight"]*obj_agt_distance_ + object_des_["weight"]*obj_cell_distance_)

        self.CUM_DISTANCES = sorted(self.CUM_DISTANCES,reverse=True)
        self.WEIGHTED_DISTANCES = sorted(self.WEIGHTED_DISTANCES,reverse=True)
        # ---------------------------------------------------------------------------- #
        
        # ----------------------------- Objective Weights ---------------------------- #
        self.MAKESPAN_WEIGHT = 10 # 10 - Letter
        self.WORKLOAD_WEIGHT = 7 # 4 - Letter
        self.ENERGY_WEIGHT = 1 # 1 - Letter
        # ---------------------------------------------------------------------------- #

        # ---------------------------------------------------------------------------- #

    def init_batch_strategy(self):
        # -------------------------------- Parameters -------------------------------- #
        self.CUTOFF_SIZE = 4 # Sorting
        self.CUTOFF = self.CUTOFF_SIZE
        self.NA_OBJS = []
        # ---------------------------------------------------------------------------- #

        # ------------------------------ Data Structures ----------------------------- #
        self.TASKS_STATUS = {}

        for task_ in range(self.N_TASKS):
            self.TASKS_STATUS[task_] = {"name": self.TASKS[task_]["name"], "subtasks": {}}
            for subtask_id_, subtask_des_ in enumerate(self.TASKS[task_]["description"]):
                if len(self.TASKS_STATUS[task_]["subtasks"]) < self.CUTOFF:
                    self.TASKS_STATUS[task_]["subtasks"][subtask_id_] = {"locked": False, "agent": "", "object": "", "start": 0, "end": 0, "vel": 0.0, "vel_max": 0.0}
        # ---------------------------------------------------------------------------- #

    def init_cp_solver(self):
        # -------------------------------- Empty Model ------------------------------- #
        self.model = CpoModel("optimizer")
        # ---------------------------------------------------------------------------- #
        
        # ----------------------------- Solver Parameters ---------------------------- #
        self.params = CpoParameters()
        # self.params.SearchType = "Restart"
        self.params.TimeLimit = 30
        self.params.RandomSeed = 123
        self.params.Workers = 20
        self.params.FailureDirectedSearch = "On"
        self.params.FailureDirectedSearchEmphasis = 10
        self.params.FailureDirectedSearchMaxMemory = 1000000000
        self.params.RestartFailLimit = 1000
        self.params.RestartGrowthFactor = 1.3
        # self.params.OptimalityTolerance = 1e-04
        # self.params.RelativeOptimalityTolerance = 0.02
        # ---------------------------------------------------------------------------- #
        
    def init_decision_variables(self):
        # --------------------------------- Makespan --------------------------------- #
        self.makespan = integer_var(min=0,name="makespan")
        # ---------------------------------------------------------------------------- #

        # --------------------------------- Workload --------------------------------- #
        self.workload_humans = float_var(min=0,name="workload_humans")
        # ---------------------------------------------------------------------------- #

        # ------------------------------- Robots Energy ------------------------------ #
        self.robots_energy = float_var(min=0,name="robots_energy")
        # ---------------------------------------------------------------------------- #

        # ------------------------------ Step Intervals ------------------------------ #
        self.tasks_intervals = {}
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    self.tasks_intervals[(self.TASKS[task_]['name'],subtask_id_)] = interval_var(start=(0,INTERVAL_MAX),end=(0,INTERVAL_MAX),name=f"{self.TASKS[task_]['name']}_subtask#{subtask_id_}_interval_var")
                else:
                    self.tasks_intervals[(self.TASKS[task_]['name'],subtask_id_)] = interval_var(start=subtask_des_["start"],end=subtask_des_["end"],name=f"{self.TASKS[task_]['name']}_subtask#{subtask_id_}_interval_var")
        # ---------------------------------------------------------------------------- #

        # ----------------------------- Object Selectors ----------------------------- #
        self.objects_selectors = {}
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS[task_]['name']
            task_des_ = self.TASKS[task_]['description']
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    for object_ in self.OBJECTS:
                        if (object_['type'] == task_des_[subtask_id_]['object_type']) & (object_['color'] == task_des_[subtask_id_]['object_color']) & (object_['name'] not in self.NA_OBJS):
                            self.objects_selectors[(task_name_,subtask_id_,object_['name'])] = binary_var(name=f"{task_name_}_subtask#{subtask_id_}_{object_['name']}_binary_var")
                else:
                    self.objects_selectors[(task_name_,subtask_id_,subtask_des_["object"])] = binary_var(name=f"{task_name_}_subtask#{subtask_id_}_{subtask_des_['object']}_binary_var")
        # ---------------------------------------------------------------------------- #

        # ------------------------------ Agent Intervals ----------------------------- #
        self.agents_intervals = {}
        self.robots_velocities = {}

        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    for agent_ in self.AGENTS:
                        # ---------------------------------- Actions --------------------------------- #
                        actions_list_ = []
                        
                        if isinstance(agent_["actions"],list):
                            actions_list_.extend(agent_["actions"])
                        elif isinstance(agent_["actions"],str):
                            actions_list_.append(agent_["actions"])
                        # ---------------------------------------------------------------------------- #
                        
                        # ----------------------------------- Check ---------------------------------- #
                        if self.TASKS[task_]["description"][subtask_id_]["action_type"] in actions_list_:
                            # -------------------------------- Allocation -------------------------------- #
                            self.agents_intervals[(agent_["name"],task_name_,subtask_id_)] = interval_var(start=(self.AGENTS_AVAILABILITY[agent_['name']],INTERVAL_MAX),optional=True,name=f"{agent_['name']}_{task_name_}_subtask#{subtask_id_}_interval_var")
                            # ---------------------------------------------------------------------------- #
                            
                            # --------------------------------- Velocity --------------------------------- #
                            if agent_["type"] == "robot":
                                self.robots_velocities[(agent_["name"],task_name_,subtask_id_)] = float_var(min=self.NULL_VEL,name=f"{agent_['name']}_{task_name_}_subtask#{subtask_id_}_float_vel_var")
                            # ---------------------------------------------------------------------------- #
                        # ---------------------------------------------------------------------------- #
                else:
                    # -------------------------------- Allocation -------------------------------- #
                    self.agents_intervals[(subtask_des_["agent"],task_name_,subtask_id_)] = interval_var(start=subtask_des_["start"],end=subtask_des_["end"],name=f"{subtask_des_['agent']}_{task_name_}_subtask#{subtask_id_}_interval_var")
                    # ---------------------------------------------------------------------------- #
                    
                    # --------------------------------- Velocity --------------------------------- #
                    if self.get_agent_type(subtask_des_["agent"]) == "robot":
                        velocity_ = subtask_des_["vel"]
                        self.robots_velocities[(subtask_des_["agent"],task_name_,subtask_id_)] = float_var(min=velocity_,max=velocity_,name=f"{subtask_des_['agent']}_{task_name_}_subtask#{subtask_id_}_float_vel_var")
                    # ---------------------------------------------------------------------------- #         
        # ---------------------------------------------------------------------------- #

    def init_constraints(self):
        # --------------------------------- Makespan --------------------------------- #
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            self.model.add(self.makespan == max_of([end_of(self.tasks_intervals[(task_name_,subtask_id_)]) for subtask_id_, subtask_des_ in SUBTASKS.items()]))
        # ---------------------------------------------------------------------------- #

        # ------------------------- Objects Allocation - PT1 ------------------------- #
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    object_prefix_ = self.TASKS[task_]["description"][subtask_id_]["object_color"] + '_' + self.TASKS[task_]["description"][subtask_id_]["object_type"]
                    FILTERED_LIST = [item for item in self.OBJECTS_NAME if (item.find(object_prefix_) != -1) & (item not in self.NA_OBJS)]
                    selectors = [self.objects_selectors[(task_name_,subtask_id_,object_)] for object_ in FILTERED_LIST]
                    self.model.add(sum_of(selectors) == 1)
                else:
                    self.model.add(self.objects_selectors[(task_name_,subtask_id_,subtask_des_["object"])]  == 1)
        # ---------------------------------------------------------------------------- #

        # ------------------------- Objects Allocation - PT2 ------------------------- #
        for object_ in self.OBJECTS:
            selectors = [self.objects_selectors[key_object_] for key_object_ in self.objects_selectors.keys() if object_["name"] == key_object_[2]]
            self.model.add(sum_of(selectors) <= 1)
        # ---------------------------------------------------------------------------- #

        # ----------------------------- Agents Allocation ---------------------------- #
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    agents_list_ = [agent_interval_ for agent_key_, agent_interval_ in self.agents_intervals.items() if (agent_key_[1] == task_name_) & (agent_key_[2] == subtask_id_)]
                    self.model.add(alternative(self.tasks_intervals[(task_name_,subtask_id_)],agents_list_))
                else:
                    self.model.add(start_of(self.tasks_intervals[(task_name_,subtask_id_)]) == start_of(self.agents_intervals[(subtask_des_["agent"],task_name_,subtask_id_)]))
                    self.model.add(end_of(self.tasks_intervals[(task_name_,subtask_id_)]) == end_of(self.agents_intervals[(subtask_des_["agent"],task_name_,subtask_id_)]))
        # ---------------------------------------------------------------------------- #

        # -------------------------------- No-Overlap -------------------------------- # 
        for agent in self.AGENTS:
            selectors = []
            for key_ in self.agents_intervals.keys():
                if agent['name'] == key_[0]:
                    selectors.append(self.agents_intervals[key_])
            
            if selectors:     
                self.model.add(no_overlap(selectors))
        # ---------------------------------------------------------------------------- #

        # -------------------------- Velocities and Duration ------------------------- #
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    for key_agent_ in self.agents_intervals.keys():
                        if (task_name_ == key_agent_[1]) & (subtask_id_ == key_agent_[2]):
                            # -------------------------------- Velocities -------------------------------- #
                            if self.get_agent_type(key_agent_[0]) == "robot":
                                self.model.add(if_then(presence_of(self.agents_intervals[key_agent_]) == False,self.robots_velocities[(key_agent_)] == self.NULL_VEL))
                                
                                velocity_min = self.get_agent_velocity(key_agent_[0],0)
                                velocity_max = self.get_agent_velocity(key_agent_[0],1)
                                    
                                self.model.add(if_then(presence_of(self.agents_intervals[key_agent_]) == True,self.robots_velocities[(key_agent_)] >= velocity_min))
                                self.model.add(if_then(presence_of(self.agents_intervals[key_agent_]) == True,self.robots_velocities[(key_agent_)] <= velocity_max))
                            # ---------------------------------------------------------------------------- #
                            
                            # --------------------------------- Duration --------------------------------- #
                            for key_object_ in self.objects_selectors.keys():
                                if (task_name_ == key_object_[0]) & (subtask_id_ == key_object_[1]):
                                    condition_ = sum_of([presence_of(self.agents_intervals[key_agent_]) == True,self.objects_selectors[(key_object_)] == 1]) == 2
                                    
                                    distance_ = self.euclidean_distance(self.get_agent_position(key_agent_[0]),self.get_object_position(key_object_[2]))
                                    distance_ = distance_ + self.euclidean_distance(self.get_object_position(key_object_[2]),self.TASKS[task_]["description"][subtask_id_]["coords"])
                                    
                                    durations_ = self.get_agent_durations(key_agent_[0])
                                    
                                    if self.get_agent_type(key_agent_[0]) == "robot":
                                        # self.model.add(if_then(condition_,length_of(self.tasks_intervals[(task_name_,subtask_id_)]) >= durations_['pick'] + durations_['place'] + durations_['extra'] + (distance_/self.robots_velocities[key_agent_])))
                                        self.model.add(if_then(condition_,length_of(self.tasks_intervals[(task_name_,subtask_id_)]) >= 24 + 24 + 12 + (distance_/self.robots_velocities[key_agent_])))
                                    else:
                                        if self.FIX_VELOCITIES == True:
                                            velocity_ = self.get_agent_velocity(key_agent_[0],1)
                                        else:
                                            velocity_ = self.get_agent_velocity(key_agent_[0],1)/(1 + self.ALPHA*(self.get_object_weight(key_object_[2]) - self.WEIGHT_MIN))
                                        self.model.add(if_then(condition_,length_of(self.tasks_intervals[(task_name_,subtask_id_)]) >= durations_['pick'] + durations_['place'] + durations_['extra'] + (distance_/velocity_)))
                            # ---------------------------------------------------------------------------- #
                elif self.get_agent_type(subtask_des_["agent"]) == "robot":
                    self.model.add(self.robots_velocities[(subtask_des_["agent"],task_name_,subtask_id_)] == subtask_des_["vel"])
        # ---------------------------------------------------------------------------- #

        # ------------------------------ Execution Order ----------------------------- #
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            for subtask_i_ in SUBTASKS.keys():
                for subtask_j_ in SUBTASKS.keys():
                    action_i_ = self.TASKS[task_]["description"][subtask_i_]["action_order"]
                    action_j_ = self.TASKS[task_]["description"][subtask_j_]["action_order"]
                    if action_i_ < action_j_:
                        self.model.add(end_before_start(self.tasks_intervals[(task_name_,subtask_i_)],self.tasks_intervals[(task_name_,subtask_j_)]))
        # ---------------------------------------------------------------------------- #
    
    def init_objective_function(self):
        # ---------------------------------------------------------------------------- #
        #                             Objective - Makespan                             #
        # ---------------------------------------------------------------------------- #

        # --------------------------------- REQ_OBJS --------------------------------- #
        self.REQ_OBJS = 0
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            self.REQ_OBJS = self.REQ_OBJS + len(SUBTASKS)
        # ---------------------------------------------------------------------------- #

        # ----------------------------------- T_MAX ---------------------------------- #
        self.T_MAX = self.REQ_OBJS*(self.PICK_MAX + self.PLACE_MAX + self.EXTRA_MAX + float(np.max(self.CUM_DISTANCES))/min(self.V_MIN_HUMANS,self.V_MIN_ROBOTS))
        # ---------------------------------------------------------------------------- #

        # ------------------------------- Normalization ------------------------------ #
        makespan_ = self.makespan/self.T_MAX
        # ---------------------------------------------------------------------------- #

        # ---------------------------------------------------------------------------- #

        # ---------------------------------------------------------------------------- #
        #                             Objective - Workload                             #
        # ---------------------------------------------------------------------------- #

        # ------------------------------- WORKLOAD_MAX ------------------------------- #
        self.WORKLOAD_MAX = float(np.max(self.WEIGHTED_DISTANCES))
        # ---------------------------------------------------------------------------- #

        # --------------------------------- Workload --------------------------------- #
        workload_humans_ = 0
        
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    for key_agent_ in self.agents_intervals.keys():
                        if (self.get_agent_type(key_agent_[0]) == "human") & (task_name_ == key_agent_[1]) & (subtask_id_ == key_agent_[2]):
                            for key_object_ in self.objects_selectors.keys():
                                if (task_name_ == key_object_[0]) & (subtask_id_ == key_object_[1]):
                                    condition_ = sum_of([presence_of(self.agents_intervals[key_agent_]) == True, self.objects_selectors[key_object_] == 1]) == 2
                                    
                                    distance_ = self.euclidean_distance(self.get_agent_position(key_agent_[0]),self.get_object_position(key_object_[2]))
                                    distance_ = distance_ + self.euclidean_distance(self.get_object_position(key_object_[2]),self.TASKS[task_]["description"][subtask_id_]["coords"])
                                    
                                    object_weight_ = self.get_object_weight(key_object_[2])
                                    
                                    workload_humans_ = workload_humans_ + condition_*distance_*object_weight_
                elif self.get_agent_type(subtask_des_["agent"]) == "human":
                    agent_ = subtask_des_['agent']
                    object_ = subtask_des_['object']
                    
                    distance_ = self.euclidean_distance(self.get_agent_position(agent_),self.get_object_position(object_))
                    distance_ = distance_ + self.euclidean_distance(self.get_object_position(object_),self.TASKS[task_]["description"][subtask_id_]["coords"])
                    
                    object_weight_ = self.get_object_weight(object_)
                            
                    workload_humans_ = workload_humans_ + distance_*object_weight_
                    
        self.model.add(self.workload_humans == workload_humans_)
        # ---------------------------------------------------------------------------- #

        # ------------------------------- Normalization ------------------------------ #
        workload_ = self.workload_humans/self.WORKLOAD_MAX
        # ---------------------------------------------------------------------------- #

        # ---------------------------------------------------------------------------- #
        
        # ---------------------------------------------------------------------------- #
        #                           Objective - Robots Energy                          #
        # ---------------------------------------------------------------------------- #
        
        # -------------------------------- ENERGY MAX -------------------------------- #
        self.ENERGY_MAX = self.V_MAX_ROBOTS*float(np.max(self.CUM_DISTANCES))
        # ---------------------------------------------------------------------------- #
        
        # ------------------------------- Robots Energy ------------------------------ #
        robots_energy_ = 0
        
        for task_ in range(self.N_TASKS):
            SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
            task_name_ = self.TASKS_STATUS[task_]["name"]
            for subtask_id_, subtask_des_ in SUBTASKS.items():
                if subtask_des_["locked"] == False:
                    for key_agent_ in self.agents_intervals.keys():
                        if (self.get_agent_type(key_agent_[0]) == "robot") & (task_name_ == key_agent_[1]) & (subtask_id_ == key_agent_[2]):
                            for key_object_ in self.objects_selectors.keys():
                                if (task_name_ == key_object_[0]) & (subtask_id_ == key_object_[1]):
                                    condition_ = sum_of([presence_of(self.agents_intervals[key_agent_]) == True, self.objects_selectors[key_object_] == 1]) == 2
                                    
                                    distance_ = self.euclidean_distance(self.get_agent_position(key_agent_[0]),self.get_object_position(key_object_[2]))
                                    distance_ = distance_ + self.euclidean_distance(self.get_object_position(key_object_[2]),self.TASKS[task_]["description"][subtask_id_]["coords"])
                                    
                                    robots_energy_ = robots_energy_ + condition_*self.robots_velocities[(key_agent_)]*distance_
                elif self.get_agent_type(subtask_des_['agent']) == "robot":
                    agent_ = subtask_des_['agent']
                    object_ = subtask_des_['object']
                    velocity_ = subtask_des_['vel']
                    
                    distance_ = self.euclidean_distance(self.get_agent_position(agent_),self.get_object_position(object_))
                    distance_ = distance_ + self.euclidean_distance(self.get_object_position(object_),self.TASKS[task_]["description"][subtask_id_]["coords"])
                    
                    robots_energy_ = robots_energy_ + velocity_*distance_
                
        self.model.add(self.robots_energy == robots_energy_)
        # ---------------------------------------------------------------------------- #
        
        # ------------------------------- Normalization ------------------------------ #
        energy_ = self.robots_energy/self.ENERGY_MAX
        # ---------------------------------------------------------------------------- #
        
        # ---------------------------------------------------------------------------- #

        # ---------------------------------------------------------------------------- #
        #                             Objective - Function                             #
        # ---------------------------------------------------------------------------- #
        self.model.add(minimize(self.MAKESPAN_WEIGHT*makespan_ + self.ENERGY_WEIGHT*energy_ + self.WORKLOAD_WEIGHT*workload_))
        # ---------------------------------------------------------------------------- #
    
    def init_control_variables(self):
        # ------------------------------ Loop Condition ------------------------------ #
        self.END = False
        # ---------------------------------------------------------------------------- #
        
        # ----------------------------- Solution Summary ----------------------------- #
        self.VISU_SOLUTION = {}
        self.SOLUTION_SUMMARY = Plan()
        # ---------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------- #
    
    # ---------------------------------------------------------------------------- #
    #                           ROS Subscribers Callbacks                          #
    # ---------------------------------------------------------------------------- #
    
    # ---------------------------------------------------------------------------- #
    
    # ---------------------------------------------------------------------------- #
    #                             ROS Service Callback                             #
    # ---------------------------------------------------------------------------- #
    def reset_trigger_srv_CB(self,req:TriggerRequest):
        # ----------------------------------- Reset ---------------------------------- #
        self.init_control_variables()
        self.init_problem_description()
        self.init_batch_strategy()
        self.init_cp_solver()
        # ---------------------------------------------------------------------------- #
        
        # --------------------------------- Response --------------------------------- #
        res = TriggerResponse()
        res.success = True
        res.message = 'Reset Performed!'
        return res
        # ---------------------------------------------------------------------------- #  
    
    def solving_trigger_srv_CB(self,req:TriggerRequest):
        # ----------------------------------- Solve ---------------------------------- #
        if self.raw_solution is None:
            self.solve()
        # ---------------------------------------------------------------------------- #
        
        # --------------------------------- Response --------------------------------- #
        res = TriggerResponse()
        res.success = True
        res.message = "Problem Solved!"
        return res
        # ---------------------------------------------------------------------------- #
    
    def show_solution_srv_CB(self,req:TriggerRequest):
        # ----------------------------- Responce Creation ---------------------------- #
        res = TriggerResponse()
        # ---------------------------------------------------------------------------- #
        
        # ----------------------------------- Check ---------------------------------- #
        if self.raw_solution is not None:
            # self.show_solution()
            res.success = True
        else:
            res.success = False
        # ---------------------------------------------------------------------------- #
        
        # ---------------------------------- Return ---------------------------------- #
        return res
        # ---------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------- #
    
    # ---------------------------------------------------------------------------- #
    #                                 Other Methods                                #
    # ---------------------------------------------------------------------------- #
    def solve(self):
        # ----------------------------------- Loop ----------------------------------- #
        while self.END == False:
            # ----------------------------------- Init ----------------------------------- #
            self.init_cp_solver()
            self.init_decision_variables()
            self.init_constraints()
            self.init_objective_function()
            # ---------------------------------------------------------------------------- #
            
            # ---------------------------------- Compute --------------------------------- #
            self.compute_solution()
            # ---------------------------------------------------------------------------- #
            
            # ---------------------------------- Update ---------------------------------- #
            self.update_status()
            # ---------------------------------------------------------------------------- #
            
            # ----------------------------------- Show ----------------------------------- #
            if self.END == True:
                self.show_solution()
            # ---------------------------------------------------------------------------- #
        # ---------------------------------------------------------------------------- #
         
    def compute_solution(self):
        # ----------------------------- Compute Solution ----------------------------- #
        self.raw_solution = self.model.solve(params=self.params)
        self.SOLVE_TIME = self.SOLVE_TIME + self.raw_solution.get_solve_time()
        print(f"Tempo interno CPLEX CP: {self.SOLVE_TIME:.4f} secondi")
        self.raw_solution.print_solution()
        # ---------------------------------------------------------------------------- #
        
    def update_status(self):
        # --------------------------- Tasks Status - Update -------------------------- #
        for task_ in range(self.N_TASKS):
            for key_agent_ in self.agents_intervals.keys():
                if self.raw_solution.get_var_solution(self.agents_intervals[key_agent_]).is_present():
                    subtask_status_ = self.raw_solution.get_var_solution(self.agents_intervals[key_agent_])
                    self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["locked"] = True
                    self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["agent"] = key_agent_[0]
                    self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["start"] = subtask_status_.get_start()
                    self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["end"] = subtask_status_.get_end()
                    
                    
                    object_prefix_ = self.TASKS[task_]["description"][key_agent_[2]]["object_color"] + '_' + self.TASKS[task_]["description"][key_agent_[2]]["object_type"]
                    FILTERED_LIST = [key_object_[2] for key_object_ in self.objects_selectors.keys() if (key_object_[0] == key_agent_[1]) & (key_object_[1] == key_agent_[2])]
                    for object_ in FILTERED_LIST:
                        if self.raw_solution.get_value(self.objects_selectors[(self.TASKS[task_]["name"],key_agent_[2],object_)]) == 1:
                            self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["object"] = object_
                            break
                        
                    if self.get_agent_type(key_agent_[0]) == "robot":
                        velocity_ = self.raw_solution.get_value(self.robots_velocities[key_agent_])
                        if is_tuple(velocity_):
                            self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["vel"] = float(0.5*(np.max(velocity_) + np.min(velocity_)))
                        else:
                            self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["vel"] = velocity_
                    else:
                        if self.FIX_VELOCITIES == True:
                            self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["vel"] = self.get_agent_velocity(key_agent_[0],1)
                        else:
                            self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["vel"] = self.get_agent_velocity(key_agent_[0],1)/(1 + self.ALPHA*(self.get_object_weight(self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["object"]) - self.WEIGHT_MIN))
                
                    self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["vel_max"] = self.get_agent_velocity(key_agent_[0],1)
                    
                    self.NA_OBJS.append(self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["object"])
                    
                    if self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["end"] > self.AGENTS_AVAILABILITY[key_agent_[0]]:
                        self.AGENTS_AVAILABILITY[key_agent_[0]] = self.TASKS_STATUS[task_]["subtasks"][key_agent_[2]]["end"]
        # ---------------------------------------------------------------------------- #
        
        # --------------------------- Tasks Status - Extend -------------------------- #
        if self.CUTOFF < self.N_SUBTASKS:

            # -------------------------------- New CUTOFF -------------------------------- #
            self.CUTOFF = min(self.CUTOFF+self.CUTOFF_SIZE,self.N_SUBTASKS)
            # ---------------------------------------------------------------------------- #

            # ---------------------------------- Extend ---------------------------------- #
            for task_ in range(self.N_TASKS):
                SUBTASKS_LIST = list(self.TASKS_STATUS[task_]["subtasks"].keys())
                for subtask_id_, subtask_des_ in enumerate(self.TASKS[task_]["description"]):
                    if (subtask_id_ not in SUBTASKS_LIST) & (len(self.TASKS_STATUS[task_]["subtasks"]) < self.CUTOFF):
                        self.TASKS_STATUS[task_]["subtasks"][subtask_id_] = {"locked": False, "agent": "", "object": "", "start": 0, "end": 0, "vel": 0.0, "vel_max": 0.0}
            # ---------------------------------------------------------------------------- #

        else:
            # -------------------------------- Update Flag ------------------------------- #
            self.END = True
            # ---------------------------------------------------------------------------- #
            
            # ------------------------------ Parse Solution ------------------------------ #
            self.VISU_SOLUTION = {}

            for task_ in range(self.N_TASKS):
                SUBTASKS = self.TASKS_STATUS[task_]["subtasks"]
                for subtask_id_, subtask_des_ in SUBTASKS.items():
                    if subtask_des_["locked"] == True:
                        # ---------------------------------- Extend ---------------------------------- #
                        if subtask_des_["agent"] not in self.VISU_SOLUTION.keys():
                            self.VISU_SOLUTION[subtask_des_["agent"]] = []
                        # ---------------------------------------------------------------------------- #
                        
                        # -------------------------------- Create Step ------------------------------- #
                        step_ = Step()
                        # ---------------------------------------------------------------------------- #
                        
                        # --------------------------------- Fill Step -------------------------------- #
                        step_.level = self.TASKS[0]["description"][subtask_id_]["action_order"]
                        
                        step_.action_id = self.TASKS[0]["description"][subtask_id_]["action_type"]
                        step_.agent_id = subtask_des_["agent"]
                        step_.object_id = subtask_des_["object"]
                        
                        pick_position_ = self.get_object_position(subtask_des_["object"])
                        step_.pick_position[0] = pick_position_[0]
                        step_.pick_position[1] = pick_position_[1]
                        
                        
                        place_position_ = self.TASKS[0]["description"][subtask_id_]["coords"]
                        step_.place_position_world[0] = place_position_[0]
                        step_.place_position_world[1] = place_position_[1]
                        
                        place_position_ = self.TASKS[0]["description"][subtask_id_]["grid_coords"]
                        step_.place_position_grid[0] = place_position_[0]
                        step_.place_position_grid[1] = place_position_[1]
                        
                        pick_movement_ = self.euclidean_distance(self.get_agent_position(subtask_des_["agent"]),self.get_object_position(subtask_des_["object"]))
                        place_movement_ = self.euclidean_distance(self.get_object_position(subtask_des_["object"]),self.TASKS[0]["description"][subtask_id_]["coords"])
                        
                        agent_durations_ = self.get_agent_durations(subtask_des_["agent"])
                        actual_duration_ = subtask_des_["end"] - subtask_des_["start"]
                        
                        if (pick_movement_ != 0) & (place_movement_ != 0):
                            actual_duration_ = actual_duration_ - agent_durations_['pick'] - agent_durations_['place'] - agent_durations_['extra']
                        elif (pick_movement_ != 0) & (place_movement_ == 0):
                            actual_duration_ = actual_duration_ - agent_durations_['pick'] - agent_durations_['extra']
                        elif (pick_movement_ == 0) & (place_movement_ != 0):
                            actual_duration_ = actual_duration_ - agent_durations_['place'] - agent_durations_['extra']
                            
                        step_.pick_duration = actual_duration_*(pick_movement_/(pick_movement_ + place_movement_))
                        step_.place_duration = actual_duration_*(place_movement_/(pick_movement_ + place_movement_))
                                                    
                        step_.step_start = subtask_des_["start"]
                        step_.step_end = subtask_des_["end"]
                        # ---------------------------------------------------------------------------- #
                        
                        # ---------------------------------- Append ---------------------------------- #
                        self.SOLUTION_SUMMARY.steps.append(step_)
                        # ---------------------------------------------------------------------------- #

                        # --------------------------------- Plot Data -------------------------------- #
                        self.VISU_SOLUTION[subtask_des_["agent"]].extend([[subtask_des_["start"],subtask_des_["end"],subtask_des_["object"],subtask_id_,self.TASKS[0]["description"][subtask_id_]["action_type"],self.TASKS[0]["description"][subtask_id_]["action_order"]]])
                        # ---------------------------------------------------------------------------- #
            # ---------------------------------------------------------------------------- #
            
            # ----------------------------- Publish Solution ----------------------------- #
            self.SOLUTION_SUMMARY.agents = self.AGENTS_NAME
            self.SOLUTION_SUMMARY.steps.sort(key=lambda x: x.step_start)
            self.plan_publisher.publish(self.SOLUTION_SUMMARY)                
            # ---------------------------------------------------------------------------- #
            
        # ---------------------------------------------------------------------------- #
    
    def show_solution(self):
        # ------------------------------- Plot Settings ------------------------------ #
        FIGSIZE_FULLSCREEN = self.get_screen_figsize()
        plt.rc('text', usetex=True)
        fig, ax = plt.subplots(figsize=FIGSIZE_FULLSCREEN)
        

        plt.tick_params(axis='x', which='major', labelsize=30)

        colors = plt.cm.Set3.colors
        crop_colors = {i: colors[i % len(colors)] for i in range(self.N_SUBTASKS)}
        bar_height = 0.8

        ax.set_yticks(list(range(len(self.AGENTS))))

        ax.set_xlabel('Time (s)',fontsize=30)
        ax.set_xlim(0,self.raw_solution.get_value(self.makespan))
        ax.xaxis.set_major_locator(MultipleLocator(100))
        ax.grid(True, axis='x', linestyle='--', alpha=0.5, zorder=0)

        ax.set_yticklabels([f"${agent}$" for agent in self.AGENTS_NAME],fontsize=40)
        
        color_list = {"red": "#ef233c", "green": "#6eeb83", "yellow": "#ffdb57", "blue": "#5fa8d3"}
        # ---------------------------------------------------------------------------- #
        
        # ----------------------------------- Plot ----------------------------------- #
        for agent_index_, agent_name_ in enumerate(self.AGENTS_NAME):
            if agent_name_ in self.VISU_SOLUTION.keys():
                for subtask_ in self.VISU_SOLUTION[agent_name_]:
                    
                    # -------------------------------- Parameters -------------------------------- #
                    action_type = subtask_[4]
                    object_type = self.get_object_type(subtask_[2])
                    object_color = self.get_object_color(subtask_[2])
                    object_id = subtask_[2][-1]
                    level_id = subtask_[5]
                    # ---------------------------------------------------------------------------- #
                    
                        
                    # bar = ax.barh(agent_index_, subtask_[1] - subtask_[0], left=subtask_[0], height=bar_height, color=crop_colors[subtask_[3]], edgecolor='black', linewidth=0.3, zorder=3)
                    bar = ax.barh(agent_index_, subtask_[1] - subtask_[0], left=subtask_[0], height=bar_height, color=color_list[object_color], edgecolor='black', linewidth=0.3, zorder=3)
                    
                    
                    # ax.text(subtask_[0] + (subtask_[1] - subtask_[0])/2, agent_index_, f'''${subtask_[3]+1}$:$\mathcal{{L}}_{level_id}$, {action_type}, {object_color}-{object_type}{object_id}''', va='center', ha='center', color='black', fontsize=7)
                    ax.text(subtask_[0] + (subtask_[1] - subtask_[0]) / 2.0, agent_index_, f'''${subtask_[3]+1}$:$\mathcal{{L}}_{level_id}$, {action_type}''', va='bottom', ha='center', color=self.get_contrasting_text_color(color_list[object_color]), fontsize=25)
                    
                    ax.text(subtask_[0] + (subtask_[1] - subtask_[0]) / 2.0, agent_index_, f'''{object_color[0].upper()}-{object_type[0].upper()}{object_id}''', va='top', ha='center', color=self.get_contrasting_text_color(color_list[object_color]), fontsize=25)
        # ---------------------------------------------------------------------------- #
        
        
        # ----------------------------------- Show ----------------------------------- #
        plt.tight_layout()
        plt.savefig(f'''{self.PATH}/figure_{datetime.datetime.now()}.svg''', format='svg', dpi=300)
        # plt.savefig(f'''{self.PATH}/figure_{datetime.datetime.now()}.png''', format='png', dpi=300)
        plt.show()
        # ---------------------------------------------------------------------------- #

    def get_screen_figsize(self,default=(30,4)):
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

    def get_contrasting_text_color(self,background_color): # --- Genera automaticamente il colore del testo (nero o bianco) in base al colore di sfondo della barra.
        # ---------------------------- Conversione in RGB ---------------------------- #
        r, g, b = mpl.colors.to_rgb(background_color)

        # -------------------------- Calcolo della luminanza ------------------------- #
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # ------------------------------ Set del Colore ------------------------------ #
        return "#111111" if luminance > 0.6 else "#f5f5f5"

    def pastel_colors(self,n, sat=0.35, val=0.95):
        return [colorsys.hsv_to_rgb(i / n, sat, val) for i in range(n)]

    # ---------------------------------------------------------------------------- #

    # ---------------------------------------------------------------------------- #
    #                                General Methos                                #
    # ---------------------------------------------------------------------------- #
    
    # ---------------------------- Function: Distance ---------------------------- #
    def euclidean_distance(self,p1:list,p2:list):
        # ---------------------------------- Compute --------------------------------- #
        distance = math.sqrt(pow(p2[0] - p1[0],2) + pow(p2[1] - p1[1],2))
        # ---------------------------------------------------------------------------- #

        return distance
    # ---------------------------------------------------------------------------- #

    # ---------------------------- Function: Distance ---------------------------- #
    def manhattan_distance(self,p1:list,p2:list):
        # ---------------------------------- Compute --------------------------------- #
        distance = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        # ---------------------------------------------------------------------------- #

        return distance
    # ---------------------------------------------------------------------------- #

    # ------------------------- Function: Agent Position ------------------------- #
    def get_agent_position(self,agent_name_):
        for agent_ in self.AGENTS:
            if agent_['name'] == agent_name_:
                return agent_['coords']
    # ---------------------------------------------------------------------------- #

    # ------------------------- Function: Agent Velocity ------------------------- #
    def get_agent_velocity(self,agent_name_:str,bound_:bool):
        for agent_ in self.AGENTS:
            if agent_['name'] == agent_name_:
                if bound_ == 0:
                    return agent_['vel']['min']
                else:
                    return agent_['vel']['max']
    # ---------------------------------------------------------------------------- #

    # --------------------------- Function: Agent Type --------------------------- #
    def get_agent_type(self,agent_name_):
        for agent_ in self.AGENTS:
            if agent_['name'] == agent_name_:
                return agent_['type']
    # ---------------------------------------------------------------------------- #

    # ------------------------- Function: Agent Durations ------------------------ #
    def get_agent_durations(self,agent_name_):
        for agent_ in self.AGENTS:
            if agent_['name'] == agent_name_:
                return agent_['durations']
    # ---------------------------------------------------------------------------- #

    # -------------------------- Function: Agent Actions ------------------------- #
    def get_agent_actions(self,agent_name_):
        for agent_ in self.AGENTS:
            if agent_['name'] == agent_name_:
                return agent_['actions']
    # ---------------------------------------------------------------------------- #

    # ------------------------- Function: Object Position ------------------------ #
    def get_object_position(self,object_name_):
        for object_ in self.OBJECTS:
            if object_['name'] == object_name_:
                return object_['coords']
    # ---------------------------------------------------------------------------- #

    # -------------------------- Function: Object Weight ------------------------- #
    def get_object_weight(self,object_name_):
        for object_ in self.OBJECTS:
            if object_['name'] == object_name_:
                return object_['weight']
    # ---------------------------------------------------------------------------- #

    # --------------------------- Function: Object Type -------------------------- #
    def get_object_type(self,object_name_):
        for object_ in self.OBJECTS:
            if object_['name'] == object_name_:
                return object_['type']
    # ---------------------------------------------------------------------------- #

    # -------------------------- Function: Object Color -------------------------- #
    def get_object_color(self,object_name_):
        for object_ in self.OBJECTS:
            if object_['name'] == object_name_:
                return object_['color']
    # ---------------------------------------------------------------------------- #

    # -------------------------- Function: Grid 2 World -------------------------- #
    def grid_2_world(self,grid_description_,desired_cell_):
        
        x_coord = grid_description_["start"][0]
        y_coord = grid_description_["start"][1]
        
        if (grid_description_["row_axis"].find("y") != -1) & (grid_description_["col_axis"].find("x") != -1):
            if grid_description_["row_axis"] == "+y":
                y_coord = y_coord + grid_description_["scale"]*(desired_cell_[1] - 1)
            else:
                y_coord = y_coord - grid_description_["scale"]*(desired_cell_[1] - 1)

            if grid_description_["col_axis"] == "+x":
                x_coord = x_coord + grid_description_["scale"]*(desired_cell_[0] - 1)
            else:
                x_coord = x_coord - grid_description_["scale"]*(desired_cell_[0] - 1)
            
        elif (grid_description_["row_axis"].find("x") != -1) & (grid_description_["col_axis"].find("y") != -1):
            
            if grid_description_["row_axis"] == "+x":
                x_coord = x_coord + grid_description_["scale"]*(desired_cell_[0] - 1)
            else:
                x_coord = x_coord - grid_description_["scale"]*(desired_cell_[0] - 1)

            if grid_description_["col_axis"] == "+y":
                y_coord = y_coord + grid_description_["scale"]*(desired_cell_[1] - 1)
            else:
                y_coord = y_coord - grid_description_["scale"]*(desired_cell_[1] - 1)
                
        return [x_coord,y_coord]
    # ---------------------------------------------------------------------------- #

    # ----------------------- Function: Get Box Description ---------------------- #
    def get_box_description(self,box_name_):
        for box_ in self.BOXES["description"]:
            if box_['box'] == box_name_:
                return box_
    # ---------------------------------------------------------------------------- #
    
    # ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                     NODE                                     #
# ---------------------------------------------------------------------------- #

# ----------------------------------- Main ----------------------------------- #
def main(args=None):
    # ------------------------------ Initialization ------------------------------ #
    rospy.init_node('cp_optimizer_node',anonymous=False)
    # ---------------------------------------------------------------------------- #
    
    # --------------------------------- Optimizer -------------------------------- #
    optimizer = OptimizerEngine()
    # ---------------------------------------------------------------------------- #
    
    # ----------------------------------- Spin ----------------------------------- #
    rospy.spin()
    # ---------------------------------------------------------------------------- #   
    
if __name__ == '__main__':
    # -------------------------------- Try-Except -------------------------------- #
    try:
        main()
    except rospy.ROSInterruptException:
        pass
    # ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #