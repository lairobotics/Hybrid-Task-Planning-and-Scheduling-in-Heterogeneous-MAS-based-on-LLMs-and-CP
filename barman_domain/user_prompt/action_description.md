You are given a system prompt that defines a planning domain for a scene (including an “Actions” section and directives about how actions behave).

Task:
Extract the list of actions and output, for each action:
- its name
- a duration specification (type + base_value)
- the list of parameter names (only names, not types)

Output format:
Return ONLY a JSON array of objects in exactly this structure (no extra text):

[
  {
    "name": <action_name>,
    "duration": {
      "type": "fixed" | "variable",
      "base_value": <number>
    },
    "params": [<param_name>, ...]
  }
]

Rules for action names:
- Use the exact action identifiers as written in the system prompt (case-sensitive).
- Include every action explicitly defined in the “Actions” section.

Rules for params:
- For each action, extract the ordered list of its parameter names exactly as written in the system prompt.
- Return only parameter names (no types, no predicates, no descriptions).
- Keep the parameter order consistent with the action definition.

Rules for duration:
- Determine "type" as follows:
  - If the action is a manipulation/transfer operation, set duration.type = "fixed".
  - If the action is a restoration/reset operation (i.e., its purpose is to restore a tool to a baseline usable condition, and/or it is explicitly referenced as a “restoration step” in the directives), set duration.type = "variable".
- Set duration.base_value = 5 for ALL actions, regardless of type.

Return JSON only, exactly matching the schema above.