You are given a system prompt describing a planning domain for a scene (objects, actions, and directives).

Task:
Extract the complete list of resources that exist in the scene, including both tools and non-tool resources (e.g., containers/instruments and ingredient-related resources), and infer how each resource becomes unavailable (blocked) and available again (released). Also distinguish between temporary blocking and permanent blocking when the domain implies that a resource is no longer usable after certain actions.

Output format:
Return ONLY a JSON array with exactly this schema (no extra text):

[
  {
    "id": <name>,
    "type": <type>,
    "blocking_action": {
      "temporarly": {
        "name": <action_name>,
        "on_param": <action_parameter_name>,
        "when": "start"
      },
      "permanently": {
        "name": <action_name>,
        "on_param": <action_parameter_name>,
        "when": "start"
      } | null
    },
    "release_action": {
      "name": <action_name>,
      "on_param": <action_parameter_name>,
      "when": "start" | "end"
    }
  }
]

Rules:
1) Resource enumeration
- List every concrete resource instance explicitly mentioned or implied by the system prompt’s objects/scenario.

2) id
- Use the exact instance names from the system prompt when they exist (e.g., shot1, shaker1).
- For ingredient-related resources: DO NOT create separate dispenser/source ids. Represent each ingredient as a resource using the ingredient identifier only (e.g., "ingredient1", "ingredient2", ...).

3) type (must be very short/synthetic)
- For multi-word tool names, reduce to the core noun (e.g., "shot glass" → "shot").
- For ingredient resources: id and type MUST match exactly (e.g., { "id": "ingredientX", "type": "ingredientX" }).
- Use consistent type naming across all resources.

4) Blocking and release inference (availability)
For each resource, infer:
- One TEMPORARY blocking action: the canonical action event that makes the resource unavailable for concurrent use, but later releases it.
- One release action: the canonical action event that makes the resource available again after temporary blocking.
- Optionally, one PERMANENT blocking action: an action event after which the resource is no longer usable/available for future tasks (i.e., it never gets released again).

Field requirements:
- "blocking_action.temporarly" MUST always be present.
- "blocking_action.temporarly.when" MUST ALWAYS be "start".
- "blocking_action.permanently" MUST be present as a key:
  - If there is no permanent blocking in the domain for that resource, set "permanently": null (do NOT omit the key).
  - If present (not null), "blocking_action.permanently.when" MUST ALWAYS be "start".
- "release_action" MUST always be present.

How to infer temporary block/release:
- Blocking must always be modeled as happening at action start:
  - temporarly.when = "start" (always)
- Infer release timing from the system prompt:
  - If the prompt implies the resource is occupied/held for the full duration, set release_action.when = "end".
  - If the prompt explicitly indicates the resource is released earlier, set release_action.when = "start".
- If the same action both blocks and releases a resource, use the same action name for both:
  - blocking_action.temporarly.when = "start"
  - release_action.when = "end" (unless explicitly stated otherwise)
- Use "on_param" to specify which action parameter corresponds to the resource in that context.

How to infer permanent blocking:
- Only assign a permanent blocking action if the system prompt explicitly states (or hard-directive implies) that after a certain action, that resource becomes unavailable for the remainder of the plan (no release exists for that condition).
- Model permanent blocking as starting at action start (when="start") and persisting thereafter.
- Do NOT invent permanent blocking; if unclear, use null.

Constraints:
- Do NOT invent actions that are not in the system prompt.
- Use exact action identifiers and exact parameter names as written in the system prompt.
- Keep output deterministic and consistent across resources.

Return JSON only, exactly matching the schema.