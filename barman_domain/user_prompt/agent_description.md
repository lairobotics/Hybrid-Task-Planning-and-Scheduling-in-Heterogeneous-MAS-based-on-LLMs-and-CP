You are given a system prompt describing a planning domain for a scene (objects, actions, and hard directives).

Known agents (authoritative):
- There are exactly 3 agents in the scene: agent1, agent2, agent3.
- All agents are bimanual.

Task:
Produce the agent description including bimanuality and the hand usage dynamics implied by the system prompt directives.

Output format:
Return ONLY a JSON array (no extra text) with exactly this schema:

[
  {
    "name": <agent_id>,
    "bimanual": 0 | 1,
    "hand_dynamics": [
      {
        "action": <action_name>,
        "effect": { "op": "minus" | "plus", "value": 1 },
        "when": "start" | "end"
      }
    ]
  }
]

Rules:

1) Agent list (fixed)
- Output exactly these agents in this order: agent1, agent2, agent3.
- Set bimanual = 1 for all agents.

2) What hand_dynamics represents
Interpret hand_dynamics as changes in the number of free hands available to an agent:
- { op: "minus", value: 1 } means one hand becomes occupied.
- { op: "plus",  value: 1 } means one hand becomes free again.

3) Holding dynamics
From the system prompt directives:
- If an action establishes holding of an object, it occupies one hand at action start:
  - action: "grasp" → minus 1 at "start"
- If an action releases holding of an object, it frees one hand at action end:
  - action: "leave" → plus 1 at "end"

4) Additional-hand usage dynamics (from directives)
If the system prompt explicitly states that an action requires an additional free hand for the entire duration (in addition to holding the main object), then model it with two entries:
- minus 1 at "start"
- plus 1 at "end"
Include these entries for every action explicitly listed in the directives as requiring an additional free hand (e.g., fill/clean/shake if stated).

5) No extra inference
- Do NOT add hand_dynamics for actions unless the system prompt explicitly states they change holding or require an additional free hand.
- Always use value = 1.

Return JSON only, exactly matching the schema above.