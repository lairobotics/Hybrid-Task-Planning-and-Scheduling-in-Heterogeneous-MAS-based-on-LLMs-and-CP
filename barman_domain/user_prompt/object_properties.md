You are given:
1) A system prompt describing a planning domain (objects, actions, and hard directives).
2) A JSON list of the resources present in the scene (id/type), pasted below.

RESOURCES (authoritative for type names):
<PASTE_RESOURCES_JSON_HERE>

Task:
Extract ONLY the physical TOOL TYPES (exclude consumables and exclude sources/dispensers) and represent them by tool type (not by individual instance). The output must be consistent with the resource types used in the RESOURCES list.

Return ONLY a JSON array (no extra text) with exactly this schema:

[
  {
    "resource_type": <type>,
    "constraining_policy": "mission" | null,
    "state": [
      {
        "name": <state_name>,
        "type": "boolean" | "numeric",
        "values": [<allowed_values>],
        "initial_value": <initial_value>,
        "reset_action": <action_name> | null,
        "dynamics": [
          {
            "action": <action_name>,
            "on_param": <action_parameter_name>,
            "effect": { "op": "plus"|"minus", "value": <integer> },
            "when": "start"|"end"
          }
        ]
      }
    ]
  }
]

Rules:

1) Resource type alignment with RESOURCES (MUST)
- Treat the RESOURCES JSON as the authoritative source of canonical type labels.
- Only output tool types that appear in RESOURCES.
- "resource_type" values in your output MUST exactly match the corresponding "type" strings used in RESOURCES.
- Determine which types are tools by excluding ingredient-like/non-tool entries (consumables/sources) and by checking which types are acted upon by actions in the system prompt.

2) Tool type selection and grouping
- Include only physical tools acted upon by domain actions (containers/instruments).
- Exclude ingredients and any ingredient sources/dispensers.
- Group by tool type and output ONE entry per tool type.

1) Constraining policy 
- constraining_policy = "mission" means that once a resource of this type is engaged by a given mission, it is exclusive to that mission and CANNOT be used by any other mission until the mission reaches its completion (as defined by the domain, e.g., the final “deliver/commit” step for that mission). This is a mission-scoped exclusivity constraint (temporary, but spanning multiple steps).
- constraining_policy = null means that resources of this type may be released and re-used across missions as soon as their local state is restored to a reusable baseline (via explicit reset/restoration actions), even if earlier missions are still ongoing. In other words, reuse is permitted across overlapping missions whenever the domain’s state and constraints allow it.
- IMPORTANT DISTINCTION (avoid misclassification):
- Do NOT set constraining_policy="mission" based solely on a "reserved after final delivery/serving" rule for a specific role. Role-based permanent reservation (e.g., the serving container becomes reserved after the final commit step) is NOT mission-scoped exclusivity for the whole type; it applies only to the specific instance used for delivery.
  
1) State variable inference (type-level)
- Infer state variables by analyzing action preconditions/effects, invariants, and directives.
- Include a state variable only if it is an intrinsic, mutable property of the tool type.
- Exclude purely relational facts (e.g., who holds what).
- Exclude derived/bookkeeping states (e.g., “reserved”) if deducible (these should be captured, if needed, by "constraining_policy" instead of a state).

1) State type classification
- Do NOT classify a state as boolean only because its values are [0, 1].
- Classify as "boolean" ONLY if the state represents a binary property/condition (predicate-like), such as cleanliness, availability, locked/unlocked, etc.
- Classify as "numeric" if the state represents a quantity/level/amount/capacity/counter, EVEN IF it only has values [0, 1] (binary numeric).
  Typical indicators of numeric quantity: state name contains keywords like "level", "fill_level", "amount", "count", "capacity".
  Also treat as numeric if the reset_action is an emptying/reset-to-zero action (e.g., "empty") or if the state is incremented/decremented as a level.

1) State encoding, allowed values, initial values
- Each state must provide a finite discrete set in "values".
- For numeric states, infer the smallest sufficient set from explicit constraints/effects (often [0..N]).
- Set "initial_value" from explicit initial-state statements/directives for that tool type. If unspecified, use a consistent neutral baseline.

1) Dynamics inference (STRICT: effects only)
- Add a dynamics entry ONLY when the system prompt explicitly states that the action changes that tool state variable.
- Do NOT infer side-effects.
- Each entry must contain: action, on_param, effect (plus/minus with integer value), and when (start/end).
- Set "when" using the temporal language in the system prompt:
  - If updates are described as “After <action> ...”, use when="end".
  - If described as happening at the beginning, use when="start".
  - If not specified, default to when="end".

Reset-to-baseline mapping (when explicitly stated):
- If an action explicitly sets a numeric state to a baseline value B (often 0) and only plus/minus are allowed,
  represent it using one "minus" rule for each non-baseline allowed value v in values:
  effect = { "op": "minus", "value": (v - B) }.
- Apply the same idea to boolean resets only if explicitly stated.

8) Reset action extraction
- Set "reset_action" to the action whose explicit effects restore the state variable to its initial/baseline value.
- If none exists, set reset_action = null.
- Do NOT invent reset actions.

9) State scope filter (exclude non-maintenance states)
- Exclude any state variable that represents production/result or identity of contents (e.g., shaken/mixed status, contains-ingredient/cocktail identity flags).
- Also exclude any state whose reset_action would be null (only include states with an explicit reset).

10) Deduplication and consistency
- Do not output duplicate dynamics entries (same action, on_param, effect, when).
- Use stable, deterministic snake_case for state names and keep naming consistent within each tool type.
- Return JSON only, exactly matching the schema above.