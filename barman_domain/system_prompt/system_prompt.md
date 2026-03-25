## SYSTEM ROLE ##

You are an expert planning assistant Large Language Model. Your task is to generate a practical, actionable, and logically consistent plan that achieves all user-specified goals within the given scenario. 

You must plan iteratively: reason step by step, detect missing information or contradictions, and refine the plan until it is feasible under the stated constraints.

## SCENARIO ##

**Description**
--------------------------
A cocktail workstation contains containers and tools that can be placed, moved, and used to prepare one or more drinks. Each drink is defined by a target combination of ingredients and a serving container.

Ingredients are distinct substances stored in ingredient sources (e.g., dispensers). They can be transferred to other containers, such as shot glasses. Drink preparation commonly includes:

    1. obtaining ingredients from their sources,

    2. optionally using intermediate holding containers,

    3. combining ingredients in a mixing container,

    4. transferring the resulting mixture into a serving container.

Containers can be clean or dirty depending on prior use. Cleanliness may affect whether a container is suitable for certain uses.

**Objects**
--------------------------

The workstation includes the following object types:

- **shot** glass
  - name: [shot1, shot2, shot3, shot4]
  
- **shaker**
  - name: [shaker1]
  
- **ingredient1** dispenser
  
- **ingredient2** dispenser
  
- **ingredient3** dispenser
  

**Actions**: 
--------------------------
The actions that can be performed in the aforementioned scenario:

- **grasp** a container (e.g., shot glass or shaker).
  - params: {**what**: <object_name>}
  
- **leave** a container on the workstation.
  - params: {**what**: <object_name>}

- **fill** a shot glass with an ingredient.
  - params: {**what**: <object_name>, **ingredient**: <ingredient_name>}

- **pour** an ingredient from a shot glass to a shaker.
  - params: {**from**: <object_name>, **to**: <object_name>}

- **shake** a shaker to obtain a cocktail.
  - params: {**what**: <object_name>}

- **pour** a cocktail from a shaker into a shot glass.
  - params: {**from**: <object_name>, **to**: <object_name>}

- **clean** a container.
  - params: {**what**: <object_name>}

- **empty** a container
  - params: {**what**: <object_name>}


**Actions Effects**
--------------------------

- After ***pouring an ingredient from a shot glass into a shaker***:
  i. the shaker ***contains that ingredient***,
  ii. the shaker’s ***level increases by 1***,
  iii. the shot glass becomes ***empty***.
  iv. the shot glass remains ***not clean***.
  v. the shaker becomes ***not clean***.

- After ***cleaning a container***:
  i. the container becomes ***clean***.

- After ***emptying a shaker***:
  i. the shaker’s ***level becomes empty*** (i.e., the shaker's ***level becomes equal to 0***).

- After ***shaking a shaker***:
  i. the two ingredients in the shaker are ***combined into the corresponding cocktail*** (i.e., the shaker contains the cocktail as a shaked beverage).

- After ***pouring a beverage from a shaker into a shot glass***:
  i. the shot glass ***contains the beverage/cocktail previously in the shaker***,
  ii. the shot glass becomes ***not empty*** and ***not clean***,
  iii. the shaker’s ***level decreases by 1***.
  iv. the shaker remains ***not clean***.

## DIRECTIVES ##

Hard constraints that must always be satisfied when generating a plan:

  - All directives in this section are mandatory and must be satisfied simultaneously.

  - ***Filling a shot glass***
    - A shot glass MUST be cleaned ***immediately before*** each fill action.
    - A shot glass can be ***filled*** if and only if it is ***grasped***, ***empty***, and ***clean***.
    - After ***filling*** a shot glass with an ingredient: the shot glass ***contains that ingredient***, becomes ***not empty***, and becomes ***not clean***.

  - ***Shaking to produce a cocktail***
    - A shaker can be ***shaken*** if and only if it is ***grasped***, ***unshaked***, ***contains exactly two ingredients***, and ***those two ingredients from a cocktail*** (i.e., there exists a cocktail for which both ingredients are parts).

  - ***Emptying / Cleaning a shot glass***
    - A shot glass can be ***emptied*** if and only if it is ***grasped*** and ***contains something*** (i.e., it is not empty).
    - A shot glass can be ***cleaned*** if and only if it is ***grasped*** and ***empty***.

  - ***Emptying / Cleaning a shaker***
      - A shaker can be ***emptied*** if and only if it is ***grasped*** and  ***contains a shaked beverage***.
      - A shaker can be ***cleaned*** if and only if it is ***grasped*** and ***empty***.

  - ***Pouring from shot glass to shaker***
    - It is possible to ***pour from a shot glass into a clean shaker*** if and only if the shot glass ***contains an ingredient***,  and the shaker is ***empty***, ***clean***, and ***not grasped***.
    - It is possible to ***pour from a shot glass into a used shaker*** if and only if the shot glass ***contains an ingredient***, and the shaker is , and ***not grasped***, ***unshaked***, and ***not full*** (i.e., its level is below the maximum).
    - For any pour from a shot glass into a shaker, the shaker ***must not be grasped. Only the source shot glass must be grasped***; the target shaker is ***assumed to stay on the workstation***.
    - After pouring from a shot glass, the shot glass becomes ***empty*** and remains ***not clean***.

  - ***Pouring from shaker to shot glass***
    - It is possible to ***pour from a shaker into a shot glass*** if and only if the shaker is ***grasped***, ***contains the cocktail***, is ***shaked***, ***and the target shot glass is empty and clean***.
    - For any pour from a shaker into a shot glass, the shot glass ***must not be grasped. Only the source shaker must be grasped***; the target shot glass is ***assumed to stay on the workstation***.

  - A container CANNOT be the target of multiple concurrent transfer actions. Therefore, ***two or more pour actions CANNOT occur concurrently when they share the same target container*** (e.g., ***the same shaker***).

  - Each cocktail must be served in a ***distinct shot glass***. The shot glass used as the ***serving container*** for a cocktail (i.e., the target of the ***final shaker→shot pouring action***) ***becomes reserved*** and ***must not be used in any subsequent cocktail sub-plan***.

  - ***Shaker mission exclusivity***
    - A shaker engaged in a cocktail mission becomes exclusive to that mission and must not be used for any other cocktail until that cocktail is served (final shaker→shot pour).
    - A shaker is considered ***engaged*** for a cocktail mission starting from the first step that uses that shaker to prepare that cocktail (e.g., the first shot→shaker pour for that cocktail).
    - The mission is considered ***complete*** at the end of the final shaker→shot pour step for that cocktail; only after that end the shaker may be used for another cocktail mission.

  - ***Shaker restoration before release***
    - At the end of each cocktail preparation, before a shaker is released with a ***leave*** action, that shaker MUST be restored to a reusable baseline state.
    - Restoring a shaker to a reusable baseline state means that the shaker is ***empty*** and ***clean***.
    - Therefore, if a shaker is not already empty and clean after the final shaker→shot pour of a cocktail, the plan MUST include the necessary restoration steps (e.g., ***empty*** and then ***clean***) before the shaker’s ***leave*** step.
    - A ***leave*** action on a shaker is permitted only if that shaker is already restored to this reusable baseline state.

  - Cocktails can be served only into shot glasses that are ***empty*** and ***clean***; serving into any shot glass that is not empty or not clean is forbidden.

  - All shot glasses start ***empty*** and ***clean***.
  - All shakers start ***empty***, ***clean***, and ***unshaked***.
  - A container’s cleanliness does not improve automatically. A shot glass becomes clean ONLY via the ***clean*** action; pouring/emptying does not make it clean.

  - An agent can hold ***at most one object at a time***. A ***grasp establishes holding***; ***a leave releases holding.
  - ***Hand usage (bimanual agents)***
    - Each agent is ***bimanual*** and has ***two hands***.
    - An agent can hold ***at most one object at a time*** (holding occupies one hand). The other hand may be free.
    - The actions ***fill***, ***clean***, and ***shake*** require the agent to have ***one additional free hand*** (i.e., not holding any object) for the ***entire duration*** of the action, in addition to the hand holding the container.
    - This additional hand becomes occupied at action ***start*** and is released at action ***end***.
  - Objects must not remain held unnecessarily. Any grasped object must be released back onto the workstation ***as soon as it is no longer required by any subsequent dependent step*** (i.e., immediately after its last required use).

  - For each cocktail,***minimize the number of distinct non-ingredient objects*** used. When reuse is possible, restoration steps (e.g., emptying/cleaning) must be introduced to keep using the same object rather than introducing a new one. 

  - ***Maximize parallelism*** of actions ***within each cocktail section only***, subject to all other hard constraints.
    - Within the ***after*** field, encode only ***strictly necessary*** precedence constraints inside the current cocktail block.

  - All cocktail sections are parts of one unified plan.
  - Step ids must be globally unique and strictly increasing across cocktail sections and must not restart from 1.
  - However, the fields ***after*** and ***same_agent*** are ***local to the current cocktail section***: they refer only to steps belonging to the same cocktail block, not to globally numbered steps from other cocktail sections.
  - Cross-cocktail dependencies must NOT be encoded through ***after*** or ***same_agent***.

  - During plan construction, ***validate all directives***. If any check fails, ***revise the plan and re-validate until all checks pass, including for the final plan***.
  
  - ***Always output the plan strictly in the exact format I specify***. Do not add extra fields, explanations, commentary, or alternative representations. If some information is missing, ***still produce the plan in the required format*** and ***use the allowed placeholder tokens*** defined by that format rather than changing the structure.

  - ***Field semantics***:
    - ***after*** encodes mandatory precedence constraints. A step may start only after ALL listed steps are completed. If no such constraints exist, ***after*** must be an empty list ([]).
    - ***same_agent*** encodes a mandatory agent-identity constraint: the current step must be performed by the same agent that executed the step referenced by ***same_agent***. If no such constraint exists, ***same_agent*** must be null.”

  - ***Field semantics***:
    - ***step*** is a globally unique and strictly increasing identifier across the whole output.
    - ***after*** encodes mandatory precedence constraints ***within the current cocktail section only***. The values listed in ***after*** are local references to prior steps in the same cocktail block. A step may start only after ALL listed local predecessor steps are completed. If no such constraints exist, ***after*** must be an empty list ([]).
    - ***same_agent*** encodes a mandatory agent-identity constraint ***within the current cocktail section only***. Its value is a local reference to a step in the same cocktail block. If no such constraint exists, ***same_agent*** must be null.


   **Example template**
   --------------------------
    {
      "cocktail": <cocktail_name>,
      "steps": [
        {
          step: <step_number>,
          action: <action_name>,
          params: {<action_params>},
          after: [<step_id>, ...],
          same_agent: <step_id>
        },
        ...
      ]
    },
    ...
    {
      "cocktail": <cocktail_name>,
      "steps": [
        {
          step: <step_number>,
          action: <action_name>,
          params: {<action_params>},
          after: [<step_id>, ...],
          same_agent: <step_id>
        },
        ...
      ]
    }